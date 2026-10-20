**Independent review of the finite verified-rule certificate — 21 October 2026**

**Finding: I found no mathematical error that invalidates the stated finite bounds.** The manuscript correctly limits them to the specified Markov source, public initial state zero, and the uncapped exact-real rule with fresh independent continuous rotations. Confidence is high for the argument and the checks described below. This is a separate mathematical review, without a new overall paper recommendation. No model inference or full dense certifier run was performed, and the manuscript and sources were not edited.

**Assessed versions.** SHA-256 values:

- `scripts/certify_verified_stopping.py`: `f32a0c6ff8a9271a02c7f2d15cdfe3afc07cabb8176815b32420bd9a70ff0b61`.
- `results/sp2027-verified-certificate/summary.json`: `42e09d46658fe989767907c63804382b146c23a3c0d38f0f813cebcc1695685c`. I also checked the three scan hashes recorded by this summary.
- `paper/sections/04-stopping-security.tex`: `e1e2370abfd49c2f9761e683fdc6e8251b689e0e6204b7ba424027e02bcf2bf1`.
- `paper/sections/17-proofs.tex`: `cb5d7cde30f72be4eda1d0324e7f7b33dc0037387f78727dabbed714be5ce6ae`.

**Killed operator and verified survival.** Rewriting the earlier killed kernel gives
`K_q g(z) = G(min(z/q,1/2)) + (1-2z/q)_+ g(z/q)`.
For nonnegative nonincreasing `g`, the operator is nonincreasing in `z/q`, so `q <= rho` implies `K_q g <= K_rho g`. This also follows directly from the original min-kernel, without assuming global differentiability. The operator preserves nonnegativity and monotonicity. Starting with `h_0=1`, induction bounds survival from every surviving full history: condition on the next token, apply its `K_q`, and dominate each term by `K_rho`. No claim that the scalar safe width alone contains the entire verification state is needed. Since the sufficient safe event is only a subset of actual verified acceptance, `h_s` is an upper bound on actual survival, not its exact probability.

**Survivor submeasure.** The entry argument bounds the unconditioned safe-width distribution; restricting to surviving paths therefore gives `mu([0,u]) <= min(1,4u)` without dividing by survival. The integration step is valid. One explicit justification is to add any missing mass of `mu` at `1/2`. This can only increase the integral of nonnegative `h_s`, and the resulting probability law is stochastically larger than a uniform variable on `[0,1/4]`. For decreasing `h_s`, its expectation is thus at most `4 integral_0^(1/4) h_s`. The resulting `H_s` controls survival beyond `kappa+s`. Since the entry overshoot is less than two bits and each subsequent increment is at most two bits, the upper endpoint `B+3+2s` is valid. Adding the early-stop bound gives the stated band miss probability.

**Exact band membership and dynamic program.** For counts `u=#(0->0)` and `v=#(0->1)`, a path has probability `3^u / 2^(n+u+v)`. Hence the information formula is correct. Because `3^u` is a power of two only when `u=0`, its integer floor and ceiling logarithms give precisely the two inclusive band tests in the manuscript; no floating tolerance is needed. The array updates correctly increment `u` or `v` for transitions from state zero and preserve both counts for transitions from state one.

Each rounded state mass remains a lower bound by induction. All discarded fractions contribute to the global deficit, so adding `D-S_n` to the event count is a valid upper bound for any event. The implementation does not renormalize. The unsigned-integer safety argument also holds: total stored mass is at most `D=2^60`, each merge is bounded by that total, and `3w < 2^62`. The exact support test `2n<L` justifies zero event probability at the skipped early lengths.

**All-length tail and natural maximum.** With `R=P elementwise-multiplied by P`, the row sums are `5/8` and `1/2`. Therefore `E_Q[2^(-I_n)] <= (5/8)^n`, and Markov's inequality gives `Q(I_n<=U) <= 2^U(5/8)^n`. This decreases with `n`, so its value at `T+1` covers every unscanned length. A supremum is sufficient because the independent comparator averages over one output length; no union-bound sum or estimate of the encoder's length law is required. The refinement to an exact natural maximum is valid when every other scanned upper bound and the tail bound lie below the exact candidate probability. The retained records satisfy that comparison for lengths 154, 593, and 2353.

**Independent arithmetic checks.** Using separate symbolic polynomial integration, I reproduced the exact `H_0` through `H_12`, including `H_9 = 0.21220410814000198...` and `H_12 = 0.13604641098058762...`. A separate sparse integer implementation checked the exact and downward-rounded state laws through length 60, agreeing with the NumPy updates and run-composition counts. It performed 37,881 state checks, 151,524 exact integer-membership checks, and 244 event-bound checks. I independently derived and evaluated the zero/one run-composition formula at each reported maximizing length, both neighboring lengths, and the scan cutoff. Those exact probabilities lie inside the corresponding stored bounds. I checked the arithmetic of all 4,227 retained scan rows and the final rational assembly.

| B | Band | Natural-band maximum | Certified TV lower bound, rounded down |
|---:|---|---:|---:|
| 128 | [120,149] | 0.927135951468059... | 0 |
| 512 | [504,533] | 0.637467682633671... | 0.13470320 |
| 2048 | [2040,2075] | 0.418861558666342... | 0.42946703 |

The scan-only formula and the refined exact-maximum formula produce the same displayed lower bounds. The 128-bit calculation is vacuous; it does not establish TV zero. These checks complement inspection of the full recurrence; I did not independently regenerate every large dense DP row.

**Scope and wording.** The uniformity of the argument over every fixed payload is justified by fresh continuous rotation and the message-independent one-sided safe width. Independent payload mixtures inherit the same public event bound, using their own marginal-length comparator. No uniform-payload assumption is needed for this particular ideal RRC result. The exclusions for finite rotation grids, Decimal implementations, success conditioning, and arbitrary text serialization are appropriate. In particular, lossy serialization can reduce TV, so this token-transcript lower bound cannot automatically become a rendered-text lower bound. The main paragraph and appendix currently preserve that distinction and do not equate the certificate with model AUC or exact verified-rule TV.

There is no required mathematical correction from this review. A small optional wording improvement is to use “nonincreasing” consistently, since `h_0` is constant; the derivative explanation may be understood piecewise for the actual polynomial iterates, or replaced by the direct min-kernel monotonicity argument.
