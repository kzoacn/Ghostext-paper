# Review: Ghostext — A Deterministic, Fail-Closed LLM Steganography Protocol with Implementation-Aligned Approximation Bounds

**Reviewer:** Anonymous · **Date:** 2026-04-22 · **Recommendation:** Weak Reject — Major Revision

本轮审读基于 `paper/` 当前版本（abstract 已重写为 "protocol-engineering contribution rather than near-perfect-security claim"，§8.4 的 aligned slice 已落地为 Table 4，6 条 Qwen case 对比 Ghostext / NLS-UTF8 / NLS-AEAD-packet）。相对之前轮次，**narrative corridor 干净、artifact 纪律延续、scope 措辞全篇收敛**，但 **experiment-level 证据厚度仍处在 "feasibility pilot + one narrow slice" 的层级**，距离任何 mainstream venue 的接收门槛仍有三到四项必须补齐的结构性 item。

---

## 1. Summary

这篇论文的 honest 定位是：**一个实现完整、协议文档规范、approximation bound 显式推导的 LLM steganography 系统论文，但 empirical core 只有 18 条主基线 + 6 条 aligned 对比 slice**。

具体构成：

1. **协议层（§3–§5）**：3-role 模型 + AEAD packet 格式 (`salt || header_nonce || sealed_header || body_nonce || body_ciphertext`) + bootstrap/body 两段式嵌入 + 配置 fingerprint (SHA256 前 64 bit) + fail-closed 失败类型学。写法清晰，protocol 描述充分。
2. **approximation bound（§5.5–§5.6, §7.3–§7.4）**：per-step TV bound $\mathrm{TV}(Q'_t, P_t) \le \alpha_t + N_t/(2F_{\text{tot}}) + \beta_t$；KL 上界 $D_{\mathrm{KL}}(\widetilde{P}_t \| Q_t) \le N_t/F_{\text{tot}}$ nats；Pinsker bridge 到 $\mathrm{Adv}_{\mathrm{censor}}$。推导严格但**所有 bound 在当前 artifact 中从未被实测过**——§7.6 的 $\widehat{B}_{\mathrm{TV}}$ 只出现在公式里，没有一条 log 数据被聚合为 histogram。
3. **pilot 实验（§8.3）**：18 条 template-known trials (9 en + 9 zh)，policy `top_p=0.995, max_candidates=64, min_entropy_bits=0.0, total_frequency=4096`；SR 18/18 (Wilson 95% CI $[0.824, 1.000]$)；encode median 50.56 s，bits/token mean 2.478；attempts_used mean 1.944。
4. **aligned slice（§8.4）**：6 条同 backend 同 policy 对比，三种方法各 n=6。Ghostext full 6/6 / NLS UTF-8 5/6 / NLS AEAD 4/6；encode median 31.85 / 8.50 / 46.21 s。

Abstract 和 §1 的 contribution statement **与上一版相比变得显著更克制**：明确写 "positioned as a protocol-engineering contribution rather than a near-perfect-security claim"（abstract 第 20 行），"an initial same-backend comparison slice"（§1 第 16 行），"do not make broad superiority claims"（§12.6 第 42 行）。这个 scope discipline 在投稿当下是**唯一能让 reviewer 继续认真读下去的因素**——论文没有用它没有的证据说话。

但 **Weak Reject** 的判断依然成立。理由：

- **主基线 n=18** 的 Wilson CI $[0.824, 1.000]$ 只能支持 "feasibility" 级别的 claim；
- **aligned slice n=6** 三个 method 的 Wilson CI 大面积重叠，只是 "descriptive observation"，不是 "statistical evidence"；
- **$h_{\min}$ sweep 零数据**，headline 2.478 bits/token 来自 $h_{\min}=0.0$ 这个论文自己承认 "not a recommended deployment point" 的 operating point；
- **detector-side (Stage 5) 零数据**，论文在 §7.6 自己承诺 "correlation analysis between $\widehat{B}_{\mathrm{TV}}$ and detector scores as a required output, not an optional add-on"，目前是未兑现的 self-commitment；
- **Qwen provenance + llama.cpp SHA 两项 metadata fix 仍未补**，这是 reproducibility 的最低工作量项。

§8.7 的 Stages 3 / 4 / 5 / 6 全部 pending。论文把责任放在了 staged protocol 的后续 revision 上，但 staged protocol 在投稿层面并不是接收理由——它是 **promise**，而 reviewer 需要 **evidence**。

---

## 2. Strengths

1. **Protocol-level 写法成熟**：§4–§5 把 encode/decode lifecycle、bootstrap/body 分段、natural tail、failure taxonomy 都写得条理清楚。`\fbox` 的 Figure 1 pipeline 虽然视觉简陋，但 §4.3 operational semantics 的文字补充足够让 reviewer 跟上协议流。
2. **approximation bound 的推导是正经的**：§5.6 给出 $\mathrm{TV}(Q'_t, P_t) \le \alpha_t + N_t/(2F_{\text{tot}}) + \beta_t$ 的三项加和 bound，正确处理了 filtering 后 renormalization 的 double-counting 问题（$\|Q'_t - R_t\|_1 = \beta_t$ 和 $\|R_t - Q_t\|_1 = \beta_t$ 都用同一个 $\beta_t$ 覆盖）。§7.4 的 KL upper bound 用 $-\log(1-u) \le u^2/(1-u)$ 加 $Q_t(v) \ge 1/F_{\text{tot}}$ 的 floor lemma，推导 3 步干净，结论 $N_t/F_{\text{tot}}$ nats 是 loose but explicit 的工程可用 bound。
3. **Cachin / Pinsker bridge 的 scope 标注**：§7.6 第 98 行 $\mathrm{Adv}_{\mathrm{censor}} \le \mathrm{TV}(Q_{1:T}, P_{1:T}) \le \sqrt{D_{\mathrm{KL}}/2}$ 之后**立刻**声明 "$\widehat{B}_{\mathrm{TV}}$ is therefore an audit signal rather than a direct detector-risk guarantee"——这是对 steganography 文献里常见的 "大小 TV → 小 detector AUC" 过度 inference 的主动防御。
4. **fingerprint collision discussion 的诚实**：§5.7 和 §7.8 两处讨论 64-bit fingerprint 的 birthday bound ($n=10^6 \to 2.7\times10^{-8}$) 和 adaptive collision ($2^{40}$ trials $\to 2^{-24}$)，并主动承认 "not a margin worth presenting as future-proof when the byte overhead of widening is negligible, 128-bit fingerprinting is the conservative future direction"。这是 crypto-engineering 审稿人会欣赏的**主动自我降权**。
5. **threat-capability matrix (Table 1)**：§3.4 把 "in scope / measured axis / out of scope" 明确分类，防止 reviewer 用 out-of-scope 的 attack surface 拷问论文。特别是 "Active text modification in transit = out of scope" 一句直接锁定了 passive-censor threat model 的边界。
6. **retry-traffic leakage 的前置暴露**：§7.9 主动指出 "retry count alone is trivially separating feature against any zero-retry natural-cover baseline; no learned detector is required to exploit that difference"。论文自己写出这条 trivially separating 结论，但**没有在 §8 里跑这条实验**——这既是 strength (scope honesty) 也是 concern (self-committed experiment 未兑现)。
7. **aligned slice 的 split claim**：§8.4 第二段 "cryptographic payload normalization removes direct plaintext structure at the carried-bitstream layer, but segmentation and runtime controls are still needed to make that randomized payload usable on this backend"——这是一条**与 Table 4 的 SR 列数据精确对齐**的 claim。NLS AEAD 单段 4/6 vs Ghostext full 6/6 这 2 例 stall 差值是这条 claim 的**直接证据**，虽然样本量偏小（见 M1）。
8. **artifact 纪律**：`results/aligned-qwen-baselines/aligned_baseline_summary.json` 一处同时暴露 `ghostext_git_head`, `paper_git_head`, `tokenizer_hash`, `backend_id`, `seed=7`, 完整 `candidate` 和 `codec` config；reproduce 脚本就位；Appendix A Table 5 也补了 aligned slice 行。这一处比主 baseline 的 summary 字段更完整。

---

## 3. Major Concerns

### M1. 样本量单薄：主基线 n=18，aligned slice per-method n=6

这是这版 empirical core 的**首要结构性限制**。

**主基线**：18 条 trials，aggregate Wilson 95% CI $[0.824, 1.000]$。per-language (n=9 each) 的 Wilson CI $[0.701, 1.000]$。这样的 CI 区间**只能支持 "在这个 pinned 18-case 上 SR=1" 的 descriptive claim**，不能支持 "Ghostext 在一般意义上 SR ≥ 0.95" 的 inferential claim。从 stego reliability 的角度，下限 0.701 意味着真实 SR 在 70% 附近也兼容——这个区间对于一个以 fail-closed 为卖点的协议来说**太宽**。

**aligned slice**：per-method n=6。三个 method 的 Wilson CI：
- Ghostext full (6/6) → $[0.610, 1.000]$
- NLS UTF-8 (5/6) → $[0.419, 0.963]$  
- NLS AEAD (4/6) → $[0.300, 0.898]$

三个区间**大面积互相重叠**。即便 6/6 vs 4/6 看起来差距显著，在 Fisher exact 下 $p \approx 0.45$，属于 non-significant。§8.4 第二段没有使用"显著优于"这类措辞（写的是"stalls on ... cases"），这是正确的 writing 纪律；但正因为写得克制，reviewer 更想看见 per-method n ≥ 30 的版本把这条 split claim 从"观察"升级为"证据"。

**本轮可接受的三条路径**（三选一）：
- (a) **主基线扩到 n ≥ 100**：cells = prompt family × language × message length = 至少 3 × 2 × 3 = 18 cells × ≥ 6 trials；
- (b) **aligned slice 每 method 扩到 n ≥ 30**：对同 6 case 跑 5 次 seed rotation；Table 4 附 per-method Wilson CI；
- (c) **重新定位为 short paper / workshop paper**（标题可加副标 "Feasibility Pilot"）。

继续停在 n ∈ {6, 18} 的区间，reviewer 在 main venue 找不到接受理由。

### M2. 主基线 vs aligned slice 的 Ghostext encode median 差 37%，未在文中解释

这个问题**非常显眼**，但论文没有处理：

| 测量来源 | $n$ | policy | Ghostext encode median (s) |
|---|---:|---|---:|
| Main baseline (§8.3 Table 2) | 18 | `top_p=0.995, max_cand=64, min_ent=0.0, F_tot=4096` | **50.56** |
| Aligned slice (§8.4 Table 4) | 6 | 同上 | **31.85** |

同一协议，同一 policy，同一 backend，encode median 差 **37%**。可能原因：
1. **Message 子集差**：aligned slice 的 6 条是主 baseline 18 条的子集（且多为 short/mid），主 baseline 有更长 message。论文确实没有在任何地方说明 aligned slice 的 case 选择规则。
2. **Retry 分布差**：主 baseline `attempts_used` mean 1.944，aligned slice 的 attempts 分布在 Table 4 里**完全丢失**（summary.md 仅显示 Ghostext full failure histogram `{}`，推断 retry = 1）。如果 aligned slice 恰好 6 条全部一次通过，这会直接解释 encode median 的下降。
3. **Seed / 运行时机**：aligned summary 显式写 `seed: 7`，主 baseline seed 未暴露；时间差上 aligned slice 是 2026-04-21T13:48:52Z 新跑，主 baseline r1+r2 是 merge。
4. **System noise**：WSL2 host 的 CPU 负载 / 内存压力差异。

**论文目前没有在 §8.4 写任何一句澄清**。在没有解释的前提下，reviewer 只能默认结论：**"Ghostext full 的 encode median" 这个数字本身不是一个稳定估计**——主 50.56 s 和 aligned 31.85 s 差 37% 意味着该 quantity 在 n=18 和 n=6 的 sample 下漂移幅度和样本间差异可能同量级。这会**同时削弱主 baseline 和 aligned slice 两张表的 interpretability**。

**Ask**：§8.4 加一段（或 Table 4 caption 下一行 footnote）明确：
> "Aligned slice reuses the six short/mid cases from the main 18-trial baseline. The lower encode median here relative to the merged $n=18$ figure reflects the shorter-message bias of this slice and reduced retry incidence, rather than a policy change."

同时把 aligned slice 的 `attempts_used` histogram 加到 Table 4——零新实验成本。

### M3. $h_{\min}$ sweep 仍然没有一行实测数据

§7.5 自己写：

> "The practical next step is therefore not to headline this single number, but to run the same condition grid at least over $h_{\min} \in \{0.0, 0.5, 1.0\}$ before treating any efficiency figure as representative of a conservative deployment envelope."

§13.1 第 13 行：

> "The reported 2.478 bits/token figure comes from an ungated baseline with $h_{\min}=0.0$ and should not be interpreted as a recommended deployment point."

但 Table 2 的 headline 仍然是 $h_{\min}=0.0$ 下的 2.478 bits/token，abstract 也用这个数。而 $h_{\min}=0.0$ 恰好是论文自己定义的 **"最激进、最不安全"** 的工作点——允许 per-step entropy 低到 0.01 bit 时仍然 embed，这是 detector 最敏感的区域。

**这条实验成本极低**：在 `results/real-backend-baseline-reproduce.sh` 基础上改一行 `--min-entropy-bits`，三档 × 18 条 = 54 runs。按每条 30–50 s encode + 30 s decode ≈ 90 s，串行 wall-clock 约 80 分钟。可以并行三进程进一步压到 30 分钟。

三档数据能立即回答：
- $h_{\min}=1.0$（implementation default）下 bits/token 还剩多少？预期 1.2–1.8 bits/token。
- $h_{\min}$ 升高是否改变 retry 分布？预期显著改变——高 $h_{\min}$ 下 low-entropy stall 触发概率上升，retry 频率会相应上升。
- $h_{\min}$ 是否改变 aligned slice 的 split claim？如果 $h_{\min}=1.0$ 下 Ghostext 也出现 stall，那 "segmentation + fail-closed 比 NLS single-segment 更稳" 这条结论的适用边界就需要被明确划出。

**这是本轮最 cheap-to-fix、最 high-value 的实验项**。reviewer 对这条的耐心是第三轮；继续不补会被视为 "author is unwilling to produce evidence that could weaken the headline number"。

### M4. Detector-side（Stage 5）零数据，§7.6 和 §7.9 的 self-commitment 未兑现

§7.6 明确写：

> "the staged detector block treats correlation analysis between $\widehat{B}_{\mathrm{TV}}$ and detector scores as a required output, not an optional add-on."

§7.9 明确写：

> "Under the current policy, retry count alone is therefore a trivially separating feature against any zero-retry natural-cover baseline; no learned detector is required to exploit that difference."

这两段话**在投稿层面已经形成 "unfulfilled self-commitment"**。§7.9 自己说 retry count 是 trivially separating AUC ≈ 1.0 的 feature，但没有把这条跑出来。§7.6 承诺 correlation analysis 是 required output，但没有一条 $\widehat{B}_{\mathrm{TV}}$ 数据被 aggregated。

**本轮 minimum 要求**：
1. **Retry-feature trivially separating AUC**：在现有 18 条 Ghostext cover + 18 条 "max_encode_attempts=1 强制截断" 的 R=1 natural-cover 对比上，直接计算 AUC。论文自己已经写了结论 AUC = 1.0，需要的是 **1 行代码 + 1 行 table**，不需要训练任何 detector。
2. **fastText binary AUC**：aligned slice 里已经有 6 × 3 = 18 条 stego cover（Ghostext full + NLS UTF-8 + NLS AEAD），再跑 18 条 natural Qwen cover（`llama-cli --temp 0.7 --seed 7 --prompt <P>`）作为 negative，用 `fastText-lid.176` 或 `cc.en.300` + logistic head 报 per-method ROC-AUC。即使 AUC 接近 0.5 也要报。
3. **$\widehat{B}_{\mathrm{TV}}$ histogram**：基于现有 runs，在 encode loop 里加一个 `per_step_log` hook，输出 $\alpha_t$ / $N_t$ / $\beta_t$，per-message 聚合为 $\widehat{B}_{\mathrm{TV}}$。这是 approximation instrumentation (Stage 3) 的最小 slice。

这三件实验**加起来不需要新模型、不需要 GPU、不需要 detector 训练**。第 1 条 < 30 min 工作量，第 2 条 < 2 小时，第 3 条 < 4 小时。

### M5. Qwen provenance + llama.cpp commit SHA：两项 metadata fix 一字未动

这是**本轮最无理由未补的一项**。§6.1 第 9 行写：

> "this paper follows the artifact identifier `Qwen/Qwen3.5-2B` as recorded in the released summaries. The companion implementation documentation points to the third-party GGUF repository `bartowski/Qwen_Qwen3.5-2B-GGUF` and the file `Qwen_Qwen3.5-2B-Q4_K_S.gguf`."

问题：**Qwen 官方从未发布 Qwen3.5-2B**。这是 bartowski 的第三方 GGUF 打包，上游真实模型应该是 Qwen2.5-1.5B / Qwen2.5-3B / Qwen3-1.7B 的某一个变体。论文在 §6.1 和 §13.1 第 23 行把这个差异交代得很诚实（"not as evidence that this string is the canonical upstream model-family tag"），但**没有补解决方案**。

两项都可以在几分钟内补上：

1. **Qwen 上游 family 解析**：
   ```bash
   llama-gguf-dump /path/to/Qwen_Qwen3.5-2B-Q4_K_S.gguf \
     | grep -E "general\.(architecture|name)|tokenizer\.(ggml\.model|chat_template)|(vocab|n_embd|n_layer|n_head)"
   ```
   这会直接暴露 `general.name` 和 architecture tag。把结果写进 §6.1，同时在 summary JSON 新增 `model.upstream_provenance` 字段。
2. **llama.cpp commit SHA**：在 `scripts/run_aligned_baselines.py` 和 `run_real_baseline.py` 入口处加：
   ```python
   llama_sha = subprocess.check_output(
       ["git", "-C", LLAMA_CPP_REPO, "rev-parse", "HEAD"]
   ).decode().strip()
   ```
   结果写进 `runtime.llama_cpp_commit`。

§13.1 第 23 行已经把这两项列为 "two reproducibility upgrades that remain"。**reviewer 对这一条的耐心是第二轮。下一轮如果仍然不补，会直接在 reproducibility 维度给出不可接受评级**，因为这一条的成本是**分钟级**，不是天级。

### M6. Table 4 信息密度不足，且无 per-case 展开

§8.4 第二段的 split claim 直接依赖 "NLS UTF-8 stalls on en_mid_01" / "NLS AEAD stalls on en_short_01 and en_mid_01" 这两条 per-case 陈述。但 Table 4 **只给 method-level aggregate**，没有 per-case 一行。结果：
- reviewer 无法从 Table 4 本身验证 "NLS AEAD stalls on 2/3 English cases" 这个数字；
- 三个 method × 6 case 的 18 cell SR pattern 信息量最丰富，却被压缩成 3 行 aggregate；
- `attempts_used` histogram 列完全缺失（见 M2）。

**Ask**：
- 在 Table 4 附近（或 appendix）增加一张 `tab:aligned-nls-slice-per-case` 展开表：6 行 × 3 列 SR（0/1 per cell），外加 per-cell encode/decode time 和 attempts_used。
- Table 4 原表增加 `attempts_used` 列（mean / max / histogram 任选）。
- §8.4 第二段的 case id 引用（`en_short_01` / `en_mid_01`）和展开表的列对齐，防止 reviewer 在 "stalls on the longest English case" 这句文字上反复跳转 JSONL 验证。

### M7. Figure 1 仍未升级，Figure 2 / retry histogram 仍未引入

Figure 1 (§4) 当前是 `\fbox{\parbox{0.96\linewidth}{...}}` 的纯文字流程框。在 ACM sigconf 双栏下，它**视觉上几乎等同于一段缩进段落**——reviewer 扫读时会直接跳过。encode path 的 "plaintext → UTF-8 bytes → packet → split → candidate + quantization + interval → cover" 这条流其实非常适合 TikZ 渲染。

Figure 2 迄今不存在。主 baseline 的 `attempts_used` histogram 信息（en `1:7, 2:1, 5:1`；zh `1:3, 2:2, 3:3, 5:1`）是论文**最操作可解释**的 signal，支撑 §7.9 的 "trivially separating" 结论，也是 M2 / M4 / M6 要求 attempt 数据暴露的根据。这条 signal 目前**只出现在 Table 3 的一个文字单元格里**，reviewer 扫读时很容易错过。

**Ask**：
- Figure 1 升级为 TikZ 两路 flow chart，encode / decode 双 row；
- 新增 Figure 2：per-language × per-method retry count histogram（stacked bar 或 CDF），从 `real-backend-baseline-summary-merged.json` + `aligned_baseline_runs.jsonl` 直接渲染，**零新实验成本**。

### M8. JSONL schema 不一致，full cover text 暴露策略不统一

- aligned slice 的 `aligned_baseline_runs.jsonl`（18 条）包含每条 run 的完整字段；论文 §5.8 第 107 行仍然写 "The current JSONL release logs metrics and metadata but not full cover strings"——这句话**对主 baseline 成立，对 aligned slice 可能不成立**，但论文没有区分。reviewer 需要跨两类 JSONL 验证同一 claim 的时候会混乱。
- `aligned_baseline_summary.json` 暴露 `passphrase_policy: "fixed local demo passphrase for aligned baseline comparison"`——这是诚实的，但**主 baseline 是否也是 fixed passphrase** 没有说明。如果主 baseline 也是固定 passphrase，那 salt + nonce 的 refresh policy 是否能触发、retry 行为如何解释，都需要在 §6 或 §8 里统一说明。

**Ask**：§5.8 / §8.3 结尾统一交代两个 JSONL schema 的差异；`real-backend-baseline-summary-merged.json` 在下一次 release 补齐 aligned slice 已有的字段（ghostext_git_head 之外还有 paper_git_head, passphrase_policy, per-run seed）。

---

## 4. Minor / Writing Issues

- **Abstract (main.tex 第 20 行)**：末句 "carrying AEAD packet bytes directly yields near-maximal payload-bit entropy yet still stalls without Ghostext's segment structure" 中的 "near-maximal" 对 non-specialist 模糊（对应 one_fraction=0.491, bit_entropy=1.000）。建议改成 "stalls on 2/6 cases in our six-case slice"，给具体数字锚点。
- **§1 第 16 行 contribution #3**：句尾加 "(six Qwen cases; see §8.4)" 明示 aligned slice 的 n=6 规模限制。
- **§5.7 第 90 行**：句首 "In adversarial settings, a party might search configuration variants that collide in 64 bits" 中的 "a party" 建议写成 "an adversary"；当前写法模糊了 threat role。
- **§5.8 Table 1 caption**：建议在 caption 下补一句 "The aligned-slice JSONL additionally logs full cover-token sequences; the main baseline JSONL records metrics and metadata only." 统一两类 artifact 的 transparency 说明。
- **§7.4 KL derivation**：虽然第 53 行已经把 $\widetilde{P}_t(v) > 0$ premise 前置到推导中段，但第一步 $\sum_v \widetilde{P}_t(v) \log(1 - \delta_t(v)/Q_t(v))$ 就应该限定 support。建议整段求和直接写成 $\sum_{v: \widetilde{P}_t(v) > 0}$，然后第 64 行的 "The $\widetilde{P}_t(v)=0$ terms contribute zero" 删除——减少 reader 的上下文跳跃。
- **§7.6 第 98 行**：$\mathrm{Adv}_{\mathrm{censor}}$ 首次出现但无 operational definition。建议公式前一行补：
  > "With $\mathrm{Adv}_{\mathrm{censor}} := |2\Pr[\text{correct}] - 1|$ for a binary hypothesis test between one sample from $Q_{1:T}$ and one from $P_{1:T}$,"
- **§8.3 Table 3 caption vs Table 4 caption 对齐**：Table 3 caption 写 "with per-cell uncertainty computed from the released JSONL logs"，Table 4 caption 没有。建议 Table 4 caption 补："CIs omitted at $n=6$ per method; see §3/M1 of evaluation discussion for sample-size caveat."
- **§8.4 Table 4 "Plaintext bits/token" 列**：Ghostext full 为 0.975 而 "Carried bits/token" 为 2.452，这两个数字之间的关系未在 caption 中说明。推测前者是 $8 B_i / T_i^{\text{all}}$（对应 §8.1 $\eta_{\text{all}}$），后者是 $8 B_i / T_i^{\text{pkt}}$（对应 $\eta_{\text{pkt}}$），但 NLS 单段 baseline 没有 "pkt vs all" 区分，所以 NLS UTF-8 的两列同为 2.487。**需要在 caption 显式给公式**，否则三行数字的可比性存疑。
- **§8.7 Stage 4.5**：描述 "initial slice released; detector-side rows, larger sample sizes, and direct OD-Stega comparison remain pending" 非常诚实。建议在 §8.4 末段也把这三项 remaining work 重复一次，而不是只留在 stage 状态表里——stage table 是 planning 附录，reviewer 扫读 §8.4 时未必跳过去。
- **§12.6 "Scope-Constrained Novelty Statement"**：第一段讲 "novelty at the systems-integration level"，第二段讲 "not a historical reproduction"。两段主题（novelty 是什么 / scope 是什么）相关但可以合并一段，减少重复措辞。
- **Appendix A Table 5**：每行 "Released evidence path or anchor" 列目前给目录级 anchor（`results/aligned-qwen-baselines/`）。双盲允许的前提下，建议细化到 script module path + function，例如 `scripts/run_aligned_baselines.py::run_case` + `scripts/merge_aligned_baselines.py::build_summary_md`——方便 reviewer 在 camera-ready 前后快速定位。
- **refs.bib / cite 覆盖**：§12.3 引用 `joulin2017fasttext` 和 `mitchell2023detectgpt`，但 §7.6 / §8 detector block 计划里没有 retry-feature trivially separating 的 cite（§7.9 自己导出了该结论，但缺乏 prior work 的 retry-count side-channel reference）。建议在 §7.9 加一个 side-channel attack on deterministic systems 的 classical cite（timing attack / retry analysis 方向）。

---

## 5. Reproducibility Assessment

**优点**：
- `results/aligned-qwen-baselines/aligned_baseline_summary.json` 暴露 `ghostext_git_head`, `paper_git_head`, `tokenizer_hash`, `backend_id`, `seed=7`, 完整 `candidate` policy, 完整 `codec` config。这是整个 artifact bundle 里 provenance 最全的一处。
- `aligned-qwen-baselines-reproduce.sh` 命令行参数与 `run_aligned_baselines.py` / `merge_aligned_baselines.py` 函数签名匹配；`real-backend-baseline-reproduce.sh` 同理覆盖主 baseline 两次 run。
- JSONL 行粒度适合 audit；`aligned_baseline_runs.jsonl` 18 行每行包含完整 encode / decode / attempts / timing 字段。

**仍未解决的短板**：
- **llama.cpp commit SHA 缺失**（所有 summary JSON 里只有 backend id 字符串，没有实际 llama.cpp build SHA）—— M5；
- **Qwen 上游 provenance 未 surface**—— M5；
- **主 baseline JSONL 是否含完整 cover text 未明示** —— M8；
- **硬件环境**：summary JSON 里只有 `platform: Linux-6.6.87.2-microsoft-standard-WSL2` + `host: kzoacn-PC`，没有 CPU model / RAM / llama.cpp 编译 flag。论文 §7.13 承认 "cross-hardware determinism is not yet established"，但 artifact 也没有记录当前 hardware 的足够 fingerprint 供未来对比；
- **`passphrase_policy` 主 baseline 未暴露**：如果主 baseline 和 aligned slice 都用 "fixed local demo passphrase"，retry 行为的可解释性会受影响（固定 passphrase 下 salt refresh 仍然是随机的，nonce 也仍然是 per-attempt 独立；但如果这两个也固定了，retry 会陷入死循环，论文需要说明实际 policy）；
- **Seed 暴露不一致**：aligned slice 写 `seed: 7`，主 baseline JSONL 是否包含 seed 未在文中说明。

---

## 6. Recommended Actions (按 reviewer 实际权重排序)

1. **$h_{\min} \in \{0.0, 0.5, 1.0\}$ sweep**（M3）—— 最 cheap、最 high-value、且论文自己已经承诺；约 60–90 分钟 wall-clock；Table 2 同时呈现三个工作点，abstract headline 数字同步更新。
2. **Qwen provenance + llama.cpp commit SHA**（M5）—— 分钟级工作量，第三轮不应再欠。
3. **Minimal detector evaluation**（M4）：retry-feature trivially separating AUC + fastText binary AUC + $\widehat{B}_{\mathrm{TV}}$ histogram。合并在同一批 cover 上跑一次。< 4 小时。
4. **扩样**（M1）—— 三选一：主 baseline 扩到 n ≥ 100 / aligned slice 每 method n ≥ 30 / 重新定位为 short paper。
5. **澄清 encode median 差异 + 补 attempts_used 列**（M2 + M6）—— presentation-only，零新实验成本。
6. **Figure 2 (retry histogram) + Figure 1 升级为 TikZ**（M7）—— 2 小时 presentation 工作。
7. **Table 4 per-case 展开表 + caption 公式标注**（M6 + 4. minor）。
8. **KL derivation premise 完全前置 + $\mathrm{Adv}_{\mathrm{censor}}$ operational definition**（M7 minor, §7.4 / §7.6）—— 行内顺序微调。
9. **JSONL schema 统一说明**（M8）—— §5.8 / §8.3 两处补一句。
10. **Appendix A Table 5 evidence anchor 升级到 module::function 级**。

---

## 7. Overall Assessment

**Strengths summary**：
- 协议层写法成熟、approximation bound 推导严格；
- Scope discipline 是本版最大优点——abstract / §1 / §7.6 / §12.6 / §13.1 全程自我降权，不用它没有的证据说话；
- Artifact 纪律延续；aligned slice 的 summary.json 字段最完整。

**Weaknesses summary**：
- Empirical core 只有 n=18 主基线 + n=6 aligned slice，都不足以支撑 inferential claim；
- 论文自己承诺的实验（$h_{\min}$ sweep / detector AUC / $\widehat{B}_{\mathrm{TV}}$ correlation / retry trivially separating）在投稿时点**全部未兑现**；
- Reproducibility metadata 两项 trivial fix 跨轮未补。

**Venue-fit 判断**：

| 目标场景 | 结论 |
|---|---|
| Security 顶会（S&P / USENIX / CCS） | **不够**：aligned slice n=6 远不足以支撑 systems-integration novelty claim；detector-side 全空白 |
| ML 顶会（NeurIPS / ICLR / ACL） | **不够**：$h_{\min}$ sweep 缺席，bits/token headline 仍在最激进 operating point；缺 detector AUC |
| Security / IH 相关 workshop（WOOT / IH&MMSec / ACSAC workshop） | **接近可接受**，需要至少补 M3 + M5；补完后作为 "protocol engineering + narrow aligned-comparison" 可尝试 |
| Short paper / poster / demo track | **本版可直接投**：narrative corridor 干净、aligned slice 支撑 split claim、artifact 可复现。M5 是 short paper reviewer 最先抓的一条，必须先补 |

**Bottom line**：本版是一个**诚实的、scope-disciplined、但 empirical 厚度不足的**系统论文 draft。在 main venue 的接收门槛下，**推到 Borderline Accept 的最短路径是 M3 ($h_{\min}$ sweep) + M4 minimal (retry AUC + fastText AUC + $\widehat{B}_{\mathrm{TV}}$ histogram) + M5 (provenance fix) + M7 (Figure 2) 四项一起补**，总工作量估计 < 1.5 个工作日。

**推荐措辞**：
- 若作者下一轮补齐上述四项 → **Borderline Accept** (workshop) / **Weak Accept** (full paper with extended slice n ≥ 30)；
- 若只补 M3 + M5（最便宜的两项）→ **Borderline Reject** (short paper OK, full paper 仍不足)；
- 若只补措辞不补实验 → **Reject**，理由：staged-protocol promise 的兑现率过低，reviewer 无法评估剩余阶段的可兑现性。

**Confidence**: 3/5（协议工程、approximation bound、Cachin/Pinsker bridge、aligned slice 数据解读有把握；detector-side 效果因论文未提交实测数据无法深判；encode median 37% gap 未经作者澄清，本 reviewer 只能给出归因假设）。
