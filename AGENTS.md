# AGENTS.md

This file is the compact execution guide for agents in this repository. Detailed policies, rationale, and extended checklists are moved to `SPEC.md`.

## 1) Mission

This repository is for drafting the Ghostext paper (target venue: ACM CCS 2026), organizing evidence-focused experiments, and keeping clear claim-to-evidence traceability.

The implementation source of truth is `../Ghostext`.

## 2) Hard Boundaries

- Follow ACM CCS CFP requirements.
- Keep ACM `sigconf` style unaltered.
- Keep main-content page length compliant.
- Keep main-content length at **at least 7 pages** (excluding references and appendices), while still complying with ACM CCS limits.
- Until this pause is explicitly lifted by the user, do **not** run experiment pipelines in this repository.
- Read `../Ghostext` before making technical claims.
- Do **not** modify `../Ghostext` unless the user explicitly asks for it.

## 3) Writing Style

Use English for the full paper and all notes, and keep the tone friendly, clear, and direct with simple wording instead of complex phrasing. If possible, avoid turning every idea into bullet points and prefer natural paragraph-style academic writing. The writing style should imitate the two key papers under `literature/`, while still matching our own technical content and evidence level. Keep edits small and reviewable, clearly separate facts from inferences and future work, and use explicit caveats whenever uncertainty exists.

## 4) Working Title And Core Story

Use this as the working title (can be modified):

**Ghostext: A Distribution-Preserving LLM Steganography with Authenticated Packet Framing**

Core setting:

- Three roles: `Alice`, `Bob`, and `Censor`.
- Alice uses a prompt, a password, and a secret message with Ghostext.
- Ghostext outputs a fluent `cover text`.
- Censor (passive observer) only sees the text and lets it pass as normal language.
- Bob uses the same prompt and password to recover the secret message.

## 5) Security Model And Claim Discipline

Assumed censor:

- Passive censor only (observes text only).
- No knowledge of the prompt or password.

Security goal:

- Censor should not distinguish stego text from natural text.

Technical basis:

- LLM supplies next-token distributions close to natural language.
- The encoding process must not distort that next-token distribution.
- Encryption makes message bits computationally indistinguishable from randomness.
- Arithmetic coding uses nearly all available entropy from the next-token distribution.
- The scheme aims to preserve model output distribution while maximizing embedded information.

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
