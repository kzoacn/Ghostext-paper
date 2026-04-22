#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_summary(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def format_metric(method: dict, key: str) -> str:
    metric = method[key]
    return f"{metric['mean']:.3f} (median {metric['median']:.3f})"


def method_label(method: str) -> str:
    return {
        "ghostext_full": "Ghostext full",
        "nls_style_utf8_single_segment": "NLS-style UTF-8",
        "nls_style_aead_packet_single_segment": "NLS-style AEAD packet",
    }.get(method, method)


def render_markdown(summary: dict) -> str:
    lines: list[str] = []
    lines.append("# Aligned Qwen Baseline Comparison")
    lines.append("")
    lines.append(
        f"Generated at `{summary['generated_at_utc']}` with backend "
        f"`{summary['model']['backend_metadata']['model_id']}` "
        f"(GGUF name `{summary['model']['upstream_provenance']['canonical_model_label']}`)."
    )
    lines.append("")
    lines.append("| Method | n | Success | Encode median (s) | Decode median (s) | Attempts | Plaintext bits/token | Payload bits/token | Payload bit entropy | One fraction |")
    lines.append("|---|---:|---:|---:|---:|---|---:|---:|---:|---:|")
    for method in summary["dataset"]["methods"]:
        item = summary["method_summaries"][method]
        lines.append(
            "| "
            + " | ".join(
                [
                    method_label(method),
                    str(item["trials"]),
                    f"{item['success_count']}/{item['trials']}",
                    f"{item['encode_latency_seconds']['median']:.2f}",
                    f"{item['decode_latency_seconds']['median']:.2f}",
                    f"{item['attempts_used']['mean']:.1f} / {item['attempts_used']['max']}",
                    f"{item['plaintext_bits_per_token_encode']['mean']:.3f}",
                    f"{item['payload_bits_per_token_encode']['mean']:.3f}",
                    f"{item['payload_bit_entropy']['mean']:.3f}",
                    f"{item['payload_bit_one_fraction']['mean']:.3f}",
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("## Failure Histograms")
    lines.append("")
    for method in summary["dataset"]["methods"]:
        item = summary["method_summaries"][method]
        lines.append(f"- `{method_label(method)}`: `{json.dumps(item['failure_histogram'], ensure_ascii=False)}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="Render a markdown summary for aligned baseline comparison")
    p.add_argument("--input-json", required=True)
    p.add_argument("--output-md", required=True)
    args = p.parse_args()

    summary = load_summary(Path(args.input_json))
    markdown = render_markdown(summary)
    Path(args.output_md).write_text(markdown, encoding="utf-8")
    print(json.dumps({"output_md": args.output_md}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
