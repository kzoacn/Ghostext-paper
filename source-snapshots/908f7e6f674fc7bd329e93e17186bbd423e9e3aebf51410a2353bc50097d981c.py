#!/usr/bin/env python3
"""Analyze all prespecified delivery trials, retaining failures and retries."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
from audit_existing_evidence import wilson


def summarize(rows):
    successful = [r for r in rows if r["status"] == "success"]
    paired = [r for r in successful if r["natural"]["status"] == "complete"
              and r["natural"]["canonical_text_roundtrip"]
              and r["natural"]["tokens"] == r["tokens"]]
    first = sum(r["status"] == "success" and len(r["attempts"]) == 1 for r in rows)
    return {
        "planned": len(rows), "deliveries": len(successful),
        "delivery_rate": len(successful) / len(rows),
        "nominal_delivery_wilson_95": wilson(len(successful), len(rows)),
        "first_attempt_deliveries": first, "attempts": sum(len(r["attempts"]) for r in rows),
        "failed_attempt_reasons": dict(Counter(
            a["failure_class"] for r in rows for a in r["attempts"] if not a["success"])),
        "delivery_statuses": dict(Counter(r["status"] for r in rows)),
        "natural_statuses_among_deliveries": dict(Counter(r["natural"]["status"] for r in successful)),
        "complete_matched_pairs": len(paired),
        "mean_net_bpt_given_delivery": statistics.fmean(r["net_bpt"] for r in successful) if successful else None,
        "aggregate_net_bpt_given_delivery": sum(len(r["message"].encode()) * 8 for r in successful)
                                              / sum(r["tokens"] for r in successful) if successful else None,
        "mean_gross_bpt_given_delivery": statistics.fmean(r["gross_bpt"] for r in successful) if successful else None,
        "median_encode_seconds_given_delivery": statistics.median(r["encode_seconds"] for r in successful)
                                                 if successful else None,
        "median_instrumented_decode_seconds_given_delivery": statistics.median(
            r["decode_seconds"] for r in successful) if successful else None,
        "all_attempt_seconds_per_planned_trial": sum(
            a["elapsed_seconds"] for r in rows for a in r["attempts"]) / len(rows),
        "probe_on_complete_matched_pairs": {
            guard: {
                label: dict(Counter(
                    (r if label == "stego" else r["natural"])["keyless_probe"][guard]["status"]
                    for r in paired))
                for label in ["stego", "natural"]
            } for guard in ["0", "128"]
        },
    }


def analyze(directory):
    manifest_path, path = directory / "manifest.json", directory / "runs.jsonl"
    manifest = json.loads(manifest_path.read_text())
    rows = [json.loads(l) for l in path.read_text().splitlines()]
    expected = {r["case_id"] for r in manifest["tasks"]}
    observed = [r["case_id"] for r in rows]
    if set(observed) != expected or len(observed) != len(expected):
        raise ValueError("Cohort incomplete or duplicated")
    for row in rows:
        assert 1 <= len(row["attempts"]) <= 10
        assert [a["attempt_index"] for a in row["attempts"]] == list(range(1, len(row["attempts"]) + 1))
        if row["status"] == "success":
            assert row["attempts"][-1]["success"]
            assert row["attempts_used"] == len(row["attempts"])
            assert hashlib.sha256(row["cover_text"].encode()).hexdigest() == row["text_sha256"]
            assert row["tokens"] == len(row["token_ids"])
            assert row["packet_bytes"] == len(row["message"].encode()) + 88
            assert abs(row["net_bpt"] - 8 * len(row["message"].encode()) / row["tokens"]) < 1e-12
            assert abs(row["gross_bpt"] - 8 * row["packet_bytes"] / row["tokens"]) < 1e-12
    output = {
        "backend": manifest["backend"], "observed": len(rows),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "runs_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "by_guard": {str(g): summarize([r for r in rows if r["guard_bits"] == g])
                     for g in sorted({r["guard_bits"] for r in rows})},
        "by_guard_language": {
            f"{g}:{lang}": summarize([r for r in rows if r["guard_bits"] == g and r["language"] == lang])
            for g in sorted({r["guard_bits"] for r in rows})
            for lang in sorted({r["language"] for r in rows})},
        "scope": (
            "Fixed prompt/repeat cohort, not an IID deployment sample. Nominal Wilson intervals "
            "do not account for shared prompt families. Rates condition on successful delivery; "
            "attempt counts and all-attempt runtime include failures. Instrumented decode latency "
            "includes duplicate candidate auditing. Probe results condition on complete matched controls."
        ),
    }
    (directory / "analysis.json").write_text(json.dumps(output, indent=2) + "\n")
    return output


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directories", nargs="+", type=Path)
    args = ap.parse_args()
    for directory in args.directories:
        result = analyze(directory)
        print(result["backend"], json.dumps(result["by_guard"], indent=2))


if __name__ == "__main__":
    main()
