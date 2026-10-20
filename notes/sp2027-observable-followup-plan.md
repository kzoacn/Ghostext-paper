# Prospective observable-text and second-model follow-up

This plan is fixed on 2026-10-21 after the independent review of PDF
`500f2431f56a735bd58ff600b70591da0c29686ad54aa1a15aa28c77b597c2f2`.
That review recommends Weak Accept. It finds no confirmed correctness blocker
but identifies canonical-pair selection, empirical breadth, and restricted
ideal assumptions as material limits. The review and its assessed release
remain unchanged. These follow-ups address those limits; they are not an
automatic rule for a different recommendation.

## 1. A score defined on every observable output

The existing GPT-2 study has already been inspected, including its original
canonical-pair and raw-token summaries. Its new observable-text analysis is
therefore a retrospective robustness check. The rule below is frozen before
any new model replay. It does not select among detectors by test performance.

The observer receives the upstream published string, public prompt, model,
and payload length B. It independently tokenizes the entire string using
`add_special_tokens=False`. If those tokens begin with the public prompt's
tokenization, the remaining tokens are scored by a fresh upstream incremental
model stepper initialized on the public prompt. The score is
`-abs(I_visible - B)`, where `I_visible` is the cumulative negative base-two
log of the selected Decimal CDF masses on that retokenized continuation.
This is a deterministic public score on the rendered string; it is not
claimed to be the exact probability of that string after summing all
tokenization preimages.

The calculation does not receive original token IDs, sender intervals,
canonicality, receiver success, the secret, a rotation tape, or a class label.
All complete generated strings and their natural controls enter. No output
is excluded for changed tokenization or failed recovery. The same public
input may reuse a previously computed result within that replay.
The selected CDF trace is retained for independent saved-data reanalysis.
Original IDs and CDFs may be compared only after scoring, as diagnostics.

The rule has explicit behavior outside the ordinary case. A prompt-prefix
mismatch, a token with zero source mass, or an empty continuation receives
score negative infinity. Their individual statuses remain visible in the
results. An implementation/infrastructure exception is recorded as an
execution failure and must be resolved or separately bounded; it must not
silently remove a row or be treated as a successful public decision.

If generation itself fails, upstream does not return a complete text.
Such an attempt has a distinguished no-output observation with score
negative infinity, not its harness-recovered private failed prefix.
All-attempt results retain this observation and explicitly identify that
augmented experiment. Results restricted to emitted strings are additionally
reported when needed and labelled with the corresponding denominators.
A passive text observer is not assumed to know that an unsent attempt occurred.
The main all-text claim requires that every planned generation completes;
otherwise its scope must state this distinction.

The original ten development and ten test prompt clusters remain unchanged.
The threshold is the higher empirical 95th percentile of development natural
scores, with strict-greater decisions. AUC, threshold TPR/FPR, per-prompt
results, and 5,000 prompt-cluster bootstrap intervals are reported separately
for each model, payload size, and arm. The bootstrap seed is 20261028.
The positive and negative class each contain all planned instances in this
analysis, including recovery failures.

The matched raw-token endpoints do not imply matched visible lengths after
lossy serialization. Consequently we additionally report AUC using the
retokenized token count of the full published string and its Unicode
code-point count as scores, with higher always meaning positive. Both counts
are zero for the no-output observation and remain defined on prompt-prefix
mismatches. Their orientation is not chosen using test labels. The fixed-endpoint arm
undergoes the identical serialization and scoring. We will not describe this
all-text result as having an exactly matched observable-length histogram
unless that equality is actually established.

## 2. A separate unchanged-upstream model replication

The second model is the public base model `Qwen/Qwen2.5-0.5B`, at immutable
revision `060db6499f32faf8b98477b0a26969ef7d8b9987`.
The weight SHA-256 is
`88c142557820ccad55bb59756bfcfcf891de9cc6202816bd346445188a0ed342`.
Every tokenizer/configuration file will also be hashed before generation.
This is a new Hugging Face model realization, distinct from the earlier
Qwen3.5-2B GGUF processed-source experiment.

The sender, receiver, and incremental model stepper remain the unchanged
functions from RRC revision
`dae326259e4fca8bc4fcf460dafdbc0e88a0a71a`.
We use the full tokenizer-supported vocabulary, the same 900-token context
window, the same `2*B` generation cap, upstream float64 CDF construction, and
`Decimal(random.Random.random())` rotations. Model weights are loaded in
float32 on CPU with one PyTorch thread per worker. There is no chat template,
top-p filter, EOS mask, or Ghostext candidate filter.

The 20 prompts, development/test assignment, B in {128, 512}, four repeats,
master seed 20261025, and 160 secret instances are exactly those in the first
upstream study. Corresponding cases reuse the prescribed experimental
secrets/tapes across models, so the two model studies are not presented as
independent prompt populations or pooled to enlarge the cluster count.
The verified/unverified pair shares its secret and tape; the independent
endpoint arm has its own secret/tape and receives the verified arm's length.
The source, serialization, controls, receiver checks, failures, and persistence
rules remain those of the original upstream plan.

The two already reserved pilot prompts supply four excluded harness cases.
They can diagnose API compatibility, determinism, serialization, and precision.
Their results will be retained and cannot change the main score, prompt set,
payload sizes, or sample count. Any necessary numerical implementation change
must be documented before confirmatory generation. No new pilot or main
sample is selected based on discrimination performance.

The all-observable-text rule in Section 1 is the new primary analysis for
this model. The earlier canonical-pair and raw-token scripts are also applied
as explicitly labelled sensitivity analyses. This replication cannot extend
the Markov theorem to general LLMs or establish low-FPR deployment behavior.

## 3. Independent endpoint budgets and recovery

For each model and all 160 original secret instances, define N to be the
verified arm's recorded endpoint. The separate fixed-endpoint stream already
has an independent secret and rotation tape. A new run continues that same
prescribed stream to 2N and assesses recovery at
`N`, `ceil(1.25*N)`, `ceil(1.5*N)`, and `2*N`.
If verified generation fails, use its predefined `2*B` cap for N and retain
that status. These are budgets drawn independently of the fixed-endpoint
stream's content; no prefix is selected because it already recovers.

The control uses the existing fixed-endpoint primitive and the same
conservative Decimal reserve, evaluated at the maximum prescribed endpoint.
Every prefix receives an independent unchanged upstream receiver replay
on both its original token IDs and its rendered text. The N-token prefix
is compared with the previous fixed-endpoint record after generation.
Any discrepancy is retained and reported; it cannot be used to select
successful trajectories. The new stream's results remain the primary
budget-curve measurements even if a numerical discrepancy is found.
Each prescribed endpoint is finalized and persisted before generation
continues. A failure after a reached endpoint leaves that completed prefix
eligible for its own receiver check; only unreached endpoints are generation
failures. The old natural-prefix helper is not used for this curve, because
it propagates a later full-stream failure to earlier prefixes and expects
natural-sampler metadata. This rule was clarified by the independent design
review before any follow-up generation.

Report ID recovery, visible-text recovery, canonicality, generation failure,
token budget, and bits per prescribed token, by model and B. Recovery
fractions retain every planned instance. Prompt-cluster intervals describe
these finite cohorts. This curve is a delivery/rate diagnostic; no natural
control is needed for a claim only about recovery, and no detector-resistance
claim is made for its larger budgets. Earlier fixed-endpoint comparisons
provide the separate source-law diagnostic.

## 4. Reporting and stopping rules

There is no outcome-dependent sample extension, test-threshold search,
successful-recovery selection, or model replacement after results are seen.
The entire planned second cohort and both full budget curves are retained,
including negative results. Unexpected failures are diagnosed with recorded
inputs and source hashes before any correction is undertaken.

The presentation will foreground the stopped-transcript contribution,
provide a compact mechanism/reference/assumption map, and compress older
prototype history. Scope remains explicit for continuous theorems, finite
software, canonical-token analyses, all-observable-text analyses, and
delivery-conditioned endpoint probes. The final assessment must again be
independent and tied to exact manuscript and anonymous-archive hashes.
