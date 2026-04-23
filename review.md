# Review: Ghostext — Near-Distribution-Preserving LLM Steganography with Authenticated Packet Framing

**Recommendation:** Reject / Major Revision (Incomplete Evaluation)

本轮基于提供的 `paper/**` LaTeX 源码（包含 `01-introduction`, `02-background`, `05-protocol-details`, `06-implementation`, `08-evaluation-plan`, `12-related-work`, `13-limitations-and-conclusion` 等章节）进行审稿。

与上一版（从原 review 推断）相比，当前版本的论文在 **Scope Discipline（预期管理）** 上做到了极致，明确排除了 detector resistance 和 cross-hardware determinism 的过大声明，并将重点完全放在了系统集成和协议层面的 deterministic recoverability 上。作者引入了完整的 AEAD packet framing 和 Segment Arithmetic Coding（简化版展示在 Algorithm 1-3），并强调了 Open Science 纪律（精确 pin 到了 GGUF metadata 和 llama.cpp 的 commit hash `f49e917`）。

然而，**当前的 Evaluation 章节（§8）出现了极其严重的退化**。论文仅仅报告了一个基于 `ghostext benchmark --runs 3` 的单 prompt、单 message 的“烟雾测试（Smoke Test）”结果。这甚至达不到 pilot study 的标准，直接导致论文的核心技术声明（如 near-distribution-preserving、overhead 表现）处于完全无证据支撑的状态。

综合判断：**系统设计极其精巧，工程与预期纪律极佳，但评估部分未完成（Incomplete），目前达不到任何学术会议的正式发表门槛。**

---

## 1. Strengths

1. **极致的 Scope Discipline 与诚实度**：这是本文最大的亮点。论文在多处反复强调自身的局限性。例如：“Evidence is implementation-level... Detector-facing resistance... are out of scope.” 这种主动自我降权的写法极大地降低了误导性，为隐写术（steganography）领域的防御性学术写作树立了诚实的标杆。
2. **清晰的系统层抽象与协议设计**：§5 详细描述了涵盖 Cryptographic Packet Layer 和 Token-Selection Layer 的双层架构。特别是引入了 Finite-Message Interval Coding（Algorithm 1），用完全整数域的操作避免了传统 streaming range coder 在模型采样环境下的重归一化（renormalization）复杂性，这在工程上非常 elegant。
3. **Artifact 纪律与 Reproducibility**：§6 和 §14 明确记录了极其详细的 provenance metadata，包括上游模型、特定的 GGUF 文件、甚至固定的 llama.cpp 编译版本。这直接回应并解决了之前审查中通常会遇到的复现环境模糊问题。
4. **Threat Model 的边界清晰**：§2 明确设定了 passive Censor 模型，并坦诚了 template-known 的风险和 multi-message 侧信道，有效防止了无谓的 out-of-scope 攻击模型拷问。

---

## 2. Major Concerns (Fatal Flaws)

### M1. Evaluation 仅为 Smoke Test，毫无统计学意义 ($n=3$)
当前 §8.1 报告的 Table 1 仅来自 `ghostext benchmark --runs 3`，使用的是固定的 passphrase (`demo-pass`)、单一的短 message (`Attack at Dawn!`) 和单一的预设 prompt。
- **这本质上是一个 unit test / integration test，而不是学术 evaluation。**
- 报告的 Encode latency (26.9s) 和 bits/token (2.72) 仅仅是针对这一个特定短句的观测值，完全缺乏在不同文本长度、不同 prompt 复杂度、不同语言下的方差和分布特征分析。
- **强烈要求**：必须恢复或扩展评估集。至少需要构造数十个不同的 prompt-message pair（如 $n \ge 100$），才能给出有说服力的 metrics（中位数、长尾延迟、成功率 Wilson 置信区间等）。

### M2. “Near-Distribution-Preserving” 缺乏实证或理论支撑
论文标题和摘要高调强调了 “Near-Distribution-Preserving”，指出其偏离自然分布的原因仅在于 deterministic quantization 和 retokenization-stability filter。
- 然而，§8 中**没有任何关于分布偏离度（如 KL-divergence, Total Variation distance）的客观测量数据**。
- Perplexity (7.53) 仅仅是一个非常粗糙的 fluency 检查指标，并不能证明生成的文本分布与原始 LLM 自然采样的概率分布不可区分。
- 此外，LaTeX 源码中缺少了理论分析章节（如 TV bound 或 KL bound 的推导）。如果没有理论 Bound 的证明，也没有实证的分布距离测算，这个核心 claim 就会沦为一句空话。

### M3. 缺乏与 Baselines 的任何对比
§1 和 §12 提到了 NLS (Neural Linguistic Steganography) 和 OD-Stega 等 baseline，并宣称了 Ghostext 系统整合的优势。但在 §8 评估中，完全没有给出 Ghostext 与 NLS 风格的 baseline 在同样设定下（同 Backend, 同 Prompt）的对比验证。没有对比，所谓的 protocol overhead 就没有锚点，读者无法评估增加的密码学 payload 到底带来了多少性能损耗。

### M4. 承诺的关键分析缺失 ($h_{\min}$ sweep)
论文在 §5.3 提到默认 $h_{\min}=1.0$ bit，但并没有展示 $h_{\min}$ 对 bits/token 或解码稳定性的实际影响。调节熵阈值 ($h_{\min}$) 是平衡生成文本隐蔽性与系统吞吐量的最关键参数，必须提供详尽的 Ablation study。

---

## 3. Minor / Presentation Issues

1. **缺失的章节结构断层**：提供的 LaTeX 源文件在命名上（`01`, `02`, `05`, `06`, `08`, `12` 等）存在明显的数字断层。这暗示了在论文重构过程中可能生硬地删减了核心分析或实验部分（如原有的第 3, 4, 7 等章节）。请在最终修订时确保正文结构的连续性和逻辑完整。
2. **可视化不足**：Algorithm 1-3 的伪代码写得非常清晰，但缺乏架构层面的直观展示。强烈建议补充一张系统层面的 Data Flow Chart (TikZ 或 PDF 图)，将 AEAD packet 的构造、bootstrap 分段和后续的整数区间映射直观可视化。

---

## 4. Recommended Actions (for Resubmission)

要想达到任何主流学术会议 (Main Venue) 或高质量 Workshop 的接收标准，必须补齐以下评估短板：

1. **扩充实验规模 (Scale up the evaluation)**：放弃 $n=3$ 的 benchmark。运行大规模、标准化的评测（如 $n=100$ runs），报告详实的 SR (Success Rate)、平均 Bits/Token 和时间开销分布。
2. **实证分布偏离度测量 (Empirical Distribution Analysis)**：既然声明了“Near-Distribution-Preserving”，请输出 $\sum (\alpha_t + N_t/(2F_{\mathrm{tot}}) + \beta_t)$ 等量化指标的直方图，或者直接计算生成的分布距离，作为对理论预期的实证交代。
3. **引入 Baseline 对比 (Baseline Comparison)**：在相同的 local llama.cpp 环境下，横向对比不包含 packet framing 的裸 NLS 变体，以证明该协议在 fail-closed 容错和安全性上换取的 trade-off 是合理的。
4. **参数消融实验 (Ablation on $h_{\min}$)**：提供 $h_{\min} \in \{0.0, 0.5, 1.0\}$ 的对比图表，展示熵阈值对 payload density 的影响。

**Bottom line**: The paper currently reads like an excellently scoped protocol specification and software manual, but it stops abruptly just before conducting a scientific evaluation. Once the evaluation data matches the rigor of the protocol design, this will be a solid and highly reproducible contribution.