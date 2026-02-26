from __future__ import annotations

import pandas as pd


def scenario_summary_table(inputs: dict) -> pd.DataFrame:
    return pd.DataFrame({"assumption": list(inputs.keys()), "value": list(inputs.values())})
