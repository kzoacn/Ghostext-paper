**Independent review of the Qwen2.5 public-observable replay — 21 October 2026**

**Finding: I found no accounting, arithmetic, or statistical discrepancy in the completed public replay.** All 492 distinct public inputs and all 960 observation bindings are retained. The public traces also permit independent arithmetic verification of the original noncanonical text-receiver outcomes that the preceding saved-data review could not reconstruct. This note makes no overall venue recommendation. I used one numerical-computation thread, ran no model inference, made no external contact, and did not inspect the unfinished budget results or modify prior reviews, experiment data, sources, plans, or manuscript files.

**Assessed data and sources.** SHA-256 values:

- `results/sp2027-observable-qwen25/manifest.json`: `126b107e8b83d0e19271d17f24c8a116efddd1d591e074f95f5c16f233298846`.
- `results/sp2027-observable-qwen25/analysis.json`: `b58cbea7ac9e6a268870b826db5cf7df0048164a9bd57343e96abda7b500a34d`.
- `results/sp2027-observable-fidelity/qwen25.json`: `4458d5414b4a49a821258d650ec9ad45937271e5abfa1ad763ba5348b2a3ee38`.
- Original cohort manifest: `results/sp2027-upstream-qwen25/manifest.json`, `10f2993e31449f4cbb8c14ae717eb65e16139a1f3c75038e16df0a04797000e3`.
- `scripts/replay_upstream_observable.py`: `22cd89a04953df3bec2170ce5488c8d49081ff703d3e2e671525a2014905e9ff`.
- `scripts/observable_upstream_score.py`: `6b49c23e9903c28d2792fba5ef242cbe4b5e32a8abbfbcf6addcc574f4e98573`.
- `scripts/analyze_upstream_observable.py`: `d2d7211eab3cfd8d8634cc66370d66fc010c9472e81bf656198acc88e4593d6b`.
- `scripts/audit_observable_fidelity.py`: `016c0bd44e8994ccb9bf6753865203ec0e573bc2b24e051f035aa076d373efa2`.

I checked all nine replay source hashes, five pinned upstream-file hashes, 162 replay input hashes, 492 scored-case hashes, and 655 fidelity input hashes. The replay's model pins equal those independently verified in the preceding cohort audit. I rechecked the six smaller model/tokenizer files here and did not repeat the large weight-file hash.

**Complete public inputs and scores.** Independent code rebuilt every public input identity from exactly the public prompt, B, and published string, and reconstructed all bindings from the 160 original cases. The resulting task list and 480 positive/negative pairs match the frozen manifest exactly. Deduplication saves repeated model replay; it does not remove or reweight repeated observations in the analysis. Each arm retains 160 positive observations and 160 natural observations, including every recovery failure and every noncanonical string.

The pinned local tokenizer independently reproduces all visible token counts, Unicode code-point counts, prompt-prefix decisions, and continuation token sequences. I checked all 40,929 selected CDF entries in the 491 complete traces as exact rational differences, then independently recomputed every accumulated surprisal and `-abs(I_visible-B)` score. All agree exactly with the retained values. The public-scoring function receives the string and public context; it receives neither original token IDs, original CDFs, canonicality, recovery outcomes, class labels, secrets, nor rotation tapes. Canonicality and recovery flags enter reporting and post-score checks without determining analysis eligibility.

The remaining input is the fixed-endpoint development output for `c4_0092_b512_r3`. Its published string retokenizes across the prompt/continuation boundary. The independently confirmed prefix mismatch receives the predeclared negative-infinity score, encoded as a null score plus its explicit flag. Its visible counts remain 135 tokens and 527 code points. It is retained as a completed emission, not converted into a missing observation or execution failure. As a development positive, it affects neither the natural-development threshold nor the reported test metrics. There are no no-output observations, empty continuations, unsupported-token outcomes, zero-mass outcomes, or unresolved execution failures in this cohort.

Every public input has one recorded begin and one persisted event. The two workers follow their disjoint manifest-index partitions, with 246 inputs each on CPUs 6 and 7. Their per-worker intervals are ordered and do not overlap; no repeated begin or execution-failed event is present.

**Statistics and conditioning.** Direct pairwise comparisons reproduce the six test AUCs, with half credit for ties. I separately reproduced the higher 95th-percentile development thresholds, strict-greater TPR/FPR, Wilson intervals, per-prompt results, visible-length baselines, and all 5,000 prescribed prompt-cluster bootstrap draws using seed 20261028. The bootstrap calculation uses an independent matrix of positive/negative cluster comparisons. Each slice has 40 development pairs and 40 test pairs, from ten development and ten test prompt clusters with four repeats each.

| Arm | B | Public-score AUC [95% prompt-cluster interval] | TPR | Visible-token-count AUC | Code-point-count AUC |
|---|---:|---|---:|---:|---:|
| Unverified | 128 | 0.971875 [0.933125, 0.997500] | 0.600 | 0.496563 | 0.485313 |
| Unverified | 512 | 0.975000 [0.953125, 0.995000] | 0.525 | 0.497500 | 0.499688 |
| Verified | 128 | 0.966250 [0.926250, 0.995625] | 0.550 | 0.496563 | 0.482188 |
| Verified | 512 | 0.975000 [0.953125, 0.995000] | 0.525 | 0.497188 | 0.499688 |
| Fixed endpoint | 128 | 0.531875 [0.423125, 0.661250] | 0.025 | 0.498750 | 0.477500 |
| Fixed endpoint | 512 | 0.480625 [0.337500, 0.604391] | 0.050 | 0.499063 | 0.520625 |

The thresholds are `-2.8672870479865935` at B=128 and `-4.090928791992724` at B=512 in every arm. Each slice has zero observed false positives among 40 test natural outputs. This is not evidence of zero population FPR: the corresponding Wilson upper endpoint is approximately 0.0876, and the prompt bootstrap cannot create false-positive events absent from its observed clusters.

Every planned generation completes, so the all-attempt analysis, emitted-pair sensitivity, and separately conditioned all-emitted-string analysis retain identical observations and agree on all shared statistics. The latter reports zero undefined bootstrap resamples. No successful-delivery conditioning is involved. Both visible-length histograms differ between classes in every slice, even though their AUCs are near 0.5. Exact raw-token endpoint matching therefore must not be described as exact visible-length matching.

**Post-score fidelity.** Independent reconstruction reproduces all 960 fidelity records. There are 783 canonical bindings, representing 403 distinct public inputs, with exact equality of token IDs, selected CDF traces, and surprisals to their original paths. This includes 51,844 binding-level selected-mass comparisons; shared inputs are counted repeatedly where they are bound to different observations. All 177 noncanonical bindings remain included, with changed public token paths or the documented prefix mismatch. Original paths are compared after scoring and do not determine eligibility.

**Original text receivers.** Using the public traces, the original prescribed secret/rotation tapes, and each original receiver's Decimal precision, I independently reconstructed all 479 prefix-compatible text receivers, comprising 387 canonical and 92 noncanonical paths. All recovered-value comparisons agree with the original receiver outcomes. Every stored receiver public surprisal also agrees with the newly retained public trace, and every sender-probability-match flag has the expected value. The remaining prefix-mismatch outcome is independently confirmed without interval replay.

Thus the previous 93-output verification limit is resolved for this saved-data audit: 92 changed paths have arithmetic replay, and one has the prescribed prefix failure. Six of those changed paths recover successfully, all in the fixed-endpoint arm; the other 86 do not. Total published-text recovery remains 120/160, 125/160, and 77/160 for unverified, verified, and fixed endpoint respectively. This adds verification coverage without changing the earlier observations or review.

**Limits.** These checks establish consistency of the frozen software, saved public traces, numerical calculations, and original receiver outcomes. They do not independently attest the neural-model computation. The public score is a deterministic score of the published string's canonical tokenization, not its exact probability after summing tokenization preimages. The finite cohorts use public B/model/prompt, small prompt populations reused across models, and a specified paired reference. Neither high stopping-arm AUC nor near-chance fixed-endpoint AUC establishes a universal security result. The four-budget study remains outside this note.
