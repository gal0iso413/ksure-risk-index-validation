"""Country-name matching between RI and target tables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .utils import (
    apply_country_name_map,
    load_country_name_map,
    normalize_country_name,
    resolve_path,
    write_excel,
)


def match_countries(
    ri_country: pd.DataFrame,
    target: pd.DataFrame,
    cfg: dict[str, Any],
    out_tables: Path,
    logger,
) -> tuple[pd.DataFrame, dict]:
    map_path = resolve_path(cfg, cfg["paths"].get("country_name_map", "config/country_name_map.json"))
    mapping = load_country_name_map(map_path if map_path.exists() else None)

    ri = ri_country.copy()
    tgt = target.copy()
    ri["country_key"] = ri["country_name"].map(
        lambda x: apply_country_name_map(normalize_country_name(x), mapping)
    )
    tgt["country_key"] = tgt["country_name"].map(
        lambda x: apply_country_name_map(normalize_country_name(x), mapping)
    )

    # Detect one name → many codes in RI
    name_code = (
        ri.groupby("country_key")["country_code"].nunique().reset_index(name="n_codes")
    )
    multi_code = name_code[name_code["n_codes"] > 1]

    ri_keys = set(ri["country_key"])
    tgt_keys = set(tgt["country_key"])
    matched = ri_keys & tgt_keys
    only_ri = sorted(ri_keys - tgt_keys)
    only_tgt = sorted(tgt_keys - ri_keys)

    unmatched = pd.DataFrame(
        {
            "country_key": only_ri + only_tgt,
            "side": ["ri_only"] * len(only_ri) + ["target_only"] * len(only_tgt),
        }
    )
    write_excel(unmatched, out_tables / "unmatched_countries.xlsx")

    analysis = ri.merge(
        tgt.drop(columns=["country_name"]),
        on="country_key",
        how="inner",
        validate="one_to_one",
    )
    # Prefer RI country_name; keep key
    analysis = analysis.rename(columns={"country_key": "country_name_matched"})
    analysis["country_name"] = analysis["country_name"]

    coverage = {
        "n_ri_countries": int(len(ri_keys)),
        "n_target_countries": int(len(tgt_keys)),
        "n_matched": int(len(matched)),
        "match_rate_ri": float(len(matched) / len(ri_keys)) if ri_keys else None,
        "match_rate_target": float(len(matched) / len(tgt_keys)) if tgt_keys else None,
        "only_ri": only_ri,
        "only_target": only_tgt,
        "multi_code_country_names": multi_code["country_key"].tolist(),
        "country_name_map_used": bool(mapping),
    }
    logger.info(
        "Country match: ri=%d target=%d matched=%d (ri_rate=%.3f target_rate=%.3f)",
        coverage["n_ri_countries"],
        coverage["n_target_countries"],
        coverage["n_matched"],
        coverage["match_rate_ri"] or 0,
        coverage["match_rate_target"] or 0,
    )
    return analysis, coverage
