# Independent code and output review of the finite verified-rule certifier

Review date: 2026-10-21. I found no scientific correctness blocker in the complete certifier or its retained outputs. A fresh complete execution reproduced all four output files byte-for-byte, and separate arithmetic checks verified the resulting certificates. The manuscript, experiment plan, and certifier source were not modified. No model inference was performed.

The reviewed source is `scripts/certify_verified_stopping.py`, SHA-256 `f32a0c6ff8a9271a02c7f2d15cdfe3afc07cabb8176815b32420bd9a70ff0b61`. The mathematical argument is assessed separately in `2026-10-21-finite-verified-certificate-assessment.md`. This review checks that the executable calculation implements that argument and that the retained outputs follow from it.

## Rational safe-rule recurrence

`killed_operator` correctly integrates each old polynomial piece, adds the surviving point-mass term, substitutes `z/rho`, and appends the constant piece on `[rho/2,1/2]`. All coefficients and integrals remain `Fraction` values. The code does not evaluate a polynomial outside its piecewise domain when the extra term vanishes.

`safe_tail_bounds` computes `4*integral_0^(1/4) h_m` with `h_0=1`. A separately written exact-Fraction implementation reproduced all 25 retained tails through m=24, including the m=9 and m=12 values used in the three cases. The retained recurrence audit checks 300 exact continuities and 1,175 direct-integral evaluations; the separate implementation also checked 825 direct evaluations. The use of an unnormalized entry submeasure is stated in the summary and matches the mathematical proof. No survival normalization enters the calculation.

These are exact values of the proposed sufficient safe-rule bound. Neither the code nor this review establishes that they are the actual verified-rule survival probabilities.

## Fixed-point propagation and integer band membership

The two uint64 arrays represent the ending state and the counts `(u,v)=(#00,#01)`. The four update slices implement precisely the transitions of the declared matrix. Existing contributions are merged with addition; no overlapping transition is overwritten. Flooring each outgoing weighted integer mass maintains a lower bound in every state.

The representation has a valid overflow proof. The initial total is D=2^60. Each pair of outgoing floor operations has sum at most the input mass, so the total remains at most D. An intermediate multiplication is at most 3D, below 2^62. Each merged destination and each unsigned sum is at most D. The calculations use integer products and shifts, with no floating conversion. The signed count arrays and indices are also far inside their int64 range for the declared cases.

I independently propagated a Python-integer dictionary, an exact integer-mass DP with denominator 4^n, and unweighted path counts. Through n=60, all 155,062 matrix-cell comparisons and exact lower-mass inequalities passed. This included 117,181 cells outside the exact reachable support, whose array entries remained zero. A further 102 high-mass fixtures, including an entire mass of 2^60 in either starting state, agreed with Python-integer propagation and preserved the total-mass invariant.

For information `I=n+u+v-log2(3^u)`, both scalar and vector band tests retain the u=0 exception in the ceiling of the logarithm. The vectorized extraction uses a different v value at each offset; clipping out-of-range indices cannot duplicate a valid contribution because the corresponding mask is false. I checked 265,160 membership decisions with direct rational-probability comparisons, 423 independently accumulated band extractions, and 283 exact event probabilities. Tests included equal integer endpoints, zero length, and bands crossing zero. All agreed.

`certify` keeps the full missing mass `D-total` and adds it to each event's stored lower mass. The shortcut `2*n<lower` correctly declares an impossible event without adding a numerical deficit: each true transition contributes at most two information bits. The missing-mass calculation is not a renormalization or a selection filter.

## Coverage of every length and exact maximum identification

The scan includes every integer length from zero through the declared cutoff. Beyond that cutoff, the code computes the exact rational collision bound `2^upper*(5/8)^(cutoff+1)`, capped at one. The exponent is correct for the first unscanned length. The proof uses the maximum row sum 5/8 of the entrywise squared transition matrix, and its geometric decrease covers every subsequent length. I separately checked 101 exact collision moments and matched 13 of them to an enumeration of individual paths.

The independent run-composition formula starts from state zero, as declared in the output. For each feasible count configuration it counts binary runs and multiplies by `3^u/2^(n+u+v)`. Summation at denominator 4^n is exact. Across 47,642 small-case cells, including unreachable cells, the composition formula matched unweighted path counts.

The exact-maximum promotion has the correct direction. The script first chooses a candidate using scanned upper bounds. It computes that candidate's exact probability separately, then compares it with every other scanned upper bound and the remaining-length bound. Only when all of those are at most the candidate's exact value does it replace the conservative bound by that exact maximum. Otherwise it keeps the maximum of the finite-scan and residual-length upper bounds.

I exercised this conservative branch in a separate in-memory namespace with auxiliary denominator eight, which deliberately makes the DP too coarse to certify a maximum. The flag remained false and the conservative bound was retained. The repository source and the production denominator were not changed.

Even when certified exactly, this quantity is the supremum of the natural band probability over fixed lengths. It is not the actual band probability under the independently length-matched mixture, and it is not exact total variation. Using the supremum is a valid conservative step in the theorem.

## Final arithmetic and reporting scope

The final subtraction uses exact fractions for the early-stop term, safe-rule tail, and natural-band bound. Negative lower bounds are clipped to zero. `decimal_down` floors the rational value before formatting, so its eight-decimal display cannot overstate the certificate. I checked 2,852 positive, negative, and near-boundary rational rounding cases at four precisions; each displayed value was at or below its exact input, with a gap smaller than one displayed unit.

The declared result remains a lower bound for the ideal, uncapped, exact-real reverse-verified rule, independent continuous rotations, public B, the given Markov transition matrix, and initial state zero. The safe-rule bound is sufficient rather than exact. The output expressly excludes transfer to finite rotations, Decimal arithmetic, PRNGs, language models, and rendered strings. A finite cap, successful-emission conditioning, source failure, or retry policy also changes the distribution and requires separate accounting. The code provides no such transfer.

The B=128 zero certificate must remain visibly vacuous. It does not establish security or small true total variation. A nonzero certificate for a larger B is not a detector-resistance measurement on the model experiments. This review does not change the earlier overall scientific recommendation.

## Complete-run reproduction and retained outputs

The complete certifier was run on core 13 into `/tmp/sp2027-independent-verified-certificate-20261021`, leaving the retained result directory untouched. Its `summary.json` and all three band-scan files are byte-identical to `results/sp2027-verified-certificate/`. The retained summary's SHA-256 is `42e09d46658fe989767907c63804382b146c23a3c0d38f0f813cebcc1695685c`. Its source hash matches the reviewed source, and all recorded scan hashes match their files.

For each output I independently checked the complete length sequence, the event and deficit numerators in every recorded row, monotonicity of the missing mass, the residual-length bound, all final fraction identities, and downward decimal rounding. The scans contain respectively 257, 833, and 3,137 consecutive rows. I also independently recomputed each candidate probability from run compositions and verified the exact inequality against every competing scanned upper bound and the collision tail. All three claimed global maxima are certified.

| B | k | m | Inclusive information band | Last scanned length | Maximizing length | Certified TV lower bound, rounded down |
|---|---|---|---|---|---|---|
| 128 | 8 | 9 | [120, 149] | 256 | 154 | 0.00000000 (vacuous) |
| 512 | 8 | 9 | [504, 533] | 832 | 593 | 0.13470320 |
| 2048 | 8 | 12 | [2040, 2075] | 3136 | 2353 | 0.42946703 |

The exact natural-band maxima, shown here only as decimal approximations, are 0.9271359514680589, 0.6374676826336709, and 0.41886155866634245. Each exact candidate exceeds the upper bound for every other length by a strictly positive rational margin. Those margins are approximately 8.7937453e-4, 3.8281990e-5, and 9.8671826e-5; identification of the maxima does not depend on floating comparisons.

The maximum missing masses across the respective scans are approximately 7.9527617e-13, 9.6633439e-12, and 1.3345531e-10. The residual-length upper bounds are approximately 2.4810403e-8, 2.6124148e-10, and 2.0552062e-16. All of these quantities are stored and compared as exact fractions. The B=128 unclipped lower bound is approximately -0.1549650596, explaining its retained zero certificate.

The finite constants in the table are supported by the audited arithmetic and complete reproduction within the stated ideal model. No code or output blocker remains to using them with that scope. They do not change the distributional exclusions or the previous overall scientific recommendation.

## Manuscript-consistency addendum

I checked the new `A finite certificate` paragraph in `paper/sections/04-stopping-security.tex` and `A Rational Finite-Size Certificate` subsection in `paper/sections/17-proofs.tex`. Their operator, survivor submeasure, terminal band, integer membership test, missing-mass bound, collision tail, source initialization, comparator, and scope match the audited mathematics. The main-text values 0.1347 and 0.4294 are conservative. Reading the retained fractions, without rerunning an artifact, gives conservative scan-plus-tail lower bounds approximately 0.1347032092224232 and 0.4294670302860559; their downward eight-decimal values are exactly the appendix's 0.13470320 and 0.42946703. B=128 remains vacuous. The exact-max refinement therefore leaves all displayed values unchanged, as stated.

No mathematical or numerical mismatch was found. I recommended one wording clarification to the parent agent: after defining `R=P⊙P`, the bound uses the ordinary row sums of R, so `Its row sums are at most 5/8` is clearer than `Its squared row sums`. The displayed matrix-moment inequality and constants are correct. I made no manuscript edits and did not change the acceptance recommendation.
