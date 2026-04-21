# Review: Ghostext — Toward Almost-Perfect LLM Steganography with a Deterministic, Fail-Closed Protocol and Measurable Approximation Bounds

**Reviewer:** Anonymous · **Date:** 2026-04-21 · **Recommendation:** Weak Reject — Major Revision（比上一轮进步明显；核心证据链仍不足以匹配"toward almost-perfect"的标题，但措辞诚实度已显著提升）

---

## 1. Summary

相对上一轮草稿，本版做了两件重要事情：

1. **Scope 下调**：摘要、引言 §1、威胁模型 §3、评估计划 §8、局限 §13 口径统一，明确把当前证据限定为"18 条 template-known pilot baseline = operational floor"，并主动标注 `Wilson 95% CI [0.824, 1.000]`；同时新增了 threat-capability matrix（Table 1）和 language-stratified bootstrap CI（Table 3）。
2. **技术内容**：协议层（packet = salt ∥ nonce ∥ sealed\_header ∥ body\_nonce ∥ body\_ct，scrypt + HKDF-SHA256 + ChaCha20-Poly1305）、近似误差分解（$\mathrm{TV}(Q'_t,P_t) \le \alpha_t + N_t/(2F_{\mathrm{tot}}) + \beta_t$）、KL 上界（$\le N_t/F_{\mathrm{tot}}$ nats）、fingerprint 碰撞讨论、retry 流量泄露 marginal 模型、$\widehat{B}_{\mathrm{TV}}$ 作为 audit signal 而非 detector guarantee 的定位—— 这些内容都比上一版更加克制、更加 implementation-aligned。

但是，**实验体量（n=18）、detector-side 证据（零）、NLS/OD-Stega 对齐对照（零）、$h_{\min}$ 扫描（零）这四条结构性缺陷并未改变**。只是把"未测"公开写进了 limitations 和 staged protocol 里。

## 2. Strengths（本版维持或新增）

1. **措辞一致性大幅提升**：Abstract → §1 "Scope boundary" → §3.6 "Security Objective" → §7.1 "Scope and Goal" → §13.1 Limitations 的措辞相互锁定，没有内部矛盾。这是上一轮被批评的标题/内容错配问题的实质性修正（虽仍不彻底，见 M1）。
2. **Threat capability matrix（Table 1）**是新增亮点：把 "in scope / measured axis / out of scope" 三类清晰列出，主动把 active text modification、runtime compromise 划出界外，避免读者误读。
3. **近似误差分解**依旧是全文最扎实的一块：每一项都对应 runtime 可 log 字段（logging schema Table §7.12），chain decomposition 诚实承认"tight analytic bound is difficult without stronger assumptions"。
4. **Bootstrap CI 的 per-cell 报告**（Table 3 en/zh 分别给出 encode/decode median 的 95% 区间以及 `attempts_used` histogram）在 n=9 的情况下已经是合理的统计呈现方式。相较上一版只报点估计是明显进步。
5. **Retry side-channel 的讨论更诚实**：§7.9 明确写出 `attempts_used` mean=1.944、max=5、en 主要 single-attempt (7/9)、zh 分散 (1:3, 2:2, 3:3, 5:1)，并指出 "a natural-cover generator without a retry loop has degenerate R=1"——这是对上一轮 M7 的直接回应，虽然仍未给出实测对照（见 M6）。
6. **Fail-closed failure taxonomy（6 类）**被明确引入 §4.5 和 §6.2，并在 evaluation protocol §8.8 作为分析单元，这种 "failure classes = analysis unit" 的工程纪律在 NLS 后继工作里少见。
7. **$\widehat{B}_{\mathrm{TV}}$ 的定位**更加谨慎：§7.6 明确说 "large value is direct evidence ... small value is only suggestive"，并把 detector correlation analysis 列为 required output 而非可选附录。这是上一版 M4 的部分回应。
8. **Artifact 纪律**延续：`results/real-backend-baseline-{r1,r2,summary-merged.{json,md}}` + `reproduce.sh` 已发布；`scripts/merge_real_backend_baseline.py` 被新增到仓库，支持从 raw JSONL 重算 merged summary。

## 3. Major Concerns

### M1. 标题仍越位，尽管"Toward"做了软化

当前标题：
> **Ghostext: Toward Almost-Perfect LLM Steganography with a Deterministic, Fail-Closed Protocol and Measurable Approximation Bounds**

"Toward almost-perfect" 比上一版的 "an almost perfect steganography"（且拼写错误）有改进，但在安全/ML 顶会审稿语境下，**"almost-perfect" 仍然会被读成暗示接近 provably-secure / distribution-matching**。然而正文多处明确否认：
- 摘要："toward almost-perfect distribution preservation, but the present contribution is narrower..."
- §7.7："The present paper does not claim that current finite-precision, truncated, stability-filtered operation already satisfies a full provable-security theorem."
- §13.1："not yet provide full empirical detector-resistance evidence."

建议要么把标题改为完全 descriptive 的形式（例如 "**A Deterministic, Fail-Closed LLM Steganography Protocol with Implementation-Aligned Approximation Bounds**"），要么**先把 detector-facing Stage 5 跑完再投**。现在的标题在送审阶段极易因"overclaim"被 desk-reject。

### M2. 样本量依然 n=18，统计叙述与实验规模之间仍有明显落差

- `p99 encode=215.40 s` 和 `p99 decode=63.92 s` 在 n=18 里本质上就是"第 17/18 个样本"，作者在 §8.3 自己也写了 "should be read as descriptive order statistics rather than stable tail estimates"——但仍出现在主结果表（Table 2）里作为 headline。要么降级到 Appendix，要么补数据；此外 "p99 driven by two five-attempt runs" 的说法已经暗示 tail 估计不稳定。
- `SR = 18/18` 的 Wilson 95% CI [0.824, 1.000]：下界 0.824 离 "operationally reliable" 的叙事有较大距离。即便所有 18 条都成功，仍无法在统计上排除 "真实 SR ≈ 0.83" 的世界。建议要么扩到 ≥100 条（Wilson 下界就能推到 0.97 左右），要么在 headline 直接写 "lower bound 82.4%"。
- Table 3 的 per-cell Wilson CI 都是 [0.701, 1.000]，这个区间在 n=9 下已经毫无统计判别力——此处的语言分层分析的主要价值是**暴露 `attempts_used` 分布的 en/zh 差异（7:1:1 vs 3:2:3:1）**，不是 SR 比较。建议 §8.3 明确讲清这点。
- 建议最低配置：prompt family × language × message length = 3 × 2 × 3 = 18 cells × 30 trials = 540 条；如果无法达到，则论文定位要**更进一步**降级（例如加上 "feasibility report" 副标题，或改投 systems track/workshop）。

### M3. NLS / OD-Stega 对齐比较仍缺席——本文最关键的 missing piece

§8.9 和 §12.4 都明确承认这是 explicit gap。但 Ghostext 的 novelty claim 是 "systems-security engineering over the same AC-style mechanism"（§12.5），那就**必须**证明:

1. 这些额外机制（fingerprint check + stability filter + fail-closed retry + packet framing）不会显著牺牲 bits/token 和延迟；
2. 如果确实牺牲，要说明牺牲换来什么可测的安全/可靠性收益。

现在 §8.9 的承诺是"post-pause first comparison table"，但在本文里既没有数据也没有初步插值估计。建议至少做一个 single-condition（同 model、同 prompt、同 message 集）对比，哪怕只 n=30 也比完全没有强。否则审稿人无法评估 Ghostext 相对 NLS 的 **marginal cost/benefit**。

### M4. $h_{\min}=0.0$ 下的 `bits/token = 2.478` 仍是主结果数字，存在误导风险

实现默认 $h_{\min}=1.0$ bit，但 baseline 跑 $h_{\min}=0.0$，`bits/token = 2.478`。§7.5 和 §13.1 都承认这是"ungated initial operating point, not ... recommended deployment default"。但：

- 它仍然出现在 Table 2 和摘要的暗示中；
- 低熵步强行嵌入是 distinguishing 最明显的工作点——这恰恰是 detector 最容易抓的位置；
- 论文承诺的 "planned $h_{\min}$ sweep over \{0.0, 0.5, 1.0\}" 尚未执行。

建议：在 Table 2 为 bits/token 行加一个**显式警示列/脚注**（"at $h_{\min}=0.0$; default deployment uses $h_{\min}=1.0$"），并在 §8.5 给出已规划的 sweep 时间线。

### M5. Retry traffic leakage 的观察没有转化为"对比实验"

§7.9 给出的是全概率 mixture 公式 $\Pr[L=\ell] = \sum_r \Pr[R=r]\Pr[L=\ell \mid R=r]$ 和 release 的 `attempts_used` 直方图。但是:

- 一个 natural LLM cover 生成器的 `R=1` 是**平凡的**——这意味着 stego 和 cover 的 retry-count 分布是 **perfectly separable**（stego 有 R>1 的质量 8/18 ≈ 44%；cover 全部 R=1）；
- 这不需要等到 Stage 6 才能报——它直接从当前 pilot 数据里读出；
- 建议在 §7.9 加一小段："under the current retry policy, the retry-count distribution alone is a trivially separating signal against any zero-retry natural-cover baseline; this motivates either (a) matching the cover generator's retry budget, or (b) hiding retry through deterministic policy tuning"。

### M6. Fingerprint 64-bit 的 adversarial 面仍未量化

§5.7 / §7.8 都承认 64-bit 是 deployment tradeoff，未来推荐 128-bit。但在当前版本：

- 只给了 honest collision bound $\approx n(n-1)/2^{65}$；
- 对 adaptive adversary 枚举 runtime 变体的场景只讲 "degrade diagnostic clarity"，没给出量化（例如给定 censor 算力 $2^{40}$ 时，碰撞概率 ≈ $2^{40}/2^{64} = 2^{-24}$，是否可忽略？）；
- 在 multi-session 下，"match 与否"的信号本身可能成为 side channel，没有讨论。

建议或者在 §7.8 给出 adversarial justification，或者在下一版默认升级到 128-bit 并保留 64-bit 作为兼容性 option。

### M7. 近似 bound 到 censor advantage 的形式化桥梁尚未落实

§7.6 写到 "in standard steganographic formulations this upper-bounds idealized detector advantage"，并引用 Cachin (1998) + Hopper et al. (2002) + Pinsker。但**没有给出一个显式的引理或公式**把 $\mathrm{TV}(Q_{1:T}, P_{1:T})$ 翻译成 censor advantage。这在该领域是已知标准结果（Cachin: $\mathrm{adv}_{\mathrm{censor}} \le \sqrt{D_{\mathrm{KL}}/2}$ by Pinsker），补一行正式陈述并不困难，但能让读者把近似 bound 直接挂到 security semantic 上。目前版本在 §7 和 §13 反复说"Bhat_TV is audit signal not guarantee"，但从未把**理想情况下它应该链接到什么**写清楚。

### M8. 孤立章节文件（09/10/11）仍在 `paper/sections/` 但未被 `main.tex` include

查 `paper/main.tex` 第 25-34 行，当前 include 的是 01–08、12、13、appendix-a。而 `sections/09-operational-walkthrough.tex`、`10-design-tradeoffs.tex`、`11-experiment-blueprint.tex` 仍留在目录里但不再被编译。这会造成两种风险:

- 如果内容已合并进 §4.3/§10 等其他节，应**删除孤立文件**避免版本控制混乱；
- 如果是本意保留但暂缓编译，应在 `main.tex` 注释说明，或者把内容移到 `drafts/` 或类似目录。

目前 git status 也显示这三个文件没有 `M` 标记，等于是被冻结的 dead code。建议本轮 cleanup。

## 4. Minor / Writing Issues

- **模型命名**：§6.1 "Qwen/Qwen3.5-2B" 仍是 artifact label。Qwen 官方没有 "Qwen3.5-2B" 这个 release。论文自己脚注说 "We therefore treat `Qwen/Qwen3.5-2B` as a reproduction label for the released artifact, not as evidence that this string is the canonical upstream model-family tag"——这等于在 reproducibility 上打问号。建议要么改标签（确认是 Qwen2.5-1.5B / Qwen3-1.7B 等哪个），要么把正式 model provenance 补入 §6.1 作为 "Reproducibility upgrade (completed)" 而非继续 pending。Bibliography / 论文里混用 "Qwen3.5-2B" 会让任何严肃审稿人质疑。
- **`huang2026odstega` 年份**：refs.bib 标注 2026。若为 EACL 2026 已接收 / 已发表，请确认卷页信息稳定；若仍是预印本，年份应跟 ACL Anthology 最终记录一致（目前 2026-04，边界情况）。
- **Cross-reference**：§5.2 引用 "Section~\ref{sec:analysis}"、§7.3 引用 "Section~\ref{sec:protocol-details}"——OK。但 §7 自身开头引用 "Section~5 bound"（§10.3，如果含的话）需复检一致性（尤其 §10 被 drop 的情况下）。
- **Table 2 caption**：`real-backend pilot results (r1+r2, template-known baseline, n=18)`，建议把 `policy: top_p=0.995, max_k=64, h_min=0.0, F_tot=4096` 直接写进 caption 以提升可读性（现在读者要去 §8.1 末段找）。
- **§4.4 Natural Tail**："Tail tokens do not carry payload and are ignored by the decoder after packet recovery" + "its role is limited to output completion rather than a separate distribution-matching defense"——这段关键定位建议在 Abstract 或 §1 的 contribution list 也写一句，否则容易被读成"tail 也是一种隐蔽手段"。
- **§7.4 KL derivation**：$u = \delta_t(v) / Q_t(v) < 1$ 的边界情形（$\delta_t(v) = 1/F_{\mathrm{tot}}, Q_t(v) = 1/F_{\mathrm{tot}}$ 时 $u=1$，$-\log(1-u) = \infty$）应显式说明："terms with $\widetilde{P}_t(v) = 0$ contribute zero to the KL sum and can be dropped"这句已写在下一段，但应当**先排除再引入泰勒不等式**，否则中间步骤看起来未定义。
- **Abstract 里的 `$\widehat{B}_{\mathrm{TV}}$`**：首次出现且没定义。建议在 Abstract 里用 natural language（"an implementation-side TV-style audit diagnostic"）替代，数学符号放到 §7 首次使用。
- **Appendix A (Table 5) claim-to-evidence**：每个 claim 只给"test group"label，没有具体 test 文件路径/函数名。在 double-blind 阶段可以理解，但**reproduce 后作者版**应补全文件级映射。
- **Bibliography 分簇**：§12.3 watermark+detector 小节建议保留 subsection 结构，但把 fastText+DetectGPT 两条 citation 的 motivation 一并解释（目前只给了 "references motivate our detector-block design"，略空）。
- **`.gitignore`**：git status 显示 `M .gitignore` 但没说明改了什么；建议 commit message 里说明，避免审稿人困惑。
- **标题中 `Fail-Closed Protocol and Measurable Approximation Bounds`** 的 "measurable" 一词选得好，它暗示 "implementation-aligned"；建议把该措辞也引入 Abstract 首句替换当前 "authenticated encryption with arithmetic-coding-style..."（当前 Abstract 首句太技术，埋没了该论文的工程定位）。

## 5. Reproducibility

优点：
- 核心 artifact `results/real-backend-baseline-{r1,r2,summary-merged.{json,md}}` + `reproduce.sh` + `scripts/merge_real_backend_baseline.py` 齐备；
- Appendix A 有模块级 claim-to-evidence condensed 表；
- `summary-merged.md` 明确 pin 了 `top_p=0.995, max_k=64, h_min=0.0, F_tot=4096`。

缺点：
- `llama.cpp commit SHA` 仍未 surface 到 summary bundle（§6.1 自己承认）；
- `Qwen/Qwen3.5-2B` label 与上游 provenance 的断联（同上）；
- JSONL 仍**不含完整 cover string**（§5.8 确认），这是 detector evaluation 无法从发布 artifact 直接启动的瓶颈；
- 硬件/OS/runtime 环境（CPU model、llama.cpp 编译 flag）在 summary 里是否完整记录，需要在 README 里 spell out。

## 6. Recommended Actions（按优先级）

1. **改标题**（去掉 "Toward Almost-Perfect" 或至少把它移到 subtitle，并对 abstract 首句做同方向调整）。
2. **放大 pilot**：至少 3 prompt family × 2 language × 3 message length × 30 trials，报 per-cell Wilson / bootstrap CI；降级 p99 到 appendix 或补足样本量。
3. **补 NLS & OD-Stega 对齐对照表**（哪怕 single-condition n=30），即便 Ghostext 略输也要报。
4. **补 $h_{\min} \in \{0.0, 0.5, 1.0\}$ 扫描**，重报 bits/token 和 failure composition；Table 2 加脚注显式警示。
5. **补 retry-count 对比段落**：stego (8/18 有重试) vs. natural-cover (平凡 R=1) 的 trivially separating 结果直接写进 §7.9。
6. **Stage 5 single-message detector AUC 最低配置**（fastText + DetectGPT + 一个 LLM judge），即便 AUC 很高也报——这是 "detector-facing claims remain pending" 的最低 pension。
7. **Fingerprint**：要么默认升到 128-bit，要么在 §7.8 给出量化 adversarial justification。
8. **Model provenance**：确认 "Qwen/Qwen3.5-2B" 对应的 canonical upstream 标签，把 llama.cpp commit SHA 加入 merged summary。
9. **清理 orphaned sections 09/10/11**：要么 re-include 要么删除，不要留在仓库里。
10. **近似 bound → censor advantage 的桥梁**：§7.6 末补一行 Cachin / Pinsker 形式化陈述，让读者明确什么情况下 $\widehat{B}_{\mathrm{TV}}$ 小会翻译为 detector 难。

## 7. Overall Assessment

本版对上一版提出的结构性批评做了**措辞层面**的彻底响应：
- 标题软化为 "Toward"；
- Abstract / §1 / §3 / §7 / §8 / §13 的 scope 口径锁定一致；
- Per-cell bootstrap CI、Wilson CI、retry histogram、failure taxonomy、logging schema 均已到位；
- $\widehat{B}_{\mathrm{TV}}$ 从 "diagnostic that suggests detector-safety" 降为 "audit signal that requires detector-side validation"。

但**实验侧的 4 条结构性缺陷几乎未动**：
- n=18 未扩；
- NLS/OD-Stega 对齐比较缺席；
- $h_{\min}$ sweep 缺席；
- detector-side evidence 为零。

这使得本文在**写作诚实度**上已达到或超过同领域平均水位，但在**证据密度**上仍停留在 "feasibility pilot" 阶段。在现状下：

- 投**安全/ML 顶会**（S&P, USENIX Security, CCS, NeurIPS, ICLR）：不够，至少需要跑完 Stage 3–6 再论；
- 投**systems track / workshop**（例如 NDSS workshop、ACM Multimedia Security & Multimedia workshop、ACM IH&MMSec）：在补齐 M1/M2/M3/M4 后**可接收**，定位为"protocol engineering + measurable approximation framework + release-quality baseline artifact"会更合适；
- 投**short paper / poster**（例如 ACSAC poster、USENIX WOOT）：当前材料已基本 ready。

如果作者决定坚持 full paper 路线，**优先级最高的是 M3（NLS 对齐对比）**——它能把"systems-integration claim"从口头变成可检验的结论；其次 M2（扩样本量）+ M4（h_min sweep），这两项技术上在现有 pipeline 上几乎没有阻力；最后才是 M7（detector-side），需要较大投入。

**Confidence:** 3/5（协议工程与近似分析有把握；detector-side 细节因论文未涉，无法深判）。

---

## Revision Delta vs. Previous Review（2026-04-17 版）

| 上一版 concern | 本版状态 |
|---|---|
| 标题"almost perfect"越位 + 拼写错误 | 已改为 "Toward Almost-Perfect ..."，拼写已修；但核心 overclaim 风险仍在（M1） |
| n=18 p99 不稳定 | 已在 §8.3 文本中明确 caveat；但 headline 表 2 未降级（M2） |
| 缺 NLS/OD-Stega 对齐对照 | 仍缺；在 §8.9 / §12.4 明确列为 pending（M3） |
| 近似 bound → security 桥梁缺失 | $\widehat{B}_{\mathrm{TV}}$ 定位大幅收敛；正式桥梁仍缺一行（M7） |
| Fingerprint 64-bit 对抗面分析不足 | 保持原状；128-bit 建议仅作 future direction（M6） |
| $h_{\min}=0.0$ 的 bits/token 高估 | 已补 caveat；sweep 未跑（M4） |
| Retry traffic leakage 无实测 | 数据已报，对比实验仍缺（M5） |
| 标题 Qwen 版本号 | 未改；§6.1 以"reproduction label"防御，但 provenance 仍未 surface |
| Cross-reference / tailing bugs | 部分修；orphaned sections 09/10/11 新问题（M8） |

结论：**进步是 substantial 的，但仍是 writing-level 的进步；下一轮必须推进 experiment-level**。
