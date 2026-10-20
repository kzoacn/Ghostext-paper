#!/usr/bin/env python3
"""Study the RRC paper's ideal stopped law under a fixed binary source."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score
from audit_existing_evidence import wilson

ROOT = Path(__file__).resolve().parents[1]


def sample_stopped(n, bits, p, rng):
    surprisal = np.zeros(n)
    lengths = np.zeros(n, dtype=int)
    alive = np.ones(n, dtype=bool)
    information = np.array([-math.log2(p), -math.log2(1 - p)])
    while alive.any():
        indices = np.flatnonzero(alive)
        choices = (rng.random(len(indices)) >= p).astype(int)
        surprisal[indices] += information[choices]
        lengths[indices] += 1
        hazard = np.exp2(np.minimum(0, surprisal[indices] - bits))
        stop = rng.random(len(indices)) < hazard
        alive[indices[stop]] = False
    return lengths, surprisal


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--samples", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=20261020)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "results/sp2027-stopping-simulation")
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    p = .75
    a, b = -math.log2(p), -math.log2(1 - p)
    rows = []
    arrays = {}
    for bits in [8, 32, 128, 512, 2048]:
        lengths, stego_surprisal = sample_stopped(args.samples, bits, p, rng)
        # Permutation gives exactly matched empirical lengths, independent
        # fresh content. Classifier receives only full-text surprisal and B.
        natural_lengths = rng.permutation(lengths)
        natural_a_count = rng.binomial(natural_lengths, p)
        natural_surprisal = natural_a_count * a + (natural_lengths - natural_a_count) * b
        stego_score = -np.abs(stego_surprisal - bits)
        natural_score = -np.abs(natural_surprisal - bits)
        auc = roc_auc_score(np.r_[np.ones(args.samples), np.zeros(args.samples)],
                            np.r_[stego_score, natural_score])
        stego_hits = (stego_surprisal >= bits - 8) & (stego_surprisal <= bits + b + 1e-8)
        natural_hits = (natural_surprisal >= bits - 8) & (natural_surprisal <= bits + b + 1e-8)
        rows.append({
            "message_bits": bits, "n_per_class": args.samples, "p_A": p,
            "mean_tokens": float(lengths.mean()), "auc_capacity_gap": float(auc),
            "preregistered_band": [bits - 8, bits + b],
            "stego_band_rate": float(stego_hits.mean()),
            "natural_band_rate": float(natural_hits.mean()),
            "stego_band_wilson_95": wilson(int(stego_hits.sum()), args.samples),
            "natural_band_wilson_95": wilson(int(natural_hits.sum()), args.samples),
            "theoretical_stego_band_lower_bound": max(0, 1 - 2**-8 / (1 - p)),
        })
        arrays[f"b{bits}_stego_tokens"] = lengths
        arrays[f"b{bits}_stego_surprisal"] = stego_surprisal
        arrays[f"b{bits}_natural_tokens"] = natural_lengths
        arrays[f"b{bits}_natural_surprisal"] = natural_surprisal
        print(bits, auc, stego_hits.mean(), natural_hits.mean(), flush=True)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.out_dir / "samples.npz", **arrays)
    summary = {
        "scope": "Monte Carlo of the ideal published RRC stopping law on an IID binary source; not an LLM experiment.",
        "seed": args.seed, "score": "-abs(total surprisal in bits - known message length in bits)",
        "results": rows,
    }
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
