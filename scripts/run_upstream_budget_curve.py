#!/usr/bin/env python3
"""Retain independently chosen upstream endpoints and measure their delivery cost."""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
import math
from pathlib import Path
import random
from time import perf_counter

from artifact_utils import build_runtime_info, utc_timestamp
from run_upstream_rrc import digest, event, save_new, stage
from upstream_rrc_experiment import (
    boundary_mass, decode, load_core, secret_and_key, summarize_record,
)

ROOT = Path(__file__).resolve().parents[1]
BUDGETS = [("1.00", 1, 1), ("1.25", 5, 4), ("1.50", 3, 2), ("2.00", 2, 1)]


def endpoints(reference):
    return {label: (reference * numerator + denominator - 1) // denominator
            for label, numerator, denominator in BUDGETS}


def persist_prefix(path, record):
    """Resume the same tape without replacing a previously observed elapsed time."""
    if path.exists():
        old = json.loads(path.read_text())
        semantic = lambda r: {k: v for k, v in r.items() if k != "elapsed_seconds"}
        if semantic(old) != semantic(record):
            raise ValueError(f"Deterministic prefix replay differs from retained observation: {path}")
        return old
    save_new(path, record)
    return record


def generate_prefixes(core, model, tokenizer, task, directory):
    """Persist each reached endpoint before the following model step.

    A later exception cannot alter a completed earlier endpoint. This loop
    calls unchanged upstream rotate/select_index and LMStepper primitives.
    """
    case_id, bits, context = task["case_id"], task["message_bits"], task["prompt"]
    prescribed = sorted(set(endpoints(task["reference_N"]).values()))
    maximum = prescribed[-1]
    ctx = tokenizer(context, return_tensors="pt")["input_ids"].to(model.device)
    vocab = min(model.config.vocab_size, len(tokenizer.vocab))
    margin = 53 + maximum * (math.ceil(math.log10(vocab)) + 17) + 16
    core.set_precision(bits, margin=margin)
    secret, key = secret_and_key(case_id, bits, exogenous=True)
    rng = random.Random(key)
    low, high, target = Decimal(0), Decimal(2) ** bits, Decimal(int(secret, 2))
    stepper = core.LMStepper(model, vocab, max_ctx_len=900)
    ids, observations, completed, trim_calls = [], [], {}, 0
    start = perf_counter()
    event(directory, case_id, "budget_stream", "begin")

    def snapshot(requested, status, error):
        record = summarize_record(
            tokenizer, ctx, ids, list(observations), status=status, error=error,
            elapsed=perf_counter() - start, trim_calls=trim_calls)
        record["requested_tokens"] = requested
        record["maximum_stream_tokens"] = maximum
        record["elapsed_scope"] = "Cumulative stream time through this endpoint or failure"
        path = directory / "prefixes" / case_id / f"n{requested}.json"
        result = persist_prefix(path, record)
        event(directory, case_id, f"prefix_n{requested}", "persisted")
        return result

    failure = None
    try:
        stepper.prefill(ctx)
    except Exception as exc:
        failure = exc
    for position in range(maximum):
        if failure is not None:
            break
        try:
            dist = stepper.distribution(vocab)
            target = core.rotate(target, low, high - low, Decimal(rng.random()))
            index, low, high = core.select_index(dist, low, high, target)
            token = int(dist.token_ids[index])
            observation = boundary_mass(dist, token)
            ids.append(token)
            observations.append(observation)
        except Exception as exc:
            failure = exc
            break
        current = position + 1
        if current in prescribed:
            # Persistence failures propagate; they are not model-generation outcomes.
            completed[current] = snapshot(current, "complete", None)
        if current < maximum:
            try:
                if stepper._cached_len > stepper.max_ctx_len:
                    trim_calls += 1
                stepper.step(token)
            except Exception as exc:
                failure = exc
                break
    if failure is not None:
        # Earlier saved prefixes stay complete; only not-yet-reached endpoints fail.
        for requested in prescribed:
            if requested not in completed:
                completed[requested] = snapshot(requested, type(failure).__name__, str(failure))
        event(directory, case_id, "budget_stream", "failed_after_retained_prefixes")
    else:
        event(directory, case_id, "budget_stream", "persisted")
    return completed


def prepare(args, provenance):
    original_path = args.cohort / "manifest.json"
    original = json.loads(original_path.read_text())
    if original["upstream"] != provenance:
        raise ValueError("Different upstream source")
    paths = sorted((args.cohort / "cases").glob("*.json"))
    rows = [json.loads(p.read_text()) for p in paths]
    expected = {t["case_id"]: t for t in original["tasks"]}
    if len(rows) != len(expected) or {r["case_id"] for r in rows} != set(expected):
        raise ValueError("Budget curve requires the complete original cohort")
    tasks = []
    for row in rows:
        assert row["manifest_sha256"] == digest(original_path)
        assert all(row[k] == v for k, v in expected[row["case_id"]].items())
        verified = row["variants"]["verified"]
        reference = verified["tokens"] if verified["status"] == "complete" else 2 * row["message_bits"]
        tasks.append({**expected[row["case_id"]], "reference_N": reference,
                      "reference_generation_status": verified["status"]})
    model_hashes = {name: digest(args.model_path / name) for name in original["model_sha256"]}
    if model_hashes != original["model_sha256"]:
        raise ValueError("Model differs from original cohort")
    sources = [Path(__file__), *[ROOT / "scripts" / name for name in [
        "analyze_upstream_budget.py", "run_upstream_rrc.py", "upstream_rrc_experiment.py",
        "fetch_upstream_rrc.py", "artifact_utils.py", "analyze_upstream_rrc.py",
        "analyze_stopping_llm.py", "audit_existing_evidence.py"]]]
    manifest = {
        "schema": "upstream-budget-curve-v1", "backend": original["backend"],
        "created_utc": utc_timestamp(), "upstream": provenance,
        "source_sha256": {str(p.relative_to(ROOT.parent)): digest(p) for p in sources},
        "inputs": {str(p.resolve().relative_to(ROOT)): digest(p)
                   for p in [original_path, args.study_plan, *paths]},
        "model_sha256": model_hashes, "tasks": tasks, "runtime": build_runtime_info(),
        "parameters": {
            "threads": 1, "model_dtype": "float32", "max_context_tokens": 900,
            "budget_multipliers": [label for label, _, _ in BUDGETS],
            "rounding": "integer ceiling",
            "maximum_precision_margin": "53 + 2*N*(ceil(log10(V))+17) + 16",
            "bootstrap_seed": 20261028, "bootstrap_repetitions": 5000,
        },
        "scope": (
            "Recovery/rate diagnostic on independent fixed-endpoint streams. "
            "All planned instances retained; each reached endpoint persists before "
            "continuation; later failures affect only unreached endpoints. "
            "No detector-resistance inference from these larger budgets."
        ),
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    path = args.out_dir / "manifest.json"
    if path.exists():
        old = json.loads(path.read_text())
        for key in ["schema", "backend", "upstream", "source_sha256", "inputs",
                    "model_sha256", "tasks", "parameters"]:
            if old[key] != manifest[key]:
                raise ValueError(f"Budget resume mismatch: {key}")
        return old, {r["case_id"]: r for r in rows}
    save_new(path, manifest)
    return manifest, {r["case_id"]: r for r in rows}


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
    manifest, originals = prepare(args, provenance)
    if args.prepare_only:
        print("Frozen", len(manifest["tasks"]), "budget trajectories")
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
        case_id = task["case_id"]
        output = args.out_dir / "cases" / f"{case_id}.json"
        if output.exists():
            continue
        prescribed = endpoints(task["reference_N"])
        existing = {n: args.out_dir / "prefixes" / case_id / f"n{n}.json"
                    for n in set(prescribed.values())}
        if all(p.exists() for p in existing.values()):
            prefixes = {n: json.loads(p.read_text()) for n, p in existing.items()}
        else:
            prefixes = generate_prefixes(core, model, tokenizer, task, args.out_dir)
        receivers = {}
        for n, prefix in prefixes.items():
            if prefix["status"] == "complete":
                receivers[n] = stage(
                    args.out_dir, case_id, f"receiver_n{n}",
                    lambda record=prefix: decode(
                        core, model, tokenizer, task["prompt"], record,
                        case_id=case_id, bits=task["message_bits"], exogenous=True))
            else:
                receivers[n] = {"status": "not_attempted_after_generation_failure"}
        origin = originals[case_id]["variants"]["fixed_endpoint"]
        base = prefixes[task["reference_N"]]
        comparison = {
            "origin_status": origin["status"], "new_status": base["status"],
            "token_ids_match": base["token_ids"] == origin["token_ids"],
            "selected_cdfs_match": base["interval_observations"] == origin["interval_observations"],
        }
        result = {
            **task, "manifest_sha256": manifest_hash,
            "origin_comparison": comparison,
            "budgets": {label: {"requested_tokens": n, "generation": prefixes[n],
                                "receiver": receivers[n]} for label, n in prescribed.items()},
        }
        save_new(output, result)
        print(case_id, {label: (
            block["generation"]["status"],
            block["receiver"].get("ids", {}).get("recovery_match"),
            block["receiver"].get("text", {}).get("recovery_match"))
            for label, block in result["budgets"].items()}, flush=True)


if __name__ == "__main__":
    main()
