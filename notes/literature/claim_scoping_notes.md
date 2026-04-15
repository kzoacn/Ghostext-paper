# Claim Scoping Notes (Security-First)

## Claims we can currently defend

- Deterministic recoverability under matched configuration assumptions.
- Fail-closed behavior under selected mismatch conditions.
- Engineering reproducibility under local backend and explicit config fingerprinting.

## Claims requiring new experiments before strong wording

- Detector resistance.
- Robustness to active edits/transforms.
- Cross-model/version interoperability.

## Writing style constraints

- Use conditional wording when assumptions are strict.
- Always separate "implemented behavior" from "security guarantee".
- Avoid "undetectable" unless directly substantiated against specified detectors.
