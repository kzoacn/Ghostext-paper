# Prospective plan for the Accept-level revision

This plan was written on 2026-10-21 (Asia/Shanghai), before any new upstream
model generation. The previous independent recommendation remains Weak Accept.
The higher user target does not change the assessment of the frozen evidence.

The main research route is a general termination result, with a useful design
consequence. A terminal-surprisal window and an explicit source
anti-concentration bound should imply separation even after the entire length
marginal is matched. We will prove the concentration premise separately for
the ideal RRC midpoint rule and for ideal arithmetic-prefix termination with
uniform random continuation. We will not transfer either premise to
verification-dependent stopping or finite integer arithmetic without a proof.

The dependent-source example is the binary Markov chain with transition
matrix `[[3/4,1/4],[1/2,1/2]]`, starting in state zero. Its two row entropies
differ. Conditional bridge probabilities permit an elementary binomial
anti-concentration bound and a direct positive-variance check. The
zero-varentropy control is a three-state chain that stays or advances modulo
three with probability one half each. Its token identities are dependent,
while its conditional surprisal is exactly the number of generated tokens.
Exact small-state calculations must check the claimed exceptions. A fixed
exogenous endpoint will test the difference between unconditional source
fidelity and successful-delivery conditioning.

## Separate upstream study

The primary new model study will execute the unchanged `embed_message` and
`extract_message` functions from RRC commit
`dae326259e4fca8bc4fcf460dafdbc0e88a0a71a` (2026-09-04).
The core SHA-256 is
`e45a4df5eebc86881d606f2fd6c3cbab5729252dce96e5ae1a7ba424be02ec4a`.
The released `0.Prompts.tsv` has SHA-256
`bb703742046ce990ad9d717e5edac77d2e8255cbacff42a349a8fd3e0041d9b7`.
These are external source inputs, fetched by immutable revision.

The first stage uses the already pinned GPT-2 weights and tokenizer. It uses
the upstream full-vocabulary source, including its special-token behavior,
with no Ghostext truncation, quantization, or stability filter. Decimal
precision in the two stopping arms follows the upstream rule with a 40-digit
margin; rotations use
the upstream `Decimal(prng.random())` path. Public probabilities are the
differences of the actual Decimal-converted cumulative boundaries, rather
than the separately reported softmax probabilities. The earlier 192-bit
quantized-grid theorem does not apply to these settings.

Twenty distinct prompts will be selected before generation by sorting the
released rows by SHA-256 of the compact UTF-8 JSON list containing selection
label `ghostext-upstream-confirmatory-20261021-v1`, row index, and original text.
Duplicate stripped texts retain their lowest row index. Experimental seeds
derive from master seed `20261025`; the bootstrap seed is `20261026`.
The first ten selected rows are development clusters and the next ten are
test clusters. Each prompt is a cluster; these are not claimed to be twenty
independently annotated semantic topics. No prompt will be selected using
generated outcomes. Two other rows, outside that selected set, are reserved
for harness pilots and will not enter confirmatory estimates.

The complete design has two payload sizes, 128 and 512 bits, and four
independent secret/rotation tapes per prompt: 160 secret instances. Each is
run with upstream verification enabled and disabled, sharing the secret and
rotation tape. A separate exogenous-endpoint arm uses independent secrets
and tapes, the same active source primitives, and a length taken from the
verified arm. Its endpoint is independent of its own sampled content.
This arm is a separately written control, not an unchanged upstream encoder.
It will retain failed recovery rather than select successful fixed-budget
deliveries.

The excluded four-case harness pilot found a numerical issue before
confirmatory generation: fixed-endpoint case `c4_0196_b512_r0` exhausted the
40-digit reserve after 111 tokens and 660.019 bits of accumulated information.
Its unchanged record is retained under `sp2027-upstream-gpt2-pilot`.
Consequently the fixed-endpoint control, and only its receiver, will use
precision margin `53 + N*(ceil(log10(V))+17) + 16`, where `N` is its predetermined
endpoint and `V` the vocabulary size. This reserves precision for continued
boundary multiplications. The two upstream stopping arms keep margin 40.
A second excluded harness pilot will check the corrected control. This
pilot-motivated change is frozen before the confirmatory cohort and changes
neither its prompts, score, endpoint choice, nor planned size.

Natural controls are independent draws from the same boundary-defined
source, using lazy unbiased-bit comparison with the exact rational values of
the Decimal-converted boundaries. This avoids attributing a second finite
uniform grid to the ideal control law. The experimental bit stream is still
provided by Python's seeded PRNG, not treated as cryptographic randomness.
One fresh natural stream may supply the required prefixes for the
paired stopping variants. Its content is independent of all chosen lengths.
Both classes therefore have exactly paired token lengths before visible-text
serialization. The control uses a separate random tape. The model context
window is 900 tokens; generation is capped at `2*B` tokens, with any trimming,
budget exhaustion, numerical error, or model failure retained. Each complete
output is decoded using the upstream receiver and a freshly initialized
model stepper.

The upstream published serialization decodes prompt plus continuation while
skipping special tokens. We retain that string, original token IDs, and
retokenized IDs. Primary text-channel estimates require complete outputs
with the original prompt prefix and continuation recovered canonically,
matched to a complete canonical natural control. A separate sensitivity
analysis also requires successful independent receiver recovery. Raw-token
and all-attempt descriptions remain separately labelled. Failed prefixes and
all exclusion counts remain available.

The score is fixed to `-abs(public interval-source surprisal - B)`.
No new score is selected after inspecting test data. A threshold, if reported,
uses the higher empirical 95th percentile of development natural scores and
a strict-greater decision. We report AUC, TPR/FPR, denominators, per-prompt
results, and 5,000 prompt-cluster bootstrap intervals. The exogenous-endpoint
arm uses the same score and analysis. A null-looking AUC is a pipeline check,
not a proof of equality; the ideal exogenous-sampling argument supplies the
analytic comparison.

Generation may resume only from persisted complete case records with
matching source, model, prompt, and parameter hashes. Per-variant records
should be persisted before the next variant begins. Any interrupted work
must be recorded explicitly. There is no outcome-dependent extension of
the cohort. A second model is optional if the general theorem supplies the
substantive contribution; it will need a separate prospective configuration
before inference.

## Assessment and reporting

The independent gap assessment provides alternative theory and external-system
routes to a fresh Accept assessment. It is not an automatic grading rule.
Negative results, recovery failures, and a verified implementation that removes
the signal will be reported. We will not keep adding samples or tune the test
score until an acceptance threshold is crossed.

The final paper must remain within the S&P 2027 page limits, and the revised
PDF, anonymous artifact, source profiles, and independent review must all refer
to the same scientific snapshot. The previous PDF and archive will be retained
as a historical release.
