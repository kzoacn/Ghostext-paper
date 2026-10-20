# Independent assessment of the proposed termination extension

Date: 2026-10-21. This is a proof assessment, not a revised acceptance recommendation. I inspected the existing stopping proof and the pinned RRC core at commit `dae326259e4fca8bc4fcf460dafdbc0e88a0a71a`. I made no manuscript or implementation changes and ran no language-model jobs.

The strongest extension I can presently justify has three instantiations: the published ideal midpoint rule, ideal arithmetic-prefix termination with a uniform continuous target, and the ideal midpoint rule with sender-side reverse verification. The verified-rule result needs a new argument; its old stopping hazard is not valid after verification. A one-sided interval that is guaranteed to decode correctly supplies the needed upper tail, under a uniform upper bound on positive next-token probabilities.

The general event inequality is correct but elementary. The substantive work is establishing the terminal information band for these mechanisms and establishing anti-concentration for a genuinely dependent source. A positive binary Markov example permits an explicit elementary anti-concentration proof, avoiding an unspecified Berry–Esseen constant. A standard Markov Berry–Esseen theorem also supports a broader, less explicit statement.

## 1. Comparator and the general event inequality

Fix a public source \(Q\), including its initial context/state, and write

\[
 I_n(y_{1:n})=-\log_2 Q(y_{1:n}).
\]

Let \(P_B\) be an almost surely finite stopped-output law. Its comparator draws \(L\) from the exact marginal law of its own stopping time, independently of a fresh \(Q\) trajectory. Thus

\[
 C_B(y_{1:n},n)=P_B(\tau=n)Q(y_{1:n}).
\]

This independence is essential. A control using the same content-dependent stopping rule is a different law. The observed length and information score must be measurable from the transcript being compared.

Suppose

\[
 P_B\{I_\tau\in[B-k_B,B+r_B]\}\ge1-\delta_B,
 \quad P_B\{\tau<n_B\}\le\eta_B,
\]

and

\[
 \sup_{n\ge n_B,x}Q\{I_n\in[x,x+k_B+r_B]\}\le\alpha_B.
\]

Using the event consisting of the information band and \(\tau\ge n_B\) gives

\[
 \operatorname{TV}(P_B,C_B)\ge1-\delta_B-\eta_B-\alpha_B.
\]

One can retain the factor \(P_B(\tau\ge n_B)\) multiplying \(\alpha_B\), but that refinement is not the main result.

There is a more useful simplification when every positive token probability is at least \(2^{-b}\). Then \(I_n\le nb\) on every supported trajectory. The information-band event itself excludes

\[
 n<n_0=\left\lceil\frac{B-k_B}{b}\right\rceil
\]

when \(B>k_B\). Consequently no short-length error term is needed:

\[
 \boxed{\operatorname{TV}(P_B,C_B)\ge
 1-\delta_B-
 \sup_{n\ge n_0,x}Q\{I_n\in[x,x+k_B+r_B]\}.}
 \tag{1}
\]

This uses the deterministic bound under the fresh reference trajectory, not a concentration claim about the encoder's length.

## 2. Markov Berry–Esseen route and its limitation

For a fixed finite-state irreducible aperiodic Markov source with positive varentropy rate \(\sigma^2\), a source-dependent constant \(A<\infty\) gives

\[
 \sup_z\left|Q\!\left\{\frac{I_n-nH}{\sigma\sqrt n}\le z\right\}
 -\Phi(z)\right|\le\frac{A}{\sqrt n}.
\]

Theorem 21 and Section VI of [Kontoyiannis and Verdú, *Optimal Lossless Data Compression: Non-Asymptotics and Asymptotics*, IEEE TIT 60(2), 2014](https://www.dpmms.cam.ac.uk/~ik355/PAPERS/SVYK-J.pdf), DOI `10.1109/TIT.2013.2291007`, provide the primary source. Section VI explicitly permits a nonstationary initial distribution. The remarks preceding Theorem 21 explicitly say that this general bound does not supply a numerical value of \(A\). It must not be presented as an explicit numerical constant.

Our consequence is

\[
 \sup_x Q\{I_n\in[x,x+w]\}
 \le \frac{w/(\sigma\sqrt{2\pi})+2A}{\sqrt n}.
 \tag{2}
\]

For closed intervals, take the left limit of the distribution function at the lower endpoint; continuity of the Gaussian distribution gives the same bound. No nonlattice assumption is needed.

A fixed public initial state is covered by taking the first emitted-state distribution to be its transition row. A finite maximum over initial states can be used if the statement is to be uniform over them.

Positive entropy is not a replacement for positive varentropy. Nor is nonuniformity of transition rows by itself a proof of positive varentropy. For a broad statement, impose \(\sigma^2>0\) explicitly. For the concrete example below, it can be proved directly.

Combining (1) and (2), an information band of width \(o(\sqrt B)\), error tending to zero, and a fixed finite \(b\) imply TV tending to one. This is a conditional theorem about the specified mechanisms and comparator, not a universal impossibility theorem for all finite-message steganography.

## 3. Explicit anti-concentration for a genuinely dependent source

Consider a positive binary transition matrix \(P\), with a fixed public \(Y_0\). Let \(m=\lfloor n/2\rfloor\). Condition on the even states \(Y_0,Y_2,\ldots,Y_{2m}\), and, when \(n\) is odd, also on the final state \(Y_n\).

The \(m\) remaining odd bridge states are conditionally independent. A bridge with endpoints \((a,b)\) has

\[
 \theta_{ab}=
 \frac{P_{a0}P_{0b}}{P_{a0}P_{0b}+P_{a1}P_{1b}},
 \qquad
 d_{ab}=\left|\log_2
 \frac{P_{a0}P_{0b}}{P_{a1}P_{1b}}\right|.
\]

Its contribution to \(I_n\) takes two values separated by \(d_{ab}\). The optional final edge for odd \(n\) contributes a constant after this conditioning.

Assume all four \(d_{ab}\) are positive. At least \(m/4\) bridges have one common endpoint pair. After conditioning on every other odd bridge, the remaining contribution is a shifted, possibly reflected, scaled binomial variable with at least \(m/4\) trials. Define

\[
 d_{\min}=\min_{a,b}d_{ab},\qquad
 K_{\max}=\max_{a,b}
 \frac{\sqrt\pi}{2\sqrt{2\theta_{ab}(1-\theta_{ab})}}.
\]

Using the existing elementary binomial atom bound, and then removing the conditioning, gives for \(n\ge2\)

\[
 \boxed{
 \sup_x Q\{I_n\in[x,x+w]\}
 \le
 \min\!\left\{1,\,
 \frac{2K_{\max}\bigl(\lfloor w/d_{\min}\rfloor+1\bigr)}
 {\sqrt{\lfloor n/2\rfloor}}\right\}.
 }
 \tag{3}
\]

The chosen endpoint pair can depend on the conditioned even-state sequence. This causes no problem because the displayed bound is uniform over all four possibilities.

A particularly simple example is

\[
 P=\begin{pmatrix}3/4&1/4\\1/2&1/2\end{pmatrix}.
 \tag{4}
\]

Its bridge parameters are

| Endpoints | \(\theta_{ab}\) | \(d_{ab}\) |
|---|---:|---:|
| \(00\) | \(9/11\) | \(\log_2(9/2)\) |
| \(01\) | \(3/5\) | \(\log_2(3/2)\) |
| \(10\) | \(3/5\) | \(\log_2(3/2)\) |
| \(11\) | \(1/3\) | \(1\) |

Thus

\[
 d_{\min}=\log_2(3/2),\quad
 K_{\max}=\frac{11\sqrt\pi}{12},\quad
 b=2,\quad a=\log_2(4/3).
 \tag{5}
\]

The row entropies are approximately \(0.811278\) and \(1\) bits. The information increments really are dependent: in stationarity their lag-one covariance is approximately \(0.0393683>0\). This is not a chain with permutation rows whose information increments remain IID.

Positive varentropy also follows without a covariance calculation. Conditional on the even-state skeleton,

\[
 \operatorname{Var}(I_n\mid\text{skeleton})
 =\sum_{j=1}^{m}\theta_{a_jb_j}(1-\theta_{a_jb_j})d_{a_jb_j}^2
 \ge m\,\frac6{25}\bigl[\log_2(3/2)\bigr]^2.
\]

The law of total variance and existence of the finite-state variance limit imply

\[
 \sigma^2\ge\frac3{25}\bigl[\log_2(3/2)\bigr]^2>0.
\]

For reference, a direct covariance calculation gives

\[
 H=\frac a2+\frac23,\qquad
 \sigma^2=\frac7{12}a^2-\frac{13}{9}a+\frac{25}{27}
 \approx0.4269101.
\]

The explicit bound (3) is valid but conservative. It should not be described as a useful numerical attack guarantee at the experimental payload lengths without evaluating it there.

## 4. Published ideal midpoint stopping

Assume throughout this section that all selected probabilities satisfy

\[
 2^{-b}\le q_t(y_t\mid y_{<t})\le\rho<1,
 \qquad a=-\log_2\rho>0.
 \tag{6}
\]

Fresh independent continuous rotations give the published midpoint hazard

\[
 h_t=\min(1,2^{I_t-B}).
\]

The existing proof is pathwise in the information increments and does not require IID tokens. It gives, for \(k\ge0\),

\[
 P_B(I_\tau<B-k)\le\frac{2^{-k}}{1-\rho},
 \qquad I_\tau<B+b.
 \tag{7}
\]

The lower tail follows by summing the candidate hazards in reverse order, using \(I_{t+1}-I_t\ge a\). The upper bound follows because the first crossing of \(B\) stops with certainty and overshoots by at most \(b\).

Combining (7) with either (2) or (3) proves the Markov extension. Taking \(k\) of order \(\log B\) yields

\[
 \operatorname{TV}(P_B,C_B)
 \ge1-O_Q(\log B/\sqrt B).
\]

The broad finite-state version can allow deterministic edges by replacing the one-step lower increment with a block lower bound. That extension is unnecessary for the explicit positive matrix (4); retaining (6) is cleaner, especially because it is also used in the verified-rule proof below.

## 5. Ideal arithmetic-prefix termination

Take \(U\) uniform on \([0,1)\), with the \(B\)-bit payload defined as \(\lfloor2^B U\rfloor\). Its remaining binary expansion is independent uniform continuation, up to null binary-expansion ambiguities. Generate the standard nested \(Q\)-arithmetic intervals containing \(U\), and stop when the current interval is contained in one payload cell.

The interval at depth \(n\) has length \(Q(Y_{1:n})=2^{-I_n}\). Containment implies \(I_\tau\ge B\).

Let \(\kappa\) be the first depth with \(I_\kappa\ge B+r\), for \(r\ge0\). Its arithmetic intervals form an antichain partition, up to a null exceptional set, assuming the source intervals shrink almost surely. Each has length at most \(2^{-B-r}\). An unresolved interval contains an interior payload-cell boundary. Disjoint intervals can be charged to distinct boundaries, of which there are \(2^B-1\). Therefore

\[
 P(\tau>\kappa)\le(2^B-1)2^{-B-r}<2^{-r}.
\]

If individual surprisals are at most \(b\), \(I_\kappa<B+r+b\). Hence

\[
 \boxed{
 P\{B\le I_\tau\le B+r+b\}\ge1-2^{-r}.
 }
 \tag{8}
\]

The argument is valid even though some trajectories have already stopped before \(\kappa\): extend their arithmetic trajectories for the proof. It is not a success-conditioned argument. The bound and almost-sure interval shrinking also imply almost-sure termination.

At a fixed exogenous depth \(N\), use the same continuous uniform target and always send exactly \(N\) tokens. The output law is exactly \(Q_N\). Declare prefix-recovery failure if its interval is not contained in a payload cell. Split the unresolved intervals into those with \(I_N<B+r\) and the remaining fine intervals. The latter are disjoint, each has width at most \(2^{-B-r}\), and each straddles a payload boundary. This proves

\[
 \boxed{
 P(\text{prefix recovery fails at }N)
 \le Q(I_N<B+r)+2^{-r}.
 }
 \tag{9}
\]

There is no conditioning denominator and no missing overshoot constant in (9). A random exogenous length independent of the trajectory is handled by averaging over it. The exact output-law assertion relies on continuous uniform \(U\), hence on a uniform payload mixture and independent continuation. It does not automatically apply to a fixed chosen payload, a finite integer guard, or a practical encrypted packet.

## 6. Ideal verified-midpoint stopping: a sufficient safe interval

The following proof concerns exact real arithmetic and independent continuous uniform rotations. It matches the mechanism “check the midpoint condition, reverse the midpoint, accept only if it rounds to the original message.” It is not a theorem about the actual Decimal precision, finite rotation grid, PRNG, text replay, or source failures of upstream software.

Let the original message be any fixed integer \(m\in\{0,\ldots,2^B-1\}\). Consider the uninterrupted rotated process, even after any hypothetical stopping time. Write its selected intervals as \([L_t,H_t)\), widths as \(W_t=2^{B-I_t}\), and current point as \(X_t\).

Maintain a half-open interval

\[
 [X_t,X_t+d_t)
\]

whose reverse replay is exactly \([m,m+d_t)\), point by point by translation. Initialize \(d_0=1/2\). This interval fits in the original domain even for \(m=0\), and every point in its reverse image rounds to \(m\).

After a rotation and selection, put

\[
 d_t=\min(d_{t-1},H_t-X_t).
 \tag{10}
\]

This preserves the invariant. The old \(d_{t-1}\) prevents crossing an older reverse-map cut; the new right margin prevents crossing the new selected-interval boundary, and hence the current parent rotation cut.

The interval must be half-open. Its right endpoint may be an earlier modulo discontinuity even when it is interior to the current interval. Exact rational checks exposed this endpoint issue; using a strict upper inequality resolves it. Under continuous rotations this affects no probability.

The sufficient event

\[
 0\le (L_t+H_t)/2-X_t<d_{t-1}
 \tag{11}
\]

guarantees both midpoint acceptance and verified recovery. The midpoint condition holds because \(d_{t-1}\le1/2\). Therefore (11) does not itself require \(W_t\le1\). The verified algorithm can also accept outside this sufficient event, so bounds on avoiding (11) are upper bounds on verified survival.

Fresh uniform rotation gives, jointly and conditionally on every past history,

\[
 P(Y_t=i,\ U_t\in du\mid\text{past})=q_t(i)\,du,\qquad
 U_t=(X_t-L_t)/W_t.
 \tag{12}
\]

In the uninterrupted process the token trajectory has law \(Q\). Conditional on any token path, the \(U_t\)'s are independent uniforms. This remains useful despite conditioning on survival: the argument below keeps a survivor indicator and never divides by its probability.

### 6.1 A uniform two-step killed-kernel bound

Let \(z=d_{t-1}/W_{t-1}\), \(q=W_t/W_{t-1}\), \(s=z/q=d_{t-1}/W_t\), and \(V=1-U_t\). The sufficient success event is

\[
 V\in[1/2,\min(1,1/2+s)),
\]

with immaterial endpoint conventions. On failure,

\[
 z'=d_t/W_t=\min(s,V)\le1/2.
 \tag{13}
\]

For a nonnegative test function \(f\), the transition with successful paths killed is

\[
 (K_qf)(z)=
 \int_0^{1/2} f(\min(z/q,v))\,dv
 +(1/2-z/q)_+f(z/q).
 \tag{14}
\]

Choose \(f(z)=z^{-1/2}\). Direct integration gives

\[
 K_qf(z)=
 \begin{cases}
 \sqrt{q/z},&z<q/2,\\
 \sqrt2,&z\ge q/2.
 \end{cases}
 \tag{15}
\]

For every nonnegative nonincreasing function \(g\), \(q\le\rho\) implies \(K_qg\le K_\rho g\): increasing \(z/q\) shrinks the survival region and increases the argument of \(g\). Also, \(K_\rho f\) is nonincreasing. Thus the two-step result below dominates all history-dependent choices of two probabilities bounded by \(\rho\), including mixtures over selected tokens.

For \(0<z\le1/2\), direct integration gives

\[
 K_\rho^2f(z)=
 \begin{cases}
 \rho z^{-1/2},&0<z<\rho^2/2,\\
 \sqrt2(1+\rho/2-z/\rho),&\rho^2/2\le z<\rho/2,\\
 (1+\rho)/\sqrt2,&\rho/2\le z\le1/2.
 \end{cases}
 \tag{16}
\]

Consequently

\[
 \boxed{K_\rho^2f(z)\le\lambda f(z),\qquad
 \lambda=(1+\rho)/2<1.}
 \tag{17}
\]

For the middle regime, the maximum of the ratio to \(f(z)\) is

\[
 \sqrt{\rho(2+\rho)^3/27}\le(1+\rho)/2.
\]

The last inequality follows from

\[
 27(1+\rho)^2-4\rho(2+\rho)^3
 =(1-\rho)(4\rho^3+28\rho^2+49\rho+27)\ge0.
\]

The first and last regimes of (16) give the same bound immediately. Thus (17) is an analytic inequality; numerical checks are merely supplementary.

### 6.2 Entering the small-width region without success conditioning

Let

\[
 \kappa=\inf\{t:I_t\ge B+1\}.
\]

Under (6), \(\kappa\) is finite, \(W_\kappa\le1/2\), and \(I_\kappa<B+1+b\). From (10),

\[
 z_\kappa=\frac{d_\kappa}{W_\kappa}
 =\min\left\{\frac{1}{2W_\kappa},
 \min_{1\le j\le\kappa}
 \frac{V_jW_j}{W_\kappa}\right\}.
\]

Conditional on the token path through \(\kappa\), for \(0<u\le1\),

\[
 P(z_\kappa<u\mid\text{token path})
 \le u\sum_{j=1}^{\kappa}\frac{W_\kappa}{W_j}
 \le\frac{u}{1-\rho}.
 \tag{18}
\]

Here \(1/(2W_\kappa)\ge1\), and the ratios satisfy \(W_\kappa/W_j\le\rho^{\kappa-j}\). The dependence of \(\kappa\) on the tokens causes no difficulty because the conditional uniforms in (12) remain independent of that token path.

Since \(0<z_\kappa\le1\), integrating (18) gives

\[
 E[f(z_\kappa)]\le\frac2{\sqrt{1-\rho}}.
 \tag{19}
\]

On the event that verified stopping has not occurred by \(\kappa\), the sufficient event (11) also failed at \(\kappa\); therefore \(z_\kappa\le1/2\) by (13). This handles the possible \(z_\kappa>1/2\) on other paths. No preliminary extra step is needed.

Apply (17) in pairs of subsequent steps, keeping the survivor indicator:

\[
 \begin{aligned}
 P(\tau_{\rm v}>\kappa+2j)
 &\le \lambda^j
 E[{\bf1}_{\{\tau_{\rm v}>\kappa\}}f(z_\kappa)]\\
 &\le \frac2{\sqrt{1-\rho}}\lambda^j .
 \end{aligned}
 \tag{20}
\]

This is a bound on the unconditioned survival probability. It does not assert the same moment bound after dividing by \(P(\tau_{\rm v}>\kappa)\). It also proves almost-sure termination of the ideal verified rule.

Since every later information increment is at most \(b\), (20) implies

\[
 \boxed{
 P\{I_{\tau_{\rm v}}>B+1+b+2jb\}
 \le\frac2{\sqrt{1-\rho}}
 \left(\frac{1+\rho}{2}\right)^j.
 }
 \tag{21}
\]

Verification can only veto candidate midpoint stops. Its lower information tail is therefore still bounded by (7). Combining the two tails yields

\[
 P\{I_{\tau_{\rm v}}\notin[B-k,\ B+1+b+2jb]\}
 \le
 \frac{2^{-k}}{1-\rho}
 +\frac2{\sqrt{1-\rho}}\lambda^j.
 \tag{22}
\]

Take \(k\) and \(j\) proportional to \(\log B\). Then (1), with either anti-concentration bound, gives

\[
 \boxed{\operatorname{TV}(P^{\rm verified}_B,
 C^{\rm verified}_B)
 \ge1-O_Q(\log B/\sqrt B).}
 \tag{23}
\]

The comparator in (23) uses the verified rule's own exact marginal length law. This is an extension of the separation conclusion, not an extension of the old explicit hazard formula.

For the concrete matrix (4), \(\rho=3/4\), \(b=2\), and \(\lambda=7/8\). Equation (22) becomes

\[
 P\{I_{\tau_{\rm v}}\notin[B-k,\ B+3+4j]\}
 \le4\,2^{-k}+4(7/8)^j.
 \tag{24}
\]

Together with (3) and (5), this is a completely explicit finite-\(B\) lower bound, albeit a loose one.

## 7. A dependent zero-varentropy counterexample

Use three states with transitions

\[
 P(i,i)=P(i,i+1\bmod3)=1/2.
\]

This chain is irreducible and aperiodic, with a genuine restriction on the next state and positive entropy rate. Conditional on a fixed initial state, every supported length-\(n\) path has probability \(2^{-n}\). Thus \(I_n=n\) and the varentropy rate is zero.

For the published midpoint rule, both width and hazard depend only on \(n\). Its stopped law factors as \(P(\tau=n)Q_n\), so the independently length-matched TV is exactly zero for every \(B\).

For ideal arithmetic-prefix coding with two equal-probability ordered children at every step, every depth-\(B\) arithmetic interval is exactly one payload cell. The stopping time is \(B\), and the complete law is again exactly its length-matched comparator.

The ideal verified midpoint rule also has exact TV zero on this particular source. To see this, fix a depth \(t\), let \(Z_j\) be the point obtained after reversing the final midpoint through steps \(t,t-1,\ldots,j+1\), and put \(e_j=Z_j-X_j\). Initially,

\[
 e_t=W_t(1/2-U_t).
\]

The forward and inverse rotation formulas imply

\[
 e_{j-1}=
 \bigl((X_{j-1}-L_{j-1}+e_j)\bmod W_{j-1}\bigr)
 -(X_{j-1}-L_{j-1})
 =
 W_{j-1}\!\left(
 \left(U_{j-1}+\frac{e_j}{W_{j-1}}\right)\bmod1-U_{j-1}
 \right).
 \tag{25}
\]

Here \(U_0=m/2^B\). To derive (25), subtract the forward rotation from the inverse formula before taking the modulo; the rotation offset cancels modulo the parent width. All absolute interval locations and selected child indices therefore disappear.

Because every supported edge has probability \(1/2\), \(W_j=2^{B-j}\) is deterministic. The midpoint test depends only on \(e_t\), and reverse verification tests whether \(m+e_0\) rounds to \(m\), equivalently \(-1/2<e_0\le1/2\). Thus the entire stopping decision at every depth is a function only of \(m\) and \(U_1,\ldots,U_t\). By (12), these uniforms are independent of the uninterrupted token trajectory. The verified stopping time is therefore independent of that trajectory, and its complete law factors exactly as

\[
 P_B^{\rm verified}(Y_{1:t}=y_{1:t},\tau=t)
 =P_B^{\rm verified}(\tau=t)\,Q(y_{1:t}).
\]

Almost-sure termination follows from (20) with \(\rho=1/2\). Hence the ideal verified rule's independently length-matched TV is exactly zero as well. The argument holds for each fixed original message and for an independently drawn message mixture. It also extends to sources with a fixed number \(d\ge2\) of equiprobable children at every history, replacing widths by \(2^B d^{-j}\).

These are dependent-source negative controls for all three ideal mechanisms. The verified conclusion uses deterministic widths and the cancellation in (25); zero varentropy alone does not establish it. This argument makes no finite-grid or roundoff claim.

## 8. Checks and remaining claim boundaries

I checked the safe-interval invariant with exact fractions on 600 generated tapes, using the asymmetric matrix (4), \(B\in\{1,2,5,12\}\), and 25 continued steps per tape. All 60,000 tested interior inverse points equaled \(m+\Delta\); all 4,588 sufficient midpoint stops recovered \(m\). A separate endpoint test showed why the safe interval's right endpoint must be excluded. I also checked the piecewise two-step inequality on 700,000 numerical \((\rho,z)\) pairs. These computations support the algebra but do not replace the proofs above.

For the verified zero-varentropy control, I independently checked (25) with exact fractions for every message at \(B=1,2\), every four-step normalized-point tape from \(\{0,1/4,1/2,3/4\}^4\), and all \(2^4\) branch paths. All 98,304 prefix-level reverse-error identities passed. Across 24,576 complete path cases, holding the normalized-point tape and message fixed made both the midpoint and reverse-verification decisions identical across branch paths, including exact boundary cases. This checks the algebraic identity, not a finite-grid distributional equivalence.

The strongest rigorous manuscript change would center the general terminal-information criterion and instantiate it with arithmetic-prefix termination and both ideal midpoint rules, followed by the explicit dependent Markov example and the zero-varentropy exception. The criterion and classical Markov limit theorem should not be advertised as newly discovered probability results. Any novelty claim should focus on the stopped-transcript security consequence, the verified-rule concentration argument, and their application to the specified schemes; that still needs a normal literature check.

The mathematical conclusions do not automatically cover finite grids under verification, finite precision, noncryptographic random generators, recovery from rendered text, selection after source failures, retries, or arbitrary language-model sources. In particular, the earlier finite-grid bridge excluded verification-dependent stopping, and (23) does not silently remove that exclusion. No acceptance grade is inferred from these extensions before their integration, independent checking, and accurate scoping.
