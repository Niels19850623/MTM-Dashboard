from __future__ import annotations

import numpy as np
import pandas as pd

from mtm_guarantee.market.fx import apply_quote_convention
from mtm_guarantee.guarantee.contract import GuaranteeContract
from mtm_guarantee.guarantee.payout import payout_distribution
from mtm_guarantee.capital.returns import waterfall


def test_quote_inversion():
    df = pd.DataFrame({"currency": ["UGX"], "fx": [3500.0], "date": ["2020-01-01"]})
    out = apply_quote_convention(df, {"UGX": True})
    assert np.isclose(out.loc[0, "fx_norm"], 1 / 3500.0)


def test_payout_sign_lender_perspective():
    c = GuaranteeContract(mode="default_triggered", coverage_pct=1.0)
    mtm = np.array([10.0, -5.0])
    d = np.array([1.0, 1.0])
    out = payout_distribution(mtm, d, 100.0, c)
    assert out[0] > 0 and out[1] == 0


def test_waterfall_identity():
    wf = waterfall(100, 100, 10, 5, 1, 10, 0.1, 20, 50, 10, 0.2)
    assert np.isclose(wf["equity_residual"], wf["net_available"] - wf["mezz_coupon"] - wf["senior_fee"])

from mtm_guarantee.io.excel_loader import load_market_data
from mtm_guarantee.config import DEFAULT_CURRENCIES


def test_loader_reads_all_currencies_if_present(tmp_path):
    p = tmp_path / "test.xlsx"
    dates = pd.date_range("2020-01-01", periods=3, freq="M")
    fx = pd.DataFrame(
        [(c, d, 100 + i) for c in DEFAULT_CURRENCIES for i, d in enumerate(dates)],
        columns=["Currency", "Date", "fx"],
    )
    rates = pd.DataFrame({"Date": dates, "USD": [5, 5, 5], **{c: [7, 7, 7] for c in DEFAULT_CURRENCIES}})
    with pd.ExcelWriter(p) as w:
        fx.to_excel(w, sheet_name="Historical_fx", index=False)
        rates.to_excel(w, sheet_name="Rates", index=False)
    fx_out, _, missing = load_market_data(str(p), DEFAULT_CURRENCIES)
    assert sorted(fx_out["currency"].unique().tolist()) == sorted(DEFAULT_CURRENCIES)
    assert missing == []
