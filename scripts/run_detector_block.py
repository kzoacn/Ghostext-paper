#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import random
import re
import sys
from typing import Any
import urllib.error
import urllib.request

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from artifact_utils import (
    build_runtime_info,
    deterministic_seed,
    pearson_correlation,
    roc_auc_score,
    sha256_hex,
    spearman_correlation,
    utc_timestamp,
)
from ghostext.errors import UnsafeTokenizationError
from ghostext.config import CandidatePolicyConfig, CodecConfig, RuntimeConfig
from ghostext.llama_cpp_backend import LlamaCppBackendConfig, QwenLlamaCppBackend
from ghostext.pipeline import prepare_quantized_distribution


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


def sample_token_id(quantized, rng: random.Random) -> int:
    draw = rng.random()
    cumulative = 0.0
    for entry in quantized.entries:
        cumulative += entry.probability
        if draw <= cumulative:
            return entry.token_id
    return quantized.entries[-1].token_id


def generate_natural_cover(
    *,
    backend: QwenLlamaCppBackend,
    config: RuntimeConfig,
    prompt: str,
    target_tokens: int,
    seed_material: tuple[object, ...],
) -> tuple[str, int]:
    rng = random.Random(deterministic_seed("natural-cover", *seed_material))
    token_ids: list[int] = []
    unstable_fallbacks = 0
    for _ in range(target_tokens):
        try:
            quantized = prepare_quantized_distribution(
                backend,
                prompt=prompt,
                generated_token_ids=token_ids,
                config=config,
            )
            token_ids.append(sample_token_id(quantized, rng))
        except UnsafeTokenizationError:
            raw_distribution = backend.distribution(prompt, token_ids, config.seed)
            top_index = int(raw_distribution.logits.argmax())
            token_ids.append(int(raw_distribution.token_ids[top_index]))
            unstable_fallbacks += 1
    return backend.render(token_ids), unstable_fallbacks


def char_ngrams(text: str, n: int = 3) -> list[str]:
    if len(text) < n:
        return [text] if text else []
    return [text[index : index + n] for index in range(len(text) - n + 1)]


def score_doc_naive_bayes(
    text: str,
    positive_docs: list[str],
    negative_docs: list[str],
    *,
    ngram_n: int = 3,
) -> float:
    pos_counts: Counter[str] = Counter()
    neg_counts: Counter[str] = Counter()
    for doc in positive_docs:
        pos_counts.update(char_ngrams(doc, n=ngram_n))
    for doc in negative_docs:
        neg_counts.update(char_ngrams(doc, n=ngram_n))
    vocab = set(pos_counts) | set(neg_counts) | set(char_ngrams(text, n=ngram_n))
    alpha = 1.0
    pos_total = sum(pos_counts.values()) + alpha * max(1, len(vocab))
    neg_total = sum(neg_counts.values()) + alpha * max(1, len(vocab))
    score = 0.0
    for ngram in char_ngrams(text, n=ngram_n):
        score += math.log((pos_counts[ngram] + alpha) / pos_total)
        score -= math.log((neg_counts[ngram] + alpha) / neg_total)
    return score


def leave_one_out_scores(samples: list[dict[str, Any]], *, ngram_n: int = 3) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for index, sample in enumerate(samples):
        train = [item for offset, item in enumerate(samples) if offset != index]
        positive_docs = [item["text"] for item in train if item["label"] == 1]
        negative_docs = [item["text"] for item in train if item["label"] == 0]
        score = score_doc_naive_bayes(
            sample["text"],
            positive_docs=positive_docs,
            negative_docs=negative_docs,
            ngram_n=ngram_n,
        )
        scored.append({**sample, "char_trigram_nb_score": score})
    return scored


def summarize_auc(scored_samples: list[dict[str, Any]], *, score_key: str) -> dict[str, Any]:
    overall_auc = roc_auc_score(
        [item["label"] for item in scored_samples],
        [item[score_key] for item in scored_samples],
    )
    by_language = {}
    for language in sorted({item["language"] for item in scored_samples}):
        subset = [item for item in scored_samples if item["language"] == language]
        by_language[language] = roc_auc_score(
            [item["label"] for item in subset],
            [item[score_key] for item in subset],
        )
    return {
        "overall_auc": overall_auc,
        "by_language_auc": by_language,
    }


def extract_response_output_text(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    collected: list[str] = []
    for output_item in payload.get("output", []):
        if not isinstance(output_item, dict):
            continue
        for content_item in output_item.get("content", []):
            if not isinstance(content_item, dict):
                continue
            text_value = content_item.get("text")
            if isinstance(text_value, str) and text_value.strip():
                collected.append(text_value.strip())
    if collected:
        return "\n".join(collected).strip()

    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        content = message.get("content", "")
        if isinstance(content, str) and content.strip():
            return content.strip()
    return ""


def call_openai_responses_api(
    *,
    api_key: str,
    api_base: str,
    model: str,
    prompt: str,
    timeout_seconds: float,
    max_output_tokens: int,
) -> str:
    payload = {
        "model": model,
        "input": prompt,
        "max_output_tokens": max_output_tokens,
    }
    endpoint = api_base.rstrip("/") + "/responses"
    request = urllib.request.Request(
        endpoint,
        method="POST",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        raise RuntimeError(f"responses_api_http_error status={exc.code} body={body[:300]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"responses_api_url_error reason={exc.reason}") from exc
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("responses_api_invalid_json") from exc
    text = extract_response_output_text(parsed)
    if not text:
        raise RuntimeError("responses_api_empty_output_text")
    return text


def build_llm_judge_prompt(
    *,
    original_prompt: str,
    candidate_a: str,
    candidate_b: str,
) -> str:
    return (
        "You are an evaluator for text naturalness in a steganography study.\n"
        "Given two candidate responses to the same writing task, pick the one that reads more like "
        "ordinary human-authored text.\n\n"
        "Task prompt shared by both candidates:\n"
        f"{original_prompt}\n\n"
        "Candidate A:\n"
        "<<A>>\n"
        f"{candidate_a}\n"
        "<</A>>\n\n"
        "Candidate B:\n"
        "<<B>>\n"
        f"{candidate_b}\n"
        "<</B>>\n\n"
        "Return strict JSON only with this schema:\n"
        "{\"choice\":\"A\"|\"B\"|\"TIE\", \"confidence\":0.0-1.0, \"reason\":\"<=20 words\"}"
    )


def parse_llm_judge_output(text: str) -> dict[str, Any]:
    stripped = text.strip()
    parsed_choice: str | None = None
    parsed_confidence: float | None = None
    parsed_reason: str | None = None

    candidates = [stripped]
    candidates.extend(match.group(0) for match in re.finditer(r"\{.*?\}", stripped, flags=re.DOTALL))
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        raw_choice = payload.get("choice")
        if isinstance(raw_choice, str):
            upper_choice = raw_choice.strip().upper()
            if upper_choice in {"A", "B", "TIE"}:
                parsed_choice = upper_choice
        raw_confidence = payload.get("confidence")
        if isinstance(raw_confidence, (int, float)):
            parsed_confidence = float(raw_confidence)
        elif isinstance(raw_confidence, str):
            try:
                parsed_confidence = float(raw_confidence)
            except ValueError:
                pass
        raw_reason = payload.get("reason")
        if isinstance(raw_reason, str) and raw_reason.strip():
            parsed_reason = raw_reason.strip()
        break

    if parsed_choice is None:
        match = re.search(r"\b(A|B|TIE)\b", stripped, flags=re.IGNORECASE)
        if match is not None:
            parsed_choice = match.group(1).upper()
    return {
        "choice": parsed_choice,
        "confidence": parsed_confidence,
        "reason": parsed_reason,
    }


def run_llm_judge_block(
    *,
    stego_runs: list[dict[str, Any]],
    natural_runs: list[dict[str, Any]],
    model: str,
    api_key: str,
    api_base: str,
    timeout_seconds: float,
    max_output_tokens: int,
    judge_seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    natural_by_key = {
        (row["case"]["case_id"], row["run_index"]): row
        for row in natural_runs
    }
    rng = random.Random(deterministic_seed("llm-judge-order", model, judge_seed, len(stego_runs)))

    pair_rows: list[dict[str, Any]] = []
    scored_samples: list[dict[str, Any]] = []
    valid_pairs = 0
    natural_preferred = 0
    stego_preferred = 0
    tie_or_unparsed = 0
    api_errors = 0

    for row in stego_runs:
        key = (row["case"]["case_id"], row["run_index"])
        natural_row = natural_by_key.get(key)
        if natural_row is None:
            continue

        stego_on_a = rng.random() < 0.5
        if stego_on_a:
            candidate_a_text = row["cover_text"]
            candidate_b_text = natural_row["cover_text"]
            source_a = "ghostext"
            source_b = "natural"
        else:
            candidate_a_text = natural_row["cover_text"]
            candidate_b_text = row["cover_text"]
            source_a = "natural"
            source_b = "ghostext"

        prompt = build_llm_judge_prompt(
            original_prompt=row["case"]["prompt"],
            candidate_a=candidate_a_text,
            candidate_b=candidate_b_text,
        )

        raw_output = ""
        parse_error: str | None = None
        judge_choice: str | None = None
        judge_confidence: float | None = None
        judge_reason: str | None = None
        try:
            raw_output = call_openai_responses_api(
                api_key=api_key,
                api_base=api_base,
                model=model,
                prompt=prompt,
                timeout_seconds=timeout_seconds,
                max_output_tokens=max_output_tokens,
            )
            parsed = parse_llm_judge_output(raw_output)
            judge_choice = parsed["choice"]
            judge_confidence = parsed["confidence"]
            judge_reason = parsed["reason"]
        except Exception as exc:
            parse_error = str(exc)
            api_errors += 1

        better_source: str | None = None
        if judge_choice == "A":
            better_source = source_a
        elif judge_choice == "B":
            better_source = source_b
        elif judge_choice == "TIE":
            better_source = None

        if better_source == "natural":
            stego_score = 1.0
            natural_score = 0.0
            valid_pairs += 1
            natural_preferred += 1
        elif better_source == "ghostext":
            stego_score = 0.0
            natural_score = 1.0
            valid_pairs += 1
            stego_preferred += 1
        else:
            stego_score = 0.5
            natural_score = 0.5
            tie_or_unparsed += 1

        pair_rows.append(
            {
                "pair_id": f"pair::{row['case']['case_id']}::{row['run_index']}",
                "case_id": row["case"]["case_id"],
                "run_index": row["run_index"],
                "language": row["case"]["language"],
                "candidate_a_source": source_a,
                "candidate_b_source": source_b,
                "candidate_a_text": candidate_a_text,
                "candidate_b_text": candidate_b_text,
                "judge_model": model,
                "judge_choice": judge_choice,
                "judge_confidence": judge_confidence,
                "judge_reason": judge_reason,
                "judge_output_sha256": sha256_hex(raw_output) if raw_output else None,
                "judge_raw_output": raw_output if raw_output else None,
                "judge_error": parse_error,
                "preferred_source": better_source,
            }
        )
        scored_samples.append(
            {
                "sample_id": f"ghostext::{row['case']['case_id']}::{row['run_index']}",
                "source": "ghostext",
                "language": row["case"]["language"],
                "label": 1,
                "llm_judge_stego_score": stego_score,
                "bhat_tv_total": row["approximation_audit"]["bhat_tv_total"],
            }
        )
        scored_samples.append(
            {
                "sample_id": f"natural::{row['case']['case_id']}::{row['run_index']}",
                "source": "natural",
                "language": row["case"]["language"],
                "label": 0,
                "llm_judge_stego_score": natural_score,
                "bhat_tv_total": None,
            }
        )

    auc_summary = summarize_auc(scored_samples, score_key="llm_judge_stego_score") if scored_samples else {
        "overall_auc": 0.0,
        "by_language_auc": {},
    }
    total_pairs = len(pair_rows)
    summary = {
        "status": "ok",
        "model": model,
        "api_base": api_base,
        "total_pairs": total_pairs,
        "valid_pairs": valid_pairs,
        "tie_or_unparsed_pairs": tie_or_unparsed,
        "api_error_pairs": api_errors,
        "natural_preferred_rate_among_valid": (
            (natural_preferred / valid_pairs) if valid_pairs else 0.0
        ),
        "stego_preferred_rate_among_valid": (
            (stego_preferred / valid_pairs) if valid_pairs else 0.0
        ),
        **auc_summary,
    }
    return pair_rows, scored_samples, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the detector-facing Ghostext pilot block")
    parser.add_argument(
        "--baseline-summary",
        default="/mnt/d/work/Ghostext-paper/results/real-backend-baseline-summary-merged.json",
    )
    parser.add_argument(
        "--baseline-runs",
        default="/mnt/d/work/Ghostext-paper/results/real-backend-baseline-runs-merged.jsonl",
    )
    parser.add_argument("--out-dir", default="/mnt/d/work/Ghostext-paper/results/detector-block")
    parser.add_argument("--disable-llm-judge", action="store_true")
    parser.add_argument("--llm-judge-model", default="gpt-5.4")
    parser.add_argument(
        "--llm-judge-api-base",
        default=os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1"),
    )
    parser.add_argument("--llm-judge-timeout-seconds", type=float, default=90.0)
    parser.add_argument("--llm-judge-max-output-tokens", type=int, default=120)
    parser.add_argument("--llm-judge-seed", type=int, default=20260422)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline_summary = load_json(Path(args.baseline_summary))
    stego_runs = [
        row
        for row in load_jsonl(Path(args.baseline_runs))
        if row.get("status") == "success" and row.get("decode_match")
    ]
    if not stego_runs:
        raise SystemExit("no successful stego baseline runs found")

    model_path = baseline_summary["model"]["resolved_model_path"]
    model_id = baseline_summary["model"]["backend_metadata"]["model_id"]
    backend = QwenLlamaCppBackend(
        LlamaCppBackendConfig(
            model_path=model_path,
            model_id=model_id,
            n_ctx=baseline_summary["model"]["ctx_size"],
            n_batch=baseline_summary["model"]["batch_size"],
            n_threads=baseline_summary["model"]["threads"],
            seed=baseline_summary["config"]["seed"],
        )
    )
    natural_config = RuntimeConfig(
        seed=baseline_summary["config"]["seed"],
        candidate_policy=CandidatePolicyConfig(
            top_p=baseline_summary["config"]["candidate"]["top_p"],
            max_candidates=baseline_summary["config"]["candidate"]["max_candidates"],
            min_entropy_bits=baseline_summary["config"]["candidate"]["min_entropy_bits"],
            enforce_retokenization_stability=baseline_summary["config"]["candidate"][
                "retokenization_stability"
            ],
        ),
        codec=CodecConfig(
            total_frequency=baseline_summary["config"]["codec"]["total_frequency"],
            max_header_tokens=baseline_summary["config"]["codec"]["header_token_budget"],
            max_body_tokens=baseline_summary["config"]["codec"]["body_token_budget"],
            natural_tail_max_tokens=baseline_summary["config"]["codec"]["natural_tail_max_tokens"],
            stall_patience_tokens=baseline_summary["config"]["codec"]["stall_patience_tokens"],
            low_entropy_window_tokens=baseline_summary["config"]["codec"]["low_entropy_window_tokens"],
            low_entropy_threshold_bits=baseline_summary["config"]["codec"][
                "low_entropy_threshold_bits"
            ],
            max_encode_attempts=1,
        ),
    )

    natural_runs: list[dict[str, Any]] = []
    for row in stego_runs:
        cover_text, fallback_count = generate_natural_cover(
            backend=backend,
            config=natural_config,
            prompt=row["case"]["prompt"],
            target_tokens=row["total_tokens"],
            seed_material=(
                row["case"]["case_id"],
                row["run_index"],
                row["total_tokens"],
                baseline_summary["config"]["seed"],
            ),
        )
        natural_runs.append(
            {
                "run_index": row["run_index"],
                "case": row["case"],
                "status": "success",
                "source": "matched_length_natural_cover",
                "attempts_used": 1,
                "total_tokens": row["total_tokens"],
                "cover_text": cover_text,
                "cover_text_sha256": sha256_hex(cover_text),
                "cover_length_chars": len(cover_text),
                "unstable_top_token_fallbacks": fallback_count,
            }
        )

    retry_scored_samples: list[dict[str, Any]] = []
    text_samples: list[dict[str, Any]] = []
    for row in stego_runs:
        retry_scored_samples.append(
            {
                "source": "ghostext",
                "language": row["case"]["language"],
                "label": 1,
                "attempts_used": row["attempts_used"],
            }
        )
        text_samples.append(
            {
                "sample_id": f"ghostext::{row['case']['case_id']}::{row['run_index']}",
                "source": "ghostext",
                "language": row["case"]["language"],
                "label": 1,
                "text": row["cover_text"],
                "bhat_tv_total": row["approximation_audit"]["bhat_tv_total"],
            }
        )
    for row in natural_runs:
        retry_scored_samples.append(
            {
                "source": "natural",
                "language": row["case"]["language"],
                "label": 0,
                "attempts_used": row["attempts_used"],
            }
        )
        text_samples.append(
            {
                "sample_id": f"natural::{row['case']['case_id']}::{row['run_index']}",
                "source": "natural",
                "language": row["case"]["language"],
                "label": 0,
                "text": row["cover_text"],
                "bhat_tv_total": None,
            }
        )

    retry_auc = summarize_auc(
        [
            {**item, "retry_score": float(item["attempts_used"])}
            for item in retry_scored_samples
        ],
        score_key="retry_score",
    )

    scored_samples: list[dict[str, Any]] = []
    for language in sorted({item["language"] for item in text_samples}):
        subset = [item for item in text_samples if item["language"] == language]
        scored_samples.extend(leave_one_out_scores(subset, ngram_n=3))
    char_trigram_auc = summarize_auc(scored_samples, score_key="char_trigram_nb_score")

    stego_scored = [item for item in scored_samples if item["source"] == "ghostext"]
    bhat_values = [float(item["bhat_tv_total"]) for item in stego_scored if item["bhat_tv_total"] is not None]
    detector_scores = [
        float(item["char_trigram_nb_score"])
        for item in stego_scored
        if item["bhat_tv_total"] is not None
    ]

    llm_judge_pairs: list[dict[str, Any]] = []
    llm_judge_scored: list[dict[str, Any]] = []
    llm_judge_summary: dict[str, Any]
    bhat_vs_llm_judge: dict[str, float] | None = None
    if args.disable_llm_judge:
        llm_judge_summary = {
            "status": "disabled_by_flag",
            "model": args.llm_judge_model,
        }
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            llm_judge_summary = {
                "status": "skipped_missing_api_key",
                "model": args.llm_judge_model,
                "api_base": args.llm_judge_api_base,
            }
        else:
            llm_judge_pairs, llm_judge_scored, llm_judge_summary = run_llm_judge_block(
                stego_runs=stego_runs,
                natural_runs=natural_runs,
                model=args.llm_judge_model,
                api_key=api_key,
                api_base=args.llm_judge_api_base,
                timeout_seconds=args.llm_judge_timeout_seconds,
                max_output_tokens=args.llm_judge_max_output_tokens,
                judge_seed=args.llm_judge_seed,
            )
            stego_llm_scored = [item for item in llm_judge_scored if item["source"] == "ghostext"]
            bhat_values_llm = [
                float(item["bhat_tv_total"])
                for item in stego_llm_scored
                if item["bhat_tv_total"] is not None
            ]
            llm_detector_scores = [
                float(item["llm_judge_stego_score"])
                for item in stego_llm_scored
                if item["bhat_tv_total"] is not None
            ]
            bhat_vs_llm_judge = {
                "pearson": pearson_correlation(bhat_values_llm, llm_detector_scores),
                "spearman": spearman_correlation(bhat_values_llm, llm_detector_scores),
            }

    summary = {
        "generated_at_utc": utc_timestamp(),
        "runtime": build_runtime_info(),
        "input_artifacts": {
            "baseline_summary": str(Path(args.baseline_summary).resolve()),
            "baseline_runs": str(Path(args.baseline_runs).resolve()),
        },
        "dataset": {
            "stego_samples": len(stego_runs),
            "natural_samples": len(natural_runs),
            "matching_policy": "same prompt and matched total token count per released stego sample",
            "text_detector_cv": "leave-one-out within language",
        },
        "retry_feature_detector": retry_auc,
        "char_trigram_naive_bayes_detector": char_trigram_auc,
        "llm_judge_detector": llm_judge_summary,
        "bhat_tv_vs_char_trigram_stego_correlation": {
            "pearson": pearson_correlation(bhat_values, detector_scores),
            "spearman": spearman_correlation(bhat_values, detector_scores),
        },
        "bhat_tv_vs_llm_judge_stego_correlation": bhat_vs_llm_judge,
    }

    natural_runs_path = out_dir / "matched_natural_covers.jsonl"
    scored_path = out_dir / "detector_scores.jsonl"
    llm_pair_path = out_dir / "llm_judge_pairs.jsonl"
    llm_scored_path = out_dir / "llm_judge_scores.jsonl"
    summary_path = out_dir / "detector_block_summary.json"
    with natural_runs_path.open("w", encoding="utf-8") as handle:
        for row in natural_runs:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with scored_path.open("w", encoding="utf-8") as handle:
        for row in scored_samples:
            output = {key: value for key, value in row.items() if key != "text"}
            handle.write(json.dumps(output, ensure_ascii=False) + "\n")
    with llm_pair_path.open("w", encoding="utf-8") as handle:
        for row in llm_judge_pairs:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with llm_scored_path.open("w", encoding="utf-8") as handle:
        for row in llm_judge_scored:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "summary_file": str(summary_path),
                "retry_feature_auc": summary["retry_feature_detector"]["overall_auc"],
                "char_trigram_auc": summary["char_trigram_naive_bayes_detector"]["overall_auc"],
                "llm_judge_status": summary["llm_judge_detector"]["status"],
                "llm_judge_auc": summary["llm_judge_detector"].get("overall_auc"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
