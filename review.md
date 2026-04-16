# Review: Ghostext — Practical LLM-Based Linguistic Steganography with Deterministic Decoding

**Reviewer:** Anonymous
**Date:** 2026-04-17
**Recommendation:** Weak Reject (major revision needed before acceptance)

## 1. Summary

作者提出 Ghostext,一个基于算术编码风格区间划分、结合认证加密分组(ChaCha20-Poly1305 + scrypt + HKDF)的 LLM 语言隐写系统。核心卖点是**工程可复现性与确定性解码**:通过配置指纹绑定、retokenization 稳定性过滤、两段式(bootstrap/body)嵌入和 fail-closed 失败分类,保证在匹配配置下的同步解码。论文给出了截断、量化、稳定性过滤三项近似误差的 TV / KL 上界,并在 18 次真实后端(llama.cpp + Qwen)试验中报告了 100% 解码成功率、2.478 平均 bits/token 和延迟分布。

## 2. Strengths

1. **工程纪律严谨。** 协议层描述具体到可审计的粒度(packet 格式、指纹字段、失败类别枚举),且主张与证据的对齐贯穿全文——例如第 13 节显式给出"evidence upgrade criteria",罕见于本领域的系统工程论文。
2. **近似误差分解清晰。** §5.6 的三项 TV 上界 `TV(Q'_t,P_t) ≤ α_t + N_t/(2F_tot) + β_t` 将截断、量化、稳定性过滤分离,每项均可从运行日志实测;§7 的 KL 上界 `D_KL(P̃_t‖Q_t) ≤ N_t/F_tot` 简洁且实现对齐。这种"每个误差源都有一个可测量的名字"的做法对同领域后续工作有参考价值。
3. **失败语义被当作一等公民。** 失败分类(integrity / config mismatch / sync mismatch / unstable-tokenization / low-entropy / token-budget)配合两段式认证,对部署侧调试和后续评测分类非常有用。
4. **Artifact 规范化程度高。** 已释出 r1/r2 原始 JSONL 日志、复现脚本、合并摘要,git HEAD、tokenizer hash、种子、策略参数均归档。

## 3. Major Concerns

### 3.1 核心卖点(不可检测性)完全未评测
论文题目中的"steganography"意味着对抗隐写分析,但 Q5(detector-facing)与 Q4(approximation term 实证)均标记为 pending。当前仅有 Q1–Q3(recoverability / runtime / efficiency),而这三项本质上只验证了"确定性编解码的工程正确性"。没有任何分类器、LLM-judge、KL/TV 实测或多样本累积检测结果。这使得论文当前证据能支撑的**最大主张**仅是"一个可复现的基于 AEAD 的可逆编码管线",而不是"隐写方案"。我认为这是当前阻止发表的首要问题——作者自己在 §3.6 与 §13 承认"detector-evasion claims remain pending",但这恰好是审稿人最需要看到的那部分。

### 3.2 样本量过小,且 Chinese 评测似乎是拼音而非中文
18 次试验(9 en + 9 zh)对任何分布性结论都不足。更关键的是:§5.8 Table 2 的 Chinese 例子 `Jin wan qi dian zai lao di fang jian` 是**拼音**而非汉字;real-backend-baseline 的摘要中 zh 的 bits/token 也明显偏低(2.370 vs 2.586)。如果"zh"条件的秘密消息/cover 均为 ASCII 拼音,它并不构成"bilingual evaluation",应明确澄清;若实际确为汉字,Table 2 的展示具有误导性。请提供至少一条真正以 CJK 汉字作为 cover 的完整三元组。

### 3.3 文中配置与实测配置不一致
- 论文 §5.3 声明 `F_tot` 默认为 **65536**,但 `results/real-backend-baseline-summary-merged.md` 里 `total_frequency: 4096`;
- §7.5 声明 `h_min = 1.0 bit`,但实测中 `min_entropy_bits: 0.0`;
- §7.4 给出的"16 个候选、F_tot=65536"数值示例(`2.44×10⁻⁴` nats)在实测配置下量级完全不同。
这些不一致直接削弱了"implementation-aligned bound"的主张,请统一文本默认值与实际运行配置,或明确区分"论文展示用默认"与"基线实验用配置"并给出各自理由。

### 3.4 novelty 定位偏弱,缺少与 NLS/OD-Stega 的数值对比
§12 将贡献定位在"systems-integration level",但全文未给出任何与 NLS [Ziegler 2019] 或 OD-Stega [Huang 2026] 在**相同模型、相同消息、相同度量**下的 bits/token、延迟、可检测性对比。没有对照的工程论文很难让读者判断权衡是否值得。至少应补充一张"Ghostext vs NLS (deterministic replay off / on)"的表格。

### 3.5 重试机制与同步一致性未讲透
§4.3 说"retries are enabled only when packet salt or nonce can be refreshed";但 salt 进入 scrypt,nonce 进入 AEAD,刷新后新密文完全不同。这意味着:
- 发送方重试产生的 cover text 是最后一次成功尝试的 token 序列;
- 接收方并不知道发送方经历了多少次重试。
那么 §7.10 中"Pr[R=r] 造成的长度/延迟混合分布"就是**仅发送侧可见的变量**;接收端同步不涉及 r。请在 §4 显式说明这一点,否则读者容易误以为 r 影响解码重放。

另外 `attempts_used: mean=1.944, max=5` 意味着平均有近一半的 cover 在被完全生成后被丢弃,这本身是一个值得讨论的 **效率 / 侧信道** 话题(能耗、对"为什么一次对话显著慢于平均"的解释),当前只做定性提及。

### 3.6 延迟过高,工程可用性边界不清
p99 encode 215 s,p99 decode 64 s,在 Qwen-3.5-2B(注:正文/摘要均写作 `Qwen3.5-2B`,但截至 2026 年 Qwen 官方无 3.5 命名的 2B 模型,疑为 `Qwen2.5-2B` 的笔误,请核对)。在什么场景下可接受 200+ s 的单消息编码?论文未给出目标带宽/可用性边界,使得"practical"这个标题修饰显得不够扎实。

### 3.7 Natural Tail 的叙述与实现有矛盾
§4.4 与 §7.14 承认 natural tail **仍然走受限候选采样器**,因此并不能解决"表面流畅性与嵌入段分布相同"这一问题。在这个前提下,natural tail 相较于直接截断到 packet 边界几乎**没有观察上的区分度**,应考虑删除该特性,或明确说明"本版本中 natural tail 的唯一作用是把输出补到一个句法边界"。现在的表述容易让读者高估其作用。

### 3.8 64-bit 配置指纹分析浅
§5.7 给 `n=10^6` 时的 `~2.7×10⁻⁸`,但没有说明:
- 指纹的底层哈希是什么(SHA-256 截断?BLAKE?),
- 截断前多少 bit 参与,
- 为何选 64 bit 而非 128 bit(节省 8 字节 header 在一个以百 token 计的 cover 中几乎无意义),
- 在 §7.8 提到的"adversarial 64-bit 碰撞搜索"下,对抗者需要 ~2^32 次尝试,这对攻击者是否可行?
建议升级到 128 bit 或显式论证 64 bit 足够。

## 4. Minor Issues

- `main.tex` 只 include 了 §§1–8, 12, 13 与附录,但仓库中还有 09-operational-walkthrough、10-design-tradeoffs、11-experiment-blueprint 三节。这些内容与 §4/§7/§8 高度重复,作者需决定要么合并、要么恢复;当前仓库/PDF 不一致不利于审阅。
- §7.4 推导 `D_KL ≤ N_t/F_tot`:`∑ δ_t(v)²/Q_t(v) ≤ ∑ (1/F_tot)²/(1/F_tot) = N_t/F_tot` 的第二个不等号需要 `Q_t(v) ≥ 1/F_tot`,已说明(每个候选至少分配 1 单位频率),但 `δ_t(v)²/Q_t(v)` 的上界应更紧;此外开头用 `log(1+x) ≤ x` 得到的是 `D_KL(P̃‖Q) ≤ ∑ δ²/Q`,缺一步推导(通常要引用 Pinsker 或做 Taylor),请补全。
- §3 威胁模型 Table 1 将"active text modification in transit"列为 out-of-scope,但 §12 Related Work 与 §13 都再次讨论 robustness 作为未来工作。建议统一口径:要么移入 pending 评测轴,要么正文也一致标 out-of-scope。
- 图 §4 的 `\Description` 写得很认真(accessibility 友好),值得保留。
- `refs.bib` 中 `huang2026odstega` 请确认引用年份与会议信息(2026 之内应当可以确认)。
- Abstract 中"formalized bounds"在 §5–§7 出现,但正文的 `\widehat{B}_{TV}` 目前只是定义,没有任何实测数,应明确标注为"diagnostic defined, measurement pending"。

## 5. Questions for Authors

1. 当重试刷新 salt/nonce 时,接收端是否完全对 `r` 不可见?这是否意味着在"salt/nonce 固定"的子模式下,`attempts_used > 1` 会直接导致 decode 失败?
2. 18-trial 基线的 `attempts_used mean ≈ 1.94` 含义是什么——发送端每条消息平均丢弃了约一条 cover?如果是,请在延迟表中区分"单次尝试耗时"与"总耗时"。
3. 为什么配置指纹选择 64 bit 而非 128 bit?在你们的部署场景下 8 字节是关键开销吗?
4. Q4 与 Q5 的时间表?如果 3 个月内能补上 detector suite(fastText / DetectGPT / 一个 LLM-judge)的单样本和多样本累积曲线,这篇论文的可接受性会显著提升。
5. 有无对 NLS / OD-Stega 的直接数值对比?同模型同消息同策略下的 bits/token 与检测 AUC。

## 6. Overall Assessment

作者在**工程纪律与可复现性**上达到了很高的标准,论文文本的克制也值得称道。然而,作为一篇宣称"practical LLM-based steganography"的论文,当前证据仅支撑"确定性编解码 + 认证分组"这一半,而另一半(**隐写本质**即不可检测性)完全缺席;加上样本量偏小、文中配置与实测不一致、Chinese 评测疑似使用拼音、缺少与 NLS/OD-Stega 的直接对比,我认为当前版本不适合直接接收。

如果作者在下一轮能补齐:(a) Q4 近似项实测分解;(b) Q5 至少单消息 + $m\in\{1,8,32\}$ 多样本累积检测曲线;(c) 配置统一;(d) 与 NLS 的数值对比;(e) 真正使用 CJK 汉字的 zh 条件——我会倾向于 Weak Accept。

---
*End of review.*
