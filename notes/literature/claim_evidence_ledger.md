# Ghostext Claim-Evidence Ledger

This note tracks what we can claim in the CCS draft, the exact scope of each claim, and evidence pointers.

## 1) Deterministic recoverability under matched configuration

Claim scope: Alice/Bob use the same model/backend, tokenizer behavior, prompt, seed, and protocol-sensitive settings.

Maturity: `implemented + tested`

Evidence pointers:
- Runtime fingerprint is computed from runtime protocol config, backend metadata, and prompt hash:
  - `../Ghostext/src/ghostext/config.py:84`
- Encoder binds fingerprint to encrypted packet metadata:
  - `../Ghostext/src/ghostext/encoder.py:119`
  - `../Ghostext/src/ghostext/crypto.py:69`
- Decoder recomputes and checks fingerprint before final decrypt:
  - `../Ghostext/src/ghostext/decoder.py:83`
  - `../Ghostext/src/ghostext/decoder.py:87`
- Matched round-trip tests:
  - `../Ghostext/tests/test_roundtrip_zh.py:10`
  - `../Ghostext/tests/test_roundtrip_en.py:10`
- Rerunnable evaluation artifacts:
  - `results/minimal_eval_results.json`
  - `results/real_backend_eval_results.json`

## 2) Encrypt-before-hide with authenticated decryption failures

Claim scope: Packet contents are encrypted and authenticated before embedding; wrong keys/tampering should fail decryption.

Maturity: `implemented + tested`

Evidence pointers:
- Key derivation and separation:
  - `../Ghostext/src/ghostext/crypto.py:23` (scrypt)
  - `../Ghostext/src/ghostext/crypto.py:34` (HKDF-SHA256)
- AEAD for header/body:
  - `../Ghostext/src/ghostext/crypto.py:64` (ChaCha20-Poly1305 body)
  - `../Ghostext/src/ghostext/crypto.py:75` (ChaCha20-Poly1305 header)
- Config mismatch and auth-failure checks:
  - `../Ghostext/src/ghostext/crypto.py:143`
  - `../Ghostext/src/ghostext/crypto.py:162`
- Crypto tests:
  - `../Ghostext/tests/test_crypto.py:20`
  - `../Ghostext/tests/test_crypto.py:37`
  - `../Ghostext/tests/test_crypto.py:54`

## 3) Fail-closed behavior under mismatch/mutation

Claim scope: Wrong seed/prompt/passphrase or packet text mutation should raise explicit decode failure.

Maturity: `implemented + tested`

Evidence pointers:
- Decoder synchronization checks and hard failures:
  - `../Ghostext/src/ghostext/decoder.py:158`
  - `../Ghostext/src/ghostext/decoder.py:177`
  - `../Ghostext/src/ghostext/decoder.py:183`
  - `../Ghostext/src/ghostext/decoder.py:188`
- Failure-oriented tests:
  - `../Ghostext/tests/test_failures.py:84`
  - `../Ghostext/tests/test_failures.py:93`
  - `../Ghostext/tests/test_failures.py:101`
- Minimal eval fail-closed summary:
  - `results/minimal_eval_results.json` (`fail_closed.fail_closed_rate = 1.0`)

## 4) Candidate policy with retokenization stability guard

Claim scope: Candidate filtering includes top-p/max-candidates/min-entropy controls and optional retokenization safety enforcement.

Maturity: `implemented + tested`

Evidence pointers:
- Candidate policy fields:
  - `../Ghostext/src/ghostext/config.py:14`
- top-p and max-candidates filtering:
  - `../Ghostext/src/ghostext/candidate_policy.py:64`
- entropy gating:
  - `../Ghostext/src/ghostext/candidate_policy.py:81`
- retokenization stability guard:
  - `../Ghostext/src/ghostext/candidate_policy.py:169`
  - `../Ghostext/src/ghostext/candidate_policy.py:219`
- Guard tests:
  - `../Ghostext/tests/test_tokenization_stability.py:78`
  - `../Ghostext/tests/test_tokenization_stability.py:93`

## 5) Deterministic quantization and finite-interval coding

Claim scope: Quantization and interval operations are deterministic and shared by encode/decode.

Maturity: `implemented + tested`

Evidence pointers:
- Quantization and deterministic tie-handling:
  - `../Ghostext/src/ghostext/quantization.py:37`
  - `../Ghostext/src/ghostext/quantization.py:46`
- Interval encoder/decoder mechanics:
  - `../Ghostext/src/ghostext/codec.py:9`
  - `../Ghostext/src/ghostext/codec.py:44`
  - `../Ghostext/src/ghostext/codec.py:88`
- Quantization and codec tests:
  - `../Ghostext/tests/test_quantization.py:10`
  - `../Ghostext/tests/test_codec_toy.py:19`

## 6) Real local backend path exists and is exercised

Claim scope: Ghostext has a local `llama.cpp` backend path for Qwen GGUF and we can run round-trip checks locally.

Maturity: `implemented + tested`

Evidence pointers:
- Local backend implementation:
  - `../Ghostext/src/ghostext/llama_cpp_backend.py:244`
- Integration test entry:
  - `../Ghostext/tests/test_llama_cpp_integration.py:16`
- Paper-repo real-backend evaluation script and artifact:
  - `scripts/run_real_backend_eval.py`
  - `results/real_backend_eval_results.json`

## 7) Passive-censor indistinguishability statement

Claim scope: Passive censor observes only text and does not know prompt/password.

Maturity: `implemented only` (no dedicated detector study in this repo)

Required caveat in paper text:
- Keep wording conditional and scoped to passive-censor assumptions.
- Do not claim broad detector resistance.

Evidence pointers:
- Threat-model statement in paper:
  - `paper/sections/02_problem_and_threat_model.tex`
- Related steganalysis context:
  - `paper/sections/07_related_work.tex`

## 8) Out-of-scope claims (must stay caveated)

Maturity: `planned`

- Robustness under active edits/reordering/deletions.
- Resistance against dedicated steganalysis detectors.
- Cross-model/cross-version decode compatibility.
- Production-grade censorship resistance.

These should remain in limitations/future-work language until dedicated experiments are added.
