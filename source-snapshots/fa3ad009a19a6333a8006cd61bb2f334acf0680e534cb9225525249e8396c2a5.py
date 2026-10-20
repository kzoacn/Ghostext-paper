#!/usr/bin/env python3
"""Check complete task accounting, interrupted stages, and supplemental workers."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cohort", type=Path, default=ROOT / "results/sp2027-upstream-qwen25")
    ap.add_argument("--out", type=Path,
                    default=ROOT / "results/sp2027-validation/upstream-qwen25-execution.json")
    args = ap.parse_args()
    cohort = args.cohort.resolve()
    inputs = {}

    def bind(path):
        inputs[str(path.resolve().relative_to(ROOT))] = sha(path)
        return path

    manifest_path = bind(cohort / "manifest.json")
    manifest = json.loads(manifest_path.read_text())
    assert manifest["schema"] == "upstream-rrc-v1"
    paths = sorted((cohort / "cases").glob("*.json"))
    cases = {path.stem: json.loads(bind(path).read_text()) for path in paths}
    assert set(cases) == {t["case_id"] for t in manifest["tasks"]}
    interruptions, extra_begins, preserved = [], Counter(), 0
    for path in sorted((cohort / "interruptions").glob("*.json")):
        row = json.loads(bind(path).read_text())
        assert row["manifest_sha256"] == sha(manifest_path)
        for relative, expected in row["preserved_files_sha256"].items():
            assert sha(bind(cohort / relative)) == expected
            preserved += 1
        last = row["last_persisted_event_or_begin"]
        if last["state"] == "begin":
            extra_begins[(last["case_id"], last["stage"])] += 1
        interruptions.append(str(path.relative_to(cohort)))

    journals, stage_count = {}, 0
    for case_id, case in cases.items():
        assert case["manifest_sha256"] == sha(manifest_path)
        path = bind(cohort / "events" / (case_id + ".jsonl"))
        events = [json.loads(line) for line in path.read_text().splitlines()]
        assert all(e["case_id"] == case_id for e in events)
        stages = {"unverified", "verified", "fixed_endpoint", "natural"}
        stages.update("receiver_" + name for name, record in case["variants"].items()
                      if record["status"] == "complete")
        assert {e["stage"] for e in events} == stages
        for stage in stages:
            selected = [e for e in events if e["stage"] == stage]
            assert [e["state"] for e in selected] == (
                ["begin"] * (1 + extra_begins[(case_id, stage)]) + ["persisted"])
            stage_count += 1
        journals[case_id] = events

    supplemental = {}
    for path in sorted((cohort / "launches").glob("*.json")):
        launch = json.loads(bind(path).read_text())
        assert launch["manifest_sha256"] == sha(manifest_path)
        assert launch["source_sha256"] == manifest["source_sha256"]
        started = datetime.fromisoformat(launch["created_utc"])
        for worker in launch["workers"]:
            position = worker["manifest_task_index"]
            case_id = worker["case_id"]
            assert manifest["tasks"][position]["case_id"] == case_id
            assert position % worker["shard_count"] == worker["shard_index"]
            assert case_id not in supplemental
            events = journals[case_id]
            assert all(datetime.fromisoformat(e["utc"]) >= started for e in events)
            assert all(e["cpu_affinity"] == [worker["cpu"]] for e in events)
            assert not any(extra_begins[(case_id, e["stage"])] for e in events)
            supplemental[case_id] = worker["cpu"]
    output = {
        "schema": "upstream-execution-audit-v1", "source_sha256": sha(Path(__file__)),
        "inputs": inputs, "planned_case_records": len(manifest["tasks"]),
        "observed_case_records": len(cases), "persisted_stages": stage_count,
        "documented_interruptions": interruptions, "preserved_file_hash_checks": preserved,
        "documented_repeated_stage_begins": [
            {"case_id": case, "stage": stage, "extra_begins": count}
            for (case, stage), count in sorted(extra_begins.items())],
        "supplemental_case_affinities": supplemental,
        "all_checks_passed": True,
        "scope": (
            "Consistency of retained case files and execution journals, not external "
            "attestation of model computation. Each supplemental case has a single "
            "recorded execution affinity and no duplicate stage begin. The documented "
            "interruption reuses the same frozen task and preserves completed files."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print(len(cases), "case records;", stage_count, "persisted stages;",
          len(supplemental), "supplemental cases without overlap;", preserved,
          "preserved-file checks")


if __name__ == "__main__":
    main()
