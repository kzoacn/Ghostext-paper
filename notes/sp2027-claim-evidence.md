# S&P 2027 claim and evidence ledger

This ledger supersedes the distribution-preservation positioning in the older
CCS notes. The baseline independent review was **strong reject**. A fresh
independent review on 2026-10-20 recommended **weak accept** for the narrow
stopping-law analysis and implementation audit. The
[final independent addendum](reviews/2026-10-21-final-independent-addendum.md),
dated 2026-10-21 in Asia/Shanghai, maintains that recommendation with moderate
confidence and finds no remaining blocking defect for those claims.
That archived release's artifact checks are recorded in the
[release validation](sp2027-release-validation.json); the recommendation does
not imply conference acceptance.

The theory and unchanged-upstream revision below was independently assessed
in the [fresh review](reviews/2026-10-21-fresh-sp-review.md). Its recommendation
is **Weak Accept, confidence 4/5**, with no confirmed scientific or artifact
blocker. The assessed PDF and archive remain unchanged under
`output/archive/weak-accept-theory-2026-10-21/`. Full reproduction passed for
1,903 indexed files and 20 source profiles.

A further [prospective follow-up](sp2027-observable-followup-plan.md) now
addresses the remaining canonical-pair selection and empirical-breadth limits.
It fixes an all-observable-text score, a second unchanged-upstream model
replication, and independent endpoint-budget recovery curves. The
[design audit](reviews/2026-10-21-observable-followup-design-review.md)
finds no remaining design-level blocker. This is a plan, not new outcome
evidence or a revised acceptance recommendation.

| Claim | Evidence | Scope and limitation |
|---|---|---|
| Original NLS terminal support can collapse while its reported KL is zero | `scripts/run_external_counterexamples.py`; `results/sp2027-external-audit/summary.json` | Unchanged pinned original encoder functions; exhaustive synthetic uniform-64 model, 256 one-byte messages. Not an empirical GPT-2 attack. |
| Legacy Ghostext integer law differs from its quantized CDF | `scripts/run_codec_security_audit.py`; `results/sp2027-codec-audit/summary.json`; implementation tests | Exact rational complete-tree enumeration, including invalid reference branches. |
| The published ideal RRC midpoint rule leaks content–length dependence | Paper Section 4 and Appendix D; external exact audit | Public model/prompt/message length; ideal independent rotations; exact marginal length matching. Does not cover later verification-before-stop code. |
| Terminal-information separation on dependent Markov sources | New general criterion, three separately proved band premises, and explicit bridge bound; `scripts/audit_termination_theory.py` | Exact-real continuous midpoint/verified rules and uniform continuous prefix target. Positive varentropy and bounded probabilities are required. Explicit finite bounds can be vacuous at experimental sizes; not a theorem for arbitrary LLMs. |
| Verified stopping retains an ideal information band | Safe-interval invariant and two-step contraction in the proof appendix; exact interior-point and reverse-error audits | No transfer to finite-grid verification or Decimal arithmetic. A dependent equal-branch source has exact TV zero. |
| Public first-resolution endpoints expose a support event | Standard TV identity applied to public stopping; capped exact prefix-tree enumeration | Conditional on public context; exact identity is for the stopped Q law. Arbitrary delivered packet laws only receive the support-event lower bound. |
| Current upstream verification repairs recovery but retains the measured signal | `results/sp2027-upstream-gpt2/`, unchanged pinned September source | 160 instances, one veto, ID recovery159/160 to160/160. Canonical matched slices110/160; held-out AUC0.938/0.998. One model, known B and prompt, finite software measured separately from ideal proof. |
| Exogenous endpoints have a measured delivery cost | Same frozen upstream study, independent secret/tape and verified-length budget | Fixed-endpoint primary AUC0.533/0.586; ID recovery74/160. Failures retained, null-compatible CIs do not prove equality. |
| Guarded authenticated delivery retains a public endpoint signal | `results/sp2027-endpoint-gpt2-corrected/`, `results/sp2027-endpoint-qwen/` | Post-hoc unchanged eligible no-tail pairs, known16-byte plaintext length. Exact endpoint accepts13/13 and37/37 delivered texts versus0/13 and1/37 controls. All reconstructed packet hashes match; no packet-uniformity premise. |
| Token-ID agreement alone is insufficient for numerical replay | `results/sp2027-endpoint-gpt2/`, retained runtime mismatch | The initial one-thread replay differs from two-thread generation. All13 records retained as diagnostic, not pooled with the corrected estimate. |
| Guarding bounds coding-only transcript error | Paper guarded-coding theorem; exhaustive audit; `../Ghostext/tests/test_guarded_codec.py` | Uniform payload and guard; same public stop rule and absorbing outcomes; no ordinary language or packet-pseudorandomness guarantee. |
| Archived Qwen covers exhibit a public bootstrap signal | `results/sp2027-keyless-legacy/` | 118 stego covers, only 18 matched controls. Historical controls use floating probabilities and three raw-argmax fallbacks; they do not isolate strict quantized Q. |
| Archived rate previously counted framing as payload | `results/sp2027-historical-audit/summary.json` | 88-byte overhead; mean net 1.1725 bits/token; 100 deliveries required 140 attempts. Historical failed prefixes unavailable. |
| Real-model stopping effects under the strict source | `results/sp2027-stopping-gpt2/`, `results/sp2027-stopping-qwen/` | Complete 160/320 attempted pairs; 90/296 eligible pairs. Primary AUCs condition on complete canonical matched pairs. All attempts retained. |
| Stopping effects under expanded candidate search | `results/sp2027-stopping-gpt2-expanded/`, `results/sp2027-stopping-qwen-expanded/` | Separate post-hoc cohorts, new seed and unchanged score/topic split. GPT-2 160/160 and Qwen 320/320 complete matched pairs; four/eight reverse mismatches. |
| Guarded versus legacy authenticated delivery | `results/sp2027-repair-gpt2/`, `results/sp2027-repair-qwen/` | All 120 trial records saved. Primary GPT-2 deliveries 19/20 per guard; Qwen 39/40 legacy and 38/39 guarded. One interrupted/resumed Qwen case excluded from primary estimates and reported separately. |
| Optional expanded candidate pool resolves specific empty-set prefixes | `results/sp2027-empty-set-diagnosis/`; `results/sp2027-expanded-*-pilot/` | Selected development diagnosis and six successful first-attempt deliveries. Not a general reliability or security estimate. |
| Verification extends three observed reverse-failure outputs | `results/sp2027-reverse-failure-gpt2/` | All three completed GPT-2 failures selected, reproduced, and independently decoded after one/two/two added tokens. Separate 40-case verified cohort vetoes zero stops. |
| Finite experimental rotations approximate the ideal public stopped law | `results/sp2027-rotation-grid/`; proof appendix | Independent uniform 192-bit draws, quantized Q, public token/stop/cap/failure transcript only. Excludes verified stopping, latent rotations, and success conditioning. |
| Source and model profiles are reconstructible | `source-snapshots/`; `results/sp2027-source-map/`; `REPRODUCIBILITY.md` | Exact source bytes for 20 declared profiles and pinned model revisions; new profile validation is recorded separately. OS-random delivery is statistically rerunnable, not seeded bit-exact regeneration. |
| Public features can be reconstructed from text | `results/sp2027-public-replay/` | Exact token/probability matches on 24 stopping texts; matching bootstrap outcomes on 12 delivery-study texts. Selection is the first eligible held-out case per stated group. |
| Interrupted work is not counted as an observed trial outcome | `results/sp2027-repair-qwen/interruption.json`; `results/sp2027-validation/repair-qwen-count-check.json` | First 64 rows byte-preserved. Case `01_zh_corner_cafe:r0:g128` uses a fresh budget on resume; original 40-case guarded-plan delivery/first-attempt counts bounded by 38–39/36–37. |
| Lightweight reproduction does not need model libraries | `results/sp2027-validation/lightweight-environment.json` | Clean virtual environment with no Torch, Transformers, or llama.cpp: 59 tests pass, one optional integration test skips, five subtests pass. |

The historical `Bhat` calculation used an inapplicable `N/(2F)` quantization
bound and omitted finite-interval error. Archived values are preserved for
provenance and must not be presented as valid security bounds. New source
audits compute quantization and integer-interval effects separately.

The strict stopping and delivery cohorts use Ghostext commit `f6ad798`.
The optional expanded candidate policy was added later in `a47336a` and is
enabled only in separately labelled follow-ups. Each manifest records actual
source-file hashes, not merely a branch name; source snapshots preserve those
versions. Core regression validation now records 59 passed and one optional
model test skipped, with five subtests passed.

The archived Weak Accept release completed its planned cohorts and public replays,
including interruption accounting. That manuscript had 13 pages, with main content
ending on page 11; all pages passed individual visual inspection. The anonymous
artifact passed its verifier. From a separate extraction, all six primary
analyses and six exact or saved-data audits reproduced their measurements.
The generated tables and figures were byte-identical, and all 13 source
profiles materialized with matching hashes. The final independent addendum
records separate successful checks of the same frozen PDF and archive,
including the full core test suite and all 13 rendered pages.
