#!/usr/bin/env python3
"""Recompute historical results from raw records, without re-running a model."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def wilson(successes, trials):
    z = 1.959963984540054
    p = successes / trials
    center = (p + z * z / (2 * trials)) / (1 + z * z / trials)
    half = z * (p * (1 - p) / trials + z * z / (4 * trials**2)) ** .5 / (1 + z * z / trials)
    return [max(0, center - half), min(1, center + half)]


def summarize(rows):
    success = [r for r in rows if r["status"] == "success" and r["decode_match"]]
    net = [8 * r["plaintext_bytes"] / r["total_tokens"] for r in success]
    gross = [8 * r["packet_len"] / r["total_tokens"] for r in success]
    return {
        "trials": len(rows), "successful_deliveries": len(success),
        "first_attempt_deliveries": sum(r["attempts_used"] == 1 for r in success),
        "recorded_attempts": sum(r["attempts_used"] for r in success),
        "attempt_histogram": dict(sorted(Counter(r["attempts_used"] for r in success).items())),
        "packet_overhead_bytes": sorted(set(r["packet_len"] - r["plaintext_bytes"] for r in success)),
        "net_plaintext_bpt_mean": statistics.fmean(net),
        "net_plaintext_bpt_aggregate": 8 * sum(r["plaintext_bytes"] for r in success) / sum(r["total_tokens"] for r in success),
        "gross_packet_bpt_mean": statistics.fmean(gross),
        "encode_seconds_median": statistics.median(r["encode_elapsed_seconds"] for r in success),
        "decode_seconds_median": statistics.median(r["decode_elapsed_seconds"] for r in success),
        "nominal_wilson_95": wilson(len(success), len(rows)),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "results/sp2027-historical-audit")
    args = ap.parse_args()
    source = ROOT / "results/prompt-message-grid/prompt_message_grid_runs.jsonl"
    rows = [json.loads(line) for line in source.read_text().splitlines() if line]
    assert len({r["pair_id"] for r in rows}) == len(rows) == 100
    for r in rows:
        assert hashlib.sha256(r["cover_text"].encode()).hexdigest() == r["cover_text_sha256"]
        assert r["packet_len"] - r["plaintext_bytes"] == 88
        assert r["total_tokens"] == r["packet_tokens"] + r["tail_tokens"]
        assert r["decode_consumed_tokens"] == r["packet_tokens"]
        assert abs(r["bits_per_token_encode"] - 8 * r["packet_len"] / r["total_tokens"]) < 1e-12
    summary = {
        "source_file": str(source.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "interpretation": "Reanalysis of historical observations, not newly executed LLM experiments.",
        "overall": summarize(rows),
        "by_prompt_language": {
            lang: summarize([r for r in rows if r["prompt"]["language"] == lang])
            for lang in ["en", "zh"]
        },
        "by_message_length": {
            length: summarize([r for r in rows if r["message"]["length_class"] == length])
            for length in ["short", "medium", "long"]
        },
        "uncertainty_caveat": (
            "Wilson interval is nominal under independent Bernoulli sampling; "
            "the fixed grid shares prompts/messages and has one run per cell. "
            "It is not a confidence bound for arbitrary prompts or deployments."
        ),
    }
    # Resample prompts as clusters, retaining their ten associated messages.
    # This measures variability over this small prompt set, not generality.
    clusters = [
        [r for r in rows if r["prompt"]["prompt_id"] == prompt_id]
        for prompt_id in sorted({r["prompt"]["prompt_id"] for r in rows})
    ]
    rng = np.random.default_rng(20261020)
    estimates = []
    for _ in range(10000):
        sample = [r for i in rng.integers(0, len(clusters), len(clusters)) for r in clusters[i]]
        estimates.append(statistics.fmean(8 * r["plaintext_bytes"] / r["total_tokens"] for r in sample))
    summary["net_bpt_prompt_cluster_bootstrap_95"] = np.quantile(estimates, [.025, .975]).tolist()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
