#!/usr/bin/env python3
"""Verify exported bytes, source profiles, cohort membership, and input links."""
from __future__ import annotations
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_new_profile(paper, manifest_path, manifest, allow_draft):
    schema = manifest["schema"]
    directory = manifest_path.parent
    if schema in {"upstream-rrc-v1", "public-endpoint-replay-v1",
                  "upstream-observable-replay-v1", "upstream-budget-curve-v1"}:
        paths = sorted((directory / "cases").glob("*.json"))
        rows = [json.loads(p.read_text()) for p in paths]
        ids = [r["case_id"] for r in rows]
        expected = {r["case_id"] for r in manifest["tasks"]}
        assert len(ids) == len(set(ids)) and set(ids) <= expected
        if not allow_draft:
            assert set(ids) == expected
        for row in rows:
            assert row["manifest_sha256"] == digest(manifest_path)
        path = directory / "analysis.json"
        if path.exists():
            analysis = json.loads(path.read_text())
            key = "cases_sha256" if schema == "public-endpoint-replay-v1" else "case_sha256"
            assert analysis["manifest_sha256"] == digest(manifest_path)
            assert analysis[key] == {p.name: digest(p) for p in paths}
        elif not allow_draft:
            raise AssertionError(f"Missing analysis: {directory.name}")
        if schema == "upstream-rrc-v1":
            plan = (paper / manifest["study_plan_path"] if "study_plan_path" in manifest else
                    paper / "results/sp2027-accept-protocol" / (manifest["study_plan_sha256"] + ".md"))
            assert digest(plan) == manifest["study_plan_sha256"]
            for row in rows:
                stage = directory / "stages" / row["case_id"]
                for variant, data in row["variants"].items():
                    assert json.loads((stage / (variant + ".json")).read_text()) == data
                    if data["status"] == "complete":
                        assert json.loads((stage / ("receiver_" + variant + ".json")).read_text()) == (
                            row["receivers"][variant])
                natural = json.loads((stage / "natural.json").read_text())
                for control in row["natural_controls"].values():
                    n = control["tokens"]
                    assert control["token_ids"] == natural["token_ids"][:n]
                    assert control["interval_observations"] == natural["interval_observations"][:n]
        elif schema == "upstream-observable-replay-v1":
            tasks = {task["case_id"]: task for task in manifest["tasks"]}
            for identity, task in tasks.items():
                public = {key: task[key] for key in ["prompt", "message_bits", "text"]}
                encoded = json.dumps(public, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                assert hashlib.sha256(encoded.encode()).hexdigest() == identity
            seen = set()
            for binding in manifest["bindings"]:
                key = (binding["case_id"], binding["variant"])
                assert key not in seen
                seen.add(key)
                for label in ["positive", "negative"]:
                    assert binding[label]["public_input_id"] in tasks
            for row in rows:
                task = tasks[row["case_id"]]
                assert row["text_sha256"] == (
                    None if task["text"] is None else hashlib.sha256(task["text"].encode()).hexdigest())
                assert row["score_is_negative_infinity"] == (row["score"] is None)
                if task["text"] is None:
                    assert row["status"] == "no_output"
        elif schema == "upstream-budget-curve-v1":
            for row in rows:
                for block in row["budgets"].values():
                    n = block["requested_tokens"]
                    prefix = directory / "prefixes" / row["case_id"] / f"n{n}.json"
                    assert json.loads(prefix.read_text()) == block["generation"]
                    if block["generation"]["status"] == "complete":
                        assert block["generation"]["tokens"] == n
                        receiver = directory / "stages" / row["case_id"] / f"receiver_n{n}.json"
                        assert json.loads(receiver.read_text()) == block["receiver"]
    elif schema == "upstream-public-replay-v1":
        path = directory / "summary.json"
        if not path.exists() and allow_draft:
            return
        summary = json.loads(path.read_text())
        assert summary["manifest_sha256"] == digest(manifest_path)
        assert summary["all_public_features_match"]
        assert {r["case_id"] for r in summary["records"]} == {
            r["case_id"] for r in manifest["tasks"]}
        assert summary["pairs"] == len(summary["records"]) == 6
        for row in summary["records"]:
            original = json.loads((paper / "results/sp2027-upstream-gpt2/cases" /
                                   (row["source_case_id"] + ".json")).read_text())
            for label, collection in [("stego", "variants"), ("natural", "natural_controls")]:
                target = original[collection][row["variant"]]
                for field in ["token_ids", "interval_observations", "surprisal_bits"]:
                    assert row[label][field] == target[field]


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
        for entry in profile.get("input_aliases", {}).values():
            assert digest(root / entry["source"]) == entry["sha256"]
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("schema") in {
                "upstream-rrc-v1", "public-endpoint-replay-v1", "upstream-public-replay-v1",
                "upstream-observable-replay-v1", "upstream-budget-curve-v1"}:
            verify_new_profile(paper, manifest_path, manifest, args.allow_draft)
            continue
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
    for name in ["sp2027-figures", "sp2027-tables", "sp2027-accept-figures", "sp2027-accept-tables",
                 "sp2027-followup-materials"]:
        if args.allow_draft and not (paper / "results" / name / "manifest.json").exists():
            continue
        manifest = json.loads((paper / "results" / name / "manifest.json").read_text())
        for category in ["inputs", "outputs", "complete_inputs", "tables"]:
            for relative, expected in manifest.get(category, {}).items():
                assert digest(paper / relative) == expected, relative
    tests = json.loads((paper / "results/sp2027-validation/core-tests.json").read_text())
    assert tests["returncode"] == 0
    assert digest(paper / "results/sp2027-validation/core-pytest.txt") == tests["stdout_sha256"]
    for relative, expected in tests["source_sha256"].items():
        assert digest(root / relative) == expected
    theory = json.loads((paper / "results/sp2027-termination-theory/summary.json").read_text())
    assert digest(paper / "scripts/audit_termination_theory.py") == theory["source_sha256"]
    observable_audit = json.loads((paper / "results/sp2027-observable-audit/summary.json").read_text())
    assert observable_audit["all_passed"] and all(observable_audit["checks"].values())
    for relative, expected in observable_audit["source_sha256"].items():
        assert digest(root / relative) == expected
    for model in ["gpt2", "qwen25"]:
        fidelity_path = paper / "results/sp2027-observable-fidelity" / (model + ".json")
        if args.allow_draft and not fidelity_path.exists():
            continue
        fidelity = json.loads(fidelity_path.read_text())
        assert fidelity["schema"] == "observable-fidelity-audit-v1"
        assert digest(paper / "scripts/audit_observable_fidelity.py") == fidelity["source_sha256"]
        for relative, expected in fidelity["inputs"].items():
            assert digest(paper / relative) == expected, relative
        assert fidelity["all_checked_paths_match"]
        assert fidelity["counts"]["all_output_bindings"] == len(fidelity["records"]) == 960
        assert len({(r["case_id"], r["variant"], r["label"])
                    for r in fidelity["records"]}) == 960
        for row in fidelity["records"]:
            if row["original_status"] == "complete" and row["original_canonical"]:
                assert row["exact_original_path_match"] and row["public_score_status"] == "complete"
    certificate_path = paper / "results/sp2027-verified-certificate/summary.json"
    if certificate_path.exists():
        certificate = json.loads(certificate_path.read_text())
        assert digest(paper / "scripts/certify_verified_stopping.py") == certificate["source_sha256"]
        for row in certificate["certificates"]:
            scan_path = certificate_path.parent / row["scan_file"]
            assert digest(scan_path) == row["scan_sha256"]
            scan = json.loads(scan_path.read_text())
            assert [r["length"] for r in scan["scan"]] == list(range(row["cutoff"] + 1))
            assert Fraction(row["tv_lower"]) == max(
                Fraction(0), 1 - Fraction(row["early_stop_upper"])
                - Fraction(row["verified_survival_upper"]) - Fraction(row["natural_band_upper"]))
    elif not args.allow_draft:
        raise AssertionError("Missing finite verified-rule certificate")
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
