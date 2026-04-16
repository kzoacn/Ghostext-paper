# Ghostext-paper

Security-first writing workspace for the Ghostext ACM CCS 2026 submission.

This repository focuses on paper drafting, claim-to-evidence traceability, and reproducible experiment planning. The implementation source of truth is `../Ghostext`.

## Current Status (2026-04-16)

- Core paper draft skeleton is in `paper/`.
- Claim-to-evidence mapping is maintained under `notes/literature/`.
- Experiment execution is paused by project policy (see `AGENTS.md`).

## Quick Start

1. Read project boundaries and claim rules:

```text
AGENTS.md
```

2. Edit the paper:

```text
paper/main.tex
paper/sections/*.tex
paper/refs.bib
```

3. Update evidence traceability when adding or changing claims:

```text
notes/literature/claim-evidence-map.md
notes/literature/related-work-matrix.md
```

4. (Optional) compile the paper locally if LaTeX toolchain is available:

```bash
cd paper
latexmk -pdf main.tex
```

## Repository Map

- `AGENTS.md`: project mission, hard boundaries, and writing constraints
- `literature/key-paper/`: mandatory full-text key papers
- `literature/key-md/`: local reading notes for key papers
- `paper/`: ACM-format draft, section files, bibliography
- `notes/policies/`: writing and reporting checklists
- `notes/literature/`: claim-evidence map and related-work matrix
- `results/`: reserved for future experiment outputs (currently paused)
- `scripts/`: reserved for future reproducible pipelines (currently placeholder)

## Important Boundary

Do not run experiment pipelines in this repository until the user explicitly lifts the pause.
