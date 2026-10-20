#!/usr/bin/env python3
"""Prespecified text-channel analysis of the complete upstream RRC cohort."""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from analyze_stopping_llm import auc
from audit_existing_evidence import wilson

BOOTSTRAP_SEED = 20261026
VARIANTS = ["unverified", "verified", "fixed_endpoint"]


def eligible(row, variant, recovered=False):
    positive, negative = row["variants"][variant], row["natural_controls"][variant]
    receiver = row["receivers"][variant].get("text", {})
    return (
        positive["status"] == negative["status"] == "complete"
        and positive["canonical_text_roundtrip"] and negative["canonical_text_roundtrip"]
        and positive["tokens"] == negative["tokens"]
        and (not recovered or receiver.get("recovery_match") is True)
    )


def score(row, variant, positive):
    record = row["variants"][variant] if positive else row["natural_controls"][variant]
    return -abs(record["surprisal_bits"] - row["message_bits"])


def summarize(rows, variant, recovered=False, bootstrap=5000):
    development = [r for r in rows if r["split"] == "development"
                   and eligible(r, variant, recovered)]
    test = [r for r in rows if r["split"] == "test" and eligible(r, variant, recovered)]
    result = {"development_pairs": len(development), "test_pairs": len(test),
              "estimable": bool(development and test)}
    if not result["estimable"]:
        return result
    train_negative = np.array([score(r, variant, False) for r in development])
    threshold = float(np.quantile(train_negative, .95, method="higher"))
    positive = np.array([score(r, variant, True) for r in test])
    negative = np.array([score(r, variant, False) for r in test])
    tpr, fpr = positive > threshold, negative > threshold
    prompts = sorted({r["prompt_id"] for r in test})
    blocks = [np.array([i for i, r in enumerate(test) if r["prompt_id"] == prompt])
              for prompt in prompts]
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    values = []
    for _ in range(bootstrap):
        selected = np.concatenate([blocks[i] for i in rng.integers(len(blocks), size=len(blocks))])
        values.append([auc(positive[selected], negative[selected]),
                       float(tpr[selected].mean()), float(fpr[selected].mean())])
    bounds = np.quantile(values, [.025, .975], axis=0)
    length_auc = auc([r["variants"][variant]["tokens"] for r in test],
                     [r["natural_controls"][variant]["tokens"] for r in test])
    assert length_auc == .5
    result.update({
        "auc": auc(positive, negative), "auc_prompt_cluster_95": bounds[:, 0].tolist(),
        "length_only_auc": length_auc, "threshold": threshold,
        "test_tpr": float(tpr.mean()), "test_fpr": float(fpr.mean()),
        "test_tpr_wilson_95": wilson(int(tpr.sum()), len(test)),
        "test_fpr_wilson_95": wilson(int(fpr.sum()), len(test)),
        "test_tpr_prompt_cluster_95": bounds[:, 1].tolist(),
        "test_fpr_prompt_cluster_95": bounds[:, 2].tolist(),
        "test_prompt_ids": prompts,
        "by_test_prompt": {
            prompt: {"pairs": len(indices), "auc": auc(positive[indices], negative[indices]),
                     "tpr": float(tpr[indices].mean()), "fpr": float(fpr[indices].mean())}
            for prompt, indices in zip(prompts, blocks)
        },
        "interval_scope": "Prompt-cluster resampling conditional on eligibility and development threshold.",
    })
    return result


def validate_record(record):
    assert hashlib.sha256(record["cover_text"].encode()).hexdigest() == record["text_sha256"]
    ids, probabilities, observed = (record[k] for k in
                                   ["token_ids", "chosen_probabilities", "interval_observations"])
    assert len(ids) == len(probabilities) == len(observed) == record["tokens"]
    for token_id, probability, interval in zip(ids, probabilities, observed):
        assert interval["token_id"] == token_id
        mass = Decimal(interval["cdf_high"]) - Decimal(interval["cdf_low"])
        assert mass == Decimal(interval["probability_decimal"])
        assert float(mass) == probability and probability > 0
    assert abs(-sum(math.log2(p) for p in probabilities) - record["surprisal_bits"]) < 1e-10
    expected_canonical = (
        record["prompt_prefix_matches"] and record["visible_continuation_token_ids"] == ids)
    assert record["canonical_text_roundtrip"] == expected_canonical


def analyze(directory, bootstrap=5000):
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    paths = sorted((directory / "cases").glob("*.json"))
    rows = [json.loads(path.read_text()) for path in paths]
    expected = {row["case_id"]: row for row in manifest["tasks"]}
    observed = [row["case_id"] for row in rows]
    if len(observed) != len(set(observed)) or set(observed) != set(expected):
        raise ValueError("Refusing analysis of an incomplete or duplicated cohort")
    for row in rows:
        assert row["manifest_sha256"] == manifest_hash
        for key, value in expected[row["case_id"]].items():
            assert row[key] == value, (row["case_id"], key)
        for variant in VARIANTS:
            validate_record(row["variants"][variant])
            validate_record(row["natural_controls"][variant])
            result = row["receivers"][variant].get("ids", {})
            if result.get("status") == "complete":
                assert result["public_probabilities_match_sender"]
        unverified, verified = row["variants"]["unverified"], row["variants"]["verified"]
        if unverified["status"] == verified["status"] == "complete":
            assert verified["token_ids"][:unverified["tokens"]] == unverified["token_ids"]
    output = {
        "schema": "upstream-rrc-analysis-v1", "pilot": manifest["pilot"],
        "planned_secret_instances": len(expected), "observed_secret_instances": len(rows),
        "manifest_sha256": manifest_hash,
        "case_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "score": "-abs(public Decimal-boundary-source surprisal - known B)",
        "threshold": "higher 95th percentile of development natural scores; strict greater",
        "bootstrap_repetitions": bootstrap, "bootstrap_seed": BOOTSTRAP_SEED,
        "scope": manifest["scope"],
        "selection_caveat": (
            "Primary text-channel analyses condition on complete canonical matched pairs. "
            "Recovered sensitivity is a further selection. Fixed-endpoint primary retains failed recovery."
        ),
        "variants": {},
    }
    for variant in VARIANTS:
        output["variants"][variant] = {
            "generation_statuses": dict(Counter(r["variants"][variant]["status"] for r in rows)),
            "natural_statuses": dict(Counter(r["natural_controls"][variant]["status"] for r in rows)),
            "canonical_generated": sum(r["variants"][variant]["canonical_text_roundtrip"] for r in rows),
            "id_receiver_successes": sum(
                r["receivers"][variant].get("ids", {}).get("recovery_match") is True for r in rows),
            "text_receiver_successes": sum(
                r["receivers"][variant].get("text", {}).get("recovery_match") is True for r in rows),
            "vetoed_candidate_stops": sum(r["variants"][variant]["rejected_stop_count"] for r in rows),
            "instances_with_vetoes": sum(
                r["variants"][variant]["rejected_stop_count"] > 0 for r in rows),
            "complete_canonical_matched_pairs": sum(eligible(r, variant) for r in rows),
            "by_message_bits": {
                str(bits): {
                    "primary": summarize([r for r in rows if r["message_bits"] == bits],
                                         variant, bootstrap=bootstrap),
                    "recovered_only_sensitivity": summarize(
                        [r for r in rows if r["message_bits"] == bits],
                        variant, recovered=True, bootstrap=bootstrap),
                } for bits in sorted({r["message_bits"] for r in rows})
            },
        }
    (directory / "analysis.json").write_text(json.dumps(output, indent=2) + "\n")
    for variant, block in output["variants"].items():
        print(variant, "matched", block["complete_canonical_matched_pairs"],
              "vetoes", block["vetoed_candidate_stops"])
        for bits, values in block["by_message_bits"].items():
            print(bits, values["primary"].get("auc"),
                  values["primary"].get("auc_prompt_cluster_95"))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", type=Path, nargs="+")
    parser.add_argument("--bootstrap", type=int, default=5000)
    args = parser.parse_args()
    for directory in args.directories:
        analyze(directory, args.bootstrap)


if __name__ == "__main__":
    main()
