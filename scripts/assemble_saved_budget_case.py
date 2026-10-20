#!/usr/bin/env python3
"""Reassemble a budget case after all of its observations were persisted."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from analyze_upstream_rrc import validate_record
from artifact_utils import utc_timestamp
from run_upstream_budget_curve import endpoints
from run_upstream_rrc import save_new

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assemble(directory, case_id):
    """Read complete prefixes and receivers; perform no model work."""
    inputs = {}

    def read(path):
        inputs[str(path.relative_to(ROOT))] = digest(path)
        return json.loads(path.read_text())

    manifest_path = directory / "manifest.json"
    manifest = read(manifest_path)
    assert manifest["schema"] == "upstream-budget-curve-v1"
    tasks = [t for t in manifest["tasks"] if t["case_id"] == case_id]
    assert len(tasks) == 1
    task = tasks[0]
    original_paths = [
        ROOT / name for name in manifest["inputs"]
        if name.endswith("/cases/" + case_id + ".json")
    ]
    assert len(original_paths) == 1
    original_path = original_paths[0]
    assert digest(original_path) == manifest["inputs"][str(original_path.relative_to(ROOT))]
    original = read(original_path)
    assert original["case_id"] == case_id

    prescribed = endpoints(task["reference_N"])
    prefixes, receivers = {}, {}
    for n in sorted(set(prescribed.values())):
        prefix = read(directory / "prefixes" / case_id / f"n{n}.json")
        validate_record(prefix)
        assert prefix["requested_tokens"] == n
        # This recovery command only joins already completed observations.
        assert prefix["status"] == "complete" and prefix["tokens"] == n
        receiver = read(directory / "stages" / case_id / f"receiver_n{n}.json")
        assert receiver.get("ids", {}).get("status") == "complete"
        assert receiver["ids"]["public_probabilities_match_sender"]
        prefixes[n], receivers[n] = prefix, receiver
    base = prefixes[task["reference_N"]]
    origin = original["variants"]["fixed_endpoint"]
    result = {
        **task,
        "manifest_sha256": digest(manifest_path),
        "origin_comparison": {
            "origin_status": origin["status"],
            "new_status": base["status"],
            "token_ids_match": base["token_ids"] == origin["token_ids"],
            "selected_cdfs_match": base["interval_observations"] == origin["interval_observations"],
        },
        "budgets": {
            label: {
                "requested_tokens": n,
                "generation": prefixes[n],
                "receiver": receivers[n],
            }
            for label, n in prescribed.items()
        },
    }
    return result, inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--case-id", required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()
    result, inputs = assemble(directory, args.case_id)
    target = directory / "cases" / f"{args.case_id}.json"
    existed = target.exists()
    save_new(target, result)
    receipt_path = directory / "assembly-receipts" / f"{args.case_id}.json"
    if not receipt_path.exists():
        save_new(receipt_path, {
            "operation": "Join already persisted prefixes and receivers after final-case write failure",
            "utc": utc_timestamp(),
            "case_id": args.case_id,
            "source_script_sha256": digest(Path(__file__)),
            "inputs": inputs,
            "output": str(target.relative_to(ROOT)),
            "output_sha256": digest(target),
            "output_already_existed": existed,
            "model_inference_performed": False,
            "new_randomness_drawn": False,
        })
    print("Assembled", args.case_id, "from", len(inputs), "unchanged input files")


if __name__ == "__main__":
    main()
