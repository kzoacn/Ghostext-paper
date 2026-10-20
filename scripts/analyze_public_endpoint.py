#!/usr/bin/env python3
"""Recompute public endpoint decisions using only saved integer CDF boundaries."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def independent_decision(arm, lengths, guard):
    """Standalone integer arithmetic; does not import the Ghostext decoder."""
    segment, endpoints, payloads = 0, [], []
    low, high = 0, 1 << (8 * lengths[0] + guard)
    for i, item in enumerate(arm["trace"]):
        assert i == item["index"]
        assert item["token_id"] == arm["visible_token_ids"][i]
        if "cdf_low" not in item:
            return "outside_candidate_set", endpoints, i + 1, payloads
        if item["allows_encoding"]:
            a, b, total = item["cdf_low"], item["cdf_high"], item["total_frequency"]
            assert 0 <= a < b <= total
            width = high - low
            low, high = low + width * a // total, low + width * b // total
            if low >= high:
                return "zero_width_interval", endpoints, i + 1, payloads
        elif item["token_id"] != item["top_token_id"]:
            return "non_greedy_token", endpoints, i + 1, payloads
        if low // (1 << guard) == (high - 1) // (1 << guard):
            endpoints.append(i + 1)
            payloads.append((low >> guard).to_bytes(lengths[segment], "big"))
            segment += 1
            if segment == len(lengths):
                return ("endpoint_at_end" if i + 1 == arm["visible_tokens"]
                        else "endpoint_before_end"), endpoints, i + 1, payloads
            low, high = 0, 1 << (8 * lengths[segment] + guard)
    if arm["status"] == "source_invalid":
        assert arm["error"] and len(arm["trace"]) < arm["visible_tokens"]
        return "source_invalid", endpoints, len(arm["trace"]), payloads
    assert len(arm["trace"]) == arm["visible_tokens"]
    return "unfinished_at_end", endpoints, len(arm["trace"]), payloads


def nominal_wilson(hits, total):
    p = hits / total
    z = 1.96
    scale = 1 + z * z / total
    middle = (p + z * z / (2 * total)) / scale
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total ** 2)) / scale
    return [max(0., middle - radius), min(1., middle + radius)]


def percentile(values, fraction):
    values = sorted(values)
    position = (len(values) - 1) * fraction
    low, high = math.floor(position), math.ceil(position)
    return values[low] + (position - low) * (values[high] - values[low])


def analyze(directory):
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    expected_ids = {t["case_id"] for t in manifest["tasks"]}
    assert manifest["schema"] == "public-endpoint-replay-v1"
    for name, expected in manifest["inputs"].items():
        assert sha(ROOT / name) == expected
    original_directory = ROOT / ("results/sp2027-repair-" + manifest["backend"])
    original = {r["case_id"]: r for r in map(
        json.loads, (original_directory / "runs.jsonl").read_text().splitlines())}
    original_manifest = json.loads((original_directory / "manifest.json").read_text())
    paths = sorted((directory / "cases").glob("*.json"))
    rows = [json.loads(p.read_text()) for p in paths]
    assert len(rows) == len(expected_ids)
    assert {r["case_id"] for r in rows} == expected_ids
    for row in rows:
        assert row["manifest_sha256"] == sha(manifest_path)
        for label in ["stego", "natural"]:
            arm = row[label]
            decision, endpoints, inspected, payloads = independent_decision(
                arm, manifest["parameters"]["known_segment_bytes"],
                manifest["parameters"]["guard_bits"])
            assert decision == arm["status"]
            assert endpoints == arm["segment_endpoints"]
            assert inspected == arm["tokens_inspected"]
            archived = original[row["case_id"]]
            if label == "natural":
                archived = archived["natural"]
            assert arm["text_sha256"] == hashlib.sha256(archived["cover_text"].encode()).hexdigest()
            assert arm["matches_archived_token_ids"] == (
                arm["visible_token_ids"] == archived["token_ids"])
            if label == "stego":
                # An after-decision fidelity check, never a classifier input
                # or an eligibility filter. No key or authentication call.
                recovered_hash = (hashlib.sha256(b"".join(payloads)).hexdigest()
                                  if len(payloads) == 2 else None)
                arm["reconstructed_packet_hash_matches_archive"] = (
                    recovered_hash == archived["attempts"][-1]["packet_sha256"])
            if label == "natural":
                old = archived["chosen_probabilities"]
                mismatches = [i for i, entry in enumerate(arm["trace"])
                              if "cdf_low" in entry and old[i] !=
                              (entry["cdf_high"] - entry["cdf_low"]) / entry["total_frequency"]]
                if "selected_mass_mismatch_indices" in arm:
                    assert mismatches == arm["selected_mass_mismatch_indices"]
                arm["selected_mass_mismatch_indices"] = mismatches
    families = sorted({r["family"] for r in rows})
    by_family = {}
    for family in families:
        subset = [r for r in rows if r["family"] == family]
        by_family[family] = {"pairs": len(subset), **{
            label: sum(r[label]["status"] == "endpoint_at_end" for r in subset)
            for label in ["stego", "natural"]}}
    rng = random.Random(20261028)
    estimates = {label: [] for label in ["stego", "natural"]}
    for _ in range(5000):
        sampled = [by_family[rng.choice(families)] for _ in families]
        denominator = sum(x["pairs"] for x in sampled)
        for label in estimates:
            estimates[label].append(sum(x[label] for x in sampled) / denominator)
    result = {
        "schema": "public-endpoint-analysis-v1", "backend": manifest["backend"],
        "manifest_sha256": sha(manifest_path),
        "cases_sha256": {p.name: sha(p) for p in paths},
        "analysis_source_sha256": sha(Path(__file__)),
        "pairs": len(rows), "families": len(families), "by_family": by_family,
        "same_thread_count_as_generation": (manifest["parameters"]["threads"] ==
                                           original_manifest["parameters"]["threads"]),
        "all_archived_token_ids_match": all(
            r[label]["matches_archived_token_ids"] for r in rows for label in ["stego", "natural"]),
        "natural_selected_mass_mismatch_count": sum(
            len(r["natural"]["selected_mass_mismatch_indices"]) for r in rows),
        "natural_inspected_mass_count": sum(len(r["natural"]["trace"]) for r in rows),
        "stego_reconstructed_packet_hash_matches": sum(
            r["stego"]["reconstructed_packet_hash_matches_archive"] for r in rows),
        "outcomes": {label: dict(Counter(r[label]["status"] for r in rows))
                     for label in ["stego", "natural"]},
        "rates": {},
        "per_pair": [{"case_id": r["case_id"], "family": r["family"], **{
            label: {k: r[label][k] for k in
                    ["status", "visible_tokens", "tokens_inspected", "segment_endpoints"]}
            for label in ["stego", "natural"]},
            "stego_packet_hash_matches": r["stego"]["reconstructed_packet_hash_matches_archive"],
            "natural_mass_mismatch_indices": r["natural"]["selected_mass_mismatch_indices"]}
                     for r in rows],
        "scope": ("Post-hoc first-prefix-resolution support test on the unchanged eligible "
                  "no-tail delivery slice. Known plaintext length is an additional public "
                  "assumption. Rates are conditional on earlier complete canonical controls; "
                  "all replay failures are retained. Family bootstrap resamples the saved "
                  "families (5000 draws, seed 20261028), not unseen deployment conditions. "
                  "An all-zero or all-one sample has a degenerate percentile interval, "
                  "which provides no calibrated bound on an unseen error probability. "
                  "Wilson intervals are nominal and ignore within-family dependence."),
    }
    for label in ["stego", "natural"]:
        hits = sum(r[label]["status"] == "endpoint_at_end" for r in rows)
        result["rates"][label] = {
            "hits": hits, "denominator": len(rows), "rate": hits / len(rows),
            "family_bootstrap_percentile_95": [
                percentile(estimates[label], .025), percentile(estimates[label], .975)],
            "nominal_wilson_95": nominal_wilson(hits, len(rows)),
        }
    result["source_replay_check_passed"] = (
        result["same_thread_count_as_generation"] and result["all_archived_token_ids_match"]
        and result["natural_selected_mass_mismatch_count"] == 0
        and result["stego_reconstructed_packet_hash_matches"] == len(rows))
    (directory / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    print(directory.name, result["pairs"], result["outcomes"],
          "source replay", result["source_replay_check_passed"])
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directories", nargs="+", type=Path)
    args = ap.parse_args()
    for directory in args.directories:
        analyze(directory)


if __name__ == "__main__":
    main()
