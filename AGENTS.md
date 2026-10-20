# AGENTS.md

This file is the execution guide for the paper revision. Implementation details
and protocol requirements are in `../Ghostext/spec.md`.

## 1) Mission

This repository is for drafting the Ghostext paper (target venue: IEEE S&P 2027), organizing evidence-focused experiments, and keeping clear claim-to-evidence traceability.

The implementation source of truth is `../Ghostext`.

## 2) Hard Boundaries

- Follow the IEEE S&P 2027 CFP requirements.
- Keep IEEEtran 1.8b `conference,compsoc` style unaltered, using US Letter.
- Keep main-content page length compliant.
- Keep main-content length at **at least 7 pages** (excluding references and appendices), and at most 13 pages, with at most 18 pages in total.
- The user's 2026-10-20 request explicitly authorizes resumed experiments and iterative paper/implementation improvements for S&P 2027.
- Read `../Ghostext` before making technical claims.
- Changes to `../Ghostext` needed for this revision are authorized by the same request; keep protocol, tests, and specification consistent.

## 3) Writing Style

Use English for the full paper and all notes, and keep the tone friendly, clear, and direct with simple wording instead of complex phrasing. If possible, avoid turning every idea into bullet points and prefer natural paragraph-style academic writing. The writing style should imitate the two key papers under `literature/`, while still matching our own technical content and evidence level. Keep edits small and reviewable, clearly separate facts from inferences and future work, and use explicit caveats whenever uncertainty exists.

## 4) Working Title And Core Story

Use this as the working title (can be modified):

**Ghostext: Auditing Finite-Message Leakage in LLM Steganography**

Core setting:

- Three roles: `Alice`, `Bob`, and `Censor`.
- Alice uses a prompt, a password, and a secret message with Ghostext.
- Ghostext outputs a fluent `cover text`.
- Censor (passive observer) sees the text and attempts to distinguish it from
  an explicitly specified reference source.
- Bob uses the same prompt and password to recover the secret message.

## 5) Security Model And Claim Discipline

Assumed censor:

- Passive censor only (observes text only).
- The observer knows the model, prompt, algorithm, and public parameters, but
  not the password or private randomness. Message length is additionally public
  in the stopping-law analysis. Historical hidden-prompt claims are superseded.

Security goal:

- Censor should not distinguish stego text from natural text.

Technical basis:

- Distinguish the raw model, processed candidate source, integer coding law,
  complete stopped transcript, and successful-retry conditioning.
- Do not infer uniform packet bytes from authenticated-encryption security.
- The guarded codec has a coding-only bound against a stopping-matched
  reference. It does not prove full-text security against ordinary generation.
- Finite-message counterexamples and the stopping separation are the primary
  contributions; packet framing and stepwise token filtering are prior art.

Claim wording:

- Do not overclaim beyond implemented and tested evidence.

## 6) Evaluation Priorities

Keep evaluation security-relevant and practical:

- Recoverability / decoding success. 
- Practical overhead (runtime, token cost, throughput).
- Reproducibility (configs, seeds, models, prompts, scripts, versions).

For detector resistance and active-edit robustness:

- Label as **preliminary** unless directly implemented and tested in this project.

## 7) Literature Requirements

Before writing core technical positioning:

- Mandatory full-text reading of the two key papers under `literature/`.

Related-work scope must include:

- Core citations and citation chains that appear in the papers under `literature/`.

## 8) Reporting Expectations

When experiment pause is lifted, report basic but complete experimental data and parameters, including at least:

- model/version,
- decoding/encoding settings,
- prompt/password setup policy (without leaking secrets),
- dataset or text source,
- metrics and units,
- hardware/runtime context.
