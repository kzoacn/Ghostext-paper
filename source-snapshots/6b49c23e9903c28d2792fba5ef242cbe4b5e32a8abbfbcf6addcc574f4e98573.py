"""A total public score on the upstream serializer's observable outputs."""
from __future__ import annotations

from decimal import Decimal
import hashlib
import math


def public_score(core, model, tokenizer, *, text, prompt, bits):
    """Input is only the published string (or no output) and public context.

    This is a score of a canonical tokenization, not a sum over all token
    preimages of a rendered string. Execution errors propagate to the caller.
    """
    core.set_precision(bits, margin=40)
    base = {
        "text_sha256": None if text is None else hashlib.sha256(text.encode()).hexdigest(),
        "visible_token_count": 0, "visible_character_count": 0,
        "token_ids": [], "interval_observations": [], "surprisal_bits": None,
        "score": None, "score_is_negative_infinity": True,
    }
    if text is None:
        return {**base, "status": "no_output"}
    context = tokenizer(prompt, return_tensors="pt")["input_ids"].to(model.device)
    visible = tokenizer.encode(text, add_special_tokens=False)
    base.update(visible_token_count=len(visible), visible_character_count=len(text))
    prefix = context[0].tolist()
    if visible[:len(prefix)] != prefix:
        return {**base, "status": "prompt_prefix_mismatch"}
    ids = visible[len(prefix):]
    base["token_ids"] = ids
    if not ids:
        return {**base, "status": "empty_continuation"}
    vocab = min(model.config.vocab_size, len(tokenizer.vocab))
    stepper = core.LMStepper(model, vocab, max_ctx_len=900)
    stepper.prefill(context)
    observations = []
    for position, token in enumerate(ids):
        dist = stepper.distribution(vocab)
        index = dist.index_of(token)
        if index < 0:
            return {**base, "status": "token_outside_source",
                    "interval_observations": observations,
                    "first_unsupported_position": position}
        low, high = str(dist.boundaries[index]), str(dist.boundaries[index + 1])
        mass = Decimal(high) - Decimal(low)
        observation = {"token_id": token, "cdf_low": low, "cdf_high": high,
                       "probability_decimal": str(mass)}
        observations.append(observation)
        if mass <= 0:
            if mass < 0:
                raise ValueError("Nonmonotone public source CDF")
            return {**base, "status": "zero_source_mass",
                    "interval_observations": observations,
                    "first_unsupported_position": position}
        if position + 1 < len(ids):
            stepper.step(token)
    information = -sum(math.log2(float(Decimal(o["probability_decimal"])))
                       for o in observations)
    return {**base, "status": "complete", "interval_observations": observations,
            "surprisal_bits": information, "score": -abs(information - bits),
            "score_is_negative_infinity": False}
