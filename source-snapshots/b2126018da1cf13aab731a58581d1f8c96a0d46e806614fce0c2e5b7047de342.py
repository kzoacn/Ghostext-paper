#!/usr/bin/env python3
"""Exact algebra checks for public endpoints and the ideal verified stopping proof."""
from __future__ import annotations
from collections import defaultdict
from fractions import Fraction as R
import hashlib
import itertools
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ((R(3, 4), R(1, 4)), (R(1, 2), R(1, 2)))


def inverse(value, history):
    for low, width, offset in reversed(history):
        value = low + (value - low - offset * width) % width
    return value


def half_down(value):
    value -= R(1, 2)
    return -((-value.numerator) // value.denominator)


def safe_interval_audit():
    rng = random.Random(20261027)
    counts = defaultdict(int)
    boundary_witness = None
    for bits in [1, 3, 6, 12]:
        for _ in range(60):
            message = rng.randrange(1 << bits)
            low, high, point = R(0), R(1 << bits), R(message)
            safe, history, state = R(1, 2), [], 0
            for depth in range(1, 21):
                width = high - low
                offset = R(rng.randrange(1 << 12), 1 << 12)
                history.append((low, width, offset))
                point = low + (point - low + offset * width) % width
                split = low + width * MATRIX[state][0]
                if point < split:
                    high, state = split, 0
                else:
                    low, state = split, 1
                old_safe = safe
                safe = min(safe, high - point)
                assert safe > 0
                for multiplier in [R(0), R(1, 7), R(1, 2), R(6, 7)]:
                    delta = safe * multiplier
                    assert inverse(point + delta, history) == message + delta
                    counts["exact_safe_interval_points"] += 1
                if boundary_witness is None and inverse(point + safe, history) != message + safe:
                    boundary_witness = {
                        "bits": bits, "message": message, "depth": depth,
                        "point": str(point), "safe_width": str(safe),
                        "right_endpoint_inverse": str(inverse(point + safe, history)),
                        "incorrect_closed_interval_value": str(message + safe),
                        "history": [[str(x) for x in h] for h in history],
                    }
                difference = (low + high) / 2 - point
                if 0 <= difference < old_safe:
                    assert -R(1, 2) < difference <= R(1, 2)
                    assert half_down(inverse((low + high) / 2, history)) == message
                    counts["sufficient_stops_recover"] += 1
                if not (0 <= difference < old_safe):
                    assert safe / (high - low) <= R(1, 2)
                    counts["failed_safe_event_normalized_width_checks"] += 1
    assert boundary_witness is not None
    return {**counts, "seed": 20261027, "right_endpoint_counterexample": boundary_witness,
            "scope": "Exact rational identities on fixed finite tapes; no finite-grid distribution theorem."}


def zero_varentropy_audit():
    counts = defaultdict(int)
    for bits in [1, 2]:
        for message in range(1 << bits):
            for tape in itertools.product([R(0), R(1, 4), R(1, 2), R(3, 4)], repeat=4):
                reference_decisions = None
                for branches in itertools.product([0, 1], repeat=4):
                    low, high, point = R(0), R(1 << bits), R(message)
                    history, uniforms, widths, decisions = [], [point / high], [high], []
                    state = 0
                    for branch, unit in zip(branches, tape, strict=True):
                        width = high - low
                        new_low = low + branch * width / 2
                        new_high = new_low + width / 2
                        new_point = new_low + unit * (new_high - new_low)
                        offset = ((new_point - point) / width) % 1
                        assert low + (point - low + offset * width) % width == new_point
                        history.append((low, width, offset))
                        low, high, point = new_low, new_high, new_point
                        uniforms.append(unit)
                        widths.append(high - low)
                        # Actual dependent three-state graph; order its two children.
                        state = sorted([state, (state + 1) % 3])[branch]
                        midpoint = (low + high) / 2
                        error = midpoint - point
                        direct = midpoint
                        for j in range(len(history), 0, -1):
                            parent_low, parent_width, parent_offset = history[j - 1]
                            direct = parent_low + (direct - parent_low -
                                                   parent_offset * parent_width) % parent_width
                            error = widths[j - 1] * (
                                (uniforms[j - 1] + error / widths[j - 1]) % 1 - uniforms[j - 1])
                        assert direct == message + error
                        counts["exact_reverse_error_identities"] += 1
                        candidate = -R(1, 2) < midpoint - point <= R(1, 2)
                        decisions.append((candidate, half_down(direct) == message))
                    if reference_decisions is None:
                        reference_decisions = decisions
                    assert decisions == reference_decisions
                    counts["complete_path_decision_checks"] += 1
    return {**counts, "source": "three-state stay-or-advance cycle, each edge 1/2",
            "scope": "Checks cancellation and branch independence on fixed normalized-point tapes."}


def two_step_kernel(rho, z):
    if z < rho * rho / 2:
        return rho / math.sqrt(z)
    if z < rho / 2:
        return math.sqrt(2) * (1 + rho / 2 - z / rho)
    return (1 + rho) / math.sqrt(2)


def kernel_audit():
    checks, worst = 0, 0.
    # Numerical integration is independent of the asserted piecewise expression.
    # Midpoint quadrature is applied after v=u^2, removing the square-root pole.
    import numpy as np
    grid = (np.arange(20000) + .5) / 20000 / math.sqrt(2)
    for rho in [.1, .25, .5, .75, .9, .99]:
        for z in [rho * rho / 8, rho * rho / 2, (rho * rho + rho) / 4, rho / 2, .5]:
            s = z / rho
            v = grid * grid
            arg = np.minimum(s, v)
            integrand = np.maximum(np.sqrt(rho / arg), math.sqrt(2)) * 2 * grid
            numeric = float(integrand.mean() / math.sqrt(2))
            numeric += max(0, .5 - s) * max(math.sqrt(rho / s), math.sqrt(2))
            exact = two_step_kernel(rho, z)
            assert abs(numeric - exact) < 2e-7, (rho, z, numeric, exact)
            checks += 1
        for z in np.geomspace(1e-12, .5, 10000):
            ratio = two_step_kernel(rho, float(z)) * math.sqrt(z)
            assert ratio <= (1 + rho) / 2 + 1e-13
            worst = max(worst, ratio / ((1 + rho) / 2))
            checks += 1
    # Exact polynomial factorization behind the middle-regime inequality.
    for rho in [R(i, 101) for i in range(1, 101)]:
        lhs = 27 * (1 + rho) ** 2 - 4 * rho * (2 + rho) ** 3
        rhs = (1 - rho) * (4 * rho ** 3 + 28 * rho ** 2 + 49 * rho + 27)
        assert lhs == rhs and rhs > 0
    return {"numeric_checks": checks, "exact_polynomial_checks": 100,
            "max_ratio_to_contraction_bound": worst,
            "scope": "Supplementary checks; the manuscript gives the analytic inequalities."}


def markov_parameters():
    pi = [R(2, 3), R(1, 3)]
    scores = [[-math.log2(float(p)) for p in row] for row in MATRIX]
    entropy = sum(float(pi[i] * MATRIX[i][j]) * scores[i][j]
                  for i in range(2) for j in range(2))
    variance = sum(float(pi[i] * MATRIX[i][j]) * (scores[i][j] - entropy) ** 2
                   for i in range(2) for j in range(2))
    lag_cov = sum(float(pi[i] * MATRIX[i][j] * MATRIX[j][k]) *
                  (scores[i][j] - entropy) * (scores[j][k] - entropy)
                  for i in range(2) for j in range(2) for k in range(2))
    sigma2 = variance + 2 * lag_cov / (1 - .25)
    a = math.log2(4 / 3)
    assert abs(entropy - (a / 2 + 2 / 3)) < 1e-14
    assert abs(sigma2 - (7 / 12 * a * a - 13 / 9 * a + 25 / 27)) < 1e-14
    bridges = []
    for i, j in itertools.product(range(2), repeat=2):
        left, right = MATRIX[i][0] * MATRIX[0][j], MATRIX[i][1] * MATRIX[1][j]
        theta = left / (left + right)
        gap = abs(math.log2(float(left / right)))
        bridges.append({"endpoints": [i, j], "theta": str(theta), "gap_bits": gap,
                        "conditional_variance": float(theta * (1 - theta)) * gap * gap,
                        "atom_constant": math.sqrt(math.pi) /
                        (2 * math.sqrt(2 * float(theta * (1 - theta))))})
    lower = 3 / 25 * math.log2(3 / 2) ** 2
    assert lag_cov > 0 and sigma2 > lower > 0
    assert abs(min(r["gap_bits"] for r in bridges) - math.log2(3 / 2)) < 1e-14
    assert abs(max(r["atom_constant"] for r in bridges) - 11 * math.sqrt(math.pi) / 12) < 1e-14
    # Explicit finite-B lower bound: conservative, often vacuous at small B.
    bounds = []
    for bits in [128, 512, 2048, 2 ** 20, 2 ** 30]:
        k = math.ceil(math.log2(bits))
        j = math.ceil(math.log(bits) / -math.log(7 / 8))
        width = k + 3 + 4 * j
        n0 = math.ceil((bits - k) / 2)
        alpha = min(1., 2 * (11 * math.sqrt(math.pi) / 12) *
                    (math.floor(width / math.log2(3 / 2)) + 1) /
                    math.sqrt(n0 // 2))
        delta = 4 * 2 ** -k + 4 * (7 / 8) ** j
        bounds.append({"bits": bits, "k": k, "j": j,
                       "verified_tv_lower_bound": max(0., 1 - delta - alpha)})
    return {"matrix": [[str(x) for x in row] for row in MATRIX], "initial_state": 0,
            "stationary_law": [str(x) for x in pi], "row_entropies": [
                sum(float(p) * s for p, s in zip(row, score, strict=True))
                for row, score in zip(MATRIX, scores, strict=True)],
            "entropy_rate": entropy, "stationary_lag_one_information_covariance": lag_cov,
            "varentropy_rate": sigma2, "certified_varentropy_lower_bound": lower,
            "bridges": bridges, "explicit_conservative_bounds": bounds}


def paths_at_depth(depth, matrix):
    stack = [((), 0, R(0), R(1))]
    for _ in range(depth):
        children = []
        for path, state, low, high in stack:
            cursor = low
            for symbol, probability in enumerate(matrix[state]):
                right = cursor + (high - low) * probability
                if probability:
                    children.append((path + (symbol,), symbol, cursor, right))
                cursor = right
        stack = children
    return stack


def resolved(low, high, bits):
    scale = 1 << bits
    # Exact half-open continuous interval: ceil(high*scale)-1 is final cell.
    a = low * scale
    b = high * scale
    return a.numerator // a.denominator == -((-b.numerator) // b.denominator) - 1


def endpoint_identity_audit():
    records = []
    for bits in [1, 2, 4]:
        for matrix in [MATRIX, ((R(1, 2), R(1, 2)),) * 2]:
            cap = 8
            stopped, lengths = {}, defaultdict(R)
            for depth in range(1, cap + 1):
                for path, _, low, high in paths_at_depth(depth, matrix):
                    if any(path[:j] in stopped for j in range(1, depth)):
                        continue
                    if depth == cap or resolved(low, high, bits):
                        stopped[path] = high - low
                        lengths[depth] += high - low
            assert sum(stopped.values()) == 1
            tv, fpr = R(0), R(0)
            for depth, length_mass in lengths.items():
                for path, _, low, high in paths_at_depth(depth, matrix):
                    reference = length_mass * (high - low)
                    tv += abs(stopped.get(path, 0) - reference) / 2
                    if path in stopped:
                        fpr += reference
            collision = sum(p * p for p in lengths.values())
            assert tv == 1 - collision and fpr == collision
            if matrix[0] == matrix[1]:
                assert tv == 0 and lengths == {bits: R(1)}
            fixed = []
            for depth in [bits, bits + 2, bits + 4]:
                leaves = paths_at_depth(depth, matrix)
                assert sum(high - low for _, _, low, high in leaves) == 1
                failure = sum(high - low for _, _, low, high in leaves
                              if not resolved(low, high, bits))
                for r in [0, 1, 2, 3]:
                    # I_N < B+r iff interval width > 2^-(B+r).
                    wide = sum(high - low for _, _, low, high in leaves
                               if high - low > R(1, 1 << (bits + r)))
                    assert failure <= wide + R(1, 1 << r)
                fixed.append({"tokens": depth, "prefix_recovery_failure": str(failure)})
            records.append({"bits": bits, "source": "dependent" if matrix == MATRIX else "uniform",
                            "public_cap": cap, "length_law": {n: str(p) for n, p in lengths.items()},
                            "exact_transcript_tv": str(tv), "endpoint_fpr": str(fpr),
                            "fixed_endpoint_failures": fixed})
    return records


def main():
    output = {
        "schema": "termination-theory-audit-v1",
        "scope": "Proof-support checks for specified ideal mechanisms, not numerical validation of a language-model limit.",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "safe_interval": safe_interval_audit(),
        "zero_varentropy": zero_varentropy_audit(),
        "killed_kernel": kernel_audit(),
        "markov_parameters": markov_parameters(),
        "public_endpoint_identity": endpoint_identity_audit(),
    }
    path = ROOT / "results/sp2027-termination-theory/summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n")
    print("Verified exact safe intervals, reverse-error cancellation, endpoint identities,",
          "fixed-endpoint failure bounds, and supplementary kernel/Markov calculations.")


if __name__ == "__main__":
    main()
