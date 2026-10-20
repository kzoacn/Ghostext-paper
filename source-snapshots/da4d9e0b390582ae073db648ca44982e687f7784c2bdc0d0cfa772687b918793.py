#!/usr/bin/env python3
"""Targeted reproduction of every completed reverse-failure in a frozen cohort."""
from __future__ import annotations
import argparse
from fractions import Fraction
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "Ghostext/src"))
from artifact_utils import build_runtime_info, deterministic_seed
from ghostext.config import CandidatePolicyConfig
from ghostext.llama_cpp_backend import LlamaCppBackendConfig, QwenLlamaCppBackend
from model_adapters import GPT2Backend
from run_stopping_llm import digest_file
from stopping_experiment import next_q, recover_integer, sample_text


def decode_from_text(backend, text, prompt, bits, seed, policy):
    """Receiver rebuilds all intervals from text; no encoder state is accepted."""
    rng = random.Random(seed)
    rng.getrandbits(bits)  # Advance the experimental tape to its rotation draws.
    ids = backend.tokenize(text, prompt)
    low, high, history = Fraction(0), Fraction(1 << bits), []
    for position, token_id in enumerate(ids):
        q = next_q(backend, prompt, ids[:position], policy)
        entry = q.entries[q.find_token_id_index(token_id)]
        offset = Fraction(rng.getrandbits(192), 1 << 192)
        history.append((low, high, offset))
        width = high - low
        low, high = (low + width * Fraction(entry.cdf_low, q.total_frequency),
                     low + width * Fraction(entry.cdf_high, q.total_frequency))
    return recover_integer(low, high, history)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", type=Path)
    ap.add_argument("--model-path", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    manifest = json.loads((args.directory / "manifest.json").read_text())
    rows = [json.loads(l) for l in (args.directory / "pairs.jsonl").read_text().splitlines()]
    assert len(rows) == len(manifest["tasks"])
    assert {r["case_id"] for r in rows} == {r["case_id"] for r in manifest["tasks"]}
    selected = sorted([r for r in rows if r["stego"]["status"] == "complete"
                       and r["stego"]["recovery_match"] is False], key=lambda r: r["case_id"])
    model_files = [args.model_path] if manifest["backend"] == "qwen" else [
        args.model_path / name for name in manifest["model_sha256"]]
    actual_hashes = {p.name: digest_file(p) for p in model_files}
    assert actual_hashes == manifest["model_sha256"]
    threads = manifest["parameters"]["threads"]
    backend = (GPT2Backend(args.model_path, threads=threads) if manifest["backend"] == "gpt2"
               else QwenLlamaCppBackend(LlamaCppBackendConfig(
                   model_path=str(args.model_path), n_threads=threads, n_ctx=4096, n_batch=128)))
    policy = CandidatePolicyConfig(
        top_p=.995, max_candidates=64, min_entropy_bits=0,
        empty_candidate_search=manifest["parameters"].get("empty_candidate_search", 0))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    profile = {
        "scope": "Every completed reverse-failure from the named cohort; targeted diagnosis, not a general repair rate or detector evaluation.",
        "selected_case_ids": [r["case_id"] for r in selected],
        "input_sha256": digest_file(args.directory / "pairs.jsonl"),
        "model_sha256": actual_hashes, "runtime": build_runtime_info(),
        "source_sha256": {str(p.relative_to(ROOT.parent)): digest_file(p) for p in [
            Path(__file__).resolve(), ROOT / "scripts/stopping_experiment.py",
            ROOT / "scripts/model_adapters.py", ROOT / "scripts/artifact_utils.py",
            *sorted((ROOT.parent / "Ghostext/src/ghostext").glob("*.py"))]},
    }
    path = args.out_dir / "manifest.json"
    if path.exists():
        old = json.loads(path.read_text())
        for key in ["selected_case_ids", "input_sha256", "model_sha256", "source_sha256"]:
            assert old[key] == profile[key]
    else:
        path.write_text(json.dumps(profile, indent=2) + "\n")
    path = args.out_dir / "runs.jsonl"
    done = {json.loads(l)["case_id"] for l in path.read_text().splitlines()} if path.exists() else set()
    with path.open("a") as output:
        for row in selected:
            if row["case_id"] in done:
                continue
            seed = deterministic_seed("stopping", manifest["parameters"]["seed"],
                                      manifest["backend"], row["case_id"])
            bits, prompt = row["message_bits"], row["prompt"]
            result = {"case_id": row["case_id"], "message_bits": bits}
            unverified = sample_text(backend, prompt, seed=seed, bits=bits, policy=policy)
            assert unverified["token_ids"] == row["stego"]["token_ids"]
            assert unverified["chosen_probabilities"] == row["stego"]["chosen_probabilities"]
            assert unverified["status"] == "complete" and unverified["recovery_match"] is False
            verified = sample_text(backend, prompt, seed=seed, bits=bits, policy=policy,
                                   verify_before_stop=True)
            assert verified["token_ids"][:len(unverified["token_ids"])] == unverified["token_ids"]
            original_value = random.Random(seed).getrandbits(bits)
            decoded_old = decode_from_text(backend, unverified["cover_text"], prompt, bits, seed, policy)
            decoded_new = decode_from_text(backend, verified["cover_text"], prompt, bits, seed, policy)
            assert decoded_old != original_value
            result.update(
                unverified=unverified, verified=verified,
                independent_text_decode_before_matches=False,
                independent_text_decode_after_matches=decoded_new == original_value,
                additional_tokens=verified["tokens"] - unverified["tokens"],
            )
            output.write(json.dumps(result, ensure_ascii=False) + "\n")
            output.flush()
            print(row["case_id"], verified["status"], "vetoes", verified["rejected_stop_count"],
                  "independent decode", result["independent_text_decode_after_matches"], flush=True)


if __name__ == "__main__":
    main()
