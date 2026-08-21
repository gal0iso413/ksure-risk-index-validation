# MEMORY — `ksure-risk-index-validation`

## Locked (2026-08-10)

- Country-level 2025 RI consistency review only (not country×industry direct).
- Wording: consistency vs 2025 indicators — not independent predictive power.
- Client: RI feature / validation-variable overlap not in scope as a dispute.
- RI files: 12 monthly XLSX; Sheet1; header Excel row 2; A:E; values `RI 1`–`RI 5`; RI5=high risk.
- Target: one XLSX; sheet `단기수출보험`; header Excel row 3; **F:K** (F=country name, G–K = grade, accident, loss, real loss, **미화국별총위험량(단기)**); grades 1–7 higher=worse.
- Join on normalized Korean country name; no fuzzy match; optional `country_name_map.json`.
- Aggregate industry→month→year; primary RI = annual median of monthly RI; primary cohort ≥6 months; one row/country.
- Zeros ≠ missing; no % rescale; cached values only.
- Exposure is a **core** target (expected: higher RI → larger short-term exposure).
- Lean `src.run_all` / `run_all.bat`. Client report = generated HTML + Markdown from `docs/report_template.md`.

## Internal run notes (2026-08-13)

- Real xlsx may be DRMONE-wrapped; Excel opens, openpyxl does not. Decrypt/export first.
- Target loader can look hung: no log until sheet scan finishes; value-only small xlsx is faster.
- Grade `0` fails the 1–7 gate (not a country_name_map issue). Exclude total/dummy rows in config.

## Open

- Manual `country_name_map.json` after `unmatched_countries.xlsx`
- Internal PC re-run after 5-target report (HTML+MD)
