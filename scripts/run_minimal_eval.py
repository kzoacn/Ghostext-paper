#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import statistics
import sys
from hashlib import sha256
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GHOSTEXT_SRC = (ROOT / "../Ghostext/src").resolve()
if str(GHOSTEXT_SRC) not in sys.path:
    sys.path.insert(0, str(GHOSTEXT_SRC))

from ghostext.config import RuntimeConfig
from ghostext.decoder import StegoDecoder
from ghostext.encoder import StegoEncoder
from ghostext.errors import GhostextError
from ghostext.model_backend import ToyCharBackend


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": float(statistics.fmean(values)),
        "min": float(min(values)),
        "max": float(max(values)),
    }


def _deterministic_bytes(label: str, n: int) -> bytes:
    out = b""
    counter = 0
    while len(out) < n:
        block = sha256(f"{label}:{counter}".encode("utf-8")).digest()
        out += block
        counter += 1
    return out[:n]


def evaluate_correctness_and_overhead() -> dict[str, Any]:
    backend = ToyCharBackend()
    passphrase = "eval-pass"
    cases = [
        {
            "id": "zh_short",
            "prompt": "请写一段温柔自然的中文短文。",
            "message": "今晚七点在老地方见。",
            "seed": 17,
        },
        {
            "id": "en_short",
            "prompt": "Write a calm and readable English paragraph.",
            "message": "Meet me near the station at seven.",
            "seed": 29,
        },
        {
            "id": "zh_medium",
            "prompt": "请写一段自然、连贯、简短的中文段落，描写傍晚散步街景。",
            "message": "这是一条更长一点的测试消息，用于观察开销表现。",
            "seed": 33,
        },
        {
            "id": "en_medium",
            "prompt": "Write a short coherent paragraph about a quiet evening walk.",
            "message": "This is a slightly longer hidden message for overhead measurement.",
            "seed": 41,
        },
    ]

    rows: list[dict[str, Any]] = []
    success = 0
    bpt_values: list[float] = []
    tps_values: list[float] = []
    tokens_values: list[float] = []

    for case in cases:
        config = RuntimeConfig(seed=case["seed"])
        encoder = StegoEncoder(backend, config)
        decoder = StegoDecoder(backend, config)
        salt = _deterministic_bytes(
            f"minimal-eval-salt:{case['id']}:{case['seed']}",
            config.crypto.salt_len,
        )
        nonce = _deterministic_bytes(
            f"minimal-eval-nonce:{case['id']}:{case['seed']}",
            config.crypto.nonce_len,
        )
        encoded = encoder.encode(
            case["message"],
            passphrase=passphrase,
            prompt=case["prompt"],
            salt=salt,
            nonce=nonce,
        )
        decoded = decoder.decode(
            encoded.text,
            passphrase=passphrase,
            prompt=case["prompt"],
        )
        ok = decoded.plaintext == case["message"]
        success += int(ok)
        row = {
            "id": case["id"],
            "seed": case["seed"],
            "success": ok,
            "message_len_chars": len(case["message"]),
            "packet_len_bytes": len(encoded.packet),
            "total_tokens": encoded.total_tokens,
            "packet_tokens": encoded.packet_tokens,
            "tail_tokens": encoded.tail_tokens,
            "bits_per_token": encoded.bits_per_token,
            "encode_tokens_per_second": encoded.tokens_per_second,
            "decode_tokens_per_second": decoded.tokens_per_second,
        }
        rows.append(row)
        bpt_values.append(float(encoded.bits_per_token))
        tps_values.append(float(encoded.tokens_per_second))
        tokens_values.append(float(encoded.total_tokens))

    return {
        "n_cases": len(cases),
        "n_success": success,
        "success_rate": success / len(cases),
        "cases": rows,
        "overhead_summary": {
            "bits_per_token": _stats(bpt_values),
            "encode_tokens_per_second": _stats(tps_values),
            "total_tokens": _stats(tokens_values),
        },
    }


def evaluate_fail_closed() -> dict[str, Any]:
    backend = ToyCharBackend()
    prompt = "请写一段简短的中文短文。"
    message = "把消息藏在文本里。"
    passphrase = "hunter2"
    good_config = RuntimeConfig(seed=7)

    encoded = StegoEncoder(backend, good_config).encode(
        message,
        passphrase=passphrase,
        prompt=prompt,
        salt=_deterministic_bytes(
            f"minimal-fail-closed-salt:{good_config.seed}",
            good_config.crypto.salt_len,
        ),
        nonce=_deterministic_bytes(
            f"minimal-fail-closed-nonce:{good_config.seed}",
            good_config.crypto.nonce_len,
        ),
    )

    scenarios = []

    def run_case(name: str, *, config: RuntimeConfig, text: str, passphrase_: str, prompt_: str) -> None:
        ok = False
        err_name = None
        try:
            decoded = StegoDecoder(backend, config).decode(
                text,
                passphrase=passphrase_,
                prompt=prompt_,
            )
            ok = decoded.plaintext == message
        except GhostextError as exc:
            err_name = type(exc).__name__
        scenarios.append(
            {
                "scenario": name,
                "expected": "fail" if name != "matched" else "success",
                "observed_success": ok,
                "error": err_name,
            }
        )

    run_case(
        "matched",
        config=good_config,
        text=encoded.text,
        passphrase_=passphrase,
        prompt_=prompt,
    )

    run_case(
        "wrong_seed",
        config=RuntimeConfig(seed=8),
        text=encoded.text,
        passphrase_=passphrase,
        prompt_=prompt,
    )

    run_case(
        "wrong_prompt",
        config=good_config,
        text=encoded.text,
        passphrase_=passphrase,
        prompt_="Write an English paragraph instead.",
    )

    run_case(
        "wrong_passphrase",
        config=good_config,
        text=encoded.text,
        passphrase_="wrong",
        prompt_=prompt,
    )

    packet_text = encoded.text[: encoded.packet_tokens]
    if packet_text:
        last = packet_text[-1]
        repl = "。" if last != "。" else "，"
        mutated_packet_text = packet_text[:-1] + repl
    else:
        mutated_packet_text = packet_text
    mutated_text = mutated_packet_text + encoded.text[encoded.packet_tokens :]
    run_case(
        "mutated_text",
        config=good_config,
        text=mutated_text,
        passphrase_=passphrase,
        prompt_=prompt,
    )

    n_expected_fail = sum(1 for s in scenarios if s["expected"] == "fail")
    n_failed_as_expected = sum(
        1 for s in scenarios if s["expected"] == "fail" and not s["observed_success"]
    )

    return {
        "scenarios": scenarios,
        "n_expected_fail": n_expected_fail,
        "n_failed_as_expected": n_failed_as_expected,
        "fail_closed_rate": (n_failed_as_expected / n_expected_fail) if n_expected_fail else 0.0,
    }


def main() -> None:
    results_dir = ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "correctness_and_overhead": evaluate_correctness_and_overhead(),
        "fail_closed": evaluate_fail_closed(),
    }

    out_json = results_dir / "minimal_eval_results.json"
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out_json}")


if __name__ == "__main__":
    main()
