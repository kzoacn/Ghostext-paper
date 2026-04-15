#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import statistics
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GHOSTEXT_SRC = (ROOT / "../Ghostext/src").resolve()
if str(GHOSTEXT_SRC) not in sys.path:
    sys.path.insert(0, str(GHOSTEXT_SRC))

from ghostext.config import CandidatePolicyConfig, CodecConfig, RuntimeConfig
from ghostext.decoder import StegoDecoder
from ghostext.encoder import StegoEncoder
from ghostext.errors import EncodingExhaustedError, GhostextError
from ghostext.llama_cpp_backend import LlamaCppBackendConfig, QwenLlamaCppBackend
from ghostext.model_assets import DEFAULT_BATCH_SIZE, DEFAULT_CTX_SIZE, DEFAULT_SEED


MODEL_PATH_CANDIDATES = [
    os.environ.get("GHOSTEXT_LLAMA_MODEL_PATH"),
    os.environ.get("GHOSTEXT_MODEL_PATH"),
    str(Path.home() / ".cache/ghostext/models/qwen35-2b-q4ks/Qwen_Qwen3.5-2B-Q4_K_S.gguf"),
]


def _resolve_model_path() -> str:
    for cand in MODEL_PATH_CANDIDATES:
        if not cand:
            continue
        p = Path(cand).expanduser().resolve()
        if p.exists():
            return str(p)
    raise FileNotFoundError("No usable GGUF model path found for real backend eval")


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": float(statistics.fmean(values)),
        "min": float(min(values)),
        "max": float(max(values)),
    }


def _build_backend(seed: int) -> QwenLlamaCppBackend:
    model_path = _resolve_model_path()
    # Keep evaluation deterministic/stable by default; callers can override.
    threads = int(os.environ.get("GHOSTEXT_LLAMA_THREADS", "1"))
    ctx = int(os.environ.get("GHOSTEXT_LLAMA_CTX", str(DEFAULT_CTX_SIZE)))
    batch = int(os.environ.get("GHOSTEXT_LLAMA_BATCH", str(DEFAULT_BATCH_SIZE)))
    return QwenLlamaCppBackend(
        LlamaCppBackendConfig(
            model_path=model_path,
            n_ctx=ctx,
            n_batch=batch,
            n_threads=threads,
            seed=seed,
        )
    )


def _build_config(seed: int) -> RuntimeConfig:
    return RuntimeConfig(
        seed=seed,
        candidate_policy=CandidatePolicyConfig(
            top_p=0.995,
            max_candidates=64,
            min_entropy_bits=0.0,
        ),
        codec=CodecConfig(
            total_frequency=4096,
            max_header_tokens=1024,
            max_body_tokens=3072,
            natural_tail_max_tokens=32,
            stall_patience_tokens=0,
            low_entropy_window_tokens=0,
            low_entropy_threshold_bits=0.0,
            max_encode_attempts=1,
        ),
    )


def evaluate_real_backend() -> dict[str, Any]:
    seed = int(os.environ.get("GHOSTEXT_LLAMA_SEED", str(DEFAULT_SEED)))
    backend = _build_backend(seed)
    config = _build_config(seed)
    passphrase = "real-eval-pass"

    cases = [
        {
            "id": "zh_real_short",
            "prompt": "请写一段自然、简短、连贯的中文段落，描写傍晚散步时看到的街景。",
            "message": "真实模型联调成功。",
        },
        {
            "id": "en_real_short",
            "prompt": "Write a short, natural, coherent paragraph about a calm evening walk in the city.",
            "message": "Real backend roundtrip check.",
        },
    ]

    rows: list[dict[str, Any]] = []
    bpt_values: list[float] = []
    enc_tps_values: list[float] = []
    dec_tps_values: list[float] = []
    success = 0

    encoder = StegoEncoder(backend, config)
    decoder = StegoDecoder(backend, config)

    max_case_retries = int(os.environ.get("GHOSTEXT_REAL_EVAL_MAX_RETRIES", "3"))

    for case in cases:
        encoded = None
        encode_error = None
        for attempt in range(1, max_case_retries + 1):
            try:
                encoded = encoder.encode(
                    case["message"],
                    passphrase=passphrase,
                    prompt=case["prompt"],
                    salt=b"s" * config.crypto.salt_len,
                    nonce=b"n" * config.crypto.nonce_len,
                )
                break
            except EncodingExhaustedError as exc:
                encode_error = exc
                if attempt == max_case_retries:
                    raise

        if encoded is None:
            assert encode_error is not None
            raise encode_error

        decoded = decoder.decode(
            encoded.text,
            passphrase=passphrase,
            prompt=case["prompt"],
        )
        ok = decoded.plaintext == case["message"]
        success += int(ok)

        rows.append(
            {
                "id": case["id"],
                "success": ok,
                "message_len_chars": len(case["message"]),
                "packet_len_bytes": len(encoded.packet),
                "total_tokens": encoded.total_tokens,
                "packet_tokens": encoded.packet_tokens,
                "tail_tokens": encoded.tail_tokens,
                "bits_per_token": encoded.bits_per_token,
                "encode_tokens_per_second": encoded.tokens_per_second,
                "decode_tokens_per_second": decoded.tokens_per_second,
                "encode_attempts": attempt,
            }
        )
        bpt_values.append(float(encoded.bits_per_token))
        enc_tps_values.append(float(encoded.tokens_per_second))
        dec_tps_values.append(float(decoded.tokens_per_second))

    # One fail-closed sanity check on wrong prompt.
    fail_closed_case = {
        "scenario": "wrong_prompt",
        "expected": "fail",
        "observed_success": False,
        "error": None,
    }
    try:
        sample = rows[0]
        # Re-encode deterministically for mismatch test.
        sample_encoded = encoder.encode(
            cases[0]["message"],
            passphrase=passphrase,
            prompt=cases[0]["prompt"],
            salt=b"s" * config.crypto.salt_len,
            nonce=b"n" * config.crypto.nonce_len,
        )
        dec = decoder.decode(
            sample_encoded.text,
            passphrase=passphrase,
            prompt="Write a totally different paragraph topic.",
        )
        fail_closed_case["observed_success"] = dec.plaintext == cases[0]["message"]
    except GhostextError as exc:
        fail_closed_case["error"] = type(exc).__name__

    return {
        "backend": "llama-cpp-qwen",
        "model_path": _resolve_model_path(),
        "seed": seed,
        "n_cases": len(cases),
        "n_success": success,
        "success_rate": success / len(cases),
        "cases": rows,
        "summary": {
            "bits_per_token": _stats(bpt_values),
            "encode_tokens_per_second": _stats(enc_tps_values),
            "decode_tokens_per_second": _stats(dec_tps_values),
        },
        "fail_closed_sanity": fail_closed_case,
    }


def main() -> None:
    out_dir = ROOT / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    data = evaluate_real_backend()
    out = out_dir / "real_backend_eval_results.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
