# Review: "Ghostext: an almost perfect stenography via large language model and arithmetic coding"

**Venue target:** ACM CCS
**Recommendation: Reject (Major Revision Required)**

---

## Summary

This paper presents Ghostext, a linguistic steganography system that embeds secret messages into LLM-generated cover text via arithmetic-coding-style interval narrowing over next-token distributions. The system features authenticated encryption (ChaCha20-Poly1305 with scrypt/HKDF key derivation), two-stage packet embedding (bootstrap header + body), a configuration fingerprint for sender-receiver synchronization, a retokenization-stability guard, and fail-closed decoding semantics. The paper explicitly operates under an "experiment pause" and therefore presents no empirical results, framing itself as a protocol description with an evaluation plan for future execution.

---

## Strengths

**S1. Honest claim discipline.**
The paper's three-tier claim taxonomy (implemented fact / inference / future work) is commendable and rare in this area. The authors resist the temptation to over-claim, and the separation is consistently maintained throughout the manuscript. This is a good practice that security venues should encourage.

**S2. Thorough engineering design.**
The system design reflects genuine implementation maturity. Specific highlights include: (a) the configuration fingerprint mechanism that binds model identity, tokenizer hash, prompt hash, seed, and codec parameters into a 64-bit commitment checked at decode time; (b) the retokenization-stability guard that explicitly addresses the tokenizer round-trip ambiguity problem highlighted by OD-Stega; (c) the two-stage embedding lifecycle that allows early rejection on header integrity failure before full body decode; (d) explicit, class-labeled failure modes that enable meaningful failure decomposition in future evaluations.

**S3. Fail-closed philosophy is well-motivated.**
The paper makes a convincing argument that fail-closed behavior is not merely a reliability feature but is security-relevant in steganographic contexts. Silent decode corruption leading to user workarounds and repeated retransmissions is a real operational risk, and the design addresses it systematically.

**S4. Detailed protocol walkthrough.**
Section 11 provides a clear, auditable end-to-end walkthrough from plaintext to cover text and back. The mapping between protocol steps, code modules, and failure classes is explicit and useful for reviewers and re-implementors.

**S5. Self-aware positioning.**
The related work section is fair and does not overstate Ghostext's contributions relative to prior formal approaches (Discop, de Witt et al.) or optimization-oriented work (OD-Stega).

---

## Weaknesses

**W1. [Critical] No experimental evaluation.**
This is the most fundamental problem. The paper contains zero quantitative results -- no recoverability rates, no latency measurements, no embedding efficiency numbers, no statistical divergence metrics, no detector-facing experiments. For a top security venue like CCS, this alone is disqualifying. The "experiment pause" framing is unusual and will not be persuasive to reviewers; a paper without evaluation is a workshop position paper or a technical report, not a conference contribution. The evaluation plan (Sections 7 and 10), while well-structured, describes work that has not been done.

**W2. [Critical] Title is misleading.**
The title claims "almost perfect steganography" (also note: "stenography" in the title appears to be a typo for "steganography"). Despite extensive disclaimers throughout the text, the title creates an expectation that is not met. The paper provides no evidence -- formal or empirical -- that the system achieves near-perfect undetectability. The phrase is repeatedly qualified as an "engineering trajectory" and "design intention," but a title should reflect what the paper delivers, not what it aspires to.

**W3. [Major] No formal security analysis.**
For a paper targeting CCS with security claims (even qualified ones), the absence of any formal analysis is a significant gap. Related work in this space provides either provable security guarantees (Zhang et al. 2021, Ding et al. 2023, de Witt et al. 2024) or rigorous statistical analysis (Ziegler et al. 2019, Shen et al. 2020). Ghostext offers only "security intuition" (Section 7). The KL divergence between stego text distribution and natural model output is never bounded, even in the idealized setting. At minimum, the paper should formally characterize the distributional gap introduced by candidate truncation, quantization rounding, and the retokenization-stability filter.

**W4. [Major] Limited novelty over prior art.**
The core mechanism -- arithmetic coding over neural LM next-token distributions -- is well-established since Ziegler et al. (2019). The engineering contributions (authenticated encryption wrapper, configuration fingerprinting, fail-closed semantics, retokenization guard) are valuable for practical deployment but may not individually or collectively meet the novelty bar for a top venue. The paper would be strengthened by demonstrating that these engineering choices lead to measurably better outcomes (security, reliability, or usability) compared to simpler baselines.

**W5. [Major] Excessively narrow threat model.**
The threat model restricts to a passive censor who does not know the prompt and cannot modify text in transit. This is a weak adversary by modern steganography standards. More critically, the paper does not discuss several realistic attack surfaces:
- A censor who compares observed text against outputs from the same model family under likely prompts (distributional fingerprinting).
- A censor who observes traffic patterns (message length, timing, frequency) rather than text content alone.
- Multi-message attacks where the censor accumulates samples over time from the same sender.
- The assumption that the censor does not know the prompt is strong; in many realistic scenarios, prompts follow predictable templates.

**W6. [Moderate] Paper is excessively long and repetitive.**
The manuscript repeats the same key points many times across sections. The "experiment pause" caveat, the claim taxonomy, and the "almost perfect" qualification each appear in 5+ sections. Sections 7 (Security Intuition) and 12 (Failure Case Studies) have substantial overlap. Sections 8 (Reproducibility) and 10 (Experiment Blueprint) overlap with Section 7 (Evaluation Plan). The paper would benefit substantially from consolidation -- a CCS paper should be concise.

**W7. [Moderate] Section numbering and organization issues.**
The main.tex file includes sections with conflicting numerical prefixes (two "07-" sections, two "08-" sections, two "09-" sections, two "10-" sections). While LaTeX handles section numbering automatically, this organizational ambiguity suggests the paper structure has grown organically rather than being designed. The 17 sections (including appendix) are too many for a conference paper; several should be merged or moved to supplementary material.

**W8. [Minor] No human evaluation or perceptual quality assessment.**
Even without full detector experiments, the paper could have included basic human evaluation of cover text quality, or at least qualitative examples of generated stego text alongside baseline model output. This would ground the "naturalness" claims even partially.

**W9. [Minor] Single model family.**
The implementation currently supports only Qwen-family models via llama.cpp. The paper does not discuss whether the protocol design is robust across model architectures, or whether the retokenization-stability issue is model-specific. Generalizability claims are weakened by single-model evidence.

---

## Detailed Comments

### Technical Issues

1. **Quantization bias is not analyzed.** Equation (2) shows the integer frequency allocation scheme, but the paper does not analyze how the rounding residual (distributed by fractional remainder) affects the effective distribution. For small candidate sets or skewed distributions, this rounding can be significant. What is the worst-case KL divergence introduced by quantization alone as a function of $F_{\text{tot}}$ and $|C_t|$?

2. **64-bit fingerprint collision risk.** The configuration fingerprint is truncated to 64 bits. While collision probability is low for honest users, the paper should discuss whether an adversary could craft a configuration that produces the same fingerprint but different decoding behavior (a second-preimage-style concern on the fingerprint).

3. **Retry strategy leakage.** Section 9.5 acknowledges that retries "may increase latency variance and can alter outward traffic patterns" but does not analyze this further. If the censor observes that Alice's messages have systematically different length distributions compared to normal model outputs (because short/failed attempts are retried), this is a detectable side channel. How many retries occur in practice? What is the length distribution shift?

4. **Entropy threshold gate.** Section 5.4 mentions that steps are only encodable if $|C_t| \geq 2$ and an "entropy threshold is met," but the threshold value and its impact on embedding efficiency vs. detectability are not specified or analyzed.

5. **Natural tail distinguishability.** The natural tail is sampled from the "same candidate mechanism" but carries no payload. If the candidate mechanism differs from unconstrained model sampling (which it does, due to truncation and quantization), the tail may still be distinguishable from natural model output. The paper should clarify whether tail tokens use the same constrained distribution or revert to unconstrained sampling.

### Presentation Issues

6. **Title typo:** "stenography" should be "steganography" (appears in the title and possibly elsewhere).

7. **Passive voice and hedging:** Many sentences are excessively hedged (e.g., "should be difficult to distinguish," "as closely as finite quantization and candidate filtering allow"). While the authors' caution is appreciated, the cumulative effect is that the paper's actual contributions become hard to identify.

8. **References:** The bibliography is relatively thin (14 entries) for a CCS submission in this area. Notable omissions include: Cachin's foundational information-theoretic treatment of steganographic security; Hopper et al.'s provably secure steganography framework; recent work on adaptive steganography and steganalysis arms races; and practical systems work on cover text quality evaluation.

9. **No figures or diagrams.** The paper contains no system diagram, no protocol flow figure, no data path illustration. A single well-designed figure showing the encode/decode pipeline would significantly improve readability.

10. **Code references are fragile.** Extensive references to file paths like `../Ghostext/src/ghostext/crypto.py` are useful for internal documentation but inappropriate for a double-blind submission. These should be anonymized or replaced with artifact references.

---

## Questions for Authors

1. What is the timeline for lifting the "experiment pause"? If the experiments are not yet done, what prevents submission after they are completed?

2. Can you provide even one concrete example of a (prompt, secret message, generated cover text) triple to help reviewers assess output quality?

3. What is the measured round-trip success rate on even a small-scale test (e.g., 100 messages of varying length)?

4. How does the retokenization-stability filter affect the effective candidate set size and embedding rate in practice? What fraction of candidates are typically filtered out?

5. Have you considered the minimum entropy coupling approach (de Witt et al. 2024) as an alternative to arithmetic coding? That approach achieves perfect steganographic security under exact distribution access -- how does your engineering-first approach compare in the settings where both apply?

---

## Minor Corrections

- Title: "stenography" -> "steganography"
- Section 1, paragraph 1: "exposed by either human inspection or algorithmic detection" -- awkward phrasing, consider "revealed by"
- Section 2.4: "conservative wording" is vague; specify what the conservatism consists of
- Section 5.6, Equation (2): clarify that $F_{\text{tot}}$ is the total frequency budget, not the frequency of a specific token (potential ambiguity)
- Table 1 caption could be more informative about what "protocol-sensitive" means in this context
- The paper uses both "covertext" and "cover text" -- pick one and be consistent
- Several sections end with forward-looking statements that read like conclusions; consolidate these

---

## Overall Assessment

Ghostext presents a well-engineered steganography system with sound design principles (determinism-first, fail-closed, authenticated encryption, configuration binding). The claim discipline and honest self-assessment are noteworthy. However, the paper in its current form is fundamentally incomplete for a top security venue: it has no experimental results, no formal security analysis, a misleading title, and significant redundancy across sections. The core technical contribution -- arithmetic coding over LLM distributions with engineering safeguards -- is an incremental advance over Ziegler et al. (2019) and needs empirical evidence of practical benefits to justify publication at CCS.

**Recommendation:** The authors should (1) complete the planned evaluation, (2) add at minimum a formal analysis of the distributional gap introduced by their candidate selection and quantization pipeline, (3) substantially condense the paper by merging redundant sections, (4) revise the title to accurately reflect the paper's contributions, and (5) include system diagrams and concrete examples. With these changes, the work could become a solid systems-security contribution.

**Confidence:** 4/5 (familiar with the steganography and applied cryptography literature; limited direct experience with LLM-based steganography systems)
