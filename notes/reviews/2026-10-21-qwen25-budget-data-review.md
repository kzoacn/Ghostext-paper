**Independent review of the completed Qwen2.5 four-budget cohort — 21 October 2026**

**Finding: all accounting, reconstructible interval arithmetic, and reported summary statistics pass the independent checks described below.** I found no demonstrated discrepancy. The offline text-receiver audit has a specific remaining limit: 98 noncanonical outputs at the larger budgets lack full retained CDF traces for their changed token paths. Their outcomes remain included in the reported statistics, but this review does not independently rederive those 98 decodings. I ran no model inference, used one numerical-computation thread, made no external contact, and did not modify the experiment source, plan, retained data, manuscript, or prior reviews. No overall venue recommendation is issued.

**Assessed versions.** SHA-256 values, with data paths relative to `results/sp2027-budget-qwen25/` unless otherwise stated:

- `manifest.json`: `89714e4b55d10234036048fb3b2c55f2480c135e5435c58d7183bc8a4aba22f2`.
- `analysis.json`: `e757f72e708303acac824d963e1d3c5e3b6bf9a7ae378e19c9a3f169ba411792`.
- `recovery-schedule.json`: `322f786dacb3a5ab15879e93ce2a74a422d189dc5563816aa51e4e165e1706ac`.
- `interruptions/worker-2-01.json`: `9ee1c88fe42e418c2a29314df67906573f4ed8911e25d64d3ecdb70a800a84be`.
- `interruptions/worker-5-01.json`: `2f981d3115e9b8772da6470ba88701f30cbf83aa070a632e4e44e2efe5b23a80`.
- `assembly-receipts/c4_0203_b128_r3.json`: `7dab18f7bd793080f6eaa7643f8c300aa3d12420724445b9f89a1990308c2308`.
- `scripts/run_upstream_budget_curve.py`: `c89e555ec7bc30369324df6c7c0377bb0b96fc46a94d3728e99d8182dbdb9619`.
- `scripts/analyze_upstream_budget.py`: `872fab86666a811e11dd5f31c329ee5ccf5fe0af0344be34ada206cb8462dfc2`.
- `scripts/assemble_saved_budget_case.py`: `680f3489b088c8daee022502506e776fb0d8dbaccef7745302114a6d65f5a0a9`.
- Supporting public-trace analysis, `results/sp2027-observable-qwen25/analysis.json`: `b58cbea7ac9e6a268870b826db5cf7df0048164a9bd57343e96abda7b500a34d`.

All nine frozen source hashes, five upstream-file hashes, 162 frozen input hashes, and 160 budget-case hashes agree. The supporting public-trace manifest and all 492 case hashes also agree with the previously audited analysis. Model pins equal the previously verified generation and public-replay pins; I rechecked the six smaller model/tokenizer files without rehashing the large weight file.

**Fixed tasks and complete prefixes.** Independent code rebuilt the 160 tasks from the original cohort and verified `N` against each original verified endpoint. The four budgets are exactly `N`, `ceil(5N/4)`, `ceil(3N/2)`, and `2N`. They are assigned from the separate verified stream, before evaluating the fixed-endpoint stream's recovery. The latter uses its separately prescribed exogenous secret and rotation tape. Source inspection and the journals agree that the full `2N` stream and all four prefixes are persisted before receiver evaluation begins. No endpoint is chosen by testing whether that stream already recovers.

All 640 generation prefixes complete, and each case agrees exactly with its four prefix files and four receiver-stage files. I independently retokenized every published prefix, checked its visible-token sequence, prompt-prefix status, canonicality, text hash, probability list, and accumulated surprisal, and checked 75,195 CDF-mass entries. The four prefixes of each trajectory are nested in both tokens and CDFs. Their Decimal precision matches the reserve prescribed for the maximum endpoint. The two streams that cross the context-window limit have the expected trim counts.

Every new N-prefix matches its original fixed-endpoint tokens and selected CDFs. Their published strings, visible tokens, canonicality, and other common semantic fields agree as well. The numerical reserve and runtime differ as expected between the old N-only execution and the new 2N trajectory. I reconstructed all 26,118 sender interval selections on the 160 maximum-length paths using the prescribed tapes and checked all 640 original-token receiver outcomes by reverse rotation. All agree with the saved records.

**Retained recovery and rate results.** Each row below retains all 80 instances at its payload size. All generation statuses are complete; unsuccessful recovery comparisons remain in the denominators.

| B | Budget | ID recoveries | Text recoveries | Canonical outputs | Aggregate payload bits per prescribed token |
|---:|---|---:|---:|---:|---:|
| 128 | N | 39/80 | 39/80 | 77/80 | 4.304330 |
| 128 | ceil(1.25N) | 59/80 | 57/80 | 77/80 | 3.403124 |
| 128 | ceil(1.5N) | 69/80 | 67/80 | 77/80 | 2.852368 |
| 128 | 2N | 77/80 | 74/80 | 73/80 | 2.152165 |
| 512 | N | 50/80 | 38/80 | 60/80 | 3.835206 |
| 512 | ceil(1.25N) | 72/80 | 54/80 | 54/80 | 3.061286 |
| 512 | ceil(1.5N) | 76/80 | 58/80 | 53/80 | 2.553775 |
| 512 | 2N | 77/80 | 59/80 | 45/80 | 1.917603 |

Independent calculations reproduce all eight summaries, including per-prompt counts, recovery fractions, Wilson intervals, token-budget means/medians/totals, both reported rate definitions, and 5,000 prompt-cluster bootstrap draws with seed 20261028. Each recovery slice uses all 20 original prompt clusters with four repeats. At 2N, the ID-recovery cluster intervals are [0.9125, 1.0000] for B=128 and [0.9000, 1.0000] for B=512; the text-recovery intervals are [0.8625, 0.9750] and [0.6500, 0.8250]. These describe the small retained cohort rather than a delivery guarantee.

The aggregate rate divides all prescribed payload bits by all prescribed tokens, including failed recoveries. The separately reported mean averages individual `B/budget` ratios and is generally different. Neither calculation removes failures or chooses a favorable endpoint for an individual trajectory. The larger-budget results measure recovery and nominal token cost; no detector-resistance measurement accompanies them.

**Exact offline text-audit coverage.** I indexed retained sender and public-replay traces by the full prompt and token history. A receiver path was considered reconstructible only when its entire sequence had retained CDF observations for that same history. All 13,192 shared-history comparisons agree; observations were not joined across divergent histories.

| Budget | Canonical receiver arithmetic covered | Additional noncanonical arithmetic covered | Prefix mismatch confirmed | Noncanonical outcomes without a full CDF path |
|---|---:|---:|---:|---:|
| N | 137 | 22 | 1 | 0 |
| ceil(1.25N) | 131 | 0 | 1 | 28 |
| ceil(1.5N) | 130 | 0 | 1 | 29 |
| 2N | 118 | 0 | 1 | 41 |

Thus 538 text paths have arithmetic coverage: 516 canonical inputs inherit the checked ID computation, and 22 noncanonical N inputs are independently replayed using the completed public traces at the new receiver precision. Their outcomes and recorded public surprisals agree. Four prefix mismatches, all from the same original case at different budgets, are independently confirmed by tokenization. The remaining 98 larger-budget noncanonical outcomes have consistent saved case/stage records and complete aggregate accounting, but no full changed-path CDF trace is available. Forty of those 98 recorded outcomes are successful recoveries. Their inclusion in the table should not be read as independent arithmetic verification of their decoding.

**Interruption preservation and assembly.** The 160 journals contain 2,241 events: one generation stream and four persisted prefixes per trajectory, four persisted receiver stages per trajectory, and one additional receiver begin from the documented interruption. No generation stream or prefix was rerun in the recorded events. All generation prefixes were persisted before receiver evaluation. Model-stage intervals on each recorded CPU affinity do not overlap.

The exit-143 interruption affects `receiver_n165` of `c4_0203_b512_r2`; its cause remains unestablished. All 60 preserved-file hashes match, including that case's four prefixes and two completed receivers. The continuation on CPU 10 completes the remaining receiver stages and restarts only the unfinished `receiver_n165` stage. The other interruption reports an allocation error while writing the final summary for `c4_0203_b128_r3`, after all eight prefix/receiver observations were saved. All 53 preserved-file hashes match. Neither infrastructure interruption becomes a new experimental sample or deletes a failed recovery. The saved timings exclude unpersisted interrupted work.

For the latter case, I independently rebuilt the final JSON solely from the ten receipt inputs: the frozen manifest, original case, four prefixes, and four receiver files. The reconstructed output is byte-for-byte identical to the retained case and matches the receipt's output hash. The assembly source performs this join without model inference or new randomness. The twenty remaining tasks from the terminated original shard match the frozen recovery schedule, use unchanged endpoints and source pins, and begin after their individual launch records. They have no duplicate stage starts. All planned cases remain included; scheduling by the preassigned N changes execution order without selecting on those tasks' recovery outcomes.

For an exact execution-record binding, the SHA-256 of the compact, key-sorted JSON map from paper-repository-relative path to file SHA-256 is `6ef7cce8e779f920b2898bc077b2261d3eafcc163bb37c7ad5f25753a5b09943`. The map covers all 160 journals, 20 individual launch records, both interruptions, the assembly receipt, `launch-commands.json`, and `recovery-schedule.json` (185 files).

These are checks of retained evidence and frozen calculations, not external attestation of model computation or process lifetime. The observed cohort exercises receiver failures and infrastructure recovery; no generation-failure trajectory occurs here, so the later-generation-failure branch is not empirically tested by this cohort. The remaining larger-budget noncanonical receiver limitation is stated above and does not alter the retained recovery totals.
