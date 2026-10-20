#!/usr/bin/env python3
"""Exhaust finite rotation tapes to validate the optional stopping ablation."""
from __future__ import annotations
from collections import Counter
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "Ghostext/src"))
from ghostext.model_backend import TokenProb
from stopping_experiment import sample_text


class BinaryBackend:
    def __init__(self, p):
        self.p = p

    def distribution(self, prompt, ids, seed):
        return [TokenProb("A", 0, self.p), TokenProb("B", 1, 1 - self.p)]

    def render(self, ids):
        return "".join("AB"[i] for i in ids)

    def tokenize(self, text, prompt):
        return ["AB".index(c) for c in text]


class TapeRandom:
    def __init__(self, message, offsets):
        self.message, self.offsets, self.first = message, iter(offsets), True

    def getrandbits(self, bits):
        if self.first:
            self.first = False
            assert self.message < (1 << bits)
            return self.message
        value = Fraction(next(self.offsets)) * (1 << bits)
        assert value.denominator == 1
        return int(value)


def run(bits, p, message, offsets, verified):
    with patch("stopping_experiment.random.Random",
               lambda seed: TapeRandom(message, offsets)):
        result = sample_text(BinaryBackend(p), "public", seed=0, bits=bits,
                             verify_before_stop=verified)
    return {k: result[k] for k in [
        "cover_text", "tokens", "status", "recovery_match", "mode",
        "first_candidate_stop_tokens", "rejected_stop_count"]}


def exhaustive(bits, p, denominator):
    laws = [Counter(), Counter()]
    failures = [Counter(), Counter()]
    prefixes = unchanged = tapes = 0
    offsets = [Fraction(i, denominator) for i in range(denominator)]
    for message in range(1 << bits):
        for tape in itertools.product(offsets, repeat=2 * bits):
            pair = [run(bits, p, message, tape, flag) for flag in [False, True]]
            for index, result in enumerate(pair):
                laws[index][(result["status"], result["cover_text"])] += 1
                failures[index][f'{result["status"]}/recovery={result["recovery_match"]}'] += 1
            assert pair[1]["cover_text"].startswith(pair[0]["cover_text"])
            prefixes += 1
            if pair[0]["recovery_match"] is True:
                assert pair[0]["cover_text"] == pair[1]["cover_text"]
                assert pair[0]["status"] == pair[1]["status"]
                unchanged += 1
            tapes += 1
    return {
        "bits": bits, "p_A": p, "offset_grid_denominator": denominator, "tapes": tapes,
        "prefix_checks": prefixes, "already_recoverable_unchanged_checks": unchanged,
        "laws": [{f"{s}:{y}": str(Fraction(count, tapes))
                  for (s, y), count in sorted(law.items())} for law in laws],
        "outcomes": [dict(c) for c in failures],
    }


def main():
    uniform = exhaustive(2, .5, 4)
    expected = {"complete:A": "1/4", "complete:B": "1/4",
                **{f"complete:{s}": "1/8" for s in ["AA", "AB", "BA", "BB"]}}
    assert uniform["laws"] == [expected, expected]
    small_uniform = exhaustive(1, .5, 8)
    failed = run(1, .75, 0, [Fraction(1, 2)] * 2, False)
    repaired = run(1, .75, 0, [Fraction(1, 2)] * 2, True)
    assert (failed["cover_text"], failed["recovery_match"]) == ("A", False)
    assert (repaired["cover_text"], repaired["recovery_match"]) == ("AA", True)
    accepted_tie = run(1, .75, 0, [Fraction(1, 8), Fraction(1, 2)], False)
    rejected_tie = run(1, .75, 0, [Fraction(5, 8), Fraction(1, 2)], False)
    assert accepted_tie["tokens"] == 1
    assert rejected_tie["tokens"] > 1
    output = {
        "scope": "Exact finite-tape checks of our rational adapter; not continuous rotations or upstream numerical code.",
        "uniform_negative_control": uniform, "finer_uniform_budget_control": small_uniform,
        "reverse_failure_fixture": {"published_rule": failed, "verified_rule": repaired},
        "half_unit_ties": {"positive_half_accepted": accepted_tie, "negative_half_rejected": rejected_tie},
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [Path(__file__), ROOT / "scripts/stopping_experiment.py"]},
    }
    destination = ROOT / "results/sp2027-stopping-adapter/summary.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({k: v for k, v in output.items() if k != "source_sha256"}, indent=2))


if __name__ == "__main__":
    main()
