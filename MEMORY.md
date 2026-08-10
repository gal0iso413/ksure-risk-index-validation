# MEMORY — `ksure-risk-index-validation`

## Locked (2026-08-10)

- Country-level 2025 RI consistency review only (not country×industry direct).
- Wording: consistency vs 2025 indicators — not independent predictive power.
- Client: RI feature / validation-variable overlap not in scope as a dispute.
- RI files: 12 monthly XLSX; Sheet1; header Excel row 2; A:E; values `RI 1`–`RI 5`; RI5=high risk.
- Target: one XLSX; sheet `단기수출보험`; header Excel row 3; **F:K only**; grades 1–7 higher=worse.
- Join on normalized Korean country name; no fuzzy match; optional `country_name_map.json`.
- Aggregate industry→month→year; primary RI = annual median of monthly RI; primary cohort ≥6 months; one row/country.
- Zeros ≠ missing; no % rescale; cached values only.
- Exposure reference-only.
- Lean `src.run_all` / `run_all.bat`.

## Open (internal confirm)

- Exact Python version + win32/amd64 for wheelhouse
- Final confirmation that report meta says RI5=high risk
- Manual country_name_map entries after first unmatched list
