#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import platform
import statistics
import subprocess
import sys
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ghostext.codec import MessageSegmentDecoder, MessageSegmentEncoder
from ghostext.config import CandidatePolicyConfig, CodecConfig, RuntimeConfig
from ghostext.crypto import build_packet, decrypt_packet
from ghostext.decoder import StegoDecoder
from ghostext.encoder import STALL_PROGRESS_EPSILON_BITS, StegoEncoder
from ghostext.errors import (
    EncodingExhaustedError,
    GhostextError,
    IntegrityError,
    LowEntropyRetryLimitError,
    ModelBackendError,
    PacketError,
    StallDetectedError,
    SynchronizationError,
    UnsafeTokenizationError,
)
from ghostext.llama_cpp_backend import LlamaCppBackendConfig, QwenLlamaCppBackend
from ghostext.model_assets import DEFAULT_MODEL_ID, resolve_default_model_path
from ghostext.pipeline import prepare_quantized_distribution

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_real_backend_baseline import build_cases, quantile, sh, utc_timestamp


METHOD_GHOSTEXT = "ghostext_full"
METHOD_NLS_UTF8 = "nls_style_utf8_single_segment"
METHOD_NLS_PACKET = "nls_style_aead_packet_single_segment"


def bit_stats(data: bytes) -> dict[str, float]:
    total_bits = len(data) * 8
    if total_bits == 0:
        return {
            "bit_count": 0.0,
            "one_fraction": 0.0,
            "bit_entropy": 0.0,
        }
    ones = sum(byte.bit_count() for byte in data)
    p1 = ones / total_bits
    p0 = 1.0 - p1
    entropy = 0.0
    if 0.0 < p1 < 1.0:
        entropy = -(p1 * math.log2(p1) + p0 * math.log2(p0))
    return {
        "bit_count": float(total_bits),
        "one_fraction": p1,
        "bit_entropy": entropy,
    }


def classify_failure(exc: Exception) -> str:
    if isinstance(exc, LowEntropyRetryLimitError):
        return "low_entropy_retry_exhaustion"
    if isinstance(exc, UnsafeTokenizationError):
        return "unstable_tokenization_exhaustion"
    if isinstance(exc, StallDetectedError):
        return "stall_detected"
    if isinstance(exc, EncodingExhaustedError):
        return "token_budget_exhaustion"
    if isinstance(exc, SynchronizationError):
        return "synchronization_mismatch"
    if isinstance(exc, PacketError):
        return "packet_error"
    if isinstance(exc, IntegrityError):
        return "integrity_mismatch"
    if isinstance(exc, ModelBackendError):
        return "backend_error"
    if isinstance(exc, UnicodeDecodeError):
        return "unicode_decode_error"
    if isinstance(exc, GhostextError):
        return "ghostext_error"
    return "unexpected_error"


def build_runtime_info() -> dict[str, Any]:
    return {
        "timestamp_utc": utc_timestamp(),
        "host": platform.node(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "ghostext_version": sh(["python3", "-m", "pip", "show", "ghostext"]),
        "ghostext_git_head": sh(["git", "-C", "/mnt/d/work/Ghostext", "rev-parse", "HEAD"]),
        "paper_git_head": sh(["git", "-C", "/mnt/d/work/Ghostext-paper", "rev-parse", "HEAD"]),
    }


class SingleSegmentCoder:
    def __init__(
        self,
        backend: QwenLlamaCppBackend,
        config: RuntimeConfig,
        *,
        max_tokens: int,
    ) -> None:
        self.backend = backend
        self.config = config
        self.max_tokens = max_tokens

    def encode(self, payload: bytes, *, prompt: str) -> dict[str, Any]:
        started = time.perf_counter()
        generated_token_ids: list[int] = []
        segment = MessageSegmentEncoder(payload)
        stall_tokens = 0
        steps = 0
        while not segment.finished:
            if steps >= self.max_tokens:
                raise EncodingExhaustedError(
                    f"single-segment baseline exceeded token budget {self.max_tokens}"
                )
            quantized = prepare_quantized_distribution(
                self.backend,
                prompt=prompt,
                generated_token_ids=generated_token_ids,
                config=self.config,
            )
            resolved_before = segment.resolved_bits
            if quantized.allows_encoding:
                index, _ = segment.choose(quantized)
                chosen_token_id = quantized.entries[index].token_id
            else:
                chosen_token_id = quantized.top.token_id
            generated_token_ids.append(chosen_token_id)
            resolved_after = segment.resolved_bits
            if resolved_after <= resolved_before + STALL_PROGRESS_EPSILON_BITS:
                stall_tokens += 1
            else:
                stall_tokens = 0
            if stall_tokens >= self.config.codec.stall_patience_tokens:
                raise StallDetectedError(
                    "single-segment baseline made no bit progress for "
                    f"{stall_tokens} consecutive tokens"
                )
            steps += 1
        return {
            "text": self.backend.render(generated_token_ids),
            "token_ids": tuple(generated_token_ids),
            "elapsed_seconds": time.perf_counter() - started,
        }

    def decode(self, text: str, *, prompt: str, payload_len: int) -> dict[str, Any]:
        started = time.perf_counter()
        observed_token_ids = self.backend.tokenize(text, prompt)
        consumed_token_ids: list[int] = []
        decoder = MessageSegmentDecoder(payload_len)
        cursor = 0
        steps = 0
        while not decoder.finished:
            if steps >= self.max_tokens:
                raise SynchronizationError(
                    f"single-segment baseline exceeded token budget {self.max_tokens}"
                )
            if cursor >= len(observed_token_ids):
                raise PacketError("stego text ended before payload resolved")
            quantized = prepare_quantized_distribution(
                self.backend,
                prompt=prompt,
                generated_token_ids=consumed_token_ids,
                config=self.config,
            )
            observed_token_id = observed_token_ids[cursor]
            if quantized.allows_encoding:
                try:
                    index = quantized.find_token_id_index(observed_token_id)
                except KeyError as exc:
                    raise SynchronizationError(
                        f"observed token {observed_token_id} not in candidate set"
                    ) from exc
                decoder.absorb(quantized, index)
            else:
                if observed_token_id != quantized.top.token_id:
                    raise SynchronizationError(
                        "observed token does not match deterministic no-payload choice"
                    )
            consumed_token_ids.append(observed_token_id)
            cursor += 1
            steps += 1
        return {
            "payload": decoder.to_bytes(),
            "observed_token_ids": tuple(observed_token_ids),
            "consumed_tokens": cursor,
            "trailing_tokens": len(observed_token_ids) - cursor,
            "elapsed_seconds": time.perf_counter() - started,
        }


def run_method(
    *,
    method: str,
    case: dict[str, Any],
    passphrase: str,
    prompt: str,
    plaintext: str,
    backend: QwenLlamaCppBackend,
    ghostext_config: RuntimeConfig,
    baseline_config: RuntimeConfig,
    full_encoder: StegoEncoder,
    full_decoder: StegoDecoder,
    single_segment: SingleSegmentCoder,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "method": method,
        "case": case,
        "status": "unknown",
    }
    plaintext_bytes = plaintext.encode("utf-8")
    payload_stats: dict[str, float]
    encode_wall_started = time.perf_counter()
    if method == METHOD_GHOSTEXT:
        enc = full_encoder.encode(plaintext, passphrase=passphrase, prompt=prompt)
        encode_wall_seconds = time.perf_counter() - encode_wall_started
        dec = full_decoder.decode(enc.text, passphrase=passphrase, prompt=prompt)
        decode_wall_seconds = dec.elapsed_seconds
        payload = enc.packet
        payload_stats = bit_stats(payload)
        item.update(
            {
                "status": "success",
                "decode_match": dec.plaintext == plaintext,
                "failure_class": None,
                "payload_kind": "ghostext_aead_packet_two_segment",
                "plaintext_bytes": len(plaintext_bytes),
                "payload_bytes": len(payload),
                "encode_elapsed_seconds": enc.elapsed_seconds,
                "decode_elapsed_seconds": dec.elapsed_seconds,
                "encode_wall_seconds": encode_wall_seconds,
                "decode_wall_seconds": decode_wall_seconds,
                "attempts_used": enc.attempts_used,
                "total_tokens": enc.total_tokens,
                "payload_tokens": enc.packet_tokens,
                "tail_tokens": enc.tail_tokens,
                "decode_consumed_tokens": dec.consumed_tokens,
                "decode_trailing_tokens": dec.trailing_tokens,
                "plaintext_bits_per_token_encode": (len(plaintext_bytes) * 8) / enc.total_tokens,
                "payload_bits_per_token_encode": (len(payload) * 8) / enc.total_tokens,
                "plaintext_bits_per_token_decode": (len(plaintext_bytes) * 8) / dec.consumed_tokens,
                "payload_bits_per_token_decode": (len(payload) * 8) / dec.consumed_tokens,
                "encode_tokens_per_second": enc.tokens_per_second,
                "decode_tokens_per_second": dec.tokens_per_second,
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
                "payload_bit_one_fraction": payload_stats["one_fraction"],
                "payload_bit_entropy": payload_stats["bit_entropy"],
            }
        )
        if not item["decode_match"]:
            item["status"] = "failure"
            item["failure_class"] = "plaintext_mismatch"
        return item

    if method == METHOD_NLS_UTF8:
        payload = plaintext_bytes
        payload_kind = "raw_plaintext_utf8"
        config_fingerprint_hex = None
    elif method == METHOD_NLS_PACKET:
        config_fingerprint = ghostext_config.config_fingerprint(
            backend_metadata=backend.metadata.as_dict(),
            prompt=prompt,
        )
        payload = build_packet(
            plaintext_bytes,
            passphrase=passphrase,
            config_fingerprint=config_fingerprint,
            crypto_config=ghostext_config.crypto,
        )
        payload_kind = "ghostext_aead_packet_single_segment"
        config_fingerprint_hex = f"{config_fingerprint:016x}"
    else:
        raise ValueError(f"unknown method: {method}")

    enc = single_segment.encode(payload, prompt=prompt)
    encode_wall_seconds = time.perf_counter() - encode_wall_started
    dec = single_segment.decode(enc["text"], prompt=prompt, payload_len=len(payload))
    decode_wall_seconds = dec["elapsed_seconds"]
    if method == METHOD_NLS_UTF8:
        recovered_plaintext = dec["payload"].decode("utf-8")
    else:
        recovered_bytes = decrypt_packet(
            dec["payload"],
            passphrase=passphrase,
            expected_config_fingerprint=int(config_fingerprint_hex, 16),
            crypto_config=ghostext_config.crypto,
        )
        recovered_plaintext = recovered_bytes.decode("utf-8")
    payload_stats = bit_stats(payload)
    total_tokens = len(enc["token_ids"])
    consumed_tokens = int(dec["consumed_tokens"])
    item.update(
        {
            "status": "success",
            "decode_match": recovered_plaintext == plaintext,
            "failure_class": None,
            "payload_kind": payload_kind,
            "plaintext_bytes": len(plaintext_bytes),
            "payload_bytes": len(payload),
            "encode_elapsed_seconds": enc["elapsed_seconds"],
            "decode_elapsed_seconds": dec["elapsed_seconds"],
            "encode_wall_seconds": encode_wall_seconds,
            "decode_wall_seconds": decode_wall_seconds,
            "attempts_used": 1,
            "total_tokens": total_tokens,
            "payload_tokens": total_tokens,
            "tail_tokens": 0,
            "decode_consumed_tokens": consumed_tokens,
            "decode_trailing_tokens": int(dec["trailing_tokens"]),
            "plaintext_bits_per_token_encode": (len(plaintext_bytes) * 8) / total_tokens,
            "payload_bits_per_token_encode": (len(payload) * 8) / total_tokens,
            "plaintext_bits_per_token_decode": (len(plaintext_bytes) * 8) / consumed_tokens,
            "payload_bits_per_token_decode": (len(payload) * 8) / consumed_tokens,
            "encode_tokens_per_second": total_tokens / enc["elapsed_seconds"] if enc["elapsed_seconds"] > 0 else 0.0,
            "decode_tokens_per_second": consumed_tokens / dec["elapsed_seconds"] if dec["elapsed_seconds"] > 0 else 0.0,
            "segments": [
                {
                    "name": "single_segment",
                    "tokens_used": total_tokens,
                    "encoding_steps": total_tokens,
                    "embedded_bits": len(payload) * 8,
                }
            ],
            "config_fingerprint_hex": config_fingerprint_hex,
            "payload_bit_one_fraction": payload_stats["one_fraction"],
            "payload_bit_entropy": payload_stats["bit_entropy"],
        }
    )
    if not item["decode_match"]:
        item["status"] = "failure"
        item["failure_class"] = "plaintext_mismatch"
    return item


def summarize_runs(
    *,
    args: argparse.Namespace,
    runs: list[dict[str, Any]],
    backend: QwenLlamaCppBackend,
) -> dict[str, Any]:
    methods = sorted({run["method"] for run in runs})
    method_summaries: dict[str, Any] = {}
    for method in methods:
        subset = [run for run in runs if run["method"] == method]
        success = [run for run in subset if run.get("status") == "success" and run.get("decode_match")]
        failures = [run for run in subset if run not in success]
        encode_lat = [run["encode_wall_seconds"] for run in success]
        decode_lat = [run["decode_wall_seconds"] for run in success]
        plaintext_bpt = [run["plaintext_bits_per_token_encode"] for run in success]
        payload_bpt = [run["payload_bits_per_token_encode"] for run in success]
        payload_entropy = [run["payload_bit_entropy"] for run in success]
        payload_one_fraction = [run["payload_bit_one_fraction"] for run in success]
        attempts = [run["attempts_used"] for run in success]
        failure_hist = dict(Counter(run.get("failure_class") or "unknown" for run in failures))
        method_summaries[method] = {
            "trials": len(subset),
            "success_count": len(success),
            "failure_count": len(failures),
            "decode_success_rate": len(success) / len(subset) if subset else 0.0,
            "failure_histogram": failure_hist,
            "encode_latency_seconds": {
                "median": statistics.median(encode_lat) if encode_lat else 0.0,
                "p90": quantile(encode_lat, 0.9),
            },
            "decode_latency_seconds": {
                "median": statistics.median(decode_lat) if decode_lat else 0.0,
                "p90": quantile(decode_lat, 0.9),
            },
            "plaintext_bits_per_token_encode": {
                "mean": statistics.fmean(plaintext_bpt) if plaintext_bpt else 0.0,
                "median": statistics.median(plaintext_bpt) if plaintext_bpt else 0.0,
            },
            "payload_bits_per_token_encode": {
                "mean": statistics.fmean(payload_bpt) if payload_bpt else 0.0,
                "median": statistics.median(payload_bpt) if payload_bpt else 0.0,
            },
            "payload_bit_entropy": {
                "mean": statistics.fmean(payload_entropy) if payload_entropy else 0.0,
                "median": statistics.median(payload_entropy) if payload_entropy else 0.0,
            },
            "payload_bit_one_fraction": {
                "mean": statistics.fmean(payload_one_fraction) if payload_one_fraction else 0.0,
                "median": statistics.median(payload_one_fraction) if payload_one_fraction else 0.0,
            },
            "attempts_used": {
                "mean": statistics.fmean(attempts) if attempts else 0.0,
                "max": max(attempts) if attempts else 0,
            },
        }
    return {
        "generated_at_utc": utc_timestamp(),
        "runtime": build_runtime_info(),
        "model": {
            "resolved_model_path": backend.config.model_path,
            "backend_metadata": backend.metadata.as_dict(),
            "ctx_size": backend.config.n_ctx,
            "batch_size": backend.config.n_batch,
            "threads": backend.config.n_threads,
        },
        "dataset": {
            "name": "real-backend aligned baseline cases",
            "cases": [asdict(case) for case in build_cases()],
            "methods": methods,
        },
        "config": {
            "seed": args.seed,
            "passphrase_policy": "fixed local demo passphrase for aligned baseline comparison",
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
                "single_segment_token_budget": args.single_segment_token_budget,
            },
        },
        "method_summaries": method_summaries,
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run aligned Ghostext vs NLS-style baselines on the Qwen backend")
    p.add_argument("--out-dir", default="/mnt/d/work/Ghostext-paper/results/aligned-qwen-baselines")
    p.add_argument(
        "--methods",
        nargs="+",
        default=[METHOD_GHOSTEXT, METHOD_NLS_UTF8, METHOD_NLS_PACKET],
        choices=[METHOD_GHOSTEXT, METHOD_NLS_UTF8, METHOD_NLS_PACKET],
    )
    p.add_argument("--model-path", default=None)
    p.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    p.add_argument("--threads", type=int, default=4)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--passphrase", default="paper-baseline-pass")
    p.add_argument("--ctx-size", type=int, default=4096)
    p.add_argument("--batch-size", type=int, default=128)
    p.add_argument("--top-p", type=float, default=0.995)
    p.add_argument("--max-candidates", type=int, default=64)
    p.add_argument("--min-entropy-bits", type=float, default=0.0)
    p.add_argument("--total-frequency", type=int, default=4096)
    p.add_argument("--header-token-budget", type=int, default=2048)
    p.add_argument("--body-token-budget", type=int, default=4096)
    p.add_argument("--single-segment-token-budget", type=int, default=6144)
    p.add_argument("--natural-tail-max-tokens", type=int, default=64)
    p.add_argument("--stall-patience-tokens", type=int, default=256)
    p.add_argument("--low-entropy-window-tokens", type=int, default=32)
    p.add_argument("--low-entropy-threshold-bits", type=float, default=0.1)
    p.add_argument("--max-encode-attempts", type=int, default=10)
    return p


def main() -> int:
    args = build_parser().parse_args()
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
    ghostext_config = RuntimeConfig(
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
    baseline_config = RuntimeConfig(
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
            natural_tail_max_tokens=0,
            stall_patience_tokens=args.stall_patience_tokens,
            low_entropy_window_tokens=args.low_entropy_window_tokens,
            low_entropy_threshold_bits=args.low_entropy_threshold_bits,
            max_encode_attempts=1,
        ),
    )
    full_encoder = StegoEncoder(backend, ghostext_config)
    full_decoder = StegoDecoder(backend, ghostext_config)
    single_segment = SingleSegmentCoder(
        backend,
        baseline_config,
        max_tokens=args.single_segment_token_budget,
    )

    runs: list[dict[str, Any]] = []
    for case in build_cases():
        for method in args.methods:
            item = {
                "case": asdict(case),
                "method": method,
            }
            try:
                run_item = run_method(
                    method=method,
                    case=asdict(case),
                    passphrase=args.passphrase,
                    prompt=case.prompt,
                    plaintext=case.message,
                    backend=backend,
                    ghostext_config=ghostext_config,
                    baseline_config=baseline_config,
                    full_encoder=full_encoder,
                    full_decoder=full_decoder,
                    single_segment=single_segment,
                )
                item.update(run_item)
            except Exception as exc:  # noqa: BLE001
                item.update(
                    {
                        "status": "failure",
                        "decode_match": False,
                        "failure_class": classify_failure(exc),
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            runs.append(item)
            print(
                json.dumps(
                    {
                        "method": item["method"],
                        "case_id": item["case"]["case_id"],
                        "status": item["status"],
                        "failure_class": item.get("failure_class"),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    runs_path = out_dir / "aligned_baseline_runs.jsonl"
    summary_path = out_dir / "aligned_baseline_summary.json"
    with runs_path.open("w", encoding="utf-8") as f:
        for run in runs:
            f.write(json.dumps(run, ensure_ascii=False) + "\n")

    summary = summarize_runs(args=args, runs=runs, backend=backend)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "runs_file": str(runs_path),
                "summary_file": str(summary_path),
                "methods": args.methods,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
