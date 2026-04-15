#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python scripts/run_minimal_eval.py
python scripts/make_tables.py

# Real backend eval is optional but executed when environment is ready.
if [ -f "$HOME/.cache/ghostext/models/qwen35-2b-q4ks/Qwen_Qwen3.5-2B-Q4_K_S.gguf" ]; then
  python scripts/run_real_backend_eval.py || true
fi

python scripts/merge_eval_tables.py

(
  cd paper
  pdflatex -interaction=nonstopmode main.tex >/dev/null
  bibtex main >/dev/null
  pdflatex -interaction=nonstopmode main.tex >/dev/null
  pdflatex -interaction=nonstopmode main.tex >/dev/null
)

echo "done"
