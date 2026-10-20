#!/usr/bin/env python3
"""Secondary raw-token analysis, retaining upstream serialization failures."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from analyze_upstream_rrc import score
from analyze_stopping_llm import auc

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(rows, variant):
    def complete(row):
        a, b = row["variants"][variant], row["natural_controls"][variant]
        return a["status"] == b["status"] == "complete" and a["tokens"] == b["tokens"]
    dev = [r for r in rows if r["split"] == "development" and complete(r)]
    test = [r for r in rows if r["split"] == "test" and complete(r)]
    threshold = float(np.quantile([score(r, variant, False) for r in dev], .95, method="higher"))
    positive = np.array([score(r, variant, True) for r in test])
    negative = np.array([score(r, variant, False) for r in test])
    prompts = sorted({r["prompt_id"] for r in test})
    blocks = [np.array([i for i, r in enumerate(test) if r["prompt_id"] == p]) for p in prompts]
    rng = np.random.default_rng(20261026)
    samples = []
    for _ in range(5000):
        indices = np.concatenate([blocks[i] for i in rng.integers(len(blocks), size=len(blocks))])
        samples.append(auc(positive[indices], negative[indices]))
    return {
        "development_pairs": len(dev), "test_pairs": len(test),
        "retained_noncanonical_test_outputs": sum(
            not r["variants"][variant]["canonical_text_roundtrip"] for r in test),
        "auc": auc(positive, negative), "auc_prompt_cluster_95": np.quantile(samples, [.025, .975]).tolist(),
        "length_only_auc": auc([r["variants"][variant]["tokens"] for r in test],
                               [r["natural_controls"][variant]["tokens"] for r in test]),
        "threshold": threshold, "test_tpr": float((positive > threshold).mean()),
        "test_fpr": float((negative > threshold).mean()),
        "test_prompt_ids": prompts,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cohort", type=Path, default=ROOT / "results/sp2027-upstream-gpt2")
    args = ap.parse_args()
    analysis = json.loads((args.cohort / "analysis.json").read_text())
    assert analysis["planned_secret_instances"] == analysis["observed_secret_instances"]
    paths = sorted((args.cohort / "cases").glob("*.json"))
    assert {p.name: sha(p) for p in paths} == analysis["case_sha256"]
    rows = [json.loads(p.read_text()) for p in paths]
    output = {
        "schema": "upstream-raw-token-sensitivity-v1",
        "analysis_sha256": sha(args.cohort / "analysis.json"),
        "source_sha256": sha(Path(__file__)),
        "scope": ("Secondary raw-token comparison specified separately from primary visible text. "
                  "Keeps serialization and receiver failures; only complete paired token paths "
                  "enter scores. No recovery conditioning. Unchanged score, split, threshold rule "
                  "and 5000 prompt-bootstrap draws with seed20261026. Not a text-channel result."),
        "generation_and_control_complete": {
            variant: sum(r["variants"][variant]["status"] == r["natural_controls"][variant]["status"]
                         == "complete" for r in rows)
            for variant in ["unverified", "verified", "fixed_endpoint"]},
        "results": {
            variant: {str(bits): summarize([r for r in rows if r["message_bits"] == bits], variant)
                      for bits in [128, 512]}
            for variant in ["unverified", "verified", "fixed_endpoint"]},
    }
    (args.cohort / "raw-token-sensitivity.json").write_text(json.dumps(output, indent=2) + "\n")
    for variant, values in output["results"].items():
        print(variant, {b: r["auc"] for b, r in values.items()})


if __name__ == "__main__":
    main()
