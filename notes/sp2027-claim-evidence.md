# S&P 2027 claim and evidence ledger

This ledger supersedes the distribution-preservation positioning in the older
CCS notes. The baseline independent review was **strong reject**. The revised
manuscript has not yet received a new acceptance recommendation.

| Claim | Evidence | Scope and limitation |
|---|---|---|
| Original NLS terminal support can collapse while its reported KL is zero | `scripts/run_external_counterexamples.py`; `results/sp2027-external-audit/summary.json` | Unchanged pinned original encoder functions; exhaustive synthetic uniform-64 model, 256 one-byte messages. Not an empirical GPT-2 attack. |
| Legacy Ghostext integer law differs from its quantized CDF | `scripts/run_codec_security_audit.py`; `results/sp2027-codec-audit/summary.json`; implementation tests | Exact rational complete-tree enumeration, including invalid reference branches. |
| The published ideal RRC midpoint rule leaks content–length dependence | Paper Section 4 and Appendix D; external exact audit | Public model/prompt/message length; ideal independent rotations; exact marginal length matching. Does not cover later verification-before-stop code. |
| Nonuniform binary IID separation tends to one | Proof with explicit constants; `scripts/run_stopping_dp.py`; simulation | Fixed source as message length grows. Dynamic program is floating-point numerical corroboration; proof establishes the result. Uniform source is a negative control. |
| Guarding bounds coding-only transcript error | Paper Theorem 2; exhaustive audit; `../Ghostext/tests/test_guarded_codec.py` | Uniform payload and guard; same public stop rule and absorbing outcomes; no ordinary language or packet-pseudorandomness guarantee. |
| Archived Qwen covers exhibit a public bootstrap signal | `results/sp2027-keyless-legacy/` | 118 stego covers, only 18 matched controls. Small pilot; controls already filtered; broad intervals. |
| Archived rate previously counted framing as payload | `results/sp2027-historical-audit/summary.json` | 88-byte overhead; mean net 1.1725 bits/token; 100 deliveries required 140 attempts. Historical failed prefixes unavailable. |
| Real-model stopping effects | `results/sp2027-stopping-gpt2/`, `results/sp2027-stopping-qwen/` | GPT-2 complete; Qwen ongoing at this checkpoint. Primary classifier analysis conditions on complete canonical matched pairs. Every attempt remains recorded. |
| Guarded versus legacy authenticated delivery | `results/sp2027-repair-gpt2/`, `results/sp2027-repair-qwen/` | Ongoing at this checkpoint. No final aggregate claim until all planned cases finish. |
| Optional expanded candidate pool resolves specific empty-set prefixes | `results/sp2027-empty-set-diagnosis/` | Post-hoc diagnosis of two named development failures; does not by itself prove successful delivery or security. Strict-policy cohorts remain unchanged. |

The historical `Bhat` calculation used an inapplicable `N/(2F)` quantization
bound and omitted finite-interval error. Archived values are preserved for
provenance and must not be presented as valid security bounds. New source
audits compute quantization and integer-interval effects separately.

Fresh long-running cohorts use Ghostext commit `f6ad798`. The optional expanded
candidate policy was added later in `a47336a` and is not enabled in those
cohorts. Each manifest records actual source-file hashes, not merely a branch
name. Source scripts are frozen in this paper revision before further changes.

Outstanding gates: finish both full cohorts, independently replay public
features, add all denominators and intervals to the paper, validate optional
policy delivery, verify all rendered pages and references, freeze an anonymous
artifact, and obtain a new independent review without relaxing its standard.
