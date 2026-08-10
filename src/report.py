"""Offline self-contained HTML report."""

from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import Any

import pandas as pd


def _img_tag(path: Path) -> str:
    if not path.exists():
        return f"<p>(missing figure: {html.escape(path.name)})</p>"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        f'<img alt="{html.escape(path.name)}" '
        f'src="data:image/png;base64,{b64}" '
        f'style="max-width:100%;height:auto;border:1px solid #ddd;margin:8px 0;" />'
    )


def _fmt(v: Any) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    if isinstance(v, float):
        return f"{v:.4f}"
    return html.escape(str(v))


def _conclusion_sentence(verdicts: dict[str, str]) -> str:
    vals = list(verdicts.values())
    if not vals:
        return "분석 단위 및 매칭 범위의 한계로 RI의 정합성을 직접 검증하기 어렵다."
    if all(v == "Untestable" for v in vals):
        return "분석 단위 및 매칭 범위의 한계로 RI의 정합성을 직접 검증하기 어렵다."
    if any(v == "Supported" for v in vals) and not any(v == "Not supported" for v in vals):
        return "RI는 일부 실제 위험지표와 기대 방향의 관계를 보여 보조지표로 활용할 가능성이 있다."
    if any(v == "Partially supported" for v in vals):
        return "RI의 정합성은 일부 지표에 한정되며, 단독 판단 기준으로 사용하기에는 근거가 부족하다."
    if all(v in {"Not supported", "Untestable"} for v in vals):
        return "현재 데이터에서는 RI와 실제 위험지표 간 일관된 관계를 확인하기 어렵다."
    return "RI의 정합성은 일부 지표에 한정되며, 단독 판단 기준으로 사용하기에는 근거가 부족하다."


def make_report(
    *,
    cfg: dict,
    profiles: dict,
    coverage: dict,
    quality: dict,
    results: dict,
    figure_paths: list[Path],
    analysis: pd.DataFrame,
    out_path: Path,
) -> Path:
    verdicts = results.get("verdicts", {})
    primary = results.get("primary_ge_6m", {})
    conclusion = _conclusion_sentence(verdicts)

    verdict_rows = "".join(
        f"<tr><td>{html.escape(k)}</td><td><strong>{html.escape(v)}</strong></td></tr>"
        for k, v in verdicts.items()
    )
    metric_rows = ""
    for key, m in (primary.get("metrics") or {}).items():
        if m.get("reference_only"):
            continue
        metric_rows += (
            "<tr>"
            f"<td>{html.escape(str(m.get('label', key)))}</td>"
            f"<td>{_fmt(m.get('n'))}</td>"
            f"<td>{_fmt(m.get('spearman_rho'))}</td>"
            f"<td>{_fmt((m.get('ci95') or {}).get('low'))} ~ {_fmt((m.get('ci95') or {}).get('high'))}</td>"
            f"<td>{_fmt((m.get('incidence') or {}).get('spearman_rho'))}</td>"
            f"<td>{html.escape(str(verdicts.get(key, '—')))}</td>"
            "</tr>"
        )

    figs = "\n".join(_img_tag(p) for p in figure_paths)

    body = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<title>국가 Risk Index 정합성 검증 보고서 (2025)</title>
<style>
body {{ font-family: "Malgun Gothic", "맑은 고딕", sans-serif; margin: 24px; color: #222; line-height: 1.5; }}
h1,h2,h3 {{ color: #1f3a4d; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 14px; }}
th, td {{ border: 1px solid #ccc; padding: 6px 8px; text-align: left; }}
th {{ background: #eef3f7; }}
.note {{ background: #f7f4ea; padding: 10px 12px; border-left: 4px solid #c4a35a; }}
.box {{ background: #f5f7f9; padding: 12px; margin: 12px 0; }}
</style>
</head>
<body>
<h1>국가 Risk Index 정합성 검증 보고서</h1>
<p class="note">본 보고서는 <strong>독립적인 예측력 검증</strong>이 아니라,
<strong>현재 RI와 2025년 위험지표 간 정합성 검토</strong>이다.
RI가 유용하다는 결론을 전제하지 않는다.</p>

<h2>1. 검증 목적</h2>
<p>2025년 국가 단위 Risk Index(RI 1~5, RI 5=고위험)가 단기수출보험 국별
사고율·손해율·실질손해율·국가등급과 기대 방향의 관계를 보이는지 검토한다.
국가×업종 직접 검증이 아니며, 모델 개발 과제가 아니다.</p>

<h2>2. 데이터 및 분석 단위</h2>
<ul>
<li>분석 연도: {cfg.get('analysis_year')}</li>
<li>RI grain: 국가×업종×월 → 국가×월 → <strong>국가×연도(1행)</strong></li>
<li>검증자료 grain: 국가×2025년 연간 집계 (시트 단기수출보험, F:K)</li>
<li>주 분석 RI: 월별 국가 RI의 연간 중앙값</li>
<li>주 분석 코호트: 관측월 ≥ {cfg['analysis']['minimum_months_primary']}개월</li>
<li>비율 단위: {cfg.get('units', {}).get('rate_unit_label', 'percentage points')} (헤더 %로 재스케일하지 않음)</li>
<li>주 분석 국가 수: {results.get('primary_cohort_n')}</li>
</ul>

<h2>3. 데이터 품질과 매칭률</h2>
<div class="box">
<ul>
<li>RI 국가 수: {coverage.get('n_ri_countries')}</li>
<li>검증자료 국가 수: {coverage.get('n_target_countries')}</li>
<li>매칭 국가 수: {coverage.get('n_matched')}</li>
<li>RI 기준 매칭률: {_fmt(coverage.get('match_rate_ri'))}</li>
<li>검증자료 기준 매칭률: {_fmt(coverage.get('match_rate_target'))}</li>
<li>국가×월 내 업종 RI 혼재 건수: {quality.get('n_mixed_ri_country_month')}
 (비율 {_fmt(quality.get('mixed_ri_share'))})</li>
</ul>
</div>

<h2>4. 분석 방법</h2>
<p>Spearman 순위상관, 국가 단위 bootstrap 95% CI, Kruskal-Wallis 및 epsilon-squared,
0 초과 발생 여부, 양수 국가 부분 집합, 관측월·집계방법 민감도 분석을 함께 사용한다.
p-value 단독으로 판정하지 않는다. 국별총위험량은 참고만 한다.</p>

<h2>5–7. 지표별 정합성</h2>
<table>
<thead><tr><th>지표</th><th>n</th><th>Spearman ρ</th><th>95% CI</th><th>발생여부 ρ</th><th>판정</th></tr></thead>
<tbody>{metric_rows}</tbody>
</table>

<h2>8. 민감도 분석</h2>
<p>12개월 완전관측, 전체 매칭, 연간 평균 RI, 고위험 월 비율로 방향을 재확인했다.
상세 수치는 statistical_results.xlsx를 참조한다.</p>

<h2>9. 종합 판정</h2>
<table>
<thead><tr><th>지표</th><th>판정</th></tr></thead>
<tbody>{verdict_rows}</tbody>
</table>
<p><strong>{html.escape(conclusion)}</strong></p>

<h2>10. 한계 및 추가 확인사항</h2>
<ul>
<li>국가×업종 RI의 직접 정합성은 검증하지 않았다.</li>
<li>검증자료가 연간 집계이므로 월별 동시성 해석에 한계가 있다.</li>
<li>사고율·손해율에 0이 많아 전체 상관과 발생여부·양수 규모를 분리했다.</li>
<li>RI 산출변수와 검증변수 중복 가능성은 고객사 합의에 따라 본 과업 쟁점에서 제외했다.</li>
</ul>

<h2>그림</h2>
{figs}

</body>
</html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body, encoding="utf-8")
    return out_path
