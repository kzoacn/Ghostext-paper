#!/usr/bin/env python3
"""Evaluate the public-bootstrap probe on archived text, without any passphrase."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "Ghostext/src"))
from artifact_utils import build_runtime_info, utc_timestamp
from audit_existing_evidence import wilson
from ghostext.llama_cpp_backend import LlamaCppBackendConfig, QwenLlamaCppBackend
from keyless_probe import probe_bootstrap


def file_hash(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-path", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "results/sp2027-keyless-legacy")
    ap.add_argument("--include-grid", action="store_true")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    sources = [
        ("legacy_stego", ROOT / "results/real-backend-baseline-runs-merged.jsonl"),
        ("historical_stable_sampler", ROOT / "results/detector-block/matched_natural_covers.jsonl"),
    ]
    if args.include_grid:
        sources.append(("legacy_grid", ROOT / "results/prompt-message-grid/prompt_message_grid_runs.jsonl"))
    inputs = []
    for label, path in sources:
        for i, line in enumerate(path.read_text().splitlines()):
            row = json.loads(line)
            if row.get("status") != "success":
                continue
            case = row.get("case", row.get("prompt", {}))
            inputs.append({
                "sample_id": f"{label}:{i}", "label": label,
                "language": case["language"], "prompt": case["prompt"],
                "text": row["cover_text"],
                "text_sha256": hashlib.sha256(row["cover_text"].encode()).hexdigest(),
            })
    if args.limit:
        inputs = inputs[:args.limit]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    backend = QwenLlamaCppBackend(LlamaCppBackendConfig(
        model_path=str(args.model_path), n_threads=args.threads, n_ctx=4096, n_batch=128, seed=7,
    ))
    manifest = {
        "schema": "keyless-bootstrap-v1",
        "inputs": {str(path.relative_to(ROOT)): file_hash(path) for _, path in sources},
        "source_sha256": {
            str(p.relative_to(ROOT.parent)): file_hash(p)
            for p in [Path(__file__).resolve(), ROOT / "scripts/keyless_probe.py",
                      *sorted((ROOT.parent / "Ghostext/src/ghostext").glob("*.py"))]
        },
        "model_sha256": file_hash(args.model_path),
        "backend_metadata": backend.metadata.as_dict(), "threads": args.threads,
        "runtime": build_runtime_info(), "created_utc": utc_timestamp(),
        "threat": "Passive text-only observer knowing exact model, prompt, policy and 60-byte bootstrap; no key.",
        "baseline_caveat": "Archived stable-filtered natural controls are length-matched and not ordinary EOS generation.",
    }
    manifest_path = args.out_dir / "manifest.json"
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text())
        for key in ["inputs", "source_sha256", "model_sha256", "backend_metadata", "threads"]:
            if old[key] != manifest[key]:
                raise ValueError(f"Resume configuration changed: {key}; use a new output directory")
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    runs_path = args.out_dir / "runs.jsonl"
    rows = [json.loads(l) for l in runs_path.read_text().splitlines()] if runs_path.exists() else []
    done = {r["sample_id"] for r in rows}
    with runs_path.open("a") as out:
        for sample in inputs:
            if sample["sample_id"] in done:
                continue
            start = time.perf_counter()
            probe = probe_bootstrap(backend, sample["text"], sample["prompt"])
            row = {k: v for k, v in sample.items() if k != "text"}
            row.update(probe)
            row["elapsed_seconds"] = time.perf_counter() - start
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            rows.append(row)
            print(sample["sample_id"], {g: r["status"] for g, r in probe["guards"].items()},
                  f"{row['elapsed_seconds']:.1f}s", flush=True)
    summary = {"threat": manifest["threat"], "by_source": {}}
    for label in sorted({r["label"] for r in rows}):
        subset = [r for r in rows if r["label"] == label]
        summary["by_source"][label] = {}
        for g in ["0", "128"]:
            statuses = Counter(r["guards"][g]["status"] for r in subset)
            positives = statuses["admissible"]
            summary["by_source"][label][g] = {
                "n": len(subset), "admissible": positives,
                "admissible_rate": positives / len(subset),
                "nominal_wilson_95": wilson(positives, len(subset)),
                "statuses": dict(statuses),
            }
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
