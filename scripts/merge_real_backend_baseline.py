#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import time
from collections import Counter
from pathlib import Path
from typing import Any


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    xs = sorted(values)
    pos = (len(xs) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1.0 - frac) + xs[hi] * frac


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def ensure_same(label: str, values: list[Any]) -> Any:
    first = values[0]
    for value in values[1:]:
        if value != first:
            raise SystemExit(f"inconsistent {label} across merged inputs")
    return first


def build_markdown(summary: dict[str, Any]) -> str:
    metrics = summary["metrics"]
    language_metrics = summary["language_metrics"]
    runtime = summary["runtime"]
    model = summary["model"]
    lines = [
        "# Merged Real-Backend Baseline Summary",
        "",
        f"Generated at `{summary['generated_at_utc']}` from released baseline artifacts.",
        "",
        "Merged inputs:",
    ]
    for item in summary["merged_from"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "Baseline policy: "
            f"`top_p={summary['config']['candidate']['top_p']}`, "
            f"`max_candidates={summary['config']['candidate']['max_candidates']}`, "
            f"`min_entropy_bits={summary['config']['candidate']['min_entropy_bits']}`, "
            f"`total_frequency={summary['config']['codec']['total_frequency']}`.",
            "",
            "## Runtime and Provenance",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| Ghostext git head | `{runtime['git_head']}` |",
            f"| Host | `{runtime['host']}` |",
            f"| Platform | `{runtime['platform']}` |",
            f"| Python | `{runtime['python']}` |",
            f"| Model id | `{model['backend_metadata']['model_id']}` |",
            f"| Backend id | `{model['backend_metadata']['backend_id']}` |",
            f"| Tokenizer hash | `{model['backend_metadata']['tokenizer_hash']}` |",
            "| llama.cpp commit SHA | not captured in released source summaries |",
            "",
            "## Overall",
            "",
            "| Metric | Value |",
            "|---|---|",
            (
                f"| Decode success rate | "
                f"{metrics['success_count']}/{summary['dataset']['total_trials']}"
                f"={metrics['decode_success_rate']:.3f} |"
            ),
            (
                f"| Failure histogram | "
                f"{json.dumps(metrics['failure_histogram'], ensure_ascii=True, sort_keys=True)} |"
            ),
            (
                f"| Encode latency (s) | median {metrics['encode_latency_seconds']['median']:.2f}, "
                f"p90 {metrics['encode_latency_seconds']['p90']:.2f}, "
                f"p99 {metrics['encode_latency_seconds']['p99']:.2f} |"
            ),
            (
                f"| Decode latency (s) | median {metrics['decode_latency_seconds']['median']:.2f}, "
                f"p90 {metrics['decode_latency_seconds']['p90']:.2f}, "
                f"p99 {metrics['decode_latency_seconds']['p99']:.2f} |"
            ),
            (
                f"| Encode bits/token | mean {metrics['bits_per_token_encode']['mean']:.3f} "
                f"(median {metrics['bits_per_token_encode']['median']:.3f}, "
                f"min {metrics['bits_per_token_encode']['min']:.3f}, "
                f"max {metrics['bits_per_token_encode']['max']:.3f}) |"
            ),
            (
                f"| Attempts used | mean {metrics['attempts_used']['mean']:.3f}, "
                f"max {metrics['attempts_used']['max']} |"
            ),
            (
                f"| Approx. single-attempt encode time (s) | "
                f"{metrics['single_attempt_encode_time_seconds']['mean_derived']:.2f} |"
            ),
            "",
            "## By Language",
            "",
            "| Lang | Trials | Encode median (s) | Decode median (s) | Mean bits/token |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for lang in sorted(language_metrics):
        item = language_metrics[lang]
        lines.append(
            f"| {lang} | {item['trials']} | "
            f"{item['encode_latency_seconds']['median']:.2f} | "
            f"{item['decode_latency_seconds']['median']:.2f} | "
            f"{item['bits_per_token_encode']['mean']:.3f} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge released Ghostext real-backend baseline artifacts")
    parser.add_argument(
        "--input-dir",
        action="append",
        required=True,
        help="Directory containing real_backend_summary.json and real_backend_runs.jsonl",
    )
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()

    input_dirs = [Path(item).resolve() for item in args.input_dir]
    summaries = [load_json(path / "real_backend_summary.json") for path in input_dirs]
    runs = [row for path in input_dirs for row in load_jsonl(path / "real_backend_runs.jsonl")]

    if not runs:
        raise SystemExit("no runs found")

    model = ensure_same("model metadata", [item["model"] for item in summaries])
    config = ensure_same("config", [item["config"] for item in summaries])
    dataset_name = ensure_same("dataset name", [item["dataset"]["name"] for item in summaries])
    cases = ensure_same("dataset cases", [item["dataset"]["cases"] for item in summaries])
    runtime = {
        "git_head": ensure_same("Ghostext git head", [item["runtime"]["git_head"] for item in summaries]),
        "host": ensure_same("host", [item["runtime"]["host"] for item in summaries]),
        "platform": ensure_same("platform", [item["runtime"]["platform"] for item in summaries]),
        "python": ensure_same("python", [item["runtime"]["python"] for item in summaries]),
        "llama_cpp_commit_sha": None,
    }

    success = [row for row in runs if row.get("status") == "success" and row.get("decode_match")]
    failures = [row for row in runs if row not in success]

    encode_lat = [row["encode_wall_seconds"] for row in success]
    decode_lat = [row["decode_wall_seconds"] for row in success]
    bits_per_token = [row["bits_per_token_encode"] for row in success]
    attempts = [row["attempts_used"] for row in success]

    failure_hist = Counter((row.get("failure_class") or "unknown") for row in failures)
    language_metrics: dict[str, Any] = {}
    for language in sorted({row["case"]["language"] for row in success}):
        rows = [row for row in success if row["case"]["language"] == language]
        language_metrics[language] = {
            "trials": len(rows),
            "encode_latency_seconds": {
                "median": statistics.median(row["encode_wall_seconds"] for row in rows),
            },
            "decode_latency_seconds": {
                "median": statistics.median(row["decode_wall_seconds"] for row in rows),
            },
            "bits_per_token_encode": {
                "mean": statistics.fmean(row["bits_per_token_encode"] for row in rows),
            },
        }

    merged = {
        "generated_at_utc": utc_timestamp(),
        "merged_from": [str(path) for path in input_dirs],
        "runtime": runtime,
        "model": model,
        "config": config,
        "dataset": {
            "name": dataset_name,
            "cases": cases,
            "source_repeats": [
                {
                    "input_dir": str(path),
                    "repeats": summary["dataset"]["repeats"],
                    "total_trials": summary["dataset"]["total_trials"],
                }
                for path, summary in zip(input_dirs, summaries)
            ],
            "total_trials": len(runs),
        },
        "metrics": {
            "decode_success_rate": len(success) / len(runs),
            "success_count": len(success),
            "failure_count": len(failures),
            "failure_histogram": dict(sorted(failure_hist.items())),
            "encode_latency_seconds": {
                "median": statistics.median(encode_lat),
                "p90": quantile(encode_lat, 0.9),
                "p99": quantile(encode_lat, 0.99),
            },
            "decode_latency_seconds": {
                "median": statistics.median(decode_lat),
                "p90": quantile(decode_lat, 0.9),
                "p99": quantile(decode_lat, 0.99),
            },
            "bits_per_token_encode": {
                "mean": statistics.fmean(bits_per_token),
                "median": statistics.median(bits_per_token),
                "min": min(bits_per_token),
                "max": max(bits_per_token),
            },
            "attempts_used": {
                "mean": statistics.fmean(attempts),
                "max": max(attempts),
                "total_attempts": sum(attempts),
            },
            "single_attempt_encode_time_seconds": {
                "mean_derived": sum(encode_lat) / sum(attempts),
                "total_encode_time_seconds": sum(encode_lat),
            },
        },
        "language_metrics": language_metrics,
    }

    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(build_markdown(merged) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
