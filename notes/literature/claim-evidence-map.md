# Ghostext Claim-Evidence Map (Draft v0)

This file maps paper claims to concrete evidence from `../Ghostext` and mandatory key papers under `literature/`.

## Scope Rules

- Claim types:
  - Implemented fact: directly evidenced in code/tests.
  - Inference: plausible implication from implemented facts.
  - Future work: requires new experiments.
- Until experiment pause is lifted, do not upgrade inference/future-work statements to confirmed empirical claims.

## C1. Packet encryption is authenticated and key-separated

- Claim type: Implemented fact.
- Claim text: Ghostext encrypts packet header and body with separated subkeys derived from a shared passphrase and salt.
- Evidence:
  - `../Ghostext/src/ghostext/crypto.py:34` derives two subkeys by HKDF.
  - `../Ghostext/src/ghostext/crypto.py:64` encrypts body with `ChaCha20Poly1305`.
  - `../Ghostext/src/ghostext/crypto.py:75` encrypts internal header with a different key.
  - `../Ghostext/tests/test_crypto.py:20` validates encrypt/decrypt round-trip.

## C2. Packet bootstrap is opaque (no plaintext magic/header marker)

- Claim type: Implemented fact.
- Evidence:
  - `../Ghostext/src/ghostext/packet.py:70` defines opaque bootstrap size.
  - `../Ghostext/tests/test_crypto.py:71` checks bootstrap does not expose `HDTX` marker.

## C3. Decode is fail-closed on config mismatch

- Claim type: Implemented fact.
- Evidence:
  - `../Ghostext/src/ghostext/decoder.py:83` computes expected fingerprint.
  - `../Ghostext/src/ghostext/decoder.py:87` rejects mismatch.
  - `../Ghostext/src/ghostext/crypto.py:143` also checks fingerprint in packet decrypt path.
  - `../Ghostext/tests/test_crypto.py:37` verifies mismatch raises `ConfigMismatchError`.

## C4. Candidate set uses top-p/max-k and entropy gate

- Claim type: Implemented fact.
- Evidence:
  - `../Ghostext/src/ghostext/candidate_policy.py:64` applies top-p/max-k cut.
  - `../Ghostext/src/ghostext/candidate_policy.py:81` computes `allows_encoding` via entropy and candidate count.

## C5. Retokenization-stability guard is enforced

- Claim type: Implemented fact.
- Evidence:
  - `../Ghostext/src/ghostext/candidate_policy.py:169` stability filtering path.
  - `../Ghostext/src/ghostext/candidate_policy.py:193` fails when no stable candidate remains.
  - `../Ghostext/tests/test_tokenization_stability.py:78` and `:93` validate both filtering and fail-closed behavior.

## C6. Quantization is integer and deterministic

- Claim type: Implemented fact.
- Evidence:
  - `../Ghostext/src/ghostext/quantization.py:37` integer frequency allocation.
  - `../Ghostext/src/ghostext/quantization.py:46` deterministic tie-break with token ID.
  - `../Ghostext/tests/test_quantization.py:24` determinism under ties.

## C7. Arithmetic interval codec is invertible under matched path

- Claim type: Implemented fact.
- Evidence:
  - `../Ghostext/src/ghostext/codec.py:47` encoder choose-by-subinterval.
  - `../Ghostext/src/ghostext/codec.py:91` decoder absorb update.
  - `../Ghostext/tests/test_codec_toy.py:19` segment round-trip test.

## C8. Encoder has bounded retry for low entropy and unstable tokenization

- Claim type: Implemented fact.
- Evidence:
  - `../Ghostext/src/ghostext/encoder.py:123` max encode attempts.
  - `../Ghostext/src/ghostext/encoder.py:144` low-entropy retry branch.
  - `../Ghostext/src/ghostext/encoder.py:163` unstable-tokenization retry branch.
  - `../Ghostext/tests/test_failures.py:205` and `:275` cover retry behavior.

## C9. Decoder ignores trailing natural tail tokens after payload resolution

- Claim type: Implemented fact.
- Evidence:
  - `../Ghostext/src/ghostext/decoder.py:118` stores trailing tokens after consumed cursor.
  - `../Ghostext/tests/test_failures.py:116` confirms decode success with extra trailing token.

## C10. Round-trip recoverability exists in toy English/Chinese and optional real-model smoke

- Claim type: Implemented fact (limited scope).
- Evidence:
  - `../Ghostext/tests/test_roundtrip_en.py:10` English toy round-trip.
  - `../Ghostext/tests/test_roundtrip_zh.py:10` Chinese toy round-trip.
  - `../Ghostext/tests/test_llama_cpp_integration.py:16` environment-gated real-model smoke round-trip.

## C11. Prompt template family is protocol-sensitive via backend metadata hash

- Claim type: Implemented fact.
- Evidence:
  - `../Ghostext/src/ghostext/llama_cpp_backend.py:322` template resolution by model markers.
  - `../Ghostext/src/ghostext/llama_cpp_backend.py:287` tokenizer hash includes prompt template ID.
  - `../Ghostext/src/ghostext/config.py:90` fingerprint binds backend metadata + prompt hash.

## C12. Security against strong detectors is not yet established in this project

- Claim type: Future work / explicit caveat.
- Evidence basis:
  - No dedicated detector benchmark scripts or result artifacts currently in this repo.
  - AGENTS boundary requires labeling detector resistance as preliminary unless directly tested.

## Literature Anchors

- `literature/key-md/D19-1115.md`: arithmetic coding + neural LM distribution-preserving framing.
- `literature/key-md/2026-eacl-long-36-od-stega.md`: optimized-distribution framing and tokenization mismatch discussion.

## Versioning Note

Update this map whenever claims in `paper/sections/*.tex` change.
