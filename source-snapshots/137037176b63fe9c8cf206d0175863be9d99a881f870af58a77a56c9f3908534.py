#!/usr/bin/env python3
"""Fresh LLM stopping study with independent, exactly length-matched controls."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "Ghostext/src"))
from artifact_utils import build_runtime_info, deterministic_seed, utc_timestamp
from experiment_prompts import prompts
from model_adapters import GPT2Backend
from ghostext.llama_cpp_backend import LlamaCppBackendConfig, QwenLlamaCppBackend
from stopping_experiment import sample_text


def digest_file(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--backend", choices=["gpt2", "qwen"], required=True)
    ap.add_argument("--model-path", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--repeats", type=int, default=4)
    ap.add_argument("--bits", type=int, nargs="+", default=[128, 512])
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20261020)
    ap.add_argument("--verify-before-stop", action="store_true")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    dataset = prompts(args.backend)
    tasks = [
        {**prompt, "repeat": repeat, "message_bits": bits,
         "case_id": f"{prompt['prompt_id']}:b{bits}:r{repeat}"}
        for repeat in range(args.repeats) for prompt in dataset for bits in args.bits
    ]
    random.Random(args.seed).shuffle(tasks)
    if args.limit is not None:
        tasks = tasks[:args.limit]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.backend == "qwen":
        backend = QwenLlamaCppBackend(LlamaCppBackendConfig(
            model_path=str(args.model_path), n_threads=args.threads, n_ctx=4096, n_batch=128,
        ))
        model_files = [args.model_path]
    else:
        backend = GPT2Backend(args.model_path, threads=args.threads)
        model_files = [args.model_path / filename for filename in
                       ["model.safetensors", "config.json", "tokenizer.json", "revision.txt"]]
    sources = [
        Path(__file__).resolve(), ROOT / "scripts/stopping_experiment.py",
        ROOT / "scripts/experiment_prompts.py", ROOT / "scripts/model_adapters.py",
        *sorted((ROOT.parent / "Ghostext/src/ghostext").glob("*.py")),
    ]
    manifest = {
        "schema": "stopping-llm-v1", "backend": args.backend,
        "backend_metadata": backend.metadata.as_dict(),
        "model_sha256": {p.name: digest_file(p) for p in model_files},
        "source_sha256": {str(p.relative_to(ROOT.parent)): digest_file(p) for p in sources},
        "parameters": {"repeats": args.repeats, "bits": args.bits, "threads": args.threads,
                       "seed": args.seed, "verify_before_stop": args.verify_before_stop,
                       "top_p": .995, "max_candidates": 64, "frequency": 4096,
                       "stability_filter": True, "rotation_bits": 192},
        "prompts": dataset, "tasks": tasks, "created_utc": utc_timestamp(),
        "runtime": build_runtime_info(),
        "scope": (
            "Rational adapter of RRC paper Algorithm 3 to Ghostext's masked, truncated, "
            "stable, quantized source Q. Optional reverse verification is separately "
            "labelled. No claim of reproducing the paper's full model setup or current source."
        ),
    }
    mp = args.out_dir / "manifest.json"
    if mp.exists():
        previous = json.loads(mp.read_text())
        for key in ["parameters", "prompts", "tasks", "source_sha256", "model_sha256"]:
            if previous[key] != manifest[key]:
                raise ValueError(f"Resume mismatch in {key}; use a new directory")
    else:
        mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    path = args.out_dir / "pairs.jsonl"
    rows = [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
    done = {r["case_id"] for r in rows}
    with path.open("a") as out:
        for task in tasks:
            if task["case_id"] in done:
                continue
            seed = deterministic_seed("stopping", args.seed, args.backend, task["case_id"])
            stego = sample_text(backend, task["prompt"], seed=seed,
                                bits=task["message_bits"], verify_before_stop=args.verify_before_stop)
            natural = sample_text(
                backend, task["prompt"],
                seed=deterministic_seed("natural", args.seed, args.backend, task["case_id"]),
                target_tokens=stego["tokens"],
            )
            for record in [stego, natural]:
                record["text_sha256"] = hashlib.sha256(record["cover_text"].encode()).hexdigest()
            row = {**task, "stego": stego, "natural": natural}
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            os.fsync(out.fileno())
            rows.append(row)
            print(args.backend, task["case_id"], stego["status"], natural["status"],
                  "tokens", stego["tokens"],
                  "gaps", round(stego["surprisal_bits"] - task["message_bits"], 2),
                  round(natural["surprisal_bits"] - task["message_bits"], 2), flush=True)
    summary = {
        "completed_pairs": len(rows), "planned_pairs": len(tasks),
        "stego_complete": sum(r["stego"]["status"] == "complete" for r in rows),
        "natural_complete": sum(r["natural"]["status"] == "complete" for r in rows),
        "stego_recovery_matches": sum(r["stego"]["recovery_match"] is True for r in rows),
        "canonical_pairs": sum(r["stego"]["canonical_text_roundtrip"] and
                               r["natural"]["canonical_text_roundtrip"] for r in rows),
    }
    (args.out_dir / "completion.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
