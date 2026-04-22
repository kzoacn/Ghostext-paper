#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import statistics
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from artifact_utils import bootstrap_ci, quantile, utc_timestamp, wilson_interval


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


def median_stat(values: list[float]) -> float:
    return statistics.median(values)


def mean_stat(values: list[float]) -> float:
    return statistics.fmean(values)


def summarize_language(rows: list[dict[str, Any]]) -> dict[str, Any]:
    success = [row for row in rows if row.get("status") == "success" and row.get("decode_match")]
    encode_lat = [row["encode_wall_seconds"] for row in success]
    decode_lat = [row["decode_wall_seconds"] for row in success]
    bits = [row["bits_per_token_encode"] for row in success]
    attempts = [row["attempts_used"] for row in success]
    wilson_lo, wilson_hi = wilson_interval(len(success), len(rows))
    return {
        "trials": len(rows),
        "success_count": len(success),
        "decode_success_rate": len(success) / len(rows) if rows else 0.0,
        "decode_success_rate_wilson_95": {
            "low": wilson_lo,
            "high": wilson_hi,
        },
        "encode_latency_seconds": {
            "median": statistics.median(encode_lat) if encode_lat else 0.0,
            "bootstrap_95": {
                "low": bootstrap_ci(encode_lat, median_stat)[0] if encode_lat else 0.0,
                "high": bootstrap_ci(encode_lat, median_stat)[1] if encode_lat else 0.0,
            },
        },
        "decode_latency_seconds": {
            "median": statistics.median(decode_lat) if decode_lat else 0.0,
            "bootstrap_95": {
                "low": bootstrap_ci(decode_lat, median_stat)[0] if decode_lat else 0.0,
                "high": bootstrap_ci(decode_lat, median_stat)[1] if decode_lat else 0.0,
            },
        },
        "bits_per_token_encode": {
            "mean": statistics.fmean(bits) if bits else 0.0,
            "bootstrap_95": {
                "low": bootstrap_ci(bits, mean_stat)[0] if bits else 0.0,
                "high": bootstrap_ci(bits, mean_stat)[1] if bits else 0.0,
            },
        },
        "attempts_used": {
            "mean": statistics.fmean(attempts) if attempts else 0.0,
            "max": max(attempts) if attempts else 0,
            "histogram": {
                str(key): value for key, value in sorted(Counter(attempts).items())
            },
        },
    }


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
            f"| Ghostext git head | `{runtime['ghostext_git_head']}` |",
            f"| Paper git head | `{runtime['paper_git_head']}` |",
            f"| Host | `{runtime['host']}` |",
            f"| Platform | `{runtime['platform']}` |",
            f"| Python | `{runtime['python']}` |",
            f"| CPU model | `{runtime['cpu_model']}` |",
            f"| RAM (GiB) | `{runtime['ram_total_gib']}` |",
            f"| llama-cpp-python version | `{runtime['llama_cpp_python_version']}` |",
            f"| llama.cpp build commit | `{runtime['llama_cpp_commit_sha']}` |",
            f"| ggml build commit | `{runtime['ggml_build_commit']}` |",
            f"| Model id | `{model['backend_metadata']['model_id']}` |",
            f"| Canonical GGUF name | `{model['upstream_provenance']['canonical_model_label']}` |",
            f"| Backend id | `{model['backend_metadata']['backend_id']}` |",
            f"| Tokenizer hash | `{model['backend_metadata']['tokenizer_hash']}` |",
            "",
            "## Overall",
            "",
            "| Metric | Value |",
            "|---|---|",
            (
                f"| Decode success rate | "
                f"{metrics['success_count']}/{summary['dataset']['total_trials']}"
                f"={metrics['decode_success_rate']:.3f} "
                f"(Wilson 95% CI: [{metrics['decode_success_rate_wilson_95']['low']:.3f}, "
                f"{metrics['decode_success_rate_wilson_95']['high']:.3f}]) |"
            ),
            f"| Failure histogram | `{json.dumps(metrics['failure_histogram'], ensure_ascii=True, sort_keys=True)}` |",
            (
                f"| Encode latency (s) | median {metrics['encode_latency_seconds']['median']:.2f}, "
                f"p90 {metrics['encode_latency_seconds']['p90']:.2f}, "
                f"p99 {metrics['encode_latency_seconds']['p99']:.2f}; "
                f"bootstrap 95% CI [{metrics['encode_latency_seconds']['bootstrap_95']['low']:.2f}, "
                f"{metrics['encode_latency_seconds']['bootstrap_95']['high']:.2f}] |"
            ),
            (
                f"| Decode latency (s) | median {metrics['decode_latency_seconds']['median']:.2f}, "
                f"p90 {metrics['decode_latency_seconds']['p90']:.2f}, "
                f"p99 {metrics['decode_latency_seconds']['p99']:.2f}; "
                f"bootstrap 95% CI [{metrics['decode_latency_seconds']['bootstrap_95']['low']:.2f}, "
                f"{metrics['decode_latency_seconds']['bootstrap_95']['high']:.2f}] |"
            ),
            (
                f"| Encode bits/token | mean {metrics['bits_per_token_encode']['mean']:.3f} "
                f"(median {metrics['bits_per_token_encode']['median']:.3f}, "
                f"min {metrics['bits_per_token_encode']['min']:.3f}, "
                f"max {metrics['bits_per_token_encode']['max']:.3f}); "
                f"bootstrap 95% CI [{metrics['bits_per_token_encode']['bootstrap_95']['low']:.3f}, "
                f"{metrics['bits_per_token_encode']['bootstrap_95']['high']:.3f}] |"
            ),
            (
                f"| Attempts used | mean {metrics['attempts_used']['mean']:.3f}, "
                f"max {metrics['attempts_used']['max']}, "
                f"histogram `{json.dumps(metrics['attempts_used']['histogram'], ensure_ascii=True, sort_keys=True)}` |"
            ),
            (
                f"| Approx. single-attempt encode time (s) | "
                f"{metrics['single_attempt_encode_time_seconds']['mean_derived']:.2f} |"
            ),
            (
                f"| Bhat TV total | mean {metrics['approximation_audit']['bhat_tv_total']['mean']:.3f}, "
                f"median {metrics['approximation_audit']['bhat_tv_total']['median']:.3f} |"
            ),
            "",
            "## By Language",
            "",
            "| Lang | Trials | Encode median (s) | Decode median (s) | Mean bits/token | Attempts histogram |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for lang in sorted(language_metrics):
        item = language_metrics[lang]
        lines.append(
            f"| {lang} | {item['trials']} | "
            f"{item['encode_latency_seconds']['median']:.2f} | "
            f"{item['decode_latency_seconds']['median']:.2f} | "
            f"{item['bits_per_token_encode']['mean']:.3f} | "
            f"`{json.dumps(item['attempts_used']['histogram'], ensure_ascii=True, sort_keys=True)}` |"
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
    parser.add_argument("--output-runs-jsonl", default=None)
    parser.add_argument("--output-step-jsonl", default=None)
    args = parser.parse_args()

    input_dirs = [Path(item).resolve() for item in args.input_dir]
    summaries = [load_json(path / "real_backend_summary.json") for path in input_dirs]
    runs = [row for path in input_dirs for row in load_jsonl(path / "real_backend_runs.jsonl")]
    step_rows = [
        row for path in input_dirs for row in load_jsonl(path / "real_backend_step_audit.jsonl")
    ]

    if not runs:
        raise SystemExit("no runs found")

    model = ensure_same("model metadata", [item["model"] for item in summaries])
    config = ensure_same("config", [item["config"] for item in summaries])
    dataset_name = ensure_same("dataset name", [item["dataset"]["name"] for item in summaries])
    cases = ensure_same("dataset cases", [item["dataset"]["cases"] for item in summaries])
    runtime = {
        key: ensure_same(key, [item["runtime"][key] for item in summaries])
        for key in summaries[0]["runtime"]
        if key != "timestamp_utc"
    }

    success = [row for row in runs if row.get("status") == "success" and row.get("decode_match")]
    failures = [row for row in runs if row not in success]
    encode_lat = [row["encode_wall_seconds"] for row in success]
    decode_lat = [row["decode_wall_seconds"] for row in success]
    bits_per_token = [row["bits_per_token_encode"] for row in success]
    attempts = [row["attempts_used"] for row in success]
    bhat_total = [row["approximation_audit"]["bhat_tv_total"] for row in success]
    bhat_prefix = [row["approximation_audit"]["bhat_tv_packet_prefix"] for row in success]
    failure_hist = Counter((row.get("failure_class") or "unknown") for row in failures)
    wilson_lo, wilson_hi = wilson_interval(len(success), len(runs))
    language_metrics = {
        language: summarize_language([row for row in runs if row["case"]["language"] == language])
        for language in sorted({row["case"]["language"] for row in runs})
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
                for path, summary in zip(input_dirs, summaries, strict=True)
            ],
            "total_trials": len(runs),
        },
        "artifacts": {
            "runs_jsonl": Path(args.output_runs_jsonl).name if args.output_runs_jsonl else None,
            "step_audit_jsonl": Path(args.output_step_jsonl).name if args.output_step_jsonl else None,
        },
        "metrics": {
            "decode_success_rate": len(success) / len(runs),
            "decode_success_rate_wilson_95": {
                "low": wilson_lo,
                "high": wilson_hi,
            },
            "success_count": len(success),
            "failure_count": len(failures),
            "failure_histogram": dict(sorted(failure_hist.items())),
            "encode_latency_seconds": {
                "median": statistics.median(encode_lat),
                "p90": quantile(encode_lat, 0.9),
                "p99": quantile(encode_lat, 0.99),
                "bootstrap_95": {
                    "low": bootstrap_ci(encode_lat, median_stat)[0],
                    "high": bootstrap_ci(encode_lat, median_stat)[1],
                },
            },
            "decode_latency_seconds": {
                "median": statistics.median(decode_lat),
                "p90": quantile(decode_lat, 0.9),
                "p99": quantile(decode_lat, 0.99),
                "bootstrap_95": {
                    "low": bootstrap_ci(decode_lat, median_stat)[0],
                    "high": bootstrap_ci(decode_lat, median_stat)[1],
                },
            },
            "bits_per_token_encode": {
                "mean": statistics.fmean(bits_per_token),
                "median": statistics.median(bits_per_token),
                "min": min(bits_per_token),
                "max": max(bits_per_token),
                "bootstrap_95": {
                    "low": bootstrap_ci(bits_per_token, mean_stat)[0],
                    "high": bootstrap_ci(bits_per_token, mean_stat)[1],
                },
            },
            "attempts_used": {
                "mean": statistics.fmean(attempts),
                "max": max(attempts),
                "total_attempts": sum(attempts),
                "histogram": {str(key): value for key, value in sorted(Counter(attempts).items())},
            },
            "single_attempt_encode_time_seconds": {
                "mean_derived": sum(encode_lat) / sum(attempts),
                "total_encode_time_seconds": sum(encode_lat),
            },
            "approximation_audit": {
                "bhat_tv_total": {
                    "mean": statistics.fmean(bhat_total),
                    "median": statistics.median(bhat_total),
                    "values": bhat_total,
                },
                "bhat_tv_packet_prefix": {
                    "mean": statistics.fmean(bhat_prefix),
                    "median": statistics.median(bhat_prefix),
                    "values": bhat_prefix,
                },
            },
        },
        "language_metrics": language_metrics,
    }

    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(build_markdown(merged) + "\n", encoding="utf-8")

    if args.output_runs_jsonl:
        output_runs = Path(args.output_runs_jsonl)
        with output_runs.open("w", encoding="utf-8") as handle:
            for row in runs:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    if args.output_step_jsonl:
        output_step = Path(args.output_step_jsonl)
        with output_step.open("w", encoding="utf-8") as handle:
            for row in step_rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
