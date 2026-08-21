# ksure-risk-index-validation — agent context

2025 **country** Risk Index consistency review for KSURE. Not ML. Not country×industry direct validation.

Plan: [`docs/plan.md`](docs/plan.md). Session start: [`docs/next-actions.md`](docs/next-actions.md).

## Paths

```
PROJECT=/home/tom/projects/ksure-risk-index-validation
```

Real monthly RI + target XLSX live only on the internal PC.

## Write boundary

```
src/  tests/  docs/  config/  outputs/  wheelhouse/
```

Never commit real `input/` files. Never paste real row values into docs/chat.

## Hard rules

1. Country-level only; aggregate industry×month before joining annual target.
2. No pseudo-replication (final table = one row per country).
3. No fuzzy country matching; optional explicit `country_name_map.json` only.
4. Do not treat Excel `#N/A` / blanks as zero; keep true zeros.
5. Do not rescale rates because header contains `%`.
6. Read cached XLSX values only (`data_only`); no external link refresh.
7. Report wording: consistency review of current RI vs 2025 indicators — not independent predictive power.
8. Five core targets including short-term country exposure (미화국별총위험량). Expected: higher RI → larger exposure. Lean transfer bundle.

## Working style

Implement/test on synthetic fixtures that mirror real layouts. Internal run only after smoke passes.
