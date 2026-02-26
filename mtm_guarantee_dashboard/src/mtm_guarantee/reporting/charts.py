from __future__ import annotations

import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def leverage_roe_curve(leverage_grid: np.ndarray, base_margin: float, loss_rate: float, target: float):
    roe = leverage_grid * (base_margin - loss_rate)
    fig = px.line(x=leverage_grid, y=roe, labels={"x": "Leverage", "y": "Equity ROE"})
    fig.add_vline(x=target, line_dash="dash", line_color="red")
    return fig


def loss_exceedance(xs, ys):
    return px.line(x=xs, y=ys, labels={"x": "Loss", "y": "P(Loss>x)"})


def waterfall_chart(wf: dict[str, float]):
    x = ["Premium", "Opex", "Reserve", "EL", "Mezz", "Senior", "Equity"]
    y = [wf["premium"], -wf["opex"], -wf["reserve"], -wf["expected_loss"], -wf["mezz_coupon"], -wf["senior_fee"], wf["equity_residual"]]
    fig = go.Figure(go.Waterfall(x=x, y=y, measure=["relative"] * 6 + ["total"]))
    return fig
