#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import statistics
import time
from pathlib import Path
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from artifact_utils import (
    FIXED_DEMO_PASSPHRASE_POLICY,
    FULL_COVER_TEXT_POLICY,
    build_runtime_info,
    extract_model_provenance,
    quantile,
    sha256_hex,
    utc_timestamp,
)
from ghostext.candidate_policy import audit_candidate_selection
from ghostext.config import CandidatePolicyConfig, CodecConfig, RuntimeConfig
from ghostext.decoder import StegoDecoder
from ghostext.encoder import StegoEncoder
from ghostext.errors import (
    EncodingExhaustedError,
    GhostextError,
    IntegrityError,
    LowEntropyRetryLimitError,
    ModelBackendError,
    SynchronizationError,
    UnsafeTokenizationError,
)
from ghostext.llama_cpp_backend import LlamaCppBackendConfig, QwenLlamaCppBackend
from ghostext.model_assets import DEFAULT_MODEL_ID, resolve_default_model_path
from ghostext.quantization import quantize_candidates


@dataclass
class Case:
    case_id: str
    language: str
    prompt_family: str
    prompt_regime: str
    prompt: str
    message: str


def build_cases() -> list[Case]:
    en_prompt = "Write a short, natural paragraph about a quiet evening walk in the city."
    zh_prompt = "请写一段自然、连贯、简短的中文段落，描写傍晚在城市里散步时看到的街景。"
    return [
        Case(
            case_id="en_short_01",
            language="en",
            prompt_family="narrative-walk",
            prompt_regime="template-known",
            prompt=en_prompt,
            message="Meet at 7 PM by the old bridge.",
        ),
        Case(
            case_id="en_short_02",
            language="en",
            prompt_family="narrative-walk",
            prompt_regime="template-known",
            prompt=en_prompt,
            message="Bring the blue notebook and wait near the station entrance.",
        ),
        Case(
            case_id="en_mid_01",
            language="en",
            prompt_family="narrative-walk",
            prompt_regime="template-known",
            prompt=en_prompt,
            message=(
                "The package has been moved to locker 14 on the east side. "
                "Use the same route as last time and send confirmation afterward."
            ),
        ),
        Case(
            case_id="zh_short_01",
            language="zh",
            prompt_family="narrative-walk-zh",
            prompt_regime="template-known",
            prompt=zh_prompt,
            message="今晚七点在河边老地方见。",
        ),
        Case(
            case_id="zh_short_02",
            language="zh",
            prompt_family="narrative-walk-zh",
            prompt_regime="template-known",
            prompt=zh_prompt,
            message="带上那本蓝色笔记本，在地铁口等我。",
        ),
        Case(
            case_id="zh_mid_01",
            language="zh",
            prompt_family="narrative-walk-zh",
            prompt_regime="template-known",
            prompt=zh_prompt,
            message="包裹已经转移到东侧十四号柜，请按原路线行动并在结束后回执。",
        ),
    ]


def classify_failure(exc: Exception) -> str:
    if isinstance(exc, LowEntropyRetryLimitError):
        return "low_entropy_retry_exhaustion"
    if isinstance(exc, UnsafeTokenizationError):
        return "unstable_tokenization_exhaustion"
    if isinstance(exc, EncodingExhaustedError):
        return "token_budget_exhaustion"
    if isinstance(exc, SynchronizationError):
        return "synchronization_mismatch"
    if isinstance(exc, IntegrityError):
        return "integrity_mismatch"
    if isinstance(exc, ModelBackendError):
        return "backend_error"
    if isinstance(exc, GhostextError):
        return "ghostext_error"
    return "unexpected_error"


def segment_labels(segment_stats: list[dict[str, Any]] | tuple[Any, ...], total_tokens: int) -> list[str]:
    labels: list[str] = []
    for segment in segment_stats:
        labels.extend([segment.name] * int(segment.tokens_used))
    if len(labels) < total_tokens:
        labels.extend(["tail"] * (total_tokens - len(labels)))
    return labels[:total_tokens]


def build_step_audit(
    *,
    backend: QwenLlamaCppBackend,
    config: RuntimeConfig,
    case: Case,
    run_index: int,
    token_ids: tuple[int, ...],
    packet_tokens: int,
    segment_stats: tuple[Any, ...],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    generated_token_ids: list[int] = []
    phase_labels = segment_labels(segment_stats, len(token_ids))
    for step_index, chosen_token_id in enumerate(token_ids):
        raw_distribution = backend.distribution(case.prompt, generated_token_ids, config.seed)
        audit = audit_candidate_selection(
            raw_distribution,
            config.candidate_policy,
            backend=backend,
            prompt=case.prompt,
            generated_token_ids=generated_token_ids,
        )
        prequantized = quantize_candidates(audit.prefilter_selection, config.codec.total_frequency)
        stable_ids = {entry.token_id for entry in audit.stable_selection.entries}
        beta_t = (
            sum(entry.frequency for entry in prequantized.entries if entry.token_id not in stable_ids)
            / config.codec.total_frequency
        )
        quantization_tv_t = len(audit.prefilter_selection.entries) / (2.0 * config.codec.total_frequency)
        bhat_tv_t = audit.truncated_tail_mass + quantization_tv_t + beta_t
        rows.append(
            {
                "run_index": run_index,
                "case_id": case.case_id,
                "language": case.language,
                "step_index": step_index,
                "phase": phase_labels[step_index],
                "is_packet_prefix": step_index < packet_tokens,
                "alpha_t": audit.truncated_tail_mass,
                "candidate_count_prefilter": len(audit.prefilter_selection.entries),
                "candidate_count_stable": len(audit.stable_selection.entries),
                "beta_t": beta_t,
                "quantization_tv_bound_t": quantization_tv_t,
                "bhat_tv_t": bhat_tv_t,
                "entropy_bits_prefilter": audit.prefilter_selection.entropy_bits,
                "entropy_bits_stable": audit.stable_selection.entropy_bits,
                "allows_encoding_prefilter": audit.prefilter_selection.allows_encoding,
                "allows_encoding_stable": audit.stable_selection.allows_encoding,
                "chosen_token_id": chosen_token_id,
                "chosen_token_text": backend.token_text(chosen_token_id),
                "chosen_token_stable": chosen_token_id in stable_ids,
            }
        )
        generated_token_ids.append(chosen_token_id)

    packet_rows = [row for row in rows if row["is_packet_prefix"]]
    total_rows = rows if rows else packet_rows
    summary = {
        "full_text_steps": len(rows),
        "packet_prefix_steps": len(packet_rows),
        "alpha_sum_total": sum(row["alpha_t"] for row in rows),
        "beta_sum_total": sum(row["beta_t"] for row in rows),
        "quantization_tv_sum_total": sum(row["quantization_tv_bound_t"] for row in rows),
        "bhat_tv_total": sum(row["bhat_tv_t"] for row in rows),
        "alpha_sum_packet_prefix": sum(row["alpha_t"] for row in packet_rows),
        "beta_sum_packet_prefix": sum(row["beta_t"] for row in packet_rows),
        "quantization_tv_sum_packet_prefix": sum(
            row["quantization_tv_bound_t"] for row in packet_rows
        ),
        "bhat_tv_packet_prefix": sum(row["bhat_tv_t"] for row in packet_rows),
        "alpha_t_max": max((row["alpha_t"] for row in total_rows), default=0.0),
        "beta_t_max": max((row["beta_t"] for row in total_rows), default=0.0),
        "bhat_tv_t_max": max((row["bhat_tv_t"] for row in total_rows), default=0.0),
    }
    return rows, summary


def build_failure_histogram(rows: list[dict[str, Any]]) -> dict[str, int]:
    histogram: dict[str, int] = {}
    for item in rows:
        key = item.get("failure_class") or "unknown"
        histogram[key] = histogram.get(key, 0) + 1
    return histogram


def run(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    model = resolve_default_model_path(args.model_path)
    backend = QwenLlamaCppBackend(
        LlamaCppBackendConfig(
            model_path=str(model.path),
            model_id=args.model_id or DEFAULT_MODEL_ID,
            n_ctx=args.ctx_size,
            n_batch=args.batch_size,
            n_threads=args.threads,
            seed=args.seed,
        )
    )

    config = RuntimeConfig(
        seed=args.seed,
        candidate_policy=CandidatePolicyConfig(
            top_p=args.top_p,
            max_candidates=args.max_candidates,
            min_entropy_bits=args.min_entropy_bits,
            enforce_retokenization_stability=True,
        ),
        codec=CodecConfig(
            total_frequency=args.total_frequency,
            max_header_tokens=args.header_token_budget,
            max_body_tokens=args.body_token_budget,
            natural_tail_max_tokens=args.natural_tail_max_tokens,
            stall_patience_tokens=args.stall_patience_tokens,
            low_entropy_window_tokens=args.low_entropy_window_tokens,
            low_entropy_threshold_bits=args.low_entropy_threshold_bits,
            max_encode_attempts=args.max_encode_attempts,
        ),
    )

    encoder = StegoEncoder(backend, config)
    decoder = StegoDecoder(backend, config)

    runs: list[dict[str, Any]] = []
    step_rows: list[dict[str, Any]] = []
    cases = build_cases()

    for r in range(args.repeats):
        for case in cases:
            item: dict[str, Any] = {
                "run_index": r,
                "case": asdict(case),
                "status": "unknown",
            }
            t0 = time.perf_counter()
            try:
                enc = encoder.encode(
                    case.message,
                    passphrase=args.passphrase,
                    prompt=case.prompt,
                )
                t1 = time.perf_counter()
                dec = decoder.decode(
                    enc.text,
                    passphrase=args.passphrase,
                    prompt=case.prompt,
                )
                t2 = time.perf_counter()
                audit_rows, audit_summary = build_step_audit(
                    backend=backend,
                    config=config,
                    case=case,
                    run_index=r,
                    token_ids=enc.token_ids,
                    packet_tokens=enc.packet_tokens,
                    segment_stats=enc.segment_stats,
                )
                step_rows.extend(audit_rows)

                item.update(
                    {
                        "status": "success",
                        "decode_match": dec.plaintext == case.message,
                        "failure_class": None,
                        "plaintext_bytes": len(case.message.encode("utf-8")),
                        "packet_len": len(enc.packet),
                        "encode_elapsed_seconds": enc.elapsed_seconds,
                        "decode_elapsed_seconds": dec.elapsed_seconds,
                        "e2e_elapsed_seconds": t2 - t0,
                        "encode_wall_seconds": t1 - t0,
                        "decode_wall_seconds": t2 - t1,
                        "attempts_used": enc.attempts_used,
                        "total_tokens": enc.total_tokens,
                        "packet_tokens": enc.packet_tokens,
                        "tail_tokens": enc.tail_tokens,
                        "decode_consumed_tokens": dec.consumed_tokens,
                        "decode_trailing_tokens": dec.trailing_tokens,
                        "bits_per_token_encode": enc.bits_per_token,
                        "bits_per_token_decode": dec.bits_per_token,
                        "encode_tokens_per_second": enc.tokens_per_second,
                        "decode_tokens_per_second": dec.tokens_per_second,
                        "cover_text": enc.text,
                        "cover_text_sha256": sha256_hex(enc.text),
                        "packet_sha256": sha256_hex(enc.packet),
                        "segments": [
                            {
                                "name": s.name,
                                "tokens_used": s.tokens_used,
                                "encoding_steps": s.encoding_steps,
                                "embedded_bits": s.embedded_bits,
                            }
                            for s in enc.segment_stats
                        ],
                        "config_fingerprint_hex": f"{enc.config_fingerprint:016x}",
                        "approximation_audit": audit_summary,
                    }
                )
                if not item["decode_match"]:
                    item["status"] = "failure"
                    item["failure_class"] = "plaintext_mismatch"
            except Exception as exc:  # noqa: BLE001
                item.update(
                    {
                        "status": "failure",
                        "decode_match": False,
                        "failure_class": classify_failure(exc),
                        "error": f"{type(exc).__name__}: {exc}",
                        "e2e_elapsed_seconds": time.perf_counter() - t0,
                    }
                )
            runs.append(item)

    success = [item for item in runs if item.get("status") == "success" and item.get("decode_match")]
    failures = [item for item in runs if item not in success]
    encode_lat = [item["encode_wall_seconds"] for item in success]
    decode_lat = [item["decode_wall_seconds"] for item in success]
    bits_per_token = [item["bits_per_token_encode"] for item in success]
    tokens_per_second = [item["encode_tokens_per_second"] for item in success]
    attempts = [item["attempts_used"] for item in success]
    audit_totals = [item["approximation_audit"]["bhat_tv_total"] for item in success]
    audit_prefix = [item["approximation_audit"]["bhat_tv_packet_prefix"] for item in success]

    summary = {
        "generated_at_utc": utc_timestamp(),
        "runtime": build_runtime_info(),
        "model": {
            **extract_model_provenance(
                model_path=model.path,
                resolved_model_source=model.source,
                backend_metadata=backend.metadata.as_dict(),
                llama_metadata=getattr(getattr(backend, "_llm", None), "metadata", {}),
            ),
            "ctx_size": args.ctx_size,
            "batch_size": args.batch_size,
            "threads": args.threads,
        },
        "config": {
            "seed": args.seed,
            "passphrase_policy": FIXED_DEMO_PASSPHRASE_POLICY,
            "cover_text_policy": FULL_COVER_TEXT_POLICY,
            "candidate": {
                "top_p": args.top_p,
                "max_candidates": args.max_candidates,
                "min_entropy_bits": args.min_entropy_bits,
                "retokenization_stability": True,
            },
            "codec": {
                "total_frequency": args.total_frequency,
                "header_token_budget": args.header_token_budget,
                "body_token_budget": args.body_token_budget,
                "natural_tail_max_tokens": args.natural_tail_max_tokens,
                "stall_patience_tokens": args.stall_patience_tokens,
                "low_entropy_window_tokens": args.low_entropy_window_tokens,
                "low_entropy_threshold_bits": args.low_entropy_threshold_bits,
                "max_encode_attempts": args.max_encode_attempts,
            },
        },
        "dataset": {
            "name": "built-in fixed prompts/messages",
            "cases": [asdict(case) for case in cases],
            "repeats": args.repeats,
            "total_trials": len(runs),
        },
        "artifacts": {
            "runs_jsonl": "real_backend_runs.jsonl",
            "step_audit_jsonl": "real_backend_step_audit.jsonl",
        },
        "metrics": {
            "decode_success_rate": len(success) / len(runs) if runs else 0.0,
            "success_count": len(success),
            "failure_count": len(failures),
            "failure_histogram": build_failure_histogram(failures),
            "encode_latency_seconds": {
                "median": statistics.median(encode_lat) if encode_lat else 0.0,
                "p90": quantile(encode_lat, 0.9),
                "p99": quantile(encode_lat, 0.99),
            },
            "decode_latency_seconds": {
                "median": statistics.median(decode_lat) if decode_lat else 0.0,
                "p90": quantile(decode_lat, 0.9),
                "p99": quantile(decode_lat, 0.99),
            },
            "bits_per_token_encode": {
                "mean": statistics.fmean(bits_per_token) if bits_per_token else 0.0,
                "median": statistics.median(bits_per_token) if bits_per_token else 0.0,
                "min": min(bits_per_token) if bits_per_token else 0.0,
                "max": max(bits_per_token) if bits_per_token else 0.0,
            },
            "encode_tokens_per_second": {
                "mean": statistics.fmean(tokens_per_second) if tokens_per_second else 0.0,
                "median": statistics.median(tokens_per_second) if tokens_per_second else 0.0,
            },
            "attempts_used": {
                "mean": statistics.fmean(attempts) if attempts else 0.0,
                "max": max(attempts) if attempts else 0,
                "total_attempts": sum(attempts),
            },
            "approximation_audit": {
                "bhat_tv_total_mean": statistics.fmean(audit_totals) if audit_totals else 0.0,
                "bhat_tv_total_median": statistics.median(audit_totals) if audit_totals else 0.0,
                "bhat_tv_packet_prefix_mean": statistics.fmean(audit_prefix) if audit_prefix else 0.0,
                "bhat_tv_packet_prefix_median": statistics.median(audit_prefix) if audit_prefix else 0.0,
            },
        },
    }

    runs_path = out_dir / "real_backend_runs.jsonl"
    step_audit_path = out_dir / "real_backend_step_audit.jsonl"
    summary_path = out_dir / "real_backend_summary.json"

    with runs_path.open("w", encoding="utf-8") as handle:
        for row in runs:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with step_audit_path.open("w", encoding="utf-8") as handle:
        for row in step_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "runs_file": str(runs_path),
                "step_audit_file": str(step_audit_path),
                "summary_file": str(summary_path),
                "total_trials": len(runs),
                "decode_success_rate": summary["metrics"]["decode_success_rate"],
                "failure_histogram": summary["metrics"]["failure_histogram"],
                "encode_latency_median": summary["metrics"]["encode_latency_seconds"]["median"],
                "decode_latency_median": summary["metrics"]["decode_latency_seconds"]["median"],
                "bpt_mean": summary["metrics"]["bits_per_token_encode"]["mean"],
                "bhat_tv_total_mean": summary["metrics"]["approximation_audit"]["bhat_tv_total_mean"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Ghostext real-backend recoverability/runtime baseline")
    parser.add_argument("--out-dir", default="/mnt/d/work/Ghostext-paper/results/real-backend-baseline")
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--passphrase", default="paper-baseline-pass")
    parser.add_argument("--ctx-size", type=int, default=4096)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--top-p", type=float, default=0.995)
    parser.add_argument("--max-candidates", type=int, default=64)
    parser.add_argument("--min-entropy-bits", type=float, default=0.0)
    parser.add_argument("--total-frequency", type=int, default=4096)
    parser.add_argument("--header-token-budget", type=int, default=2048)
    parser.add_argument("--body-token-budget", type=int, default=4096)
    parser.add_argument("--natural-tail-max-tokens", type=int, default=64)
    parser.add_argument("--stall-patience-tokens", type=int, default=256)
    parser.add_argument("--low-entropy-window-tokens", type=int, default=32)
    parser.add_argument("--low-entropy-threshold-bits", type=float, default=0.1)
    parser.add_argument("--max-encode-attempts", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=2)
    return parser


if __name__ == "__main__":
    raise SystemExit(run(build_parser().parse_args()))
