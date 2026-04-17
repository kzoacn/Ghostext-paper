# Review: Ghostext — An Almost Perfect Steganography via LLM and Arithmetic Coding

**Reviewer:** Anonymous · **Date:** 2026-04-17 · **Recommendation:** Weak Reject (major revision needed before a top-tier security/ML venue; borderline acceptable at a systems/workshop venue)

---

## 1. Summary

Ghostext 提出一个基于大语言模型 next-token 分布 + 算术编码式区间收缩的生成式文本隐写系统，核心贡献在于**工程/协议层**：
- 基于 scrypt + HKDF + ChaCha20-Poly1305 的 authenticated packet framing；
- 发送-接收双方通过 64-bit 配置 fingerprint 做确定性同步；
- bootstrap/body 两阶段嵌入 + fail-closed 失败语义（带显式失败类别）；
- retokenization-stability filtering，降低 render/re-tokenize 往返不一致的风险；
- 给出 truncation / quantization / stability filter 三项的可测 TV 上界；
- 在 llama.cpp Qwen 后端跑了 18 条 (en×9 + zh×9) baseline，汇报 SR=18/18、bits/token≈2.48、编解码延迟分布。

作者把论文明确限定在 "passive censor + 可恢复性/运行时/效率 baseline" 的范围，Q4（approximation 实测）和 Q5（detector/traffic 侧）承认 pending。

## 2. Strengths

1. **Scope 诚实**：论文反复强调 detector-resistance 尚无证据、主动修改 out-of-scope、Q4/Q5 pending。摘要、引言、限制、evaluation plan 的措辞一致，没有越位。在这个方向的论文里难得。
2. **协议工程细节扎实**：packet 格式、fingerprint 绑定 (runtime/backend/prompt_sha256)、fail-closed 六类失败、low-entropy retry 的窗口规则 ($w=32,\tau=0.1$)、retry 仅 sender-side 不影响 replay —— 这些是多数 NLS 后继工作讲不清楚的地方。
3. **近似误差分解清晰**：$\mathrm{TV}(Q'_t,P_t)\le \alpha_t + N_t/(2F_{\mathrm{tot}}) + \beta_t$ 三项物理意义清楚、每项都可从运行时日志直接测得；KL 上界 $\le N_t/F_{\mathrm{tot}}$ (nats) 给出数量级直觉。
4. **Artifact 纪律**：`results/real-backend-baseline-{r1,r2}` + merged summary + reproduce.sh 已发布，claim↔evidence appendix 对模块级映射做了 condensed 版。
5. **Threat capability matrix** (Table 1) 和 **logging schema** (Table §7) 把"what is / isn't measured"列得很规整，便于审稿和后续扩展。

## 3. Major Concerns

### M1. 标题与内容严重不匹配
标题 "**an almost perfect steganography**" 暗示一个接近 provable-secure / indistinguishable 的结果，但正文明确说：
- §7.7: "The present paper does not claim that current finite-precision, truncated, stability-filtered operation already satisfies a full provable-security theorem."
- §8: Q5 detector-facing pending；§13: "not yet provide full empirical detector-resistance evidence."

现状是 **18 条 trial 的可恢复性 + 延迟 baseline**，连 single-sample detector AUC 都没有。标题应改为 "*A Deterministic, Fail-Closed LLM Steganography Protocol with Measurable Approximation Bounds*" 之类；否则以现在的标题投任何安全会议都会直接被拒。

### M2. 实验体量过小，statistical claims 站不住脚
- $n=18$（en 9 + zh 9）就报 p90/p99 延迟，p99 在 n=9 里本质上就是"最大值"，没有意义。
- SR=18/18=1.000 在这个样本量下 95% Wilson CI 约 [0.82, 1.00]，离 "operationally reliable" 的叙事有距离。
- 没有 CI、bootstrap 区间、effect size —— §8.10 自己定的"statistical reporting rules"没在 Table 2/3 里兑现。
- 至少需要 prompt family × language × message length 3×2×3 = 18 个 cell，每 cell ≥30 条；总量 ≳ 500 才谈得上 baseline。

### M3. 缺乏与 NLS / OD-Stega 的对齐对比
§8.8 和 §12.3 都承认这是 explicit gap。但这是 **本论文最关键的比较基线**：既然 Ghostext 的 novelty 定位是 "systems-security engineering over the same AC-style mechanism"，那就必须证明这些额外机制（fingerprint、stability filter、fail-closed 回路）没有显著牺牲 bits/token 或延迟。没有这一张表，"positioning" 只是口头声明。

### M4. 近似分析的 "bound" 与 security 之间缺一步关键推导
§7 给的 TV / KL bound 是 $Q'_t$ 对 $\widetilde{P}_t$ 或 $P_t$ 的 per-step 距离。但对 censor 而言，真正重要的是 **stego 序列分布 vs. 自然 LLM cover 分布** 的 TV/KL，并且要做 detector-advantage 的翻译（例如 Cachin 框架下 $\mathrm{adv}\le \mathrm{TV}$）。作者在 §7.6 用 chain decomposition 写了 sequence KL，但随即放弃 analytic bound、退到 "log per-step and compute $\widehat{B}_{\mathrm{TV}}$"。

这是可以接受的工程折中，但请至少补：
- (a) 一个显式的 "TV bound → censor advantage" 的形式化桥梁引用；
- (b) 说明 $\widehat{B}_{\mathrm{TV}}$ 作为 audit signal 的 **单调性假设**（即 $\widehat{B}_{\mathrm{TV}}$ 小是否确实意味着 detector 难）——目前文中直接承认 "not a direct detector-risk guarantee"，那它的用途需要更谨慎的定位。

### M5. Fingerprint 64-bit 的对抗面分析不充分
§5.7 / §7.8 承认 64-bit 是兼容性选择而非安全最优。但在 multi-session / adaptive 场景下：
- 若 censor 掌握 prompt 模板、枚举 runtime 变体做 fingerprint 碰撞，虽然不破坏 AEAD，但会让 "mismatch vs. match" 的信号噪化——这可能被 **用作 side channel**（多条消息都 match 的 session 的行为 vs 单条 match 的行为）。作者只说"degrade diagnostic clarity"，但没量化。
- 建议或者默认升到 128-bit，或者给出 64-bit 在当前 threat model 下的**显式 justification**。

### M6. $h_{\min}=0.0$ 的 baseline 设定使 capacity 数字被高估
实现默认 $h_{\min}=1.0$ bit，但 baseline 跑的是 $h_{\min}=0.0$，bits/token=2.478 是在**完全不门控低熵步**的前提下拿到的。§7.5 虽提及这是"避免 entropy-threshold gating during this initial run"，但这恰恰是最容易被 detector 抓住的工作点（低熵步强行嵌入 → 词元选择偏离 $P_t$ 最明显）。
→ 至少需要同时汇报 $h_{\min}\in\{0.0, 0.5, 1.0\}$ 三档，否则 bits/token=2.478 的数字极具误导性。

### M7. Retry 的 traffic leakage 只给了 marginal mixture 式子，没有实测
§7.9 的公式是平凡的全概率展开，没有提供任何数据。而 "attempts used: mean 1.944, max 5" 本身就是强信号——一个 natural LLM 生成基线不会有重试分布，单这一条就可能把 stego vs. cover 区分开。这不是 Q5 pending 可以完全搪塞的，因为它直接由 Q3 的测量数据导出。建议至少补一个 "stego retry-count distribution vs. natural-cover (trivially all-zero)" 的对比段落。

## 4. Minor / Writing Issues

- **标题**：同 M1。另外 "almost perfect stenography" 应为 "**steganography**"，拼写错误出现在标题里非常刺眼。
- **模型命名**：§6.1 的 "Qwen/Qwen3.5-2B" 是 artifact label；Qwen 官方并无 3.5-2B 这个版本号，请核对是 Qwen2.5-1.5B/3B 还是其他，避免审稿人对复现性产生怀疑。
- §5 引用 "Section~5" 自引——改 cross-reference 标签或改写。
- Table 2 (tab:examples) 把整个 §5 example 塞进了 table*，但正文 §5.8 说的 "current JSONL release logs metrics and metadata but not full cover strings" 与 Table 2 中给出的具体 cover text prefix 存在微妙矛盾（这两条是 toy backend，不是 real backend；需要在 caption 里把 "toy backend" 顶格说清楚，避免被误读）。
- §4.4 "tail ... is not a distinct detector-evasion mechanism" 重要结论，建议在 abstract 里也提一句；现在 abstract 看起来 tail 是设计的一部分，实则是 "extend text to a more complete ending" 的操作性收尾。
- §7.4 KL 推导里 $u<1$ 的条件在 $\delta_t(v)=1/F_{\mathrm{tot}}, Q_t(v)=1/F_{\mathrm{tot}}$ 的边界情形下 $u=1$ 使 $-\log(1-u)=\infty$，证明需要指出 "由构造 $\widetilde{P}_t(v)\ge 0$ 且存在候选仅在 $\widetilde{P}_t(v)>0$ 时计算"，否则 bound 的 finiteness 有歧义。
- Bibliography 里 `huang2026odstega` 的年份是 2026——需核对是否真的是 2026 发表的预印本或会议版本（当前是 2026-04，边界情况）。
- `refs.bib`/编号：建议把 watermark 和 detector 两簇引用合并到一个 "detector & watermark" 小节，目前分散在 §12.2 后段，逻辑跳跃。

## 5. Reproducibility

优点：实现代码、raw JSONL、merged summary、reproduce.sh 都在 repo 内。appendix A 的模块级 claim mapping 也在位。

缺点：
- JSONL 当前不含完整 cover string（§5.8 / §8.3 都承认），detector-side 评估无法从已发布 artifact 直接启动；
- 后端 build 环境（llama.cpp commit、编译 flag、硬件）只在 §7.11 抽象地提了"应记录"，但 baseline 的 r1/r2 summary 是否已经 log 了需在 artifact README 里明示。

## 6. Recommended Actions (按优先级)

1. **改标题** + 把 abstract 措辞和标题对齐（去掉 "almost perfect"）。
2. **放大实验**：至少 3 prompt family × 2 language × 3 message length × 30 trials，报 Wilson / bootstrap CI。
3. **补 NLS & OD-Stega 对齐对照表**（哪怕只做一个 condition）。
4. **补 $h_{\min}$ 扫描**（至少三档），重报 bits/token 和 failure composition。
5. **补 retry-count 分布对比**（stego vs. natural cover trivial-0）。
6. **Q5 至少补 single-message detector AUC**（fastText + DetectGPT + 一个 LLM judge），即便结果对 Ghostext 不利也要报。
7. **Fingerprint**：给出 64→128 bit 的 migration 路径或明确 adversarial justification。
8. 修正标题拼写、Qwen 版本号、内部 cross-reference、toy/real backend caption 区分。

## 7. Overall Assessment

论文的 **工程谨慎度** 和 **scope 诚实度** 都高于这个领域的平均水位，近似误差分解、fail-closed 失败类别、configuration fingerprint 绑定都是实打实的系统贡献。但：

- **标题严重越位**；
- **实验体量不足以支撑任何统计化叙事**；
- **与最相关基线 (NLS, OD-Stega) 的对齐比较缺席**；
- **detector-side 证据为零**。

如果作者把本文定位改为 "protocol engineering + measurable approximation framework + baseline release"（去掉 "almost perfect" 暗示），扩到 workshop 或 system track，在补齐 M2/M3 后可接收；投安全顶会则需要在补完 Stage 3–6 之后再论。

**Confidence:** 3/5（系统/密码工程层面有把握；detector-side 细节因论文未涉，无法深判）。
