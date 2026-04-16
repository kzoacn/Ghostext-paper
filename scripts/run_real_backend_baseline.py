#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

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


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sh(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    except Exception:
        return "unknown"
    return out.strip() or "unknown"


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


def build_runtime_info() -> dict[str, Any]:
    return {
        "timestamp_utc": utc_timestamp(),
        "host": platform.node(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "ghostext_version": sh(["python3", "-m", "pip", "show", "ghostext"]),
        "git_head": sh(["git", "-C", "/mnt/d/work/Ghostext", "rev-parse", "HEAD"]),
    }


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

    success = [x for x in runs if x.get("status") == "success" and x.get("decode_match")]
    fail = [x for x in runs if x not in success]

    encode_lat = [x["encode_wall_seconds"] for x in success]
    decode_lat = [x["decode_wall_seconds"] for x in success]
    bpt = [x["bits_per_token_encode"] for x in success]
    tps = [x["encode_tokens_per_second"] for x in success]

    failure_hist: dict[str, int] = {}
    for x in fail:
        key = x.get("failure_class") or "unknown"
        failure_hist[key] = failure_hist.get(key, 0) + 1

    summary = {
        "generated_at_utc": utc_timestamp(),
        "runtime": build_runtime_info(),
        "model": {
            "resolved_model_path": str(model.path),
            "resolved_model_source": model.source,
            "backend_metadata": backend.metadata.as_dict(),
            "ctx_size": args.ctx_size,
            "batch_size": args.batch_size,
            "threads": args.threads,
        },
        "config": {
            "seed": args.seed,
            "passphrase_policy": "fixed local demo passphrase for reproducible baseline",
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
            "cases": [asdict(c) for c in cases],
            "repeats": args.repeats,
            "total_trials": len(runs),
        },
        "metrics": {
            "decode_success_rate": len(success) / len(runs) if runs else 0.0,
            "success_count": len(success),
            "failure_count": len(fail),
            "failure_histogram": failure_hist,
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
                "mean": statistics.fmean(bpt) if bpt else 0.0,
                "median": statistics.median(bpt) if bpt else 0.0,
                "min": min(bpt) if bpt else 0.0,
                "max": max(bpt) if bpt else 0.0,
            },
            "encode_tokens_per_second": {
                "mean": statistics.fmean(tps) if tps else 0.0,
                "median": statistics.median(tps) if tps else 0.0,
            },
        },
    }

    runs_path = out_dir / "real_backend_runs.jsonl"
    summary_path = out_dir / "real_backend_summary.json"
    with runs_path.open("w", encoding="utf-8") as f:
        for r in runs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "runs_file": str(runs_path),
        "summary_file": str(summary_path),
        "total_trials": len(runs),
        "decode_success_rate": summary["metrics"]["decode_success_rate"],
        "failure_histogram": failure_hist,
        "encode_latency_median": summary["metrics"]["encode_latency_seconds"]["median"],
        "decode_latency_median": summary["metrics"]["decode_latency_seconds"]["median"],
        "bpt_mean": summary["metrics"]["bits_per_token_encode"]["mean"],
    }, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run Ghostext real-backend recoverability/runtime baseline")
    p.add_argument("--out-dir", default="/mnt/d/work/Ghostext-paper/results/real-backend-baseline")
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
    p.add_argument("--natural-tail-max-tokens", type=int, default=64)
    p.add_argument("--stall-patience-tokens", type=int, default=256)
    p.add_argument("--low-entropy-window-tokens", type=int, default=32)
    p.add_argument("--low-entropy-threshold-bits", type=float, default=0.1)
    p.add_argument("--max-encode-attempts", type=int, default=10)
    p.add_argument("--repeats", type=int, default=2)
    return p


if __name__ == "__main__":
    raise SystemExit(run(build_parser().parse_args()))
