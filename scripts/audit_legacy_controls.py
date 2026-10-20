#!/usr/bin/env python3
"""Check the archived pilot's actual reference policy and visible lengths."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    natural_path = ROOT / "results/detector-block/matched_natural_covers.jsonl"
    stego_path = ROOT / "results/real-backend-baseline-runs-merged.jsonl"
    probe_path = ROOT / "results/sp2027-keyless-legacy/runs.jsonl"
    load = lambda p: [json.loads(l) for l in p.read_text().splitlines()]
    natural, stego, probes = load(natural_path), load(stego_path), load(probe_path)
    key = lambda r: (r["case"]["case_id"], r["run_index"])
    probes = [r for r in probes if r["label"] == "historical_stable_sampler"]
    assert len(natural) == len(probes) == len(stego) == 18
    assert len({r["cover_text"] for r in natural}) == 18
    records = []
    for index, (partner, row, probe) in enumerate(zip(stego, natural, probes)):
        assert hashlib.sha256(row["cover_text"].encode()).hexdigest() == probe["text_sha256"]
        # The merged historical batches reuse (case_id, run_index). The original
        # generator emits controls in raw-row order; never join by that key alone.
        assert key(partner) == key(row)
        assert row["total_tokens"] == partner["total_tokens"] == probe["visible_tokens"]
        records.append({
            "raw_row_index": index, "case_id": row["case"]["case_id"], "run_index": row["run_index"],
            "visible_tokens": probe["visible_tokens"], "length_matches": True,
            "recorded_unfiltered_fallbacks": row["unstable_top_token_fallbacks"],
            "legacy_probe_status": probe["guards"]["0"]["status"],
        })
    result = {
        "reference": "Filtered floating-point probabilities with raw-argmax fallback after empty stable sets.",
        "not_the_reference": "Not the strict integer-frequency Q used in fresh studies; not ordinary EOS sampling.",
        "fallback_events": sum(r["recorded_unfiltered_fallbacks"] for r in records),
        "texts_with_fallbacks": sum(r["recorded_unfiltered_fallbacks"] > 0 for r in records),
        "fallback_positions": "Not recorded; cannot infer whether before or after the bootstrap.",
        "pairing": "Original raw-row order, checked against prompt/case identifiers and visible lengths.",
        "reused_case_run_keys": len(stego) - len({key(r) for r in stego}),
        "records": records,
        "input_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in [natural_path, stego_path, probe_path,
                                   ROOT / "scripts/run_detector_block.py"]},
    }
    target = ROOT / "results/sp2027-keyless-legacy/reference-audit.json"
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"records", "input_sha256"}},
                     indent=2))


if __name__ == "__main__":
    main()
