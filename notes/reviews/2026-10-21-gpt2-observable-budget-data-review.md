**Independent GPT-2 observable-output and budget data review — 21 October 2026**

**Finding: no accounting or numerical correctness error found in the reviewed results.** The primary observable analysis retains the intended complete cohort, and the budget summaries agree with independent calculations. Confidence is high for the saved-data arithmetic and accounting, with the text-recovery verification limit stated below. This note makes no new overall recommendation. Earlier reviews remain unchanged. I ran no language-model inference and did not modify the plan, experiment source, manuscript, or retained results.

**Exact records reviewed.** Both cohorts bind the frozen follow-up plan SHA-256 `776778d862924f1b12bf77bac16fb1f2a31d6868fc7c7da62ba7facf4ece71f2`.

- `results/sp2027-observable-gpt2/manifest.json`: `fad68cbe7528ae57c7b422ab54ec4ed117196c6632c4431e0fe7ec52e50c01df`; `analysis.json`: `2325cbb0f26ee0e0b94dccc001f629c52c73ac0844942ebf7128140342ea4203`.
- `results/sp2027-budget-gpt2/manifest.json`: `bc0a6d42d5cec27d8119722d86ae6527bf4a42b104d0d6366eb738ee6ca04a88`; `analysis.json`: `ed410159090fb653f15eb916c02725664ecd444b14a9265d88d270d819ac4a0c`.
- `results/sp2027-observable-fidelity/gpt2.json`: `c2082346e01e3d24dbcb6f021c02f8e3ca89f2621cb73d40ac480029b66fc70d`.

**Observable-output accounting and derivation.** I verified all 480 arm/case pairs and 960 positive/control bindings against the original 160-instance cohort. They map to exactly 482 distinct public inputs, without missing or duplicate case/arm bindings. Deduplicated inputs are reused consistently; the 960 bindings are not 960 independent texts. Every generation and public replay completes. All 174 noncanonical complete bindings remain included, representing 88 distinct noncanonical inputs. The 786 canonical bindings reproduce their original IDs and CDF traces, including 40,925 selected-mass comparisons. I independently checked all individual fidelity records and both analyses' case-hash maps. All 18 source-hash entries and 324 input-hash entries in the two manifests match.

Using the pinned tokenizer without model inference, I independently retokenized every public string and checked its prompt boundary, continuation IDs, full-string token count, Unicode code-point count, and text hash. All 27,047 selected masses in the distinct-input replay equal the recorded CDF differences. Recomputing cumulative information and `-abs(I_visible-B)` reproduces every score exactly. The scorer takes public inputs only; canonicality and receiver outcomes enter later diagnostics, not score construction or primary eligibility.

Direct pairwise AUC calculations and a separate prompt-block bootstrap reproduce the reported estimates and intervals. Each row below uses 40 development and 40 held-out pairs, with ten held-out prompt clusters. Thresholds are the prespecified higher development-control 95th percentiles, `-5.74470951680081` at 128 bits and `-5.567879902378479` at 512 bits, with strict-greater decisions.

| Arm | Bits | AUC [95% prompt-cluster interval] | TPR / FPR |
|---|---:|---|---|
| Both stopping arms | 128 | 0.923125 [0.865, 0.9725] | 31/40 / 7/40 |
| Both stopping arms | 512 | 0.97125 [0.925, 0.999375] | 30/40 / 0/40 |
| Fixed endpoint | 128 | 0.54875 [0.41125, 0.70189] | 8/40 / 7/40 |
| Fixed endpoint | 512 | 0.535 [0.42186, 0.653125] | 4/40 / 0/40 |

The independently calculated length baselines also match. For verified stopping, token-count AUCs are 0.5059375/0.4934375 and character-count AUCs are 0.5728125/0.511875. The unverified 128-bit character AUC is 0.5734375; its other values coincide. Fixed-endpoint token-count AUCs are 0.5021875/0.4971875 and character-count AUCs are 0.499375/0.485. None of these held-out visible-length histogram pairs is exactly equal. Accordingly, this follow-up supports an all-observable-output result on the retained GPT-2 cohort, not an exactly observable-length-matched claim. The analysis remains retrospective, and 0/40 false positives does not establish a low-FPR deployment operating point.

**Budget accounting and recovery.** All 160 cases have all four prescribed endpoints, totaling 640 completed prefix records. Integer-ceiling budgets, prefix-file contents, receiver-stage records, chronological prefix persistence, nested IDs/CDFs, and numerical precision agree with the plan. There is no context trimming. Every original-N prefix independently matches the earlier fixed-endpoint IDs and selected CDFs: 160/160 for both comparisons.

The entries below are **ID/text recovery successes, each out of 80 planned instances**.

| Bits | N | ceil(1.25N) | ceil(1.5N) | 2N |
|---|---|---|---|---|
| 128 | 39 / 35 | 59 / 53 | 72 / 63 | 79 / 70 |
| 512 | 35 / 26 | 64 / 48 | 75 / 56 | 79 / 59 |

I independently reconstructed the prescribed secret and rotation tape and checked the rotated target against all 18,026 selected intervals in the maximal streams. A separate Decimal inverse calculation reproduces all 640 ID-recovery outcomes. It also reproduces 506 text-recovery outcomes: all canonical paths, plus all noncanonical original-N texts using their existing public replay CDFs. Thus all 160 N-endpoint text receivers are independently covered. Budget recovery fractions, prompt-cluster intervals, canonicality counts, and both mean and aggregate prescribed-token rates match independent calculations. At 2N, the combined counts are 158/160 ID recovery and 129/160 text recovery. Prescribed-token rates include unsuccessful recovery and should retain that denominator description.

**Verification limit and failure handling.** The other 134 noncanonical text receivers, exclusively at larger budgets, retain execution summaries but not their retokenized CDF traces. Their reported outcomes, including 46 successes, are counted correctly; I cannot independently reconstruct those outcomes without additional traces or new inference. I found no contradictory record. This limit should be preserved when describing what this review verified.

Both analyzers and the fidelity audit reproduced byte-identically in a separate temporary copy. The synthetic audit passed all twelve scorer and persistence checks, including unsupported public inputs, negative-infinity ties, execution-error propagation, unmatched emissions, later failures, and resume preservation. The implementation now retains class-wise emitted-string summaries as well as the labelled emitted-pair sensitivity. Actual GPT-2 records contain no generation or scoring failures, so those fallback paths are supported by code inspection and synthetic checks rather than failures in this cohort.
