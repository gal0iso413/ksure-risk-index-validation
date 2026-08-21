# Plan — `ksure-risk-index-validation`

## 목적

2025년 국가 RI(1–5, RI5=고위험)와 단기수출보험 국별 위험지표의 **정합성 검토**.
독립 예측력 검증이 아니며, RI 유용성 결론을 강제하지 않는다.

## 데이터

- RI: 월별 XLSX 12개, `Sheet1`, 헤더 Excel 2행, A:E, `RI n` 문자열, 코드는 문자열
- Target: 1파일, `단기수출보험`, 헤더 Excel 3행, F:K (F 국가명, G~K 국가등급·사고율·손해율·실질손해율·미화국별총위험량(단기))
- 조인: 국가한글명 + 선택적 수동 맵. 퍼지 금지
- 집계: 국가×월(업종 RI 혼재 시 중앙값) → 연간 중앙값(주분석). 코호트 ≥6개월

## 통계

전체 Spearman+bootstrap CI, 0초과 발생여부(비율 지표), 양수 부분(n≥10), Kruskal-Wallis+ε²,
국가등급·총위험량, 민감도(12개월/전체/평균/고위험월비율).

판정: Supported / Partially supported / Not supported / Untestable
총위험량 기대 방향: RI↑ → 총위험량↑.

## 품질 게이트

12개월 파일·시트·헤더·RI범위·등급1–7·타깃 국가명 중복·cached value 실패 시 중단.
월 일부 결측·업종 RI 혼재·미매칭·고비율 0은 경고+표.

## 실행

`python -m src.run_all --config config/analysis_config.json` 또는 `run_all.bat`
