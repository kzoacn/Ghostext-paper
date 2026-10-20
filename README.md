# Ghostext: IEEE S&P 2027 revision

This branch contains the S&P 2027 manuscript, retained measurements, exact
audits, and reproducibility tools. The implementation source is `../Ghostext`.
The revision studies finite-message padding, integer rounding, and public
stopping leakage. Its guarded codec repairs a specified coding defect; it
does not establish complete-text security against ordinary model generation.

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

The completed stopping studies contain 960 planned pairs across two models
and two separately analyzed candidate policies. The delivery studies retain
120 trial records. One Qwen trial resumed after an external termination and
is reported separately; primary bounded-attempt estimates use the other 119
trials, with conservative bounds for the interrupted case.

Start with [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for model pins, frozen source
profiles, exact checks, saved-data analyses, and replay commands. The lightweight
environment needs no model libraries: its regression run passed 59 tests, with
one optional integration test skipped and five subtests passed.
The export builder creates `output/ghostext-sp2027-artifact.zip`, preserving
observations while removing identifying metadata. The final PDF is
`output/pdf/ghostext-sp2027.pdf`: 13 pages overall, with main content ending
on page 11. All pages passed visual inspection.

The [release validation](notes/sp2027-release-validation.json) records a fresh
extraction of the final ZIP in the lightweight environment. All six primary
analyses reproduced exactly; the generated tables and both figure PDFs were
byte-identical. All 13 source profiles materialized with matching source,
helper, and staged-input hashes.

The [final independent review](notes/reviews/2026-10-21-final-independent-addendum.md)
recommends **weak accept, with moderate confidence**, for the narrow security
analysis and implementation audit. It confirms the regression and artifact
issues identified in the original review are resolved. This is an internal
quality gate, not a prediction of conference
acceptance. Human authors must review the final content and complete the ethics
and AI-use disclosures before submission. Older CCS notes and unused section
files are historical material, excluded from the active manuscript and review
artifact.

Second-cycle abstract registration is November 10, 2026 and paper submission is
November 17, 2026, both 23:59:59 AoE, according to the CFP checked on 2026-10-20.
