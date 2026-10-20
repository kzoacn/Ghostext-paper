"""Text-only bootstrap admissibility probe. No key or plaintext is an input."""
from __future__ import annotations
import math
from ghostext.candidate_policy import select_candidates
from ghostext.codec import MessageSegmentDecoder, interval_rounding_tv
from ghostext.config import CandidatePolicyConfig
from ghostext.errors import ModelBackendError, UnsafeTokenizationError
from ghostext.quantization import quantize_candidates


def probe_bootstrap(backend, text, prompt, *, guards=(0, 128), payload_len=60,
                    policy=None, total_frequency=4096, seed=7, max_tokens=2048):
    policy = policy or CandidatePolicyConfig(top_p=.995, max_candidates=64, min_entropy_bits=0)
    decoders = {g: MessageSegmentDecoder(payload_len, guard_bits=g) for g in guards}
    results = {
        g: {"status": "unfinished", "tokens_observed": 0, "log_likelihood_ratio": 0.,
            "max_codec_rounding_tv": 0., "sum_codec_rounding_tv": 0.}
        for g in guards
    }
    token_ids = backend.tokenize(text, prompt)
    prefix = []
    for index, token_id in enumerate(token_ids[:max_tokens]):
        active = [g for g in guards if results[g]["status"] == "unfinished"]
        if not active:
            break
        try:
            raw = backend.distribution(prompt, prefix, seed)
            selection = select_candidates(raw, policy, backend=backend, prompt=prompt,
                                          generated_token_ids=prefix)
            q = quantize_candidates(selection, total_frequency)
        except (UnsafeTokenizationError, ModelBackendError) as exc:
            for g in active:
                results[g].update(status=type(exc).__name__, tokens_observed=index)
            break
        for g in active:
            result, decoder = results[g], decoders[g]
            result["tokens_observed"] = index + 1
            if not q.allows_encoding:
                if token_id != q.top.token_id:
                    result["status"] = "non_greedy_token"
                continue
            try:
                selected = q.find_token_id_index(token_id)
            except KeyError:
                result["status"] = "outside_candidate_set"
                continue
            before = decoder.high - decoder.low
            tv = float(interval_rounding_tv(decoder.low, decoder.high, q))
            result["max_codec_rounding_tv"] = max(result["max_codec_rounding_tv"], tv)
            result["sum_codec_rounding_tv"] += tv
            try:
                decoder.absorb(q, selected)
            except ValueError:
                result["status"] = "zero_width_interval"
                result["log_likelihood_ratio"] = None  # mathematical -infinity
                continue
            after = decoder.high - decoder.low
            result["log_likelihood_ratio"] += (
                math.log(after / before) - math.log(q.entries[selected].frequency / total_frequency)
            )
            if decoder.finished:
                result["status"] = "admissible"
        prefix.append(token_id)
    for result in results.values():
        if result["status"] == "unfinished":
            result["status"] = "incomplete_bootstrap"
    return {"visible_tokens": len(token_ids), "guards": {str(g): r for g, r in results.items()}}
