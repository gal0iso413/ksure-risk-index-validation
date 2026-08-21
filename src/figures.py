"""Static PNG figures for the offline report."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .stats import CORE_METRIC_KEYS, RATE_METRICS


def _setup_font() -> None:
    candidates = [
        "Malgun Gothic",
        "맑은 고딕",
        "NanumGothic",
        "AppleGothic",
        "DejaVu Sans",
    ]
    from matplotlib import font_manager

    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False


def make_figures(
    analysis: pd.DataFrame,
    coverage: dict,
    results: dict,
    fig_dir: Path,
    primary_min_months: int,
) -> list[Path]:
    _setup_font()
    fig_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    primary = analysis[analysis["months_present"] >= primary_min_months].copy()
    primary["ri_level"] = primary["ri_annual_median"].round().clip(1, 5)

    # 1. RI distribution
    fig, ax = plt.subplots(figsize=(7, 4))
    vc = primary["ri_level"].value_counts().sort_index()
    ax.bar(vc.index.astype(str), vc.values, color="#4C6A7A")
    ax.set_title(f"2025 국가별 RI 분포 (주분석, ≥{primary_min_months}개월, n={len(primary)})")
    ax.set_xlabel("RI (연간 중앙값 반올림)")
    ax.set_ylabel("국가 수")
    p = fig_dir / "01_ri_distribution.png"
    fig.tight_layout()
    fig.savefig(p, dpi=120)
    plt.close(fig)
    paths.append(p)

    # 2. months present
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(analysis["months_present"], bins=np.arange(0.5, 13.5, 1), color="#7A8F6A", edgecolor="white")
    ax.set_title(f"국가별 RI 관측 월 수 (매칭 국가 n={len(analysis)})")
    ax.set_xlabel("관측 월 수")
    ax.set_ylabel("국가 수")
    p = fig_dir / "02_months_present.png"
    fig.tight_layout()
    fig.savefig(p, dpi=120)
    plt.close(fig)
    paths.append(p)

    # 3. RI × country grade
    fig, ax = plt.subplots(figsize=(7, 4))
    sub = primary.dropna(subset=["country_grade", "ri_level"])
    if not sub.empty:
        for lvl, g in sub.groupby("ri_level"):
            ax.scatter(
                np.full(len(g), float(lvl)) + np.random.default_rng(0).uniform(-0.1, 0.1, len(g)),
                g["country_grade"],
                alpha=0.6,
                s=20,
                label=f"RI {int(lvl)}",
            )
        ax.set_xlabel("RI")
        ax.set_ylabel("국가등급 (클수록 고위험)")
    ax.set_title("RI별 국가등급 분포")
    p = fig_dir / "03_ri_country_grade.png"
    fig.tight_layout()
    fig.savefig(p, dpi=120)
    plt.close(fig)
    paths.append(p)

    # 4-6 incidence rates
    for i, (col, flag, label) in enumerate(RATE_METRICS, start=4):
        fig, ax = plt.subplots(figsize=(7, 4))
        rates = []
        labels = []
        for lvl in sorted(primary["ri_level"].dropna().unique()):
            s = primary.loc[primary["ri_level"] == lvl, col]
            s = s.dropna()
            labels.append(str(int(lvl)))
            rates.append(float((s > 0).mean()) if len(s) else np.nan)
        ax.bar(labels, rates, color="#A65D4E")
        ax.set_ylim(0, 1)
        ax.set_title(f"RI별 {label} 발생 국가 비율 (값>0, n={len(primary)})")
        ax.set_xlabel("RI")
        ax.set_ylabel("발생 비율")
        p = fig_dir / f"0{i}_incidence_{col}.png"
        fig.tight_layout()
        fig.savefig(p, dpi=120)
        plt.close(fig)
        paths.append(p)

    # 7 positive-only boxplots
    fig, axes = plt.subplots(1, 3, figsize=(11, 4))
    for ax, (col, _, label) in zip(axes, RATE_METRICS):
        pos = primary[primary[col] > 0].copy()
        if pos.empty:
            ax.set_title(f"{label} 양수 없음")
            continue
        data = [
            pos.loc[pos["ri_level"] == lvl, col].dropna().values
            for lvl in sorted(pos["ri_level"].dropna().unique())
        ]
        labels = [str(int(lvl)) for lvl in sorted(pos["ri_level"].dropna().unique())]
        ax.boxplot(data, tick_labels=labels, showfliers=True)
        ax.set_title(f"{label} (양수만, n={len(pos)})")
        ax.set_xlabel("RI")
    fig.suptitle("양수 국가 RI별 분포")
    p = fig_dir / "07_positive_distributions.png"
    fig.tight_layout()
    fig.savefig(p, dpi=120)
    plt.close(fig)
    paths.append(p)

    # 8 Spearman CI summary (five core targets)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    primary_metrics = results.get("primary_ge_6m", {}).get("metrics", {})
    names, rhos, los, his = [], [], [], []
    for key in CORE_METRIC_KEYS:
        m = primary_metrics.get(key, {})
        names.append(m.get("label", key))
        rhos.append(m.get("spearman_rho") if m.get("spearman_rho") is not None else 0)
        los.append((m.get("ci95") or {}).get("low") or 0)
        his.append((m.get("ci95") or {}).get("high") or 0)
    y = np.arange(len(names))
    ax.hlines(y, los, his, color="#333333")
    ax.plot(rhos, y, "o", color="#2F5D8A")
    ax.axvline(0, color="gray", lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.set_title("Spearman ρ 및 bootstrap 95% CI (주분석)")
    ax.set_xlabel("Spearman ρ")
    p = fig_dir / "08_spearman_ci.png"
    fig.tight_layout()
    fig.savefig(p, dpi=120)
    plt.close(fig)
    paths.append(p)

    # 9 matching
    fig, ax = plt.subplots(figsize=(6, 4))
    vals = [
        coverage.get("n_matched", 0),
        len(coverage.get("only_ri", [])),
        len(coverage.get("only_target", [])),
    ]
    ax.bar(["매칭", "RI만", "검증만"], vals, color=["#2F5D8A", "#A65D4E", "#C4A35A"])
    ax.set_title("국가 매칭·미매칭 수")
    ax.set_ylabel("국가 수")
    p = fig_dir / "09_matching.png"
    fig.tight_layout()
    fig.savefig(p, dpi=120)
    plt.close(fig)
    paths.append(p)

    # 10 exposure by RI (size metric; log y when values are large)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    exp = primary.dropna(subset=["exposure", "ri_level"])
    if exp.empty:
        ax.set_title("미화국별총위험량(단기) — 값 없음")
    else:
        levels = sorted(exp["ri_level"].dropna().unique())
        data = [exp.loc[exp["ri_level"] == lvl, "exposure"].to_numpy(float) for lvl in levels]
        labels = [str(int(lvl)) for lvl in levels]
        ax.boxplot(data, tick_labels=labels, showfliers=True)
        med = float(np.nanmedian(exp["exposure"].to_numpy(float)))
        if med >= 10_000:
            ax.set_yscale("log")
        ax.set_xlabel("RI")
        ax.set_ylabel("미화국별총위험량(단기)")
        ax.set_title(f"RI별 미화국별총위험량(단기) (주분석 n={len(primary)})")
    p = fig_dir / "10_exposure_by_ri.png"
    fig.tight_layout()
    fig.savefig(p, dpi=120)
    plt.close(fig)
    paths.append(p)

    return paths
