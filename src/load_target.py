"""Load 2025 annual target validation sheet (short-term export insurance)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from openpyxl import load_workbook

from .utils import (
    PipelineError,
    excel_header_to_pandas,
    is_excel_error,
    normalize_country_name,
    resolve_path,
    to_numeric_or_na,
)


def _normalize_header(text: str) -> str:
    return " ".join(str(text).replace("\n", " ").split())


def _read_with_cached_values(path, sheet: str, header_row: int, usecols: str) -> pd.DataFrame:
    wb = load_workbook(path, read_only=True, data_only=True)
    if sheet not in wb.sheetnames:
        wb.close()
        raise PipelineError(f"Sheet {sheet!r} not found in {path.name}")
    ws = wb[sheet]

    # usecols like "F:K" → 6..11 (1-based)
    start_s, end_s = usecols.split(":")
    start_idx = pd.Index([start_s]).map(lambda c: openpyxl_col_index(c))[0]
    end_idx = pd.Index([end_s]).map(lambda c: openpyxl_col_index(c))[0]

    header_excel_row = header_row + 1  # pandas 0-based → Excel 1-based already passed converted
    # header_row is pandas index; Excel row = header_row + 1
    excel_header = header_row + 1
    headers = []
    for col in range(start_idx, end_idx + 1):
        cell = ws.cell(excel_header, col)
        val = cell.value
        if isinstance(val, str) and val.startswith("="):
            wb.close()
            raise PipelineError(
                f"Header cell {cell.coordinate} is a formula without usable cached value"
            )
        headers.append(_normalize_header(val if val is not None else f"col_{col}"))

    rows = []
    formula_without_cache = []
    max_row = ws.max_row or excel_header
    for r in range(excel_header + 1, max_row + 1):
        values = []
        empty = True
        for col in range(start_idx, end_idx + 1):
            cell = ws.cell(r, col)
            val = cell.value
            if isinstance(val, str) and val.startswith("="):
                formula_without_cache.append(cell.coordinate)
                val = None
            if val is not None and not (isinstance(val, str) and not str(val).strip()):
                empty = False
            values.append(val)
        if empty:
            continue
        rows.append(values)
    wb.close()

    if formula_without_cache:
        raise PipelineError(
            "Formula cells without cached values in target sheet: "
            + ", ".join(formula_without_cache[:20])
        )

    return pd.DataFrame(rows, columns=headers)


def openpyxl_col_index(col_letters: str) -> int:
    col_letters = col_letters.strip().upper()
    n = 0
    for ch in col_letters:
        if not ("A" <= ch <= "Z"):
            raise PipelineError(f"Invalid column letter: {col_letters}")
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n


def load_target(cfg: dict[str, Any], logger) -> tuple[pd.DataFrame, dict]:
    path = resolve_path(cfg, cfg["paths"]["target_file"])
    if not path.exists():
        raise PipelineError(f"Target file not found: {path}")

    tex = cfg["target_excel"]
    sheet = tex["sheet_name"]
    header_pd = excel_header_to_pandas(int(tex["excel_header_row"]))
    usecols = tex["usecols"]
    expected = [_normalize_header(h) for h in tex["expected_headers"]]
    exclude = {
        normalize_country_name(x) for x in tex.get("exclude_country_names", [])
    }

    df = _read_with_cached_values(path, sheet, header_pd, usecols)
    actual = [_normalize_header(c) for c in df.columns]
    if actual != expected:
        # Allow minor spacing differences already normalized; still fail on mismatch
        raise PipelineError(
            f"Unexpected target headers: got {actual}, expected {expected}"
        )

    rename = {
        expected[0]: "country_name_raw",
        expected[1]: "country_grade",
        expected[2]: "accident_rate",
        expected[3]: "loss_ratio",
        expected[4]: "real_loss_ratio",
        expected[5]: "exposure",
    }
    df = df.rename(columns=rename)
    df["country_name"] = df["country_name_raw"].map(normalize_country_name)

    # Drop excluded / blank labels
    before = len(df)
    df = df[~df["country_name"].isin(exclude) & (df["country_name"] != "")].copy()
    dropped_excl = before - len(df)

    # Convert metrics: errors → NA; keep zeros
    for col in ("country_grade", "accident_rate", "loss_ratio", "real_loss_ratio", "exposure"):
        # Mark excel errors before numeric conversion
        err_mask = df[col].map(is_excel_error)
        df.loc[err_mask, col] = np.nan
        df[col] = to_numeric_or_na(df[col])

    if df[["accident_rate", "loss_ratio", "real_loss_ratio"]].isna().all().all() is False:
        # Ensure columns are numeric dtype
        for col in ("accident_rate", "loss_ratio", "real_loss_ratio", "exposure"):
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise PipelineError(f"Rate/exposure column not numeric: {col}")

    # Country grade hard gate for non-missing values
    grades = df["country_grade"].dropna()
    if not grades.empty:
        bad = grades[(grades < 1) | (grades > 7) | (grades != grades.round(0))]
        if not bad.empty:
            raise PipelineError(
                f"country_grade outside integer 1–7: examples {bad.head(5).tolist()}"
            )
        df.loc[df["country_grade"].notna(), "country_grade"] = df.loc[
            df["country_grade"].notna(), "country_grade"
        ].round(0)

    # Duplicate country names are a hard fail
    dup = df["country_name"][df["country_name"].duplicated(keep=False)]
    if not dup.empty:
        raise PipelineError(
            "Duplicate country names in target sheet: "
            + ", ".join(sorted(dup.unique().tolist())[:20])
        )

    # Unit profiling (do not rescale)
    rate_cols = ["accident_rate", "loss_ratio", "real_loss_ratio"]
    unit_profile = {}
    for col in rate_cols:
        s = df[col].dropna()
        unit_profile[col] = {
            "n": int(s.shape[0]),
            "min": float(s.min()) if not s.empty else None,
            "median": float(s.median()) if not s.empty else None,
            "max": float(s.max()) if not s.empty else None,
            "zero_share": float((s == 0).mean()) if not s.empty else None,
            "reported_unit": cfg.get("units", {}).get(
                "rate_unit_label", "percentage points"
            ),
            "rescaled": False,
        }

    profile = {
        "n_rows_raw_kept": int(len(df)),
        "n_excluded_labels": int(dropped_excl),
        "n_countries": int(df["country_name"].nunique()),
        "missing_grade_share": float(df["country_grade"].isna().mean()) if len(df) else None,
        "unit_profile": unit_profile,
        "note": "Values read as cached XLSX numbers; header % not used to rescale.",
    }
    logger.info(
        "Loaded target %s countries=%d excluded_labels=%d",
        path.name,
        profile["n_countries"],
        dropped_excl,
    )
    return df[
        [
            "country_name",
            "country_grade",
            "accident_rate",
            "loss_ratio",
            "real_loss_ratio",
            "exposure",
        ]
    ], profile
