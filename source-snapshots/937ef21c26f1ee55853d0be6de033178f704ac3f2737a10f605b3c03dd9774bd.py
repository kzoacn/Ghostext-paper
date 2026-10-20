#!/usr/bin/env python3
"""Deterministic IID stopping-law checks, with a uniform-source negative control."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np


def step(weights, p):
    result = np.zeros(len(weights) + 1)
    result[:-1] += p * weights
    result[1:] += (1 - p) * weights
    return result


def evaluate(bits, p, band_back=8):
    # Index k counts the less likely symbol; p >= 1/2 throughout this study.
    a, b = -math.log2(p), -math.log2(1 - p)
    active, natural = np.ones(1), np.ones(1)
    total, stego_band, control_band, count_length_tv = 0., 0., 0., 0.
    mean_length, length_mass = 0., []
    # Every possible path has reached S >= B by this finite horizon.
    for n in range(1, math.ceil(bits / a) + 2):
        active, natural = step(active, p), step(natural, p)
        surprisal = n * a + np.arange(n + 1) * (b - a)
        hazards = np.exp2(np.minimum(0., surprisal - bits))
        stopped = active * hazards
        mass = float(stopped.sum())
        event = (surprisal >= bits - band_back) & (surprisal <= bits + b)
        stego_band += float(stopped[event].sum())
        control_band += mass * float(natural[event].sum())
        count_length_tv += float(np.abs(stopped - mass * natural).sum()) / 2
        total += mass
        mean_length += n * mass
        length_mass.append(mass)
        active *= 1 - hazards
    assert abs(total - 1) < 2e-12, total
    assert float(active.sum()) < 2e-12
    assert abs(float(natural.sum()) - 1) < 2e-12
    if p == .5:
        assert count_length_tv < 2e-12
        assert abs(stego_band - control_band) < 2e-12
    # Constants in the proof; the loose closed-form bound need not be positive.
    k = math.log2(bits)
    if p != .5:
        aa = 1 / (1 - 2 ** -a)
        mp = math.sqrt(math.pi) / (2 * math.sqrt(2 * p * (1 - p)))
        proof_bound = max(0., 1 - aa * 2 ** -k - aa * 2 ** (-bits / 2)
                          - mp * math.sqrt(2 * b / bits) * (math.floor((k + b) / (b - a)) + 1))
    else:
        proof_bound = None
    return {
        "message_bits": bits, "p_A": p, "total_stopped_mass": total,
        "unresolved_mass": float(active.sum()), "mean_length": mean_length,
        "band": [bits - band_back, bits + b],
        "stego_band_probability": stego_band, "control_band_probability": control_band,
        "band_event_advantage": stego_band - control_band,
        "count_and_length_tv": count_length_tv, "closed_form_proof_bound": proof_bound,
        "length_mass": length_mass,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path("results/sp2027-stopping-dp/summary.json"))
    args = ap.parse_args()
    results = [evaluate(bits, p) for p in [.5, .75]
               for bits in [8, 32, 64, 128, 256, 512, 1024, 2048]]
    output = {
        "method": "Float64 dynamic program over (length, number of rare symbols), without sampling.",
        "scope": "Published ideal midpoint hazard on IID sources; not an LLM or revised RRC implementation.",
        "control": "Exact stopping-length marginal with independent fresh IID content.",
        "tv_scope": "Count-and-length TV is a lower bound on full ordered-transcript TV.",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    for row in results:
        print(row["p_A"], row["message_bits"], "band advantage",
              round(row["band_event_advantage"], 6), "count/length TV",
              round(row["count_and_length_tv"], 6))


if __name__ == "__main__":
    main()
