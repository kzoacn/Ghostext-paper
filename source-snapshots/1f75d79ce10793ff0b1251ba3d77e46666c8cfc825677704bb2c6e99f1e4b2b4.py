#!/usr/bin/env python3
"""Check the upstream study score from visible text and public inputs alone."""
from __future__ import annotations
import argparse
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path

from analyze_upstream_rrc import eligible
from upstream_rrc_experiment import load_core, boundary_mass

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_features(core, model, tokenizer, *, text, prompt, bits):
    """No secret, rotation tape, sender intervals, saved IDs or class label."""
    core.set_precision(bits, margin=40)
    context = tokenizer(prompt, return_tensors="pt")["input_ids"].to(model.device)
    visible = tokenizer.encode(text, add_special_tokens=False)
    prefix = context[0].tolist()
    if visible[:len(prefix)] != prefix:
        return {"status": "prompt_prefix_mismatch"}
    ids = visible[len(prefix):]
    vocab = min(model.config.vocab_size, len(tokenizer.vocab))
    stepper = core.LMStepper(model, vocab, max_ctx_len=900)
    stepper.prefill(context)
    observations = []
    for i, token in enumerate(ids):
        dist = stepper.distribution(vocab)
        observations.append(boundary_mass(dist, token))
        if i + 1 < len(ids):
            stepper.step(token)
    information = -sum(math.log2(float(Decimal(o["probability_decimal"])))
                       for o in observations)
    return {"status": "complete", "token_ids": ids,
            "interval_observations": observations, "surprisal_bits": information,
            "score": -abs(information - bits)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-path", type=Path, required=True)
    ap.add_argument("--cohort", type=Path, default=ROOT / "results/sp2027-upstream-gpt2")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "results/sp2027-upstream-public-features")
    args = ap.parse_args()
    cohort_manifest = json.loads((args.cohort / "manifest.json").read_text())
    analysis = json.loads((args.cohort / "analysis.json").read_text())
    assert analysis["observed_secret_instances"] == analysis["planned_secret_instances"]
    assert analysis["manifest_sha256"] == sha(args.cohort / "manifest.json")
    paths = sorted((args.cohort / "cases").glob("*.json"))
    assert {p.name: sha(p) for p in paths} == analysis["case_sha256"]
    rows = [json.loads(p.read_text()) for p in paths]
    selected = []
    for bits in [128, 512]:
        for variant in ["unverified", "verified", "fixed_endpoint"]:
            row = next(r for r in rows if r["split"] == "test"
                       and r["message_bits"] == bits and eligible(r, variant))
            selected.append((row, variant))
    core, _, provenance = load_core()
    assert provenance == cohort_manifest["upstream"]
    core.use_single_cpu_thread()
    model_hashes = {name: sha(args.model_path / name)
                    for name in cohort_manifest["model_sha256"]}
    assert model_hashes == cohort_manifest["model_sha256"]
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in [
        args.cohort / "manifest.json", args.cohort / "analysis.json", *paths]}
    sources = [Path(__file__), *[ROOT / "scripts" / name for name in [
        "upstream_rrc_experiment.py", "fetch_upstream_rrc.py", "artifact_utils.py",
        "analyze_upstream_rrc.py", "analyze_stopping_llm.py", "audit_existing_evidence.py"]]]
    manifest = {
        "schema": "upstream-public-replay-v1", "backend": "gpt2", "inputs": inputs,
        "source_sha256": {str(p.relative_to(ROOT.parent)): sha(p) for p in sources},
        "model_sha256": model_hashes, "upstream": provenance,
        "tasks": [{"case_id": row["case_id"] + ":" + variant,
                   "source_case_id": row["case_id"], "variant": variant} for row, variant in selected],
        "parameters": {"threads": 1, "cpu_affinity": sorted(os.sched_getaffinity(0))},
        "selection": "First lexicographic complete canonical matched held-out case per bit length and variant",
        "scope": "Public visible-text features; archived IDs and CDFs compared only after scoring. No private inputs.",
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model = AutoModelForCausalLM.from_pretrained(args.model_path, local_files_only=True).eval()
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True)
    records, cache = [], {}
    for row, variant in selected:
        output = {"case_id": row["case_id"] + ":" + variant,
                  "source_case_id": row["case_id"], "variant": variant}
        for label, source in [
                ("stego", row["variants"][variant]),
                ("natural", row["natural_controls"][variant])]:
            key = (source["cover_text"], row["prompt"], row["message_bits"])
            reused = key in cache
            if not reused:
                cache[key] = public_features(core, model, tokenizer, text=key[0],
                                            prompt=key[1], bits=key[2])
            result = cache[key]
            assert result["status"] == "complete"
            assert result["token_ids"] == source["token_ids"]
            assert result["interval_observations"] == source["interval_observations"]
            assert abs(result["surprisal_bits"] - source["surprisal_bits"]) < 1e-10
            output[label] = {**result, "matches_saved_ids": True, "matches_saved_cdfs": True,
                             "reused_identical_public_input": reused}
        records.append(output)
        print(output["case_id"], "both text-derived CDF traces match", flush=True)
    summary = {"manifest_sha256": sha(args.out_dir / "manifest.json"),
               "pairs": len(records), "distinct_public_inputs": len(cache),
               "records": records, "all_public_features_match": True}
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
