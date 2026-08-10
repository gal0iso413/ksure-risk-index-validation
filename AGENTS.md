# ksure-risk-index-validation — agent context

Korean trade-insurance **country Risk Index consistency validation** for KSURE (한국무역보험공사).
Short PoC: check whether country RI (grades 1–5) aligns with observed risk indicators (loss ratio, real loss ratio, accident rate, country grade). Not ML, not a dashboard.

Governing plan: [`docs/plan.md`](docs/plan.md). Start each session at [`docs/next-actions.md`](docs/next-actions.md).

## Paths

```
PROJECT=/home/tom/projects/ksure-risk-index-validation
```

Real RI / target files live only on the **internal KSURE PC**. Never copy them into this workspace.

## Write boundary

Agents may write only under:

```
src/  tests/  docs/  config/  outputs/  wheelhouse/
```

Never write real data under `input/` into git. Never paste real company names or raw row values into docs, commits, or chat.

## Hard rules

1. **Country-level only.** Even if RI has industry, aggregate to country before joining country-level targets. Do not claim country×industry consistency.
2. **No pseudo-replication.** Do not fan country monthly stats onto every industry row and treat those as independent samples.
3. **Lean internal transfer.** Prefer one `run_all` entrypoint + few modules over many CLI scripts.
4. **Offline.** No internet, CDN, external APIs. HTML report must be self-contained.
5. **Honest verdicts.** Supported / Partially supported / Not supported / Untestable per indicator — never force a single “accuracy” score.
6. **Exposure (`국별총위험량`)** is reference-only, not a core target.

## Working style

- Lock column maps and grade order from user-provided meta before coding joins.
- Implement against synthetic data first; internal PC run only after smoke passes.
- Keep the transfer bundle small: code + example configs + requirements + wheels + `run_all.bat`.
