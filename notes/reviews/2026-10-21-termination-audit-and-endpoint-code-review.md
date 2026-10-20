# Independent correctness review of termination audits and endpoint replay

Review date: 2026-10-21, Asia/Shanghai. Final data snapshot for this note: 2026-10-20 18:56:20 UTC. This is a focused correctness review, not an acceptance recommendation or a review of the newly integrated manuscript.

I found no blocking arithmetic or classifier error in the inspected code. The theory summary reproduces, the classifier respects the declared public-input boundary, and the two-thread GPT-2 correction is supported by independent replay evidence. The corrected GPT-2 cohort is complete at this snapshot. The Qwen cohort is still incomplete, so its full-cohort endpoint rates and final replay-fidelity conclusion remain unverified.

I made no manuscript or implementation edits and ran no model jobs. I reran lightweight arithmetic functions in memory, tested three in-memory mutations, exercised the classifier with a synthetic two-token backend, and independently recomputed every currently saved endpoint trace using integer arithmetic without importing the Ghostext decoder.

## Theory audit and saved summary

The source hash in `results/sp2027-termination-theory/summary.json` matches `scripts/audit_termination_theory.py`. Rerunning all five audit functions reproduced the saved summary exactly after JSON normalization. They completed in approximately 3.85 seconds in this review.

The safe-interval audit is useful rather than circular. It constructs a forward rotation history, computes the proposed safe width, and separately reverse-replays nonzero interior displacements through the full history. The checked equality is not merely the definition of the safe width. The audit covers 19,200 interior points, 1,379 sufficient stopping events that recover, and 3,421 failed-safe-event normalized-width checks. Its stored right-endpoint witness demonstrates the half-open boundary issue explicitly.

The reverse-error audit also compares distinct computations: one uses absolute interval locations and rotation offsets, while the other uses the normalized error recurrence. It then compares stopping decisions across different branch paths at a fixed normalized-point tape. All 98,304 reverse-error identities and 24,576 complete-path comparisons reproduced. The three-state graph variable does not affect the numerical widths because both outgoing edges have probability one half; that is the reason for the cancellation, rather than a defect in the check. The audit is not an empirical proof that continuous uniforms are independent of the token path. That part remains an analytic premise established by the fresh-rotation factorization.

I changed three expressions only in memory and confirmed that the existing audits reject each mutation:

- Replacing `min(previous_safe, right_margin)` by `right_margin`, thereby forgetting older cuts.
- Removing the modulo from the reverse-error recurrence.
- Treating the continuous arithmetic interval's right endpoint as closed.

The kernel audit independently integrates the second killed transition after removing its square-root singularity, and compares that result with the piecewise two-step expression. It still uses the derived one-step kernel inside that integration, so it is supplementary evidence rather than an independent derivation of every kernel formula. The 60,030 numerical checks and 100 exact rational polynomial evaluations reproduce. The recorded maximum normalized ratio `1.0000000000000002` is ordinary floating-point rounding within the stated tolerance, not a failure of the analytic contraction.

The Markov parameter calculations match the asymmetric matrix, distinct row entropies, positive lag-one covariance, bridge parameters, and varentropy expression from the proof assessment. The numerical lower bound is honestly reported as zero at the small and intermediate payload sizes listed, including \(2^{20}\). No useful finite-message attack magnitude should be inferred from an asymptotic theorem whose displayed explicit bound is vacuous at those sizes.

The six public-endpoint enumerations are **capped laws with cap eight**. The exact TV calculation sums the two separately constructed transcript laws and then checks the collision expression; it does not simply assign TV from that expression. The continuous half-open containment test is correct. However, an endpoint at the public cap need not be successful payload resolution. For the dependent source with \(B=4\), unresolved mass at depth eight is `8145/32768`. Preserve the cap qualification wherever these exact TV values appear; they are not enumerations of the uncapped successfully decoded law.

## Classifier boundary and implementation

The `replay` function takes the backend, visible text, prompt, source policy, guard precision, frequency denominator, source seed, and the two public segment lengths. It retokenizes the text. It does not receive the delivery class, stored token IDs, plaintext, password, packet value, or decrypted header.

The surrounding runner uses delivery records to establish the previously declared eligibility slice and to assert the fixed 16-byte plaintext setting. This is study selection and a public chosen-length assumption, not a classifier input. The function performs saved-ID and natural-mass comparisons only after its text-derived decision.

The source processing matches the frozen `prepare_quantized_distribution` sequence: backend distribution, candidate selection, then integer quantization. The candidate stability checks and deterministic non-encoding emissions are retained. Once the first segment resolves, the runner resets the integer interval for the second segment while retaining the token context. It reports the first final resolution as either at the visible end or before it, and otherwise reports unfinished or a distinct invalidity outcome.

Synthetic checks of the actual classifier passed:

- Two one-byte segments under a uniform binary source: 15 tokens are unfinished, 16 end exactly, and 17 contain an earlier endpoint.
- Empty text remains unfinished.
- An out-of-set token is reported separately.
- A non-greedy token at a deterministic step is reported separately.
- A synthetic source exception is retained with the correct inspected-prefix length.

The plan correctly calls this a two-segment prefix-resolution support test. It does not claim to mirror rolling-entropy, stall, or token-budget abort predicates, or to authenticate replayed bytes. That narrow description is necessary and matches the implementation.

## Runtime correction and source preservation

The original GPT-2 generation manifest specifies two threads. The initial endpoint diagnostic used one. The corrected runner now rejects a mismatch before importing or loading a model; I exercised that rejection using a nonexistent model path.

The old and corrected GPT-2 manifests select exactly the same 13 cases. Both select the original 13 complete, canonical, matched guard-128 pairs. Qwen selects the original 37 eligible pairs and preserves the interrupted-case exclusion. I independently reconstructed eligibility and checked the manifest input hashes.

The initial runner hash is `36b18a9cc417fac4680828cde31564854595be89decbeabbd74621bfb2fc1c92`. Its byte-exact source snapshot exists and hashes correctly. That same source hash is retained in the Qwen manifest, whose run already used two threads. The correction changes the default and adds the thread check, correction-note input hash, and post-decision natural-mass comparison. It does not change the classifier or eligibility rule.

All selected core source objects and the model adapter hash match their generation manifest entries and retained snapshots. A future artifact freeze should retain the corrected runner and analyzer as well before further edits; at this review snapshot the corrected runner is still directly available at its recorded current-source hash.

## Independent arithmetic and packet-fidelity evidence

I recomputed integer intervals directly from each logged selected CDF pair:

\[
 [L,H)\longmapsto
 [L+\lfloor(H-L)c_{\rm low}/F\rfloor,\,
  L+\lfloor(H-L)c_{\rm high}/F\rfloor).
\]

The stopping check used equality of the two payload-block indices. This reproduced every saved status and segment endpoint without importing `MessageSegmentDecoder`.

After completing each decision, I also reconstructed resolved segment bytes from their public interval states, concatenated the 60-byte and 44-byte segments, and compared their SHA-256 hash with the original successful attempt's archived packet hash. No decryption or password was used, and this comparison did not alter classification or eligibility.

| Replay at the snapshot | Saved/planned pairs | Stego endpoint outcomes | Completed reconstructed packets matching archive | Natural selected-mass mismatches |
|---|---:|---|---:|---:|
| Initial one-thread GPT-2 diagnostic | 13/13 | 7 exact, 2 early, 4 unfinished | 0/9 | 14/2874 inspected masses |
| Corrected two-thread GPT-2 | 13/13 | 13 exact | 13/13 | 0/2876 inspected masses |
| Two-thread Qwen, incomplete | 13/37 | 13 exact | 13/13 | 0/3673 inspected masses |

The initial GPT-2 mismatches are all one frequency unit in either direction. Its natural outcomes are eight early endpoints and five unfinished outputs. The corrected GPT-2 natural outcomes are also eight early endpoints and five unfinished outputs, but its reconstructed stego packets now all match. At this partial Qwen snapshot, natural outcomes are seven early endpoints and six unfinished outputs.

The packet check is materially stronger than endpoint or token-ID agreement alone: all nine fully reconstructed packets in the wrong-thread GPT-2 diagnostic were wrong, including the seven texts that nevertheless landed exactly on an endpoint. Its measured outcomes must not be combined with the corrected cohort or treated as an attack against the original source.

Selected-mass agreement concerns the inspected prefix only. It does not directly establish that every original CDF boundary or every unobserved candidate probability was identical: the old natural records retained selected probabilities, not full CDFs. The code and model provenance, matching runtime parameter, natural selected-mass check, and complete stego packet-hash check together provide concrete replay-fidelity evidence on this cohort. They are not a universal numerical invariance theorem.

## Analysis code and remaining conditions

I also read the newly added `scripts/analyze_public_endpoint.py`. Its independent integer replay does not import the codec. Its after-decision packet hash comparison is not used to change eligibility. It requires the complete fixed case set before producing a result and exposes a separate replay-fidelity flag. Source exceptions necessarily rely on the logged error record rather than being regenerated by an arithmetic-only analyzer; the checked snapshots contain no such replay exceptions.

The family bootstrap preserves the saved family clusters and the pairing of arms. Its explicit warning about degenerate intervals for all-zero/all-one samples is appropriate. A zero empirical FPR and a zero-width bootstrap interval are not a calibrated zero upper bound on future FPR. The nominal Wilson interval also correctly carries a warning that it ignores family dependence.

There is no new correctness blocker for the scoped theory audits or endpoint classifier. Before a final full-cohort empirical claim:

1. Finish and analyze the remaining Qwen cases without changing eligibility. The 13/37 snapshot here is not a 37-pair result.
2. Retain any later replay discrepancy in the outcomes and investigate it before claiming source replay passed. Do not filter it out using the fidelity checks.
3. Keep the one-thread run explicitly diagnostic, preserve the source/version distinction, and freeze the corrected source and final analyses.
4. Maintain the mathematical scope: the endpoint support observation applies to successful no-tail outputs under the declared public segment lengths; it does not show authenticated packet uniformity or instantiate the ideal TV identity for the actual retry-conditioned packet law.

The new manuscript integration was not part of this code review and still needs its own proof and claim-to-evidence review.

## Reviewed source identifiers

| File | SHA-256 |
|---|---|
| `scripts/audit_termination_theory.py` | `b2126018da1cf13aab731a58581d1f8c96a0d46e806614fce0c2e5b7047de342` |
| `results/sp2027-termination-theory/summary.json` | `d5316be34c7836ac2f88a692503e9bff253365b2d097344777649fce4ea5fa54` |
| `scripts/run_public_endpoint_replay.py` | `6bfda41d3a6df5d04d5f26362e90f2651fdffaa806b65ce3831315b345ef5c25` |
| `scripts/analyze_public_endpoint.py` | `03739afa689ba5b82bcfda63d04576ba2278bd4ee3140da3a0b29962a2d5e635` |
| `notes/sp2027-endpoint-replay-plan.md` | `400218dd69b8c4dae7911ae96d59501a5d1b40e67eb18669a4e664f45549c375` |
| `notes/sp2027-endpoint-runtime-correction.md` | `bbd329515625998ef6bcfa229c82129caed72f52eb6ec07667b65585589b722d` |
