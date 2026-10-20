#!/usr/bin/env python3
"""Prospective paired study of unchanged upstream RRC and an endpoint control."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import random

from artifact_utils import build_runtime_info, utc_timestamp
from upstream_rrc_experiment import (
    EXPERIMENT_SEED, decode, embed, load_core, prefix_record,
    sample_control, select_prompts,
)

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def save_new(path, value):
    """Atomically persist a completed stage; never replace existing observations."""
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path.exists():
        if path.read_text() != encoded:
            raise ValueError(f"Refusing to replace saved observations: {path}")
        return
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    with temporary.open("w") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def event(directory, case_id, stage, state):
    path = directory / "events" / f"{case_id}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"case_id": case_id, "stage": stage, "state": state,
              "utc": datetime.now(timezone.utc).isoformat(), "pid": os.getpid(),
              "cpu_affinity": sorted(os.sched_getaffinity(0))}
    with path.open("a") as handle:
        handle.write(json.dumps(record) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def stage(directory, case_id, name, run):
    path = directory / "stages" / case_id / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text())
    event(directory, case_id, name, "begin")
    result = run()
    save_new(path, result)
    event(directory, case_id, name, "persisted")
    return result


def prepare(args, provenance, source):
    selected, pilots, prompt_counts = select_prompts(source)
    dataset = pilots if args.pilot else selected
    repeats = 1 if args.pilot else 4
    tasks = [
        {**prompt, "message_bits": bits, "repeat": repeat,
         "case_id": f"{prompt['prompt_id']}_b{bits}_r{repeat}"}
        for prompt in dataset for bits in [128, 512] for repeat in range(repeats)
    ]
    random.Random(EXPERIMENT_SEED).shuffle(tasks)
    sources = [
        Path(__file__).resolve(), ROOT / "scripts/upstream_rrc_experiment.py",
        ROOT / "scripts/fetch_upstream_rrc.py", ROOT / "scripts/artifact_utils.py",
        ROOT / "scripts/analyze_upstream_rrc.py", ROOT / "scripts/analyze_stopping_llm.py",
        ROOT / "scripts/audit_existing_evidence.py",
    ]
    model_files = [args.model_path / name for name in [
        "model.safetensors", "config.json", "tokenizer.json", "tokenizer_config.json",
        "vocab.json", "merges.txt", "revision.txt",
    ]]
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True)
    model_config = json.loads((args.model_path / "config.json").read_text())
    source_dimensions = {
        "model_output_vocabulary": model_config["vocab_size"],
        "tokenizer_vocabulary": len(tokenizer.vocab),
        "effective_vocabulary": min(model_config["vocab_size"], len(tokenizer.vocab)),
    }
    inputs = {str(args.study_plan.resolve().relative_to(ROOT)): digest(args.study_plan)}
    if args.backend == "qwen25":
        pin_path = ROOT / "results/sp2027-environment/qwen25-download.json"
        pin = json.loads(pin_path.read_text())
        if {p.name: digest(p) for p in model_files} != {
                p.name: pin["files"][p.name] for p in model_files}:
            raise ValueError("Second-model files differ from the prospective official pin")
        inputs[str(pin_path.relative_to(ROOT))] = digest(pin_path)
    manifest = {
        "schema": "upstream-rrc-v1", "backend": args.backend, "pilot": args.pilot,
        "created_utc": utc_timestamp(), "upstream": provenance,
        "source_sha256": {str(p.relative_to(ROOT.parent)): digest(p) for p in sources},
        "model_sha256": {p.name: digest(p) for p in model_files},
        "source_dimensions": source_dimensions,
        "study_plan_sha256": digest(args.study_plan),
        "study_plan_path": str(args.study_plan.resolve().relative_to(ROOT)),
        "inputs": inputs,
        "parameters": {
            "seed": EXPERIMENT_SEED, "message_bits": [128, 512], "repeats": repeats,
            "threads": 1, "max_context_tokens": 900, "generation_cap": "2*message_bits",
            "model_dtype": "float32",
            "precision_margin": 40, "candidate_source": "upstream full vocabulary",
            "rotations": "Decimal(random.Random.random()), nominal 53-bit uniform grid",
            "natural_sampling": "lazy unbiased-bit sampling of exact Decimal(str(CDF)) masses",
            "serialization": "tokenizer.decode(context+continuation, skip_special_tokens=True)",
            "variants": ["unverified", "verified", "fixed_endpoint"],
            "fixed_endpoint": "verified length, independent message/rotation tape",
            "fixed_endpoint_precision_margin": "53 + N*(ceil(log10(vocabulary_size))+17) + 16",
        },
        "prompt_counts": prompt_counts, "prompts": dataset, "tasks": tasks,
        "runtime": build_runtime_info(),
        "packages": {name: importlib.metadata.version(name)
                     for name in ["numpy", "torch", "transformers", "tokenizers", "safetensors"]},
        "scope": (
            "Unchanged upstream embed/extract functions for stopping variants; "
            "separate fixed-endpoint and rational natural samplers. Known B/model/prompt. "
            "All stage outputs and failures retained; no cryptographic PRNG claim."
        ),
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    path = args.out_dir / "manifest.json"
    if path.exists():
        old = json.loads(path.read_text())
        for key in ["schema", "backend", "pilot", "upstream", "source_sha256", "model_sha256",
                    "study_plan_sha256", "study_plan_path", "inputs", "parameters",
                    "source_dimensions", "prompts", "tasks"]:
            if old[key] != manifest[key]:
                raise ValueError(f"Resume mismatch in {key}")
        return old
    save_new(path, manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--backend", choices=["gpt2", "qwen25"], default="gpt2")
    parser.add_argument("--study-plan", type=Path,
                        default=ROOT / "notes/sp2027-accept-study-plan.md")
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    args = parser.parse_args()
    if not 0 <= args.shard_index < args.shard_count:
        raise ValueError("Invalid task shard")
    core, source, provenance = load_core()
    core.use_single_cpu_thread()
    manifest = prepare(args, provenance, source)
    if args.prepare_only:
        print("Frozen", len(manifest["tasks"]), "planned secret instances.")
        return
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path, local_files_only=True, dtype=torch.float32).eval()
    assert all(p.dtype == torch.float32 for p in model.parameters())
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True)
    for index, task in enumerate(manifest["tasks"]):
        if index % args.shard_count != args.shard_index:
            continue
        case_id, bits, context = task["case_id"], task["message_bits"], task["prompt"]
        output = args.out_dir / "cases" / f"{case_id}.json"
        if output.exists():
            continue
        records = {}
        for name, verified in [("unverified", False), ("verified", True)]:
            records[name] = stage(
                args.out_dir, case_id, name,
                lambda flag=verified: embed(core, model, tokenizer, context,
                                            case_id=case_id, bits=bits, verified=flag))
        length = records["verified"]["tokens"]
        if records["verified"]["status"] != "complete":
            length = 2 * bits
        records["fixed_endpoint"] = stage(
            args.out_dir, case_id, "fixed_endpoint",
            lambda: sample_control(core, model, tokenizer, context, case_id=case_id,
                                   bits=bits, tokens=length, exogenous=True))
        natural_length = max(length, *(records[n]["tokens"] for n in ["unverified", "verified"]))
        natural = stage(
            args.out_dir, case_id, "natural",
            lambda: sample_control(core, model, tokenizer, context, case_id=case_id,
                                   bits=bits, tokens=natural_length, exogenous=False))
        receivers = {}
        for name in ["unverified", "verified", "fixed_endpoint"]:
            if records[name]["status"] != "complete":
                receivers[name] = {"status": "not_attempted_after_generation_failure"}
                continue
            receivers[name] = stage(
                args.out_dir, case_id, f"receiver_{name}",
                lambda mode=name: decode(core, model, tokenizer, context, records[mode],
                                         case_id=case_id, bits=bits,
                                         exogenous=mode == "fixed_endpoint"))
        controls = {
            name: prefix_record(natural, tokenizer, record["tokens"])
            for name, record in records.items()
        }
        row = {**task, "variants": records, "natural_controls": controls,
               "receivers": receivers,
               "manifest_sha256": digest(args.out_dir / "manifest.json")}
        save_new(output, row)
        print(case_id,
              {name: (r["status"], r["tokens"], r["canonical_text_roundtrip"],
                      r["rejected_stop_count"]) for name, r in records.items()}, flush=True)
    print("Shard finished", args.shard_index, "of", args.shard_count, flush=True)


if __name__ == "__main__":
    main()
