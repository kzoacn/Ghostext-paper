**Independent review of the unchanged-upstream Qwen2.5 cohort — 21 October 2026**

**Finding: the saved-data accounting, interval arithmetic, and reported canonical/raw-token statistics pass the independent checks described below.** I found no required correction. The retained records support completion of every frozen task, preservation of the interrupted worker's completed work, and execution of the supplemental assignments without duplicate recorded stages. This is a separate data review, with no new overall paper recommendation. I did not run model inference, contact an external service, or modify the experiment source, plan, manuscript, retained data, or earlier reviews.

**Assessed files.** SHA-256 values:

- `results/sp2027-upstream-qwen25/manifest.json`: `10f2993e31449f4cbb8c14ae717eb65e16139a1f3c75038e16df0a04797000e3`.
- `results/sp2027-upstream-qwen25/analysis.json`: `0abf85b96fca82958a9147c350a691442649c032aaee8e545e86a18509f3df8d`.
- `results/sp2027-upstream-qwen25/raw-token-sensitivity.json`: `c91644fa3f3623864797f7227ba474f43666e0212708ec219e7543457eed175b`.
- `results/sp2027-validation/upstream-qwen25-execution.json`: `49381400d014f42950b93928c826de64c285edc5017c58f5579edcf6f5893a40`.

I verified the seven experiment-source hashes, five pinned upstream-file hashes, seven model/tokenizer-file hashes, both manifest input hashes, all case hashes in the analysis, and all 423 input hashes in the execution receipt. The model is the pinned base `Qwen/Qwen2.5-0.5B`, revision `060db6499f32faf8b98477b0a26969ef7d8b9987`; the effective vocabulary is 151,665 tokens. I independently reconstructed the released-prompt deduplication and hash ranking, the ten-development/ten-test split, and the shuffled list of all 160 tasks. They agree exactly with the manifest.

**Independent arithmetic and serialization checks.** Standalone checking code, without importing the experiment or analysis functions, retokenized the published strings with the pinned local tokenizer. It reproduced context tokens, visible tokens, prefix-match flags, canonicality, text hashes, CDF differences, and cumulative surprisals for 1,120 stage/prefix records. The 91,383 mass-entry checks include shared prefixes and are not additional independent samples. Each case agrees with its seven persisted stages; natural controls are the prescribed prefixes of the saved independent natural stream. There are no unexpected case-stage directories or temporary files in the cohort.

Using the prescribed secret and rotation seeds and each record's Decimal precision, I reconstructed all 39,162 sender interval selections across the three arms. Every rotated point lies inside its saved selected interval. Reverse rotation reproduces all 480 original-token receiver outcomes. For both stopping arms, every tested stopping candidate, veto, and final acceptance agrees with the saved output; the verified stream extends the unverified stream under the shared tape. Each fixed endpoint equals its paired verified length and uses its independent prescribed secret/tape. Separately, all 13,059 natural sampling cells generated from the prescribed random-bit tape lie inside their selected rational CDF intervals, with the recorded bit consumption.

| Arm | Completed generations | Canonical outputs | ID recovery | Published-text recovery | Canonical matched pairs |
|---|---:|---:|---:|---:|---:|
| Unverified | 160/160 | 125/160 | 154/160 | 120/160 | 112/160 |
| Verified | 160/160 | 125/160 | 160/160 | 125/160 | 112/160 |
| Fixed endpoint | 160/160 | 137/160 | 89/160 | 77/160 | 117/160 |

All natural streams also complete. The six unverified ID failures are exactly the six cases with verified vetoes. They reject 12 candidate stops and add 15 generated tokens in total. The saved `rejected_stop_count` measures rejected candidates; it is not necessarily the difference in output lengths. Canonicality is also distinct from recoverability: the fixed-endpoint arm's 77 recorded text recoveries include six noncanonical strings.

There is an explicit verification limit for the text receivers. The 387 canonical sender outputs supply the same receiver token sequence as the original IDs, so their receiver arithmetic is covered by the reconstruction. For the remaining 93 outputs, the local tokenizer independently confirms the changed token sequence or prefix mismatch, and their reported outcomes agree across case files, stage files, and aggregate counts. This cohort does not retain the altered-path receiver CDF traces. I therefore did not independently rederive those noncanonical text-receiver outcomes. More generally, these checks establish consistency with the retained CDFs; they do not independently attest that the neural model produced those CDFs.

**Statistics.** Independent calculations reproduce all 18 summaries: canonical pairs, the further recovered-only selection, and raw-token pairs, for both payload sizes and all three arms. This includes AUC, development thresholds, TPR/FPR, per-prompt results where reported, Wilson intervals, and the prescribed 5,000 prompt-cluster bootstrap draws. A separate cluster-pair calculation reproduces the bootstrap intervals. No threshold or orientation was selected using test outcomes.

| Arm | B | Canonical test pairs | Canonical AUC | Raw-token AUC | Raw-token 95% prompt-cluster interval |
|---|---:|---:|---:|---:|---|
| Unverified | 128 | 38 | 0.981302 | 0.978750 | [0.948125, 0.997500] |
| Unverified | 512 | 19 | 1.000000 | 1.000000 | [1.000000, 1.000000] |
| Verified | 128 | 38 | 0.975762 | 0.973125 | [0.943750, 0.996250] |
| Verified | 512 | 19 | 1.000000 | 1.000000 | [1.000000, 1.000000] |
| Fixed endpoint | 128 | 39 | 0.529915 | 0.535625 | [0.421234, 0.662516] |
| Fixed endpoint | 512 | 18 | 0.506173 | 0.473750 | [0.339375, 0.602516] |

Every raw-token slice has 40 development and 40 test pairs. Canonical development counts are 34/21 for each stopping arm and 35/25 for the fixed-endpoint arm, for B=128/512 respectively. The raw-token TPRs are 0.60/0.70, 0.55/0.70, and 0.025/0.05 for the three arms in table order. Each raw slice has zero observed false positives among its 40 test natural outputs. These small clustered cohorts do not establish deployment behavior at a low population FPR; a degenerate empirical bootstrap interval is not a population certainty statement. The prescribed prompt population and tapes are reused across the two upstream model studies, so this replication does not supply an independent enlarged prompt sample.

The raw-token length AUC is exactly 0.5 because paired token endpoints match. This does not establish equality of published-string lengths. Canonical-pair selection excludes 48 pairs from each stopping arm and 43 from the fixed-endpoint arm, with particularly substantial exclusions at 512 bits. These are sensitivity analyses under the prospective follow-up plan; the JSON's inherited `primary` field names must not be mistaken for the new all-observable-string primary analysis. Near-chance fixed-endpoint AUC is consistent with the intended source-law control and does not itself prove indistinguishability or reliable delivery.

**Interrupted and supplemental execution.** The only repeated stage begin is `receiver_verified` for `c4_0092_b512_r3`. Its original begin precedes the recorded exit-143 observation, and its resumed begin follows that observation. The interruption record correctly leaves the termination cause unknown. All 109 files hashed before resumption remain unchanged, including the completed sender/control stages of that case. The resumed receiver uses the same frozen case, manifest, source hashes, and prescribed tape. Unpersisted interrupted work is excluded from the saved stage runtime, as the interruption record states.

Each of the 12 supplemental cases begins after its recorded launch assignment, matches its manifest index, uses the designated CPU affinity throughout all seven stages, and has exactly one begin/persisted pair per stage. The other 148 cases follow their original shard assignments. The original workers complete 40, 40, 40, and 28 cases; the supplemental workers complete 4, 4, 3, and 1. Within every CPU affinity, recorded case execution spans do not overlap, and the original workers' task indices increase. All 160 cases and 1,120 persisted stages are present. These records show no duplicate task execution, omitted outcome, replacement sample, or recovery-based inclusion, within the limits of an audit of retained journals rather than external execution attestation.

The complete all-string replay and four-budget study remain outside this review. Their frozen cohorts and outcomes require their own completed-data checks before a final full-paper assessment.
