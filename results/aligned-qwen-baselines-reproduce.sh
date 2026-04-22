#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

python3 "$ROOT/scripts/run_aligned_baselines.py" \
  --out-dir "$ROOT/results/aligned-qwen-baselines"

python3 "$ROOT/scripts/merge_aligned_baselines.py" \
  --input-json "$ROOT/results/aligned-qwen-baselines/aligned_baseline_summary.json" \
  --output-md "$ROOT/results/aligned-qwen-baselines/aligned_baseline_summary.md"
