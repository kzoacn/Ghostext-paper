#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def _fmt(x: float, n: int = 3) -> str:
    return f"{x:.{n}f}"


def main() -> None:
    src = RESULTS / "minimal_eval_results.json"
    if not src.exists():
        raise SystemExit(f"missing {src}; run scripts/run_minimal_eval.py first")

    data = json.loads(src.read_text(encoding="utf-8"))

    cc = data["correctness_and_overhead"]
    fc = data["fail_closed"]

    lines = []
    lines.append("# Minimal Evaluation Tables (Toy Backend)")
    lines.append("")
    lines.append("## Table 1: Correctness and Overhead")
    lines.append("")
    lines.append("| Case | Seed | Success | Msg Chars | Packet Bytes | Total Tok | Packet Tok | Tail Tok | Bits/Tok | Enc Tok/s | Dec Tok/s |")
    lines.append("|---|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in cc["cases"]:
        lines.append(
            "| {id} | {seed} | {success} | {ml} | {pb} | {tt} | {pt} | {tail} | {bpt} | {etps} | {dtps} |".format(
                id=row["id"],
                seed=row["seed"],
                success="Y" if row["success"] else "N",
                ml=row["message_len_chars"],
                pb=row["packet_len_bytes"],
                tt=row["total_tokens"],
                pt=row["packet_tokens"],
                tail=row["tail_tokens"],
                bpt=_fmt(row["bits_per_token"], 3),
                etps=_fmt(row["encode_tokens_per_second"], 2),
                dtps=_fmt(row["decode_tokens_per_second"], 2),
            )
        )

    lines.append("")
    lines.append(
        "Summary: success {}/{} ({:.1f}%), mean bits/token {}, mean encode tok/s {}, mean total tokens {}.".format(
            cc["n_success"],
            cc["n_cases"],
            100.0 * cc["success_rate"],
            _fmt(cc["overhead_summary"]["bits_per_token"]["mean"], 3),
            _fmt(cc["overhead_summary"]["encode_tokens_per_second"]["mean"], 2),
            _fmt(cc["overhead_summary"]["total_tokens"]["mean"], 2),
        )
    )

    lines.append("")
    lines.append("## Table 2: Fail-Closed Behavior")
    lines.append("")
    lines.append("| Scenario | Expected | Observed Success | Error Type |")
    lines.append("|---|---|:---:|---|")
    for s in fc["scenarios"]:
        lines.append(
            "| {name} | {exp} | {obs} | {err} |".format(
                name=s["scenario"],
                exp=s["expected"],
                obs="Y" if s["observed_success"] else "N",
                err=s["error"] or "-",
            )
        )

    lines.append("")
    lines.append(
        "Summary: fail-closed rate {}/{} ({:.1f}%).".format(
            fc["n_failed_as_expected"],
            fc["n_expected_fail"],
            100.0 * fc["fail_closed_rate"],
        )
    )

    out = RESULTS / "minimal_eval_tables.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
