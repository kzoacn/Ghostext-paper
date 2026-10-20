# Reproducing the S&P 2027 revision

The artifact separates exact coding checks, saved-data analysis, model replay,
and fresh generation. The original raw records remain in the working
repository. The anonymous export removes host names, personal paths, and
repository commit identifiers from metadata; it does not change cover texts,
token IDs, probabilities, outcomes, or measurements. Its file index records
both original and exported hashes.

Use Python 3.12. The commands below run from `Ghostext-paper/`, alongside
`../Ghostext/`. A virtual environment is recommended.

```bash
python -m pip install -r requirements-analysis.txt
python -m pip install --no-deps -e ../Ghostext
```

The observed complete research environment is pinned in
`requirements-revision.txt`. The supplementary snapshot in
`results/sp2027-environment/python-packages.json` distinguishes package fields
recorded by the original manifests from fields captured later in the same
session. Several older delivery manifests did not record every package.
The experiments used CPU inference; no cross-hardware bitwise claim is made.

## Checks without model weights

```bash
PYTHONPATH=../Ghostext/src python -m pytest ../Ghostext/tests -q
python scripts/run_codec_security_audit.py
python scripts/audit_stopping_adapter.py
python scripts/audit_rotation_grid.py
python scripts/audit_termination_theory.py
python scripts/certify_verified_stopping.py
python scripts/audit_observable_followup.py
python scripts/run_stopping_dp.py
python scripts/audit_existing_evidence.py
python scripts/audit_legacy_controls.py
python scripts/analyze_stopping_llm.py \
  results/sp2027-stopping-gpt2 results/sp2027-stopping-qwen \
  results/sp2027-stopping-gpt2-expanded results/sp2027-stopping-qwen-expanded
python scripts/analyze_repair_matrix.py \
  results/sp2027-repair-gpt2 results/sp2027-repair-qwen
python scripts/analyze_stopping_ablation.py \
  results/sp2027-stopping-gpt2 results/sp2027-stopping-gpt2-verified
python scripts/analyze_upstream_rrc.py \
  results/sp2027-upstream-gpt2 \
  results/sp2027-upstream-gpt2-pilot results/sp2027-upstream-gpt2-pilot-v2 \
  results/sp2027-upstream-qwen25-pilot results/sp2027-upstream-qwen25
python scripts/analyze_upstream_tokens.py
python scripts/analyze_upstream_tokens.py --cohort results/sp2027-upstream-qwen25
python scripts/analyze_upstream_observable.py \
  results/sp2027-observable-gpt2 results/sp2027-observable-qwen25
python scripts/analyze_upstream_budget.py \
  results/sp2027-budget-gpt2 results/sp2027-budget-qwen25
python scripts/audit_observable_fidelity.py \
  --cohort results/sp2027-upstream-gpt2 --replay results/sp2027-observable-gpt2 \
  --out results/sp2027-observable-fidelity/gpt2.json
python scripts/audit_observable_fidelity.py \
  --cohort results/sp2027-upstream-qwen25 --replay results/sp2027-observable-qwen25 \
  --out results/sp2027-observable-fidelity/qwen25.json
python scripts/analyze_public_endpoint.py \
  results/sp2027-endpoint-gpt2 results/sp2027-endpoint-gpt2-corrected \
  results/sp2027-endpoint-qwen
python scripts/generate_evaluation_tables.py --require-all
python scripts/generate_revision_figures.py
python scripts/generate_accept_materials.py
python scripts/generate_followup_materials.py
```

The model integration test is skipped unless explicitly configured. It is
separate from the retained real-model cohorts. Exact-tree and finite-tape
checks assert their claimed rational values. Saved-data analyses reject
incomplete or duplicated cohorts and verify recorded text/probability
consistency before reporting statistics.

The original NLS function audit additionally needs PyTorch and internet access
to fetch two source files from the pinned 2019 revision. It executes selected
original function definitions unchanged; the synthetic model and injective
renderer belong to the audit harness.

```bash
python -m pip install -r requirements-revision.txt
python scripts/run_external_counterexamples.py
python scripts/run_stopping_simulation.py
```

The expected exact results include NLS complete-text TV `15/16` with reported
KL zero, ideal RRC matched-length TV `33/256`, and finite-grid/capped TV `1/96`
in the supplied regression example. The uniform-source stopping negative
control has zero distance. These are distinct experiments and reference laws.

`audit_termination_theory.py` additionally checks the verified-rule safe interval,
reverse-error cancellation, a dependent Markov source's constants, and exact
public endpoint identities. Its six prefix-tree identity checks use a public
cap of eight tokens and include unresolved cap outcomes. They must not be
read as laws conditioned on successful payload resolution. Numerical kernel
quadrature supplements, rather than replaces, the analytic proof.

`certify_verified_stopping.py` uses exact rational killed-kernel integrals and
integer lower-mass dynamic programming for the specified two-state Markov
source. Its missing mass remains an explicit error budget. Integer-power
tests define closed information bands; a squared-transition moment covers
every length beyond the finite scan. A separate run-composition formula
computes the candidate maximum exactly and certifies it against the other
lengths' upper bounds. The JSON stores exact fractions and downward-rounded
decimal lower bounds, including the vacuous 128-bit result. This is a
certificate for continuous, exact-real, uncapped reverse verification, not
for finite rotations, Decimal software, an LLM, or its rendered strings.

`audit_observable_followup.py` checks the all-text score's defined failure
states and infinity ties, retains unmatched emitted strings in its separate
class-wise analysis, and injects later failure/interruption into the budget
stream. Earlier reached endpoints must remain complete and byte-preserved.
The all-text analyses themselves consume every planned output binding;
deduplicating an identical public input does not remove its repeated binding.

The historical 18-control pilot used filtered floating probabilities and
three raw-argmax fallbacks. The old JSON label `historical_stable_sampler`
remains an identifier, not a claim that these are strict quantized-Q samples.
Historical merged batches also reuse six `(case_id, run_index)` keys.
`audit_legacy_controls.py` pairs by original row order and checks identifiers
and visible lengths; joining only on those reused keys is incorrect.

## Exact models

```bash
python scripts/fetch_revision_models.py
```

Weights are downloaded to `../models/` and are not included in the archive.
The Qwen experiment uses
`bartowski/Qwen_Qwen3.5-2B-GGUF` at revision
`6521bcb22761828aa55639d1c814a207234c3e70`, filename
`Qwen_Qwen3.5-2B-Q4_K_S.gguf`. Its SHA-256 starts `ae7c7f78251e36c8`.
The upstream main branch later replaced this file; using the same filename
from the latest revision does not reproduce the experiment.

GPT-2 uses `openai-community/gpt2` at revision
`607a30d783dfa663caf39e06633721c8d4cfcd7e`.
`results/sp2027-environment/model-downloads.json` gives complete hashes,
including tokenizer files. Existing models can be checked without downloading:

```bash
python scripts/fetch_revision_models.py --verify-only \
  --qwen-path ../models/qwen/Qwen_Qwen3.5-2B-Q4_K_S.gguf \
  --gpt2-path ../models/gpt2
```

The additional unchanged-upstream replication uses the official base model
`Qwen/Qwen2.5-0.5B`, revision
`060db6499f32faf8b98477b0a26969ef7d8b9987`. It is distinct from the Qwen3.5-2B
GGUF source above. Its 988,097,824-byte weight file has SHA-256
`88c142557820ccad55bb59756bfcfcf891de9cc6202816bd346445188a0ed342`.
The tokenizer has 151,665 supported entries, used by the upstream source out
of 151,936 model output slots. CPU inference explicitly loads float32 weights
and uses one PyTorch thread per worker.

```bash
python scripts/fetch_qwen25_model.py
python scripts/fetch_qwen25_model.py --verify-only
```

The fetcher verifies the pinned weight digest and official Git object IDs
for tokenizer/configuration files. All local SHA-256 values are recorded in
`results/sp2027-environment/qwen25-download.json`.

## Frozen source profiles and generation

Source changed between cohorts. Running an old resume command against the
current source is expected to fail its hash check. The source-object store
preserves exact bytes, indexed by SHA-256, and
`results/sp2027-source-map/protocols.json` maps every profile to its entry point,
arguments, candidate policy, stopping horizon, and recorded CPU affinity.
Materialization also stages hash-checked input records for the archived
bootstrap probe, targeted reverse-failure diagnostic, and new text replays.
It preserves source objects needed for the replays' own frozen-code imports.
Each upstream profile stages its exact archived study plan at the path its
runner expects; this keeps the two excluded pilot versions distinct.
Command-index paths
are relative to the root of the materialized profile; use absolute model and
output paths when running those commands.
Helpers omitted from old manifests are separately pinned at artifact freeze,
with their status distinguished from originally recorded hashes.
`results/sp2027-validation/helper-compatibility.json` checks whole unchanged
modules or the unchanged imported function ASTs against the earlier research
milestone.

| Profile | Planned pairs or trials | Candidate policy | Stop/generation policy |
|---|---:|---|---|
| `sp2027-stopping-gpt2` | 160 pairs | Strict | Published midpoint rule, cap `2B` |
| `sp2027-stopping-qwen` | 320 pairs | Strict | Published midpoint rule, cap `2B` |
| `sp2027-stopping-gpt2-expanded` | 160 pairs | Bounded expansion after empty set | Same rule and cap, new seed |
| `sp2027-stopping-qwen-expanded` | 320 pairs | Bounded expansion after empty set | Same rule and cap, new seed |
| `sp2027-repair-gpt2` | 40 trials | Strict | Authenticated packet, guards 0/128, ten attempts |
| `sp2027-repair-qwen` | 80 trials | Strict | Authenticated packet, guards 0/128, ten attempts |
| `sp2027-stopping-gpt2-verified` | 40 pairs | Strict | Separate verification-before-stop adapter |
| `sp2027-upstream-gpt2` | 160 secret instances | Upstream full vocabulary | Unchanged verified/unverified sender and receiver, plus independent-endpoint control |
| `sp2027-upstream-gpt2-pilot` | 4 excluded instances | Same source | Original control reserve; one precision failure retained |
| `sp2027-upstream-gpt2-pilot-v2` | 4 excluded instances | Same source | Corrected control reserve, frozen before the main cohort |
| `sp2027-endpoint-gpt2-corrected` | 13 existing pairs | Original frozen delivery source | Text-only two-segment endpoint replay, original two threads |
| `sp2027-endpoint-qwen` | 37 existing pairs | Original frozen delivery source | Same replay and previous interruption exclusion |
| `sp2027-endpoint-gpt2` | 13 existing pairs | Mismatched runtime | Retained one-thread diagnostic; not a same-source result |
| `sp2027-upstream-public-features` | 6 existing arm/control pairs | Upstream full vocabulary | Public score replay; nine distinct text inputs |
| `sp2027-upstream-qwen25-pilot` | 4 excluded instances | New Qwen2.5 upstream source | API/numerical pilot; all raw and receiver outcomes retained |
| `sp2027-upstream-qwen25` | 160 secret instances | New Qwen2.5 upstream source | Same prompts/tapes and three arms as the GPT-2 study |
| `sp2027-observable-gpt2` | 160 instances across three arms | Original upstream source | Public score on every published string; no canonical/recovery selection |
| `sp2027-observable-qwen25` | 160 instances across three arms | New Qwen2.5 upstream source | Same frozen public score and every-output accounting |
| `sp2027-budget-gpt2` | 160 trajectories, four budgets each | Original upstream source | Independent endpoints N, ceiling(1.25N), ceiling(1.5N), 2N |
| `sp2027-budget-qwen25` | 160 trajectories, four budgets each | New Qwen2.5 upstream source | Same endpoint assignment and failure-preserving prefix persistence |

The expanded-source study was introduced after diagnosing development-case
filter failures. It uses seed `20261023`, retains the original topic split and
fixed detector score, and is analyzed separately from the strict source.
The verified 40-case GPT-2 cohort vetoed no stops; it is an unchanged-path check.
The separate `sp2027-reverse-failure-gpt2` diagnostic selects all three completed
reverse failures from the original 160-pair cohort and checks independent text
decoding before and after verification. It is not a randomly sampled repair
benchmark or an assessment of current upstream RRC software.

For example, reconstruct the original strict GPT-2 sources:

```bash
python scripts/materialize_profile.py sp2027-stopping-gpt2 \
  --destination tmp/profiles/gpt2-strict
python tmp/profiles/gpt2-strict/Ghostext-paper/scripts/run_stopping_llm.py \
  --backend gpt2 --model-path ../models/gpt2 \
  --out-dir local-results/stopping-gpt2 --threads 2 --repeats 8 \
  --bits 128 512 --seed 20261020
```

Use a new output directory for regeneration. If resuming, source hashes,
weights, task membership, and parameters must match the original manifest.
Recorded affinities document the original host and are not portable CPU
identifiers. Runtime comparisons are limited: jobs ran concurrently, and
delivery replay includes additional candidate auditing.

Stopping experiments use deterministic public experimental random tapes.
Authenticated delivery uses OS randomness for fresh packets and guards.
Delivery is therefore statistically rerunnable; a task-order seed does not
reproduce identical cover texts. The saved texts support independent replay.

The Qwen delivery process terminated after 64 saved trials. Its original
source profile and configuration were restored to resume the remaining tasks.
`results/sp2027-repair-qwen/interruption.json` records the saved-prefix hash
and the next task. The first 64 rows are checked byte for byte. The interrupted
in-flight trial, `01_zh_corner_cafe:r0:g128`, had not been persisted and resumes
with a fresh attempt budget and OS randomness. Its original ten-attempt and
first-attempt outcomes are unknown. Primary summaries exclude it, leaving 79
uninterrupted trials; the resumed record and conservative one-case bounds for
the original plan are reported separately. Unknown interrupted work is excluded
from attempt counts and timing.

## Independent public-feature replay

```bash
python scripts/replay_public_features.py results/sp2027-stopping-gpt2 \
  --study stopping --model-path ../models/gpt2 \
  --out local-results/replay-stopping-gpt2.json
python scripts/replay_public_features.py results/sp2027-repair-qwen \
  --study repair --model-path ../models/qwen/Qwen_Qwen3.5-2B-Q4_K_S.gguf \
  --out local-results/replay-repair-qwen.json
```

The replay selects the first eligible held-out case in each relevant group
and consumes text and public configuration only. It compares every selected
quantized probability or bootstrap-probe outcome with the saved record.
Additional retained replays cover both models and candidate settings.

The current-upstream study uses RRC commit
`dae326259e4fca8bc4fcf460dafdbc0e88a0a71a`; its unchanged core SHA-256 is
`e45a4df5eebc86881d606f2fd6c3cbab5729252dce96e5ae1a7ba424be02ec4a`.
External files are fetched by immutable revision and checked before execution:

```bash
python scripts/fetch_upstream_rrc.py
python scripts/audit_upstream_rrc.py
python scripts/replay_upstream_public_features.py \
  --model-path ../models/gpt2 --out-dir local-results/upstream-public-replay
python scripts/run_public_endpoint_replay.py \
  --backend gpt2 --model-path ../models/gpt2 --threads 2 \
  --out-dir local-results/endpoint-gpt2
```

For generation, materialize `sp2027-upstream-gpt2` and use its command index.
It has 20 prompt clusters, ten development and ten test, four tapes and two
payload sizes. The fixed-endpoint arm's extra Decimal reserve was fixed
after an excluded pilot failure, before the main cohort. It retains receiver
failures. All raw variants, stage files and execution journals are included.
Upstream worker interruptions are recorded separately, with hashes of completed
stages and cases. Resuming reuses the frozen tasks and random tapes, preserves
those completed records, and repeats only unfinished stages. It does not
allocate a fresh secret or sample. The verifier checks the preserved-file hashes;
unpersisted interrupted work is not included in runtime totals.
The exact model-probability source is defined by differences of upstream
Decimal-converted CDF boundaries, not by separately reported softmax values.

The observable follow-up is fixed in
`notes/sp2027-observable-followup-plan.md`. GPT-2's all-text replay is
retrospective; Qwen2.5 is a separate prospective model replication. They
reuse the same 20 prompts and experimental tapes, so the second model does
not double the number of independent prompt clusters.

```bash
python scripts/replay_upstream_observable.py \
  --cohort results/sp2027-upstream-gpt2 --model-path ../models/gpt2 \
  --out-dir local-results/observable-gpt2
python scripts/run_upstream_budget_curve.py \
  --cohort results/sp2027-upstream-gpt2 --model-path ../models/gpt2 \
  --out-dir local-results/budget-gpt2
python scripts/audit_observable_fidelity.py \
  --cohort results/sp2027-upstream-gpt2 --replay results/sp2027-observable-gpt2 \
  --out local-results/observable-fidelity-gpt2.json
```

The Qwen2.5 equivalents use `sp2027-upstream-qwen25` and
`../models/qwen25-0.5b`. For bit-exact generation/replay provenance, use the
corresponding materialized source profile and its command index.

The public score retokenizes the full published string, removes the public
prompt's token prefix when present, and replays that continuation. Its
negative log probability is not a sum over alternative tokenizations of the
same string. Public prefix mismatch, empty continuation, unsupported token,
and zero source mass receive negative infinity. Infrastructure exceptions
remain unfinished work rather than successful classifications.
No generation/recovery label enters scoring. A failed generation is represented
by no output, not its private failed prefix. If such failures occur, the
augmented all-attempt experiment, emitted-pair sensitivity, and class-wise
all-emitted-string summaries have separate denominators. Passive observers
are not assumed to see unsent attempts. The length baselines use full-string
token and Unicode code-point counts; raw token-length pairing need not survive
serialization as an equal observable-length histogram.

Budget runs use each verified endpoint only to assign the separate stream's
budgets. The extra stream and each distinct ID/text receiver input use the
unchanged upstream primitives. Identical ID/text inputs reuse their checked
receiver result. Reached prefixes are saved before continuing, so a later
failure cannot invalidate an earlier completed endpoint. The N-token comparison
with the original fixed-endpoint stream is a post-generation diagnostic.
It cannot select trajectories. Larger-budget measurements concern recovery
and prescribed-token cost, without a detector-resistance claim.
Budget records retain sender CDF traces and receiver outcomes. Those traces
support an offline inverse check for the original token path; the observable
replay supplies additional retokenized traces at N. Larger-budget noncanonical
text receivers retain their execution summaries but require model inference
to reconstruct their different CDF paths.

Endpoint replay is post-hoc and knows the 16-byte application-message length,
giving two public segment sizes of 60 and 44 bytes. Classification only uses
visible text and public inputs. Integer-only reanalysis independently
recomputes all decisions from selected CDF boundaries. After classification,
reconstructed packet hashes and inspected natural selected masses are compared
with the archive to check fidelity; they do not filter the cohort.

The first GPT-2 replay used one thread instead of the original two. Token IDs
still matched, but some integer frequencies changed and reconstructed packets
did not match. This complete run remains under `sp2027-endpoint-gpt2` as a
runtime-mismatch diagnostic. The corrected run repeats the same 13 pairs with
two threads. Reproduction therefore requires the recorded numerical runtime,
not merely matching weight and tokenizer hashes. The source profile preserves
the original diagnostic runner; the current runner rejects a thread mismatch.

## Building the paper

```bash
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The unmodified IEEEtran 1.8b class and bibliography style are included with
their original notices. The manuscript uses `conference,compsoc`, US Letter,
and an empty author block. The review PDF and artifact checks accompany the
export. A final submission still requires the human authors' content review
and completion of the venue's ethics and AI-use fields.
