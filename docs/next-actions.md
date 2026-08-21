# 다음 작업 — `ksure-risk-index-validation`

**Last updated:** 2026-08-21  
**Current phase:** 5지표 보고서 재실행 (내부 PC)

## 지금

1. ~~데이터 메타·파이프라인·합성 테스트~~
2. ~~requirements 패키지: 내부 PC에 이미 있음 → wheelhouse 불필요~~
3. ~~RI 방향: 1–5, RI5=고위험 확정~~
4. ~~내부 PC 1차 실행 (DRM 해제 후 HTML 산출)~~
5. ~~1차 고객 설명 (4지표)~~
6. **내부 PC에서 코드 반영 후 `run_all.bat` 재실행** — 총위험량 핵심 타깃 + 상세 HTML/MD
7. 산출: `outputs/report/risk_index_validation_report.html` (본문) · `.md` (Word 붙여넣기)
8. 필요 시 `unmatched_countries.xlsx` 보고 `country_name_map.json` 보강 후 재실행

문장 수정은 [`report_template.md`](report_template.md). 읽기: [`results-guide.md`](results-guide.md). 1차 4지표 기록: [`results-guide-first.md`](results-guide-first.md).

## 하지 않음

- 실데이터 git 반입
- 국가×업종 직접 정합성 주장
- 퍼지 국가매칭, 비율 재스케일, 수식 재계산
- ML/대시보드
- wheelhouse (현재 환경에서는 불필요)
