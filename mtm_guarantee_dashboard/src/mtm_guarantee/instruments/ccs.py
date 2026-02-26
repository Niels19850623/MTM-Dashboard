from __future__ import annotations

import numpy as np


def ccs_mtm_proxy(base_mtm: np.ndarray, carry: np.ndarray, t: float) -> np.ndarray:
    return np.maximum(base_mtm * (1 + 0.25 * (np.exp(carry * t) - 1.0)), 0.0)
