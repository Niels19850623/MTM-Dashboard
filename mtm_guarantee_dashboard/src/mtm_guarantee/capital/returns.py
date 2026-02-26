from __future__ import annotations


def waterfall(
    notional: float,
    client_fee_bps: float,
    opex_bps: float,
    reserve_bps: float,
    expected_loss: float,
    mezz_notional: float,
    mezz_coupon: float,
    senior_limit: float,
    senior_fee_bps: float,
    equity_capital: float,
    senior_capital_factor: float,
) -> dict[str, float]:
    premium = notional * client_fee_bps / 1e4
    opex = notional * opex_bps / 1e4
    reserve = notional * reserve_bps / 1e4
    net_available = premium - opex - reserve - expected_loss
    mezz_coupon_amt = mezz_notional * mezz_coupon
    senior_fee = senior_limit * senior_fee_bps / 1e4
    equity_residual = net_available - mezz_coupon_amt - senior_fee
    equity_roe = equity_residual / equity_capital if equity_capital > 0 else 0.0
    mezz_icr = net_available / mezz_coupon_amt if mezz_coupon_amt > 0 else 0.0
    implied_senior_roe = senior_fee / (senior_limit * senior_capital_factor) if senior_limit > 0 else 0.0
    return {
        "premium": premium,
        "opex": opex,
        "reserve": reserve,
        "expected_loss": expected_loss,
        "net_available": net_available,
        "mezz_coupon": mezz_coupon_amt,
        "senior_fee": senior_fee,
        "equity_residual": equity_residual,
        "equity_roe": equity_roe,
        "mezz_icr": mezz_icr,
        "implied_senior_roe": implied_senior_roe,
    }
