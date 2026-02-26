from __future__ import annotations

import numpy as np
import pandas as pd


def simulate_fx_paths(
    returns: pd.DataFrame,
    s0: pd.Series,
    tenor_years: int,
    n_paths: int,
    mode: str = "historical",
    corr_stress: float = 1.0,
    seed: int = 42,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    months = tenor_years * 12
    n_ccy = len(s0)
    if mode == "historical":
        arr = returns.values
        idx = rng.integers(0, arr.shape[0], size=(n_paths, months))
        shocks = arr[idx, :]
    else:
        mu = returns.mean().values
        cov = returns.cov().values * corr_stress
        shocks = rng.multivariate_normal(mu, cov, size=(n_paths, months))
    log_paths = np.cumsum(shocks, axis=1)
    paths = s0.values[None, None, :] * np.exp(log_paths)
    return paths
