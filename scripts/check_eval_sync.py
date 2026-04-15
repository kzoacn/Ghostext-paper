#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
REAL_STATUS_FILE = RESULTS / "real_backend_eval_status.txt"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_minimal_results(data: dict, errors: list[str]) -> None:
    corr = data.get("correctness_and_overhead", {})
    fail = data.get("fail_closed", {})

    if corr.get("n_success") != corr.get("n_cases"):
        errors.append("minimal_eval_results: matched round-trip is not 100%")

    if fail.get("n_failed_as_expected") != fail.get("n_expected_fail"):
        errors.append("minimal_eval_results: fail-closed scenarios did not all fail as expected")

    expected_errors = {
        "wrong_seed": "SynchronizationError",
        "wrong_prompt": "SynchronizationError",
        "wrong_passphrase": "IntegrityError",
        "mutated_text": "SynchronizationError",
    }
    observed = {row.get("scenario"): row.get("error") for row in fail.get("scenarios", [])}
    for scenario, err in expected_errors.items():
        if observed.get(scenario) != err:
            errors.append(
                f"minimal_eval_results: {scenario} error mismatch "
                f"(expected {err}, got {observed.get(scenario)!r})"
            )

    for row in corr.get("cases", []):
        if not row.get("success", False):
            errors.append(f"minimal_eval_results: case {row.get('id')} did not decode successfully")


def _check_real_results(data: dict, errors: list[str]) -> None:
    if data.get("n_success") != data.get("n_cases"):
        errors.append("real_backend_eval_results: matched round-trip is not 100%")

    sanity = data.get("fail_closed_sanity", {})
    if sanity.get("observed_success") is not False:
        errors.append("real_backend_eval_results: wrong-prompt sanity did not fail closed")
    if not sanity.get("error"):
        errors.append("real_backend_eval_results: wrong-prompt sanity did not report an explicit error")


def _check_markdown_summaries(minimal: dict, real: dict | None, real_status: str, errors: list[str]) -> None:
    min_md = (RESULTS / "minimal_eval_tables.md").read_text(encoding="utf-8")
    con_md = (RESULTS / "consolidated_eval_tables.md").read_text(encoding="utf-8")

    minimal_summary = (
        "Summary: success "
        f"{minimal['correctness_and_overhead']['n_success']}/"
        f"{minimal['correctness_and_overhead']['n_cases']} (100.0%), "
        "mean bits/token "
        f"{minimal['correctness_and_overhead']['overhead_summary']['bits_per_token']['mean']:.3f}, "
        "mean encode tok/s "
        f"{minimal['correctness_and_overhead']['overhead_summary']['encode_tokens_per_second']['mean']:.2f}, "
        "mean total tokens "
        f"{minimal['correctness_and_overhead']['overhead_summary']['total_tokens']['mean']:.2f}."
    )
    if minimal_summary not in min_md:
        errors.append("minimal_eval_tables.md summary does not match minimal_eval_results.json")

    fail_closed_summary = (
        "Summary: fail-closed rate "
        f"{minimal['fail_closed']['n_failed_as_expected']}/"
        f"{minimal['fail_closed']['n_expected_fail']} (100.0%)."
    )
    if fail_closed_summary not in min_md:
        errors.append("minimal_eval_tables.md fail-closed summary mismatch")

    toy_summary = (
        "Toy summary: success "
        f"{minimal['correctness_and_overhead']['n_success']}/"
        f"{minimal['correctness_and_overhead']['n_cases']} (100.0%), fail-closed "
        f"{minimal['fail_closed']['n_failed_as_expected']}/"
        f"{minimal['fail_closed']['n_expected_fail']} (100.0%)."
    )
    if toy_summary not in con_md:
        errors.append("consolidated_eval_tables.md toy summary mismatch")

    if real_status == "ok":
        if real is None:
            errors.append("real_backend_eval_status=ok but real_backend_eval_results.json is missing")
            return
        real_summary_pattern = re.escape(
            "Real summary: success "
            f"{real['n_success']}/{real['n_cases']} (100.0%), mean bits/token "
        ) + r"[0-9]+\.[0-9]{3}" + re.escape(", mean encode tok/s ") + r"[0-9]+\.[0-9]{2}"
        if not re.search(real_summary_pattern, con_md):
            errors.append("consolidated_eval_tables.md real summary missing or malformed")
    elif real_status == "failed":
        expect = "Real backend evaluation failed in this run; real-backend table is intentionally omitted."
        if expect not in con_md:
            errors.append("consolidated_eval_tables.md missing failed-real-backend marker")
    elif real_status == "skipped_no_model":
        expect = "Real backend evaluation was skipped in this run because no local GGUF model was found."
        if expect not in con_md:
            errors.append("consolidated_eval_tables.md missing skipped-real-backend marker")
    else:
        expect = "Real backend artifact exists, but run status is unknown; table is omitted for safety."
        if real is not None and expect not in con_md:
            errors.append("consolidated_eval_tables.md missing unknown-status safety marker")


def _load_real_status(errors: list[str]) -> str:
    if not REAL_STATUS_FILE.exists():
        errors.append("missing required artifact: results/real_backend_eval_status.txt")
        return "unknown"
    status = REAL_STATUS_FILE.read_text(encoding="utf-8").strip() or "unknown"
    if status not in {"ok", "failed", "skipped_no_model"}:
        errors.append(f"unexpected real backend status: {status!r}")
    return status


def main() -> int:
    errors: list[str] = []
    required = [
        RESULTS / "minimal_eval_results.json",
        RESULTS / "minimal_eval_tables.md",
        RESULTS / "consolidated_eval_tables.md",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing required artifact: {path}")

    if errors:
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1

    minimal = _load_json(RESULTS / "minimal_eval_results.json")
    real_status = _load_real_status(errors)
    real_path = RESULTS / "real_backend_eval_results.json"
    real = _load_json(real_path) if real_path.exists() else None

    _check_minimal_results(minimal, errors)
    if real_status == "ok":
        if real is None:
            errors.append("real backend status is ok but real_backend_eval_results.json is missing")
        else:
            _check_real_results(real, errors)
    _check_markdown_summaries(minimal, real, real_status, errors)

    if errors:
        print("ERROR: evaluation artifacts failed consistency checks", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1

    print("ok: evaluation artifacts pass stability-safe consistency checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
