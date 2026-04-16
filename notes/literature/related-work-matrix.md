# Related Work Matrix (Ghostext Draft)

## Objective

Provide concise positioning against key papers, with clear separation between implemented overlap and non-overlap.

## Mandatory Anchors

The two papers under `literature/key-paper/` are mandatory anchors for this draft:

- Ziegler et al. 2019 (Neural Linguistic Steganography)
- Huang et al. 2026 (OD-Stega)

## Matrix

| Work | Core idea | Security framing | Engineering concerns highlighted | Relation to Ghostext |
|---|---|---|---|---|
| Ziegler et al. 2019 (Neural Linguistic Steganography) | Arithmetic coding on neural LM next-token distributions | Distribution matching and KL-based view | Truncation, quality-vs-KL tradeoff, practical generation evaluation | Ghostext directly inherits this arithmetic-coding + LM framing, including Alice/Bob/Censor role structure and distribution-preserving objective language. |
| Huang et al. 2026 (OD-Stega) | Optimize replacement distribution under divergence constraints | Relative security under constrained divergence | Tokenization mismatch, truncation + optimization coupling, detector-facing sweeps | Ghostext uses this paper as the main reference for controlled security-capacity tradeoff wording and tokenization-risk discussion, but does not yet implement OD optimization itself. |
| Shen et al. 2020 (Self-adjusting AC) | Adaptive coding to improve imperceptibility | Near-imperceptibility emphasis | Adaptive tuning and practical coding | Ghostext differs by emphasizing protocol verifiability and explicit retry/failure semantics over adaptive strategy exploration. |
| Ding et al. 2023 (Discop) | Distribution-copy-based secure steganography | Provable-security style in practice | Practical secure construction choices | Ghostext is a complementary engineering path rather than a replacement. |
| de Witt et al. 2024 (MEC-based perfect security) | Minimum entropy coupling for perfect security | Strong theoretical guarantees | Coupling construction complexity | Ghostext should not claim equivalent guarantees; use as upper-bound reference point and contrast with practical constraints. |

## Citation Chain To Expand Later

The two mandatory key papers reference additional lines of work that should appear in final related-work prose:

- Earlier linguistic steganography (edit-based and generation-based baselines).
- Markov and RNN-era generation methods.
- Recent LLM-era steganalysis and detector literature.
- Perfectly secure and public-key steganography lines where relevant.

## Drafting Rules

- Use direct language and keep claims narrow.
- If a statement is not implemented in `../Ghostext`, mark it as planned or external.
- For detector robustness or active-edit resilience, explicitly label as preliminary in current draft.
