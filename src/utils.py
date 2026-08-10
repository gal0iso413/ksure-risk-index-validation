"""Shared helpers for the RI consistency validation pipeline."""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

EXCEL_ERROR_TOKENS = {
    "#N/A",
    "#NA",
    "#VALUE!",
    "#REF!",
    "#DIV/0!",
    "#NUM!",
    "#NAME?",
    "#NULL!",
}


class PipelineError(RuntimeError):
    """Hard quality-gate failure; abort the run."""


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_config(path: str | Path) -> dict[str, Any]:
    cfg_path = Path(path)
    if not cfg_path.is_absolute():
        cfg_path = project_root() / cfg_path
    with cfg_path.open(encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["_config_path"] = str(cfg_path)
    cfg["_config_dir"] = str(cfg_path.parent)
    cfg["_root"] = str(project_root())
    return cfg


def resolve_path(cfg: dict[str, Any], maybe_relative: str) -> Path:
    p = Path(maybe_relative)
    if p.is_absolute():
        return p
    return Path(cfg["_root"]) / p


def setup_logging(output_dir: Path) -> logging.Logger:
    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "run_summary.log"
    logger = logging.getLogger("ri_validation")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def excel_header_to_pandas(excel_header_row: int) -> int:
    """Convert 1-based Excel row number to pandas header index."""
    if excel_header_row < 1:
        raise PipelineError(f"excel_header_row must be >= 1, got {excel_header_row}")
    return excel_header_row - 1


def normalize_country_name(value: Any) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    text = str(value).replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_country_name_map(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    mappings = raw.get("mappings", raw)
    return {
        normalize_country_name(k): normalize_country_name(v)
        for k, v in mappings.items()
        if normalize_country_name(k)
    }


def apply_country_name_map(name: str, mapping: dict[str, str]) -> str:
    return mapping.get(name, name)


def is_excel_error(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and np.isnan(value):
        return False
    text = str(value).strip().upper()
    return text in {t.upper() for t in EXCEL_ERROR_TOKENS}


def to_numeric_or_na(series: pd.Series) -> pd.Series:
    """Convert to float; Excel errors and blanks → NA; keep true zeros."""

    def _one(v: Any):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return np.nan
        if isinstance(v, str) and not v.strip():
            return np.nan
        if is_excel_error(v):
            return np.nan
        if isinstance(v, (int, float, np.integer, np.floating)):
            return float(v)
        text = str(v).strip().replace(",", "")
        if not text or is_excel_error(text):
            return np.nan
        try:
            return float(text)
        except ValueError:
            return np.nan

    return series.map(_one).astype("float64")


def parse_ri_value(value: Any) -> float:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    text = str(value).strip()
    if not text:
        return np.nan
    m = re.fullmatch(r"RI\s*([1-5])", text, flags=re.IGNORECASE)
    if not m:
        raise PipelineError(f"Invalid Risk Index value: {value!r}")
    return float(m.group(1))


def extract_month_from_filename(path: Path, year: int) -> int:
    name = path.name
    if name.startswith("~$"):
        raise PipelineError(f"Temporary Excel lock file must be excluded: {name}")
    m = re.search(rf"{year}년\s*(\d{{1,2}})월", name)
    if not m:
        m = re.search(r"(\d{1,2})월", name)
    if not m:
        raise PipelineError(f"Cannot extract month from RI filename: {name}")
    month = int(m.group(1))
    if month < 1 or month > 12:
        raise PipelineError(f"Month out of range in {name}: {month}")
    return month


def mode_or_nan(values: pd.Series) -> float:
    clean = values.dropna()
    if clean.empty:
        return np.nan
    modes = clean.mode(dropna=True)
    if modes.empty:
        return np.nan
    return float(modes.iloc[0])


def ensure_output_dirs(output_dir: Path) -> dict[str, Path]:
    paths = {
        "root": output_dir,
        "tables": output_dir / "tables",
        "figures": output_dir / "figures",
        "logs": output_dir / "logs",
        "report": output_dir / "report",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def write_excel(df: pd.DataFrame, path: Path, sheet_name: str = "Sheet1") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False, sheet_name=sheet_name)


def set_seed(seed: int) -> np.random.Generator:
    return np.random.default_rng(int(seed))
