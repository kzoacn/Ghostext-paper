# Independent assessment of the public endpoint identity

Date: 2026-10-21. This note checks the proposed exact identity, its finite-law approximation, and its relevance to a post-hoc replay of the saved delivery cohort. It does not change the manuscript or make a new acceptance recommendation.

## Exact identity

Let \(Q\) be a probability law on uninterrupted token trajectories, with public context fixed. Let \(\tau\) be an almost surely finite stopping time that is a deterministic function of the public token history. Put

\[
 A_n=\{y_{1:n}:\tau(y_{1:n})=n\},\qquad
 \ell(n)=Q_n(A_n).
\]

The stopped law and independently length-matched reference are

\[
 S(y,n)=Q_n(y){\bf1}_{A_n}(y),\qquad
 C(y,n)=\ell(n)Q_n(y).
\]

Define \(E=\{(y,n):y\in A_n\}\). On \(E\), \(S\ge C\); on its complement, \(S=0\le C\). Consequently

\[
 \boxed{\operatorname{TV}(S,C)
 =S(E)-C(E)=1-\sum_n\ell(n)^2.}
\]

Thus the endpoint-consistency test attains the complete TV distance: its TPR is one and its FPR is the collision probability of the stopping-length law. This is an exact statement, not just a lower bound.

More generally, for any independent natural length law \(\gamma\),

\[
 \boxed{\operatorname{TV}(S,\gamma(n)Q_n)
 =1-\sum_n\gamma(n)\ell(n).}
\]

In particular, the closest member of this family has distance \(1-\sup_n\ell(n)\), attained by a fixed modal length. Exact marginal length matching is an especially transparent comparator, but it is not generally the closest independently sampled length law.

The stopping-time assumption ensures that \(A_n\) can be determined from the reported prefix. A deterministic rule that uses future unseen tokens need not have this property. A privately randomized stopping rule, including the midpoint rules studied elsewhere, is also outside this identity unless the relevant private randomness becomes part of the observer's stated information.

For arithmetic-prefix termination, the interval containment predicate is public given the source and payload length. The payload value is not needed: one checks whether the interval lies within *some* payload cell. With a continuous uniform target, the uninterrupted trajectory has law \(Q\), so the identity applies directly.

For text rather than token transcripts, the endpoint test must be computable from the visible text and public inputs. Canonical tokenizer replay, or another justified injective representation, is needed. A hidden tokenization that cannot be reconstructed by the observer does not by itself yield the same text-level identity.

## Prior-work status

The probability identity should be treated as an elementary corollary of a standard total-variation overlap calculation. A directly relevant primary reference is [Paolo Perrone, *Markov Categories and Entropy*, IEEE Transactions on Information Theory 70(3):1671–1692, 2024](https://arxiv.org/pdf/2212.11719), DOI `10.1109/TIT.2023.3328825`. Sections 4.2.3 and 4.3.2, especially Theorem 4.10 and Corollary 4.12, give

\[
 \operatorname{TV}(\mathcal L(X,X),\mathcal L(X)\otimes\mathcal L(X))
 =1-\sum_x p(x)^2
\]

and show that the diagonal attains TV. The quantity is the Gini–Simpson index, also called linear entropy. This reference supports the standard underlying calculation, not a claim that Perrone states the steganographic stopping corollary.

To connect them, lift the experiment to full paths and a reported length. The stopped experiment reports \(\tau(\omega)\), while the reference reports an independent length. Their consistency graph is the maximizing event. Because \(\tau\) is a stopping time, projecting the full path to the reported prefix preserves membership in this event. The short direct proof above is clearer than importing categorical machinery.

I did not identify the exact steganographic formulation in the targeted search. That does not establish priority. The paper can cite the standard identity, prove the public-stopping corollary in a few lines, and focus its contribution on the protocol consequence and validated replay.

## Approximation and arbitrary packet laws

Suppose \(P\) and \(S\) are normalized laws on the same complete transcript space and \(\operatorname{TV}(P,S)\le\varepsilon\). Let \(\ell_P\) be \(P\)'s length marginal, and let \(C_P(y,n)=\ell_P(n)Q_n(y)\). Then

\[
 \operatorname{TV}(C_P,C)
 =\operatorname{TV}(\ell_P,\ell)\le\varepsilon,
\]

because different lengths have disjoint transcript supports. The triangle inequality gives

\[
 \boxed{\operatorname{TV}(P,C_P)
 \ge1-\sum_n\ell(n)^2-2\varepsilon.}
\]

The same public endpoint event satisfies \(P(E)\ge1-\varepsilon\) and

\[
 C_P(E)=\sum_n\ell_P(n)\ell(n).
\]

This is also a direct proof of the bound. In fact it gives the sometimes sharper numerical lower bound

\[
 \operatorname{TV}(P,C_P)
 \ge1-\varepsilon-\sum_n\ell_P(n)\ell(n).
\]

For the guarded codec, the reference \(S\) in such a corollary must be the \(Q\) sampler using the same **integer-state** public stopping predicate, horizon, and invalid-state handling as the coding theorem. That theorem does not automatically provide closeness to the separate continuous arithmetic-prefix law. There is no need to conflate them: the exact public-stop identity can be applied to either predicate separately when its hypotheses hold.

There is a useful packet-independent support statement. If an arbitrary delivered law \(P\) always emits exactly at the public first-resolution endpoint, then \(P(E)=1\), whether or not packet bits are uniform and whether or not delivery involved retries. Against its independently length-matched control,

\[
 \boxed{\operatorname{TV}(P,C_P)
 \ge1-\sum_n\ell_P(n)\ell(n).}
\]

This is a lower bound, not an exact formula for arbitrary \(P\). It needs no claim that authenticated packet bytes are uniform. Its empirical form is simply the endpoint test's measured TPR minus FPR under the explicitly chosen populations.

## Caps, failures, conditioning, and public context

A public cap is handled by defining \(\tau_T=\min(\tau,T)\) and treating the cap as a valid endpoint of this capped experiment. Use the capped marginal \(\ell_T\). If the test instead accepts only genuine completed prefixes and rejects cap outcomes, its TPR is the completion probability, not one.

Deterministic failure can also be included, but the source and observation law must remain normalized. A source that cannot emit further tokens cannot silently be treated as an uninterrupted \(Q_n\) for arbitrary \(n\). One must specify an absorbing failure construction or the corresponding finite sampling kernels.

If the observer sees a terminal type \(J\) and the comparator independently draws the joint descriptor \((N,J)\), the analogous calculation gives \(1-\sum_{n,j}\ell(n,j)^2\), provided \(\{N=n,J=j\}\) is publicly decidable from the relevant prefix. This is a different comparator. Independently assigning a failure label can create inconsistent text/label combinations that are absent from a natural text-only experiment.

For example, let every output have length one, with its public label determined by a token that has probabilities \(3/4,1/4\). The text law equals its length-matched control and has TV zero. Independently resampling the label changes the joint comparison and produces TV \(3/8\). That extra separation must not be attributed to the visible text alone.

Removing failures or conditioning on successful delivery changes the laws. An unconditional \(\varepsilon\) bound and its exact identity do not survive such conditioning unchanged. A support-only endpoint statement for the selected delivered population remains valid, but its control and denominator must be stated separately.

All identities are conditional on the public context: prompt, model, source processing, segment sizes, and other public protocol parameters. If the observer knows context \(H\), and lengths are matched conditionally on it, then

\[
 \operatorname{TV}(S,C)
 =E_H\!\left[1-\sum_n\ell_H(n)^2\right].
\]

It is generally incorrect to replace this with \(1-\sum_n(E_H\ell_H(n))^2\). Pooling heterogeneous prompt lengths in that way can overstate the separation. Paired natural controls generated at the same prompt and sampled stego length directly estimate the relevant FPR; estimating a separate collision law from two repeats per prompt is unnecessary.

## Assessment of the proposed delivery-cohort replay

The proposed replay is a reasonable explicitly post-hoc diagnostic of the remaining endpoint signal. The saved runner sets `natural_tail_max_tokens=0`, uses 16-byte plaintexts, and encodes two segments. Given the fixed framing, their sizes are 60 bytes and 44 bytes. Treating the second length as public is an additional chosen-length assumption; an unaided observer should not be credited with decrypting the internal header.

The classifier should take only the visible text, prompt, and declared public source/protocol parameters. Retokenize the text and replay the public candidate tables and integer interval updates. Stop the first segment at its first resolution, initialize the second immediately, and record its first resolution index. Accept the endpoint event exactly when this final index equals the visible token count. Neither the password nor decrypted bytes are needed.

Saved token IDs can verify that replay was faithful, but should not be the detector's input. Record separately: endpoint exactly at text end, endpoint before text end, unfinished at text end, and replay/source invalidity. Preserve the existing cohort and eligibility decisions, including the previously documented interrupted record; do not select a new subset based on the endpoint outcomes.

The distinction between “resolved by the end” and “first resolved exactly at the end” is substantive. Under the ideal own-length-matched law, the weaker event has FPR

\[
 \sum_n\ell(n)Q(\tau\le n)
 =\frac{1+\sum_n\ell(n)^2}{2},
\]

whereas the exact endpoint event has FPR \(\sum_n\ell(n)^2\).

The encoder also has public rolling-entropy, stall, and segment-budget aborts. Mirror those if the test is described as complete protocol legality. If the replay checks only the two-segment prefix-resolution rule, use that narrower description. Every successful no-tail output still satisfies the narrower endpoint property; it does not require proving that arbitrary replayed bytes form an authentic packet.

Complete/canonical natural controls are a conditional comparison when source failures or tokenization failures exclude other controls. Report those denominators next to any endpoint accuracy. TPR one is a structural consequence for correctly replayed successful no-tail outputs; it is not evidence of an independently validated general-purpose detector. A post-hoc result on this small cohort cannot establish a deployment-wide low-FPR claim, unknown-prompt performance, or detection with an unspecified natural tail.

## Lightweight exact checks

I enumerated a binary \(Q\) with probabilities \(3/4,1/4\), stopping at the first second symbol or at cap three. The exact length law was \((1/4,3/16,9/16)\); enumeration gave TV \(75/128\) and endpoint FPR \(53/128\), exactly matching the identity.

Moving mass \(1/32\) between two legal endpoints changed the coded law by TV \(1/32\). Its own-length comparator had TV \(299/512\), equal to the support-event lower bound, and above the \(2\varepsilon\) guarantee \(67/128\). The separate label example above gave text TV zero and independently labeled joint TV \(3/8\). No model jobs or delivery-cohort replays were run for this assessment.
