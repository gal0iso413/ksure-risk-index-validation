# Intake — `ksure-risk-index-validation`

Date: 2026-08-10 (updated with confirmed file layouts)  
Status: **active** — 2025 주분석 완료. 후속은 2026-09-07 미팅 ([`meeting-2026-09-07.md`](meeting-2026-09-07.md)).

### Identity

| Field | Value |
|-------|-------|
| Repo | `ksure-risk-index-validation` |
| Korean title | 국가 Risk Index 정합성 검증 |
| Path | `~/projects/ksure-risk-index-validation/` |
| Remote | https://github.com/gal0iso413/ksure-risk-index-validation.git |
| Hosts | Home = code/synthetic; Internal PC = real XLSX |

### Goal

2025 국가 RI와 단기수출보험 국별 사고율·손해율·실질손해율·국가등급·미화국별총위험량(단기)의 정합성 검토.  
표현은 예측력 검증이 아님.

intake 당시 고객사는 RI 산출·검증변수 중복을 쟁점에서 제외했다. **2026-09-07 미팅에서 국가등급이 RI 구성 변수에 들어감이 확인**됐고, 등급 상관(ρ≈0.84)은 재현일 수 있다고 공유했다. 후속 문장에는 이 순환을 적는다.

한도 활용 의도(미팅): 공식 연동이 아니라 총액한도 **정성 가감의 보조 근거**·내부 활용 이력. 관심 코호트는 등급 5·6·7·심층감시국.

### Data (confirmed)

| Source | Layout |
|--------|--------|
| RI | 12× monthly `2025년 N월 Risk Index 보고서.xlsx`, Sheet1, header row 2, A:E |
| Target | `04.월별손해율총괄분석_국별 사고율, 손해율_단기수출보험만.xlsx`, sheet `단기수출보험`, header row 3, F:K (K = 미화국별총위험량(단기), core target) |

### Forbidden

Real RI/target files, company-level PII, credentials in git or chat.

### Git remote

[gal0iso413/ksure-risk-index-validation](https://github.com/gal0iso413/ksure-risk-index-validation.git)
