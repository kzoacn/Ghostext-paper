#!/usr/bin/env python3
"""Recovery versus independently assigned endpoint budgets, retaining all trials."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np

from analyze_upstream_rrc import validate_record
from audit_existing_evidence import wilson


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(rows, label, bootstrap):
    blocks = [r["budgets"][label] for r in rows]
    metrics = np.array([
        [b["receiver"].get("ids", {}).get("recovery_match") is True,
         b["receiver"].get("text", {}).get("recovery_match") is True,
         b["generation"]["status"] == "complete" and b["generation"]["canonical_text_roundtrip"],
         r["message_bits"] / b["requested_tokens"]]
        for r, b in zip(rows, blocks)], dtype=float)
    prompts = sorted({r["prompt_id"] for r in rows})
    clusters = [np.array([i for i, r in enumerate(rows) if r["prompt_id"] == p]) for p in prompts]
    rng = np.random.default_rng(20261028)
    resampled = []
    for _ in range(bootstrap):
        chosen = np.concatenate([clusters[i] for i in rng.integers(len(clusters), size=len(clusters))])
        resampled.append(metrics[chosen].mean(axis=0))
    bounds = np.quantile(resampled, [.025, .975], axis=0)
    budgets = [b["requested_tokens"] for b in blocks]
    return {
        "planned_instances": len(rows), "prompt_clusters": len(prompts),
        "generation_statuses": dict(Counter(b["generation"]["status"] for b in blocks)),
        "id_recovery_successes": int(metrics[:, 0].sum()),
        "text_recovery_successes": int(metrics[:, 1].sum()),
        "canonical_complete_outputs": int(metrics[:, 2].sum()),
        "id_recovery_fraction": float(metrics[:, 0].mean()),
        "text_recovery_fraction": float(metrics[:, 1].mean()),
        "id_recovery_prompt_cluster_95": bounds[:, 0].tolist(),
        "text_recovery_prompt_cluster_95": bounds[:, 1].tolist(),
        "id_recovery_wilson_95": wilson(int(metrics[:, 0].sum()), len(rows)),
        "text_recovery_wilson_95": wilson(int(metrics[:, 1].sum()), len(rows)),
        "mean_prescribed_tokens": float(np.mean(budgets)),
        "median_prescribed_tokens": float(np.median(budgets)),
        "total_prescribed_tokens": sum(budgets),
        "mean_bits_per_prescribed_token": float(metrics[:, 3].mean()),
        "aggregate_bits_per_prescribed_token": sum(r["message_bits"] for r in rows) / sum(budgets),
        "rate_scope": "Payload bits per prescribed budget, retaining decoding and generation failures",
        "by_prompt": {
            prompt: {"instances": len(indices),
                     "id_recovery_successes": int(metrics[indices, 0].sum()),
                     "text_recovery_successes": int(metrics[indices, 1].sum())}
            for prompt, indices in zip(prompts, clusters)},
    }


def analyze(directory, bootstrap=5000):
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    paths = sorted((directory / "cases").glob("*.json"))
    rows = [json.loads(p.read_text()) for p in paths]
    expected = {t["case_id"]: t for t in manifest["tasks"]}
    observed = [r["case_id"] for r in rows]
    if len(observed) != len(set(observed)) or set(observed) != set(expected):
        raise ValueError("Refusing analysis of an incomplete/duplicated budget cohort")
    for row in rows:
        assert row["manifest_sha256"] == sha(manifest_path)
        assert all(row[k] == v for k, v in expected[row["case_id"]].items())
        previous = None
        for label in manifest["parameters"]["budget_multipliers"]:
            block = row["budgets"][label]
            record = block["generation"]
            validate_record(record)
            assert record["requested_tokens"] == block["requested_tokens"]
            if record["status"] == "complete":
                assert record["tokens"] == block["requested_tokens"]
            else:
                assert record["tokens"] < block["requested_tokens"]
            if previous is not None:
                length = min(previous["tokens"], record["tokens"])
                assert previous["token_ids"][:length] == record["token_ids"][:length]
                assert previous["interval_observations"][:length] == record["interval_observations"][:length]
            previous = record
            receiver = block["receiver"].get("ids", {})
            if receiver.get("status") == "complete":
                assert receiver["public_probabilities_match_sender"]
    output = {
        "schema": "upstream-budget-analysis-v1", "backend": manifest["backend"],
        "manifest_sha256": sha(manifest_path), "case_sha256": {p.name: sha(p) for p in paths},
        "planned_instances": len(expected), "observed_instances": len(rows),
        "bootstrap_repetitions": bootstrap, "bootstrap_seed": 20261028,
        "origin_prefix_matches": {
            key: sum(r["origin_comparison"][key] for r in rows)
            for key in ["token_ids_match", "selected_cdfs_match"]},
        "scope": manifest["scope"], "by_message_bits": {},
    }
    for bits in sorted({r["message_bits"] for r in rows}):
        selected = [r for r in rows if r["message_bits"] == bits]
        output["by_message_bits"][str(bits)] = {
            label: summarize(selected, label, bootstrap)
            for label in manifest["parameters"]["budget_multipliers"]}
        print(bits, {label: (
            b["id_recovery_successes"], b["text_recovery_successes"], b["planned_instances"])
            for label, b in output["by_message_bits"][str(bits)].items()}, flush=True)
    (directory / "analysis.json").write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    return output


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directories", nargs="+", type=Path)
    ap.add_argument("--bootstrap", type=int, default=5000)
    args = ap.parse_args()
    for directory in args.directories:
        analyze(directory, args.bootstrap)


if __name__ == "__main__":
    main()
