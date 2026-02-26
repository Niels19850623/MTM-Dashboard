from __future__ import annotations


def layer_amounts(notional: float, equity_pct: float, mezz_pct: float) -> dict[str, float]:
    equity = notional * equity_pct
    mezz = notional * mezz_pct
    senior = max(notional - equity - mezz, 0.0)
    return {"equity": equity, "mezz": mezz, "senior": senior}
