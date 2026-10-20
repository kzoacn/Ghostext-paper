#!/usr/bin/env python3
"""Check a prespecified verified-adapter subset against its original tapes."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("original", type=Path)
    ap.add_argument("verified", type=Path)
    args = ap.parse_args()
    load = lambda p: [json.loads(l) for l in p.read_text().splitlines()]
    old_path, new_path = args.original / "pairs.jsonl", args.verified / "pairs.jsonl"
    original = {r["case_id"]: r for r in load(old_path)}
    verified = load(new_path)
    manifest = json.loads((args.verified / "manifest.json").read_text())
    assert len(verified) == len(manifest["tasks"])
    assert {r["case_id"] for r in verified} == {r["case_id"] for r in manifest["tasks"]}
    records = []
    for row in verified:
        old, new = original[row["case_id"]]["stego"], row["stego"]
        assert new["token_ids"][:len(old["token_ids"])] == old["token_ids"]
        assert new["chosen_probabilities"][:len(old["chosen_probabilities"])] == old["chosen_probabilities"]
        if old["recovery_match"] is True:
            assert new["token_ids"] == old["token_ids"]
            assert new["status"] == old["status"]
        records.append({
            "case_id": row["case_id"], "original_status": old["status"],
            "original_reverse_match": old["recovery_match"],
            "verified_status": new["status"], "verified_reverse_match": new["recovery_match"],
            "additional_tokens": new["tokens"] - old["tokens"],
            "rejected_stop_count": new["rejected_stop_count"],
        })
    output = {
        "scope": "Mechanical adapter ablation on the same experimental random tapes; not upstream-code security.",
        "cases": len(records), "paired_prefix_and_probability_checks": len(records),
        "rejected_stops": sum(r["rejected_stop_count"] for r in records),
        "records_with_rejected_stops": sum(r["rejected_stop_count"] > 0 for r in records),
        "verified_statuses": dict(Counter(r["verified_status"] for r in records)),
        "interpretation": (
            "If no stops are rejected, this cohort does not exercise the verification branch "
            "and does not demonstrate a recovery repair."
        ),
        "records": records, "inputs": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [old_path, new_path]},
    }
    target = args.verified / "paired-ablation.json"
    target.write_text(json.dumps(output, indent=2) + "\n")
    print("cases", len(records), "rejected stops", output["rejected_stops"])


if __name__ == "__main__":
    main()
