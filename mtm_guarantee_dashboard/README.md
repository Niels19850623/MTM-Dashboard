# mtm_guarantee_dashboard

Interactive model and Streamlit dashboard for an EM FX hedge MTM guarantee vehicle.

## What it does
- Loads FX and rates data from `FX Data and Interest rates.xlsx`.
- Restricts currency universe to `UGX,TZS,KES,BWP,BDT,LKR,VND,IDR`.
- Simulates MTM and guarantee payouts in two modes:
  - **Default-triggered** positive close-out MTM.
  - **Full-MTM** sensitivity mode.
- Computes EL/VaR/ES, required capital (`VaR/ES + overlays`), max leverage, and currency tail risk contribution.
- Builds a 3-layer capital stack waterfall with equity/mezz/senior metrics.
- Estimates liquidity buffer from monthly cash-call stresses.

## What it does not do
- This is a proxy model (Phase 0/1), not a full legal/ISDA valuation stack.
- Rates treatment is an explainable approximation for carry and forward effects.

## Install and run
```bash
pip install -e .
streamlit run app.py -- --excel "./FX Data and Interest rates.xlsx"
```

## Excel mapping
Configured in `src/mtm_guarantee/config.py`:
- FX sheet: `Historical_fx` with `Currency`, `Date`, and FX value (or wide dates melted).
- Rates sheet: first match among `Rates`, `Interest_rates`, `Historical_rates`.
- If missing, loader throws actionable errors and dashboard surfaces warnings.

## Dashboard pages / sections
- Portfolio Builder
- Risk & Capital
- Investor Returns
- Scenarios & Sensitivities
- Liquidity

## Default scenario
- 8 currencies equal weight, USD 100m, 5y tenor
- 80% CCS / 20% NDF
- PD 4%, LGD 100%
- 100% coverage, no attachment, limit 100%
- Fees: 50/10/5 bps (client/opex/reserve)
- ES 99.5% with 20% overlay
- Target leverage 15x

## Exports
- Scenario CSV download from dashboard
- Tear sheet markdown saved to `outputs/tear_sheet.md`
