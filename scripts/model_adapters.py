"""Local CPU adapter for an independently pinned GPT-2 experiment."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

import numpy as np
from ghostext.errors import ModelBackendError
from ghostext.model_backend import BackendMetadata, RawNextTokenDistribution


class GPT2Backend:
    """Raw prompt continuation; no chat template or remote inference."""

    def __init__(self, model_dir, *, threads=2, seed=7):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        torch.set_num_threads(threads)
        self.seed = seed
        path = Path(model_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
        self.model = AutoModelForCausalLM.from_pretrained(path, local_files_only=True).eval()
        self.n_ctx = self.model.config.n_positions
        self.eos_id = self.tokenizer.eos_token_id
        revision = (path / "revision.txt").read_text().strip()
        tokenizer_hash = hashlib.sha256(
            (path / "tokenizer.json").read_bytes() + b"/raw-prompt-continuation-v1"
        ).hexdigest()
        self.metadata = BackendMetadata(
            model_id=f"openai-community/gpt2@{revision}",
            tokenizer_hash=tokenizer_hash,
            backend_id="transformers-cpu-float32-gpt2",
        )
        self._cached_ids = []
        self._past = None
        self._last_logits = None

    def tokenize(self, text, prompt):
        return self.tokenizer.encode(text, add_special_tokens=False)

    def render(self, token_ids):
        return self.tokenizer.decode(token_ids, clean_up_tokenization_spaces=False,
                                     skip_special_tokens=False)

    def token_text(self, token_id):
        return self.render([token_id])

    def distribution(self, prompt, generated_token_ids, seed):
        if seed != self.seed:
            raise ModelBackendError("backend seed mismatch")
        prefix = self.tokenizer.encode(prompt, add_special_tokens=False)
        if not prefix:
            prefix = [self.eos_id]
        ids = prefix + generated_token_ids
        if len(ids) >= self.n_ctx:
            raise ModelBackendError(f"context would exceed GPT-2 n_ctx={self.n_ctx}")
        if ids[:len(self._cached_ids)] != self._cached_ids:
            self._cached_ids, self._past, self._last_logits = [], None, None
        delta = ids[len(self._cached_ids):]
        if delta:
            with self.torch.inference_mode():
                outputs = self.model(
                    self.torch.tensor([delta], dtype=self.torch.long),
                    past_key_values=self._past, use_cache=True,
                )
            self._past = outputs.past_key_values
            self._last_logits = outputs.logits[0, -1].detach().cpu().numpy().astype(np.float64)
            self._cached_ids = list(ids)
        logits = self._last_logits.copy()
        # Match Ghostext's payload-channel policy. Ordinary EOS control must
        # explicitly restore this logit and record the distinct policy.
        logits[self.eos_id] = -np.inf
        return RawNextTokenDistribution(np.arange(len(logits), dtype=np.int32), logits)

    def provenance(self):
        return {"model": self.metadata.as_dict(), "n_ctx": self.n_ctx,
                "prompt_template": "raw-prompt-continuation-v1"}
