from __future__ import annotations

import numpy as np

from .contract import GuaranteeContract


def apply_tranche(raw_loss: np.ndarray, notional: float, c: GuaranteeContract) -> np.ndarray:
    att = c.attachment * notional
    det = c.detachment * notional
    lim = c.limit_pct * notional
    clipped = np.clip(raw_loss - att, 0.0, max(det - att, 0.0))
    return np.minimum(clipped, lim)


def payout_distribution(
    mtm_at_default: np.ndarray,
    default_flags: np.ndarray,
    notional: float,
    contract: GuaranteeContract,
) -> np.ndarray:
    if contract.mode == "default_triggered":
        raw = default_flags * np.maximum(mtm_at_default, 0.0) * contract.coverage_pct
    else:
        raw = np.maximum(mtm_at_default, 0.0) * contract.coverage_pct
    return apply_tranche(raw, notional, contract)
