from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from mtm_guarantee.config import DEFAULT_CURRENCIES, DEFAULT_SCENARIO
from mtm_guarantee.io.excel_loader import ExcelMappingError, load_market_data
from mtm_guarantee.io.validation import validate_weights
from mtm_guarantee.market.fx import apply_quote_convention, monthly_returns
from mtm_guarantee.market.rates import get_rate_differential
from mtm_guarantee.market.simulation import simulate_fx_paths
from mtm_guarantee.instruments.mtm_proxy import mtm_phase0, mtm_phase1, blend_ccs_ndf
from mtm_guarantee.credit.default_model import default_time_from_pd
from mtm_guarantee.guarantee.contract import GuaranteeContract
from mtm_guarantee.guarantee.payout import payout_distribution
from mtm_guarantee.capital.loss_dist import exceedance_curve, var_es
from mtm_guarantee.capital.rating_capital import required_capital
from mtm_guarantee.capital.returns import waterfall
from mtm_guarantee.capital.liquidity import liquidity_buffer
from mtm_guarantee.reporting.charts import leverage_roe_curve, loss_exceedance, waterfall_chart
from mtm_guarantee.reporting.tables import scenario_summary_table
from mtm_guarantee.reporting.tearsheet import write_tearsheet


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--excel", default="./FX Data and Interest rates.xlsx")
    return p.parse_known_args()[0]


@st.cache_data
def get_data(path: str, currencies: list[str]):
    return load_market_data(path, currencies)


@st.cache_data
def run_model(fx, rates, weights, inputs):
    fxr = monthly_returns(fx)
    s0 = fx.pivot(index="date", columns="currency", values="fx_norm").sort_index().iloc[-1]
    paths = simulate_fx_paths(
        fxr[s0.index], s0, inputs["tenor_years"], int(inputs["paths"]), mode=inputs["simulation_mode"], corr_stress=inputs["corr_stress"]
    )
    n_paths, months, n_ccy = paths.shape
    dt = default_time_from_pd(inputs["pd_annual"], inputs["tenor_years"], n_paths)
    default_flags = (~np.isnan(dt)).astype(float)
    idx = np.minimum(np.nan_to_num(dt, nan=inputs["tenor_years"]) * 12, months - 1).astype(int)

    weighted_mtm = np.zeros(n_paths)
    contrib = {c: np.zeros(n_paths) for c in s0.index}
    for j, c in enumerate(s0.index):
        st_at = paths[np.arange(n_paths), idx, j]
        base0 = mtm_phase0(inputs["portfolio_notional"] * weights[c], s0.iloc[j], st_at)
        if inputs["mtm_phase"] == "phase1":
            carry = get_rate_differential(rates, c)
            ccs = mtm_phase1(inputs["portfolio_notional"] * weights[c], s0.iloc[j], st_at, np.full_like(st_at, carry), dt.clip(min=0, max=inputs["tenor_years"]))
            ndf = mtm_phase1(inputs["portfolio_notional"] * weights[c], s0.iloc[j], st_at, np.full_like(st_at, carry * 0.5), dt.clip(min=0, max=inputs["tenor_years"]))
            mtm = blend_ccs_ndf(ccs, ndf, inputs["ccs_weight"])
        else:
            mtm = base0
        contrib[c] = mtm
        weighted_mtm += mtm

    contract = GuaranteeContract(
        coverage_pct=inputs["coverage_pct"], attachment=inputs["attachment"], detachment=inputs["detachment"], limit_pct=inputs["limit_pct"], mode=inputs["default_mode"]
    )
    losses = payout_distribution(weighted_mtm, default_flags, inputs["portfolio_notional"], contract)
    el, var, es = var_es(losses, inputs["capital_confidence"])
    cap = required_capital(var, es, inputs["capital_method"], inputs["overlay_pct"])
    max_lev = inputs["portfolio_notional"] / cap if cap > 0 else np.inf
    xs, ys = exceedance_curve(losses)
    tail_cut = np.quantile(losses, inputs["capital_confidence"])
    tail = losses >= tail_cut
    tail_contrib = {k: float(v[tail].mean() if tail.any() else 0.0) for k, v in contrib.items()}

    monthly_claims = np.repeat(losses / max(inputs["tenor_years"] * 12, 1), inputs["tenor_years"] * 12)
    liq = liquidity_buffer(monthly_claims, inputs["liq_floor_pct"], inputs["portfolio_notional"])

    return {"losses": losses, "el": el, "var": var, "es": es, "cap": cap, "max_lev": max_lev, "xs": xs, "ys": ys, "tail_contrib": tail_contrib, "liq": liq}


def main():
    args = parse_args()
    st.set_page_config(page_title="MTM Guarantee Dashboard", layout="wide")
    st.title("EM FX MTM Guarantee Dashboard")

    with st.sidebar:
        st.header("Global Settings")
        selected = st.multiselect("Currencies", DEFAULT_CURRENCIES, default=DEFAULT_CURRENCIES)
        fast = st.toggle("Fast mode (2k paths)", value=False)
        sim_mode = st.selectbox("Simulation", ["historical", "parametric"])
        corr_stress = st.slider("Correlation stress", 0.5, 1.5, 1.0)
        run = st.button("Run simulation", type="primary")

    if not selected:
        st.warning("Select at least one currency.")
        return

    try:
        fx, rates, missing = get_data(args.excel, selected)
    except (FileNotFoundError, ExcelMappingError) as e:
        st.error(str(e))
        return

    if missing:
        st.warning(f"Missing currencies in workbook: {missing}")

    inv = {c: st.sidebar.checkbox(f"Invert quote {c}", value=False) for c in selected}
    fx = apply_quote_convention(fx, inv)

    st.subheader("Portfolio Builder")
    wdf = pd.DataFrame({"currency": selected, "weight": [1 / len(selected)] * len(selected)}).set_index("currency")
    wdf = st.data_editor(wdf)
    weights = validate_weights(wdf["weight"].to_dict())
    st.caption(f"Normalised weights sum: {sum(weights.values()):.4f}")

    c1, c2, c3 = st.columns(3)
    notional = c1.number_input("Total notional (USD)", value=float(DEFAULT_SCENARIO["portfolio_notional"]))
    tenor = c2.slider("Tenor (years)", 1, 10, DEFAULT_SCENARIO["tenor_years"])
    ccs_weight = c3.slider("CCS weight", 0.0, 1.0, DEFAULT_SCENARIO["ccs_weight"])

    inputs = {
        "portfolio_notional": notional,
        "tenor_years": tenor,
        "paths": DEFAULT_SCENARIO["fast_paths"] if fast else DEFAULT_SCENARIO["paths"],
        "simulation_mode": sim_mode,
        "corr_stress": corr_stress,
        "pd_annual": st.slider("PD annual", 0.0, 0.2, DEFAULT_SCENARIO["pd_annual"]),
        "lgd": st.slider("LGD", 0.0, 1.0, DEFAULT_SCENARIO["lgd"]),
        "coverage_pct": st.slider("Coverage", 0.0, 1.0, DEFAULT_SCENARIO["coverage_pct"]),
        "attachment": st.slider("Attachment % notional", 0.0, 0.5, DEFAULT_SCENARIO["attachment"]),
        "detachment": st.slider("Detachment % notional", 0.5, 1.0, DEFAULT_SCENARIO["detachment"]),
        "limit_pct": st.slider("Limit % notional", 0.1, 1.0, DEFAULT_SCENARIO["limit_pct"]),
        "default_mode": st.selectbox("Payout mode", ["default_triggered", "full_mtm"]),
        "mtm_phase": st.selectbox("MTM engine", ["phase0", "phase1"]),
        "ccs_weight": ccs_weight,
        "capital_method": st.selectbox("Capital method", ["ES", "VaR"]),
        "capital_confidence": st.selectbox("Confidence", [0.99, 0.995], index=1),
        "overlay_pct": st.slider("Overlay %", 0.0, 1.0, DEFAULT_SCENARIO["overlay_pct"]),
        "target_leverage": st.slider("Target leverage", 5.0, 20.0, DEFAULT_SCENARIO["target_leverage"]),
        "client_fee_bps": st.number_input("Client fee bps", value=float(DEFAULT_SCENARIO["client_fee_bps"])),
        "opex_bps": st.number_input("Opex bps", value=float(DEFAULT_SCENARIO["opex_bps"])),
        "reserve_bps": st.number_input("Reserve bps", value=float(DEFAULT_SCENARIO["reserve_bps"])),
        "liq_floor_pct": st.slider("Liquidity floor %", 0.0, 0.2, 0.02),
    }

    if run:
        res = run_model(fx, rates, weights, inputs)
        st.subheader("Risk & Capital")
        a, b, c, d = st.columns(4)
        a.metric("EL", f"${res['el']:,.0f}")
        b.metric("VaR", f"${res['var']:,.0f}")
        c.metric("ES", f"${res['es']:,.0f}")
        d.metric("Required Capital", f"${res['cap']:,.0f}")
        st.metric("Max leverage", f"{res['max_lev']:.2f}x")
        st.plotly_chart(loss_exceedance(res["xs"], res["ys"]), use_container_width=True)
        st.plotly_chart(px.bar(x=list(res["tail_contrib"].keys()), y=list(res["tail_contrib"].values()), labels={"x": "Currency", "y": "Tail contribution"}), use_container_width=True)

        st.subheader("Investor Returns")
        mezz_pct = st.slider("Mezz %", 0.0, 0.5, 0.15)
        mezz_coupon = st.slider("Mezz coupon", 0.0, 0.2, 0.08)
        senior_limit = st.slider("Senior limit %", 0.0, 1.0, 0.6) * notional
        senior_fee_bps = st.slider("Senior fee bps", 0.0, 500.0, 80.0)
        senior_cap_factor = st.slider("Senior capital factor", 0.01, 1.0, 0.2)
        equity_capital = notional / inputs["target_leverage"]
        wf = waterfall(notional, inputs["client_fee_bps"], inputs["opex_bps"], inputs["reserve_bps"], res["el"], notional * mezz_pct, mezz_coupon, senior_limit, senior_fee_bps, equity_capital, senior_cap_factor)
        st.plotly_chart(waterfall_chart(wf), use_container_width=True)
        st.plotly_chart(leverage_roe_curve(np.linspace(5, 20, 40), (inputs["client_fee_bps"] - inputs["opex_bps"] - inputs["reserve_bps"]) / 1e4, res["el"] / notional, inputs["target_leverage"]), use_container_width=True)
        st.write({"Equity ROE": wf["equity_roe"], "Mezz ICR": wf["mezz_icr"], "Senior implied ROE": wf["implied_senior_roe"]})

        st.subheader("Scenarios & Sensitivities")
        pd_grid = np.linspace(0.01, 0.1, 8)
        vol_grid = np.linspace(0.8, 1.4, 8)
        heat = np.array([[inputs["target_leverage"] * ((inputs["client_fee_bps"] - inputs["opex_bps"] - inputs["reserve_bps"]) / 1e4 - p * v * 0.2) for v in vol_grid] for p in pd_grid])
        st.plotly_chart(px.imshow(heat, x=np.round(vol_grid, 2), y=np.round(pd_grid, 3), labels={"x": "Vol multiplier", "y": "PD", "color": "Equity ROE proxy"}), use_container_width=True)

        st.subheader("Liquidity")
        st.write(res["liq"])
        st.plotly_chart(px.histogram(x=np.repeat(res["losses"] / (tenor * 12), tenor * 12), nbins=40, labels={"x": "Monthly cash call"}), use_container_width=True)

        summary = scenario_summary_table(inputs)
        st.dataframe(summary, use_container_width=True)
        st.download_button("Download scenario CSV", summary.to_csv(index=False).encode("utf-8"), file_name="scenario_outputs.csv")

        out_path = write_tearsheet("outputs/tear_sheet.md", "MTM Guarantee Tear Sheet", {"EL": res["el"], "ES": res["es"], "Capital": res["cap"], "MaxLeverage": res["max_lev"]}, summary.to_markdown(index=False))
        st.success(f"Tear sheet saved to {out_path}")


if __name__ == "__main__":
    main()
