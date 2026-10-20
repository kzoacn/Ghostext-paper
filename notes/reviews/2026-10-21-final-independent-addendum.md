Final independent addendum: S&P 2027 revision

Review date: 2026-10-21, Asia/Shanghai. Checks were performed on 2026-10-20 UTC.

**Recommendation: weak accept. Confidence: moderate overall.**

I recommend weak accept for the frozen paper as a focused security analysis and implementation audit. The completed experiments and reproducible release strengthen the evidence, and the concrete regression and artifact problems identified in my original review have been addressed. The main contribution remains the public stopping likelihood and the separation that persists after matching the entire length marginal. The modest practical scope, concentrated novelty, and conditional real-model evaluation keep my recommendation at weak accept.

This is a new assessment of the final scientific snapshot. It supplements, and does not replace or edit, [my original review](2026-10-20-independent-sp2027-review.md). I inspected the final manuscript, completed data, source profiles, and anonymous archive. All reruns used my own temporary extraction of the final ZIP. I made no changes to the canonical manuscript, implementation, raw observations, PDF, or archive.

The reviewed working-repository scientific commits are `1c25344db3be9958470fd228f6478715532e3c31` for Ghostext-paper and `624bae9eacccbf955a6c491d4542254072c7ba77` for Ghostext. The identifying hashes are:

| Item | SHA-256 |
|---|---|
| `output/pdf/ghostext-sp2027.pdf` | `d59bbd0daaa94981a6a08f3d4f81bad60b265f3c240c49821860f5117638dd41` |
| `output/ghostext-sp2027-artifact.zip` | `a049f07125eada70d943af2758dbffcd9d49802a65b77852a91dd9f801e09cc0` |
| Original independent review | `bf4de2baa8c99cd42b076140c4eccfb8b8b6596600cd089d3ef9934dea257975` |

The mathematical conclusions survive the final changes. I found no error in the ideal RRC hazard calculation, the exact matched-length counterexample, the fixed nonuniform binary-IID separation proof, or the guarded coding bound under uniform segments and independent uniform guards. The finite-rotation-grid appendix supplies a useful bridge: when the quantization denominator divides the rotation grid, active token sampling remains exact and the public token/stop kernel has a uniform error bound that composes over the horizon. Its stated exclusions matter: this does not cover private rotations, recovery flags, verification-conditioned stopping, timing, or the cryptographic quality of the experimental pseudorandom generator. I independently reran the supplied finite-grid example; all eight message/failure settings give exact TV `1/96`.

The original NLS audit remains a synthetic counterexample to the encoder's diagnostic. My earlier independent execution of the corrected injective renderer reproduced complete-text TV `15/16` with reported KL zero, including all 256 messages and all 4096 natural two-symbol texts. I did not rerun that PyTorch-dependent harness during this final lightweight check. The final manuscript retains the synthetic model, disabled sentence completion, and limited transfer to other systems. It also retains the essential distinction between the published RRC midpoint rule and later verification-before-stop software.

The completed stopping cohorts now contain all 960 planned pairs, with unique case identifiers and exact agreement with manifest task membership. I independently checked the raw text hashes, token/probability lengths, quantized probabilities, and recomputed surprisals. The observed counts are:

| Source and model | Planned pairs | Stego complete | Control complete | Complete canonical matched pairs | Completed stego reverse failures |
|---|---:|---:|---:|---:|---:|
| Strict GPT-2 | 160 | 121 | 123 | 90 | 3 |
| Strict Qwen | 320 | 301 | 315 | 296 | 16 |
| Expanded GPT-2 | 160 | 160 | 160 | 160 | 4 |
| Expanded Qwen | 320 | 320 | 320 | 320 | 8 |

All four stopping analyses reproduced byte-identical `analysis.json` files. The completed strict Qwen results and the separate expansion cohorts add useful evidence that the measured signal is not solely a consequence of excluding strict-source generation failures. Expansion changes the candidate source, however, and was introduced after inspecting development failures. The final paper correctly calls it a separate post-hoc follow-up. The strict and expanded results remain conditional on their stated sources, public prompt/model/message length, and five held-out topic families. High AUC is still not a demonstrated low-FPR operating guarantee.

I independently checked the 40 GPT-2 and 80 Qwen delivery rows and reran both analyses; both resulting JSON files are byte-identical to the release. The Qwen interruption is now handled correctly. The first 64 raw rows reproduce the recorded prefix hash, and the next case is `01_zh_corner_cafe:r0:g128`. Because the unpersisted task received a fresh attempt budget, its original bounded-attempt and first-attempt outcomes remain unknown. The primary analysis excludes that case from outcome, rate, timing, and probe summaries. My direct recount gives:

| Model and guard | Primary trials | Delivered | First-attempt deliveries | Recorded attempts |
|---|---:|---:|---:|---:|
| GPT-2, `g=0` | 20 | 19 | 12 | 51 |
| GPT-2, `g=128` | 20 | 19 | 12 | 46 |
| Qwen, `g=0` | 40 | 39 | 33 | 59 |
| Qwen, `g=128` | 39 | 38 | 36 | 56 |

The resumed Qwen case succeeds in one recorded attempt, but the paper does not treat this as the missing original outcome. The original 40-case guarded plan has conservative counts of 38–39 bounded-attempt deliveries and 36–37 first-attempt deliveries. Unknown interrupted work is excluded from timing rather than counted as zero. I also confirmed the five low-entropy failed attempts in the uninterrupted Qwen legacy arm; the remaining failed attempts there and all failures in the other listed arms are token-filter failures.

The probe counts agree with the final tables. GPT-2 has nine complete matched pairs under the legacy guard and thirteen under the repaired guard; the corresponding admissible stego/control counts are `9/4` and `13/13`. Qwen has 37 matched pairs in each arm, with counts `37/19` and `37/37`. These results remove the measured zero-width rejection signal in those matched sets. They do not establish that the full authenticated packet satisfies the theorem's uniform-source assumption or that other distinguishers fail.

The specific issues in my original review are resolved or clearly bounded:

- The historical 18-control pilot is explicitly described as a floating-probability sampler with three raw-argmax fallbacks. The corrected audit reproduces its row-order pairing and visible lengths. It is not represented as a strict integer-frequency-Q experiment.
- The experimental `2B` token cap appears in the manuscript and command/protocol metadata. It remains distinct from the uncapped ideal theorem.
- The 40-case verified GPT-2 cohort is explicitly an unchanged-path check because it vetoed no stops. A separate diagnostic selects all three completed reverse failures in the original GPT-2 cohort. I checked their identities and saved original token/probability sequences: verification adds one, two, and two tokens, with saved independent text decoding failing before and succeeding afterward. This is a selected diagnostic, not a general recovery rate or an evaluation of current upstream RRC.
- The invalid visible-mutation regression expectation has been replaced by deterministic tests of a payload-preserving guard edit and a packet-changing authentication failure. The manuscript and implementation documentation explain that visible edits within a packet-bearing prefix can preserve the authenticated payload.
- Frozen source objects, transitive supplemental helpers, required data inputs, model revisions/hashes, dependency records, and explicit commands are now packaged. Later-captured helper/environment evidence is identified as supplementary rather than retroactively attributed to old manifests.

The final artifact checks were independently executable. Before modifying my extraction, `verify_artifact.py` verified all 268 indexed files and 13 source profiles, including complete cohort membership and source/data links. I then materialized all 13 profiles into separate temporary directories and checked every declared source, helper, and input hash. In particular, the historical probe and targeted reverse-failure profiles now stage the input records their scripts require.

Using the lightweight environment after checking that it had no Torch, Transformers, or llama.cpp installation, I ran the full extracted core suite with the extracted implementation on `PYTHONPATH`: **59 passed, 1 optional model integration test skipped, and 5 subtests passed** in 74.17 seconds. The earlier mutation-test failure is closed.

I also independently reran `run_codec_security_audit.py`, `audit_stopping_adapter.py`, `audit_rotation_grid.py`, `run_stopping_dp.py`, `audit_existing_evidence.py`, and `audit_legacy_controls.py`. Every resulting audit JSON was byte-identical to its released counterpart. This includes all 24 guarded exact-tree entries and the dynamic-program values through 2048 bits. Regenerating the ablation analysis, three generated evaluation tables, and both figure PDFs succeeded; the three tables and both figures were byte-identical to the release.

The retained public-feature replay reports cover 24 stopping texts and 12 delivery texts. I checked their case-selection rule, source-input hashes, text hashes, and saved output fields against the underlying observations. The stopping reports record exact probability agreement; the delivery comparisons reproduce the cached probe statuses and stopping positions. I did not independently rerun their neural forward passes. No new language-model inference, model download, or real-model experiment was performed for this final recheck. Stopping tapes are repeatable on the compatible recorded stack; authenticated delivery uses OS randomness and is statistically rerunnable, with saved texts available for replay. Neither fact establishes cross-hardware bitwise reproducibility.

I rendered and visually inspected all 13 pages of the final PDF. Figures, tables, equations, and appendix text are legible, with no clipping or overlapping content found. References start on page 11, which also contains the final main-paper table and discussion, so the conservative main-content count is 11 pages. The document uses the unmodified IEEEtran class, US Letter, and an empty author block. The ethics and AI-use appendices candidly leave the human authors' final content review and submission declarations unasserted.

I found no remaining blocking proof, numerical, or artifact defect for the paper's narrow claims. My positive recommendation rests on the exact stopping analysis and the disciplined distinction between coding fidelity, selection, and complete-text security. Broader deployment security, unknown-prompt or unknown-length attacks, and a low-FPR detector remain unestablished. The final evidence justifies **weak accept**, with the human authors still responsible for the manuscript and submission.
