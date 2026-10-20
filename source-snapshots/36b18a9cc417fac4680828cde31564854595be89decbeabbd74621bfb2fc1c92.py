#!/usr/bin/env python3
"""Post-hoc, keyless first-prefix-resolution replay of the frozen delivery cohort."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


def frozen_imports(generation_manifest, destination):
    """Load the original source objects, without relying on current codec defaults."""
    objects = generation_manifest["source_sha256"]
    selected = {name: expected for name, expected in objects.items()
                if name.startswith("Ghostext/src/ghostext/")
                or name == "Ghostext-paper/scripts/model_adapters.py"}
    for name, expected in selected.items():
        data = (ROOT / "source-snapshots" / (expected + ".py")).read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            assert path.read_bytes() == data
        else:
            path.write_bytes(data)
    sys.path.insert(0, str(destination / "Ghostext/src"))
    sys.path.insert(0, str(destination / "Ghostext-paper/scripts"))
    return selected


def replay(backend, text, prompt, *, policy, guard, frequency, seed, lengths):
    # These are the classifier's entire inputs. Saved IDs, packet bytes, secret,
    # key, delivery labels and decrypted headers are deliberately absent.
    from ghostext.candidate_policy import select_candidates
    from ghostext.codec import MessageSegmentDecoder
    from ghostext.quantization import quantize_candidates
    ids = backend.tokenize(text, prompt)
    result = {"text_sha256": hashlib.sha256(text.encode()).hexdigest(),
              "visible_token_ids": ids, "visible_tokens": len(ids),
              "status": "unfinished_at_end", "segment_endpoints": [], "trace": []}
    decoder = MessageSegmentDecoder(lengths[0], guard_bits=guard)
    segment = 0
    prefix = []
    for i, token in enumerate(ids):
        try:
            raw = backend.distribution(prompt, prefix, seed)
            selected = select_candidates(raw, policy, backend=backend,
                                         prompt=prompt, generated_token_ids=prefix)
            q = quantize_candidates(selected, frequency)
        except Exception as exc:
            result.update(status="source_invalid", error=type(exc).__name__,
                          error_message=str(exc), tokens_inspected=i)
            return result
        entry = {"index": i, "token_id": token, "allows_encoding": q.allows_encoding,
                 "total_frequency": q.total_frequency, "top_token_id": q.top.token_id}
        try:
            j = q.find_token_id_index(token)
            chosen = q.entries[j]
            entry.update(cdf_low=chosen.cdf_low, cdf_high=chosen.cdf_high)
        except KeyError:
            result["trace"].append(entry)
            result.update(status="outside_candidate_set", tokens_inspected=i + 1)
            return result
        result["trace"].append(entry)
        if not q.allows_encoding:
            if token != q.top.token_id:
                result.update(status="non_greedy_token", tokens_inspected=i + 1)
                return result
        else:
            try:
                decoder.absorb(q, j)
            except ValueError:
                result.update(status="zero_width_interval", tokens_inspected=i + 1)
                return result
        prefix.append(token)
        if decoder.finished:
            result["segment_endpoints"].append(i + 1)
            segment += 1
            if segment == len(lengths):
                result.update(status="endpoint_at_end" if i + 1 == len(ids)
                              else "endpoint_before_end", tokens_inspected=i + 1)
                return result
            decoder = MessageSegmentDecoder(lengths[segment], guard_bits=guard)
    result["tokens_inspected"] = len(ids)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--backend", choices=["gpt2", "qwen"], required=True)
    ap.add_argument("--model-path", type=Path, required=True)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    source_dir = ROOT / ("results/sp2027-repair-" + args.backend)
    generation = json.loads((source_dir / "manifest.json").read_text())
    rows = [json.loads(line) for line in (source_dir / "runs.jsonl").read_text().splitlines()]
    interruption = source_dir / "interruption.json"
    excluded_id = (json.loads(interruption.read_text())["first_unpersisted_case_id"]
                   if interruption.exists() else None)
    decisions, tasks = [], []
    for row in rows:
        reason = ("different_guard" if row["guard_bits"] != 128 else
                  "previously_interrupted" if row["case_id"] == excluded_id else
                  "delivery_failed" if row["status"] != "success" else
                  "natural_incomplete" if row["natural"]["status"] != "complete" else
                  "natural_noncanonical" if not row["natural"]["canonical_text_roundtrip"] else
                  "length_mismatch" if row["natural"]["tokens"] != row["tokens"] else "eligible")
        decisions.append({"case_id": row["case_id"], "reason": reason})
        if reason == "eligible":
            assert row["config"]["codec"]["natural_tail_max_tokens"] == 0
            assert len(row["message"].encode()) == 16
            tasks.append(row)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    source_objects = frozen_imports(
        generation, ROOT / "tmp/public-endpoint-frozen" / args.backend)
    from ghostext.config import CandidatePolicyConfig
    from ghostext.llama_cpp_backend import LlamaCppBackendConfig, QwenLlamaCppBackend
    from model_adapters import GPT2Backend
    model_files = ([args.model_path] if args.backend == "qwen" else
                   [args.model_path / n for n in generation["model_sha256"]])
    model_hashes = {p.name: sha(p) for p in model_files}
    assert model_hashes == generation["model_sha256"]
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in
              [source_dir / "manifest.json", source_dir / "runs.jsonl",
               source_dir / "analysis.json", ROOT / "notes/sp2027-endpoint-replay-plan.md"]}
    if interruption.exists():
        inputs[str(interruption.relative_to(ROOT))] = sha(interruption)
    manifest = {
        "schema": "public-endpoint-replay-v1", "backend": args.backend,
        "inputs": inputs, "source_sha256": {
            **source_objects, "Ghostext-paper/scripts/run_public_endpoint_replay.py": sha(Path(__file__))},
        "model_sha256": model_hashes, "eligibility": decisions,
        "eligibility_counts": dict(Counter(d["reason"] for d in decisions)),
        "tasks": [{"case_id": r["case_id"], "prompt_id": r["prompt_id"],
                   "language": r["language"]} for r in tasks],
        "parameters": {"known_segment_bytes": [60, 44], "guard_bits": 128,
                       "threads": args.threads, "cpu_affinity": sorted(os.sched_getaffinity(0))},
        "runtime": {"python": platform.python_version(), "platform": platform.platform()},
        "scope": ("Post-hoc replay of the previously eligible successful no-tail delivery "
                  "pairs, with known 16-byte plaintext length. Tests only first two-segment "
                  "prefix resolution at the visible endpoint; no authentication, decrypted "
                  "header, stall, rolling-entropy or token-budget legality test. The old "
                  "interrupted case stays excluded. No new text generation or selection "
                  "using endpoint outcomes. Model and core source hashes match generation."),
    }
    path = args.out_dir / "manifest.json"
    if path.exists():
        assert json.loads(path.read_text()) == manifest, "Resume manifest mismatch"
    else:
        write_json(path, manifest)
    backend = (GPT2Backend(args.model_path, threads=args.threads) if args.backend == "gpt2"
               else QwenLlamaCppBackend(LlamaCppBackendConfig(
                   model_path=str(args.model_path), n_threads=args.threads,
                   n_ctx=4096, n_batch=128)))
    case_dir = args.out_dir / "cases"
    case_dir.mkdir(exist_ok=True)
    for row in tasks:
        path = case_dir / (row["case_id"].replace(":", "_") + ".json")
        if path.exists():
            previous = json.loads(path.read_text())
            assert previous["manifest_sha256"] == sha(args.out_dir / "manifest.json")
            continue
        start = time.perf_counter()
        config = row["config"]
        result = {"case_id": row["case_id"], "prompt_id": row["prompt_id"],
                  "family": row["family"], "language": row["language"],
                  "manifest_sha256": sha(args.out_dir / "manifest.json")}
        for label, arm in [("stego", row), ("natural", row["natural"])]:
            observed = replay(
                backend, arm["cover_text"], row["prompt"],
                policy=CandidatePolicyConfig(**config["candidate_policy"]),
                guard=config["codec"]["guard_bits"],
                frequency=config["codec"]["total_frequency"], seed=config["seed"],
                lengths=manifest["parameters"]["known_segment_bytes"])
            # This comparison is an audit after the text-only decision.
            observed["matches_archived_token_ids"] = observed["visible_token_ids"] == arm["token_ids"]
            result[label] = observed
        result["elapsed_seconds"] = time.perf_counter() - start
        write_json(path, result)
        print(row["case_id"], result["stego"]["status"], result["natural"]["status"],
              round(result["elapsed_seconds"], 2), flush=True)
    print("Finished", len(tasks), "fixed delivery pairs.", flush=True)


if __name__ == "__main__":
    main()
