from __future__ import annotations

import numpy as np


def adjust_pd_for_fx(pd_base: float, fx_shock: np.ndarray, dependence: float) -> np.ndarray:
    # dependence >0 means wrong-way (higher default with adverse FX)
    adj = np.clip(pd_base * np.exp(dependence * fx_shock), 1e-4, 0.95)
    return adj
