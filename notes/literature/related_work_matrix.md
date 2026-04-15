# Related Work Matrix (Security-First Positioning)

This matrix is for internal drafting. It separates established facts from tentative claims.

## 1. Foundational Steganography Security Model

1. Simmons (CRYPTO 1983), "The Prisoners' Problem and the Subliminal Channel"  
   Relevance: canonical communication-under-surveillance framing.
2. Anderson & Petitcolas (IEEE JSAC 1998), "On the limits of steganography"  
   Relevance: formal/security limitations context.
3. Hopper, Langford, von Ahn (CRYPTO 2002; IEEE TC 2009), "Provably Secure Steganography"  
   Relevance: provable-security baseline language for modern comparisons.

Positioning vs Ghostext:

- Ghostext is not introducing a new information-theoretic stego definition.
- Ghostext contributes an engineering protocol for deterministic LLM-channel recoverability under explicit synchronization assumptions.

## 2. Neural / Generative Linguistic Steganography

1. Fang et al. (ACL 2017), "Generating Steganographic Text with LSTMs"
2. Ziegler et al. (EMNLP-IJCNLP 2019), "Neural Linguistic Steganography"
3. Zhang et al. (Findings ACL 2021), "Provably Secure Generative Linguistic Steganography"
4. Lin et al. (NAACL 2024), "Zero-shot Generative Linguistic Steganography"
5. Qi et al. (IEEE TDSC 2025), "Provably Secure Disambiguating Neural Linguistic Steganography"
6. Yan & Murawaki (EMNLP 2025), "Addressing Tokenization Inconsistency in Steganography and Watermarking Based on LLMs"

Positioning vs Ghostext:

- Closest technical overlap: arithmetic/range coding over language-model distributions.
- Ghostext emphasis: end-to-end fail-closed recoverability with explicit config fingerprint and deterministic pipeline constraints.
- Tokenization-path consistency is directly relevant (Ghostext has retokenization stability guard).

## 3. Security-Systems and Modern Covert Messaging

1. Kaptchuk et al. (CCS 2021), "Meteor"
2. Ding et al. (IEEE S&P 2023), "Discop"
3. Bauer et al. (CODASPY 2024), "Leveraging Generative Models for Covert Messaging (Dead-Drop)"
4. Jois et al. (CCS 2024), "Pulsar: Secure Steganography for Diffusion Models"

Positioning vs Ghostext:

- These works frame stronger or broader security/deployment settings.
- Ghostext should avoid claiming equivalent security guarantees without matching proofs/evaluations.
- Practical contribution claim should stay scoped: deterministic local-model covert channel prototype with explicit boundary conditions.

## 4. Steganalysis / Detection

1. Yang et al. (IEEE TIFS 2019), "RNN-Stega" (generation method often used in comparative context)
2. Yi et al. (ICASSP 2022), "Exploiting Language Model for Efficient Linguistic Steganalysis"
3. Guo et al. (IEEE SPL 2022), "Linguistic Steganalysis Merging Semantic and Statistical Features"
4. Yang et al. (ICASSP 2023), "LINK: Linguistic Steganalysis Framework with External Knowledge"
5. Bai et al. (arXiv 2024), "Towards Next-Generation Steganalysis: LLMs Unleash the Power of Detecting Steganography"

Positioning vs Ghostext:

- Detector resistance is an open concern for current Ghostext scope.
- In CCS draft, detection-resistance claims should be treated as future work unless we run dedicated experiments.

## 5. Drafting Guardrails

- Safe novelty framing:
  - protocol-level synchronization discipline
  - fail-closed decoding behavior
  - reproducible local deployment path
- Unsafe novelty framing (unless new evidence is added):
  - "undetectable" in general
  - robust to edits / transport noise
  - strong guarantees across model/version drift
