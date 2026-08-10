# MEMORY — `ksure-risk-index-validation`

Confirmed facts and locked decisions. Never paste real RI/target rows.

## Project

- KSURE **국가 Risk Index 정합성 검증** PoC.
- Repo: `ksure-risk-index-validation` · path `/home/tom/projects/ksure-risk-index-validation`
- Sisters: `ksure-overseas-biz-analysis`, `ksure-similar-claim-search`
- Governing docs: `docs/plan.md`, `docs/next-actions.md`, `docs/intake.md`

## Locked decisions (2026-08-10)

- Scope = **country RI** only — not country×industry consistency claims.
- Lean internal transfer: one `run_all` + few `src` modules (not 6 separate CLIs as the delivery shape).
- No real data in git; synthetic only on Home PC.
- Core targets: 손해율, 실질손해율, 사고율, 국가등급. Exposure = reference only.
- Verdicts per indicator: Supported / Partially supported / Not supported / Untestable.
- Pseudo-replication forbidden when joining country targets to industry-level RI.
- Offline HTML report (no CDN/JS libs).

## Open (need user meta)

- Input file names, sheets, extensions
- Column map (Korean headers)
- Exact RI grain and target grain
- RI direction (higher = riskier?)
- Official country-grade order JSON
- Internal Python version / install policy

## Repo pointers

- `README.md` — name, Korean title, run commands
- `AGENTS.md` — write boundary and hard rules
- `docs/intake.md` — identity and security
- `docs/plan.md` — method summary
- `docs/next-actions.md` — session start
