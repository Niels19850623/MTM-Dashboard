from __future__ import annotations

import numpy as np


def liquidity_buffer(monthly_claims: np.ndarray, floor_pct: float, notional: float) -> dict[str, float]:
    one_m_95 = float(np.quantile(monthly_claims, 0.95))
    one_m_99 = float(np.quantile(monthly_claims, 0.99))
    three_m = monthly_claims.reshape(-1, 3).sum(axis=1) if len(monthly_claims) >= 3 else monthly_claims
    three_m_95 = float(np.quantile(three_m, 0.95))
    three_m_99 = float(np.quantile(three_m, 0.99))
    rec = max(one_m_99, three_m_95, floor_pct * notional)
    return {
        "expected_monthly": float(np.mean(monthly_claims)),
        "1m_95": one_m_95,
        "1m_99": one_m_99,
        "3m_95": three_m_95,
        "3m_99": three_m_99,
        "recommended": rec,
    }
