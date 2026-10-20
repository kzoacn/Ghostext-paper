# Ghostext: IEEE S&P 2027 revision

This workspace contains the paper, historical raw measurements, and ongoing
experiments. The implementation source is `../Ghostext`. The user authorized
resuming experiments and revising both repositories on 2026-10-20.

The draft is being revised against the
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

The revision is not yet ready for submission. An independent reviewer is
examining correctness, novelty, empirical security, and reproducibility. An
internal weak-accept recommendation is a quality gate, not a prediction of
conference acceptance. Human authors must review the final content and complete
the ethics and AI-use disclosures before submission.

Second-cycle abstract registration is November 10, 2026 and paper submission is
November 17, 2026, both 23:59:59 AoE, according to the CFP checked on 2026-10-20.
