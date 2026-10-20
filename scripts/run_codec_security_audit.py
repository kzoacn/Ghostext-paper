#!/usr/bin/env python3
"""Exact finite-source distribution enumeration; no language model is used."""
from __future__ import annotations
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "Ghostext/src"))
from ghostext.candidate_policy import select_candidates
from ghostext.codec import interval_rounding_tv
from ghostext.config import CandidatePolicyConfig
from ghostext.model_backend import TokenProb
from ghostext.quantization import quantize_candidates


def make_q(probs, total=4096):
    selection = select_candidates(
        [TokenProb(str(i), i, p) for i, p in enumerate(probs)],
        CandidatePolicyConfig(top_p=1.0, max_candidates=len(probs), min_entropy_bits=0,
                              enforce_retokenization_stability=False),
    )
    return quantize_candidates(selection, total)


def exact_tree(models, payload_bits, guard_bits, horizon=32):
    """Enumerate every nonzero integer-source path and every invalid Q branch.

    Reference sampler follows f/F with the same public interval updates and
    prefix stopping rule. An invalid zero-width branch is an absorbing event,
    never conditioned away. Both laws are capped at the same token horizon.
    """
    domain = 1 << (payload_bits + guard_bits)
    stack = [(0, domain, 0, 0, Fraction(1))]
    twice_tv = Fraction(0)
    invalid_mass = Fraction(0)
    unresolved_mass = Fraction(0)
    max_rounding_tv = Fraction(0)
    nodes = leaves = 0
    while stack:
        low, high, depth, state, ref_mass = stack.pop()
        nodes += 1
        width = high - low
        resolved = low >> guard_bits == (high - 1) >> guard_bits
        if resolved or depth == horizon:
            leaves += 1
            actual_mass = Fraction(width, domain)
            twice_tv += abs(actual_mass - ref_mass)
            if not resolved:
                unresolved_mass += actual_mass
            continue
        q = models[state % len(models)]
        max_rounding_tv = max(max_rounding_tv, interval_rounding_tv(low, high, q))
        for index, entry in enumerate(q.entries):
            lo = low + width * entry.cdf_low // q.total_frequency
            hi = low + width * entry.cdf_high // q.total_frequency
            mass = ref_mass * Fraction(entry.frequency, q.total_frequency)
            if hi == lo:
                invalid_mass += mass
                twice_tv += mass
            else:
                stack.append((lo, hi, depth + 1, state + index, mass))
    n = max(len(q.entries) for q in models)
    bound = min(Fraction(1), Fraction(horizon * n, 1 << (guard_bits + 1)))
    tv = twice_tv / 2
    assert tv <= bound
    return {
        "payload_bits": payload_bits, "guard_bits": guard_bits, "horizon": horizon,
        "nodes_enumerated": nodes, "terminal_paths": leaves,
        "transcript_tv": float(tv),
        "transcript_tv_exact": str(tv),
        "reference_invalid_probability": float(invalid_mass),
        "coded_horizon_exhaustion_probability": float(unresolved_mass),
        "max_local_rounding_tv": float(max_rounding_tv),
        "coding_only_tv_bound": float(bound),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "results/sp2027-codec-audit")
    args = ap.parse_args()
    cases = {
        "uniform64": [make_q([1 / 64] * 64)],
        "skew3": [make_q([.61, .28, .11])],
        "context_dependent": [make_q([.61, .28, .11]), make_q([.1, .2, .3, .4])],
    }
    rows = []
    for name, models in cases.items():
        for g in [0, 2, 4, 8, 16, 32, 64, 128]:
            result = exact_tree(models, payload_bits=8, guard_bits=g)
            rows.append({"case": name, **result})
            print(name, g, "TV", result["transcript_tv"], "invalid", result["reference_invalid_probability"], flush=True)
    legacy = next(r for r in rows if r["case"] == "uniform64" and r["guard_bits"] == 0)
    guarded = next(r for r in rows if r["case"] == "uniform64" and r["guard_bits"] == 4)
    assert legacy["transcript_tv_exact"] == "15/16"
    assert guarded["transcript_tv_exact"] == "0"
    q = make_q([1 - 63e-9] + [1e-9] * 63)
    quant_tv = sum(abs(e.probability - e.frequency / q.total_frequency) for e in q.entries) / 2
    summary = {
        "method": "Exact rational enumeration of complete stopped transcript laws, including reference invalid paths.",
        "reference": "f/F sampler with identical public prefix stopping, not ordinary EOS-terminated LLM text.",
        "source": "Uniform payload and independent uniform guard bits; not a cryptographic packet assumption.",
        "code_sha256": hashlib.sha256((ROOT.parent / "Ghostext/src/ghostext/codec.py").read_bytes()).hexdigest(),
        "results": rows,
        "historical_quantization_bound_counterexample": {
            "candidate_count": 64, "total_frequency": 4096,
            "actual_tv": quant_tv, "invalid_old_bound": 64 / 8192,
        },
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
