from __future__ import annotations

import pandas as pd


def get_rate_differential(rates: pd.DataFrame, ccy: str, usd_col: str = "USD") -> float:
    cols = rates.columns
    if ccy not in cols or usd_col not in cols:
        return 0.0
    return float((rates[ccy] - rates[usd_col]).dropna().tail(12).mean() / 100.0)
