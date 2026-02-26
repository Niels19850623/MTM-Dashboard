from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValidationIssue:
    level: str
    message: str


def validate_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(v, 0.0) for v in weights.values())
    if total <= 0:
        n = len(weights)
        return {k: 1 / n for k in weights}
    return {k: max(v, 0.0) / total for k, v in weights.items()}
