from __future__ import annotations

import numpy as np
import pandas as pd


def stressed_corr(returns: pd.DataFrame, stress: float = 1.0) -> pd.DataFrame:
    corr = returns.corr().fillna(0.0)
    ident = np.eye(len(corr))
    stressed = ident + (corr.values - ident) * stress
    return pd.DataFrame(stressed, index=corr.index, columns=corr.columns)
