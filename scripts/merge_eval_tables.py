#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def _fmt(x: float, n: int = 3) -> str:
    return f"{x:.{n}f}"


def _load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    toy = _load_json(RESULTS / "minimal_eval_results.json")
    real = _load_json(RESULTS / "real_backend_eval_results.json")

    lines: list[str] = []
    lines.append("# Consolidated Evaluation Tables")
    lines.append("")

    if toy:
        cc = toy["correctness_and_overhead"]
        fc = toy["fail_closed"]
        lines.append("## A. Toy Backend (Protocol Regression Baseline)")
        lines.append("")
        lines.append("| Case | Success | Packet Bytes | Total Tok | Bits/Tok | Enc Tok/s | Dec Tok/s |")
        lines.append("|---|:---:|---:|---:|---:|---:|---:|")
        for row in cc["cases"]:
            lines.append(
                "| {id} | {ok} | {pb} | {tt} | {bpt} | {etps} | {dtps} |".format(
                    id=row["id"],
                    ok="Y" if row["success"] else "N",
                    pb=row["packet_len_bytes"],
                    tt=row["total_tokens"],
                    bpt=_fmt(row["bits_per_token"]),
                    etps=_fmt(row["encode_tokens_per_second"], 2),
                    dtps=_fmt(row["decode_tokens_per_second"], 2),
                )
            )
        lines.append("")
        lines.append(
            "Toy summary: success {}/{} ({:.1f}%), fail-closed {}/{} ({:.1f}%).".format(
                cc["n_success"],
                cc["n_cases"],
                100.0 * cc["success_rate"],
                fc["n_failed_as_expected"],
                fc["n_expected_fail"],
                100.0 * fc["fail_closed_rate"],
            )
        )
        lines.append("")

    if real:
        lines.append("## B. Real Backend (llama.cpp + Qwen3.5-2B GGUF)")
        lines.append("")
        lines.append("| Case | Success | Packet Bytes | Total Tok | Bits/Tok | Enc Tok/s | Dec Tok/s |")
        lines.append("|---|:---:|---:|---:|---:|---:|---:|")
        for row in real["cases"]:
            lines.append(
                "| {id} | {ok} | {pb} | {tt} | {bpt} | {etps} | {dtps} |".format(
                    id=row["id"],
                    ok="Y" if row["success"] else "N",
                    pb=row["packet_len_bytes"],
                    tt=row["total_tokens"],
                    bpt=_fmt(row["bits_per_token"]),
                    etps=_fmt(row["encode_tokens_per_second"], 2),
                    dtps=_fmt(row["decode_tokens_per_second"], 2),
                )
            )
        lines.append("")
        lines.append(
            "Real summary: success {}/{} ({:.1f}%), mean bits/token {}, mean encode tok/s {}, wrong-prompt fail-closed sanity: success={}, error={}.".format(
                real["n_success"],
                real["n_cases"],
                100.0 * real["success_rate"],
                _fmt(real["summary"]["bits_per_token"]["mean"]),
                _fmt(real["summary"]["encode_tokens_per_second"]["mean"], 2),
                "Y" if real["fail_closed_sanity"]["observed_success"] else "N",
                real["fail_closed_sanity"]["error"] or "-",
            )
        )
        lines.append("")

    out = RESULTS / "consolidated_eval_tables.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
