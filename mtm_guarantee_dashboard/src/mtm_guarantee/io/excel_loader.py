from __future__ import annotations

import pandas as pd

from mtm_guarantee.config import DEFAULT_CURRENCIES, EXCEL_MAPPING


class ExcelMappingError(ValueError):
    pass


def _find_rate_sheet(xls: pd.ExcelFile, candidates: list[str]) -> str:
    for c in candidates:
        if c in xls.sheet_names:
            return c
    raise ExcelMappingError(
        f"No rates sheet found. Expected one of {candidates}; available={xls.sheet_names}."
    )


def load_market_data(excel_path: str, currencies: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    currencies = currencies or DEFAULT_CURRENCIES
    xls = pd.ExcelFile(excel_path)
    if EXCEL_MAPPING["fx_sheet"] not in xls.sheet_names:
        raise ExcelMappingError(
            f"FX sheet '{EXCEL_MAPPING['fx_sheet']}' missing. Available={xls.sheet_names}"
        )

    fx_raw = pd.read_excel(xls, EXCEL_MAPPING["fx_sheet"])
    if EXCEL_MAPPING["currency_col"] in fx_raw.columns and EXCEL_MAPPING["date_col"] in fx_raw.columns:
        fx = fx_raw.copy()
    elif EXCEL_MAPPING["currency_col"] in fx_raw.columns:
        fx = fx_raw.melt(id_vars=[EXCEL_MAPPING["currency_col"]], var_name=EXCEL_MAPPING["date_col"], value_name="fx")
    else:
        raise ExcelMappingError(
            "Historical_fx format unsupported: need Currency column and Date or date-like columns."
        )

    fx = fx.rename(columns={EXCEL_MAPPING["currency_col"]: "currency", EXCEL_MAPPING["date_col"]: "date"})
    fx["date"] = pd.to_datetime(fx["date"], errors="coerce")
    if "fx" not in fx.columns:
        if "value" in fx.columns:
            fx = fx.rename(columns={"value": "fx"})
        else:
            num_cols = [c for c in fx.columns if c not in {"currency", "date"}]
            fx = fx.rename(columns={num_cols[0]: "fx"})

    fx = fx.dropna(subset=["date", "currency", "fx"])
    fx = fx[fx["currency"].isin(currencies)].sort_values(["currency", "date"])
    present = sorted(fx["currency"].unique().tolist())
    missing = sorted(set(currencies) - set(present))

    rate_sheet = _find_rate_sheet(xls, EXCEL_MAPPING["rate_sheet_candidates"])
    rates = pd.read_excel(xls, rate_sheet)
    rates.columns = [str(c).strip() for c in rates.columns]
    if "Date" not in rates.columns:
        rates = rates.rename(columns={rates.columns[0]: "Date"})
    rates["Date"] = pd.to_datetime(rates["Date"], errors="coerce")
    rates = rates.dropna(subset=["Date"])

    return fx, rates, missing
