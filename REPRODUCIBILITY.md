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
python scripts/generate_evaluation_tables.py --require-all
python scripts/generate_revision_figures.py
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

## Frozen source profiles and generation

Source changed between cohorts. Running an old resume command against the
current source is expected to fail its hash check. The source-object store
preserves exact bytes, indexed by SHA-256, and
`results/sp2027-source-map/protocols.json` maps every profile to its entry point,
arguments, candidate policy, stopping horizon, and recorded CPU affinity.

| Profile | Planned pairs or trials | Candidate policy | Stop/generation policy |
|---|---:|---|---|
| `sp2027-stopping-gpt2` | 160 pairs | Strict | Published midpoint rule, cap `2B` |
| `sp2027-stopping-qwen` | 320 pairs | Strict | Published midpoint rule, cap `2B` |
| `sp2027-stopping-gpt2-expanded` | 160 pairs | Bounded expansion after empty set | Same rule and cap, new seed |
| `sp2027-stopping-qwen-expanded` | 320 pairs | Bounded expansion after empty set | Same rule and cap, new seed |
| `sp2027-repair-gpt2` | 40 trials | Strict | Authenticated packet, guards 0/128, ten attempts |
| `sp2027-repair-qwen` | 80 trials | Strict | Authenticated packet, guards 0/128, ten attempts |
| `sp2027-stopping-gpt2-verified` | 40 pairs | Strict | Separate verification-before-stop adapter |

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
