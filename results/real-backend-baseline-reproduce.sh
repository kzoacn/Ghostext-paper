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

python3 - <<'PY'
import json
from pathlib import Path
root = Path('/mnt/d/work/Ghostext-paper/results')
print('r1 summary:', root/'real-backend-baseline-r1'/'real_backend_summary.json')
print('r2 summary:', root/'real-backend-baseline-r2'/'real_backend_summary.json')
print('merged summary:', root/'real-backend-baseline-summary-merged.json')
PY
