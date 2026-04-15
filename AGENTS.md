# Ghostext-paper Agent Guide

## 1. Mission

This repository is for writing the Ghostext paper targeting ACM CCS 2026.

The implementation source of truth is `../Ghostext`. This repository is for:

- paper drafting
- experiment orchestration
- figure/table generation
- claim tracking and evidence bookkeeping

Default principles:

- security-first framing (not AI benchmark framing)
- no claim without evidence
- no positioning statement without literature evidence

## 2. Source Of Truth

When writing technical statements, prioritize these sources in order:

1. `../Ghostext/src/ghostext/*.py`
2. `../Ghostext/tests/*.py`
3. `../Ghostext/spec.md`
4. `../Ghostext/README.md`

If spec text and code differ, treat code + tests as ground truth, then record the discrepancy in paper notes.

## 3. Current System Understanding (from codebase)

Ghostext is an encrypt-then-steganography pipeline over next-token distributions.

Key facts already implemented in `../Ghostext`:

- `opaque packet v2`: encrypted internal header + encrypted body
- key derivation: `scrypt` master key + `HKDF-SHA256` key separation
- AEAD: `ChaCha20-Poly1305`
- deterministic recoverability requires same model, tokenizer, prompt, seed, and protocol-sensitive settings
- candidate policy: top-p + max-candidates + minimum entropy threshold
- retokenization stability guard is enforced before embedding
- integer quantization and finite-interval codec are used for segment encoding/decoding
- fail-closed behavior exists for mismatch/mutation/sync errors
- bilingual test coverage exists (Chinese and English toy backend round-trip)
- real local backend path exists (`llama.cpp` with Qwen GGUF), plus toy backend for protocol testing

## 4. CCS Framing (Security-First)

Primary framing:

- This is a computer security paper on practical text steganographic communication under an explicit threat model.
- LLMs are used as a channel construction mechanism, not as the paper's main novelty axis.
- Writing should prioritize security properties, failure modes, assumptions, and reproducibility.

Avoid drifting into:

- pure generative quality storytelling
- broad AI model comparison without security relevance
- benchmark-style "model SOTA" narrative

## 5. Claim Boundaries For CCS Draft

Safe claims (allowed by current implementation/tests):

- deterministic decode under fully matched runtime configuration
- strong fail-closed behavior under prompt/seed/config/text mismatch
- encrypt-before-hide design with authenticated decryption failure on wrong key/tampering
- protocol-oriented engineering with explicit configuration fingerprint checks

Unsafe claims (do not make unless new evidence is added):

- robustness under active text edits/reordering/deletions
- resistance to dedicated steganalysis detectors
- cross-model or cross-version decode compatibility
- production-grade censorship resistance

## 6. Required Writing Workflow

For every nontrivial technical paragraph:

1. Identify the exact claim and its threat-model scope.
2. Attach at least one evidence pointer (code/test/experiment/literature).
3. Mark claim maturity in internal notes:
   - `implemented + tested`
   - `implemented only`
   - `planned`
4. If not `implemented + tested`, add explicit caveat text in draft.

Never present planned experiments as completed.

## 6.1 Related Work Is Mandatory

Before locking Introduction/Related Work/Evaluation positioning, conduct a focused literature scan.

Minimum requirement for each major claim axis (security model, LLM steganography method, detectability, robustness, reproducibility):

1. Find representative papers (classics + recent results).
2. Record why each paper is relevant/different from Ghostext.
3. Mark evidence type:
   - `peer-reviewed`
   - `preprint`
   - `benchmark/dataset/tool`
4. Track uncertainty explicitly (for claims we still need to verify).

Do not write novelty claims before completing this step.

## 7. CCS Template And Format (Must Follow Official CFP)

Use ACM CCS 2026 official formatting requirements from the conference CFP page:

- ACM double-column `sigconf` format
- at most 12 pages main content (bibliography/appendices/supplementary excluded per CFP wording)
- unaltered ACM template (no margin/font/whitespace hacks)
- retain required ACM metadata blocks

Primary references:

- CCS 2026 CFP (official):  
  https://www.sigsac.org/ccs/CCS2026/call-for/call-for-papers.html
- ACM proceedings template page:  
  https://www.acm.org/publications/proceedings-template

CFP also points to `sample-ccs2026.tex` and `sample-ccs2026.pdf`; prefer those when accessible.

## 8. Paper Structure Baseline

Use this baseline unless we intentionally change target framing:

1. Abstract
2. Introduction
3. Problem Setting and Threat Model
4. Design Overview
5. Protocol and Implementation Details
6. Evaluation
7. Limitations and Ethics
8. Related Work
9. Conclusion

Default narrative order:

- why recoverability is hard in LLM stego
- how Ghostext enforces synchronized decoding
- what can be reproduced today
- where boundaries remain

## 9. Evaluation Strategy (Security Paper, Not Benchmark Paper)

Keep evaluation focused and security-relevant. Minimum expected set:

1. Correctness and recoverability:
   - matched configuration round-trip success
   - bilingual cases are a plus, not the core claim
2. Fail-closed and boundary behavior:
   - wrong prompt/seed/passphrase/config mismatch
   - text mutation or mismatch should fail predictably
3. Practical overhead:
   - bits/token, token overhead, encode/decode throughput
4. Reproducibility essentials:
   - deterministic reruns and environment disclosure

Not mandatory by default:

- large ablation grids
- extensive model-to-model leaderboard comparisons

If detector-resistance is discussed, label it as preliminary unless a dedicated steganalysis section is completed.

## 10. Reproducibility Rules

- fix random seeds and record them in artifacts
- record model file identifier and hash-related metadata
- keep raw outputs; do not report only manually copied summaries
- scripts must be rerunnable from command line
- all figures/tables must be regenerable from saved raw results

## 11. Collaboration Rules For Agents

Agents working in this repository must:

- read `../Ghostext` before writing technical claims
- avoid modifying `../Ghostext` unless explicitly requested
- prefer small, reviewable changes
- clearly separate facts, inferences, and future work
- keep language conservative and security-accurate

When uncertainty exists, choose explicit caveats over optimistic wording.

## 12. Immediate Next Steps

1. Build a related-work reading list and security positioning notes.
2. Build CCS-format paper skeleton from official template requirements.
3. Draft threat model, assumptions, and security goals first.
4. Implement only the necessary experiment scripts for correctness/fail-closed/overhead.
5. Maintain an internal evidence note file to avoid unsupported claims in writing.

## 13. Current Repository State (Implemented)

Already prepared in this repository:

- CCS policy notes:
  - `notes/policies/ccs2026_requirements.md`
  - cached official files:
    - `notes/policies/ccs2026_cfp.html`
    - `notes/policies/sample-ccs2026.tex`
    - `notes/policies/sample-ccs2026.pdf`
- Literature notes:
  - `notes/literature/related_work_matrix.md`
  - `notes/literature/reading_list.md`
  - `notes/literature/claim_scoping_notes.md`
- Paper skeleton:
  - `paper/main.tex`
  - section stubs in `paper/sections/`
  - bibliography: `paper/references.bib`
- Minimal evaluation pipeline:
  - `scripts/run_minimal_eval.py`
  - `scripts/make_tables.py`
  - `scripts/run_all.sh`
  - outputs under `results/`

Default execution entrypoint:

```bash
./scripts/run_all.sh
```

## 14. Codex Writing Preferences (User-Specified)

For this paper, use English throughout and prefer natural, friendly prose in full paragraphs. Avoid overusing bullet lists unless a list is strictly necessary for clarity. Keep wording simple and readable, and avoid unnecessarily complicated vocabulary.

Use the working title: "Ghostext: an almost perfect stenography via large language model and arithmetic coding". In the main narrative, describe the communication setting with three roles: Alice, Bob, and Censor. Alice uses a shared prompt and password together with her secret message as input to Ghostext, and Ghostext outputs a cover text. The passive Censor only inspects the text and should see nothing suspicious, so the message is allowed to pass. Bob, using the same prompt and password, recovers the original secret message.

When describing security, use a passive-censor threat model: the censor observes only the transmitted text and does not know the prompt or password. The target claim is indistinguishability between stego text and natural text under this passive setting. Keep the claim conservative and scoped to this model.

When explaining the technical intuition, highlight two linked points. First, modern language models provide next-token distributions that approximate natural-language generation behavior. Second, the embedding process should preserve that distributional behavior as much as possible. Connect this to the system design: encryption makes the payload computationally indistinguishable from randomness, and arithmetic coding maps that randomized payload into token choices by fully using the available entropy in the next-token distribution.

The paper may use "almost perfect" to describe this design intent: the scheme is designed to preserve the model distribution while efficiently consuming available entropy for embedding. This wording should be presented as a scoped claim tied to explicit assumptions, implementation constraints, and available evidence, not as an unconditional universality claim.

For related work, include both LLM steganography and LLM watermarking literature, because they share technical overlap in token-distribution shaping, coding over token probabilities, and detectability/recoverability tradeoffs. Position Ghostext relative to both lines of work.

For experiments, include a minimal but concrete demonstration that the system works in practice, and report basic metrics and parameters (for example success rate, fail-closed behavior under mismatch, bits per token, throughput, and key runtime settings).

In the paper narrative (Abstract, main sections, appendices), do not mention the toy backend. Treat the toy backend strictly as an internal protocol-testing utility, not as paper-facing experimental evidence or positioning.
