"""Aggregate RI from country×industry×month → country×month → country×year."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .utils import mode_or_nan


def aggregate_country_month(ri: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rows = []
    mixed = 0
    for (country, code, month), g in ri.groupby(
        ["country_name", "country_code", "month"], sort=False
    ):
        uniq = g["ri"].nunique(dropna=True)
        if uniq > 1:
            mixed += 1
            month_ri = float(g["ri"].median())
        else:
            month_ri = float(g["ri"].iloc[0])
        rows.append(
            {
                "country_name": country,
                "country_code": code,
                "month": int(month),
                "industry_rows": int(len(g)),
                "n_industries": int(g["industry_code"].nunique()),
                "ri_nunique": int(uniq),
                "ri_month": month_ri,
                "ri_month_median": float(g["ri"].median()),
                "ri_month_mean": float(g["ri"].mean()),
                "ri_month_mode": mode_or_nan(g["ri"]),
                "ri_month_min": float(g["ri"].min()),
                "ri_month_max": float(g["ri"].max()),
                "ri_high_industry_share": float((g["ri"] >= 4).mean()),
            }
        )
    cm = pd.DataFrame(rows)
    quality = {
        "n_country_month": int(len(cm)),
        "n_mixed_ri_country_month": int(mixed),
        "mixed_ri_share": float(mixed / len(cm)) if len(cm) else None,
    }
    return cm, quality


def aggregate_country_year(cm: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (country, code), g in cm.groupby(["country_name", "country_code"], sort=False):
        g = g.sort_values("month")
        months_present = int(g["month"].nunique())
        ri_series = g["ri_month"]
        # change count: adjacent month differences
        changes = int((ri_series.diff().fillna(0) != 0).sum())
        rows.append(
            {
                "country_name": country,
                "country_code": code,
                "months_present": months_present,
                "industry_rows_total": int(g["industry_rows"].sum()),
                "ri_annual_median": float(ri_series.median()),
                "ri_annual_mean": float(ri_series.mean()),
                "ri_annual_mode": mode_or_nan(ri_series),
                "ri_annual_min": float(ri_series.min()),
                "ri_annual_max": float(ri_series.max()),
                "ri_high_month_share": float((ri_series >= 4).mean()),
                "ri_high_industry_share": float(
                    np.average(g["ri_high_industry_share"], weights=g["industry_rows"])
                    if g["industry_rows"].sum() > 0
                    else np.nan
                ),
                "ri_change_count": changes,
            }
        )
    return pd.DataFrame(rows)
