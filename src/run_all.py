"""Pipeline entrypoint: inspect → validate → aggregate → join → stats → figures → report."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

import pandas as pd

from .aggregate import aggregate_country_month, aggregate_country_year
from .figures import make_figures
from .load_ri import load_risk_index
from .load_target import load_target
from .matching import match_countries
from .report import make_report
from .stats import results_to_tables, run_validation
from .utils import (
    PipelineError,
    ensure_output_dirs,
    load_config,
    resolve_path,
    set_seed,
    setup_logging,
    write_excel,
)


def run(config_path: str) -> int:
    cfg = load_config(config_path)
    out_dir = resolve_path(cfg, cfg["paths"]["output_dir"])
    paths = ensure_output_dirs(out_dir)
    logger = setup_logging(out_dir)
    rng = set_seed(int(cfg.get("seed", 42)))

    try:
        logger.info("Starting RI validation year=%s", cfg.get("analysis_year"))
        ri, ri_profile = load_risk_index(cfg, logger)
        target, target_profile = load_target(cfg, logger)

        cm, cm_quality = aggregate_country_month(ri)
        cy = aggregate_country_year(cm)

        analysis, coverage = match_countries(
            cy, target, cfg, paths["tables"], logger
        )

        # Final country-level analysis table
        col_order = [
            "country_name",
            "country_code",
            "months_present",
            "industry_rows_total",
            "ri_annual_median",
            "ri_annual_mean",
            "ri_annual_mode",
            "ri_annual_min",
            "ri_annual_max",
            "ri_high_month_share",
            "ri_high_industry_share",
            "ri_change_count",
            "country_grade",
            "accident_rate",
            "loss_ratio",
            "real_loss_ratio",
            "exposure",
        ]
        # Ensure required columns exist
        for c in col_order:
            if c not in analysis.columns:
                analysis[c] = pd.NA
        final = analysis[col_order].copy()
        if final["country_name"].duplicated().any():
            raise PipelineError("Final analysis table has duplicate country_name")
        write_excel(final, paths["tables"] / "country_analysis_table.xlsx")

        # Quality / profile outputs
        write_excel(cm, paths["tables"] / "ri_country_month.xlsx")
        profile_rows = []
        for k, v in {**ri_profile, **{f"target_{kk}": vv for kk, vv in target_profile.items() if kk != "unit_profile"}}.items():
            profile_rows.append({"key": k, "value": json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v})
        write_excel(pd.DataFrame(profile_rows), paths["tables"] / "data_profile.xlsx")
        write_excel(pd.DataFrame([cm_quality]), paths["tables"] / "ri_mix_quality.xlsx")
        cov_row = {
            k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v)
            for k, v in coverage.items()
        }
        write_excel(pd.DataFrame([cov_row]), paths["tables"] / "join_coverage.xlsx")

        unit_rows = []
        for col, info in target_profile.get("unit_profile", {}).items():
            unit_rows.append({"metric": col, **info})
        write_excel(pd.DataFrame(unit_rows), paths["tables"] / "rate_unit_profile.xlsx")

        results = run_validation(final, cfg, rng)
        tables = results_to_tables(results)
        write_excel(tables["statistical_results"], paths["tables"] / "statistical_results.xlsx")
        write_excel(tables["verdicts"], paths["tables"] / "verdicts.xlsx")

        figs = make_figures(
            final,
            coverage,
            results,
            paths["figures"],
            int(cfg["analysis"]["minimum_months_primary"]),
        )
        report_path = make_report(
            cfg=cfg,
            profiles={"ri": ri_profile, "target": target_profile},
            coverage=coverage,
            quality=cm_quality,
            results=results,
            figure_paths=figs,
            analysis=final,
            figure_dir=paths["figures"],
            out_dir=paths["report"],
        )
        logger.info("Report written: %s", report_path)
        logger.info("Verdicts: %s", results.get("verdicts"))
        return 0
    except PipelineError as exc:
        logger.error("QUALITY GATE FAIL: %s", exc)
        return 1
    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected failure: %s", exc)
        logger.error(traceback.format_exc())
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="국가 Risk Index 정합성 검증 파이프라인")
    parser.add_argument("--config", required=True, help="path to analysis_config.json")
    args = parser.parse_args(argv)
    return run(args.config)


if __name__ == "__main__":
    raise SystemExit(main())
