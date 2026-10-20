"""Exact rational implementation of the published RRC rotation/stop rule.

This is an adapter to the shared Ghostext candidate source, not a reproduction
of the RRC paper's model/candidate configuration or its later verified release.
"""
from __future__ import annotations
from fractions import Fraction
import math
import random
from time import perf_counter

from ghostext.candidate_policy import select_candidates
from ghostext.config import CandidatePolicyConfig
from ghostext.errors import GhostextError
from ghostext.quantization import quantize_candidates


POLICY = CandidatePolicyConfig(top_p=.995, max_candidates=64, min_entropy_bits=0)


def next_q(backend, prompt, ids):
    raw = backend.distribution(prompt, ids, 7)
    selection = select_candidates(raw, POLICY, backend=backend, prompt=prompt,
                                  generated_token_ids=ids)
    return quantize_candidates(selection, 4096)


def recover_integer(low, high, history):
    point = (low + high) / 2
    for left, right, offset in reversed(history):
        width = right - left
        point = left + (point - left - offset * width) % width
    value = point - Fraction(1, 2)
    return -(-value.numerator // value.denominator)


def sample_text(backend, prompt, *, seed, bits=None, target_tokens=None,
                verify_before_stop=False):
    """RRC-paper if bits is set, otherwise independent fixed-length Q sampling."""
    rng = random.Random(seed)
    ids, probabilities, widths, history = [], [], [], []
    start = perf_counter()
    mode = "rrc_paper" if bits is not None else "matched_q_sampler"
    if bits is not None:
        low, high = Fraction(0), Fraction(1 << bits)
        target = Fraction(rng.getrandbits(bits))
        message_integer = int(target)
        max_tokens = 2 * bits  # Matches the pinned April RRC harness budget.
    else:
        max_tokens = target_tokens
    status, error = "token_budget", None
    for _ in range(max_tokens):
        try:
            q = next_q(backend, prompt, ids)
        except GhostextError as exc:
            status, error = type(exc).__name__, str(exc)
            break
        if bits is not None:
            width = high - low
            offset = Fraction(rng.getrandbits(192), 1 << 192)
            history.append((low, high, offset))
            target = low + (target - low + offset * width) % width
            selected = None
            for index, entry in enumerate(q.entries):
                lo = low + width * Fraction(entry.cdf_low, q.total_frequency)
                hi = low + width * Fraction(entry.cdf_high, q.total_frequency)
                if lo <= target < hi:
                    selected = index
                    low, high = lo, hi
                    break
            if selected is None:
                raise AssertionError("rotation point outside rational partition")
            widths.append(float(math.log2(high - low)))
        else:
            draw = rng.randrange(q.total_frequency)
            selected = next(i for i, entry in enumerate(q.entries) if draw < entry.cdf_high)
        entry = q.entries[selected]
        ids.append(entry.token_id)
        probabilities.append(entry.frequency / q.total_frequency)
        if bits is not None and -Fraction(1, 2) < (low + high) / 2 - target <= Fraction(1, 2):
            if not verify_before_stop or recover_integer(low, high, history) == message_integer:
                status = "complete"
                break
    if bits is None and len(ids) == target_tokens:
        status = "complete"
    text = backend.render(ids) if ids else ""
    canonical = backend.tokenize(text, prompt) == ids
    surprisal = -sum(math.log2(p) for p in probabilities)
    return {
        "mode": mode, "status": status, "error": error, "cover_text": text,
        "token_ids": ids, "chosen_probabilities": probabilities,
        "tokens": len(ids), "canonical_text_roundtrip": canonical,
        "surprisal_bits": surprisal, "interval_log2_widths": widths,
        "elapsed_seconds": perf_counter() - start,
        "verify_before_stop": verify_before_stop,
        "recovery_match": (
            recover_integer(low, high, history) == message_integer
            if bits is not None and status == "complete" else None
        ),
    }
