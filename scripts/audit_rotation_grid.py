#!/usr/bin/env python3
"""Exact checks of finite-grid rotation against ideal midpoint stopping."""
from __future__ import annotations
from collections import Counter, defaultdict
from fractions import Fraction as R
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Q = [("A", R(3, 4)), ("B", R(1, 4))]


def discrete(message, tape, fail_aa):
    low, high, target, prefix = R(0), R(4), R(message), ""
    for offset in tape:
        if fail_aa and prefix == "AA":
            return "source_failure:" + prefix
        width = high - low
        target = low + (target - low + offset * width) % width
        cursor = low
        for symbol, probability in Q:
            right = cursor + width * probability
            if cursor <= target < right:
                low, high, prefix = cursor, right, prefix + symbol
                break
            cursor = right
        if -R(1, 2) < (low + high) / 2 - target <= R(1, 2):
            return "stop:" + prefix
    return "token_budget:" + prefix


def continuous(fail_aa):
    output = defaultdict(R)
    stack = [("", R(1), R(4))]
    while stack:
        prefix, mass, width = stack.pop()
        if fail_aa and prefix == "AA":
            output["source_failure:" + prefix] += mass
            continue
        if len(prefix) == 3:
            output["token_budget:" + prefix] += mass
            continue
        for symbol, probability in Q:
            new_width = width * probability
            hazard = min(R(1), 1 / new_width)
            output["stop:" + prefix + symbol] += mass * probability * hazard
            if hazard < 1:
                stack.append((prefix + symbol, mass * probability * (1 - hazard), new_width))
    assert sum(output.values()) == 1
    return output


def main():
    # For W=3, M=8, counts change only at the following grid-phase boundaries.
    width, grid = R(3), 8
    spacing = width / grid
    intervals = [(R(0), width * R(3, 4)), (width * R(3, 4), width)]
    endpoints = set()
    for low, high in intervals:
        mid = (low + high) / 2
        for x in [low, high, max(low, mid - R(1, 2)), min(high, mid + R(1, 2))]:
            endpoints.add(x % spacing)
    ordered = sorted(endpoints)
    phases = sorted(set(ordered + [(x + y) / 2 for x, y in
                                  zip(ordered, ordered[1:] + [spacing])]))
    max_errors = [R(0), R(0)]
    for phase in phases:
        points = [(phase + j * spacing) % width for j in range(grid)]
        for i, (low, high) in enumerate(intervals):
            selected = [x for x in points if low <= x < high]
            assert len(selected) == grid * Q[i][1]
            mid = (low + high) / 2
            accepted = sum(mid - R(1, 2) <= x < mid + R(1, 2) for x in selected)
            error = abs(R(accepted, len(selected)) - min(R(1), 1 / (high - low)))
            assert error < 1 / (grid * Q[i][1])
            max_errors[i] = max(max_errors[i], error)
    records = []
    for failure in [False, True]:
        ideal = continuous(failure)
        for message in range(4):
            counts = Counter(discrete(message, tape, failure)
                             for tape in itertools.product([R(i, grid) for i in range(grid)], repeat=3))
            observed = {key: R(value, grid ** 3) for key, value in counts.items()}
            tv = sum(abs(observed.get(k, 0) - ideal.get(k, 0))
                     for k in set(observed) | set(ideal)) / 2
            assert tv == R(1, 96)
            records.append({
                "fixed_message": message, "source_failure_at_active_AA": failure,
                "transcript_tv_exact": str(tv),
                "discrete": {k: str(v) for k, v in sorted(observed.items())},
                "continuous": {k: str(v) for k, v in sorted(ideal.items())},
            })
    result = {
        "scope": "Public token/stop/cap/failure transcript only; no private rotations, reverse-recovery flag, timing or conditioning.",
        "grid_size": grid, "cdf_denominator": 4, "message_bits": 2, "horizon": 3,
        "phase_representatives": [str(p) for p in phases],
        "maximum_conditional_hazard_errors": [str(x) for x in max_errors],
        "full_tape_enumerations": records,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    out = ROOT / "results/sp2027-rotation-grid/summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print("Exact grid audit:", len(phases), "phases;", len(records),
          "message/failure settings; every transcript TV = 1/96")


if __name__ == "__main__":
    main()
