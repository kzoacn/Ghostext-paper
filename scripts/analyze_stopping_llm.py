#!/usr/bin/env python3
"""Frozen-score analysis with topic-held-out tests and topic-cluster intervals."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import rankdata
from audit_existing_evidence import wilson


def auc(positive, negative):
    positive, negative = np.asarray(positive), np.asarray(negative)
    ranks = rankdata(np.r_[positive, negative])
    n, m = len(positive), len(negative)
    return float((ranks[:n].sum() - n * (n + 1) / 2) / (n * m))


def eligible(row, require_recovery=False):
    s, n = row["stego"], row["natural"]
    return (
        s["status"] == n["status"] == "complete"
        and s["canonical_text_roundtrip"] and n["canonical_text_roundtrip"]
        and s["tokens"] == n["tokens"]
        and (not require_recovery or s["recovery_match"] is True)
    )


def score(row, label):
    return -abs(row[label]["surprisal_bits"] - row["message_bits"])


def summarize_slice(rows, *, bootstrap=5000, require_recovery=False):
    train = [r for r in rows if r["split"] == "development" and eligible(r, require_recovery)]
    test = [r for r in rows if r["split"] == "test" and eligible(r, require_recovery)]
    if not train or not test:
        return {"development_pairs": len(train), "test_pairs": len(test), "estimable": False}
    train_n = np.array([score(r, "natural") for r in train])
    threshold = float(np.quantile(train_n, .95, method="higher"))
    positive = np.array([score(r, "stego") for r in test])
    negative = np.array([score(r, "natural") for r in test])
    tpr = positive > threshold
    fpr = negative > threshold
    topics = sorted({r["family"] for r in test})
    blocks = [np.array([i for i, r in enumerate(test) if r["family"] == topic]) for topic in topics]
    rng = np.random.default_rng(20261022)
    resampled = []
    for _ in range(bootstrap):
        indices = np.concatenate([blocks[i] for i in rng.integers(len(blocks), size=len(blocks))])
        resampled.append([auc(positive[indices], negative[indices]),
                          float(tpr[indices].mean()), float(fpr[indices].mean())])
    bounds = np.quantile(np.asarray(resampled), [.025, .975], axis=0)
    length_auc = auc([r["stego"]["tokens"] for r in test], [r["natural"]["tokens"] for r in test])
    assert abs(length_auc - .5) < 1e-12
    return {
        "estimable": True,
        "development_pairs": len(train), "test_pairs": len(test),
        "development_families": sorted({r["family"] for r in train}), "test_families": topics,
        "auc": auc(positive, negative), "auc_topic_cluster_95": bounds[:, 0].tolist(),
        "length_only_auc": length_auc,
        "score": "-abs(public Q-source surprisal - known message bits)",
        "threshold": threshold, "positive_rule": "score strictly greater than threshold",
        "calibration": "95th percentile (higher) of development natural scores; no test tuning",
        "development_natural_fpr": float((train_n > threshold).mean()),
        "test_tpr": float(tpr.mean()), "test_fpr": float(fpr.mean()),
        "test_tpr_wilson_95": wilson(int(tpr.sum()), len(test)),
        "test_fpr_wilson_95": wilson(int(fpr.sum()), len(test)),
        "test_tpr_topic_cluster_95": bounds[:, 1].tolist(),
        "test_fpr_topic_cluster_95": bounds[:, 2].tolist(),
        "interval_scope": (
            f"Topic bootstrap over {len(topics)} eligible held-out families, "
            "conditional on the fitted threshold and eligibility rule."
        ),
        "by_test_family": {
            topic: {
                "pairs": len(indices), "auc": auc(positive[indices], negative[indices]),
                "tpr": float(tpr[indices].mean()), "fpr": float(fpr[indices].mean()),
            } for topic, indices in zip(topics, blocks)
        },
    }


def analyze(directory, bootstrap):
    manifest_path = directory / "manifest.json"
    runs_path = directory / "pairs.jsonl"
    manifest = json.loads(manifest_path.read_text())
    rows = [json.loads(l) for l in runs_path.read_text().splitlines()]
    expected = {r["case_id"] for r in manifest["tasks"]}
    observed = [r["case_id"] for r in rows]
    if set(observed) != expected or len(observed) != len(expected):
        raise ValueError(f"{directory}: cohort incomplete or contains duplicate cases")
    for row in rows:
        for label in ["stego", "natural"]:
            record = row[label]
            assert hashlib.sha256(record["cover_text"].encode()).hexdigest() == record["text_sha256"]
            assert len(record["token_ids"]) == len(record["chosen_probabilities"]) == record["tokens"]
            assert abs(-sum(np.log2(record["chosen_probabilities"])) - record["surprisal_bits"]) < 1e-8
    result = {
        "backend": manifest["backend"], "planned_pairs": len(expected), "observed_pairs": len(rows),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "runs_sha256": hashlib.sha256(runs_path.read_bytes()).hexdigest(),
        "scope": manifest["scope"],
        "stego_statuses": dict(Counter(r["stego"]["status"] for r in rows)),
        "natural_statuses": dict(Counter(r["natural"]["status"] for r in rows)),
        "completed_but_reverse_recovery_failed": sum(
            r["stego"]["status"] == "complete" and not r["stego"]["recovery_match"] for r in rows),
        "complete_canonical_matched_pairs": sum(eligible(r) for r in rows),
        "recovered_matched_pairs": sum(eligible(r, True) for r in rows),
        "selection_caveat": (
            "Primary AUC is conditional on complete canonical length-matched pairs. "
            "This is not the unconditional law of attempts or ordinary EOS generation. "
            "All excluded attempts remain in raw data and status counts."
        ),
        "by_message_bits": {},
    }
    for bits in sorted({r["message_bits"] for r in rows}):
        subset = [r for r in rows if r["message_bits"] == bits]
        result["by_message_bits"][str(bits)] = {
            "planned_pairs": len(subset),
            "complete_pairs": sum(eligible(r) for r in subset),
            "algorithm_completion_analysis": summarize_slice(subset, bootstrap=bootstrap),
            "recovered_only_sensitivity": summarize_slice(subset, bootstrap=bootstrap, require_recovery=True),
            "all_attempts_gap_auc": auc([score(r, "stego") for r in subset],
                                        [score(r, "natural") for r in subset]),
        }
    (directory / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directories", type=Path, nargs="+")
    ap.add_argument("--bootstrap", type=int, default=5000)
    args = ap.parse_args()
    for directory in args.directories:
        result = analyze(directory, args.bootstrap)
        print(result["backend"], "pairs", result["observed_pairs"],
              "matched", result["complete_canonical_matched_pairs"])
        for bits, block in result["by_message_bits"].items():
            r = block["algorithm_completion_analysis"]
            print(bits, {k: r.get(k) for k in ["test_pairs", "auc", "auc_topic_cluster_95", "test_tpr", "test_fpr"]})


if __name__ == "__main__":
    main()
