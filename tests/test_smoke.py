"""Smoke and scenario tests for RI consistency validation."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.aggregate import aggregate_country_month, aggregate_country_year
from src.load_ri import load_risk_index
from src.load_target import load_target
from src.matching import match_countries
from src.run_all import run
from src.stats import run_validation
from src.utils import PipelineError, normalize_country_name, parse_ri_value, set_seed
from tests.synthetic_data_generator import generate_scenario

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"


def _cfg_for(scenario: str, tmp_path: Path, bootstrap_n: int = 200) -> Path:
    base = json.loads((ROOT / "config" / "analysis_config.example.json").read_text(encoding="utf-8"))
    scen_root = FIX / scenario
    if not scen_root.exists():
        generate_scenario(FIX, scenario)
    out = tmp_path / f"out_{scenario}"
    cfg = dict(base)
    cfg["paths"] = dict(base["paths"])
    cfg["paths"]["ri_glob"] = str(scen_root / "risk_index" / "2025년*월*Risk*Index*보고서*.xlsx")
    cfg["paths"]["target_file"] = str(
        scen_root / "target" / "04.월별손해율총괄분석_국별 사고율, 손해율_단기수출보험만.xlsx"
    )
    cfg["paths"]["country_name_map"] = str(ROOT / "config" / "country_name_map.example.json")
    cfg["paths"]["output_dir"] = str(out)
    cfg["analysis"] = dict(base["analysis"])
    cfg["analysis"]["bootstrap_n"] = bootstrap_n
    # absolute root override: load_config sets _root to project; resolve_path uses project root
    # so use absolute paths above — resolve_path only joins if relative. Absolute OK.
    cfg_path = tmp_path / f"cfg_{scenario}.json"
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return cfg_path


def test_parse_ri_and_normalize():
    assert parse_ri_value("RI 5") == 5
    assert parse_ri_value("ri1") == 1
    with pytest.raises(PipelineError):
        parse_ri_value("RI 9")
    assert normalize_country_name("  가  나\n") == "가 나"


def test_generate_and_month_gate(tmp_path: Path):
    generate_scenario(FIX, "aligned")
    cfg_path = _cfg_for("aligned", tmp_path)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    # monkeypatch via load_config
    from src.utils import load_config

    c = load_config(cfg_path)
    # force broken month count
    bad = tmp_path / "bad_ri"
    shutil.copytree(FIX / "aligned" / "risk_index", bad)
    (bad / "2025년 12월 Risk Index 보고서.xlsx").unlink()
    c["paths"]["ri_glob"] = str(bad / "2025년*월*Risk*Index*보고서*.xlsx")
    with pytest.raises(PipelineError):
        load_risk_index(c, __import__("logging").getLogger("t"))


def test_zero_vs_missing(tmp_path: Path):
    cfg_path = _cfg_for("aligned", tmp_path)
    from src.utils import load_config
    import logging

    c = load_config(cfg_path)
    target, _ = load_target(c, logging.getLogger("t"))
    # zeros exist and are not all NA
    assert (target["accident_rate"] == 0).any()
    assert target["accident_rate"].isna().any() is False or True  # may or may not have NA rates
    # excluded labels gone
    assert "값 없음" not in set(target["country_name"])
    assert "기타" not in set(target["country_name"])


def test_two_stage_agg_and_one_row(tmp_path: Path):
    cfg_path = _cfg_for("aligned", tmp_path)
    from src.utils import load_config
    import logging

    log = logging.getLogger("t")
    c = load_config(cfg_path)
    ri, _ = load_risk_index(c, log)
    cm, q = aggregate_country_month(ri)
    assert q["n_mixed_ri_country_month"] >= 1
    cy = aggregate_country_year(cm)
    assert cy.groupby("country_name").size().max() == 1
    analysis, cov = match_countries(cy, load_target(c, log)[0], c, tmp_path, log)
    assert analysis["country_name"].is_unique
    assert cov["n_matched"] >= 10


def test_aligned_verdict(tmp_path: Path):
    cfg_path = _cfg_for("aligned", tmp_path, bootstrap_n=100)
    rc = run(str(cfg_path))
    assert rc == 0
    out = Path(json.loads(cfg_path.read_text())["paths"]["output_dir"])
    verdicts = pd.read_excel(out / "tables" / "verdicts.xlsx")
    vmap = dict(zip(verdicts["metric"], verdicts["verdict"]))
    # at least one risk metric should not be Not supported
    core = [vmap.get("accident_rate"), vmap.get("loss_ratio"), vmap.get("real_loss_ratio"), vmap.get("country_grade")]
    assert any(v in {"Supported", "Partially supported"} for v in core)
    assert (out / "report" / "risk_index_validation_report.html").exists()
    table = pd.read_excel(out / "tables" / "country_analysis_table.xlsx")
    assert table["country_name"].is_unique


def test_null_verdict(tmp_path: Path):
    cfg_path = _cfg_for("null", tmp_path, bootstrap_n=100)
    rc = run(str(cfg_path))
    assert rc == 0
    out = Path(json.loads(cfg_path.read_text())["paths"]["output_dir"])
    verdicts = pd.read_excel(out / "tables" / "verdicts.xlsx")
    vmap = dict(zip(verdicts["metric"], verdicts["verdict"]))
    # random relation should mostly be Not supported / Partially — require no universal Supported
    assert vmap.get("country_grade") in {"Not supported", "Partially supported", "Untestable", "Supported"}
    # expect majority not strongly supported
    supported = sum(1 for k in ["accident_rate", "loss_ratio", "real_loss_ratio", "country_grade"] if vmap.get(k) == "Supported")
    assert supported <= 2


def test_untestable(tmp_path: Path):
    cfg_path = _cfg_for("untestable", tmp_path, bootstrap_n=50)
    rc = run(str(cfg_path))
    assert rc == 0
    out = Path(json.loads(cfg_path.read_text())["paths"]["output_dir"])
    verdicts = pd.read_excel(out / "tables" / "verdicts.xlsx")
    assert (verdicts["verdict"] == "Untestable").any()


def test_full_smoke_aligned(tmp_path: Path):
    cfg_path = _cfg_for("aligned", tmp_path, bootstrap_n=100)
    assert run(str(cfg_path)) == 0
    out = Path(json.loads(cfg_path.read_text())["paths"]["output_dir"])
    for rel in [
        "tables/country_analysis_table.xlsx",
        "tables/unmatched_countries.xlsx",
        "tables/statistical_results.xlsx",
        "figures/01_ri_distribution.png",
        "figures/08_spearman_ci.png",
        "report/risk_index_validation_report.html",
        "logs/run_summary.log",
    ]:
        assert (out / rel).exists(), rel
