#!/usr/bin/env python3
"""Rational finite-size certificates for the ideal reverse-verified Markov rule.

No Monte Carlo, language-model inference, or floating probability arithmetic
enters the certificate. NumPy uint64 arrays store downward-rounded masses.
Their entire missing mass upper-bounds the error of every event. Fractions
retain the killed-kernel tail, residual-length bound, and final TV bound.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from fractions import Fraction as F
import hashlib
import json
from math import comb
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RHO = F(3, 4)
HALF = F(1, 2)
SCALE_BITS = 60
SCALE = 1 << SCALE_BITS
CASES = [(128, 8, 9), (512, 8, 9), (2048, 8, 12)]


def polynomial_value(coefficients, x):
    value = F(0)
    for coefficient in reversed(coefficients):
        value = value * x + coefficient
    return value


def polynomial_integral(coefficients, left, right):
    primitive = [F(0)] + [c / (i + 1) for i, c in enumerate(coefficients)]
    return polynomial_value(primitive, right) - polynomial_value(primitive, left)


def piecewise_value(pieces, x):
    for index, (left, right, coefficients) in enumerate(pieces):
        if left <= x < right or (index == len(pieces) - 1 and x == right):
            return polynomial_value(coefficients, x)
    raise ValueError("Point outside the safe-width domain")


def piecewise_integral(pieces, left, right):
    answer = F(0)
    for a, b, coefficients in pieces:
        lo, hi = max(left, a), min(right, b)
        if lo < hi:
            answer += polynomial_integral(coefficients, lo, hi)
    return answer


def killed_operator(pieces):
    """K_rho g(z)=G(min(z/rho,1/2))+(1-2z/rho)_+g(z/rho)."""
    result, cumulative = [], F(0)
    for left, right, coefficients in pieces:
        primitive = [F(0)] + [c / (i + 1) for i, c in enumerate(coefficients)]
        new = [F(0)] * (len(coefficients) + 1)
        new[0] = cumulative - polynomial_value(primitive, left)
        for degree, coefficient in enumerate(coefficients):
            new[degree] += coefficient
            new[degree + 1] += coefficient / (degree + 1) - 2 * coefficient
        # The polynomial above is in x=z/rho.
        new = [c / RHO**degree for degree, c in enumerate(new)]
        result.append((RHO * left, RHO * right, new))
        cumulative += polynomial_integral(coefficients, left, right)
    result.append((RHO * HALF, HALF, [cumulative]))
    return result


def safe_tail_bounds(maximum=24):
    pieces = [(F(0), HALF, [F(1)])]
    tails, checks = [], {"exact_continuities": 0, "direct_integral_recurrences": 0}
    for steps in range(maximum + 1):
        tail = 4 * piecewise_integral(pieces, F(0), F(1, 4))
        assert 0 <= tail <= 1
        tails.append(tail)
        for (_, boundary, left), (same, _, right) in zip(pieces, pieces[1:]):
            assert boundary == same
            assert polynomial_value(left, boundary) == polynomial_value(right, boundary)
            checks["exact_continuities"] += 1
        following = killed_operator(pieces)
        # A direct integral evaluation is independent of the polynomial assembly.
        points = {F(0), HALF, *[F(i, 40) for i in range(21)]}
        points.update((a + b) / 2 for a, b, _ in following)
        points.update(a for a, _, _ in following)
        for z in points:
            x = z / RHO
            value = piecewise_integral(pieces, F(0), min(x, HALF))
            if x < HALF:
                value += (1 - 2 * x) * piecewise_value(pieces, x)
            assert value == piecewise_value(following, z)
            checks["direct_integral_recurrences"] += 1
        pieces = following
    assert tails[:4] == [F(1), F(5, 6), F(37, 54), F(1999439, 3538944)]
    return tails, checks


def next_lower_masses(zero, one):
    """All operations are exact integers; discarded fractions are retained as deficit."""
    size = zero.shape[0] + 1
    next_zero = np.zeros((size, size), dtype=np.uint64)
    next_one = np.zeros_like(next_zero)
    # Each entry and total are <=2^60, so 3*entry is <2^62 and cannot overflow.
    next_zero[1:, :-1] = (3 * zero) >> 2
    next_zero[:-1, :-1] += one >> 1
    next_one[:-1, 1:] = zero >> 2
    next_one[:-1, :-1] += one >> 1
    return next_zero, next_one


def logarithm_floors(limit):
    power, values = 1, []
    for _ in range(limit + 1):
        values.append(power.bit_length() - 1)
        power *= 3
    return np.array(values, dtype=np.int64)


def band_membership(n, u, v, lower, upper):
    """Exact comparison for I=n+u+v-u log2(3), including u=0."""
    floor_log = (3**u).bit_length() - 1
    ceil_log = floor_log + int(u > 0)
    integer = n + u + v
    return integer - ceil_log >= lower and integer - floor_log <= upper


def event_lower_mass(zero, one, n, lower, upper, floors):
    u = np.arange(n + 1, dtype=np.int64)
    low_v = lower - n - u + floors[:n + 1] + (u > 0)
    high_v = upper - n - u + floors[:n + 1]
    v = low_v[:, None] + np.arange(upper - lower + 1, dtype=np.int64)[None, :]
    selected = (v >= 0) & (v <= n) & (v <= high_v[:, None])
    clipped = np.clip(v, 0, n)
    zero_sum = np.where(selected, zero[u[:, None], clipped], np.uint64(0)).sum(dtype=np.uint64)
    one_sum = np.where(selected, one[u[:, None], clipped], np.uint64(0)).sum(dtype=np.uint64)
    return int(zero_sum) + int(one_sum)


def path_multiplicity(n, state, u, v):
    """Independent run-composition formula for paths starting in state zero."""
    if v == 0:
        return int(state == 0 and u == n)
    x = n - u - 2 * v + state  # Number of 1->1 transitions.
    if x < 0:
        return 0
    if state == 0:
        return comb(u + v, v) * comb(x + v - 1, v - 1)
    return comb(u + v - 1, v - 1) * comb(x + v - 1, v - 1)


def exact_band_probability(n, lower, upper):
    """Exact independent probability at one length, denominator 4**n."""
    numerator, power_three = 0, 1
    for u in range(n + 1):
        floor_log = power_three.bit_length() - 1
        low_v = max(0, lower - n - u + floor_log + int(u > 0))
        high_v = min(n, upper - n - u + floor_log)
        for v in range(low_v, high_v + 1):
            for state in [0, 1]:
                multiplicity = path_multiplicity(n, state, u, v)
                if multiplicity:
                    assert n - u - v >= 0
                    numerator += (multiplicity * power_three) << (n - u - v)
        power_three *= 3
    result = F(numerator, 1 << (2 * n))
    assert 0 <= result <= 1
    return result


def small_exact_audit():
    zero, one = np.zeros((1, 1), dtype=np.uint64), np.zeros((1, 1), dtype=np.uint64)
    zero[0, 0] = SCALE
    exact = {(0, 0, 0): 1}
    counts = {(0, 0, 0): 1}
    floors = logarithm_floors(40)
    checked = {"statewise_lower_bounds": 0, "integer_band_memberships": 0,
               "event_upper_bounds": 0, "run_composition_counts": 0}
    for n in range(41):
        denominator = 1 << (2 * n)
        assert sum(exact.values()) == denominator
        total = int(zero.sum(dtype=np.uint64)) + int(one.sum(dtype=np.uint64))
        missing = SCALE - total
        assert 0 <= missing <= SCALE
        for (state, u, v), weight in exact.items():
            approximate = int((zero if state == 0 else one)[u, v])
            assert approximate * denominator <= weight * SCALE
            checked["statewise_lower_bounds"] += 1
            assert path_multiplicity(n, state, u, v) == counts[(state, u, v)]
            checked["run_composition_counts"] += 1
        for lower in [0, 8, 16, 24, 40]:
            upper, exact_event = lower + 3, 0
            for (state, u, v), weight in exact.items():
                integer = n + u + v
                direct = ((3**u) << lower) <= (1 << integer) <= ((3**u) << upper)
                assert direct == band_membership(n, u, v, lower, upper)
                checked["integer_band_memberships"] += 1
                if direct:
                    exact_event += weight
            approximate = event_lower_mass(zero, one, n, lower, upper, floors)
            assert approximate * denominator <= exact_event * SCALE
            assert exact_event * SCALE <= (approximate + missing) * denominator
            assert exact_band_probability(n, lower, upper) == F(exact_event, denominator)
            checked["event_upper_bounds"] += 1
        if n == 40:
            checked["missing_mass_at_40"] = str(F(missing, SCALE))
            break
        following, following_counts = defaultdict(int), defaultdict(int)
        for (state, u, v), weight in exact.items():
            count = counts[(state, u, v)]
            if state == 0:
                updates = [((0, u + 1, v), 3), ((1, u, v + 1), 1)]
            else:
                updates = [((0, u, v), 2), ((1, u, v), 2)]
            for key, multiplier in updates:
                following[key] += multiplier * weight
                following_counts[key] += count
        exact, counts = following, following_counts
        zero, one = next_lower_masses(zero, one)
    return checked


def decimal_down(value, digits=8):
    """A displayed lower bound must be rounded toward minus infinity."""
    factor = 10**digits
    integer = (value.numerator * factor) // value.denominator
    sign = "-" if integer < 0 else ""
    absolute = abs(integer)
    return f"{sign}{absolute // factor}.{absolute % factor:0{digits}d}"


def certify(bits, k, steps, tail, out_dir):
    lower, upper = bits - k, bits + 3 + 2 * steps
    cutoff = (3 * bits + 1) // 2 + 64
    zero, one = np.zeros((1, 1), dtype=np.uint64), np.zeros((1, 1), dtype=np.uint64)
    zero[0, 0] = SCALE
    floors = logarithm_floors(cutoff)
    scan, maximum_missing = [], 0
    for n in range(cutoff + 1):
        total = int(zero.sum(dtype=np.uint64)) + int(one.sum(dtype=np.uint64))
        missing = SCALE - total
        assert 0 <= missing <= SCALE
        maximum_missing = max(maximum_missing, missing)
        if 2 * n < lower:
            # Exact source support makes the event impossible.
            event, bound = 0, 0
        else:
            event = event_lower_mass(zero, one, n, lower, upper, floors)
            bound = min(SCALE, event + missing)
        scan.append({"length": n, "event_lower_numerator": str(event),
                     "missing_mass_numerator": str(missing),
                     "event_upper_numerator": str(bound)})
        if n < cutoff:
            zero, one = next_lower_masses(zero, one)
        if n and n % 800 == 0:
            print("B", bits, "certified through length", n, flush=True)
    best = max(scan, key=lambda row: int(row["event_upper_numerator"]))
    best_length = best["length"]
    finite_upper = F(int(best["event_upper_numerator"]), SCALE)
    # For all n>cutoff: Q(I_n<=upper)<=2**upper*(5/8)**n.
    remaining_upper = min(F(1), (F(2)**upper) * F(5, 8)**(cutoff + 1))
    exact_at_candidate = exact_band_probability(best_length, lower, upper)
    assert exact_at_candidate <= finite_upper
    other_upper = max(
        F(max(int(row["event_upper_numerator"]) for row in scan if row["length"] != best_length), SCALE),
        remaining_upper)
    exact_maximum_certified = other_upper <= exact_at_candidate
    natural_upper = exact_at_candidate if exact_maximum_certified else max(finite_upper, remaining_upper)
    early = F(4, 1 << k)
    raw_lower = 1 - early - tail - natural_upper
    tv_lower = max(F(0), raw_lower)
    scan_path = out_dir / f"band-scan-b{bits}-k{k}-m{steps}.json"
    scan_path.write_text(json.dumps({
        "schema": "verified-markov-band-scan-v1", "bits": bits, "k": k, "steps": steps,
        "band": [lower, upper], "fixed_point_denominator": str(SCALE), "scan": scan,
    }, indent=2) + "\n")
    return {
        "bits": bits, "k": k, "steps": steps, "band": [lower, upper], "cutoff": cutoff,
        "early_stop_upper": str(early), "verified_survival_upper": str(tail),
        "finite_scan_upper": str(finite_upper), "argmax_length": best_length,
        "exact_probability_at_candidate": str(exact_at_candidate),
        "other_lengths_upper": str(other_upper),
        "all_lengths_exact_maximum_certified": exact_maximum_certified,
        "beyond_cutoff_upper": str(remaining_upper),
        "natural_band_upper": str(natural_upper),
        "maximum_missing_mass": str(F(maximum_missing, SCALE)),
        "unclipped_tv_lower": str(raw_lower), "tv_lower": str(tv_lower),
        "tv_lower_decimal_rounded_down": decimal_down(tv_lower),
        "scan_file": scan_path.name,
        "scan_sha256": hashlib.sha256(scan_path.read_bytes()).hexdigest(),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "results/sp2027-verified-certificate")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    tails, kernel_checks = safe_tail_bounds()
    exact_checks = small_exact_audit()
    certificates = []
    for bits, k, steps in CASES:
        result = certify(bits, k, steps, tails[steps], args.out_dir)
        certificates.append(result)
        print("B", bits, "TV >=", result["tv_lower_decimal_rounded_down"],
              "exact natural maximum certified", result["all_lengths_exact_maximum_certified"], flush=True)
    output = {
        "schema": "finite-verified-stopping-certificate-v1",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_matrix": [["3/4", "1/4"], ["1/2", "1/2"]], "initial_state": 0,
        "safe_entry_submeasure_cdf_upper": "min(1,4*u), without survival normalization",
        "kernel": "K_rho g(z)=integral_0^min(z/rho,1/2)g(v)dv+(1-2z/rho)_+g(z/rho)",
        "survival_bounds": {str(m): str(tail) for m, tail in enumerate(tails)},
        "kernel_checks": kernel_checks, "small_exact_checks": exact_checks,
        "certificates": certificates,
        "scope": (
            "Rigorous lower bounds for ideal, uncapped, exact-real reverse verification "
            "with independent continuous rotations and the stated Markov source. "
            "Safe-rule tails are upper bounds, not actual verified tails. "
            "No transfer to finite rotations, Decimal, PRNGs, LLMs, or rendered strings."
        ),
    }
    (args.out_dir / "summary.json").write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    main()
