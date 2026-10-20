# S&P 2027 claim and evidence ledger

This ledger supersedes the distribution-preservation positioning in the older
CCS notes. The baseline independent review was **strong reject**. A fresh
independent review on 2026-10-20 recommends **weak accept** for the narrow
stopping-law analysis and implementation audit. Its explicit artifact checks
are being closed before the final addendum; the recommendation does not imply
conference acceptance.

| Claim | Evidence | Scope and limitation |
|---|---|---|
| Original NLS terminal support can collapse while its reported KL is zero | `scripts/run_external_counterexamples.py`; `results/sp2027-external-audit/summary.json` | Unchanged pinned original encoder functions; exhaustive synthetic uniform-64 model, 256 one-byte messages. Not an empirical GPT-2 attack. |
| Legacy Ghostext integer law differs from its quantized CDF | `scripts/run_codec_security_audit.py`; `results/sp2027-codec-audit/summary.json`; implementation tests | Exact rational complete-tree enumeration, including invalid reference branches. |
| The published ideal RRC midpoint rule leaks content–length dependence | Paper Section 4 and Appendix D; external exact audit | Public model/prompt/message length; ideal independent rotations; exact marginal length matching. Does not cover later verification-before-stop code. |
| Nonuniform binary IID separation tends to one | Proof with explicit constants; `scripts/run_stopping_dp.py`; simulation | Fixed source as message length grows. Dynamic program is floating-point numerical corroboration; proof establishes the result. Uniform source is a negative control. |
| Guarding bounds coding-only transcript error | Paper Theorem 2; exhaustive audit; `../Ghostext/tests/test_guarded_codec.py` | Uniform payload and guard; same public stop rule and absorbing outcomes; no ordinary language or packet-pseudorandomness guarantee. |
| Archived Qwen covers exhibit a public bootstrap signal | `results/sp2027-keyless-legacy/` | 118 stego covers, only 18 matched controls. Historical controls use floating probabilities and three raw-argmax fallbacks; they do not isolate strict quantized Q. |
| Archived rate previously counted framing as payload | `results/sp2027-historical-audit/summary.json` | 88-byte overhead; mean net 1.1725 bits/token; 100 deliveries required 140 attempts. Historical failed prefixes unavailable. |
| Real-model stopping effects under the strict source | `results/sp2027-stopping-gpt2/`, `results/sp2027-stopping-qwen/` | Complete 160/320 attempted pairs; 90/296 eligible pairs. Primary AUCs condition on complete canonical matched pairs. All attempts retained. |
| Stopping effects under expanded candidate search | `results/sp2027-stopping-gpt2-expanded/`, `results/sp2027-stopping-qwen-expanded/` | Separate post-hoc cohorts, new seed and unchanged score/topic split. GPT-2 complete 160/160; Qwen ongoing at this checkpoint. |
| Guarded versus legacy authenticated delivery | `results/sp2027-repair-gpt2/`, `results/sp2027-repair-qwen/` | GPT-2 complete 40/40, 19/20 deliveries per guard. Qwen ongoing at this checkpoint. Every failed attempt retained. |
| Optional expanded candidate pool resolves specific empty-set prefixes | `results/sp2027-empty-set-diagnosis/`; `results/sp2027-expanded-*-pilot/` | Selected development diagnosis and six successful first-attempt deliveries. Not a general reliability or security estimate. |
| Verification extends three observed reverse-failure outputs | `results/sp2027-reverse-failure-gpt2/` | All three completed GPT-2 failures selected, reproduced, and independently decoded after one/two/two added tokens. Separate 40-case verified cohort vetoes zero stops. |
| Finite experimental rotations approximate the ideal public stopped law | `results/sp2027-rotation-grid/`; proof appendix | Independent uniform 192-bit draws, quantized Q, public token/stop/cap/failure transcript only. Excludes verified stopping, latent rotations, and success conditioning. |
| Source and model profiles are reconstructible | `source-snapshots/`; `results/sp2027-source-map/`; `REPRODUCIBILITY.md` | Exact source bytes for 13 profiles and pinned model revisions. OS-random delivery is statistically rerunnable, not seeded bit-exact regeneration. |

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

Outstanding gates: finish the two remaining Qwen cohorts and their independent
public replays, integrate final denominators, inspect every final PDF page,
verify the anonymous artifact, and obtain the independent review addendum.
