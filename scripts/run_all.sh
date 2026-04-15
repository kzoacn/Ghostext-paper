#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
RESULTS_DIR="$ROOT/results"
REAL_STATUS_FILE="$RESULTS_DIR/real_backend_eval_status.txt"

mkdir -p "$RESULTS_DIR"

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    echo "error: neither 'python' nor 'python3' is available" >&2
    exit 1
  fi
fi

"$PYTHON_BIN" scripts/run_minimal_eval.py
"$PYTHON_BIN" scripts/make_tables.py

# Real backend eval is optional but executed when environment is ready.
if [ -f "$HOME/.cache/ghostext/models/qwen35-2b-q4ks/Qwen_Qwen3.5-2B-Q4_K_S.gguf" ]; then
  if ! "$PYTHON_BIN" scripts/run_real_backend_eval.py; then
    echo "failed" > "$REAL_STATUS_FILE"
    echo "warning: real backend eval failed; keeping previous real-backend artifact if present" >&2
    echo "warning: consolidated tables will mark real-backend results as unavailable for this run" >&2
  else
    echo "ok" > "$REAL_STATUS_FILE"
  fi
else
  echo "skipped_no_model" > "$REAL_STATUS_FILE"
fi

"$PYTHON_BIN" scripts/merge_eval_tables.py
"$PYTHON_BIN" scripts/check_eval_sync.py
"$PYTHON_BIN" scripts/generate_eval_tex.py

if command -v pdflatex >/dev/null 2>&1 && command -v bibtex >/dev/null 2>&1; then
  (
    cd paper
    pdflatex -interaction=nonstopmode main.tex >/dev/null
    bibtex main >/dev/null
    pdflatex -interaction=nonstopmode main.tex >/dev/null
    pdflatex -interaction=nonstopmode main.tex >/dev/null
  )
else
  echo "warning: skipped PDF build because pdflatex/bibtex are not available" >&2
fi

echo "done (python=$PYTHON_BIN)"
