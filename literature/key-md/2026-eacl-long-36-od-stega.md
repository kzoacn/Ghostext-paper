# **OD-Stega: LLM-Based Relatively Secure Steganography via Optimized Distributions**

**Yu-Shin Huang[1], Peter Just[1], Hanyun Yin[2], Krishna Narayanan[1], Ruihong Huang[2]**, **Chao Tian[1]**

1Department of Electrical and Computer Engineering, Texas A&M University, 2Department of Computer Scicence and Engineering, Texas A&M University {yushinh, peter601, hanyun_yin, krn, huangrh, chao.tian}@tamu.edu

## **Abstract**

We consider coverless steganography where a Large Language Model (LLM) is used to generate stego-texts in combination with arithmetic coding. An efficient method should embed secret bits in as few language tokens as possible while keeping the stego-text as natural as possible. We show that this problem is equivalent to maximizing the entropy of a replacement probability distribution of the next token generation, subject to a constraint on the divergence between the new distribution and the original one produced by the LLM. A closed-form solution is provided under either the KL divergence or the total variation constraint. Several important practical issues are also tackled: 1) An often-overlooked tokenization mismatch issue is resolved with a simple prompt selection approach, 2) The combination of the optimized distribution and the vocabulary truncation technique is considered, and 3) The incorporation of the proposed approach with existing (potentially non arithmetic coding based) techniques, e.g., the Discop technique.

## **1 Introduction**

In a steganography system, Alice, the sender, aims to convey a secret message to Bob, the receiver. The carrier signal can take the form of text, image, audio, or video (Anderson and Petitcolas, 1998; Cox et al., 2007; Provos and Honeyman, 2003). In this work, we focus on natural language text messages as the carrier signals, and the resultant signal with the secret message embedded is therefore referred to as the stego-text. Alice transmits the stego-text to Bob via a channel monitored by an eavesdropper Eve. Eve wishes to determine whether there is a hidden message. Alice must ensure that the stego-text can be decoded correctly by Bob, and at the same time, guarantee with a high probability that Eve cannot detect the message.

Conventionally, steganography relies on an existing cover signal (cover text), and achieves steganog-

raphy by making subtle changes imperceptible to Eve on the cover text (Topkara et al., 2006; Chang and Clark, 2010). As LLMs have grown more powerful, coverless steganography has achieved significant gains in both capacity and stealth. By generating fluent, human-like text, LLM-based schemes can produce stego-text that is difficult to distinguish from natural language while embedding more secret information in shorter outputs than traditional cover-text-based methods (Fang et al., 2017; Yang et al., 2018; Ziegler et al., 2019; Xiang et al., 2017; Dai and Cai, 2019; Zhang et al., 2021; Shen et al., 2020; Kaptchuk et al., 2021; Ding et al., 2023; de Witt et al., 2024).

Though not always the case (e.g., (Ding et al., 2023)), the underlying driver for LLM-based steganography is usually the arithmetic coding (AC) algorithm (Witten et al., 1987), which is an efficient data compression algorithm based on the idea that any finite-length finite-alphabet data sequence (e.g., text) can be mapped to a small interval in the range of [0 _,_ 1). In LLM-based steganography, Alice utilizes the AC **decoder**, together with the probability distribution produced by the LLM, to map the secret binary sequence to a stego-text. Bob can then recover the secret message by performing the AC encoding. Intuitively, the AC decoder performs sampling with the probability distribution given by the LLM, using the secret message bits as the driving randomness, where we assume the secret message has been pre-encrypted with a secret key shared between Alice and Bob but not Eve (see (Shen et al., 2020; Kaptchuk et al., 2021)), and the encrypted message is an i.i.d. binary sequence.

In many scenarios, steganography security can be relaxed when Eve is computation-bounded (e.g., mobile devices), delay-constrained (e.g., streaming or time-sensitive tasks), or limited by societal constraints (e.g., censorship under constitutional protection). In such cases, Eve can be modeled as a weak detector, and correspondingly, the steganogra-

phy security requirement can be relaxed. This consideration was in fact already implicit in several previous works invoking “near-imperceptibility" (Dai and Cai, 2019; Shen et al., 2020). Generalizing this idea, we can replace the conditional probability distribution while ensuring deterministic, causal synchronization between Alice and Bob under relaxed security constraints. We refer to this approach as _relatively-secure steganography_. Since practical stego-texts always have _finite lengths_, even perfectly secure approaches, e.g., (Zhang et al., 2024; Ding et al., 2023; de Witt et al., 2024), will induce a non-zero probability of steganography being detected, and the relatively-secure steganography only needs to keep this probability under control.

The generalized view suggests a fundamental tradeoff between the amount of secret bits one can hide in the stego-text and the detectability of steganography; the former consideration is usually measured by the embedding capability or embedding utilization in the literature (Dai and Cai, 2019; Shen et al., 2020; Kaptchuk et al., 2021; Ding et al., 2023). Improving the utilization is particularly important for LLM-based steganography, since the generative process in LLMs can become almost deterministic and therefore difficult to hide secrets. We formalize the entropy maximization problem under two different probability divergence measures, and provide closed-form solutions. We refer to this approach of choosing an optimized distribution as OD-Stega. OD-Stega provides an additional _design freedom_ beyond the conventional perfectly secure steganography. By choosing the KL divergence (or total variation distance) constraint as a hyperparameter in the specific engineering application, it can either fully recover the underlying perfectly secure algorithm or take advantage of Eve’s weakness when such knowledge is available.

In addition to the principled formulation outlined above, our work also tackles several practical issues. First, most previous LLM-based steganography relied inherently on a bijective tokenization assumption, which does not hold in practice. We provide a simple solution via LLM prompting selection. Secondly, we combine OD-Stega with the existing technique of vocabulary truncation to reduce the computation complexity, and analyze the overall KL divergence of this strategy. Lastly, the proposed approach is universal and can be integrated into existing methods, and we specifically provide results on incorporating the proposed approach with Discop (Ding et al., 2023).

## **2 Preliminary**

## **2.1 LLM-based Steganography**

An LLM can provide an estimate for the conditional probability distribution for the next token, given the sequence of tokens preceding it (Vaswani, 2017; Brown, 2020; Touvron et al., 2023). To generate a natural language sequence, one can sample the tokens from these distributions in an autoregressive manner.

The secret message bit sequence _S_ in steganography is pre-encrypted with a secret key shared with Bob but hidden from Eve. Before encoding, Alice selects an initial prompt text _Tp_, independent of _S_, which determines the nature or semantics of the resulting stego-text. To encode _S_, Alice uses an encoding function _f_ (_Tp, S_) to produce a sequence of tokens _x_ ~~_i_~~ _>_ 0[= (] _[x]_[1] _[, x]_[2] _[, x]_[3] _[,...]_[)][, which] is then converted to the corresponding stego-text _Ts_ via detokenizing. The prompt and the stego-text (_Tp, Ts_) are sent on the public channel. Bob first converts _Ts_ into the token form _x_ ~~_i_~~ _>_ 0[, then uses a] decoding function _g_ (_·_) such that _g_ (_Tp, x_ ~~_i_~~ _>_ 0[) =] _[ S]_[.]

In LLM-based steganography, both _f_ and _g_ rely on the same LLM. At time _i_, an LLM takes the tokenized input _x_ ~~_i_~~ _−_ 1 = (_x−np−_ 1 _, x−np−_ 2 _, · · ·, xi−_ 1) as the prompt, where _x_ ~~0~~[= (] _[x][−][n] p[−]_[1] _[, x][−][n] p[−]_[2] _[,][ · · ·][, x]_[0][)][ represents the to-] kenized sequence of _Tp_ and _np_ is the number of tokens in _Tp_. This produces the probability distribution _PLLM_ for the next token _xi_. We shall write it as _P[i]_ = _PLLM_ (**Y** = _xi | x_ ~~_i_~~ _−_ 1[)][,][which][is][the] conditional probability for the next token, given the proceeding tokens (in the context window).

## **2.2 Arithmetic Coding**

Several authors have shown that Arithmetic Coding (AC), can be used together with language models to perform steganography (Ziegler et al., 2019; Shen et al., 2020; Ivasenko et al., 2021). Typically, AC compresses the character in the sequence sequentially into a sequence of bits, and the decompressor can convert the sequence back to text. For steganography, an AC decoder can be viewed as a sampler in the set of natural language paragraphs using the secret message as a random seed, and since the secret message is uniformly distributed on the message set, the sampled text would look like natural language. There may be a small mismatch in the sampling probability as noted in (Ding et al., 2023), however for a reasonably long sequence, this discrepancy becomes negligible. An illustrative exam-![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0003-00.png)

Figure 1: Example of AC in steganography: The sequence 10111 can be represented as the interval **I** = [0 _._ 101110000 _· · ·_ 2 _,_ 0 _._ 1011111111 _· · ·_ 2) _≃_ [0 _._ 71875 _,_ 0 _._ 75). We identify the range where this interval falls in the probability distribution _P[i]_.

## ple is given in Figure 1.

During decoding, Bob recognizes the starting token of the stego-text from the received text, and then derives the identical distribution from the same LLM with the starting prompt text. With those stego-text he receives, Bob retrieves the probabilities _P[i>]_[0] and reconstructs the bit sequence, until every bit is recovered.

## **3 Proposed Methodology**

A well-known fact in data compression is that the expected minimum number of bits to represent a symbol following a probability _P_ is the entropy _H_ (_P_) (Cover and Thomas, 1991), and AC is an algorithm that can compress at a rate close to this rate. The same relation holds for LLM-based steganography using AC, in the sense that the expected number of secret message bits that can be embedded for a given token position- _i_ is the entropy of the conditional distribution _H_ (_P[i]_). For example, if a token has a conditional distribution of _{_[1] 4 _[,]_[1] 4 _[,]_[1] 4 _[,]_[1] 4 _[}]_ on four possible token values, then 2 bits of secret message can be embedded in the stego-text.

If Eve is a weak detector, then we can take advantage of the opportunity to make the conditional distribution _P_ more amicable for embedding secret message bits, i.e., choose a different distribution _Q_ with a higher _H_ (_Q_). If _Q_ is close to _P_, we expect the generated stego-text to be nearly imperceptible to Eve. We model the detector strength of Eve via a divergence constraint _δ_. By tuning _δ_, we can recover a perfectly secure scheme or explicitly exploit Eve’s limitations, leading to the formulation below.

## **3.1 Optimized Distribution under Constraint**

We formulate the following optimization problem.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0003-09.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0003-10.png)

where _N_ = _|V|_ is the total number of symbols in the vocabulary. The objective function _H_ (_Q[i]_) is the standard Shannon entropy. The divergence, denoted as _D_ (_Q[i] ||P[i]_), could be KL divergence or TV (see discussion in (Dai and Cai, 2019; Shen et al., 2020)), and A _i_ is the index set of elements with zero probability in _P[i]_ (i.e., _Pj[i]_[= 0][).][Without] loss of generality, we assume that the elements in the vocabulary are in descending order of the probabilities _P[i]_, and the number of nonzero elements in _P[i]_ is written as _Ni_ (i.e., _Ni_ = _N −|_ A _i|_).

In the optimization problem above, we seek to replace the natural language distribution probability distribution _Pi_ given by the LLMs with a new distribution _Qi_ towards a larger entropy value (a more uniform distribution). This would allow for embedding a greater number of secret bits. The new distribution needs to be close to that of the natural language, which is ensured by the constraint in (2). This optimization problem is convex as long as the divergence function in (2) is convex.

## **3.2 Optimal Probability Adjustment**

The main theoretical contribution of the work is shown in Theorem 1 and Theorem 2.

**Theorem 1** _When the divergence in (2) is the KL divergence, the optimal solution Q[i] to the problem (1)-(5) is obtained by performing temperature scaling on P[i] when δ ∈_ [0 _, N_[1] _i_ � _Nj_ =1 _i_[log(] _Ni_ 1 _Pj[i]_[)]]![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0003-16.png)

_for some T ≥_ 1 _s.t. DKL_ (_Q[i] ||P[i]_) = _δ. Otherwise,_![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0003-18.png)

**Remark 1** _If the LLM generated distribution P[i] is defined via a softmax over logits Z[i], then applying temperature scaling T to P[i] is equivalent to scaling the logits Z[i] by T_[1] _[(see Appendix][ B][ for a proof).]_

In Theorem 1 and Remark 1, we showed that the optimal adjustment _Q[i]_ can be expressed by Equation (6), which is mathematically equivalent to adjusting the temperature parameter in the LLM

architecture. This finding offers an interesting theoretical justification for the practice of temperature tuning in language generation (without the steganography consideration), i.e., increasing the temperature maximizes the next token entropy under the KL divergence constraint.

**Lemma 1** _For Q[i] chosen as in (6) and any δ ∈_ [0 _, N_[1] _i_ � _Nj_ =1 _i_[log(] _Ni_ 1 _Pj[i]_[)]] _[, there exists a][ T][≥]_[1] _[, such] that the solution given in Theorem 1 satisfies the constraint (2) with equality_![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0004-02.png)

_Moreover, DKL_ (_Q[i] ||P[i]_) _is a monotonically increasing function of T ≥_ 1 _._

The proofs of Theorem 1, Remark 1, and Lemma 1 are given in Appendix B, C and D, built on a careful analysis of the KKT conditions. The specified _δ_ only places a meaningful constraint within the range given in Theorem 1. Otherwise, the KL constraint is too loose, and the optimal solution _Q[i]_ defaults to a uniform distribution. It remains to solve for the temperature value _T_ that satisfies the KL constraint with equality. Lemma 1 states that the KL divergence grows with increasing _T_, which allows us to numerically find _T_ through a straightforward bisection search.

**Theorem 2 (informal)** _When the divergence in (2) is the total variation distance (TV), the optimal solution Q[i] to the problem (1)-(5) is obtained by splitting the budget δ into half equally, half to increase the lower-end probabilities to a certain common value, and the other half to decrease the higher-end probabilities to another certain common value._

The proof of Theorem 2 and the closed-form solution are provided in Appendix F. The proof demonstrates that the solution follows a water-filling procedure to increase the low-probability components of _P[i]_, and a reverse water-filling procedure to reduce the high-probability components, resembling the approach used in classical resource allocation problems. If the _δ_ constraint is loose, then the optimal _Q[i]_ becomes the uniform distribution, i.e., the two common values become equal. Figure 2 provides a clear visualization of the solution in Theorem 2.

## **3.3 Adaptive** _δ_ **Value Selection**

Let us denote the divergence threshold in each time _i_ as _δi_. If _δi_ is set too large, the resulting adjustment![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0004-09.png)

Figure 2: Optimal adjustment allocation under total variation constraint.

to the probability distribution may lead to the selection of unusual tokens, negatively impacting the fluency of the stego-text. This issue is particularly noticeable when dealing with positions that have probability distributions with very low entropy values, i.e., most tokens have near-zero probability and the choices of tokens are almost deterministic. To address this issue, we need to choose _δi_ adaptively to the entropy _H_ (_P[i]_), i.e. _δi_ = _h_ (_H_ (_P[i]_)). We take a straightforward approach in this work by setting _δi_ = _C · H_ (_P[i]_) where _C_ is a constant.

## **4 Practical Considerations and Variations**

## **4.1 Tokenization Errors**

LLM-based steganography relies on several assumptions, one of which is that Bob’s tokenization process matches what was intended by Alice. This assumption is in fact quite subtle. The tokenizers in pre-trained LLMs guarantee that after detokenizing, the original text can be recovered; however, they do not guarantee to reproduce a unique sequence of tokens from any detokenized text. For example, Alice encodes the stego-text as _{_ “This” _,_ “mount” _,_ “ain” _,_ “is” _,_ “high” _}_, forming “This mountain is high.” However, Bob may tokenize it as _{_ “This” _,_ “mountain” _,_ “is” _,_ “high” _}_, causing errors. In order words, the tokenizer merged “mountain" into a single token rather than the two that the stego-text encoder intended. This issue exists in most of the previous LLM-based steganography approaches (Ziegler et al., 2019; Shen et al., 2020), though only limited attention has been given to it (Yan et al., 2023, 2024).

This tokenization error leads Bob to decode a bit sequence different from the original secret bit sequence. Since LLMs are computationally demanding, it is too computationally expensive to enumerate such potential error cases to prevent such errors from occurring (see e.g. (Yan et al., 2023, 2024) for efforts in this direction). Instead, we observe that tokenization errors are uncommon and the likelihood of such errors occurring is proportional to the length of the bit file. Moreover,![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0005-00.png)

Figure 3: The OD-Stega approach

Alice can in fact verify whether the stego-text can be correctly decoded by Bob since both have a copy of the same tokenizer. We therefore propose prepending a short sequence of additional _B_ bits to the bit sequence _S_ (a form of prompting). Alice then iterates among all _B_ -bits combinations, and uses _f_ (_Tp,_ (_B, S_)) to produce the stego-text, until she verifies Bob can correctly decode. Bob simply discards the beginning _B_ bits after decoding. More experimental details to determine _B_ heuristically are given in Appendix M. The overall OD-Stega approach with this consideration is illustrated in Figure 3.

## **4.2 Vocabulary Truncation**

To reduce the computational complexity when the vocabulary set is large, a simple strategy is to truncate the vocabulary in the subsequent processing once a probability distribution has been generated. This strategy has been adopted in (Shen et al., 2020). To leverage our optimization formulation, we consider a two-stage process: first, we truncate the vocabulary, and second, we optimize the probability adjustment on the truncated vocabulary as discussed in the previous section. For this twostage approach, we establish the KL divergence (and total variation) between the original distribution and the eventual optimized distribution on the truncated vocabulary, given below in Theorem 3.

Let us make the two-stage strategy more precise. We first expand the zero-probability index set A _i_ from [ _Ni_ + 1: _N_ ] to [ _Nϵ_ + 1: _N_ ], where _Nϵ_ = min _{n |_[�] _[n] j_ =1 _[P][ i] j[≥]_[1] _[ −][ϵ][}]_[.][This leaves us with] a total of _Nϵ_ variables. In addition, we define the re-normalized probability _P_[ˆ] _j[i]_[(] _[ϵ]_[)][=] 1 _−_ 1 _ϵ[P][ i] j_[, which] we refer to as an _ϵ_ cutoff probability of _P[i]_. After the first stage, the variables in the optimization problem are reduced to [ _Q[i]_ 1 _[,][ · · ·][, Q][i] Nϵ_[]][.]

The initial truncation phase creates the probability divergence _D_ (_P_[ˆ] _[i]_ (_ϵ_) _||P[i]_), and the second proba-![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0005-07.png)

Figure 4: The two-stage design: Vocabulary truncation and distribution optimization

bility adjustment phase, as proposed in Section 3.2, results in the divergence _D_ (_Q[i] ||P_[ˆ] _[i]_ (_ϵ_)). The KL divergence does not satisfy the triangular inequality in general; however, in the specific case with a cutoff probability and its optimized counterpart, the following theorem demonstrates the additivity of KL divergences across these two stages.

**Theorem 3** _Let P_[ˆ] _[i]_ (_ϵ_) _be the ϵ cutoff probability distribution of P[i] and Q[i] be the solution of the optimization problem (1)-(5) with the constraint DKL_ (_Q[i] ||P_[ˆ] _[i]_ (_ϵ_)) _≤ δ_[ˆ] (_ϵ_) _, then it holds that_![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0005-11.png)

The proof can be found in Appendix G. Given a total KL budgetˆ _δ_, it is clear that we can determine _δ_ (_ϵ_) = _δ − DKL_ (ˆ _P[i]_ (_ϵ_) _||P[i]_).

For the case when TV is used in the divergence constraint, the triangular inequality allows us to set _δ_[ˆ] (_ϵ_) = _δ − DTV_ (_P_[ˆ] _[i]_ (_ϵ_) _||P[i]_) = _δ −_ 2 _ϵ_, which guarantees the overall _DTV_ (_Q[i] ||P[i]_) stays below _δ_. Details are given in the Appendix H.

## **4.3 Variations and OD-Discop**

So far we have focused on using an AC decoder to directly drive the steganography encoder in a successive manner. Many existing AC-based methods can be naturally generalized to their relatively secure version in a straightforward manner, e.g., (Kaptchuk et al., 2021; Shen et al., 2020; Dai and Cai, 2019; Ziegler et al., 2019; Ivasenko et al., 2021); note that in the extreme case of without distribution optimization (i.e., _δi_ = 0), these reduce to their original forms. More interestingly, our proposed approach even applies to techniques that do not directly rely on arithmetic coding. In the following, we discuss an adaptation of the Discop method (Ding et al., 2023), which relies on distribution copies for encoding.

Discop (Ding et al., 2023) duplicates the probability distributions produced by an LLM, which the sampling distribution can follow exactly via

pseudo-random numbers shared by Alice and Bob. The duplicated distributions are offset by different amounts, and the secret bits are encoded as the unique copy index in which the pseudo-number matches the sampled token. Though the exact mechanism becomes less transparent, it is straightforward to see that a highly non-uniform sampling distribution also induces low embedding utility in Discop. Therefore, adopting our proposed distribution-optimization technique can also improve embedding utility. To do so, we simply replace the LLM-produced distributions with our ODadjusted version, prior to making the distribution copies, without impacting any other components of the coding pipeline. The corresponding experiments are given in the next section.

## **5 Experimental Results**

## **5.1 Experiment Setup**

We adopt the LLAMA2-7B pre-trained model (Touvron et al., 2023) as the underlying LLM in the experiment for OD-Stega, together with the SentencePiece tokenizer. We are aware that LLAMA3 (Grattafiori et al., 2024) and LLAMA4 (Meta AI, 2025) have become available; however, to evaluate the proposed technique, the larger models do not make any significant difference. As mentioned earlier, we conducted experiments on OD-Discop, which combines Discop (Ding et al., 2023) with the proposed distribution optimization technique; in these experiments, the GPT2-XL pre-trained model with a capacity of 50,000 tokens is used. This was the LLM used in the original Discop, and we preserved it to avoid introducing unintentional confounders. The overall computational bottleneck is in the LLM and the additional computation of the proposed optimization is negligible, since closedform solutions are available.

We performed experiments using a range of starting prompts on different topics of interest. Examples of topics include the Olympics, news, technology, and blogs, among others. The prompts usually have 10 to 20 words. In our two-stage optimization framework, we select a cutoff value _ϵ_ typically in the range (0 _,_ 0 _._ 05], and also adjust the constant _C ∈_ [0 _,_ 0 _._ 1] to control the _δi_ values. Setting the cutoff _ϵ_ at its maximum of 0 _._ 05 results in the effective elimination of roughly 2000 lowest probability token choices for Llama2. By adjusting the range of _δi_, we can assess how they impact the naturalness of the generated stego-texts and utilization.

We referred to the stego-texts produced under the KL constraint as OD-KL, while those created under the TV constraint were called OD-TV.

The first evaluation metric is the embedding utilization, or equivalently the number of embedded bytes for a fixed number of generated stego-text tokens. The second quantity to evaluate is the naturalness (perceptability) of the generated stego-text, which is measured by three metrics: 1) The **KL Divergence** where a lower value implies better imperceptibility; 2) The detection rate using existing **steganalysis** techniques; 3) A perception evaluation using **GPT-4** as a human perception surrogate, where we simply ask GPT to determine whether the stego-text is written by human or not. Three different steganalysis techniques FCN (Yang et al., 2019), SESY (Yang et al., 2021), and GS-Llama (Yang et al., 2024), are chosen. These techniques require training, and relevant details are given in Appendix K.

## **5.2 Utilization-KL Tradeoff**

To study the embedding utilization performance, we keep the number of tokens in the stego-text fixed at 25, and evaluate how many secret bits can be embedded. We first verify that the constraining parameter _C_ indeed correlates linearly with the KL divergence of the sequence, and the results are shown in Appendix I. Equipped with this understanding, we focus on the study of the average number of bits that can be embedded vs. the parameter _C_ in the sequel.

For OD-Stega, the parameter _C_ is varied from 0 to 0 _._ 1, and the truncation cutoff value parameter _ϵ_ is varied from 0 _._ 005 to 0 _._ 045. For each _C_ and _ϵ_, we average the numbers of bits embedded over 200 stego-texts to obtain the average. The results of OD-KL and OD-TV are illustrated in Figure 5, where different colors indicate different truncation cutoff values, and the horizontal axis indicates the value of the parameter _C_.

Observe first that the squares indicate the performance where only truncation is used without distribution optimization. It can be seen that embedding utilization decreases as the truncation value _ϵ_ increases. Second, the points on the upper contour are produced with the lowest cutoff value _ϵ_ = 0 _._ 005, consistent with the fact that higher cutoff reduces the embedding capacity. As _C_ increases (which corresponds to increasing _δi_ ’s), the embedding utilization increases, initially more quickly and then roughly in a linear manner for OD-KL![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0007-00.png)

Figure 5: **OD-Stega.** Average bits embedded per 25 tokens (over 200 stego-texts) under KL and TV constraints, across parameter _C_ and cutoff _ϵ_.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0007-02.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0007-03.png)

Figure 6: **OD-Discop.** Average bits embedded per 25 tokens (over 200 stego-texts) under KL and TV constraints, across parameter _C_ and cutoff _ϵ_.

case. For OD-TV, the growth appears approximately linear throughout the entire range of _C_.

With _C_ = 0 _._ 01, which can be viewed as difficult to distinguish, i.e., when Eve is assumed to be a strong detector (see the next section for discussion on steganalysis techniques), the proposed method can increase embedding utilization by 20%; If Eve is a weaker detector, then _C_ can be chosen at _C_ = 0 _._ 05, and the utilization can increase by 55% in some cases.

In a similar manner, we evaluate the performance of OD-Discop, shown in Figure 6. We see a similar trend for OD-Discop, which confirms that the proposed approach indeed works as intended in Discop. The slight difference in the overall embedding utilization between Figure 5 and Figure 6 is mostly due to the completely different approaches in embedding the secret bits as well as the underlying LLMs, and should not be interpreted as one is better than the other.

## **5.3 Steganalysis: Stego-Text Detection**

Relatively secure steganography allows a weaker but controlled security degradation, and we now evaluate the behaviors of such degradation in ODStega and OD-Discop. Throughout this subsection, we fix the truncation cutoff parameter _ϵ_ = 0 _._ 025. Note that current LLMs also usually include such a parameter, set at values ranging from 0 _._ 01 to 0 _._ 05.

Before performing tests on stego-texts, we first verify that setting _C_ = 0 in our OD-Stega approach indeed produces texts that are indistinguishable from LLM-generated texts without the arithmetic coding procedure at all. To do so, we utilize GSLlama to obtain a classifier trained on a dataset with 500 texts from each class and then use it on a separate test dataset of 500 texts from each class. The classifier achieves roughly 50% accuracy, implying that these two classes are indeed indistinguishable. Additional details can be found in Appendix N.

As mentioned earlier, FCN, SESY, and GSLLaMA are used to model Eve, who can have different levels of detection capabilities. We trained these detectors using OD-stega and OD-Discop stego-texts generated under both KL and TV constraints with various parameter _C_, combined with non-stego texts produced by the base language models (LLaMA2-7B and GPT2-XL). More details on the training procedure are given in Appendix K.

For tests on OD-Stega and OD-Discop, the test dataset consists of 300 stego-texts for each _C_ value under KL and TV constraints, including the setting with _C_ = 0 and naturally generated texts without steganography coding. The results are shown in Figure 7 and Figure 8. The circle markers correspond to the OD-KL method, while the triangular markers represent the OD-TV method. The horizontal dotted lines indicate the percentage nonstego texts that are correctly detected as non-stego, while the other lines indicate the percentage of stego-texts detected incorrectly as non-stego.

In Figure 7, we see that as _C_ increases, the classifiers have a higher chance of classifying the stegotexts as so. In detecting OD-KL stego-texts, when _C <_ 0 _._ 01, all three classifiers classify more than half of the stego-texts as non-stego. In the OD-TV case, the classifiers struggle to detect stego-texts when _C <_ 0 _._ 05. Similar trends can be observed in the OD-Discop method, as shown in Figure 8. Additionally, as _C →_ 0, the percentage of stegotexts classified as stego-coded approaches that of LLM-generated texts.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0008-00.png)

Figure 7: **Steganalysis on OD-stega coded texts.** The y-axis shows the fraction (%) of stego-texts that the detector labels as _non-stego_. Each data point is computed over 300 stego-texts for each value of parameter _C_.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0008-02.png)

Figure 8: **Steganalysis on OD-Discop coded texts.** The y-axis shows the fraction (%) of stego-texts that the detector labels as _non-stego_. Each data point is computed over 300 stego-texts for each value of parameter _C_.

In Figures 7 and 8, the detectors may appear to perform similarly when considering only the stegotexts, however, FCN has a much lower percentage of correctly classifying natural texts, and similarly, SESY has an improved percentage of correctly classifying natural texts but not as high as GS-Llama. FCN is indeed considered the weakest model in the steganalysis literature that uses the least amount of computational resources. In Appendix L, Fig. 13 provides the overall detection accuracy vs. the parameter C, which illustrates this effect from another perspective. We additionally report steganalysis experiments for longer tokens (token length 100) in Appendix P. The results exhibit similar trends to those for token length 25, with a slight shift for longer text sequences.

The behavior above confirms our early observation that the strength of the detector should be taken into account to achieve higher steganography embedding utilization. Additionally, given the linear![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0008-06.png)

Figure 9: GPT-4 detection score on OD-Stega vs. average (over 200 texts) bits embedded per 25 tokens under KL and TV constraint.

relation between _C_ and KL-divergence in Fig. 10, we see that the latter is indeed a reliable measure to determine the imperceptibility threshold.

## **5.4 GPT Evaluation**

We also use GPT-4 without fine-tuning to assess whether our stego-text appears natural and can escape detection by an untrained human-like evaluator. We instructed GPT to mimic a human evaluator to assess the text and determine if it was likely written by a human. In this experiment, we examined hundreds of generated stego-texts with GPT-4 under various parameters outlined in Section 5.2. The OD-Stega result is shown in Figure 9 (that for OD-Discop in Appendix O), where the score indicates the percentage of texts rated as non-stego texts. The behavior is consistent with that in steganalysis: As the probability distribution gradually deviates further, more secret bits can be embedded at the expense of a gradually increased likelihood of attracting the evaluator’s attention.

## **5.5 Examples of Generated Stego-Texts**

We present several examples of stego-texts generated using OD-Stega-KL in Table 1, each with different values of _C_. The corresponding classification results from the SESY and FCN models are also shown. Here, NS denotes non-stego text and S denotes stego-text. As expected, larger values of _C_ are more likely to induce unnaturalness and are generally easier for the classifier to detect as stego-text. However, this is not always the case. For example, the fourth example with _C_ = 0 _._ 05 is not classified as stego-text, while the example with _C_ = 0 _._ 01 is. It can also be seen that FCN makes a mistake in the third example, while SESY is correct. Additional examples can be found in Appendix R.

Table 1: Example stego-texts (OD-Stega-KL)

|Parameters|Prompt: Over the next few days, the<br>weather will be|SESY|FCN|
|---|---|---|---|
|||||
|_C_ = 0_._01<br>_ϵ_ = 0_._025|icy cold, with a temperature that could<br>drop as low as -4 degrees on Christmas<br>Eve. The Montereyand...|NS|NS|
|_C_ = 0_._05<br>_ϵ_ = 0_._025|ATARSITY ADVENRTURE so if I<br>didnt mention any of the places that<br>I went...|S|S|
|||||
||Prompt: Due to recent advances in<br>technology,|||
|||||
|_C_ = 0_._01<br>_ϵ_ = 0_._025|3D printing has revolutionized not only<br>the operation of manufacturing sectors,<br>but also current procedures. Homolo-<br>gation of...|S|NS|
|_C_ = 0_._05<br>_ϵ_ = 0_._025|3d printers are able to melt a plastic<br>resin within the pores of a ceramic ob-<br>ject...|NS|NS|

## **6 Conclusion**

We propose a technique to improve embedding utilization by formulating and solving a constrained optimization problem, resulting in the OD-Stega technique. We further address several practical issues, including tokenization errors, and vocabulary truncation. Moreover, variations such as ODDiscop were considered. We conducted extensive tests to show that the technique is indeed effective, and utilized both steganalysis tools and GPT to study the naturalness of the generated stega-texts.

## **7 Limitations**

Relatively secure steganography can take advantage of the knowledge of the weak detector Eve’s perceptibility, however, in this work, we did not consider the perceptibility question itself. Instead, we use the KL divergence as a surrogate to control it. An analogy is in image compression, where a compression method that can produce compressed images of different qualities may not specify the just noticeable difference (JND) value (Zhang et al., 2016; Liu et al., 2019). The "imperceptible threshold" is clearly application-dependent and potentially individual-person-dependent, and therefore we treat it as a control lever in our work. Techniques to systematically design new perception neural networks to learn this threshold is beyond the scope of this work.

The OD adjustment relies on optimizing each token individually using the conditional distribution causally. This process does not consider the impact that modifying the current token may have on the embedding capability for subsequent tokens. To

take into account such long-term impact, one may need to consider a finite look-ahead approach, however, such an approach based on LLMs appears prohibitively expensive computationally (Huang et al., 2025). On the other hand, the KL divergence does decompose on the sequence level to the token level (Shen et al., 2020), therefore, the KL divergence on the sequence level can be well-controlled if it is well-controlled on the individual token level, although directly applying our individual-tokenbased optimization technique will not guarantee the optimality on the sequence level.

## **References**

- Ross J Anderson and Fabien AP Petitcolas. 1998. On the limits of steganography. _IEEE Journal on selected areas in communications_, 16(4):474–481.

- Tom B Brown. 2020. Language models are few-shot learners. _arXiv preprint arXiv:2005.14165_.

- Ching Yun Chang and Stephen Clark. 2010. Linguistic steganography using automatically generated paraphrases. In _Human Language Technologies: The 2010 Annual Conference of the North American Chapter of the Association for Computational Linguistics_, pages 591–599.

- Ching-Yun Chang and Stephen Clark. 2014. Practical linguistic steganography using contextual synonym substitution and a novel vertex coding method. _Computational linguistics_, 40(2):403–448.

- Thomas M Cover and Joy A Thomas. 1991. Elements of information theory.

- Ingemar Cox, Matthew Miller, Jeffrey Bloom, Jessica Fridrich, and Ton Kalker. 2007. _Digital watermarking and steganography_. Morgan kaufmann.

- Weihui Dai, Yue Yu, Yonghui Dai, and Bin Deng. 2010. Text steganography system using Markov chain source model and des algorithm. _J. Softw._, 5(7):785–792.

- Christian Schroeder de Witt, Samuel Sokota, J Zico Kolter, Jakob Nicolaus Foerster, and Martin Strohmeier. 2024. Perfectly secure steganography using minimum entropy coupling. In _The Eleventh International Conference on Learning Representations_.

- Jinyang Ding, Kejiang Chen, Yaofei Wang, Na Zhao, Weiming Zhang, and Nenghai Yu. 2023. Discop: Provably secure steganography in practice based on “distribution copies". In _2023 IEEE Symposium on Security and Privacy (SP)_, pages 2238–2255. IEEE.

- Tina Fang, Martin Jaggi, and Katerina Argyraki. 2017. Generating steganographic text with LSTMs. In _Proceedings of ACL 2017, Student Research Workshop_, pages 100–106.

- Aaron Grattafiori, Abhimanyu Dubey, Abhinav Jauhri, Abhinav Pandey, Abhishek Kadian, Ahmad AlDahle, Aiesha Letman, Akhil Mathur, Alan Schelten, Alex Vaughan, et al. 2024. The llama 3 herd of models. _arXiv preprint arXiv:2407.21783_.

- Yu-Shin Huang, Chao Tian, Krishna Narayanan, and Lizhong Zheng. 2025. Relatively-secure llm-based steganography via constrained markov decision processes. _arXiv preprint arXiv:2502.01827_.

- Maksym Ivasenko, Olha Suprun, and Oleh Suprun. 2021. Information transmission protection using linguistic steganography with arithmetic encoding and decoding approach. In _2021 IEEE 3rd International Conference on Advanced Trends in Information Theory (ATIT)_, pages 174–178. IEEE.

- Huanhua Liu, Yun Zhang, Huan Zhang, Chunling Fan, Sam Kwong, C-C Jay Kuo, and Xiaoping Fan. 2019. Deep learning-based picture-wise just noticeable distortion prediction model for image compression. _IEEE Transactions on Image Processing_, 29:641– 656.

- Meta AI. 2025. The llama 4 herd: The beginning of a new era of natively multimodal ai innovation. https://ai.meta.com/blog/ llama-4-multimodal-intelligence/. Accessed: 2026-01-20.

- H Hernan Moraldo. 2012. An approach for text steganography based on Markov chains. In _IV Workshop de Seguridad Informática (WSegI 2012)(XLI JAIIO, La Plata, 27 al 31 de agosto de 2012)_.

- Niels Provos and Peter Honeyman. 2003. Hide and seek: An introduction to steganography. _IEEE security & privacy_, 1(3):32–44.

- Cao Qi, Sun Xingming, and Xiang Lingyun. 2013. A secure text steganography based on synonym substitution. In _IEEE Conference Anthology_, pages 1–3. IEEE.

- Jiaming Shen, Heng Ji, and Jiawei Han. 2020. Nearimperceptible neural linguistic steganography via self-adjusting arithmetic coding. In _Proceedings of_

   - _the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)_, pages 303–313.

- Umut Topkara, Mercan Topkara, and Mikhail J Atallah. 2006. The hiding virtues of ambiguity: quantifiably resilient watermarking of natural language text through synonym substitutions. In _Proceedings of the 8th workshop on Multimedia and security_, pages 164–174.

- Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, et al. 2023. Llama: Open and efficient foundation language models. _arXiv preprint arXiv:2302.13971_.

- A Vaswani. 2017. Attention is all you need. _Advances in Neural Information Processing Systems_.

- Ian H Witten, Radford M Neal, and John G Cleary. 1987. Arithmetic coding for data compression. _Communications of the ACM_, 30(6):520–540.

- Lingyun Xiang, Xinhui Wang, Chunfang Yang, and Peng Liu. 2017. A novel linguistic steganography based on synonym run-length encoding. _IEICE transactions on Information and Systems_, 100(2):313– 322.

- Ruiyi Yan, Tian Song, and Yating Yang. 2024. A nearimperceptible disambiguating approach via verification for generative linguistic steganography. In _2024 IEEE International Conference on Systems, Man, and Cybernetics (SMC)_, pages 1638–1643. IEEE.

- Ruiyi Yan, Yating Yang, and Tian Song. 2023. A secure and disambiguating approach for generative linguistic steganography. _IEEE Signal Processing Letters_, 30:1047–1051.

- Jinshuai Yang, Zhongliang Yang, Siyu Zhang, Haoqin Tu, and Yongfeng Huang. 2021. Sesy: Linguistic steganalysis framework integrating semantic and syntactic features. _IEEE Signal Processing Letters_, 29:31– 35.

- Minhao Bai Yang, Kaiyi Pang, Huili Wang, Yongfeng Huang, et al. 2024. Towards next-generation steganalysis: Llms unleash the power of detecting steganography. _arXiv preprint arXiv:2405.09090_.

- Zhong-Liang Yang, Xiao-Qing Guo, Zi-Ming Chen, Yong-Feng Huang, and Yu-Jin Zhang. 2018. RNNstega: Linguistic steganography based on recurrent neural networks. _IEEE Transactions on Information Forensics and Security_, 14(5):1280–1295.

- Zhongliang Yang, Yongfeng Huang, and Yu-Jin Zhang. 2019. A fast and efficient text steganalysis method. _IEEE Signal Processing Letters_, 26(4):627–631.

- Siyu Zhang, Zhongliang Yang, Jinshuai Yang, and Yongfeng Huang. 2021. Provably secure generative linguistic steganography. In _Findings of the Association for Computational Linguistics: ACL-IJCNLP 2021_, pages 3046–3055.

- Xin Zhang, Kejiang Chen, Jinyang Ding, Yuqi Yang, Weiming Zhang, and Nenghai Yu. 2024. Provably secure public-key steganography based on elliptic curve cryptography. _IEEE Transactions on Information Forensics and Security_.

- Xinfeng Zhang, Shiqi Wang, Ke Gu, Weisi Lin, Siwei Ma, and Wen Gao. 2016. Just-noticeable differencebased perceptual optimization for jpeg compression. _IEEE Signal Processing Letters_, 24(1):96–100.

## **Appendices**

## **A Related Works**

Linguistic Steganography (LS) can be divided into two main areas: modification-based (coverbased) and generation-based (coverless). The modification-based approach conceals secret messages by altering the cover text through synonyms, syntactic changes, and word substitutions (Topkara et al., 2006; Chang and Clark, 2010; Qi et al., 2013; Chang and Clark, 2014). In contrast, the generation-based approach creates stego-texts using methods like Markov chains (Dai et al., 2009, 2010; Moraldo, 2012) and deep learning techniques. With the advancement of generative language models, an increasing number of steganography research efforts now leverage neural networks to produce steganographic texts (Fang et al., 2017; Yang et al., 2018; Ziegler et al., 2019; Xiang et al., 2017; Dai and Cai, 2019; Zhang et al., 2021; Shen et al., 2020; Kaptchuk et al., 2021; Ding et al., 2023; de Witt et al., 2024)

(Fang et al., 2017), for instance, explored a block-based methodology in which they designed a text generation model that first partitions the dictionary and allocates a specific code for each word. During the output stage, modified wordlevel LSTM neural network is utilized to choose words according to the encoded secret information. Their method organizes the vocabulary into subsets, the best word is chosen from a candidate pool based on the encoded bitstream at every generation step. (Yang et al., 2018) presented a model that enhances text fluency and security in steganography by encoding each word dynamically based on its conditional probability distribution, employing both fixed-length coding (FLC) and variable-length coding (VLC). Through the use of structures like full binary trees or Huffman trees, this method enhances the naturalness and quality of generated texts while embedding hidden information more effectively.

(Ziegler et al., 2019) also utilized GPT-2 to create stego-texts, by proposing a linguistic steganography method that uses arithmetic coding with a pretrained neural language model. This method encodes secret messages by truncating the token distribution to the top _K_ most probable tokens at each generation step, thus minimizing the difference between the conditional probability distributions of steganographic and normal text, achieving close

to optimal statistical security. Human evaluations were conducted to confirm that the generated text successfully deceived readers.

Building on Ziegler et al.’s arithmetic coding and truncating probability method, (Shen et al., 2020) modified _K_ for each iteration, adjusting the conditional probability threshold with each new token. They claimed to select the smallest _K_ that still ensured near-imperceptibility. Additionally, they employed human evaluations to confirm their findings, demonstrating their method’s effectiveness in deceiving eavesdroppers.

(Dai and Cai, 2019) employed GPT-2 for generating steganographic texts, crafting a novel steganographic mapping to embed secret messages and showcasing that effective mapping increases text security. They also proposed the patient-Huffman algorithm in such setting, which dynamically adjusts the embedding rate through the application of Kullback-Leibler divergence, enhancing both the quality and imperceptibility of steganographic texts. Their approach achieved near-imperceptibility, validated using total variation distance.

Recognizing the informal nature in the treatment of the security aspect of the methods in the studies from natural language processing community (Ziegler et al., 2019; Dai and Cai, 2019; Shen et al., 2020), the security research community further refined these methods to obtain provably secure protocols (Kaptchuk et al., 2021; Zhang et al., 2021; Ding et al., 2023; de Witt et al., 2024). (Zhang et al., 2021) attempted to use grouping to match the granularity of probability to that of the secret message distribution granularity, however, their method is only perfectly secure when the natural language distribution allows such a grouping. Moreover, the grouping operation itelf also leads to a loss of embedding utilization. (Kaptchuk et al., 2021) replaced the repeated secret key in (Ziegler et al., 2019) with pseudo-random generators, and showed that the resulting protocol is provably secure. However, the arithmetic coding component in (Kaptchuk et al., 2021) is a reduced version from the full version, resulting in a slight loss in the embedding utilization. Instead of encrypting the original message and then using the generative model for steganography encoding, (Ding et al., 2023) combined the encryption step and the steganography encoding, resulting in another provably secure protocol. The work (de Witt et al., 2024) proposed a different approach to couple the message and the stego-text than using arithmetic coding directly.

In this paper, we present our encoding-decoding framework, drawing inspiration from (Ziegler et al., 2019) and (Shen et al., 2020). We observed that truncating a significant portion of the conditional probability from below leads to a reduction in bits embedded, which improves computational efficiency but reduces capacity. In fact, their approach for embedding long secret messages requires more computation in order to generate long stego-texts. To resolve this issue, we propose a novel method for adjusting the conditional probability to maximize the information embedded while maintaining near imperceptibility.

## **B Proof of Remark 1**

For each generation time _i_, if the LLM generated distribution _P[i]_ results from the softmax of logits _Z[i]_, the relation is shown as follows.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0012-07.png)

Applying temperature scaling to _P[i]_ involve raising each probability in _P[i]_ by the power _T_[1][, followed] by renormalization.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0012-09.png)

The equivalence in (9) follows from (8). Equations (9)-(11) demonstrate that temperature scaling to _P[i]_ matches the scaling to _Z[i]_ by _T_[1][at the logit level,] proving the remark.

## **C Proof of Theorem 1**

The Lagrangian function of the problem (1) - (5) with KL divergence constraint is![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0012-13.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0013-00.png)

## 2. Dual variables:![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0013-02.png)

where _u,_ _**λ**, ω_ are the Lagrangian multipliers of constraint (2), (3) and (4), respectively. Then the KKT condition can be derived as follows:

## 1. Stationarity:![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0013-05.png)

It is straightforward to verify all the KKT conditions are satisfied, except the dual feasibility condition _u ≥_ 0, which we prove in the next section.

## 2. Primal feasibility:

## **D Proof of** _u ≥_ 0 **and Lemma 1 First Part**![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0013-09.png)

## 3. Dual feasibility:![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0013-11.png), because![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0013-13.png)

4. Complementary slackness:![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0013-15.png)

Since the optimization problem is convex and clearly feasible, a solution to the KKT condition is also a global optimal solution. We claim the following is a solution to the KKT conditions:

## 1. Primal variables:![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0013-18.png)

Second, note that that _DKL_ (_Q[i] ||P[i]_) is continuous in _u ≥_ 0. To see this, consider _Pj[i]_[as the known] distribution value, _Q[i] j_[is continuous in] _[ u][≥]_[0][ be-] cause 1+ _uu_[is continuous in][ R] _[ \ {−]_[1] _[}]_[.][In addition,] _Q[i] j_[will][not][be][zero][for][all] _[j][∈]_[[1][:] _[N][i]_[]][,][which] indicates that log(_QPj[i] j[i]_[)][is][continuous.][Therefore,] _DKL_ (_Q[i] ||P[i]_) is also continuous in _u ≥_ 0 since the function is a linear combination of continuous functions.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0013-20.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0013-21.png)

We will prove that _DKL_ (_Q[i] ||P[i]_) is nonincreasing in _u_ for _u ≥_ 0 in the next section. By the Intermediate-Value Theorem (IVT), it is clear that there exists a positive _u_ such that the KL divergence is equal to the given _δ ∈_ [0 _, N_[1] _i_ � _Nj_ =1 _i_[log(] _Ni_ 1 _Pj[i]_[)]][.]

In case _δ > N_ 1 _i_ � _Nj_ =1 _i_[log(] _Ni_ 1 _Pj[i]_[)][, we have]![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0013-24.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0014-00.png)

Here, we introduce the notation _T_[1][=] 1+ _uu_[to sim-] plify expressions and clarify the intuition behind the solution _Q[i]_. From this definition, it follows that _T_ = 1 + _u_[1][.][Because there exists a positive] _[ u]_[ such] that _DKL_ � _Q[i] ∥ P[i]_[�] = _δ_, we equivalently have a _T ≥_ 1 that satisfies this equality. This proves the first part of Lemma 1.

## **E Proof of Lemma 1 Second Part**

Here we show that _DKL_ (_Q[i] ||P[i]_) is non-increasing in _u_ for _u ≥_ 0, by analyzing the derivative as follows:

are above average, both with the total amount of 2 _[δ]_[.] A detailed closed-form solution is given below.

reformulate it as:![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-02.png)

Assuming _Pj[i]_[is sorted in descending order, let] _SH_ and _SL_ be the index sets of tokens. Define _SH_ = _{j ∈_ [1: _Ni_ ] _|Pj[i][≥] N_ 1 _i[}]_[ for high probability] tokens, and _SL_ = _{j ∈_ [1: _Ni_ ] _|Pj[i][<] N_ 1 _i[}]_[ for low] probability tokens. The closed-form solution of optimal _Q[i] j_[in the optimization problem (][39][)-(][44][)] is described by different cases.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-04.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-05.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-06.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-07.png)

The total variation _DTV_ (_Q[i] ||P[i]_), as defined in (38), is the norm 1 of the difference between _Q[i]_ and _P[i]_. Since all norms are convex, this problem remains a convex optimization problem and can be resolved by identifying the solution that meets all KKT conditions.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-09.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-10.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-11.png)

Clearly, the TV function is not differential at the point _Q[i] j_[=] _[P][ i] j_[, resulting in the failure to achieve] stationarity. Thus, we introduce new variables _bj ≥_ 0 to this problem such that _|Q[i] j[−][P][ i] j[|][≤][b][j]_[.] The equivalent optimization problem (33)-(37) corresponding to (39)-(44) is now described as follows:![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-13.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-14.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-15.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-16.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-17.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-18.png)

The intuitive illustration of the solution _Q[i]_ is given in Figure 2.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-20.png)

Given that this optimization problem is convex, the solution is obtained by solving the KKT conditions. The Lagrangian function for problem (39)(44) is

The solution to this problem is similar to the waterfilling algorithm. To see this, we must recognize that the maximum entropy _Q[i]_ occurs when it is a uniform distribution. However, modifications to _Q[i]_ from _P[i]_ are restricted by a given limit _δ_. To allocate the value of each _bj_ such that their sum equals _δ_, the most straightforward method is to split _δ_ in half, then water-fill the probabilities that are below average _N_ 1 _i_[,][while][decrease][the][probabilities][that]![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0015-23.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0016-00.png)

where _u, α, β, λ, ω, η_ are the Lagrangian multipliers of constraint in (40)-(44). Then the KKT condition can be derived as follows:

We claim a solution to the KKT conditions as follows:

For _j ∈ SL_,

   1. Primal variables: The primal variables are the same as the formula stated in the Theorem. If there exist some K where _Ni − K ∈ SL_ and 2 _δ ∈_ [ _KPN[i] i−K[−]_[�] _[N] k_ = _[i] Ni−K_ +1 _[P][ i] k[,]_[ (] _[K]_[+] 1) _PN[i] i−K−_ 1 _[−]_[�] _[N] k_ = _[i] Ni−K[P] k[ i]_[)][, then]

1. stationarity:![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0016-06.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0016-07.png)

## 2. primal feasibility:

Otherwise, if 2 _[δ][≥]_[�] _k∈SL_[(] _N_[1] _i[−][P][ i] k_[)][,][then] _Q[i] j_[=] _N_ 1 _i_[and] _[ b][j]_[=] _N_ 1 _i[−][P][ i] j[,][∀][j][∈][S][L]_[.]![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0016-10.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0016-11.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0016-12.png)

## 3. dual feasibility:

## 4. complementary slackness:

The dual variables _u_ and all _βj, ηj_ s are positive because _K_ 1+1 � 2 _δ_[+][ �] _k[N]_ = _[i] Ni−K[P] k[ i]_ � _≤ P[i]_ 1 _[l][ ∈][S][L][ \]_[ [] _[N][i][ −][K]_[:] _[ N][i]_[]][.] _l[≤] Ni[,]_![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0017-00.png)

For _j ∈ SH_,![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0017-02.png)

This completes the proof.

## **G Proof of Theorem 3**

The result in proof of Theorem 1 shows that the solution to the optimization problem with constraint _DKL_ (_Q[i] ||P_[ˆ] _[i]_ (_ϵ_)) _≤ δ_[ˆ] (_ϵ_) is:![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0017-06.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0017-07.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0017-08.png)

Otherwise,![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0017-10.png)

Otherwise, if 2 _[δ][≥]_[�] _k∈SH_[(] _[P] k[ i][−] N_ 1 _i_[)][,][then] _Q[i] j_[=] _N_ 1 _i_[and] _[ b][j]_[=] _[ P][ i] j[−] N_ 1 _i[,][∀][j][∈][S][H]_[.]

for all _j ∈_ [1: _Nϵ_ ] and for some positive _u_ ˆ(_ϵ_). In addition, Lemma 1 states that when _δ_[ˆ] (_ϵ_) _∈_ [0 _, N_[1] _ϵ_ � _Nj_ =1 _ϵ_[log(] _Nϵ_ 1 _P_[ˆ] _j[i]_[)]][, the obtained solution en-] sures that the KL divergence _DKL_ (_Q[i] ||P_[ˆ] _[i]_ (_ϵ_)) is equal to the given constraint _δ_[ˆ] (_ϵ_). We first calculate the KL divergence of the truncation process, which is the distance between _P[i]_ and _P_[ˆ] _[i]_ (_ϵ_).

2. Dual Variables: Continue with the conditions above about _[δ]_ 2[,] for _[δ]_ 2 _[∈]_[[][�] _k[K]_ =1 _[P][ i] k[−][KP] K[ i]_ +1 _[,]_[ �] _k[K]_ =1[+1] _[P] k[ i][−]_ (_K_ + 1) _PK[i]_ +2[)][,]![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0017-14.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0017-15.png)

The dual variables _u_ and all _αj, ηj_ s are positive because _K_ 1+1 �� _Kk_ =1+1 _[P] k[ i][−]_ 2 _[δ]_ � _≥ Pl[i][≥]_

+ _DTV_ (_Q[i] ||P_[ˆ] _[i]_ (_ϵ_)) (73)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0018-01.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0018-02.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0018-03.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0018-04.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0018-05.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0018-06.png)

_u_ ˆ(_ϵ_) where Γ([ˆ] _ϵ_) =[�] _[N] j_ =1 _[ϵ][P][ i] j_ 1+ˆ _u_ (_ϵ_) in (67) and equation (71) follows from (63).

## **H Choice of** _δ_[ˆ] (_ϵ_) **Under TV Constraint**

Under TV constraint, the optimal solution _Q[i]_ to this optimization problem is given in theorem 2. By adopting a probability cutoff before adjustments, the TV distance upper bound between _P[i]_ and _Q[i]_ becomes the sum of the cutoff and adjustment TV distances, due to the triangular inequality.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0018-10.png)

Calculating the TV distance between the original probability and the reduced probability is straightforward:![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0018-12.png)

Assuming the cutoff tokens [ _Nϵ_ + 1: _N_ ] have probabilities summing up to _ϵ_, the rest of the probabilities from [1: _Nϵ_ ] sum to 1 _− ϵ_, leading to the equality in equation (75). Therefore, the equation (73) can be further derived as:![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0018-14.png)

However, this upper bound is not a strict upper bound. In fact, the actual value of the total variation between _Q[i], P[i]_ may be slightly lower than this upper bound, given that the TV divergence is not additive, this differs from the conclusion in Theorem 3, where we found that the KL divergence is additive in the particular case.

## **I KL divergence vs. Parameter C**

In this section, we demonstrated that our adjustment parameter _C_ is strongly correlated with the KL divergence between stego-text and natural text. As shown in Figure 10, these two values exhibit an almost linear relationship, indicating that as _C_ increases, the distortion relative to the original probability distribution given by the LLM also increases. This result is intuitive since we define _δi_ = _C · H_ (_P[i]_), meaning that a larger _C_ directly leads to a larger _δi_, which is a larger adjustment. Figure 11 gives a comparable plot for OD-TV. Despite the non-linear relationship between KL divergence and parameter C here, the figure illustrates that C remains effective in controlling the probability divergence.

## **J OD-KL v.s. Temperature Adjsutment**

This section presents an experiment comparing ODKL adjustments with direct temperature scaling in![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0019-00.png)

Figure 11: KL-divergence vs. parameter C (OD-TV).

the LLM. In Figure 12, the x-axis represents the KL divergence between the adjusted distribution and the original LLM distribution, while the y-axis indicates the number of bits that can be embedded into the stego-text, which corresponds to the entropy. The red triangles denote the results obtained by tuning the temperature parameter, whereas the ODKL adjustment is computed using our closed-form expression provided in Theorem 1. We observe that the two methods yield identical results, which confirms our claim in Remark 1 that OD-KL adjustment is equivalent to temperature scaling at the logits level.

## **K Details for Steganalysis Models**

For the three steganalysis techniques, the models were trained using stego-texts generated with the parameter _C_ ranging from 0.01 to 0.1 (in step 0.01) and with _ϵ_ = 0 _._ 025, combining generations under both KL and total variation (TV) constraints. These were mixed with naturally generated texts without any steganographic encoding. For each of the 10 distinct _C_ values, 200 stego-texts are included in the training set, alongside 4000 naturally generated texts (non-stego) generated from Llama2-7B![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0019-05.png)

Figure 12: OD-KL vs. Adjusted Temperature

and GPT2-XL. For GS-Llama, we applied LoRA to fine-tune Llama-3.1-8B-Instruct, optimizing for efficiency while maintaining performance. The model underwent 10 epochs of training (24 GPU hours) using one NVIDIA H100 GPU (80GB memory), a learning rate of 1 _×_ 10 _[−]_[5], FP16 precision, a sequence length of 128, and the AdamW optimizer, without implementing a validation split to leverage the data fully. For FCN, training was conducted over 300 epochs with a learning rate of 5 _×_ 10 _[−]_[4]. For SESY, training was performed over 10 epochs using the AdamW optimizer with a learning rate of 5 _×_ 10 _[−]_[5]. The model was trained for 10 epochs, which took approximately 8 GPU hours on a single NVIDIA A100 GPU with 40 GB of memory. Other parameters were kept as the default values in FCN (Yang et al., 2019), SESY (Yang et al., 2021), and GS-Llama (Yang et al., 2024).

## **L Alternative Plots for Steganalysis Results**

In this section, we present the accuracy plots of steganalysis results for the three models: FCN, SESY, and GS-LLaMA. As shown in Figure 13 and Figure 14, it is evident that FCN achieves lower accuracy compared to the other two models. In fact, FCN struggles to reach 70% accuracy, even when the parameter _C_ is set to a relatively large value such as 0.1. In contrast, the other two models—SESY and GS-LLaMA achieve over 70% accuracy when _C >_ 0 _._ 05. This improved performance is likely due to their transformer-based architectures. In particular, GS-LLaMA, which is fine-tuned from the LLaMA3-8B model, serves as a very strong detector in this context.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0020-00.png)

Figure 13: Steganalysis results of three detection models on OD-Stega, with accuracy plotted on the y-axis.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0020-02.png)

Figure 14: Steganalysis results of three detection models on OD-Discop, with accuracy plotted on the y-axis.

## **M Parameter Choice to Avoid Tokenization Error and Experiment Details**

We heuristically determine the length of _B_ that guarantees the steganography process succeeds with high probability, which we set as 1 _−_ 10 _[−]_[8] in our work. We observe that for Llama2-7B models, a single bit produces a tokenization error at a rate below 2 _×_ 10 _[−]_[4]. We can make 2 _[|][B][|]_ separate attempts, and only one successful attempt is needed, i.e.,![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0020-06.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0020-07.png)![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0020-08.png)

assuming _B_ is significantly shorter than _S_. Bob can indeed determine the length of _B_ by referencing the length of the secret message _S_ using equation (78).

Our experiment begins with random B-bit prefixes, which is equivalent to selecting a random

initial interval in the probability distribution, ensuring that token sequence selection is unbiased under this process. If this generated text runs into a tokenization error, we randomly sample a new B-bit prefix. In our experiments, out of 100 generated text sequences of 25 tokens each, fewer than 10 cases needed a second attempt with a new prefix B, showing that the iteration rate of this procedure is sufficiently low.

## **N Non-Stego vs.** _δ_ = 0 **Stego-Text**

We employ GS-Llama as a classifier to assess whether the detector can differentiate between natural text and stego-text encoded with _δ_ = 0. For this purpose, we train a binary classification approach using a balanced dataset of 1,000 samples, consisting of 500 naturally generated texts (from Llama27B) and 500 _δ_ = 0 OD-stage encoded texts. The stego-texts were labeled as "stego," while natural texts were labeled as "non-stego". Each input followed a standardized prompt format:

### Text: {input_text}

### Question: Is the above text stego or non-stego?

### Answer:

We fine-tune the Llama-3.1-8B-Instruct model to function as a classifier with the same training details provided in section K and assess its performance using a separate test set. As shown in Table 2 and 3, the classifier achieve an overall accuracy of 49.8% and a macro F1 score of 49.8%, performing at chance level. These results indicate that _δ_ = 0 stego-texts are computationally indistinguishable from naturally generated texts, even when analyzed by a strong large language model-based detector.

Table 2: Binary classifier results on 500 stego-texts and 500 natural texts. The value in the table is the number of texts count.

|xts count.|||
|---|---|---|
|True<br>Predict|Stego|Non-stego|
|Stego_δ_ = 0|248|252|
|Non-stego|250|250|

Table 3: Binary classifier results on 500 stego-texts and 500 natural texts. These are the common metrics that evaluate the model performances.

|Test data|Precisi|on<br>Recall|F1|
|---|---|---|---|
|Stego_δ_ = 0<br>|0.498<br>|0.496<br>|0.497<br>|![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0021-02.png)

Figure 15: GPT4 detection score on OD-Discop-KL with GPT2-XL vs. average (over 200 texts) bits embedded per 25 tokens.

## **O Additional GPT Evaluation Result**

We include the result of GPT-4 evaluation on ODDiscop in Figure 15 and 16.

## **P Steganalysis Result on Longer Text Sequence**

We retrained the detection models with extended text sequences and conduct steganalysis on the ODstega outputs with token length of 100, using a probability cutoff of _ϵ_ = 0 _._ 025 and varying the parameter C in the range from 0 _._ 01 to 0 _._ 1. The results are presented in Figure 17. In both detection methods, the accuracy curves follow the same trend as those for the shorter sequences but are shifted upward. This upward shift occurs because longer sequences make the embedded signal easier to detect: as the detector observes more tokens, subtle distributional differences in the stego-text accumulate and become more perceptible. These results further motivate embedding more information into shorter texts to reduce detectability.

Figure 18 presents a comparison of GPT-4 evaluation scores for token length 100 (circular markers) and token length 25 (square markers). The dashed line and solid line illustrate how the scores for token 100 and token 25, respectively, evolve as the parameter _C_ increases. We observe that as _C_ increases, the distance between the two lines![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0021-09.png)

Figure 16: GPT4 detection score on OD-Discop-TV with GPT2-XL vs. average (over 200 texts) bits embedded per 25 tokens.

becomes larger, indicating that the divergence of each token accumulates over the length of the texts. Consequently, text sequences of length 100 exhibit a higher average embedding rate but a lower detection score, implying they are more likely to be flagged as abnormal. This observation is consistent with the results shown in Figure 17.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0021-12.png)

Figure 17: Steganalysis results on longer text sequences (token length 100) verses shorter text sequences (token length 25), with accuracy plotted on the y-axis.

## **Q More Graphs**

In Figure 19, we present the embedding utilization behavior under a fixed total variation constraint for OD-Discop stego-texts. While OD-Discop-KL (or temperature adjustment) is optimal for maximizing the number of embedded bits under a KL divergence constraint, it is not optimal under a TV constraint. This indicates that temperature tuning is no longer the best adjustment strategy when a different constraint, such as total variation, is considered.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0022-00.png)

Figure 18: GPT4 detection score on OD-Stega longer text sequences (token length 100) verses shorter text sequences (token length 25), with average embedding rate on the y-axis.![](2026-eacl-long-36-od-stega_images/2026-eacl-long-36-od-stega.pdf-0022-02.png)

Figure 19: Average bits embedded using different adjusting methods OD-Discop-KL and OD-Discop-TV under the same total variation distance.

## **R More Stego-Text Examples**

Tables 4 and 5 demonstrate the generated OD-KL stego-text by setting the parameter _ϵ_ = 0 _._ 025 and comparing results from small and larger adjustment values _C_. In Table 5, odd content arises in the larger parameter _C_ = 0 _._ 05 stego-text. Nonetheless, in most instances, the stego-text generated with a larger _C_ appears typical, as depicted in Table 4.

In Table 6, we present examples produced by OD-TV adjustments. Notably, SESY demonstrates its strength. Even when the text appears normal in the _C_ = 0 _._ 05 scenario, SESY still identifies it as stego-text correctly.

Table 4: Example stego-texts OD-KL: Same cutoff, different adjustment parameter _C_.

|Parameters|Prompt: Once upon a time, there was<br>a princess who|SESY|FCN|
|---|---|---|---|
|||||
|_C_ = 0_._01<br>_ϵ_ = 0_._025<br>_C_ = 0_._05<br>_ϵ_=0025|was going to marry a prince. She lived<br>in a cramped palace. It wasn’t big, and<br>she wasn...<br>liked travel. After a few sprees through<br>|NS<br>S|NS<br>NS|
|_._<br>_C_ = 0_._09<br>_ϵ_ = 0_._025|Paris, Milan, Rome and Palm Springs,<br>she...<br>cried out, ’Ah well, I do adore thick<br>pungent sweat pouring down onto my<br>crim...|S|S|

Table 5: Example stego-texts OD-KL: Same cutoff, different adjustment parameter _C_.

|Parameters|Prompt: Over the next few days, the<br>weather will be|SESY|FCN|
|---|---|---|---|
|||||
|_C_ = 0_._01<br>_ϵ_ = 0_._025|16 to 20 degrees, after the 11th 12th<br>temperature was slightlylower,...|NS|NS|
|_C_ = 0_._05<br>_ϵ_ = 0_._025|4 minutes earlier each night, Sun/Mon<br>AFAIK no Co2 Med Decision Don,<br>MS October 9...|S|S|

rameter _C_ is considerably high. It is observed that this occurs because such prompts are capable of generating text sequences with higher entropy. Tables also show that SESY outperforms FCN as a detector.

Table 6: Example stego-texts OD-TV: Same cutoff, different adjustment parameter C

|Parameters|Prompt: I went to this restraunt the<br>other day, and I would rate its food|SESY|FCN|
|---|---|---|---|
|||||
|_C_ = 0_._01<br>_ϵ_ = 0_._025|4 stars out of 5. The place was half<br>empty, which was great, because the<br>onlything you needed to fll|NS|NS|
|_C_ = 0_._03<br>_ϵ_ = 0_._0175|8/10. My mother and father said how-<br>ever, that its not as good as it used to<br>be. Never ce...|NS|NS|
|_C_ = 0_._05<br>_ϵ_ = 0_._005|6 out of 10. It was dirty and dishev-<br>elled, too. The load text and video<br>entered...|S|NS|

In Figure 20 and 21 we show more examples of generated stego-texts using the proposed OD-Stega approach with various parameters. It can be seen that as the _C_ parameters increase for fixed cutoff value, the embedding capability increases. The generated stego-texts mostly remain fluent in this parameter range.

In tables 7 and 8, we have included several text samples that illustrate the OD-Discop method. In these examples, the cutoff value _ϵ_ is held constant while the value of the parameter _C_ is varied. It is evident that in certain prompts the OD-Discop texts continue to appear normal even when the pa-

Table 8: Example stego-texts: OD-Discop-TV stegotext example (GPT2-XL).

Table 7: Example stego-texts: OD-Discop-KL stegotext example (GPT2-XL).

|text example (GPT2-XL).|p|.|||
|---|---|---|---|---|
|<br>Parameters<br>Prompt: There are many species of an-<br>imals living in the Amazon rainforest,<br>including species such as<br>SESY<br>FCN<br>Discop<br>_ϵ_ = 0_._025<br>ursids such as Amazon fre bats, but<br>the recently announced discoveries in<br>China of evidence for alien primates<br>was an "earth-...<br>NS<br>NS<br>_C_ = 0_._01<br>_ϵ_ = 0_._025<br>ichthyosaurs, which were partly scav-<br>enged by large turtles like ammonoids,<br>which had a diet that consisted mostly<br>of wood...<br>NS<br>NS<br>_C_ = 0_._05<br>_ϵ_ = 0_._025<br>ichthyosaurs that sat 150 feet under-<br>ground, sometimes buried in silt be-<br>tween a surface rainforest (corals and<br>mounds...<br>S<br>NS<br>_C_ = 0_._09<br>_ϵ_ = 0_._025<br>ichneumon beetles, carbon dioxide-<br>loving methanodonts, rodents, humans<br>and landrover loads of other...<br>S<br>NS<br>Parameters<br>Prompt: For all the sports fans out<br>there, there was a recent upset between<br>Discop<br>_ϵ_ = 0_._025<br>Panthers LB Luke Kuechly and Saints<br>LB Joe Vellano, in the same division.<br>If Carolina...<br>NS<br>NS<br>_C_ = 0_._01<br>_ϵ_ = 0_._025<br>iced tea and hot water that you really<br>probably missed. Speaking of hot, that<br>Minnesota Snack Club (someone hurt<br>someone)...<br>NS<br>S<br>_C_ = 0_._03<br>_ϵ_ = 0_._025<br>Kent State and Utah.<br>What I really<br>miss most about the neutral court, and<br>mycapacityto sit and watch sports...<br>NS<br>NS<br>_C_ = 0_._07<br>_ϵ_ = 0_._025<br>Mount Bank BC and Carrie 10 BC that<br>saw the band and its supporters are dis-<br>illusioned with Season 5!!! Let me re<br>...<br>S<br>S<br>_C_ = 0_._09<br>_ϵ_ = 0_._025<br>lloVici Gaming and Nomia PK brand.<br>The fag-ship Jungler hit kills around<br>the mapin the bad Fight...<br>S<br>NS|Parameters|Prompt: In this blog post, I would like<br>to recount an event that happened to<br>me the other day. I was leaving my<br>house when|SESY|FCN|
||||||
||Discop<br>_ϵ_ = 0_._025|I came across an interesting volume of<br>mythography. The celestial mythogra-<br>phers of Mesopotamia were present in<br>verylarge...|S|S|
||_C_ = 0_._01<br>_ϵ_ = 0_._025|I noticed things very strangely going<br>on inside my front door. Something<br>was big and metallic, so it seemed to<br>be drawing...|NS|NS|
||_C_ = 0_._03<br>_ϵ_ = 0_._025|as I rounded the corner to the tenway<br>exit I saw a taxi cab driver swatting at<br>a debt frm car out...|S|NS|
||_C_ = 0_._05<br>_ϵ_ = 0_._025|I felt hering Chinese launched his<br>strike at me.<br>It all happened very<br>quickly and in that moment I just re-<br>alised I...|S|NS|
||_C_ = 0_._07<br>_ϵ_ = 0_._025|a pigeon appeared from outside, RITP<br>puffng till it enlarged the bolt holes on<br>myroof! A third...|S|NS|
||||||
||Parameters|Prompt: In the recent Tokyo 2024<br>Olympics, the most notable event was<br>the|||
||||||
||Discop<br>_ϵ_ = 0_._025|ichinen sumo wrestling contest be-<br>tween sumo’s three greatest battlers,<br>Mark Kerr, Babaev and Hikaru S...|NS|NS|
||_C_ = 0_._01<br>_ϵ_ = 0_._025|ichi rugby sevens qualifying match be-<br>tween Britain, Scotland and Fiji, whose<br>fans underlined their policy of joining<br>in whenever Japan has...|NS|NS|
||_C_ = 0_._03<br>_ϵ_ = 0_._025|izakaya<br>("bar<br>and<br>sauna")<br>being<br>erected in Ho-ho-koo, right next to<br>Mount Fuji,...|NS|NS|
||_C_ = 0_._05<br>_ϵ_ = 0_._025|izakaya span will open to bid patrons<br>starting 15 months after the November<br>2015 opening day, when you would<br>likelyfail the...|S|NS|

||Bytes<br>Embedded<br>Parameters<br>(delta, cutoff)<br>Prompt+ stego-text<br>13<br>(0, 0.025)<br>Due to recent advances in technology,3D Printing  has enabled rapid prototyping to become reality. Smaller<br>businesses can use such printing to develop…<br>14<br>(0.005, 0.025)<br>Once upon a time, there was a princess who— after  one too many fits of pique -- had become so angry at<br>her sister that she abruptly left the palace…<br>14<br>(0.015, 0.025)<br>In this blog post, I would like to recount an event that happened to me the other day. I was leaving my house<br>when12 young students between 17 to 19 years of age  drove towards me fast, completely enamoured on…<br>15<br>(0.025, 0.025)<br>BREAKING NEWS: Yesterday in Pennsylvania,5-time Ryder  Cup Golf star and Chicago's favorite son,<br>Steve Stricker had this picture of him put…<br>17<br>(0.035, 0.025)<br>Due to recent advances in technology,3D printers  can solve so many different problems across multiple<br>industries - our SEMI Boston event and first-ever…<br>18<br>(0.045, 0.025)<br>Over the next few days, the weather will be7 degrees  off prime fishing period averages. From tomorrow at<br>dawn until Sunday, new moon starts Wednesday…<br>12<br>(0.015, 0.045)<br>The newest development in the recent election is1.3  million votes and counting from provisional ballots still<br>being tallied. Some Democrats have speculated that…<br>17<br>(0.015, 0.015)<br>For all the sports fans out there, there was a recent upset between6th and 12th seeds such that the energy  in<br>the Houston Astrodome almost made every eye in the…<br>16<br>(0.015, 0.005)<br>BREAKING NEWS: Yesterday in Pennsylvania,300 guests  attended an opening reception honoring Your<br>Sculpture Man of the Year Don Bredeskin….<br>16<br>(0.035, 0.045)<br>The newest development in the recent election is3,000  votes being reported under Mr. Bush’s name on<br>punch cards in the recount in…<br>19<br>(0.035, 0.015)<br>For all the sports fans out there, there was a recent upset between49er Colin Kaepernick and DoDo Dallah<br>of England. Each is specifically covered by their respective ex…<br>20<br>(0.035, 0.005)<br>BREAKING NEWS: Yesterday in Pennsylvania,17 bands  plus Mighty Mofo and Kraftwerk respectively<br>took the Field of Toledo podiums to c…|
|---|---|

Figure 20: Stego-text examples (OD-KL) in different pair of parameters (_C, ϵ_) and length of secret message embedded.

|Bytes<br>Embedded|Parameters<br>(delta, cutoff)|Prompt+ stego-text (first 25 tokens)|
|---|---|---|
|12|(0.000, 0.025)|Once upon a time, there was a princess whohad a meadow with a pond and a flock<br>of ducks. And once again, there was a prince who...|
|13|(0.010, 0.025)|For all the sports fans out there, there was a recent upset between2 major sports<br>organizations that’s somewhat related to sports.<br>The USTA gives American kids a headstart in...|
|14|(0.020, 0.025)|The newest development in the recent election is47 percent of voters are claiming to<br>not know who they want President. I have some advice for these “und...|
|13|(0.030, 0.025)|In this blog post, I would like to recount an event that happened to me the other day.<br>I was leaving my house when2 random guys, approached me and pressed me to join<br>them outside. They justified it by saying: “We wanted to...|
|17|(0.040, 0.025)|The newest development in the recent election is87,000 votes in Orange County<br>remain uncounted, namely because of improper registration. Democrats tra...|
|16|(0.050, 0.025)|In this blog post, I would like to recount an event that happened to me the other day.<br>I was leaving my house when2 gorgeous females followed me.<br>Since this went on for nearly a block it was quite nice to stay and wait...|
|16|(0.060, 0.025)|For all the sports fans out there, there was a recent upset between2 major athletes.<br>Firstly, Tiger Woods was recently lowered off of his privacy over, when records...|
|17|(0.070, 0.025)|Due to recent advances in technology,3d printing now offers the true potential to<br>control meal portion and macronutrient intake. Complex RIT...|
|19|(0.080, 0.025)|Over the next few days, the weather will be1 degrees warmer than on Saturday. Best<br>blessing!! Jack Frost might be on vacation, but let's...|
|19|(0.090, 0.025)|Once upon a time, there was a princess who❤food.... OMG, her name is you.<br>Crowned as December's Kno...|
|23|(0.100, 0.025)|The newest development in the recent election is10 lbs/lb opinion. Per the husband<br>who cheers from the sidelines, Democratic days are here....|
|21|(0.110, 0.025)|I went to this restaurant the other day, and I would rate its food2 from one to five.<br>Third was without ingredients like green seasoning, rosemary cheese and spie...|
|21|(0.120, 0.025)|Due to recent advances in technology,3G speeds are helping replace wires and<br>create wireless untethered results; theatres, TV, present...|
|23|(0.130, 0.025)|For all the sports fans out there, there was a recent upset between5 spots of John<br>Lobb Royce Navy grain leather we highlighted on (Boot Renching post)...|

Figure 21: Stego-text examples (OD-TV) in different pair of parameters (_C, ϵ_ = 0 _._ 025) and length of secret message embedded.
