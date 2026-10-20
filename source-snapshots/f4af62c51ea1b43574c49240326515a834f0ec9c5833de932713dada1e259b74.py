#!/usr/bin/env python3
"""Verify exported bytes, source profiles, cohort membership, and input links."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("artifact_root", type=Path)
    ap.add_argument("--allow-draft", action="store_true")
    args = ap.parse_args()
    root = args.artifact_root.resolve()
    index = json.loads((root / "FILE-INDEX.json").read_text())
    if not args.allow_draft:
        assert index["status"] == "frozen-review-artifact"
    for relative, entry in index["files"].items():
        assert digest(root / relative) == entry["exported_sha256"], relative
    paper = root / "Ghostext-paper"
    profiles = json.loads((paper / "results/sp2027-source-map/index.json").read_text())["profiles"]
    protocols = json.loads((paper / "results/sp2027-source-map/protocols.json").read_text())
    assert profiles.keys() == protocols.keys()
    for name, profile in profiles.items():
        manifest_path = paper / profile["manifest"]
        assert digest(manifest_path) == profile["manifest_sha256"]
        for path, expected in {**profile["sources"], **profile["supplemental_helpers"]}.items():
            assert digest(paper / "source-snapshots" / (expected + ".py")) == expected
        for path, expected in profile.get("data_inputs", {}).items():
            assert digest(root / path) == expected
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("schema") not in {"stopping-llm-v1", "repair-matrix-v1"}:
            continue
        filename = "pairs.jsonl" if manifest["schema"] == "stopping-llm-v1" else "runs.jsonl"
        data_path = manifest_path.parent / filename
        rows = [json.loads(l) for l in data_path.read_text().splitlines()]
        ids = [r["case_id"] for r in rows]
        assert len(ids) == len(set(ids))
        expected_ids = {r["case_id"] for r in manifest["tasks"]}
        assert set(ids) <= expected_ids
        if not args.allow_draft:
            assert set(ids) == expected_ids
        analysis_path = manifest_path.parent / "analysis.json"
        if analysis_path.exists():
            analysis = json.loads(analysis_path.read_text())
            assert analysis["manifest_sha256"] == digest(manifest_path)
            assert analysis["runs_sha256"] == digest(data_path)
    for name in ["sp2027-figures", "sp2027-tables"]:
        manifest = json.loads((paper / "results" / name / "manifest.json").read_text())
        for category in ["inputs", "outputs", "complete_inputs", "tables"]:
            for relative, expected in manifest.get(category, {}).items():
                assert digest(paper / relative) == expected, relative
    tests = json.loads((paper / "results/sp2027-validation/core-tests.json").read_text())
    assert tests["returncode"] == 0
    assert digest(paper / "results/sp2027-validation/core-pytest.txt") == tests["stdout_sha256"]
    for relative, expected in tests["source_sha256"].items():
        assert digest(root / relative) == expected
    if not args.allow_draft:
        validation = json.loads((paper / "results/sp2027-format/validation.json").read_text())
        assert digest(paper / "paper/main.pdf") == validation["pdf_sha256"]
        for relative, expected in validation["paper_sources_sha256"].items():
            assert digest(paper / relative) == expected
        visual = json.loads((paper / "results/sp2027-format/visual-review.json").read_text())
        assert visual["pdf_sha256"] == validation["pdf_sha256"] and visual["all_pages_inspected"]
    print("Verified", len(index["files"]), "exported files and", len(profiles), "source profiles.")
    print("All present cohort analyses and figure/table inputs match their exported data.")


if __name__ == "__main__":
    main()
