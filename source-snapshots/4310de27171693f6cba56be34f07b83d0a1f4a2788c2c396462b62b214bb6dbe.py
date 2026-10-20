"""Cache public candidate tables during replay, avoiding redundant LLM passes."""
from __future__ import annotations
from ghostext.candidate_policy import select_candidates
from ghostext.codec import MessageSegmentDecoder
from ghostext.quantization import quantize_candidates


class CandidateTrace:
    def __init__(self, backend, policy, total_frequency=4096):
        self.backend = backend
        self.policy = policy
        self.total_frequency = total_frequency
        self.tables = []

    def __getattr__(self, name):
        return getattr(self.backend, name)

    def clear(self):
        self.tables.clear()

    def distribution(self, prompt, generated_token_ids, seed):
        raw = self.backend.distribution(prompt, generated_token_ids, seed)
        selection = select_candidates(
            raw, self.policy, backend=self.backend, prompt=prompt,
            generated_token_ids=generated_token_ids,
        )
        q = quantize_candidates(selection, self.total_frequency)
        if len(generated_token_ids) != len(self.tables):
            raise ValueError("candidate trace requires a single sequential replay")
        self.tables.append(q)
        return raw


def probe_trace(ids, tables, guards=(0, 128), payload_len=60):
    results = {}
    for guard in guards:
        decoder = MessageSegmentDecoder(payload_len, guard_bits=guard)
        status = "incomplete_bootstrap"
        observed = 0
        for token_id, q in zip(ids, tables):
            observed += 1
            if not q.allows_encoding:
                if token_id != q.top.token_id:
                    status = "non_greedy_token"
                    break
                continue
            try:
                index = q.find_token_id_index(token_id)
            except KeyError:
                status = "outside_candidate_set"
                break
            try:
                decoder.absorb(q, index)
            except ValueError:
                status = "zero_width_interval"
                break
            if decoder.finished:
                status = "admissible"
                break
        results[str(guard)] = {"status": status, "tokens_observed": observed}
    return results
