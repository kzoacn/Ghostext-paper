# Independent mathematical assessment of a finite verified-rule certificate

Review date: 2026-10-21. This note assesses a proposed sharpening of the existing ideal continuous-rotation theorem. It does not change the manuscript, experiment plan, model scripts, or previous scientific recommendation. No model inference was performed.

The proposed route is valid. I found no conditioning, operator, entry-law, or collision-moment gap. It gives a computable lower bound on total variation for the specified ideal Markov example, provided the implementation uses the exact band endpoints, accounts for every length, and retains its arithmetic error bounds. A complete implementation and its outputs still require a separate code audit before adoption.

## The safe-rule operator

Retain the one-sided safe interval and notation from the existing proof. Put \(z=d_{t-1}/W_{t-1}\), let the selected transition probability be \(q\), and set \(s=z/q\). For a fresh continuous uniform \(V\), a sufficient verified-success event is

\[
 V\in[1/2,\min(1,1/2+s)).
\]

On its complement the updated state is \(z'=\min(s,V)\le1/2\). Thus the transition with sufficient-success paths killed is, for nonnegative \(g\),

\[
 K_qg(z)=\int_0^{\min(s,1/2)}g(v)\,dv
          +(1-2s)_+g(s),\qquad s=z/q.
 \tag{1}
\]

The second term is evaluated only for \(s<1/2\); its notation must not cause an implementation to evaluate \(g\) outside its domain and then multiply by zero.

For decreasing \(g\), the right side decreases in \(s\). On a differentiable piece with \(s<1/2\), its derivative is

\[
 -g(s)+(1-2s)g'(s)\le0.
\]

For \(s\ge1/2\) it is constant. Downward jumps of a general decreasing \(g\) also preserve the inequality. Therefore \(q\le\rho\) implies \(K_qg\le K_\rho g\), and \(K_\rho\) preserves nonnegative decreasing functions.

Set \(h_0=1\) and \(h_{m+1}=K_\rho h_m\). Induction gives a uniform upper bound on survival for the next \(m\) safe-rule steps from any full surviving history. The induction can condition on the next selected token: fresh rotation makes its normalized position uniform, independently of that token, and every resulting \(K_qh_m\) is bounded by \(K_\rho h_m\). This argument accommodates later probabilities determined by the token history; it does not assume a fixed future token path after conditioning on survival. Actual reverse verification can accept outside the sufficient safe event, so its survival probability is no larger.

For rational \(\rho\), each \(h_m\) is an exact piecewise polynomial with rational coefficients and breakpoints among

\[
 0,\quad \tfrac12\rho^m,\ldots,\tfrac12\rho,\quad\tfrac12.
\]

The recurrence integrates each old piece, substitutes \(s=z/\rho\), and adds a constant final piece. Exact continuity checks are useful implementation checks; they are not a substitute for (1).

## Entry distribution and the terminal-information band

Let \(\kappa=\inf\{t:I_t\ge B+1\}\) in the uninterrupted process, and define the survivor submeasure

\[
 \mu(A)=P(\tau_{\rm v}>\kappa,\ z_\kappa\in A).
\]

On this event the safe test failed at \(\kappa\), so \(z_\kappa\le1/2\). The existing entry argument gives

\[
 \mu([0,u])\le\min\{1,u/(1-\rho)\}.
 \tag{2}
\]

This is an unnormalized submeasure. Dividing it by the probability of entry survival would destroy (2) and invalidate the proposed conclusion.

For \(\rho=3/4\), the right side of (2) is the CDF of the uniform distribution on \([0,1/4]\). Since \(h_m\) is nonnegative and decreasing, integration by parts, or elementary first-order stochastic dominance with missing mass placed to the right, gives

\[
 P(\tau_{\rm v}>\kappa+m)
 \le\int h_m\,d\mu
 \le H_m:=4\int_0^{1/4}h_m(z)\,dz.
 \tag{3}
\]

The domination remains valid when \(\mu\) has total mass below one. It requires no success-conditioned entry law. The factorization used to derive (2) conditions on tokens through \(\kappa\), which is a token-dependent time; it does not condition on verification survival.

The source is the two-state chain

\[
 P=\begin{pmatrix}3/4&1/4\\1/2&1/2\end{pmatrix},
\]

started from the same specified known state as the comparison source. Its positive transition surprisals are at most \(b=2\). Consequently \(I_\kappa<B+3\), and (3), together with the existing lower-tail bound, yields

\[
 P\{I_{\tau_{\rm v}}\notin[B-k,B+3+2m]\}
 \le 4\,2^{-k}+H_m.
 \tag{4}
\]

Here \(k,m\) are nonnegative integers. Both endpoints in (4) are integers. An inclusive upper band is conservative even though the entry overshoot bound is strict.

The computed \(H_m\) is exact for this relaxed operator-and-entry bound. It is not the actual verified stopping tail: both the worst-case choice \(q=\rho\) and the extremal entry distribution can be loose, and the sufficient safe event omits other successful verification events.

## An exact band test and a rigorous lower-mass DP

For a path of \(n\) transitions, write \(u=\#00\), \(v=\#01\), and \(M=n+u+v\). Its information is

\[
 I_n=M-\log_2(3^u).
 \tag{5}
\]

Let \(f_u=\operatorname{bit\_length}(3^u)-1\) and \(c_u=f_u+\mathbf1_{\{u>0\}}\). These are exactly the floor and ceiling of \(\log_2(3^u)\). In particular, \(u=0\) is the integer-log exception and must be retained. For integer \(L,U\), band membership is exactly

\[
 L\le I_n\le U
 \quad\Longleftrightarrow\quad
 M-c_u\ge L\ \text{ and }\ M-f_u\le U.
 \tag{6}
\]

No floating logarithm or tolerance is needed. Equivalently, at a fixed \(u\) the integer \(v\) range runs from \(L-n-u+c_u\) through \(U-n-u+f_u\), inclusive.

Use denominator \(D=2^{60}\). A DP state consists of the current Markov state and \((u,v)\); store an integer \(w\) representing a lower mass \(w/D\). Propagate state-zero mass by \(\lfloor3w/4\rfloor\) and \(\lfloor w/4\rfloor\), and state-one mass by two copies of \(\lfloor w/2\rfloor\). Merge the resulting integer contributions by addition. Induction proves a statewise lower bound, because each transition weight and every merging operation is nonnegative.

At depth \(n\), let \(S_n\) be the sum of all stored masses and \(E_n\) the sum over states satisfying (6). Since the exact chain has total mass one,

\[
 \frac{E_n}{D}
 \le Q(L\le I_n\le U)
 \le \frac{E_n+D-S_n}{D}.
 \tag{7}
\]

The entire missing mass is an error budget; it must not be renormalized away. The upper side of (7) is at most one because \(E_n\le S_n\). If an implementation prunes other states, their omitted mass must also remain in \(D-S_n\).

Unsigned 64-bit arithmetic suffices for this specific representation: the total stored mass is at most \(2^{60}\), and the largest intermediate product is \(3w\le3\cdot2^{60}<2^{64}\). Integer multiplication followed by a shift is required; floating multiplication by 0.75 or 0.5 would not provide this proof. Bounds on array indices, subtraction, and accumulators must also be respected by the implementation.

## Covering all lengths with the collision moment

A finite scan alone cannot establish the supremum over lengths. The proposed squared-transition argument supplies a particularly convenient exact tail.

Let \(R=P\odot P\), where the product is entrywise. For a known initial state \(x_0\),

\[
 E_Q[2^{-I_n}]
 =\sum_{y_{1:n}}Q_n(y_{1:n})^2
 =e_{x_0}^{\mathsf T}R^n\mathbf1.
\]

The squared row sums are \(5/8\) and \(1/2\). Thus \(R\mathbf1\le(5/8)\mathbf1\), and nonnegativity gives

\[
 E_Q[2^{-I_n}]\le(5/8)^n,
 \qquad
 Q(I_n\le U)\le 2^U(5/8)^n.
 \tag{8}
\]

The second inequality is Markov's inequality applied to the nonnegative variable \(2^{-I_n}\). It requires no independence of successive information increments. For all \(n>T\), the right side is bounded by its exact rational value at \(T+1\).

Combining (7) and (8), define

\[
 \widehat A=
 \min\left\{1,\max\left(
 \max_{0\le n\le T}\frac{E_n+D-S_n}{D},
 \;2^U(5/8)^{T+1}\right)\right\}.
 \tag{9}
\]

Then \(\sup_n Q(L\le I_n\le U)\le\widehat A\). The finite-scan and tail bounds combine by a maximum, because the target is a supremum over lengths. A sum would also be conservative but is unnecessary. Length zero must be included if it can lie in the band; provably empty early lengths may be skipped. The initial source state and any initial-information convention must match (5).

As an alternative finite-horizon proof, \(\log_2(4/3)>2/5\), since \((4/3)^5>4\). For positive integer \(U\), every \(n\ge\lceil5U/2\rceil\) is outside the upper band. The collision bound permits a shorter scan and does not rely on an unchecked floating cutoff.

## Resulting certificate and its scope

Take \(L=B-k\), \(U=B+3+2m\), and let \(C_B\) be the natural Markov source sampled independently at a length drawn from the ideal verified rule's own marginal length distribution. The visible token event \(L\le I_n\le U\) has stego probability at least \(1-4\,2^{-k}-H_m\) and comparator probability at most \(\widehat A\). Therefore

\[
 \boxed{\operatorname{TV}(P_B^{\rm verified},C_B)
 \ge\max\{0,1-4\,2^{-k}-H_m-\widehat A\}.}
 \tag{10}
\]

All terms can remain rational until presentation. A displayed certified decimal lower bound must be rounded downward. Deterministically choosing the best \((k,m,T)\) among fully certified candidates is valid optimization of sufficient bounds; it is not statistical testing of model outcomes. A vacuous result for a smaller \(B\) establishes only that this certificate is weak there.

This is a finite certificate for the exact-real, independent continuous-uniform-rotation mechanism and the specified Markov source. The ideal rule runs until verified termination; a finite token cap or conditioning on successful emission changes the distribution. It applies to every fixed payload integer under the assumptions of the existing proof, and hence to independent payload mixtures. It does not transfer automatically to finite rotation grids, Decimal arithmetic, a PRNG, model-source failure, retries, rendered-string serialization, or a different source with different probability bounds. In particular, the previous finite-grid bridge that excluded sender verification does not establish such a transfer. The bound concerns the complete stopped law against its stated independent-length comparator; it is not exact TV, an upper bound on detection risk, or a theorem about ordinary language-model EOS generation.

## Independent arithmetic checks

I implemented a separate exact-Fraction recurrence through \(m=24\). All piece boundaries were continuous, and 825 independent direct-integral evaluations agreed with the resulting polynomials. Selected values are

\[
 H_0=1,\quad H_1=5/6,\quad H_2=37/54,\quad
 H_3=1999439/3538944.
\]

Further values, displayed as approximations only, are \(H_8=0.24693733449447175\), \(H_9=0.21220410814000198\), \(H_{12}=0.13604641098058762\), \(H_{16}=0.07606565983653257\), \(H_{20}=0.042722919929649564\), and \(H_{24}=0.024029919169554395\).

An independent exact integer-mass DP with denominator \(4^n\) checked the lower-mass DP through \(n=40\). All 11,521 statewise inequalities, 69,126 band-membership checks against integer-power comparisons, and 205 event-bound checks passed. The fixed-point missing mass at \(n=40\) was exactly \(699/2^{60}\).

I also checked an independent closed-form path count. Starting from state zero and ending in state \(s\), let \(x=n-u-2v+s\). For \(v\ge1\), the counts are

\[
 N_{n,u,v,0}=\binom{u+v}{v}\binom{x+v-1}{v-1},
 \qquad
 N_{n,u,v,1}=\binom{u+v-1}{v-1}\binom{x+v-1}{v-1},
\]

with zero count for infeasible parameters, plus the all-zero path when \(s=0,v=0,u=n\). These formulas matched 20,832 cells of an unweighted exact DP through \(n=30\). Multiplying them by \(3^u/2^{n+u+v}\) and summing the exact band at \(n=593\), \([L,U]=[504,533]\), gives

\[
 Q(504\le I_{593}\le533)\approx0.6374676826336709.
\]

This independently supports the root agent's preliminary fixed-point upper value of approximately \(0.6374676826375748\) at that length. Its reported \(B=512,k=8,m=9\) lower-bound arithmetic, approximately 0.1347032092, is consistent with (10). I have not independently rerun the entire preliminary maximizing-length scan, and these probe values are not a substitute for the planned standalone certifier and its subsequent audit.
