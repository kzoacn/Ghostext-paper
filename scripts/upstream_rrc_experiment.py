"""Observation harness for unchanged pinned upstream RRC functions.

The fixed-endpoint and natural controls are separate routines. The upstream
encoder, receiver, numerical primitives, and model stepper are never patched.
"""
from __future__ import annotations

import csv
from decimal import Decimal, getcontext
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
from time import perf_counter

from artifact_utils import deterministic_seed
from fetch_upstream_rrc import fetch

SELECTION_LABEL = "ghostext-upstream-confirmatory-20261021-v1"
EXPERIMENT_SEED = 20261025
BOOTSTRAP_SEED = 20261026


def load_core(destination=None):
    source, provenance = fetch() if destination is None else fetch(destination)
    spec = importlib.util.spec_from_file_location("audited_upstream_rrc", source / "rrc_core.py")
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    return core, source, provenance


def select_prompts(source):
    with (Path(source) / "0.Prompts.tsv").open(newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    unique, seen = [], set()
    for row in sorted(rows, key=lambda r: int(r["idx"])):
        if row["text"].strip() in seen:
            continue
        seen.add(row["text"].strip())
        payload = json.dumps([SELECTION_LABEL, int(row["idx"]), row["text"]],
                             ensure_ascii=False, separators=(",", ":"))
        unique.append({
            "prompt_id": f"c4_{int(row['idx']):04d}", "source_row": int(row["idx"]),
            "prompt": row["text"],
            "selection_sha256": hashlib.sha256(payload.encode()).hexdigest(),
        })
    ordered = sorted(unique, key=lambda r: r["selection_sha256"])
    selected = [{**row, "split": "development" if i < 10 else "test"}
                for i, row in enumerate(ordered[:20])]
    pilots = [{**row, "split": "pilot"} for row in ordered[20:22]]
    return selected, pilots, {"released_rows": len(rows), "distinct_prompt_texts": len(unique)}


def secret_and_key(case_id, bits, *, exogenous=False):
    prefix = "exogenous" if exogenous else "stopped"
    secret_rng = random.Random(deterministic_seed(
        "upstream", EXPERIMENT_SEED, prefix, case_id, "secret"))
    secret = format(secret_rng.getrandbits(bits), f"0{bits}b")
    key = deterministic_seed("upstream", EXPERIMENT_SEED, prefix, case_id, "rotation")
    return secret, key


def boundary_mass(dist, token_id):
    index = dist.index_of(int(token_id))
    if index < 0:
        raise ValueError("Observed token absent from upstream candidate list")
    low, high = str(dist.boundaries[index]), str(dist.boundaries[index + 1])
    mass = Decimal(high) - Decimal(low)
    if mass <= 0:
        raise ValueError("Selected upstream interval has nonpositive mass")
    return {"token_id": int(token_id), "cdf_low": low, "cdf_high": high,
            "probability_decimal": str(mass)}


def traced_stepper(core, model, vocab_size, max_ctx_len=900):
    class TracedStepper(core.LMStepper):
        def __init__(self):
            super().__init__(model, vocab_size, max_ctx_len=max_ctx_len)
            self.observations, self.pending, self.trim_calls = [], None, 0

        def distribution(self, top_k):
            result = super().distribution(top_k)
            self.pending = result
            return result

        def step(self, token_id):
            self.observations.append(boundary_mass(self.pending, token_id))
            if self._cached_len > self.max_ctx_len:
                self.trim_calls += 1
            super().step(token_id)

        def finish(self, ids):
            if len(ids) == len(self.observations) + 1:
                self.observations.append(boundary_mass(self.pending, ids[-1]))
            if [r["token_id"] for r in self.observations] != list(ids):
                raise AssertionError("Instrumentation lost an upstream token")

    return TracedStepper()


def exception_prefix(exc, function_name):
    """Recover an unreturned failed prefix without altering upstream code."""
    trace = exc.__traceback__
    while trace:
        if trace.tb_frame.f_code.co_name == function_name:
            state = trace.tb_frame.f_locals
            return list(state.get("generated", [])), int(state.get("retries", 0))
        trace = trace.tb_next
    return [], 0


def summarize_record(tokenizer, context_ids, ids, observations, *, status, error,
                     elapsed, trim_calls, extra_tokens=0):
    full_ids = context_ids[0].tolist() + list(ids)
    # This is the upstream CLI's published serialization, not a stability repair.
    visible = tokenizer.decode(full_ids, skip_special_tokens=True)
    observed = tokenizer.encode(visible, add_special_tokens=False)
    prefix = context_ids[0].tolist()
    prefix_matches = observed[:len(prefix)] == prefix
    observed_suffix = observed[len(prefix):] if prefix_matches else None
    canonical = prefix_matches and observed_suffix == list(ids)
    probabilities = [float(Decimal(r["probability_decimal"])) for r in observations]
    return {
        "status": status, "error": error, "token_ids": list(ids), "tokens": len(ids),
        "cover_text": visible, "text_sha256": hashlib.sha256(visible.encode()).hexdigest(),
        "context_token_ids": prefix, "visible_token_ids": observed,
        "visible_continuation_token_ids": observed_suffix,
        "prompt_prefix_matches": prefix_matches, "canonical_text_roundtrip": canonical,
        "chosen_probabilities": probabilities, "interval_observations": observations,
        "surprisal_bits": -sum(math.log2(p) for p in probabilities),
        "elapsed_seconds": elapsed, "context_trim_calls": trim_calls,
        "rejected_stop_count": extra_tokens,
        "decimal_precision": getcontext().prec,
    }


def embed(core, model, tokenizer, context, *, case_id, bits, verified):
    core.set_precision(bits, margin=40)
    ctx = tokenizer(context, return_tensors="pt")["input_ids"].to(model.device)
    vocab_size = min(model.config.vocab_size, len(tokenizer.vocab))
    stepper = traced_stepper(core, model, vocab_size)
    secret, key = secret_and_key(case_id, bits)
    start = perf_counter()
    try:
        result = core.embed_message(stepper, ctx, secret, random.Random(key), vocab_size,
                                    max_tokens=2 * bits, verify=verified)
        ids, extra, status, error = result["token_ids"], result["extra_tokens"], "complete", None
    except Exception as exc:
        ids, extra = exception_prefix(exc, "embed_message")
        status, error = type(exc).__name__, str(exc)
    elapsed = perf_counter() - start
    stepper.finish(ids)
    return summarize_record(tokenizer, ctx, ids, stepper.observations,
                            status=status, error=error, elapsed=elapsed,
                            trim_calls=stepper.trim_calls, extra_tokens=extra)


def sample_exact_boundary(dist, rng):
    """Lazy unbiased-bit sampling from the Decimal(str(CDF)) rational law."""
    bits, prefix = 64, rng.getrandbits(64)
    while True:
        low, high = Fraction(prefix, 1 << bits), Fraction(prefix + 1, 1 << bits)
        left, right = 0, len(dist.boundaries) - 2
        while left < right:
            middle = (left + right) // 2
            if Fraction(str(dist.boundaries[middle + 1])) > low:
                right = middle
            else:
                left = middle + 1
        if high <= Fraction(str(dist.boundaries[left + 1])):
            return left, bits
        prefix = (prefix << 32) | rng.getrandbits(32)
        bits += 32


def sample_control(core, model, tokenizer, context, *, case_id, bits, tokens, exogenous):
    core.set_precision(bits, margin=40)
    ctx = tokenizer(context, return_tensors="pt")["input_ids"].to(model.device)
    vocab_size = min(model.config.vocab_size, len(tokenizer.vocab))
    if exogenous:
        # This control continues past payload completion. Reserve digits for
        # every further boundary multiplication instead of inheriting the
        # stopping encoder's payload-only precision allowance.
        margin = 53 + tokens * (math.ceil(math.log10(vocab_size)) + 17) + 16
        core.set_precision(bits, margin=margin)
    stepper = traced_stepper(core, model, vocab_size)
    secret, key = secret_and_key(case_id, bits, exogenous=True)
    rng = random.Random(key if exogenous else deterministic_seed(
        "upstream", EXPERIMENT_SEED, case_id, "natural"))
    low, high, target = Decimal(0), Decimal(2) ** bits, Decimal(int(secret, 2))
    ids, random_bit_counts = [], []
    start, status, error = perf_counter(), "complete", None
    try:
        stepper.prefill(ctx)
        for position in range(tokens):
            dist = stepper.distribution(vocab_size)
            if exogenous:
                target = core.rotate(target, low, high - low, Decimal(rng.random()))
                index, low, high = core.select_index(dist, low, high, target)
            else:
                index, consumed = sample_exact_boundary(dist, rng)
                random_bit_counts.append(consumed)
            ids.append(int(dist.token_ids[index]))
            if position + 1 < tokens:
                stepper.step(ids[-1])
    except Exception as exc:
        status, error = type(exc).__name__, str(exc)
    elapsed = perf_counter() - start
    stepper.finish(ids)
    result = summarize_record(tokenizer, ctx, ids, stepper.observations,
                              status=status, error=error, elapsed=elapsed,
                              trim_calls=stepper.trim_calls)
    result["requested_tokens"] = tokens
    if not exogenous:
        result["sampling_bits_per_token"] = random_bit_counts
    return result


def prefix_record(record, tokenizer, tokens):
    """Take an independently generated natural prefix for a paired endpoint."""
    if record["status"] != "complete" or record["tokens"] < tokens:
        return {**record, "requested_tokens": tokens}
    # Only serialization changes; every selected probability remains the same.
    import torch
    context = torch.tensor([record["context_token_ids"]])
    result = summarize_record(tokenizer, context, record["token_ids"][:tokens],
                              record["interval_observations"][:tokens],
                              status="complete", error=None, elapsed=record["elapsed_seconds"],
                              trim_calls=record["context_trim_calls"])
    result["requested_tokens"] = tokens
    result["elapsed_scope"] = "Time of the full shared natural stream, not this prefix"
    result["sampling_bits_per_token"] = record["sampling_bits_per_token"][:tokens]
    result["decimal_precision"] = record["decimal_precision"]
    return result


def decode(core, model, tokenizer, context, record, *, case_id, bits, exogenous=False):
    core.set_precision(bits, margin=40)
    if exogenous:
        getcontext().prec = record["decimal_precision"]
    ctx = tokenizer(context, return_tensors="pt")["input_ids"].to(model.device)
    vocab_size = min(model.config.vocab_size, len(tokenizer.vocab))
    secret, key = secret_and_key(case_id, bits, exogenous=exogenous)
    results, previous = {}, None
    for mode, ids in [("ids", record["token_ids"]),
                      ("text", record["visible_continuation_token_ids"])]:
        if ids is None:
            results[mode] = {"status": "prompt_prefix_mismatch", "recovery_match": False}
            continue
        if previous is not None and ids == record["token_ids"]:
            results[mode] = {**previous, "execution": "same verified receiver input as ids"}
            continue
        stepper = traced_stepper(core, model, vocab_size)
        start = perf_counter()
        try:
            recovered = core.extract_message(
                stepper, ctx, ids, bits, random.Random(key), vocab_size)
            stepper.finish(ids)
            result = {
                "status": "complete", "recovery_match": recovered == secret,
                "public_probabilities_match_sender": (
                    stepper.observations == record["interval_observations"]),
                "public_surprisal_bits": -sum(
                    math.log2(float(Decimal(o["probability_decimal"])))
                    for o in stepper.observations),
            }
        except Exception as exc:
            result = {"status": type(exc).__name__, "error": str(exc),
                      "recovery_match": False}
        result["elapsed_seconds"] = perf_counter() - start
        result["execution"] = "fresh upstream receiver and model stepper"
        results[mode] = result
        if mode == "ids":
            previous = result
    return results
