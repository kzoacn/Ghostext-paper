#!/usr/bin/env python3
"""Compare legacy and guarded Ghostext with all encoding attempts retained."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "Ghostext/src"))
from artifact_utils import build_runtime_info, deterministic_seed
from experiment_prompts import prompts
from ghostext.config import CandidatePolicyConfig, CodecConfig, RuntimeConfig
from ghostext.encoder import StegoEncoder
from ghostext.decoder import StegoDecoder
from ghostext.llama_cpp_backend import LlamaCppBackendConfig, QwenLlamaCppBackend
from model_adapters import GPT2Backend
from run_stopping_llm import digest_file
from stopping_experiment import sample_text
from trace_probe import CandidateTrace, probe_trace


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--backend", choices=["qwen", "gpt2"], required=True)
    ap.add_argument("--model-path", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--guards", type=int, nargs="+", default=[0, 128])
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    dataset = prompts(args.backend)
    tasks = [
        {**prompt, "repeat": repeat, "guard_bits": guard,
         "case_id": f"{prompt['prompt_id']}:r{repeat}:g{guard}"}
        for repeat in range(args.repeats) for prompt in dataset for guard in args.guards
    ]
    random.Random(20261021).shuffle(tasks)
    if args.limit is not None:
        tasks = tasks[:args.limit]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    backend = (
        GPT2Backend(args.model_path, threads=args.threads) if args.backend == "gpt2"
        else QwenLlamaCppBackend(LlamaCppBackendConfig(
            model_path=str(args.model_path), n_threads=args.threads, n_ctx=4096, n_batch=128))
    )
    model_files = [args.model_path] if args.backend == "qwen" else [
        args.model_path / name for name in ["model.safetensors", "tokenizer.json", "config.json", "revision.txt"]
    ]
    policy = CandidatePolicyConfig(top_p=.995, max_candidates=64, min_entropy_bits=0)
    trace = CandidateTrace(backend, policy)
    sources = [Path(__file__).resolve(), *[ROOT / "scripts" / f for f in
        ["model_adapters.py", "experiment_prompts.py", "trace_probe.py", "stopping_experiment.py"]],
        *sorted((ROOT.parent / "Ghostext/src/ghostext").glob("*.py"))]
    manifest = {
        "schema": "repair-matrix-v1", "backend": args.backend,
        "backend_metadata": backend.metadata.as_dict(),
        "source_sha256": {str(p.relative_to(ROOT.parent)): digest_file(p) for p in sources},
        "model_sha256": {p.name: digest_file(p) for p in model_files},
        "tasks": tasks, "runtime": build_runtime_info(),
        "parameters": {"threads": args.threads, "cpu_affinity": sorted(os.sched_getaffinity(0)),
                       "tail_tokens": 0, "max_encode_attempts": 10, "plaintext_bytes": 16,
                       "top_p": .995, "max_candidates": 64, "min_entropy": 0, "frequency": 4096,
                       "test_passphrase": "public-artifact-evaluation-key"},
        "scope": "Controlled codec comparison; public test payloads/credentials; all retries retained.",
    }
    mp = args.out_dir / "manifest.json"
    if mp.exists():
        old = json.loads(mp.read_text())
        for key in ["tasks", "parameters", "source_sha256", "model_sha256"]:
            if old[key] != manifest[key]:
                raise ValueError(f"Resume mismatch: {key}")
    else:
        mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    path = args.out_dir / "runs.jsonl"
    rows = [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
    done = {r["case_id"] for r in rows}
    with path.open("a") as out:
        for task in tasks:
            if task["case_id"] in done:
                continue
            number = int(task["prompt_id"][:2]) * args.repeats + task["repeat"]
            message = ("公开测试" if task["language"] == "zh" else "test payload") + f"{number:04d}"
            assert len(message.encode()) == 16
            config = RuntimeConfig(candidate_policy=policy, codec=CodecConfig(
                total_frequency=4096, guard_bits=task["guard_bits"],
                natural_tail_max_tokens=0, max_encode_attempts=10,
            ))
            attempts = []
            row = {**task, "message": message, "config": json.loads(config.to_json()),
                   "status": "failure", "attempts": attempts}
            start = time.perf_counter()
            try:
                enc = StegoEncoder(backend, config).encode(
                    message, passphrase=manifest["parameters"]["test_passphrase"],
                    prompt=task["prompt"], attempt_callback=lambda r: attempts.append(asdict(r)),
                    retry_notice_callback=lambda _: None,
                )
                trace.clear()
                dec = StegoDecoder(trace, config).decode(
                    enc.text, passphrase=manifest["parameters"]["test_passphrase"], prompt=task["prompt"],
                )
                row.update({
                    "status": "success" if dec.plaintext == message else "plaintext_mismatch",
                    "cover_text": enc.text, "text_sha256": hashlib.sha256(enc.text.encode()).hexdigest(),
                    "token_ids": list(enc.token_ids), "packet_bytes": len(enc.packet),
                    "tokens": enc.total_tokens, "packet_tokens": enc.packet_tokens,
                    "encode_seconds": enc.elapsed_seconds, "decode_seconds": dec.elapsed_seconds,
                    "net_bpt": 8 * len(message.encode()) / enc.total_tokens,
                    "gross_bpt": enc.bits_per_token, "attempts_used": enc.attempts_used,
                    "keyless_probe": probe_trace(enc.token_ids, trace.tables),
                })
                trace.clear()
                natural = sample_text(
                    trace, task["prompt"], target_tokens=enc.total_tokens,
                    seed=deterministic_seed("repair-natural", args.backend, task["case_id"]),
                )
                natural["keyless_probe"] = probe_trace(natural["token_ids"], trace.tables)
                row["natural"] = natural
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
            row["total_elapsed_seconds"] = time.perf_counter() - start
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            os.fsync(out.fileno())
            rows.append(row)
            print(args.backend, task["case_id"], row["status"], "attempts", len(attempts),
                  "seconds", round(row["total_elapsed_seconds"], 1), row.get("error", ""), flush=True)
    (args.out_dir / "completion.json").write_text(json.dumps({
        "planned": len(tasks), "completed": len(rows),
        "deliveries": sum(r["status"] == "success" for r in rows),
        "attempts": sum(len(r["attempts"]) for r in rows),
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
