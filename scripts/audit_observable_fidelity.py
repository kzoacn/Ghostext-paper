#!/usr/bin/env python3
"""Compare public replays with sender traces only after every score is fixed."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cohort", type=Path, required=True)
    ap.add_argument("--replay", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    original_paths = sorted((args.cohort / "cases").glob("*.json"))
    score_paths = sorted((args.replay / "cases").glob("*.json"))
    originals = {p.stem: json.loads(p.read_text()) for p in original_paths}
    scores = {p.stem: json.loads(p.read_text()) for p in score_paths}
    manifest_path, analysis_path = args.replay / "manifest.json", args.replay / "analysis.json"
    manifest = json.loads(manifest_path.read_text())
    analysis = json.loads(analysis_path.read_text())
    assert analysis["manifest_sha256"] == sha(manifest_path)
    assert analysis["case_sha256"] == {p.name: sha(p) for p in score_paths}
    assert set(scores) == {t["case_id"] for t in manifest["tasks"]}
    counts, distinct_canonical, records = Counter(), set(), []
    for binding in manifest["bindings"]:
        origin = originals[binding["case_id"]]
        for label, group in [("positive", "variants"), ("negative", "natural_controls")]:
            saved = origin[group][binding["variant"]]
            public_id = binding[label]["public_input_id"]
            replayed = scores[public_id]
            counts["all_output_bindings"] += 1
            result = {"case_id": binding["case_id"], "variant": binding["variant"],
                      "label": label, "public_input_id": public_id,
                      "original_status": saved["status"],
                      "original_canonical": saved["canonical_text_roundtrip"],
                      "public_score_status": replayed["status"]}
            if saved["status"] != "complete":
                assert replayed["status"] == "no_output" and replayed["text_sha256"] is None
                counts["unsent_private_prefixes_not_scored"] += 1
            elif saved["canonical_text_roundtrip"]:
                assert replayed["status"] == "complete"
                for field in ["token_ids", "interval_observations", "surprisal_bits"]:
                    assert replayed[field] == saved[field], (binding["case_id"], label, field)
                counts["canonical_bindings_with_exact_sender_matches"] += 1
                counts["canonical_selected_masses_compared"] += len(replayed["interval_observations"])
                distinct_canonical.add(public_id)
                result["exact_original_path_match"] = True
            else:
                counts["noncanonical_complete_bindings_retained"] += 1
                result["retokenized_path_differs_from_original"] = (
                    replayed["token_ids"] != saved["token_ids"])
            records.append(result)
    assert counts["all_output_bindings"] == 2 * len(manifest["bindings"])
    inputs = [manifest_path, analysis_path, args.cohort / "manifest.json",
              *original_paths, *score_paths]
    output = {
        "schema": "observable-fidelity-audit-v1", "backend": manifest["backend"],
        "source_sha256": sha(Path(__file__)),
        "inputs": {str(p.resolve().relative_to(ROOT)): sha(p) for p in inputs},
        "counts": dict(counts), "distinct_canonical_inputs": len(distinct_canonical),
        "all_checked_paths_match": True, "records": records,
        "scope": (
            "Post-scoring numerical fidelity check. Original paths are never supplied "
            "to the public scorer or used to filter its analysis. Noncanonical complete "
            "strings remain scored on their own retokenized paths."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print(manifest["backend"], dict(counts), flush=True)


if __name__ == "__main__":
    main()
