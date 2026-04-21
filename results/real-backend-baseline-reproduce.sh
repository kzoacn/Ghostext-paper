#!/usr/bin/env bash
set -euo pipefail

ROOT="/mnt/d/work/Ghostext-paper"

python3 "$ROOT/scripts/run_real_backend_baseline.py" \
  --repeats 1 \
  --threads 4 \
  --out-dir "$ROOT/results/real-backend-baseline-r1"

python3 "$ROOT/scripts/run_real_backend_baseline.py" \
  --repeats 2 \
  --threads 4 \
  --out-dir "$ROOT/results/real-backend-baseline-r2"

python3 "$ROOT/scripts/merge_real_backend_baseline.py" \
  --input-dir "$ROOT/results/real-backend-baseline-r1" \
  --input-dir "$ROOT/results/real-backend-baseline-r2" \
  --output-json "$ROOT/results/real-backend-baseline-summary-merged.json" \
  --output-md "$ROOT/results/real-backend-baseline-summary-merged.md"
