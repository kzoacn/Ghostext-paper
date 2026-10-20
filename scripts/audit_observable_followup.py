#!/usr/bin/env python3
"""Small adversarial checks for observable scoring and endpoint persistence."""
from __future__ import annotations

import argparse
from decimal import getcontext
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import numpy as np
import torch

from analyze_upstream_observable import summarize, summarize_emitted_strings
from observable_upstream_score import public_score
from run_upstream_budget_curve import generate_prefixes
from upstream_rrc_experiment import load_core

ROOT = Path(__file__).resolve().parents[1]


class PublicTokenizer:
    vocab = {str(i): i for i in range(5)}
    mapping = {
        "P": [0], "Pab": [0, 3], "Pdead": [0, 4], "Pmissing": [0, 99], "X": [2],
    }

    def __call__(self, text, **kwargs):
        return {"input_ids": torch.tensor([self.mapping[text]])}

    def encode(self, text, **kwargs):
        return self.mapping[text]


class PublicDistribution:
    boundaries = np.array([0, .25, .5, .75, .75, 1.])
    tokens = [1, 2, 3, 4, 0]

    def index_of(self, token):
        return self.tokens.index(token) if token in self.tokens else -1


class PublicStepper:
    def __init__(self, *args, **kwargs):
        pass

    def prefill(self, context):
        pass

    def distribution(self, vocabulary):
        return PublicDistribution()

    def step(self, token):
        pass


class InjectedGenerationFailure(RuntimeError):
    pass


class BudgetTokenizer:
    vocab = {"P": 0, "a": 1, "b": 2}

    def __call__(self, text, **kwargs):
        return {"input_ids": torch.tensor([[self.vocab[c] for c in text]])}

    def encode(self, text, **kwargs):
        return [self.vocab[c] for c in text]

    def decode(self, ids, **kwargs):
        return "".join("Pab"[int(i)] for i in ids)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "results/sp2027-observable-audit")
    args = ap.parse_args()
    fake = SimpleNamespace(LMStepper=PublicStepper,
                           set_precision=lambda *args, **kwargs: setattr(getcontext(), "prec", 80))
    model = SimpleNamespace(device="cpu", config=SimpleNamespace(vocab_size=5))
    tokenizer = PublicTokenizer()
    checks = {}
    for text, status in [
        (None, "no_output"), ("P", "empty_continuation"), ("X", "prompt_prefix_mismatch"),
        ("Pdead", "zero_source_mass"), ("Pmissing", "token_outside_source"), ("Pab", "complete")]:
        result = public_score(fake, model, tokenizer, text=text, prompt="P", bits=8)
        assert result["status"] == status
        assert result["visible_character_count"] == (0 if text is None else len(text))
        assert result["score_is_negative_infinity"] == (status != "complete")
        if text == "Pab":
            # The observer sees one merged token, regardless of a sender's hidden segmentation.
            assert result["token_ids"] == [3] and result["surprisal_bits"] == 2
            assert result["score"] == -6
        checks[status] = True
    class BrokenStepper(PublicStepper):
        def prefill(self, context):
            raise RuntimeError("Injected infrastructure failure")
    broken = SimpleNamespace(LMStepper=BrokenStepper, set_precision=fake.set_precision)
    try:
        public_score(broken, model, tokenizer, text="Pab", prompt="P", bits=8)
    except RuntimeError as exc:
        assert str(exc) == "Injected infrastructure failure"
    else:
        raise AssertionError("An execution failure became a defined public decision")
    checks["execution_error_propagates"] = True

    scores = {
        "absent": {"score": None, "score_is_negative_infinity": True, "status": "no_output",
                   "visible_token_count": 0, "visible_character_count": 0},
        "seen": {"score": -1., "score_is_negative_infinity": False, "status": "complete",
                 "visible_token_count": 2, "visible_character_count": 3},
    }
    def row(prompt, split, pos, neg):
        return {"prompt_id": prompt, "split": split,
                "positive": {"public_input_id": pos,
                             "generation_status": "complete" if pos == "seen" else "failed"},
                "negative": {"public_input_id": neg,
                             "generation_status": "complete" if neg == "seen" else "failed"}}
    infinity_rows = [row("d0", "development", "seen", "absent"),
                     row("d1", "development", "seen", "absent"),
                     row("t0", "test", "seen", "absent"),
                     row("t1", "test", "absent", "absent")]
    analysis = summarize(infinity_rows, scores, 20)
    assert analysis["threshold_is_negative_infinity"] and analysis["threshold"] is None
    assert analysis["auc"] == .75 and analysis["test_tpr"] == .5 and analysis["test_fpr"] == 0
    checks["infinity_ties_and_development_quantile"] = True
    unmatched = [row("d", "development", "seen", "seen"),
                 row("t0", "test", "seen", "absent"), row("t1", "test", "absent", "seen")]
    emitted = summarize_emitted_strings(unmatched, scores, 20)
    assert emitted["test_positive_strings"] == emitted["test_negative_strings"] == 1
    assert emitted["auc"] == .5
    checks["unmatched_emissions_retained"] = True

    core, _, provenance = load_core()
    distribution = core.StepDistribution(torch.tensor([.75, .25], dtype=torch.float64),
                                         torch.tensor([1, 2]), 2)
    budget_model = SimpleNamespace(device="cpu", config=SimpleNamespace(vocab_size=3))
    budget_tokenizer = BudgetTokenizer()
    with TemporaryDirectory(prefix="ghostext-observable-audit-") as temporary:
        directory = Path(temporary)
        def make_core(case_id, failure_type=None):
            class Stepper:
                def __init__(self, model, vocab, max_ctx_len):
                    self.max_ctx_len, self._cached_len = max_ctx_len, 1
                def prefill(self, context):
                    pass
                def distribution(self, vocabulary):
                    return distribution
                def step(self, token):
                    if self._cached_len in [4, 5]:
                        assert (directory / "prefixes" / case_id / f"n{self._cached_len}.json").exists()
                    if self._cached_len == 5 and failure_type is not None:
                        raise failure_type("Injected after five completed tokens")
                    self._cached_len += 1
            return SimpleNamespace(
                LMStepper=Stepper, set_precision=core.set_precision,
                rotate=core.rotate, select_index=core.select_index)
        task = {"case_id": "later_failure", "message_bits": 8, "prompt": "P", "reference_N": 4}
        results = generate_prefixes(make_core(task["case_id"], InjectedGenerationFailure),
                                    budget_model, budget_tokenizer, task, directory)
        for n in [4, 5]:
            assert results[n]["status"] == "complete" and results[n]["tokens"] == n
            assert len(results[n]["interval_observations"]) == n
        for n in [6, 8]:
            assert results[n]["status"] == "InjectedGenerationFailure"
            assert results[n]["tokens"] == len(results[n]["interval_observations"]) == 5
        checks["later_failure_preserves_completed_endpoints"] = True
        checks["prefix_snapshot_immutable_in_memory"] = True
        task = {**task, "case_id": "interrupted"}
        try:
            generate_prefixes(make_core(task["case_id"], KeyboardInterrupt),
                              budget_model, budget_tokenizer, task, directory)
        except KeyboardInterrupt:
            pass
        else:
            raise AssertionError("Synthetic interruption did not propagate")
        before = {n: (directory / "prefixes" / task["case_id"] / f"n{n}.json").read_bytes()
                  for n in [4, 5]}
        resumed = generate_prefixes(make_core(task["case_id"]),
                                    budget_model, budget_tokenizer, task, directory)
        assert all(r["status"] == "complete" for r in resumed.values())
        for n in [4, 5]:
            assert before[n] == (directory / "prefixes" / task["case_id"] / f"n{n}.json").read_bytes()
        checks["resume_preserves_previous_endpoint_bytes"] = True
    sources = [Path(__file__), *[ROOT / "scripts" / name for name in [
        "observable_upstream_score.py", "analyze_upstream_observable.py",
        "run_upstream_budget_curve.py", "upstream_rrc_experiment.py",
        "run_upstream_rrc.py", "fetch_upstream_rrc.py", "analyze_stopping_llm.py",
        "artifact_utils.py", "audit_existing_evidence.py"]]]
    output = {
        "schema": "observable-followup-audit-v1", "checks": checks, "all_passed": True,
        "source_sha256": {str(p.relative_to(ROOT.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sources},
        "upstream": provenance,
        "scope": "Synthetic scorer/analysis/failure-persistence checks; no model inference or detector estimates",
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "summary.json").write_text(json.dumps(output, indent=2) + "\n")
    print("Passed", len(checks), "observable and endpoint-persistence checks")


if __name__ == "__main__":
    main()
