#!/usr/bin/env python3
"""Check pinned upstream verification and the observation/control harness."""
from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import torch

from upstream_rrc_experiment import load_core, sample_exact_boundary, traced_stepper

ROOT = Path(__file__).resolve().parents[1]


class BinaryModel:
    device = torch.device("cpu")
    config = SimpleNamespace(vocab_size=2)

    def __call__(self, input_ids, **kwargs):
        logits = torch.log(torch.tensor([.75, .25], dtype=torch.float64))
        return SimpleNamespace(
            logits=logits.reshape(1, 1, 2).repeat(1, input_ids.shape[1], 1),
            past_key_values=(),
        )


class RotationTape:
    def __init__(self, values):
        self.values = iter(values)

    def random(self):
        return next(self.values)


class BitTape:
    def __init__(self, prefix, high_suffix=False):
        self.prefix, self.high_suffix, self.first = prefix, high_suffix, True

    def getrandbits(self, bits):
        if self.first:
            assert bits == 64
            self.first = False
            return self.prefix
        return (1 << bits) - 1 if self.high_suffix else 0


def main():
    core, _, provenance = load_core()
    core.use_single_cpu_thread()
    core.set_precision(1)
    model, ctx = BinaryModel(), torch.tensor([[0]])
    fixtures = {}
    for verified in [False, True]:
        stepper = traced_stepper(core, model, 2)
        result = core.embed_message(stepper, ctx, "0", RotationTape([.5, .5]),
                                    2, max_tokens=2, verify=verified)
        stepper.finish(result["token_ids"])
        assert result["token_ids"] == ([0, 0] if verified else [0])
        assert result["extra_tokens"] == int(verified)
        receiver = traced_stepper(core, model, 2)
        try:
            recovered = core.extract_message(
                receiver, ctx, result["token_ids"], 1, RotationTape([.5, .5]), 2)
            recovered_correctly = recovered == "0"
            recovery_status = "complete"
        except core.RRCError as exc:
            recovered_correctly, recovery_status = False, type(exc).__name__
        assert recovered_correctly is verified
        assert all(Decimal(r["probability_decimal"]) == Decimal(".75")
                   for r in stepper.observations)
        fixtures[str(verified)] = {
            "token_ids": result["token_ids"], "rejected_stop_count": result["extra_tokens"],
            "receiver_status": recovery_status, "recovery_match": recovered_correctly,
        }
    # A non-dyadic boundary forces refinement of a straddling random-bit cell.
    boundary = "0.3333333333333333"
    fraction = Fraction(boundary)
    prefix = (fraction * (1 << 64)).numerator // (fraction * (1 << 64)).denominator
    dist = SimpleNamespace(boundaries=[0.0, float(boundary), 1.0])
    left, left_bits = sample_exact_boundary(dist, BitTape(prefix))
    right, right_bits = sample_exact_boundary(dist, BitTape(prefix, True))
    assert (left, right) == (0, 1)
    assert left_bits > 64 and right_bits > 64
    # No Decimal setting or observations may change the downloaded source.
    output = {
        "scope": "Unchanged pinned upstream functions with a synthetic binary model; no real-model claim.",
        "upstream": provenance, "verification_fixture": fixtures,
        "lazy_rational_sampler": {
            "boundary": boundary, "lower_branch": left, "upper_branch": right,
            "lower_bits": left_bits, "upper_bits": right_bits,
        },
        "source_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in [
                Path(__file__), ROOT / "scripts/upstream_rrc_experiment.py",
                ROOT / "scripts/fetch_upstream_rrc.py",
            ]
        },
    }
    destination = ROOT / "results/sp2027-upstream-audit/summary.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print("Upstream verification veto, independent extraction, trace masses, and lazy sampler passed.")


if __name__ == "__main__":
    main()
