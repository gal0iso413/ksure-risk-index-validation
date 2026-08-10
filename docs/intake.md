# Intake — `ksure-risk-index-validation`

Date: 2026-08-10 (updated with confirmed file layouts)  
Status: **active** — implementation against confirmed 2025 schemas

### Identity

| Field | Value |
|-------|-------|
| Repo | `ksure-risk-index-validation` |
| Korean title | 국가 Risk Index 정합성 검증 |
| Path | `~/projects/ksure-risk-index-validation/` |
| Remote | https://github.com/gal0iso413/ksure-risk-index-validation.git |
| Hosts | Home = code/synthetic; Internal PC = real XLSX |

### Goal

2025 국가 RI와 단기수출보험 국별 사고율·손해율·실질손해율·국가등급의 정합성 검토.  
표현은 예측력 검증이 아님. 고객사는 RI 산출·검증변수 중복을 본 과업 쟁점에서 제외.

### Data (confirmed)

| Source | Layout |
|--------|--------|
| RI | 12× monthly `2025년 N월 Risk Index 보고서.xlsx`, Sheet1, header row 2, A:E |
| Target | `04.월별손해율총괄분석_국별 사고율, 손해율_단기수출보험만.xlsx`, sheet `단기수출보험`, header row 3, F:K |

### Forbidden

Real RI/target files, company-level PII, credentials in git or chat.

### Git remote

[gal0iso413/ksure-risk-index-validation](https://github.com/gal0iso413/ksure-risk-index-validation.git)
