from __future__ import annotations

DEFAULT_CURRENCIES = ["UGX", "TZS", "KES", "BWP", "BDT", "LKR", "VND", "IDR"]

DEFAULT_SCENARIO = {
    "portfolio_notional": 100_000_000,
    "tenor_years": 5,
    "ccs_weight": 0.8,
    "ndf_weight": 0.2,
    "pd_annual": 0.04,
    "lgd": 1.0,
    "coverage_pct": 1.0,
    "attachment": 0.0,
    "detachment": 1.0,
    "limit_pct": 1.0,
    "client_fee_bps": 50,
    "opex_bps": 10,
    "reserve_bps": 5,
    "capital_method": "ES",
    "capital_confidence": 0.995,
    "overlay_pct": 0.2,
    "horizon_years": 1,
    "target_leverage": 15.0,
    "simulation_mode": "historical",
    "paths": 10_000,
    "fast_paths": 2_000,
    "mtm_phase": "phase1",
    "default_mode": "default_triggered",
}

EXCEL_MAPPING = {
    "fx_sheet": "Historical_fx",
    "date_col": "Date",
    "currency_col": "Currency",
    "rate_sheet_candidates": ["Rates", "Interest_rates", "Historical_rates"],
}
