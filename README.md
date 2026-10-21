# Ghostext: IEEE S&P 2027 revision

This branch contains the S&P 2027 manuscript, retained measurements, exact
audits, and reproducibility tools. The implementation source is `../Ghostext`.
The revision studies complete stopped transcripts, finite-message padding,
and integer rounding. Its main theorem covers three ideal termination
mechanisms, including reverse verification, with an explicit dependent-source
finite certificate and a full-support finite-order corollary. Its guarded
codec repairs a specified coding defect; it does not establish complete-text
security against ordinary model generation.

The review manuscript follows the
[official S&P 2027 CFP](https://sp2027.ieee-security.org/cfpapers.html):
IEEEtran 1.8b, `conference,compsoc`, US Letter, at most 13 pages of main text and
18 pages overall. No author block appears in the review version. The unmodified
class and bibliography style are vendored from
[CTAN](https://ctan.org/pkg/ieeetran); their license notices remain intact.

Build from `paper/`:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Historical results are retained unchanged. They must not be mistaken for new
runs or for proof of detector resistance. In particular, the historical
`bits_per_token_encode` metric counts the entire encrypted packet, including
88 bytes of framing, rather than only application plaintext.

The unchanged current-upstream RRC study retains 160 instances each for GPT-2
and Qwen2.5-0.5B, with verified, unverified, and independent-endpoint arms.
Public replays score every published string without canonicality or recovery
selection. Separate four-budget runs retain all 640 prefixes per model.
The models share twenty prompt clusters and prescribed tapes; replication
does not enlarge the prompt population.

Earlier processed-source studies contain 960 planned pairs across two models
and two separately analyzed candidate policies. Authenticated-delivery studies
retain 120 trial records. One interrupted Qwen trial is reported separately;
primary bounded-attempt estimates use the other 119 trials, with conservative
bounds for the interrupted case. These cohorts are not pooled with the
unchanged-upstream results.

Start with [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for model pins, frozen source
profiles, exact checks, saved-data analyses, and replay commands. The lightweight
environment needs no model libraries: its regression run passed 59 tests, with
one optional integration test skipped and five subtests passed.
The export builder creates `output/ghostext-sp2027-artifact.zip`, preserving
observations while removing identifying metadata. The current PDF is
`output/pdf/ghostext-sp2027.pdf`: 18 pages overall, with main content ending
on page 13. All eighteen pages passed individual visual inspection, and the
mechanical format checks pass. The current source index contains 26 profiles.

Earlier independent reviews and frozen releases remain archived; their
recommendations apply to their named PDF and ZIP hashes. The
[final independent research review](notes/reviews/2026-10-21-final-research-review.md)
recommends **Accept, confidence 4/5**, for the complete two-model revision,
with no unresolved substantive blocker for its stated claims. This is an
independent internal assessment, not a conference acceptance decision.
The [final release validation](notes/sp2027-complete-release-validation.json)
binds that assessment to the exact PDF and anonymous archive, whose 8,626
indexed files and 26 source profiles pass the strict verifier.
[Separate-extraction reproduction](results/sp2027-validation/followup-artifact-reproduction.json)
passes 19 checks with 48 byte-identical outputs, including the finite
certificates, analyses, and generated materials.
[All 26 profiles](results/sp2027-validation/followup-profile-preflight.json)
materialize correctly; nine upstream command entries reproduce their scientific
manifest fields without model inference. Human authors remain responsible for
reviewing the content and completing the ethics and AI-use disclosures before
submission. Older CCS notes and unused section files are historical material,
excluded from the active manuscript and review artifact.

Second-cycle abstract registration is November 10, 2026 and paper submission is
November 17, 2026, both 23:59:59 AoE, according to the CFP checked on 2026-10-20.
