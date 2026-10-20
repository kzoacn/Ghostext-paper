#!/usr/bin/env python3
"""Post-hoc delivery validation of an explicitly different candidate policy."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "Ghostext/src"))
from artifact_utils import build_runtime_info
from experiment_prompts import prompts
from ghostext.config import CandidatePolicyConfig, CodecConfig, RuntimeConfig
from ghostext.encoder import StegoEncoder
from ghostext.decoder import StegoDecoder
from ghostext.llama_cpp_backend import LlamaCppBackendConfig, QwenLlamaCppBackend
from model_adapters import GPT2Backend
from run_stopping_llm import digest_file


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--backend", choices=["qwen", "gpt2"], required=True)
    ap.add_argument("--model-path", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--repeats", type=int, default=2)
    args = ap.parse_args()
    wanted = {"04_en_market", "03_zh_garden"} if args.backend == "qwen" else {"04_en_market"}
    tasks = [{**p, "repeat": r, "case_id": f'{p["prompt_id"]}:expanded:r{r}'}
             for p in prompts(args.backend) if p["prompt_id"] in wanted
             for r in range(args.repeats)]
    config = RuntimeConfig(
        candidate_policy=CandidatePolicyConfig(top_p=.995, max_candidates=64,
                                               min_entropy_bits=0, empty_candidate_search=4096),
        codec=CodecConfig(total_frequency=4096, guard_bits=128, natural_tail_max_tokens=0,
                          max_encode_attempts=10))
    backend = (GPT2Backend(args.model_path, threads=args.threads) if args.backend == "gpt2"
               else QwenLlamaCppBackend(LlamaCppBackendConfig(
                   model_path=str(args.model_path), n_threads=args.threads,
                   n_ctx=4096, n_batch=128)))
    model_files = [args.model_path] if args.backend == "qwen" else [
        args.model_path / name for name in ["model.safetensors", "tokenizer.json", "config.json", "revision.txt"]]
    manifest = {
        "scope": "Post-hoc development-case delivery pilot; a changed source, not a security repair or general reliability estimate.",
        "backend": args.backend, "tasks": tasks, "config": json.loads(config.to_json()),
        "model_sha256": {p.name: digest_file(p) for p in model_files},
        "source_sha256": {str(p.relative_to(ROOT.parent)): digest_file(p) for p in [
            Path(__file__).resolve(), ROOT / "scripts/model_adapters.py",
            ROOT / "scripts/experiment_prompts.py",
            *sorted((ROOT.parent / "Ghostext/src/ghostext").glob("*.py"))]},
        "runtime": build_runtime_info(), "threads": args.threads,
        "test_passphrase": "public-artifact-evaluation-key",
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    path = args.out_dir / "manifest.json"
    if path.exists():
        old = json.loads(path.read_text())
        for key in ["tasks", "config", "model_sha256", "source_sha256", "threads"]:
            if old[key] != manifest[key]:
                raise ValueError(f"Resume mismatch: {key}")
    else:
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    path = args.out_dir / "runs.jsonl"
    rows = [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
    done = {r["case_id"] for r in rows}
    with path.open("a") as output:
        for task in tasks:
            if task["case_id"] in done:
                continue
            message = ("公开测试" if task["language"] == "zh" else "test payload") + f'{task["repeat"]:04d}'
            attempts = []
            row = {**task, "message": message, "status": "failure", "attempts": attempts}
            start = time.perf_counter()
            try:
                encoded = StegoEncoder(backend, config).encode(
                    message, passphrase=manifest["test_passphrase"], prompt=task["prompt"],
                    attempt_callback=lambda r: attempts.append(asdict(r)),
                    retry_notice_callback=lambda _: None)
                decoded = StegoDecoder(backend, config).decode(
                    encoded.text, passphrase=manifest["test_passphrase"], prompt=task["prompt"])
                row.update(
                    status="success" if decoded.plaintext == message else "plaintext_mismatch",
                    cover_text=encoded.text, token_ids=list(encoded.token_ids),
                    text_sha256=hashlib.sha256(encoded.text.encode()).hexdigest(),
                    encode_seconds=encoded.elapsed_seconds, decode_seconds=decoded.elapsed_seconds,
                    tokens=encoded.total_tokens, attempts_used=encoded.attempts_used)
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
            row["elapsed_seconds"] = time.perf_counter() - start
            rows.append(row)
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
            output.flush()
            print(task["case_id"], row["status"], len(attempts),
                  round(row["elapsed_seconds"], 1), row.get("error", ""), flush=True)
    (args.out_dir / "completion.json").write_text(json.dumps({
        "planned": len(tasks), "observed": len(rows),
        "delivered": sum(r["status"] == "success" for r in rows),
        "attempts": sum(len(r["attempts"]) for r in rows)}, indent=2) + "\n")


if __name__ == "__main__":
    main()
