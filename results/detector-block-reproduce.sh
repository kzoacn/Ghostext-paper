#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

python3 "$ROOT/scripts/run_detector_block.py" \
  --baseline-summary "$ROOT/results/real-backend-baseline-summary-merged.json" \
  --baseline-runs "$ROOT/results/real-backend-baseline-runs-merged.jsonl" \
  --out-dir "$ROOT/results/detector-block" \
  --llm-judge-model "gpt-5.4"
