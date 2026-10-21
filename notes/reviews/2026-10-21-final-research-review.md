**Independent IEEE S&P research review — 21 October 2026**

**Overall recommendation: Accept. Confidence: 4/5 (high).**

I would support acceptance at a normal IEEE S&P research bar. The paper identifies a consequential gap between preserving active token probabilities and securing the complete transmitted text, establishes that gap for a meaningful family of termination mechanisms, and connects it to an actual published security argument and retained implementation evidence. The reverse-verified stopping analysis is the strongest technical contribution. I found no unresolved substantive correctness or evidence blocker for the claims actually made. This recommendation is for the scoped audit and theory presented here; it is not an endorsement of Ghostext as a secure deployment system.

**Versions and independence.**

The final reviewed manuscript is `paper/main.pdf`, 18 total pages with 13 main-content pages, SHA-256:

`47726fb28c94c5c09db316a520ea6ad65d61a18b984cd94ecdf5c73993f4f4b7`

The final reviewed archive is `output/ghostext-sp2027-artifact.zip`, SHA-256:

`a12e3c40c2d36870a63e144ecd1fda46515909ae727ef486138be047b440a6b1`

I read the complete manuscript and all proof appendices, inspected all 18 rendered pages, examined the relevant implementation and analysis code, and checked primary references. I did not consult other research reviews, project goal/status notes, or conversation history to form this judgment. No pretrained language-model inference, detector training, or external messaging was performed.

Most executable checks ran in a separate extraction of the supplied prerelease archive, SHA-256 `4db29efd219ee8aa568426364fd806570ea8c8e138cae65d5df5d5c629c0a2d0`. I subsequently extracted the exact final archive separately, checked its CRC and file hashes, ran its strict verifier, and compared every archived file with the tested snapshot. There are 8,616 unchanged files, nine changed indexed files plus the changed file index, one added reproduction receipt, and no removals. The changes concern the literature acknowledgment, bibliography/PDF, documentation, and validation receipts. No implementation, experiment script, retained observation, numerical analysis, or figure/table result changed. I also independently recomputed the headline score/AUC results from the final extraction. The final PDF's source changes were confined to the introduction, related work, and the added primary reference; I checked the revised wording and all newly rendered pages.

**Contribution and significance.**

The main result goes beyond detecting an anomalous output-length histogram. The comparator receives the encoder's entire marginal length law, but its fresh content is sampled independently of that length. Under the stated source assumptions, the encoder concentrates terminal information near the payload size while the comparator spreads that information over a wider range. This yields a distinguishing event even when length alone is uninformative. The analysis covers arithmetic-prefix recovery, the published RRC midpoint rule, and its reverse-verified idealization, with an explicit dependent example and a dependent negative control.

This addresses a concrete claim in the literature. The published RRC proof in Appendix B.3 introduces a termination factor and then dismisses its distinguishing effect. Ghostext supplies an explicit law and a public information statistic that expose the missing dependence without recovering the private rotations. The original source confirms that this is a relevant security target, rather than a comparator invented without relation to the prior claim. [Yan and Murawaki, ACL 2026](https://aclanthology.org/2026.acl-long.39.pdf).

The novelty should remain centered on this stopping analysis, especially reverse verification. Random continuation, rounding effects, tokenization checks, and public probability-based auditing have substantial prior art. The final manuscript now appropriately credits the closely related precision-loss audit of Cao et al. Their method targets numerical support loss under matched generation settings; Ghostext's principal separation persists in exact arithmetic and concerns content–endpoint dependence. This distinction is technically meaningful. The NLS padding counterexample and guarded integer implementation are useful supporting contributions, but would be much less compelling as the paper's sole novelty. [Cao, Wang, and Hu, Findings ACL 2026](https://aclanthology.org/2026.findings-acl.1013/).

**Correctness assessment.**

I found the main proof chain coherent. The terminal-band criterion is elementary, and the paper correctly locates the substantive work in proving concentration for each mechanism. The Markov anti-concentration step is supported by the cited Berry–Esseen result, including its treatment of nonstationary initialization. The full-support zero-varentropy argument correctly uses the context graph rather than assuming every entry of its transition matrix is positive. [Kontoyiannis and Verdú, Theorem 21 and Section VI](https://www.dpmms.cam.ac.uk/~ik355/PAPERS/SVYK-J.pdf).

I checked the reverse-verification argument particularly closely: the safe interval is half-open; its update preserves a sufficient reverse-recovery event; the killed kernel includes both failure regions; and the two-step contraction controls small safe widths without conditioning away difficult survivors. The entry-time potential bound and the subsequent survival bound are consistent. The finite certificate likewise retains omitted probability as an error budget and covers lengths beyond the finite scan. These are important details, because reusing the unverified hazard after adding a recovery veto would not be valid.

The guarded-code theorem also has an appropriate scope. Weighting the local rounding discrepancy by interval probability and counting unresolved intervals gives the stated coding-only bound against the stopping-matched reference. The manuscript does not infer uniform packet bytes from authenticated encryption, does not identify this comparator with ordinary model generation, and does not turn the guard size into an end-to-end security level. The separate endpoint support claim does not require packet uniformity. I found no mathematical contradiction between these claims.

**Empirical assessment.**

The unchanged-upstream study is the strongest empirical part. Its public scorer consumes the published string and public context, while canonicality and receiver success are checked afterward. All planned outputs enter the main analysis. This avoids a serious selection problem that would arise from evaluating only successfully recovered or canonically tokenized texts. The independent-endpoint arm and its budget extension are useful controls: the former tests the dependence mechanism, while the latter exposes the associated delivery cost.

My independent recomputation from saved CDF masses gives these held-out AUCs:

| Model | Payload bits | Verified stopping | Independent endpoint |
|---|---:|---:|---:|
| GPT-2 | 128 | 0.923125 | 0.548750 |
| GPT-2 | 512 | 0.971250 | 0.535000 |
| Qwen2.5-0.5B | 128 | 0.966250 | 0.531875 |
| Qwen2.5-0.5B | 512 | 0.975000 | 0.480625 |

The saved-data recomputations also reproduce the reported recovery increases at twice the independent budget: 158/160 and 154/160 from token IDs, and 129/160 and 133/160 from published text. The guarded endpoint replay reproduces 13/13 and 37/37 stego acceptances, against 0/13 and 1/37 controls. These observations support the stated mechanism and implementation findings.

There are meaningful limits. Each main model/payload/arm cell has only 40 held-out observations per class from ten prompt clusters, and the models share the prompt population. GPT-2's 128-bit verified test FPR is 7/40 under the fixed development threshold. High AUC therefore does not establish a calibrated low-FPR operating point. The 50-pair authenticated endpoint study is a conditional, post-hoc, no-tail diagnostic with known plaintext length; its true-positive property is structural. The paper explicitly acknowledges these limits and does not pool the older conditional cohorts into the unchanged-upstream result.

**Substantive blockers and optional improvements.**

I identify no remaining substantive blocker for acceptance of the current claims. The source assumptions, numerical idealizations, observer knowledge, serialization effects, and delivery conditioning are sufficiently explicit to evaluate the conclusions. In particular, the absence of a theorem for arbitrary LLMs is not concealed by the finite-state result.

The principal limits on significance are the restricted operational setting and the incremental nature of the precision/packet components. The work does not establish detection under unknown prompts, unknown-length mixtures, ordinary EOS policies, natural tails, or model mismatch, and it does not supply a secure complete protocol. Its contribution is nevertheless substantial as a security audit of specified mechanisms and claims.

Optional improvements would be to streamline the main text's multiple historical cohorts and implementation details, and to prioritize natural tails, uncertain payload lengths, and larger independently sampled prompt populations in follow-up work. These would improve accessibility and practical coverage; they are not prerequisites for the present theorem or its demonstrated counterexamples. The figures and tables are legible, and I found no clipping, broken equations, or unresolved references in the final rendering.

**Checks actually executed.**

Commands below refer to the independently extracted `Ghostext-paper/` directory. Analysis writes affected only the reviewer's temporary extraction, never the working experiment records.

- `python3 scripts/verify_artifact.py .. --allow-draft` passed on the prerelease: 8,625 indexed files and 26 source profiles. `python3 scripts/verify_artifact.py ..` passed on the final archive: 8,626 indexed files and 26 profiles. The final ZIP's CRC, safe extraction paths, complete hash comparison, and embedded PDF hash also passed.
- `PYTHONPATH=../Ghostext/src python3 -m pytest ../Ghostext/tests -q` passed: **59 passed, 1 skipped, 5 subtests passed**. The skipped test is the explicitly enabled real-model integration test; its model environment variable was removed for this review.
- `run_codec_security_audit.py` and `run_external_counterexamples.py` passed. These reproduced the exact coding-law results, including NLS complete-text TV `15/16` with reported KL zero and the published RRC matched-length TV `33/256`. The NLS execution used synthetic constant logits and the pinned original functions, not pretrained-model generation.
- `audit_termination_theory.py`, `audit_rotation_grid.py`, and `audit_stopping_adapter.py` passed. The checks include safe intervals, reverse-error cancellation, public endpoint identities, the fixed-endpoint failure inequality, the finite-grid `1/96` example, and verified-stop recovery fixtures.
- For `certify_verified_stopping.py`, I executed `safe_tail_bounds()`, `small_exact_audit()`, and a complete `certify(512, 8, 9, ...)` recomputation. The regenerated 512-bit certificate and scan matched the archived result, including lower bound `0.13470320`. This also checked 11,521 statewise lower bounds, 57,605 integer band memberships, 205 event bounds, and 11,521 run-composition counts. I separately recomputed the 2048-bit candidate maximum probability and its final rational lower-bound arithmetic. **I did not rerun the complete 2048-bit dynamic-programming scan.**
- `analyze_upstream_observable.py` ran on both all-string cohorts with the default 5,000 prompt-cluster resamples. `analyze_upstream_budget.py` ran on both budget cohorts. `analyze_public_endpoint.py` ran on the corrected GPT-2 and Qwen endpoint cohorts. All passed.
- `audit_observable_fidelity.py` passed separately for GPT-2 and Qwen2.5: all 960 output bindings per model were retained, with 786 and 783 canonical bindings exactly matching the sender paths; the 174 and 177 noncanonical bindings remained included.
- The 13 regenerated deterministic audit/analysis result files were byte-identical to their archived counterparts. Separately written arithmetic and pairwise-ranking checks reproduced the small exact counterexamples, every Table 3 point estimate and threshold result, and the upstream ID/text recovery counts without importing the paper's analysis functions. The headline AUC computation was repeated directly on the final extraction.

The review environment used Python 3.12.12, NumPy 1.26.4, pytest 9.0.3, cryptography 46.0.3, and PyTorch 2.11.0+cu130. This was a code, proof, and saved-data audit, not a reconstruction of the full inference environment. Saved records and hash consistency do not independently attest the original model computation, and no such attestation is claimed here.
