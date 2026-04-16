# CCS Draft Checklist (Ghostext)

## Non-Negotiables

- Use ACM `sigconf` style without local format hacks.
- Keep main content at least 10 pages and within CCS policy.
- Keep references and appendices outside main-content count checks.
- Do not run experiment pipelines until user lifts pause.

## Claim Hygiene

- Every technical claim in `paper/sections/*.tex` must map to:
  - code evidence in `../Ghostext`, or
  - published citation, or
  - explicit future-work label.
- Avoid words like “provably secure” unless formal proof is actually provided for our exact setting.
- Use “almost perfect” only with passive-censor and finite-precision caveats.

## Evaluation Reporting (When Pause Is Lifted)

Always report:

- model/version and backend path,
- seed and all protocol-sensitive config,
- prompt policy and passphrase handling policy (without leaking secret material),
- dataset/text source,
- metrics with units,
- hardware/runtime environment,
- exact command/scripts used.

## Reproducibility Artifacts To Maintain

- `results/*.json` raw summaries,
- script entry points under `scripts/`,
- table generation scripts/logs,
- commit hash of `../Ghostext` used for experiments.
