#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

python3 "$ROOT/scripts/run_hmin_sweep.py" \
  --baseline-summary "$ROOT/results/real-backend-baseline-summary-merged.json" \
  --out-dir "$ROOT/results/hmin-sweep"
