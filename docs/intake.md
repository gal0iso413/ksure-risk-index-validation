# Intake — `ksure-risk-index-validation`

Date: 2026-08-10  
Status: **active** — repo bootstrap; awaiting data meta from outside.

---

### 1. Identity

| Field | Value |
|-------|-------|
| Repository / project name | `ksure-risk-index-validation` |
| Korean title | 국가 Risk Index 정합성 검증 |
| Workspace path | `~/projects/ksure-risk-index-validation/` |
| Sister projects | `ksure-overseas-biz-analysis`, `ksure-similar-claim-search` |
| Primary host | **Home PC** — code·합성 데이터·문서만. 실데이터·실실행은 **내부 KSURE PC** (air-gapped) |
| Security level | **Mixed** — 구조/메타 OK; 실값·원자료 금지 |
| Deploy / run target | 내부 Windows PC, 오프라인 `run_all.bat` |

### 2. Goal

- **Goal:** 국가 RI(1~5)와 손해율·실질손해율·사고율·국가등급 등 실제 위험지표의 **정합성**을 비모수로 검증하고, 오프라인 HTML 보고서로 판정한다.
- **Success criteria:**
  - 원본 미수정, 매칭률·분석 단위·의사반복 없음이 보고됨
  - 지표별 Supported / Partially / Not supported / Untestable 판정
  - 합성 데이터(정합·무관) smoke 통과 후 내부 실행 가능
  - 내부 이관 파일 세트 최소화
- **Out of scope:** ML/예측 서비스, 대시보드, 국가×업종 직접 정합성 주장, 국별총위험량 핵심 타깃화, 인터넷 의존

### 3. Data and access

| Source | Access | Classification |
|--------|--------|----------------|
| RI (국가 위험등급 1~5) | 내부 PC만; 외부에서는 메타·컬럼맵만 | **Internal-restricted** |
| Target (국가·재무·위험 통계) | 내부 PC만; 외부 메타 OK | **Internal-restricted** |
| Synthetic fixtures under `tests/` | Home PC | **Safe to commit** |

- **Forbidden:** 실 RI/타깃 원자료, 기업명, 민감 행값, 내부 자격증명
- **Approval required:** git remote push, 내부 PC로의 대량 wheel 반입 정책 우회

### 4. Agents

| Role | Needed? | Notes |
|------|---------|-------|
| builder | Yes | Cursor — lean pipeline + docs |
| scout | Human | 사용자가 내부 메타·파일 확장자 확인 |
| researcher / Hermes | No (default) | 요청 시에만 |

### 5. Outputs

| Artifact | Path |
|----------|------|
| Tables | `outputs/tables/` |
| Figures | `outputs/figures/` |
| HTML report | `outputs/report/risk_index_validation_report.html` |
| Log | `outputs/logs/run_summary.log` |

### 6. Human approval points

- [x] External messages / uploads
- [x] Deployments
- [x] File deletion
- [x] Real data into this repo
- [ ] Internal PC package contents (keep minimal)

### 7. Backup / export

- Git remote: **TBD** (local-only until user asks)
- Suggested private remote name: `ksure-risk-index-validation`
