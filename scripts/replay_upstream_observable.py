#!/usr/bin/env python3
"""Replay every public upstream output, without canonical/recovery selection."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from artifact_utils import build_runtime_info, utc_timestamp
from observable_upstream_score import public_score
from run_upstream_rrc import digest, event, save_new
from upstream_rrc_experiment import load_core

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ["unverified", "verified", "fixed_endpoint"]


def prepare(args, provenance):
    cohort_path = args.cohort / "manifest.json"
    original = json.loads(cohort_path.read_text())
    if original["upstream"] != provenance:
        raise ValueError("Upstream source differs from generation")
    paths = sorted((args.cohort / "cases").glob("*.json"))
    rows = [json.loads(path.read_text()) for path in paths]
    expected = {r["case_id"]: r for r in original["tasks"]}
    if len(rows) != len(expected) or {r["case_id"] for r in rows} != set(expected):
        raise ValueError("Observable replay requires the entire original cohort")
    inputs = {str(p.resolve().relative_to(ROOT)): digest(p) for p in [
        cohort_path, args.study_plan, *paths]}
    tasks, bindings = {}, []
    for row in rows:
        assert row["manifest_sha256"] == digest(cohort_path)
        assert all(row[key] == value for key, value in expected[row["case_id"]].items())
        for variant in VARIANTS:
            binding = {key: row[key] for key in
                       ["case_id", "prompt_id", "split", "message_bits", "repeat"]}
            binding["variant"] = variant
            for label, group in [("positive", "variants"), ("negative", "natural_controls")]:
                record = row[group][variant]
                # Failed private prefixes are never passed to the observer.
                text = record["cover_text"] if record["status"] == "complete" else None
                public = {"prompt": row["prompt"], "message_bits": row["message_bits"],
                          "text": text}
                canonical = json.dumps(public, sort_keys=True, ensure_ascii=False,
                                       separators=(",", ":"))
                identity = hashlib.sha256(canonical.encode()).hexdigest()
                tasks[identity] = {"case_id": identity, **public}
                binding[label] = {
                    "public_input_id": identity, "generation_status": record["status"],
                    "sender_canonical": record["canonical_text_roundtrip"],
                }
            binding["text_receiver_success"] = (
                row["receivers"][variant].get("text", {}).get("recovery_match") is True)
            bindings.append(binding)
    model_hashes = {name: digest(args.model_path / name) for name in original["model_sha256"]}
    if model_hashes != original["model_sha256"]:
        raise ValueError("Replay model files differ from generation")
    sources = [Path(__file__), *[ROOT / "scripts" / name for name in [
        "observable_upstream_score.py", "analyze_upstream_observable.py",
        "run_upstream_rrc.py", "upstream_rrc_experiment.py", "fetch_upstream_rrc.py",
        "artifact_utils.py", "analyze_stopping_llm.py", "audit_existing_evidence.py"]]]
    manifest = {
        "schema": "upstream-observable-replay-v1", "backend": original["backend"],
        "created_utc": utc_timestamp(), "upstream": provenance,
        "source_sha256": {str(p.relative_to(ROOT.parent)): digest(p) for p in sources},
        "inputs": inputs, "model_sha256": model_hashes,
        "parameters": {"threads": 1, "model_dtype": "float32", "max_context_tokens": 900,
                       "bootstrap_seed": 20261028, "bootstrap_repetitions": 5000},
        "tasks": [tasks[k] for k in sorted(tasks)], "bindings": bindings,
        "runtime": build_runtime_info(),
        "scope": (
            "Every planned observable output; no canonicality or recovery selection. "
            "Only text and public context enter public_score. Negative infinity for "
            "specified public unsupported cases or a no-output observation. Execution "
            "exceptions remain unfinished until diagnosed. Raw endpoint pairing need "
            "not survive lossy serialization as matching visible lengths."
        ),
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    target = args.out_dir / "manifest.json"
    if target.exists():
        old = json.loads(target.read_text())
        for key in ["schema", "backend", "upstream", "source_sha256", "inputs",
                    "model_sha256", "parameters", "tasks", "bindings"]:
            if old[key] != manifest[key]:
                raise ValueError(f"Replay resume mismatch: {key}")
        return old
    save_new(target, manifest)
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cohort", type=Path, required=True)
    ap.add_argument("--model-path", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--study-plan", type=Path,
                    default=ROOT / "notes/sp2027-observable-followup-plan.md")
    ap.add_argument("--prepare-only", action="store_true")
    ap.add_argument("--shard-count", type=int, default=1)
    ap.add_argument("--shard-index", type=int, default=0)
    args = ap.parse_args()
    if not 0 <= args.shard_index < args.shard_count:
        raise ValueError("Invalid shard")
    core, _, provenance = load_core()
    manifest = prepare(args, provenance)
    if args.prepare_only:
        print("Frozen", len(manifest["tasks"]), "distinct public inputs")
        return
    core.use_single_cpu_thread()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path, local_files_only=True, dtype=torch.float32).eval()
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True)
    manifest_hash = digest(args.out_dir / "manifest.json")
    for index, task in enumerate(manifest["tasks"]):
        if index % args.shard_count != args.shard_index:
            continue
        target = args.out_dir / "cases" / f"{task['case_id']}.json"
        if target.exists():
            continue
        event(args.out_dir, task["case_id"], "public_score", "begin")
        try:
            result = public_score(core, model, tokenizer, text=task["text"],
                                  prompt=task["prompt"], bits=task["message_bits"])
        except Exception:
            event(args.out_dir, task["case_id"], "public_score", "execution_failed")
            raise
        save_new(target, {"case_id": task["case_id"], "manifest_sha256": manifest_hash, **result})
        event(args.out_dir, task["case_id"], "public_score", "persisted")
        print(index + 1, "of", len(manifest["tasks"]), result["status"], flush=True)


if __name__ == "__main__":
    main()
