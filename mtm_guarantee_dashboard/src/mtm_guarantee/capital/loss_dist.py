from __future__ import annotations

import numpy as np


def var_es(losses: np.ndarray, confidence: float) -> tuple[float, float, float]:
    losses = np.asarray(losses)
    el = float(losses.mean())
    var = float(np.quantile(losses, confidence))
    tail = losses[losses >= var]
    es = float(tail.mean() if len(tail) else var)
    return el, var, es


def exceedance_curve(losses: np.ndarray, points: int = 100) -> tuple[np.ndarray, np.ndarray]:
    xs = np.linspace(0, float(np.max(losses)), points)
    ys = np.array([(losses > x).mean() for x in xs])
    return xs, ys
