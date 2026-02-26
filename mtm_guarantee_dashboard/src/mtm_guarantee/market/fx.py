from __future__ import annotations

import numpy as np
import pandas as pd


def apply_quote_convention(fx_df: pd.DataFrame, inverted: dict[str, bool]) -> pd.DataFrame:
    out = fx_df.copy()
    out["fx_norm"] = out.apply(
        lambda r: 1.0 / r["fx"] if inverted.get(r["currency"], False) else r["fx"], axis=1
    )
    return out


def monthly_returns(fx_df: pd.DataFrame) -> pd.DataFrame:
    piv = fx_df.pivot(index="date", columns="currency", values="fx_norm").sort_index()
    return np.log(piv / piv.shift(1)).dropna()
