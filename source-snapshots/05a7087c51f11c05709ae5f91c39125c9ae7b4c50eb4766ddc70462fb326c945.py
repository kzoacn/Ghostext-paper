#!/usr/bin/env python3
"""Independently reconstruct attack features from visible text and public inputs."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "Ghostext/src"))
from artifact_utils import build_runtime_info
from ghostext.candidate_policy import select_candidates
from ghostext.config import CandidatePolicyConfig
from ghostext.llama_cpp_backend import LlamaCppBackendConfig, QwenLlamaCppBackend
from ghostext.quantization import quantize_candidates
from keyless_probe import probe_bootstrap
from model_adapters import GPT2Backend
from run_stopping_llm import digest_file


def public_surprisal(backend, text, prompt, policy):
    ids = backend.tokenize(text, prompt)
    probabilities = []
    for position, token_id in enumerate(ids):
        prefix = ids[:position]
        raw = backend.distribution(prompt, prefix, 7)
        selection = select_candidates(
            raw, policy, backend=backend, prompt=prompt, generated_token_ids=prefix)
        q = quantize_candidates(selection, 4096)
        entry = q.entries[q.find_token_id_index(token_id)]
        probabilities.append(entry.frequency / q.total_frequency)
    return ids, probabilities, -sum(math.log2(p) for p in probabilities)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", type=Path)
    ap.add_argument("--study", choices=["stopping", "repair"], required=True)
    ap.add_argument("--model-path", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    manifest = json.loads((args.directory / "manifest.json").read_text())
    filename = "pairs.jsonl" if args.study == "stopping" else "runs.jsonl"
    rows = [json.loads(line) for line in (args.directory / filename).read_text().splitlines()]
    if {r["case_id"] for r in rows} != {r["case_id"] for r in manifest["tasks"]}:
        raise ValueError("Complete the prespecified cohort before selecting validation cases")
    selected = {}
    for row in sorted(rows, key=lambda r: r["case_id"]):
        if row["split"] != "test":
            continue
        if args.study == "stopping":
            if not (row["stego"]["status"] == row["natural"]["status"] == "complete"
                    and row["stego"]["canonical_text_roundtrip"]
                    and row["natural"]["canonical_text_roundtrip"]):
                continue
            group = (row["message_bits"], row["language"])
        else:
            if not (row["status"] == "success" and row["natural"]["status"] == "complete"):
                continue
            group = (row["guard_bits"], row["language"])
        selected.setdefault(group, row)
    model_files = [args.model_path] if manifest["backend"] == "qwen" else [
        args.model_path / name for name in manifest["model_sha256"]]
    actual_hashes = {p.name: digest_file(p) for p in model_files}
    if actual_hashes != manifest["model_sha256"]:
        raise ValueError("Model hashes do not match the cohort")
    threads = manifest["parameters"]["threads"]
    backend = (GPT2Backend(args.model_path, threads=threads)
               if manifest["backend"] == "gpt2" else
               QwenLlamaCppBackend(LlamaCppBackendConfig(
                   model_path=str(args.model_path), n_threads=threads, n_ctx=4096, n_batch=128)))
    policy = CandidatePolicyConfig(top_p=.995, max_candidates=64, min_entropy_bits=0)
    records = []
    for row in selected.values():
        for label in ["stego", "natural"]:
            expected = row if label == "stego" and args.study == "repair" else row[label]
            text, prompt = expected["cover_text"], row["prompt"]
            record = {"case_id": row["case_id"], "label": label,
                      "text_sha256": hashlib.sha256(text.encode()).hexdigest()}
            if args.study == "stopping":
                ids, probs, surprisal = public_surprisal(backend, text, prompt, policy)
                assert ids == expected["token_ids"]
                assert len(probs) == len(expected["chosen_probabilities"])
                delta = max((abs(x - y) for x, y in zip(probs, expected["chosen_probabilities"])),
                            default=0.)
                assert delta == 0, delta
                assert abs(surprisal - expected["surprisal_bits"]) < 1e-10
                record.update(tokens=len(ids), surprisal_bits=surprisal,
                              max_probability_difference=delta, exact_probability_match=True)
            else:
                actual = probe_bootstrap(backend, text, prompt, policy=policy)["guards"]
                cached = expected["keyless_probe"]
                for guard in ["0", "128"]:
                    for key in ["status", "tokens_observed"]:
                        assert actual[guard][key] == cached[guard][key], (actual, cached)
                record.update(probe=actual, cached_probe_matches=True)
            records.append(record)
            print(args.study, row["case_id"], label, "matches", flush=True)
    output = {
        "scope": "Independent replay consumes only visible text, prompt, public model and policy.",
        "selection": "First lexicographic eligible held-out case per (message bits or guard, language).",
        "study": args.study, "backend": manifest["backend"], "records": records,
        "source_input_sha256": digest_file(args.directory / filename),
        "model_sha256": actual_hashes, "runtime": build_runtime_info(),
        "source_sha256": {str(p.relative_to(ROOT.parent)): digest_file(p) for p in [
            Path(__file__).resolve(), ROOT / "scripts/keyless_probe.py",
            ROOT / "scripts/model_adapters.py",
            *sorted((ROOT.parent / "Ghostext/src/ghostext").glob("*.py"))]},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    main()
