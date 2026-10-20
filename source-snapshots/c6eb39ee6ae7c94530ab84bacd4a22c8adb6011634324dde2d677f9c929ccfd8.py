#!/usr/bin/env python3
"""Diagnose a named failed development case without changing its recorded result."""
from __future__ import annotations
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "Ghostext/src"))
from artifact_utils import build_runtime_info
from ghostext.candidate_policy import audit_candidate_selection
from ghostext.config import CandidatePolicyConfig
from ghostext.llama_cpp_backend import LlamaCppBackendConfig, QwenLlamaCppBackend
from model_adapters import GPT2Backend
from run_stopping_llm import digest_file


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", type=Path)
    ap.add_argument("--case-id", required=True)
    ap.add_argument("--model-path", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--search-limit", type=int, default=4096)
    args = ap.parse_args()
    manifest = json.loads((args.directory / "manifest.json").read_text())
    matches = [json.loads(line) for line in (args.directory / "runs.jsonl").read_text().splitlines()
               if json.loads(line)["case_id"] == args.case_id]
    if len(matches) != 1:
        raise ValueError("Expected exactly one recorded case")
    case = matches[0]
    if case["split"] != "development" or case["status"] == "success":
        raise ValueError("This diagnostic requires a failed development case")
    model_files = [args.model_path] if manifest["backend"] == "qwen" else [
        args.model_path / name for name in manifest["model_sha256"]]
    actual_hashes = {p.name: digest_file(p) for p in model_files}
    if actual_hashes != manifest["model_sha256"]:
        raise ValueError("Diagnostic model files differ from the original cohort")
    backend = (GPT2Backend(args.model_path, threads=args.threads)
               if manifest["backend"] == "gpt2" else
               QwenLlamaCppBackend(LlamaCppBackendConfig(
                   model_path=str(args.model_path), n_threads=args.threads,
                   n_ctx=4096, n_batch=128)))
    policy = CandidatePolicyConfig(**case["config"]["candidate_policy"])
    unique = sorted({tuple(a["token_ids"]) for a in case["attempts"]
                     if a["failure_class"] == "UnsafeTokenizationError"})
    records = []
    for prefix in unique:
        prefix = list(prefix)
        raw = backend.distribution(case["prompt"], prefix, case["config"]["seed"])
        record = {"token_ids": prefix, "prefix_text": backend.render(prefix), "policies": {}}
        for limit in [0, args.search_limit]:
            config = replace(policy, empty_candidate_search=limit)
            try:
                audit = audit_candidate_selection(
                    raw, config, backend=backend, prompt=case["prompt"], generated_token_ids=prefix)
                record["policies"][str(limit)] = {
                    "status": "nonempty", "fallback_used": audit.fallback_used,
                    "candidate_count": len(audit.stable_selection.entries),
                    "token_ids": [e.token_id for e in audit.stable_selection.entries],
                    "truncated_tail_mass": audit.truncated_tail_mass,
                    "prefilter_removed_mass": audit.stability_removed_mass,
                }
            except Exception as exc:
                record["policies"][str(limit)] = {"status": type(exc).__name__, "error": str(exc)}
        records.append(record)
        print(args.case_id, len(prefix), {k: r["status"] for k, r in record["policies"].items()},
              flush=True)
    result = {
        "scope": "Post-hoc diagnosis of a named failed development case; no delivery claim.",
        "case_id": args.case_id, "backend": manifest["backend"],
        "case_sha256": hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest(),
        "original_case": case, "unique_failed_prefixes": len(records), "records": records,
        "model_sha256": actual_hashes, "runtime": build_runtime_info(),
        "source_sha256": {str(p.relative_to(ROOT.parent)): digest_file(p) for p in [
            Path(__file__).resolve(), ROOT / "scripts/model_adapters.py",
            *sorted((ROOT.parent / "Ghostext/src/ghostext").glob("*.py"))]},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
