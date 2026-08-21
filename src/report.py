"""Fill docs/report_template.md with run numbers; write HTML and Markdown reports."""

from __future__ import annotations

import base64
import html
import re
from pathlib import Path
from typing import Any

import pandas as pd

from .stats import CORE_METRIC_KEYS, SIZE_METRIC_KEYS
from .utils import PipelineError, project_root

SENSITIVITY_LABELS = {
    "complete_12m": "12개월 모두 있는 국가",
    "all_matched": "매칭 국가 전체",
    "primary_mean_ri": "연간 평균 RI",
    "primary_high_share": "고위험 월 비율",
}


def _fmt_num(v: Any, digits: int = 4) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    if isinstance(v, int):
        return str(v)
    return str(v)


def _fmt_pct(v: Any) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    try:
        return f"{float(v) * 100:.1f}%"
    except (TypeError, ValueError):
        return "—"


def _fmt_ci(m: dict) -> str:
    ci = m.get("ci95") or {}
    lo, hi = ci.get("low"), ci.get("high")
    if lo is None and hi is None:
        return "—"
    return f"{_fmt_num(lo)} ~ {_fmt_num(hi)}"


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    esc = [str(h).replace("|", "\\|") for h in headers]
    lines = ["| " + " | ".join(esc) + " |", "| " + " | ".join("---" for _ in esc) + " |"]
    for row in rows:
        cells = [str(c).replace("|", "\\|") for c in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _conclusion_sentence(verdicts: dict[str, str]) -> str:
    vals = list(verdicts.values())
    if not vals:
        return "분석에 쓸 수 있는 국가가 부족해, 이번 자료로는 RI와 지표의 정합성을 판단하기 어렵다."
    if all(v == "Untestable" for v in vals):
        return "분석에 쓸 수 있는 국가가 부족해, 이번 자료로는 RI와 지표의 정합성을 판단하기 어렵다."
    if any(v == "Supported" for v in vals) and not any(v == "Not supported" for v in vals):
        return "RI는 일부 지표와 기대 방향의 관계를 보인다. 지표별 판정을 함께 본다."
    if all(v in {"Not supported", "Untestable"} for v in vals):
        return "이번 자료에서는 RI와 검토 지표 사이에 기대 방향의 일관된 관계를 확인하지 못했다."
    return "RI의 정합성은 지표에 따라 다르며, 한 지표의 결과만으로 전체를 단정하지 않는다."


def _rho_direction(rho: float | None) -> str:
    if rho is None or (isinstance(rho, float) and pd.isna(rho)):
        return "계산하지 못했다"
    if rho > 0.02:
        return "양수(기대 방향)"
    if rho < -0.02:
        return "음수(기대와 반대)"
    return "0에 가깝다"


def _narrative_grade(m: dict, verdict: str) -> str:
    rho = m.get("spearman_rho")
    n = m.get("n")
    lines = [
        f"주분석 n={_fmt_num(n, 0)}, Spearman ρ={_fmt_num(rho)}, 95% 신뢰구간 {_fmt_ci(m)}. 판정은 **{verdict}** 이다.",
        f"ρ는 {_rho_direction(rho)}.",
    ]
    if verdict == "Supported":
        lines.append(
            "2025년 국가 단위로 보면, RI와 국가등급은 같은 위험 순서를 가리킨다. "
            "이 결과는 국가등급과의 정합성이다."
        )
    elif verdict == "Partially supported":
        lines.append("방향은 기대와 같으나, 강도나 일부 구간에서는 예외가 있다.")
    elif verdict == "Not supported":
        lines.append("이번 주분석에서는 국가등급과 기대 방향의 정합성을 지지하지 않는다.")
    else:
        lines.append("이번 자료로는 국가등급과의 관계를 판단하지 않았다.")
    return "\n\n".join(lines)


def _narrative_rates(
    metrics: dict[str, dict],
    verdicts: dict[str, str],
) -> str:
    keys = ["accident_rate", "loss_ratio", "real_loss_ratio"]
    bits = []
    for key in keys:
        m = metrics.get(key, {})
        v = verdicts.get(key, "—")
        inc = (m.get("incidence") or {}).get("spearman_rho")
        bits.append(
            f"- **{m.get('label', key)}:** n={_fmt_num(m.get('n'), 0)}, "
            f"ρ={_fmt_num(m.get('spearman_rho'))} ({_rho_direction(m.get('spearman_rho'))}), "
            f"발생여부 ρ={_fmt_num(inc)}, 판정 **{v}**."
        )
    body = "\n".join(bits)
    vs = [verdicts.get(k, "") for k in keys]
    if all(x == "Not supported" for x in vs):
        wrap = (
            "세 비율 모두 주분석에서 기대 방향(RI가 높을수록 사고·손해가 큼)을 지지하지 않는다. "
            "발생 여부 ρ도 같은 표에서 함께 본다."
        )
    elif all(x == "Supported" for x in vs):
        wrap = "세 비율 모두 기대 방향의 정합성이 있다."
    else:
        wrap = "세 비율의 판정은 지표마다 다르다. 표의 지표별 판정을 그대로 읽는다."
    pos = metrics.get("accident_rate", {}).get("positive_subset") or {}
    extra = ""
    if pos.get("n") is not None:
        extra = (
            f"\n\n값이 0보다 큰 국가 수는 사고율 {_fmt_num(pos.get('n'), 0)}개국 규모이다. "
            "양수 국가만 본 그림은 전체 순위상관과 따로 읽는다."
        )
    return wrap + "\n\n" + body + extra


def _narrative_exposure(m: dict, verdict: str) -> str:
    rho = m.get("spearman_rho")
    n = m.get("n")
    lines = [
        f"주분석 n={_fmt_num(n, 0)}, Spearman ρ={_fmt_num(rho)}, 95% 신뢰구간 {_fmt_ci(m)}. 판정은 **{verdict}** 이다.",
        f"ρ는 {_rho_direction(rho)}.",
    ]
    if verdict == "Supported":
        lines.append("RI가 높은 국가일수록 단기 총위험량도 큰 경향이 있다.")
    elif verdict == "Partially supported":
        lines.append("방향은 기대와 같으나, 강도는 약하거나 일부에서만 보인다.")
    elif verdict == "Not supported":
        lines.append("이번 주분석에서는 RI가 높을수록 총위험량이 크다는 기대 방향을 지지하지 않는다.")
    else:
        lines.append("이번 자료로는 총위험량과의 관계를 판단하지 않았다.")
    return "\n\n".join(lines)


def _sensitivity_text(results: dict) -> str:
    primary = results.get("primary_ge_6m", {}).get("metrics", {})
    lines = []
    for key in CORE_METRIC_KEYS:
        label = (primary.get(key) or {}).get("label", key)
        pr = (primary.get(key) or {}).get("spearman_rho")
        same = []
        other = []
        for cname, clabel in SENSITIVITY_LABELS.items():
            block = results.get(cname) or {}
            rho = (block.get("metrics") or {}).get(key, {}).get("spearman_rho")
            if rho is None or pr is None:
                continue
            same_dir = (pr > 0.02 and rho > 0.02) or (pr < -0.02 and rho < -0.02) or (
                abs(pr) <= 0.02 and abs(rho) <= 0.02
            )
            (same if same_dir else other).append(clabel)
        if not same and not other:
            lines.append(f"- **{label}:** 주분석 ρ={_fmt_num(pr)}.")
            continue
        extra = ""
        if other:
            extra = f" 방향이 달랐던 확인: {', '.join(other)}."
        lines.append(
            f"- **{label}:** 주분석 ρ={_fmt_num(pr)} ({_rho_direction(pr)}). "
            f"같은 방향: {', '.join(same) if same else '해당 없음'}."
            + extra
        )
    return "\n".join(lines)


def _coverage_table(cfg: dict, coverage: dict, quality: dict, primary_n: int) -> str:
    year = cfg.get("analysis_year", "")
    n_ri = coverage.get("n_ri_countries")
    n_tg = coverage.get("n_target_countries")
    n_m = coverage.get("n_matched")
    rows = [
        ["분석 연도", str(year), "월별 RI와 연간 검증자료를 같은 해로 맞춤"],
        ["RI 국가 수", _fmt_num(n_ri, 0), "월별 RI에 등장한 국가"],
        ["검증자료 국가 수", _fmt_num(n_tg, 0), "연간 검증표의 국가(제외 라벨 처리 후)"],
        ["양쪽 매칭", _fmt_num(n_m, 0), "이름이 같아 붙인 국가"],
        ["RI 기준 매칭률", f"{_fmt_num(coverage.get('match_rate_ri'))} ({_fmt_pct(coverage.get('match_rate_ri'))})", "RI 국가 중 검증표와 연결된 비율"],
        ["검증자료 기준 매칭률", f"{_fmt_num(coverage.get('match_rate_target'))} ({_fmt_pct(coverage.get('match_rate_target'))})", "검증표 국가 중 RI와 연결된 비율"],
        ["주분석 국가 수", _fmt_num(primary_n, 0), "매칭 국가 중 관측 월이 기준 이상인 국가"],
        [
            "국가×월 업종 RI 혼재",
            f"{_fmt_num(quality.get('n_mixed_ri_country_month'), 0)}건 ({_fmt_pct(quality.get('mixed_ri_share'))})",
            "같은 국가·같은 달에 업종별 RI가 서로 다른 경우",
        ],
    ]
    return _md_table(["항목", "값", "의미"], rows)


def _metrics_table(primary: dict, verdicts: dict[str, str]) -> str:
    metrics = primary.get("metrics") or {}
    rows = []
    for key in CORE_METRIC_KEYS:
        m = metrics.get(key, {})
        if key in SIZE_METRIC_KEYS:
            inc = "—"
        else:
            inc = _fmt_num((m.get("incidence") or {}).get("spearman_rho"))
        rows.append(
            [
                str(m.get("label", key)),
                _fmt_num(m.get("n"), 0),
                _fmt_num(m.get("spearman_rho")),
                _fmt_ci(m),
                inc,
                f"**{verdicts.get(key, '—')}**",
            ]
        )
    return _md_table(["지표", "n", "Spearman ρ", "95% 신뢰구간", "발생여부 ρ", "판정"], rows)


def _verdicts_table(metrics: dict, verdicts: dict[str, str]) -> str:
    rows = []
    for key in CORE_METRIC_KEYS:
        label = (metrics.get(key) or {}).get("label", key)
        rows.append([str(label), f"**{verdicts.get(key, '—')}**"])
    return _md_table(["지표", "판정"], rows)


def _ri_dist_table(analysis: pd.DataFrame, min_months: int) -> str:
    primary = analysis[analysis["months_present"] >= min_months].copy()
    if primary.empty or "ri_annual_median" not in primary.columns:
        return "_주분석 국가가 없다._"
    lvl = primary["ri_annual_median"].round().clip(1, 5)
    vc = lvl.value_counts().sort_index()
    rows = []
    for i in range(1, 6):
        n = int(vc.get(i, 0))
        note = "저위험" if i == 1 else ("고위험" if i == 5 else "")
        rows.append([str(i), str(n), note])
    return _md_table(["연간 RI", "국가 수", ""], rows)


def _build_context(
    *,
    cfg: dict,
    coverage: dict,
    quality: dict,
    results: dict,
    analysis: pd.DataFrame,
) -> dict[str, str]:
    year = str(cfg.get("analysis_year", ""))
    min_months = int(cfg["analysis"]["minimum_months_primary"])
    verdicts = results.get("verdicts") or {}
    primary = results.get("primary_ge_6m") or {}
    metrics = primary.get("metrics") or {}
    primary_n = int(results.get("primary_cohort_n") or 0)
    n_matched = int(coverage.get("n_matched") or 0)
    n_below = max(n_matched - primary_n, 0)
    mixed_share = quality.get("mixed_ri_share")

    return {
        "year": year,
        "min_months": str(min_months),
        "conclusion": _conclusion_sentence(verdicts),
        "primary_n": str(primary_n),
        "n_matched": str(n_matched),
        "n_below_min_months": str(n_below),
        "n_only_target": str(len(coverage.get("only_target") or [])),
        "n_only_ri": str(len(coverage.get("only_ri") or [])),
        "mixed_n": _fmt_num(quality.get("n_mixed_ri_country_month"), 0),
        "mixed_share_pct": _fmt_pct(mixed_share),
        "coverage_table": _coverage_table(cfg, coverage, quality, primary_n),
        "metrics_table": _metrics_table(primary, verdicts),
        "verdicts_table": _verdicts_table(metrics, verdicts),
        "ri_dist_table": _ri_dist_table(analysis, min_months),
        "narrative_grade": _narrative_grade(metrics.get("country_grade") or {}, verdicts.get("country_grade", "—")),
        "narrative_rates": _narrative_rates(metrics, verdicts),
        "narrative_exposure": _narrative_exposure(metrics.get("exposure") or {}, verdicts.get("exposure", "—")),
        "sensitivity_text": _sensitivity_text(results),
    }


def _fill_template(template: str, ctx: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return ctx.get(key, match.group(0))

    return re.sub(r"\{\{(\w+)\}\}", repl, template)


def _inline_html(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return escaped


def _img_html(fig_dir: Path, filename: str, alt: str) -> str:
    path = fig_dir / filename
    cap = html.escape(alt)
    if not path.exists():
        return f"<p>(그림 없음: {html.escape(filename)})</p>"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        f'<figure><img alt="{cap}" src="data:image/png;base64,{b64}" />'
        f"<figcaption>{cap}</figcaption></figure>"
    )


def _md_table_to_html(block: str) -> str:
    lines = [ln for ln in block.strip().splitlines() if ln.strip()]
    if len(lines) < 2:
        return ""
    def cells(line: str) -> list[str]:
        raw = line.strip()
        if raw.startswith("|"):
            raw = raw[1:]
        if raw.endswith("|"):
            raw = raw[:-1]
        return [c.strip() for c in raw.split("|")]

    headers = cells(lines[0])
    body_lines = lines[2:] if re.match(r"^\s*\|?\s*:?-{3,}", lines[1]) else lines[1:]
    thead = "".join(f"<th>{_inline_html(h)}</th>" for h in headers)
    rows_html = []
    for ln in body_lines:
        cs = cells(ln)
        tds = "".join(f"<td>{_inline_html(c)}</td>" for c in cs)
        rows_html.append(f"<tr>{tds}</tr>")
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{''.join(rows_html)}</tbody></table>"


def markdown_to_html(md: str, fig_dir: Path) -> str:
    """Minimal Markdown → HTML (headings, tables, lists, images, bold). No extra packages."""
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    def is_table_row(s: str) -> bool:
        return s.strip().startswith("|") and "|" in s.strip()[1:]

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue
        if stripped == "---":
            out.append("<hr />")
            i += 1
            continue
        if stripped.startswith("#"):
            m = re.match(r"^(#{1,3})\s+(.*)$", stripped)
            if m:
                level = len(m.group(1))
                out.append(f"<h{level}>{_inline_html(m.group(2))}</h{level}>")
                i += 1
                continue
        if stripped.startswith("!["):
            m = re.match(r"^!\[(.*?)\]\(\.\./figures/([^)]+)\)$", stripped)
            if m:
                out.append(_img_html(fig_dir, m.group(2), m.group(1)))
                i += 1
                continue
        if is_table_row(stripped):
            block = [stripped]
            i += 1
            while i < n and is_table_row(lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            out.append(_md_table_to_html("\n".join(block)))
            continue
        if stripped.startswith("- "):
            items = []
            while i < n and lines[i].strip().startswith("- "):
                items.append(f"<li>{_inline_html(lines[i].strip()[2:])}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                text = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                items.append(f"<li>{_inline_html(text)}</li>")
                i += 1
            out.append("<ol>" + "".join(items) + "</ol>")
            continue

        para = [stripped]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if (
                not nxt
                or nxt == "---"
                or nxt.startswith("#")
                or nxt.startswith("![")
                or nxt.startswith("- ")
                or is_table_row(nxt)
                or re.match(r"^\d+\.\s+", nxt)
            ):
                break
            para.append(nxt)
            i += 1
        out.append("<p>" + _inline_html(" ".join(para)) + "</p>")

    body = "\n".join(out)
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<title>국가 Risk Index 정합성 검토 보고서</title>
<style>
body {{ font-family: "Malgun Gothic", "맑은 고딕", sans-serif; max-width: 900px;
  margin: 32px auto; padding: 0 20px; color: #222; line-height: 1.6; }}
h1, h2, h3 {{ color: #1f3a4d; page-break-after: avoid; }}
h1 {{ font-size: 22px; }}
h2 {{ font-size: 18px; margin-top: 1.6em; }}
h3 {{ font-size: 16px; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 14px; }}
th, td {{ border: 1px solid #ccc; padding: 6px 8px; text-align: left; vertical-align: top; }}
th {{ background: #eef3f7; }}
figure {{ margin: 16px 0; page-break-inside: avoid; }}
img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
figcaption {{ font-size: 13px; color: #444; margin-top: 6px; }}
code {{ font-size: 90%; }}
hr {{ border: none; border-top: 1px solid #ddd; margin: 24px 0; }}
@media print {{
  body {{ margin: 12mm; max-width: none; }}
  h2 {{ page-break-before: auto; }}
}}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def make_report(
    *,
    cfg: dict,
    profiles: dict,
    coverage: dict,
    quality: dict,
    results: dict,
    figure_paths: list[Path],
    analysis: pd.DataFrame,
    out_path: Path | None = None,
    figure_dir: Path | None = None,
    out_dir: Path | None = None,
) -> Path:
    """Write Markdown + self-contained HTML. ``out_path`` kept for older callers."""
    if out_dir is None:
        if out_path is not None:
            out_dir = out_path.parent
        else:
            raise PipelineError("make_report needs out_dir or out_path")
    if figure_dir is None:
        if figure_paths:
            figure_dir = figure_paths[0].parent
        else:
            figure_dir = out_dir.parent / "figures"

    tmpl_path = project_root() / "docs" / "report_template.md"
    if not tmpl_path.exists():
        raise PipelineError(f"Report template not found: {tmpl_path}")
    template = tmpl_path.read_text(encoding="utf-8")
    ctx = _build_context(
        cfg=cfg,
        coverage=coverage,
        quality=quality,
        results=results,
        analysis=analysis,
    )
    md = _fill_template(template, ctx)
    html_doc = markdown_to_html(md, figure_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "risk_index_validation_report.md"
    html_path = out_path if out_path is not None else out_dir / "risk_index_validation_report.html"
    md_path.write_text(md, encoding="utf-8")
    html_path.write_text(html_doc, encoding="utf-8")
    return html_path
