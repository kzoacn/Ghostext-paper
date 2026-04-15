# Ghostext-paper

Security-first paper workspace for the Ghostext CCS 2026 submission.

## Quick Start

1. Run minimal evaluation + table generation + PDF build:

```bash
./scripts/run_all.sh
```

2. Main paper entry:

```text
paper/main.tex
```

3. Generated artifacts:

- `results/minimal_eval_results.json`
- `results/minimal_eval_tables.md`
- `paper/main.pdf`

## Repository Map

- `AGENTS.md`: project execution rules and scope boundaries
- `notes/policies/`: CCS 2026 CFP/template materials + compliance notes
- `notes/literature/`: related-work matrix and claim-scoping notes
- `paper/`: CCS-format LaTeX skeleton and bibliography
- `scripts/`: reproducible minimal evaluation pipeline
- `results/`: generated evaluation outputs
