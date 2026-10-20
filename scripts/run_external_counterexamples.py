#!/usr/bin/env python3
"""Pinned NLS source execution and exact RRC-paper stopped-law counterexample."""
from __future__ import annotations
import argparse
import ast
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import urllib.request

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
NLS_COMMIT = "05a3944f2bc71eb252ef600c5b80a15f98fea425"


def fetch_nls(name):
    url = f"https://raw.githubusercontent.com/harvardnlp/NeuralSteganography/{NLS_COMMIT}/{name}"
    cache = ROOT / "tmp/primary-source" / NLS_COMMIT / name
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=60) as response:
            cache.write_bytes(response.read())
    return url, cache.read_text()


def original_nls_counterexample():
    torch.set_num_threads(1)
    namespace = {"torch": torch, "F": F, "np": np, "math": math}
    dependencies = {"limit_past", "kl", "entropy", "bits2int", "int2bits",
                    "is_sent_finish", "num_same_from_beg"}
    sources = []
    for filename, functions in [
        ("utils.py", dependencies), ("arithmetic.py", {"encode_arithmetic"})
    ]:
        url, source = fetch_nls(filename)
        tree = ast.parse(source)
        extracted = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in functions]
        assert {node.name for node in extracted} == functions
        # Run unchanged function definitions only. Repository import-time code
        # and model-download helpers are not executed or copied into this repo.
        exec(compile(ast.Module(body=extracted, type_ignores=[]), url, "exec"), namespace)
        sources.append({"url": url, "sha256": hashlib.sha256(source.encode()).hexdigest(),
                        "functions_executed_unchanged": sorted(functions)})

    class ToyModel:
        def __call__(self, x, past=None):
            logits = torch.full((1, x.shape[-1], 1024), -1e20)
            logits[:, :, :64] = 0
            return logits, []

    class ToyTokenizer:
        def decode(self, ids):
            # An injective synthetic text channel, including the context token.
            return "".join(chr(0x400 + int(token)) for token in ids)

        def encode(self, text):
            return [ord(symbol) - 0x400 for symbol in text]

    endings = Counter()
    lengths = Counter()
    texts = Counter()
    reported_kl = []
    for value in range(256):
        bits = [int(c) for c in f"{value:08b}"]
        tokens, _, kl, _, _ = namespace["encode_arithmetic"](
            ToyModel(), ToyTokenizer(), bits, [800], finish_sent=False,
            device="cpu", precision=16, topk=64,
        )
        endings[tokens[-1]] += 1
        lengths[len(tokens)] += 1
        text = ToyTokenizer().decode(tokens)
        assert ToyTokenizer().encode(text) == list(tokens)
        texts[text] += 1
        reported_kl.append(float(kl))
    tv = sum(abs(Fraction(endings[token], 256) - Fraction(1, 64)) for token in range(64)) / 2
    assert lengths == {2: 256}
    assert sorted(endings.values()) == [64] * 4
    assert tv == Fraction(15, 16)
    assert set(reported_kl) == {0.}
    text_tv = sum(abs(Fraction(texts[ToyTokenizer().decode(pair)], 256) - Fraction(1, 4096))
                  for pair in itertools.product(range(64), repeat=2)) / 2
    assert len(texts) == 256 and text_tv == Fraction(15, 16)
    return {
        "scope": "Unmodified original NLS coding function on synthetic logits; not a GPT-2 attack.",
        "sources": sources, "message_bits": 8, "messages_enumerated": 256,
        "precision": 16, "active_uniform_tokens": 64, "topk": 64, "finish_sent": False,
        "output_length_histogram": dict(lengths),
        "terminal_token_histogram": dict(endings),
        "terminal_tv_exact": str(tv), "reported_average_kl_max": max(reported_kl),
        "rendering": "Injective Unicode symbols: token t maps to chr(0x400+t).",
        "distinct_stego_texts": len(texts), "natural_two_symbol_texts": 4096,
        "complete_text_tv_exact": str(text_tv),
        "rendered_text_histogram": dict(sorted(texts.items())),
    }


def rrc_stopped_law(probabilities, payload_bits):
    stack = [("", Fraction(1), Fraction(1 << payload_bits))]
    stopped = defaultdict(Fraction)
    while stack:
        prefix, mass, width = stack.pop()
        for token, prob in probabilities.items():
            path = prefix + token
            next_width = width * prob
            hazard = min(Fraction(1), 1 / next_width)
            stopped[path] += mass * prob * hazard
            if hazard < 1:
                stack.append((path, mass * prob * (1 - hazard), next_width))
    assert sum(stopped.values()) == 1
    return dict(stopped)


def rrc_exact_counterexample():
    probabilities = {"A": Fraction(3, 4), "B": Fraction(1, 4)}
    stopped = rrc_stopped_law(probabilities, 1)
    lengths = defaultdict(Fraction)
    for path, mass in stopped.items():
        lengths[len(path)] += mass
    reference = {}
    for length, length_mass in lengths.items():
        for tokens in itertools.product(probabilities, repeat=length):
            path = "".join(tokens)
            reference[path] = length_mass * math.prod(probabilities[t] for t in tokens)
    tv = sum(abs(stopped.get(s, 0) - reference.get(s, 0)) for s in set(stopped) | set(reference)) / 2
    assert stopped == {"A": Fraction(1, 2), "B": Fraction(1, 4), "AA": Fraction(1, 6),
                       "AB": Fraction(1, 16), "AAA": Fraction(1, 64), "AAB": Fraction(1, 192)}
    assert tv == Fraction(33, 256)
    return {
        "scope": "Published RRC Algorithm 3 with ideal independent uniform rotations, not revised verify-before-stop source.",
        "paper": "https://aclanthology.org/2026.acl-long.39.pdf",
        "message_bits": 1, "probabilities": {k: str(v) for k, v in probabilities.items()},
        "stopped_distribution": {k: str(v) for k, v in sorted(stopped.items())},
        "length_distribution": {k: str(v) for k, v in sorted(lengths.items())},
        "reference": "Independent natural sampling with exactly the same marginal length distribution",
        "reference_distribution": {k: str(v) for k, v in sorted(reference.items())},
        "transcript_tv_exact": str(tv),
        "event_complete_output_B_advantage_exact": str(stopped["B"] - reference["B"]),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "results/sp2027-external-audit")
    args = ap.parse_args()
    summary = {"nls": original_nls_counterexample(), "rrc_paper": rrc_exact_counterexample(),
               "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
