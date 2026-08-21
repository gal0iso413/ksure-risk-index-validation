"""Nonparametric consistency statistics and verdicts."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

RATE_METRICS = [
    ("accident_rate", "has_accident", "사고율"),
    ("loss_ratio", "has_loss", "손해율"),
    ("real_loss_ratio", "has_real_loss", "실질손해율"),
]

# Core verdict targets. Size-like metrics skip incidence (value>0) in the verdict.
CORE_METRIC_KEYS = [
    "accident_rate",
    "loss_ratio",
    "real_loss_ratio",
    "country_grade",
    "exposure",
]
SIZE_METRIC_KEYS = frozenset({"country_grade", "exposure"})
SENSITIVITY_COHORTS = [
    "primary_ge_6m",
    "complete_12m",
    "all_matched",
    "primary_mean_ri",
    "primary_high_share",
]


def _spearman(x: pd.Series, y: pd.Series) -> tuple[float | None, float | None, int]:
    mask = x.notna() & y.notna()
    n = int(mask.sum())
    if n < 3 or x[mask].nunique() < 2 or y[mask].nunique() < 2:
        return None, None, n
    r, p = stats.spearmanr(x[mask], y[mask])
    if np.isnan(r):
        return None, None, n
    return float(r), float(p), n


def _bootstrap_spearman(
    x: np.ndarray,
    y: np.ndarray,
    rng: np.random.Generator,
    n_boot: int,
) -> tuple[float | None, float | None]:
    n = len(x)
    if n < 3:
        return None, None
    stats_boot = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        xb, yb = x[idx], y[idx]
        if len(np.unique(xb)) < 2 or len(np.unique(yb)) < 2:
            continue
        r, _ = stats.spearmanr(xb, yb)
        if not np.isnan(r):
            stats_boot.append(r)
    if len(stats_boot) < max(50, n_boot // 10):
        return None, None
    lo, hi = np.percentile(stats_boot, [2.5, 97.5])
    return float(lo), float(hi)


def _kruskal_eps2(groups: list[np.ndarray]) -> tuple[float | None, float | None, float | None]:
    clean = [g[~np.isnan(g)] for g in groups if len(g) and not np.all(np.isnan(g))]
    clean = [g for g in clean if len(g) > 0]
    if len(clean) < 2:
        return None, None, None
    if sum(len(np.unique(g)) > 0 for g in clean) < 2:
        return None, None, None
    try:
        h, p = stats.kruskal(*clean)
    except ValueError:
        return None, None, None
    n = sum(len(g) for g in clean)
    if n < 3:
        return float(h), float(p), None
    eps2 = float(h) * (n + 1) / (n**2 - 1) if n > 1 else None
    return float(h), float(p), eps2


def _is_mostly_monotonic(values: list[float | None], increasing: bool) -> bool:
    nums = [v for v in values if v is not None and not np.isnan(v)]
    if len(nums) < 3:
        return False
    diffs = np.diff(nums)
    if increasing:
        return float(np.mean(diffs >= -1e-12)) >= 0.7
    return float(np.mean(diffs <= 1e-12)) >= 0.7


def _verdict(
    *,
    expected_positive: bool,
    rho: float | None,
    ci: tuple[float | None, float | None],
    mono_ok: bool,
    incidence_rho: float | None,
    positive_rho: float | None,
    sensitivity_signs: list[int],
    n: int,
    n_positive: int,
    min_n: int,
    pos_min: int,
    has_variation: bool,
) -> str:
    if n < min_n or not has_variation:
        return "Untestable"
    if rho is None and incidence_rho is None:
        return "Untestable"

    def sign(v: float | None) -> int:
        if v is None or np.isnan(v):
            return 0
        if v > 0.02:
            return 1
        if v < -0.02:
            return -1
        return 0

    want = 1 if expected_positive else -1
    main_s = sign(rho)
    lo, hi = ci
    ci_ok = False
    if lo is not None and hi is not None:
        if expected_positive:
            ci_ok = lo > 0 or (lo >= -0.05 and hi > 0 and main_s >= 0)
        else:
            ci_ok = hi < 0 or (hi <= 0.05 and lo < 0 and main_s <= 0)

    sens_ok = True
    nonzero = [s for s in sensitivity_signs if s != 0]
    if nonzero:
        sens_ok = all(s == want for s in nonzero) or (
            sum(1 for s in nonzero if s == want) >= len(nonzero) - 1
        )
        if any(s == -want for s in nonzero) and sum(1 for s in nonzero if s == -want) >= 2:
            return "Not supported"

    if main_s == -want:
        return "Not supported"
    if main_s == 0 and sign(incidence_rho) == 0 and sign(positive_rho) == 0:
        return "Not supported"

    strong = (
        main_s == want
        and ci_ok
        and mono_ok
        and sens_ok
    )
    if strong:
        return "Supported"

    partial = (
        main_s == want
        or sign(incidence_rho) == want
        or (n_positive >= pos_min and sign(positive_rho) == want)
    )
    if partial and sens_ok:
        return "Partially supported"
    if partial and not sens_ok:
        return "Partially supported"
    return "Not supported"


def _ri_level(series: pd.Series) -> pd.Series:
    # Round annual median to nearest RI class for grouping displays
    return series.round().clip(1, 5).astype("Int64")


def analyze_cohort(
    df: pd.DataFrame,
    cfg: dict[str, Any],
    rng: np.random.Generator,
    cohort_name: str,
    ri_col: str = "ri_annual_median",
) -> dict[str, Any]:
    min_n = int(cfg["analysis"]["min_countries_testable"])
    pos_min = int(cfg["analysis"]["positive_subset_min_n"])
    n_boot = int(cfg["analysis"]["bootstrap_n"])
    expected_positive = bool(cfg.get("ri_higher_means_riskier", True))

    out: dict[str, Any] = {"cohort": cohort_name, "ri_col": ri_col, "n": int(len(df))}
    if df.empty:
        out["verdicts"] = {}
        return out

    work = df.copy()
    if ri_col == "ri_high_month_share":
        # map 0–1 share onto pseudo RI levels for descriptive tables only
        work["ri_level"] = (
            (work[ri_col] * 4 + 1).round().clip(1, 5).astype("Int64")
        )
    else:
        work["ri_level"] = _ri_level(work[ri_col])
    for col, flag, _ in RATE_METRICS:
        work[flag] = np.where(work[col].isna(), np.nan, (work[col] > 0).astype(float))

    metric_results = {}
    for col, flag, label in RATE_METRICS:
        rho, pval, n = _spearman(work[ri_col], work[col])
        mask = work[ri_col].notna() & work[col].notna()
        ci = (None, None)
        if mask.sum() >= 3:
            ci = _bootstrap_spearman(
                work.loc[mask, ri_col].to_numpy(float),
                work.loc[mask, col].to_numpy(float),
                rng,
                n_boot,
            )

        # by RI level descriptive
        desc_rows = []
        groups = []
        levels = sorted([int(x) for x in work["ri_level"].dropna().unique()])
        for lvl in levels:
            sub = work[work["ri_level"] == lvl][col]
            groups.append(sub.to_numpy(float))
            desc_rows.append(
                {
                    "ri_level": lvl,
                    "n": int(sub.notna().sum()),
                    "median": float(sub.median()) if sub.notna().any() else None,
                    "mean": float(sub.mean()) if sub.notna().any() else None,
                    "q1": float(sub.quantile(0.25)) if sub.notna().any() else None,
                    "q3": float(sub.quantile(0.75)) if sub.notna().any() else None,
                    "zero_share": float((sub == 0).mean()) if sub.notna().any() else None,
                    "positive_share": float((sub > 0).mean()) if sub.notna().any() else None,
                    "n_positive": int((sub > 0).sum()),
                }
            )
        h, hp, eps2 = _kruskal_eps2(groups)
        mono = _is_mostly_monotonic([r["median"] for r in desc_rows], expected_positive)

        # incidence
        inc_rho, inc_p, inc_n = _spearman(work[ri_col], work[flag])
        pos = work[work[col] > 0]
        if len(pos) < pos_min:
            pos_rho, pos_p, pos_n = None, None, int(len(pos))
            pos_status = "Untestable"
        else:
            pos_rho, pos_p, pos_n = _spearman(pos[ri_col], pos[col])
            pos_status = "ok"

        metric_results[col] = {
            "label": label,
            "spearman_rho": rho,
            "spearman_p": pval,
            "n": n,
            "ci95": {"low": ci[0], "high": ci[1]},
            "kruskal_h": h,
            "kruskal_p": hp,
            "epsilon_squared": eps2,
            "median_monotonic": mono,
            "by_ri_level": desc_rows,
            "incidence": {
                "spearman_rho": inc_rho,
                "spearman_p": inc_p,
                "n": inc_n,
            },
            "positive_subset": {
                "status": pos_status,
                "spearman_rho": pos_rho,
                "spearman_p": pos_p,
                "n": pos_n,
            },
        }

    # country grade
    g_rho, g_p, g_n = _spearman(work[ri_col], work["country_grade"])
    g_mask = work[ri_col].notna() & work["country_grade"].notna()
    g_ci = (None, None)
    if g_mask.sum() >= 3:
        g_ci = _bootstrap_spearman(
            work.loc[g_mask, ri_col].to_numpy(float),
            work.loc[g_mask, "country_grade"].to_numpy(float),
            rng,
            n_boot,
        )
    grade_desc = []
    for lvl in sorted([int(x) for x in work["ri_level"].dropna().unique()]):
        sub = work[work["ri_level"] == lvl]["country_grade"]
        grade_desc.append(
            {
                "ri_level": lvl,
                "n": int(sub.notna().sum()),
                "median": float(sub.median()) if sub.notna().any() else None,
                "mean": float(sub.mean()) if sub.notna().any() else None,
            }
        )
    cross = (
        pd.crosstab(work["ri_level"], work["country_grade"])
        if g_n > 0
        else pd.DataFrame()
    )
    metric_results["country_grade"] = {
        "label": "국가등급",
        "spearman_rho": g_rho,
        "spearman_p": g_p,
        "n": g_n,
        "ci95": {"low": g_ci[0], "high": g_ci[1]},
        "by_ri_level": grade_desc,
        "crosstab": cross.to_dict() if not cross.empty else {},
        "median_monotonic": _is_mostly_monotonic(
            [r["median"] for r in grade_desc], expected_positive
        ),
    }

    # exposure: core target (expected: higher RI → larger short-term exposure)
    e_rho, e_p, e_n = _spearman(work[ri_col], work["exposure"])
    e_mask = work[ri_col].notna() & work["exposure"].notna()
    e_ci = (None, None)
    if e_mask.sum() >= 3:
        e_ci = _bootstrap_spearman(
            work.loc[e_mask, ri_col].to_numpy(float),
            work.loc[e_mask, "exposure"].to_numpy(float),
            rng,
            n_boot,
        )
    exp_desc = []
    exp_groups = []
    for lvl in sorted([int(x) for x in work["ri_level"].dropna().unique()]):
        sub = work[work["ri_level"] == lvl]["exposure"]
        exp_groups.append(sub.to_numpy(float))
        exp_desc.append(
            {
                "ri_level": lvl,
                "n": int(sub.notna().sum()),
                "median": float(sub.median()) if sub.notna().any() else None,
                "mean": float(sub.mean()) if sub.notna().any() else None,
            }
        )
    e_h, e_hp, e_eps2 = _kruskal_eps2(exp_groups)
    metric_results["exposure"] = {
        "label": "미화국별총위험량(단기)",
        "spearman_rho": e_rho,
        "spearman_p": e_p,
        "n": e_n,
        "ci95": {"low": e_ci[0], "high": e_ci[1]},
        "kruskal_h": e_h,
        "kruskal_p": e_hp,
        "epsilon_squared": e_eps2,
        "by_ri_level": exp_desc,
        "median_monotonic": _is_mostly_monotonic(
            [r["median"] for r in exp_desc], expected_positive
        ),
        "missing_share": float(work["exposure"].isna().mean()) if len(work) else None,
    }

    out["metrics"] = metric_results
    out["ri_level_counts"] = (
        work["ri_level"].value_counts().sort_index().astype(int).to_dict()
    )
    return out


def run_validation(analysis: pd.DataFrame, cfg: dict[str, Any], rng: np.random.Generator) -> dict:
    min_months = int(cfg["analysis"]["minimum_months_primary"])
    complete = int(cfg["analysis"]["complete_year_months"])
    min_n = int(cfg["analysis"]["min_countries_testable"])
    pos_min = int(cfg["analysis"]["positive_subset_min_n"])
    expected_positive = bool(cfg.get("ri_higher_means_riskier", True))

    cohorts = {
        "primary_ge_6m": analysis[analysis["months_present"] >= min_months].copy(),
        "complete_12m": analysis[analysis["months_present"] >= complete].copy(),
        "all_matched": analysis.copy(),
    }

    results = {}
    for name, cdf in cohorts.items():
        results[name] = analyze_cohort(cdf, cfg, rng, name, "ri_annual_median")
        if name == "primary_ge_6m":
            results["primary_mean_ri"] = analyze_cohort(
                cdf, cfg, rng, "primary_mean_ri", "ri_annual_mean"
            )
            results["primary_high_share"] = analyze_cohort(
                cdf, cfg, rng, "primary_high_share", "ri_high_month_share"
            )

    # Verdicts on primary cohort with sensitivity signs
    primary = results["primary_ge_6m"]
    verdicts = {}
    for key in CORE_METRIC_KEYS:
        sens_signs = []
        for sens_name in SENSITIVITY_COHORTS:
            m = results[sens_name]["metrics"].get(key, {})
            rho = m.get("spearman_rho")
            if rho is None:
                continue
            if rho > 0.02:
                sens_signs.append(1)
            elif rho < -0.02:
                sens_signs.append(-1)
            else:
                sens_signs.append(0)

        pm = primary["metrics"][key]
        n = int(pm.get("n") or 0)
        n_pos = int(pm.get("positive_subset", {}).get("n") or 0)
        has_var = n >= 3 and len(primary.get("ri_level_counts", {})) >= 2
        ci = pm.get("ci95") or {}
        if key in SIZE_METRIC_KEYS:
            verdicts[key] = _verdict(
                expected_positive=expected_positive,
                rho=pm.get("spearman_rho"),
                ci=(ci.get("low"), ci.get("high")),
                mono_ok=bool(pm.get("median_monotonic")),
                incidence_rho=None,
                positive_rho=None,
                sensitivity_signs=sens_signs,
                n=n,
                n_positive=n,
                min_n=min_n,
                pos_min=pos_min,
                has_variation=has_var,
            )
        else:
            verdicts[key] = _verdict(
                expected_positive=expected_positive,
                rho=pm.get("spearman_rho"),
                ci=(ci.get("low"), ci.get("high")),
                mono_ok=bool(pm.get("median_monotonic")),
                incidence_rho=pm.get("incidence", {}).get("spearman_rho"),
                positive_rho=pm.get("positive_subset", {}).get("spearman_rho"),
                sensitivity_signs=sens_signs,
                n=n,
                n_positive=n_pos,
                min_n=min_n,
                pos_min=pos_min,
                has_variation=has_var,
            )
            if pm.get("positive_subset", {}).get("status") == "Untestable" and n < min_n:
                verdicts[key] = "Untestable"

    results["verdicts"] = verdicts
    results["primary_cohort_n"] = int(len(cohorts["primary_ge_6m"]))
    return results


def results_to_tables(results: dict) -> dict[str, pd.DataFrame]:
    rows = []
    for cohort, block in results.items():
        if not isinstance(block, dict) or "metrics" not in block:
            continue
        for key, m in block["metrics"].items():
            rows.append(
                {
                    "cohort": cohort,
                    "metric": key,
                    "label": m.get("label"),
                    "n": m.get("n"),
                    "spearman_rho": m.get("spearman_rho"),
                    "spearman_p": m.get("spearman_p"),
                    "ci_low": (m.get("ci95") or {}).get("low"),
                    "ci_high": (m.get("ci95") or {}).get("high"),
                    "kruskal_h": m.get("kruskal_h"),
                    "kruskal_p": m.get("kruskal_p"),
                    "epsilon_squared": m.get("epsilon_squared"),
                    "incidence_rho": (m.get("incidence") or {}).get("spearman_rho"),
                    "positive_n": (m.get("positive_subset") or {}).get("n"),
                    "positive_rho": (m.get("positive_subset") or {}).get("spearman_rho"),
                    "reference_only": m.get("reference_only", False),
                }
            )
    summary = pd.DataFrame(rows)
    verdict_df = pd.DataFrame(
        [{"metric": k, "verdict": v} for k, v in results.get("verdicts", {}).items()]
    )
    return {"statistical_results": summary, "verdicts": verdict_df}
