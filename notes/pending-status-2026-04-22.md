# Pending Status (2026-04-22)

This note records the current checkpoint so work can resume without context loss.

## Completed in this checkpoint

- Updated paper evidence alignment for released artifacts:
  - `paper/sections/07-analysis-and-discussion.tex`
  - `paper/sections/08-evaluation-plan.tex`
  - `paper/sections/13-limitations-and-conclusion.tex`
- Updated baseline/provenance wording to match released merged summary fields:
  - llama.cpp build commit is now explicitly treated as released
  - GGUF upstream provenance is now explicitly treated as released
  - per-run full cover-text release is now explicitly treated as released
- Added/updated detector script support for LLM-as-a-judge:
  - `scripts/run_detector_block.py`
  - `results/detector-block-reproduce.sh`
  - new CLI path: `--llm-judge-model`, default `gpt-5.4`
  - new outputs (when run completes): `llm_judge_pairs.jsonl`, `llm_judge_scores.jsonl`

## Released artifacts already available

- Merged real-backend baseline:
  - `results/real-backend-baseline-summary-merged.json`
  - `results/real-backend-baseline-summary-merged.md`
  - `results/real-backend-baseline-runs-merged.jsonl`
  - `results/real-backend-baseline-step-audit-merged.jsonl`
- h_min sweep (pilot):
  - `results/hmin-sweep/hmin_sweep_summary.json`
  - `results/hmin-sweep/hmin_sweep_summary.md`
  - condition subdirs: `hmin-0.5/`, `hmin-1.0/`

## Still pending

- Detector block final artifact is not finished:
  - `results/detector-block/` is currently empty.
  - Previous run was interrupted.
- LLM judge requires `OPENAI_API_KEY` in environment to run the judge path.
- Aligned baseline scripts were refactored earlier; rerun is still recommended to refresh outputs under the updated provenance/reporting format.
- Paper compile/check was not rerun in this checkpoint.

## Resume commands

Run detector block without LLM judge (local smoke / baseline):

```bash
python3 scripts/run_detector_block.py \
  --baseline-summary results/real-backend-baseline-summary-merged.json \
  --baseline-runs results/real-backend-baseline-runs-merged.jsonl \
  --out-dir results/detector-block \
  --disable-llm-judge
```

Run detector block with LLM judge (default model `gpt-5.4`):

```bash
export OPENAI_API_KEY="<your_key>"
python3 scripts/run_detector_block.py \
  --baseline-summary results/real-backend-baseline-summary-merged.json \
  --baseline-runs results/real-backend-baseline-runs-merged.jsonl \
  --out-dir results/detector-block \
  --llm-judge-model gpt-5.4
```

Refresh aligned-baseline artifacts:

```bash
python3 scripts/run_aligned_baselines.py --out-dir results/aligned-qwen-baselines
python3 scripts/merge_aligned_baselines.py \
  --input-json results/aligned-qwen-baselines/aligned_baseline_summary.json \
  --output-md results/aligned-qwen-baselines/aligned_baseline_summary.md
```

Compile paper:

```bash
cd paper
latexmk -pdf main.tex
```
