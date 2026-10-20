# Review of the full-support finite-order varentropy corollary

Review date: 2026-10-21. The proposed corollary is correct. The counting and maximal-row-entropy proof is valid; the proof below gives a shorter finish using the de Bruijn context graph. This is a standard consequence of the zero-variance coboundary criterion, not a new probabilistic contribution. No model inference, manuscript edits, or changes to prior reviews were made.

## Precise statement

Fix an alphabet \(\mathcal A\) of size \(V\ge2\), a finite order \(k\ge0\), and a time-homogeneous kernel satisfying

\[
 q(a\mid h)>0\quad\text{for every }h\in\mathcal A^k,
 \ a\in\mathcal A.
\]

For a fixed initial full context, let \(I_n\) be the information of the next \(n\) symbols under this kernel. The limit \(\sigma^2=\lim_n n^{-1}\operatorname{Var}(I_n)\) exists, is independent of the initial context, and is zero if and only if \(q(a\mid h)=1/V\) for every \((h,a)\). Equivalently, the future symbols are uniform IID. The usual stationary-source varentropy has the same rate.

Full support here concerns the \(V\) symbol choices from each context. For \(k>1\), the context transition matrix still has the structural zeros imposed by shifting the window; it is not a strictly positive matrix on every pair of contexts.

## Concise proof suitable for an appendix

For \(k=0\), the symbols are IID and \(\sigma^2=\operatorname{Var}[-\log_2 q(Y)]\). This vanishes exactly when the positive probabilities \(q(a)\) are all equal. Alternatively, lift this case to one-symbol contexts. One must not collapse all its symbol-labelled transitions into the single transition of a one-state chain.

Let \(k\ge1\), and write \(Z_t\) for the length-\(k\) context after \(t\) generated symbols. Full support makes its finite context chain irreducible: any desired context is reached by appending its \(k\) symbols. Constant-symbol contexts have self-loops, so the chain is also aperiodic. Let \(P\) and \(\pi\) denote its transition matrix and positive stationary distribution. On allowed edges put \(g(i,j)=-\log_2 P_{ij}\), and let

\[
 H=\sum_{i,j}\pi_iP_{ij}g(i,j),\qquad
 f(i)=\sum_jP_{ij}g(i,j)-H.
\]

Solve the finite-chain Poisson equation \((I-P)u=f\), which is possible because \(\pi f=0\). Then

\[
 D_t=g(Z_{t-1},Z_t)-H+u(Z_t)-u(Z_{t-1})
\]

is a bounded martingale difference, and

\[
 I_n-nH=\sum_{t=1}^nD_t+u(Z_0)-u(Z_n),\qquad
 \sigma^2=\sum_{i,j}\pi_iP_{ij}
 [g(i,j)-H+u(j)-u(i)]^2.
 \tag{1}
\]

For a stationary start, orthogonality gives the martingale's variance exactly as \(n\mathbb E_\pi D_1^2\). For any fixed start, averaging its conditional variances gives the same limit by ergodicity. The bounded endpoint term has no effect after division by \(n\): its variance is bounded and its covariance with the martingale is \(O(\sqrt n)\). This also establishes the claimed variance limit.

If \(\sigma^2=0\), every allowed-edge summand in (1) vanishes. Thus, for each continuation from initial context \(h\),

\[
 I_n=nH+u(h)-u(Z_n).
\]

At \(n=k\), each word \(a_1\cdots a_k\) is its own final context and occurs with positive probability. Normalization therefore gives, for every \(h\),

\[
 1=2^{-kH-u(h)}\sum_{j\in\mathcal A^k}2^{u(j)}.
\]

The rightmost sum is independent of \(h\), so \(u\) is constant. Hence every allowed transition has probability \(2^{-H}\); the \(V\) probabilities in each row sum to one, giving \(H=\log_2 V\) and \(q(a\mid h)=1/V\). Conversely, this kernel has \(I_n=n\log_2 V\) and zero varentropy. \(\square\)

The proposed alternative finish is also correct: the bounded endpoint term makes all \(V^n\) continuation probabilities lie within a fixed multiplicative factor of \(2^{-nH}\). Their sum forces \(H=\log_2V\), and equality in the stationary average of row entropies then makes every row uniform because every context has positive stationary probability.

## Standard references and scope

An accessible primary reference is I. Kontoyiannis, “Asymptotic Recurrence and Waiting Times for Stationary Processes,” *Journal of Theoretical Probability* 11(3), 795–811 (1998), DOI [10.1023/A:1022610816550](https://doi.org/10.1023/A:1022610816550). Section 6 of the [author's full text](https://www.dpmms.cam.ac.uk/~ik355/PAPERS/jtp.pdf) proves the stronger edge-potential characterization: zero information variance rate is equivalent to all positive transitions having the form \(2^{-H}v_i/v_j\) for positive state potentials. The finite-order statement above follows by lifting symbols to contexts and using full support.

The already cited [Kontoyiannis–Verdú paper](https://www.dpmms.cam.ac.uk/~ik355/PAPERS/SVYK-J.pdf), *IEEE Transactions on Information Theory* 60(2), 777–795 (2014), Section IV-C, remark 4 after Definition 1, states the equivalent deterministic-equipartition characterization and cites Kontoyiannis (1998) and Yushkevich (1953). Its Section VI and Theorem 21 cover finite-order Markov sources. These references support presenting the observation as a standard corollary rather than claiming novelty for it.

For each fixed nonuniform kernel in this class, finiteness and full support also imply a strictly positive minimum transition probability and a maximum below one. Thus the existing bounded-increment and positive-varentropy assumptions hold. The kernel and context order must remain fixed in the asymptotic statement; this supplies neither a uniform lower bound on varentropy across kernels nor a useful numerical mixing or finite-payload certificate.

An ideal autoregressive source fits only if its exact next-symbol law is a fixed function of a fixed finite token window and is positive on every symbol at every context. A finite window limit alone does not establish this: absolute position, retained hidden state, window-reset behavior, filtering, masks, and rounded CDFs can violate the premises. This corollary does not establish them for an implementation, extend the continuous stopping theorem to finite arithmetic, or transfer a token-law result to rendered text. The dependent three-state zero-varentropy control has a forbidden next symbol in each row, so it lies outside the full-support hypothesis and creates no contradiction.
