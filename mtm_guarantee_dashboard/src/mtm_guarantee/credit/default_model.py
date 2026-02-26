from __future__ import annotations

import numpy as np


def default_time_from_pd(pd_annual: float, tenor_years: float, n_paths: int, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    hazard = -np.log(max(1 - pd_annual, 1e-8))
    u = rng.random(n_paths)
    t = -np.log(np.maximum(1 - u, 1e-12)) / max(hazard, 1e-8)
    t[t > tenor_years] = np.nan
    return t
