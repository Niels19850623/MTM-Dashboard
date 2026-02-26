from __future__ import annotations


def required_capital(var: float, es: float, method: str, overlay_pct: float) -> float:
    base = es if method.upper() == "ES" else var
    return base * (1 + overlay_pct)
