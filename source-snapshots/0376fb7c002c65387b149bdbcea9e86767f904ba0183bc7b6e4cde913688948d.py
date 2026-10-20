#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from artifact_utils import utc_timestamp
from run_real_backend_baseline import build_parser as build_baseline_parser
from run_real_backend_baseline import run as run_baseline


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def format_hmin(value: float) -> str:
    return f"{value:.1f}"


def condition_row(summary: dict[str, Any], *, hmin: float, source: str) -> dict[str, Any]:
    metrics = summary["metrics"]
    return {
        "min_entropy_bits": hmin,
        "source": source,
        "trials": summary["dataset"]["total_trials"],
        "success_count": metrics["success_count"],
        "decode_success_rate": metrics["decode_success_rate"],
        "decode_success_rate_wilson_95": metrics.get("decode_success_rate_wilson_95"),
        "encode_latency_median_seconds": metrics["encode_latency_seconds"]["median"],
        "decode_latency_median_seconds": metrics["decode_latency_seconds"]["median"],
        "bits_per_token_mean": metrics["bits_per_token_encode"]["mean"],
        "attempts_mean": metrics["attempts_used"]["mean"],
        "attempts_max": metrics["attempts_used"]["max"],
        "attempts_histogram": metrics["attempts_used"].get("histogram"),
        "bhat_tv_total_mean": metrics.get("approximation_audit", {}).get("bhat_tv_total", {}).get(
            "mean",
            metrics.get("approximation_audit", {}).get("bhat_tv_total_mean", 0.0),
        ),
        "bhat_tv_packet_prefix_mean": metrics.get("approximation_audit", {})
        .get("bhat_tv_packet_prefix", {})
        .get(
            "mean",
            metrics.get("approximation_audit", {}).get("bhat_tv_packet_prefix_mean", 0.0),
        ),
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# h_min Sweep Summary",
        "",
        f"Generated at `{summary['generated_at_utc']}`.",
        "",
        "| h_min | Trials | Success | Encode median (s) | Decode median (s) | Mean bits/token | Attempts mean/max | Mean Bhat TV | Source |",
        "|---:|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    for row in summary["conditions"]:
        lines.append(
            f"| {row['min_entropy_bits']:.1f} | {row['trials']} | "
            f"{row['success_count']}/{row['trials']} | "
            f"{row['encode_latency_median_seconds']:.2f} | "
            f"{row['decode_latency_median_seconds']:.2f} | "
            f"{row['bits_per_token_mean']:.3f} | "
            f"{row['attempts_mean']:.2f} / {row['attempts_max']} | "
            f"{row['bhat_tv_total_mean']:.3f} | "
            f"`{row['source']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or summarize the Ghostext h_min sweep")
    parser.add_argument("--out-dir", default="/mnt/d/work/Ghostext-paper/results/hmin-sweep")
    parser.add_argument(
        "--baseline-summary",
        default="/mnt/d/work/Ghostext-paper/results/real-backend-baseline-summary-merged.json",
        help="Existing h_min=0.0 merged baseline summary to reuse",
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--passphrase", default="paper-baseline-pass")
    parser.add_argument("--hmins", nargs="+", type=float, default=[0.0, 0.5, 1.0])
    parser.add_argument("--rerun-zero", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline_summary_path = Path(args.baseline_summary)
    conditions: list[dict[str, Any]] = []

    for hmin in args.hmins:
        if hmin == 0.0 and baseline_summary_path.exists() and not args.rerun_zero:
            summary = load_json(baseline_summary_path)
            conditions.append(condition_row(summary, hmin=hmin, source=str(baseline_summary_path)))
            continue

        condition_dir = out_dir / f"hmin-{format_hmin(hmin)}"
        baseline_args = build_baseline_parser().parse_args(
            [
                "--out-dir",
                str(condition_dir),
                "--threads",
                str(args.threads),
                "--seed",
                str(args.seed),
                "--passphrase",
                args.passphrase,
                "--min-entropy-bits",
                str(hmin),
                "--repeats",
                str(args.repeats),
            ]
        )
        run_baseline(baseline_args)
        summary_path = condition_dir / "real_backend_summary.json"
        summary = load_json(summary_path)
        conditions.append(condition_row(summary, hmin=hmin, source=str(summary_path)))

    rendered = {
        "generated_at_utc": utc_timestamp(),
        "conditions": sorted(conditions, key=lambda item: item["min_entropy_bits"]),
    }
    output_json = out_dir / "hmin_sweep_summary.json"
    output_md = out_dir / "hmin_sweep_summary.md"
    output_json.write_text(json.dumps(rendered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(rendered) + "\n", encoding="utf-8")
    print(json.dumps({"output_json": str(output_json), "output_md": str(output_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
