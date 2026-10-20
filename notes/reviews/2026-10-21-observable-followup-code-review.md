# Independent correctness review of the observable-output follow-up

Review date: 2026-10-21. This is a code and protocol review against `notes/sp2027-observable-followup-plan.md`. It assigns no acceptance grade and leaves the previous review unchanged. I did not edit the manuscript, perform model inference, or make external network requests.

I found no scientific correctness blocker in the inspected follow-up implementation. The public scorer does not consume sender-only inputs; the analysis retains every planned binding and handles negative-infinity ties correctly; the budget loop persists reached endpoints before continuing and preserves them across the tested later failure and interruption. These conclusions concern the implementation and synthetic checks, not the empirical performance or compatibility of the new model run.

## Public score and every-output accounting

`observable_upstream_score.public_score` receives the published string or `None`, the public prompt and bit length, and the model/tokenizer/upstream module. It independently tokenizes the full published string with special-token insertion disabled, constructs the prompt context independently, and uses a fresh upstream incremental stepper for the continuation. Original IDs, sender intervals, canonicality, recovery results, secret bits, rotation seeds, and class labels are absent from its arguments and calculation.

The score uses Decimal differences of the replayed CDF boundaries and is `-abs(I_visible - B)`, as planned. It is a score of the chosen retokenization, not the probability of the rendered string summed over serialization preimages. This distinction is stated in the code and must remain in the empirical description.

No output, prompt-prefix mismatch, empty continuation, a token outside the supported vocabulary, and zero source mass produce explicit negative-infinity decisions. Character and full-string token counts remain defined for emitted unsupported strings; only the no-output observation receives zero counts by convention. Nonmonotone CDFs and execution failures raise exceptions. The replay worker logs execution failure and leaves the public task unfinished, so an infrastructure exception is not silently converted into a negative-infinity classification.

`replay_upstream_observable.prepare` verifies the entire original cohort before constructing the new tasks. It maps a failed generation to `None` even when the archived harness record contains a private failed prefix. Complete strings enter regardless of canonicality or receiver success. Binding records retain those fields as diagnostics, but only the public tuple `(prompt, B, text)` determines a scorer task.

Deduplication is safe here: identical public inputs are computed once, while every original arm/class binding remains in the analysis. I independently reconstructed the frozen GPT-2 manifest's public hashes and bindings. Its 160 original instances contribute 480 arm pairs and 960 output bindings, backed by 482 distinct public inputs. No binding was lost through deduplication or eligibility filtering. All 960 underlying generation bindings in that original GPT-2 cohort are complete; this is a check of the input cohort, not a report of completed new public-score replays.

A separate synthetic manifest test retained noncanonical and recovery-failed complete strings, hid an injected private failed prefix, and preserved all six bindings from a two-case fixture while deduplicating them into two public inputs. This tests the observer boundary in the runner as well as in the scorer itself.

## Infinity ties, thresholds, and unmatched emissions

The all-attempt analysis keeps both observations from every planned pair. Negative infinity is represented in JSON by `score: null` and an explicit flag, then converted to `-inf` for ranking and threshold comparisons. The higher empirical 95th percentile is implemented by the appropriate ordered index, and decisions use strict greater-than. Thus a negative-infinity observation does not pass a negative-infinity threshold merely by tying it.

The imported AUC function uses average ranks for ties. I compared it with a direct pairwise win/half-tie calculation on 720 synthetic cases, including all-infinite scores, mixtures of finite and infinite scores, and unequal class sizes. All comparisons agreed. The retained audit also checks a negative-infinity development threshold with AUC `0.75`, TPR `0.5`, and FPR zero.

The emitted-pair sensitivity is explicitly separate from `summarize_emitted_strings`. The latter conditions each class only on its own complete emission. It retains an emitted positive when its paired natural generation failed, and vice versa. It also retains complete strings whose public score is negative infinity because their public tokenization is unsupported. I checked this last case separately: it remains in the emitted-string denominators and contributes an ordinary tie, not an exclusion.

For the separately conditioned emission analysis, both classes use the same sampled prompt clusters. A resample lacking either class is recorded as undefined rather than being assigned a fabricated AUC or silently replaced by another draw. Its reported interval is consequently based on the defined resamples; the undefined count and stated scope must accompany it when nonzero.

Full-string token-count and Unicode code-point-count AUCs have the fixed higher-is-positive orientation. The code does not assert that raw endpoint pairing survives serialization as equal visible lengths. The all-attempt/no-output experiment and the emitted-string analyses remain distinct, as the plan requires. A passive observer is not thereby credited with observing unsent attempts.

## Budget assignment and persistence

`run_upstream_budget_curve` assigns N from the recorded verified endpoint, or the prescribed `2*B` cap when verified generation failed. A synthetic preparation check confirmed that a failed three-token private prefix at B=8 produces N=16, not N=3. The four budgets use exact integer ceilings. They do not depend on whether the separate fixed-endpoint stream has already recovered its payload.

The stream uses the existing exogenous secret/tape namespace. It reserves Decimal precision for the maximum 2N endpoint, then uses the unchanged upstream rotation, selection, and model-stepper primitives. Each prefix record contains that precision; the receiver helper restores it for its separate replay. The N-prefix comparison with the earlier fixed-endpoint record is diagnostic only and is not used to select or replace the new trajectory. A possible difference caused by the larger numerical reserve is therefore observable rather than silently filtered away.

The persistence order is correct. A reached endpoint is serialized and atomically saved before the next model step. The snapshot copies both the token list and the observation list, so later continuation cannot extend an earlier record in memory. If a later generation operation fails, only endpoints not yet reached receive the failure status. Earlier completed prefixes remain complete and receive their own receiver checks.

The retained synthetic audit injects a failure after five generated tokens with budgets 4, 5, 6, and 8. It confirms that the first two records remain complete, while only 6 and 8 fail with a five-token diagnostic prefix. It separately injects `KeyboardInterrupt`, resumes the prescribed tape, and verifies that the previously persisted endpoint files remain byte-identical.

On resume, existing observations are compared semantically, excluding only elapsed time. A different replay raises an error rather than overwriting the earlier observation. Receiver stages and final cases are persisted separately. Both follow-up analyzers refuse an incomplete planned case set; I exercised that rejection for each analyzer. An unresolved infrastructure or resume discrepancy therefore cannot silently shrink the reported cohort.

The budget analysis retains all planned instances in recovery fractions. A generation failure contributes no receiver success. The rates are explicitly payload bits per prescribed token budget, including failed generation or decoding; they are not achieved-delivery throughput. The larger budgets carry no detector-resistance claim.

The receiver helper is independent of the sender's interval state and uses the unchanged extraction function. When original IDs and retokenized text yield exactly the same receiver input, it reuses the already computed receiver result and records that fact. Describe this as replay of each distinct receiver input, rather than two physically separate model executions in every canonical case.

## Frozen functions and the second-model generalization

I verified all five cached upstream files against the hard-coded hashes at revision `dae326259e4fca8bc4fcf460dafdbc0e88a0a71a`, without fetching anything. The upstream core hash is `e45a4df5eebc86881d606f2fd6c3cbab5729252dce96e5ae1a7ba424be02ec4a`. The existing `upstream_rrc_experiment.py` and `fetch_upstream_rrc.py` also match their hashes in the original GPT-2 generation manifest. The follow-up does not patch the upstream sender, extractor, arithmetic functions, or model stepper.

The `run_upstream_rrc.py` changes add backend/plan selection, model-dimension and pin checks, explicit float32 loading, an asserted parameter dtype, and CPU-affinity logging. The sender/control/receiver loops and their stopping behavior are unchanged. Full tokenizer-supported vocabulary, one PyTorch thread, the 900-token context setting, and the original generation cap remain explicit. The separate fixed-endpoint sampler is correctly described as a harness routine using upstream primitives, not an unchanged upstream stopping encoder.

The inspected Qwen pilot manifest names the new follow-up plan, agrees with the declared model-file hashes, records 151,936 model output slots and 151,665 tokenizer/effective entries, and contains exactly four excluded cases from two pilot prompts disjoint from the main 20 prompts. Its model pin matches revision `060db6499f32faf8b98477b0a26969ef7d8b9987` and the specified weight digest. This validates the frozen metadata and launch configuration; actual Qwen API compatibility and numerical behavior still require the planned pilot execution.

All inspected manifest source hashes match the reviewed files, and all frozen input hashes checked successfully. The same prompt population and prescribed experimental secrets are reused across models, as declared; the implementation supplies no basis for treating the second model as a larger independent prompt sample.

## Checks performed and conclusion

I reran `audit_observable_followup.py` into a temporary directory with network access disabled. All 12 checks passed, and its summary exactly matched the retained synthetic-audit JSON. Additional checks covered public-input manifest construction, original-cohort binding completeness, failed-verified budget fallback, 720 independent AUC oracle comparisons, unsupported but emitted strings, incomplete-analysis rejection, upstream byte hashes, and pilot/main prompt separation.

No scientific blocker was found that requires changing the frozen score, selection rule, or budget design before execution. The review does not establish any model result. Reporting must still keep every planned outcome, distinguish no-output attempts from emitted strings, preserve numerical discrepancies, and use the declared conditional scopes. The previous scientific review and its recommendation remain unchanged.

## Reviewed identifiers

| File | SHA-256 |
|---|---|
| `observable_upstream_score.py` | `6b49c23e9903c28d2792fba5ef242cbe4b5e32a8abbfbcf6addcc574f4e98573` |
| `replay_upstream_observable.py` | `22cd89a04953df3bec2170ce5488c8d49081ff703d3e2e671525a2014905e9ff` |
| `analyze_upstream_observable.py` | `d2d7211eab3cfd8d8634cc66370d66fc010c9472e81bf656198acc88e4593d6b` |
| `run_upstream_budget_curve.py` | `c89e555ec7bc30369324df6c7c0377bb0b96fc46a94d3728e99d8182dbdb9619` |
| `analyze_upstream_budget.py` | `872fab86666a811e11dd5f31c329ee5ccf5fe0af0344be34ada206cb8462dfc2` |
| `audit_observable_followup.py` | `8a2c51e5f037a7e00e0ee22c0a86f1ec0c00b5980ca07603c469a53e536279da` |
| `run_upstream_rrc.py` | `baa9d4574e429526d7837a2833b99ba3f682b1b6def49f1ffd540ffef6da1cbd` |
| `notes/sp2027-observable-followup-plan.md` | `776778d862924f1b12bf77bac16fb1f2a31d6868fc7c7da62ba7facf4ece71f2` |
