# Ghostext-paper Agent Guide (Short)

This file is the compact execution guide for agents in this repository. Detailed policies, rationale, and extended checklists are moved to `SPEC.md`.

## 1. Mission

This repository is for drafting the Ghostext paper (target: ACM CCS 2026), orchestrating evidence-focused experiments, and maintaining claim-to-evidence traceability. The implementation source of truth is `../Ghostext`.

## 2. Source Of Truth Priority

When technical statements are written, prioritize evidence in this order: `../Ghostext/src/ghostext/*.py`, `../Ghostext/tests/*.py`, `../Ghostext/spec.md`, then `../Ghostext/README.md`. If spec text and implementation differ, treat code plus tests as ground truth and record the discrepancy in notes.

## 3. Core Framing

Use security-first framing rather than AI benchmark framing. Focus on threat model, assumptions, failure modes, and reproducibility. Do not present unsupported novelty or broad model-SOTA narratives.

## 4. Claim Boundaries

Safe claims are deterministic decode under fully matched runtime configuration behavior under tested mismatch classes, encrypt-before-hide authenticated packetization, and protocol-oriented configuration fingerprint checks. Unsafe claims unless new evidence is added include active-edit robustness, dedicated steganalysis resistance, cross-model/version compatibility, and production-grade censorship resistance.

## 5. Required Writing Discipline

For every nontrivial technical paragraph, explicitly scope the claim, attach at least one evidence pointer, and apply maturity labels (`implemented + tested`, `implemented only`, `planned`) in internal notes. If a statement is not `implemented + tested`, add explicit caveat text. Never present planned experiments as completed.

Writing style hard requirement for paper text: do not use bullet lists or numbered lists for narrative exposition; write complete natural-language paragraphs instead. In explicit shorthand: **不要分条，写完整的自然段**.

## 6. Format And Evaluation Constraints

Follow ACM CCS CFP requirements with unaltered ACM `sigconf` style and page-limit compliance for main content. Keep evaluation security-relevant and centered on recoverability, fail-closed behavior, practical overhead, and reproducibility. Detector resistance or active-edit robustness must be labeled preliminary unless directly implemented and tested.

## 6.1 Temporary Experiment Pause

Until this pause is explicitly lifted by the user, do not run experiment pipelines in this repository, including `./scripts/run_all.sh`, `scripts/run_minimal_eval.py`, and similar long-running evaluation commands. Experiment execution is temporarily paused because runtime cost is too high at this stage. Keep Evaluation-related paper sections as clear placeholders and mark missing measurements/tables as pending.

## 7. Collaboration Rules

Read `../Ghostext` before making technical claims. Do not modify `../Ghostext` unless explicitly requested. Prefer small reviewable changes, separate facts from inferences and future work, and choose explicit caveats when uncertain.

## 8. Execution Pointers

Default pipeline entrypoint is `./scripts/run_all.sh`, but it is currently under the temporary experiment pause above and must not be executed unless the user explicitly asks to resume experiments. Repository detail, literature workflow, CCS policy cache, structure baseline, and expanded checklists are in `SPEC.md`.

## 9. Key Literature Requirement

The two key papers under `literature/key-paper/` are mandatory full-text reading before writing core technical positioning:

- `literature/key-paper/D19-1115.pdf`
- `literature/key-paper/2026-eacl-long-36-od-stega.pdf`

Abstract-only or summary-only reading is not sufficient for claims that depend on these papers.
