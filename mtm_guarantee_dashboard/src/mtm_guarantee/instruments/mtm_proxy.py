from __future__ import annotations

import numpy as np


def mtm_phase0(notional: float, s0: np.ndarray, st: np.ndarray) -> np.ndarray:
    return notional * np.maximum(s0 / st - 1.0, 0.0)


def mtm_phase1(notional: float, s0: np.ndarray, st: np.ndarray, carry: np.ndarray, t_years: float) -> np.ndarray:
    fx_leg = np.maximum(s0 / st - 1.0, 0.0)
    carry_adj = np.exp(carry * t_years) - 1.0
    return notional * np.maximum(fx_leg + 0.5 * carry_adj, 0.0)


def blend_ccs_ndf(ccs_mtm: np.ndarray, ndf_mtm: np.ndarray, ccs_weight: float) -> np.ndarray:
    return ccs_weight * ccs_mtm + (1.0 - ccs_weight) * ndf_mtm
