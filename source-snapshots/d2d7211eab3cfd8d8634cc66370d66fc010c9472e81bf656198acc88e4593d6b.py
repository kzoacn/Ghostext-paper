#!/usr/bin/env python3
"""Analyze public-string scores over the entire fixed upstream cohort."""
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

BOOTSTRAP_SEED = 20261028


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric_score(record):
    if record["score_is_negative_infinity"]:
        assert record["score"] is None
        return -math.inf
    assert math.isfinite(record["score"])
    return record["score"]


def summarize(rows, scores, bootstrap):
    development = [r for r in rows if r["split"] == "development"]
    test = [r for r in rows if r["split"] == "test"]
    result = {"development_pairs": len(development), "test_pairs": len(test),
              "estimable": bool(development and test)}
    if not result["estimable"]:
        return result
    def record(row, label):
        return scores[row[label]["public_input_id"]]
    train_negative = sorted(numeric_score(record(r, "negative")) for r in development)
    threshold = train_negative[math.ceil(.95 * (len(train_negative) - 1))]
    positive = np.array([numeric_score(record(r, "positive")) for r in test])
    negative = np.array([numeric_score(record(r, "negative")) for r in test])
    tpr, fpr = positive > threshold, negative > threshold
    prompts = sorted({r["prompt_id"] for r in test})
    blocks = [np.array([i for i, r in enumerate(test) if r["prompt_id"] == p]) for p in prompts]
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    samples = []
    for _ in range(bootstrap):
        indices = np.concatenate([blocks[i] for i in rng.integers(len(blocks), size=len(blocks))])
        samples.append([auc(positive[indices], negative[indices]),
                        float(tpr[indices].mean()), float(fpr[indices].mean())])
    bounds = np.quantile(samples, [.025, .975], axis=0)
    result.update({
        "auc": auc(positive, negative), "auc_prompt_cluster_95": bounds[:, 0].tolist(),
        "threshold": None if threshold == -math.inf else threshold,
        "threshold_is_negative_infinity": threshold == -math.inf,
        "test_tpr": float(tpr.mean()), "test_fpr": float(fpr.mean()),
        "test_tpr_prompt_cluster_95": bounds[:, 1].tolist(),
        "test_fpr_prompt_cluster_95": bounds[:, 2].tolist(),
        "test_tpr_wilson_95": wilson(int(tpr.sum()), len(test)),
        "test_fpr_wilson_95": wilson(int(fpr.sum()), len(test)),
        "test_prompt_ids": prompts,
        "length_baselines": {
            feature: {"auc": auc([record(r, "positive")[feature] for r in test],
                                 [record(r, "negative")[feature] for r in test]),
                      "orientation": "higher is positive"}
            for feature in ["visible_token_count", "visible_character_count"]},
        "score_statuses": {
            label: dict(Counter(record(r, label)["status"] for r in test))
            for label in ["positive", "negative"]},
        "by_test_prompt": {
            prompt: {"pairs": len(indices), "auc": auc(positive[indices], negative[indices]),
                     "tpr": float(tpr[indices].mean()), "fpr": float(fpr[indices].mean())}
            for prompt, indices in zip(prompts, blocks)},
        "interval_scope": "Prompt-cluster resampling; fixed development threshold; no canonical selection.",
    })
    return result


def summarize_emitted_strings(rows, scores, bootstrap):
    """Condition each class on its own emission, retaining unmatched emissions."""
    def emitted(row, label):
        return row[label]["generation_status"] == "complete"
    def rec(row, label):
        return scores[row[label]["public_input_id"]]
    development = [r for r in rows if r["split"] == "development"]
    test = [r for r in rows if r["split"] == "test"]
    dev_negative = [r for r in development if emitted(r, "negative")]
    positives = [r for r in test if emitted(r, "positive")]
    negatives = [r for r in test if emitted(r, "negative")]
    result = {
        "development_positive_strings": sum(emitted(r, "positive") for r in development),
        "development_negative_strings": len(dev_negative),
        "test_positive_strings": len(positives), "test_negative_strings": len(negatives),
        "estimable": bool(dev_negative and positives and negatives),
        "selection": "Each class conditions only on its own complete emission; unmatched emissions retained",
    }
    if not result["estimable"]:
        return result
    training = sorted(numeric_score(rec(r, "negative")) for r in dev_negative)
    threshold = training[math.ceil(.95 * (len(training) - 1))]
    pos = np.array([numeric_score(rec(r, "positive")) for r in positives])
    neg = np.array([numeric_score(rec(r, "negative")) for r in negatives])
    tpr, fpr = pos > threshold, neg > threshold
    prompts = sorted({r["prompt_id"] for r in test})
    pos_blocks = [np.array([i for i, r in enumerate(positives) if r["prompt_id"] == p],
                           dtype=int) for p in prompts]
    neg_blocks = [np.array([i for i, r in enumerate(negatives) if r["prompt_id"] == p],
                           dtype=int) for p in prompts]
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    samples, undefined = [], 0
    for _ in range(bootstrap):
        chosen = rng.integers(len(prompts), size=len(prompts))
        pi = np.concatenate([pos_blocks[i] for i in chosen])
        ni = np.concatenate([neg_blocks[i] for i in chosen])
        if not len(pi) or not len(ni):
            undefined += 1
            continue
        samples.append([auc(pos[pi], neg[ni]), float(tpr[pi].mean()), float(fpr[ni].mean())])
    bounds = np.quantile(samples, [.025, .975], axis=0) if samples else None
    result.update({
        "auc": auc(pos, neg), "auc_prompt_cluster_95": None if bounds is None else bounds[:, 0].tolist(),
        "threshold": None if threshold == -math.inf else threshold,
        "threshold_is_negative_infinity": threshold == -math.inf,
        "test_tpr": float(tpr.mean()), "test_fpr": float(fpr.mean()),
        "test_tpr_prompt_cluster_95": None if bounds is None else bounds[:, 1].tolist(),
        "test_fpr_prompt_cluster_95": None if bounds is None else bounds[:, 2].tolist(),
        "undefined_bootstrap_resamples": undefined,
        "bootstrap_scope": "Same prompt resample for both separately conditioned classes; empty-class draws undefined",
        "length_baselines": {
            feature: {"auc": auc([rec(r, "positive")[feature] for r in positives],
                                 [rec(r, "negative")[feature] for r in negatives]),
                      "orientation": "higher is positive"}
            for feature in ["visible_token_count", "visible_character_count"]},
    })
    return result


def analyze(directory, bootstrap=5000):
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    paths = sorted((directory / "cases").glob("*.json"))
    records = [json.loads(p.read_text()) for p in paths]
    expected = {t["case_id"]: t for t in manifest["tasks"]}
    scores = {r["case_id"]: r for r in records}
    if len(scores) != len(records) or set(scores) != set(expected):
        raise ValueError("Refusing analysis of an incomplete or duplicated public replay")
    for identity, record in scores.items():
        task = expected[identity]
        assert record["manifest_sha256"] == sha(manifest_path)
        assert record["text_sha256"] == (
            None if task["text"] is None else hashlib.sha256(task["text"].encode()).hexdigest())
        numeric_score(record)
        observations = record["interval_observations"]
        for index, observation in enumerate(observations):
            assert observation["token_id"] == record["token_ids"][index]
            assert Decimal(observation["cdf_high"]) - Decimal(observation["cdf_low"]) == (
                Decimal(observation["probability_decimal"]))
        if record["status"] == "complete":
            assert not record["score_is_negative_infinity"]
            assert len(observations) == len(record["token_ids"]) > 0
            information = -sum(math.log2(float(Decimal(o["probability_decimal"])))
                               for o in observations)
            assert information == record["surprisal_bits"]
            assert -abs(information - task["message_bits"]) == record["score"]
        else:
            assert record["score_is_negative_infinity"]
    bindings = manifest["bindings"]
    output = {
        "schema": "upstream-observable-analysis-v1", "backend": manifest["backend"],
        "manifest_sha256": sha(manifest_path), "case_sha256": {p.name: sha(p) for p in paths},
        "distinct_public_inputs": len(scores), "arm_pairs": len(bindings),
        "bootstrap_repetitions": bootstrap, "bootstrap_seed": BOOTSTRAP_SEED,
        "score": "-abs(retokenized public continuation source information - known B)",
        "negative_infinity_policy": [
            "no_output", "prompt_prefix_mismatch", "empty_continuation",
            "token_outside_source", "zero_source_mass"],
        "threshold": "higher 95th percentile of development natural scores; strict greater",
        "all_planned_generations_complete": all(
            r[label]["generation_status"] == "complete"
            for r in bindings for label in ["positive", "negative"]),
        "selection": "No canonicality or receiver-success exclusions",
        "variants": {},
    }
    for variant in sorted({r["variant"] for r in bindings}):
        rows = [r for r in bindings if r["variant"] == variant]
        block = {
            "pairs": len(rows), "text_receiver_successes": sum(r["text_receiver_success"] for r in rows),
            "generation_statuses": {
                label: dict(Counter(r[label]["generation_status"] for r in rows))
                for label in ["positive", "negative"]},
            "public_score_statuses": {
                label: dict(Counter(scores[r[label]["public_input_id"]]["status"] for r in rows))
                for label in ["positive", "negative"]},
            "by_message_bits": {},
        }
        for bits in sorted({r["message_bits"] for r in rows}):
            selected = [r for r in rows if r["message_bits"] == bits]
            all_attempts = summarize(selected, scores, bootstrap)
            emitted = [r for r in selected if all(
                r[label]["generation_status"] == "complete" for label in ["positive", "negative"])]
            block["by_message_bits"][str(bits)] = {
                "all_attempts": all_attempts,
                "emitted_pair_sensitivity": summarize(emitted, scores, bootstrap),
                "all_emitted_strings": summarize_emitted_strings(selected, scores, bootstrap),
            }
            print(variant, bits, all_attempts.get("auc"),
                  all_attempts.get("auc_prompt_cluster_95"), flush=True)
        output["variants"][variant] = block
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
