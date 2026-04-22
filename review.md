# Review: Ghostext — A Deterministic, Fail-Closed LLM Steganography Protocol with Implementation-Aligned Approximation Bounds

**Reviewer:** Anonymous · **Date:** 2026-04-22 · **Recommendation:** Weak Reject — Major Revision (conditional on completing self-committed experiments and fixing one invalid derivation step)

本轮基于 `paper/main.tex` + `paper/sections/*.tex` + `results/` artifact bundle 当前状态通读。对照上一轮（`cba0a60` → `ac8a422`），作者已把 title、abstract、§1 contribution、§3 threat scope、§7 analysis 措辞**整体向下校准到 pilot/baseline 级别**，并新增 §8.4 aligned NLS-style slice 作为同 backend 对比证据。这个 scope discipline 是本版最明显的改进——但 **empirical 体量依然处于 "18-trial 主基线 + 6-case 对比 slice" 的 feasibility-pilot 水位**，论文自己承诺的实验（$h_{\min}$ sweep / detector AUC / $\widehat{B}_{\mathrm{TV}}$ 实测 / retry 边信道 AUC）在投稿时点一项都没有落地，且 §7.4 的 KL 上界推导中间步有一个**显式错误的不等式**（在 $u>0$ 区间不成立），虽然最终 bound 仍然正确。

综合判断：**措辞已诚实，证据不充分，推导有一个 fixable 错误。**

---

## 1. Paper at a glance

- **Topic**：generation-based LLM steganography，在 arithmetic-coding 家族里加 AEAD packet + bootstrap/body 双段嵌入 + 配置 fingerprint + fail-closed 失败类型学。
- **Core contribution (按 §1 表述)**：(i) implementation-aligned protocol description with authenticated packetization; (ii) approximation bound 的形式化分解 $\alpha_t + N_t/(2F_{\mathrm{tot}}) + \beta_t$; (iii) real-backend pilot (18 trial) + aligned slice (6 case × 3 method)。
- **Empirical scope**：Qwen-family q4_k_s GGUF on llama.cpp，template-known prompt family，`top_p=0.995, max_candidates=64, min_entropy_bits=0.0, total_frequency=4096`。固定 passphrase，seed=7。
- **Headline numbers**：SR 18/18（Wilson 95% CI $[0.824, 1.000]$）；encode median 50.56 s；bits/token mean 2.478；attempts_used mean 1.944 max 5。
- **Not claimed**：detector resistance、active-attacker robustness、cross-hardware determinism、跨模型家族泛化。

---

## 2. Strengths

1. **Scope discipline 是全版最大优点**。abstract（main.tex L20）一处明写 "protocol-engineering contribution rather than a near-perfect-security claim"，§1 contribution #3 加 "(six Qwen cases; see Section 8.4)"，§12.6 "do not make broad superiority claims"，§13.1 九条 limitations 逐条列出。这种**主动降权**让 reviewer 不必用 claim-hunting 模式读 paper。
2. **§4–§5 协议层写法成熟**。packet 格式 `salt ‖ header_nonce ‖ sealed_header ‖ body_nonce ‖ body_ciphertext`、bootstrap/body 双段嵌入、natural tail 与 payload 分离、fail-closed 失败类型学（authentication / configuration / synchronization / unstable-tokenization / low-entropy / token-budget 六类）都写得条理清楚。§4.3 operational encode/decode semantics 的自然语言补充足够支撑 Figure 1 那张纯文字 flow 框。
3. **§5.6 TV bound 推导正确**。$\mathrm{TV}(Q'_t, P_t) \le \alpha_t + N_t/(2F_{\mathrm{tot}}) + \beta_t$ 的三项加和，正确处理了 stability filter 后 renormalization 的 double-counting（证明 $\|Q'_t - R_t\|_1 = \beta_t$ 和 $\|R_t - Q_t\|_1 = \beta_t$ 复用同一个 $\beta_t$）。
4. **§7.9 retry-induced traffic leakage 的主动 self-exposure**。论文自己写 "retry count alone is therefore a trivially separating feature against any zero-retry natural-cover baseline; no learned detector is required to exploit that difference"，并用 18-trial 的 `attempts_used` 分布（en `1:7, 2:1, 5:1`；zh `1:3, 2:2, 3:3, 5:1`）给出具体数字。这种**先于审稿人把问题指出来**的写法是加分项，尽管它同时把实验责任推给了未来阶段。
5. **§7.8 fingerprint collision 的 deployment tradeoff 讨论诚实**。同一份数字（$n=10^6 \to 2.7\times10^{-8}$ birthday，$2^{40}$ adaptive trials $\to 2^{-24}$）在 §5.7 和 §7.8 两处复现，并主动承认 "not a margin worth presenting as future-proof when the byte overhead of widening is negligible, 128-bit is the conservative future direction"——主动 self-downgrade 而不是为现有 64-bit 选择辩护。
6. **§3.4 Table 1 threat-capability matrix**。把 "in scope / measured axis / out of scope" 分三列列出，尤其 "Active text modification in transit = out of scope"、"Runtime compromise of sender/receiver endpoint = out of scope" 两句**直接锁定 passive-censor 模型边界**，防止后续用 out-of-scope attack 拷问论文。
7. **§8.4 aligned slice 的 split claim 与 Table 4 数据对齐**。"cryptographic payload normalization removes direct plaintext structure at the carried-bitstream layer, but segmentation and runtime controls are still needed to make that randomized payload usable on this backend"——这条结论直接对应 Table 4 里 Ghostext full (6/6) vs NLS AEAD single-segment (4/6) 的 2-case 差值，且 Appendix Table 5 per-case 展开了具体 stall 位置（`en_short_01`、`en_mid_01`）。结论小，但证据链闭合。
8. **Artifact 纪律延续**。`results/aligned-qwen-baselines/aligned_baseline_summary.json` 一处暴露 `ghostext_git_head`（b1eb84c7…）、`paper_git_head`（cba0a607…）、`tokenizer_hash`、`backend_id`、`seed=7`、完整 candidate + codec config、显式 `passphrase_policy`。`reproduce.sh` 命令行参数与脚本函数签名匹配。这是整个 bundle 里 provenance 最全的一处。

---

## 3. Major Concerns

### M1. §7.4 KL 上界推导存在一个**显式错误的中间不等式**（最终结论仍正确）

这是本轮 reviewer 新发现的技术问题，不出现在前一轮 review 中，值得作者优先处理。

§7.4 第 53 行声称：

> "For terms with $\widetilde{P}_t(v)>0$, we have $u=\delta_t(v)/Q_t(v)<1$ and may use $-\log(1-u)\le \frac{u^2}{1-u}$"

然后用这个不等式推出 $D_{\mathrm{KL}}(\widetilde{P}_t \| Q_t) \le \sum_v \delta_t(v)^2/Q_t(v)$。

**问题**：不等式 $-\log(1-u) \le u^2/(1-u)$ **在 $u > 0$ 区间不成立**。数值验证：

| $u$ | $-\log(1-u)$ | $u^2/(1-u)$ | 关系 |
|---:|---:|---:|---|
| $-0.50$ | $-0.4055$ | $0.1667$ | ✓ |
| $0.00$ | $0.0000$ | $0.0000$ | ✓ (边界) |
| $+0.10$ | $0.1054$ | $0.0111$ | **✗ LHS > RHS** |
| $+0.25$ | $0.2877$ | $0.0833$ | **✗ LHS > RHS** |
| $+0.50$ | $0.6931$ | $0.5000$ | **✗ LHS > RHS** |
| $+0.75$ | $1.3863$ | $2.2500$ | ✓ |
| $+0.90$ | $2.3026$ | $8.1000$ | ✓ |

不等式在 $u \in (0, \sim 0.683]$ 整个连续区间失效。而 $u = \delta_t/Q_t > 0$ 恰好对应**量化时 $Q_t(v) > \widetilde{P}_t(v)$** 的分支——亦即 quantizer "给 candidate 分配的频率多于连续概率" 的一半 token 位置。整个推导的主要支撑力度**来自这个伪不等式**。

**但最终 bound $D_{\mathrm{KL}} \le \sum \delta^2/Q$ 本身是正确的**，它就是标准的 $\chi^2$-divergence 上界（见 Tsybakov 2009 Ch.2 或 Cover & Thomas Thm. 2.7.1 的 variational 形式）。所以这是一个 **"bound 对，derivation 错"** 的 fixable error。

**修复建议**（三选一）：

- **(a) 最简**：直接引用 $KL \le \chi^2$ 这个标准结果，删掉中间那步伪不等式。正文改为："Applying the standard $\chi^2$-divergence upper bound on KL (cf. Tsybakov 2009, Eq. (2.28)), we have $D_{\mathrm{KL}}(\widetilde{P}_t \| Q_t) \le \chi^2(\widetilde{P}_t, Q_t) = \sum_v \delta_t(v)^2 / Q_t(v)$. Using $Q_t(v) \ge 1/F_{\mathrm{tot}}$ and $|\delta_t(v)| \le 1/F_{\mathrm{tot}}$, ..."
- **(b) 保留 log 展开路线**：把中间不等式改成正确形式 $-\log(1-u) \le u + u^2/(1-u)$（对 $u < 1$ 全局成立，可用 Taylor 比较证），然后显式展开 $\sum \widetilde{P}_t(v) \cdot u = -\sum \delta^2/Q$ 并与 $u^2/(1-u)$ 项合并。合并后净系数是 $\frac{1}{2}$ 的 Taylor 主项左右，需要重新计算 $N_t/F_{\mathrm{tot}}$ 的常数，可能变成 $N_t/(2F_{\mathrm{tot}})$。
- **(c) 另一条更干净的路线**：直接用 $\log(x) \le x - 1$（即 $\log(\widetilde{P}/Q) \le \widetilde{P}/Q - 1$），从而 $D_{\mathrm{KL}} = \sum \widetilde{P} \log(\widetilde{P}/Q) \le \sum \widetilde{P}(\widetilde{P}/Q - 1) = \sum \widetilde{P}^2/Q - 1$。然后用 $\widetilde{P} = Q - \delta$ 展开到 $\sum \delta^2/Q$。

**本 concern 的 severity 评级**：中-高。因为 §5.6 TV bound 正确、最终 KL bound 本身也正确，不影响 §7 analysis 的结论；但一个以 "implementation-aligned approximation bounds" 为 headline 的论文**不应该在其核心技术章节里留一个小学代数能反驳的不等式**。这是会被 theoretical reviewer 第一眼抓到的 sitting duck，且修复工作量是 30 min 级。

**自检建议**：把 §5.5（quantization bound $\|Q_t - \widetilde{P}_t\|_1 \le N_t/F_{\mathrm{tot}}$）和 §7.4（KL bound）两处的不等式全部在 Python/sympy 里跑一遍数值检验，每一行都明写 premise（如 $u < 1$、$Q_t \ge 1/F_{\mathrm{tot}}$）。这是一次性工作、永久收益。

### M2. 样本量：主基线 n=18，aligned slice per-method n=6

**主基线 18-trial**：SR 18/18 看似完美，但 Wilson 95% CI 下界 **0.824**。这意味着真实 $\mathrm{SR}$ 在 80% 附近也与观测数据相容。对于一个以 "fail-closed + deterministic decode" 为核心卖点的协议，"真实 SR ≥ 80%" 是一个**远远不够的 floor**。per-language（n=9 each）的 Wilson CI $[0.701, 1.000]$ 更宽。§8.3 末段的写法（"operational floor rather than a settled reliability estimate"）在措辞层已经诚实，但 reviewer 需要的是更窄的区间，不是更小心的措辞。

**aligned slice per-method n=6**：三个 method 的 Wilson 95% CI：

- Ghostext full (6/6) → $[0.610, 1.000]$
- NLS-UTF8 (5/6) → $[0.419, 0.963]$
- NLS-AEAD (4/6) → $[0.300, 0.898]$

三区间**大面积重叠**。Fisher exact: 6/6 vs 4/6 给 $p \approx 0.45$（两尾）。§8.4 第二段正确地避免了 "significantly outperforms" 措辞（写的是 "stalls on ... cases"），但**split claim 的统计说服力也对应下降**——它目前是一个对 6 条 trace 的观察报告，不是一个可外推的统计陈述。

**三条可行路径**（三选一）：

- **(a) 主基线扩到 n ≥ 100**：prompt family × language × message length 拉成 3 × 2 × 3 cell × 6 trial = 108 trials。wall-clock 估算 108 × 50 s encode + 30 s decode ≈ 2.5 h（串行），可 3 并发压到 50 min。
- **(b) aligned slice 每 method 扩到 n ≥ 30**：保持 6 case 不变，每 case × method 跑 5 个 seed rotation，总 6 × 3 × 5 = 90 run。Table 4 附 per-method Wilson CI。
- **(c) 显式降级为 short paper / workshop pilot paper**：标题增加副标 "A Feasibility Pilot"，main venue 不投。

继续停在 $n \in \{6, 18\}$，**任何 main venue 都找不到接收理由**。

### M3. $h_{\min}$ sweep 零数据——论文自己承诺的实验

§7.5 第 80 行：

> "The practical next step is therefore not to headline this single number, but to run the same condition grid at least over $h_{\min}\in\{0.0,0.5,1.0\}$ before treating any efficiency figure as representative of a conservative deployment envelope."

§13.1 第 13 行：

> "The reported 2.478 bits/token figure comes from an ungated baseline with $h_{\min}=0.0$ and should not be interpreted as a recommended deployment point."

**但 abstract 和 Table 2 的 headline 仍然是 $h_{\min}=0.0$ 下的 2.478 bits/token。**$h_{\min}=0.0$ 是论文自己定义的 "最激进、最不安全" 工作点——per-step entropy 接近 0 时仍然 embed，这恰好是 detector 最敏感的区域。headline 数字用最激进 operating point、同时在正文写 "不是 recommended deployment point"——这是**内部自相矛盾的报告姿态**。

**成本极低**：`results/real-backend-baseline-reproduce.sh` 改一行 `--min-entropy-bits`，三档 × 18 条 = 54 runs × 平均 ~80 s = 72 分钟 wall-clock（并行三进程 < 30 min）。三档数据可立即回答：

1. $h_{\min}=1.0$（implementation default）下 bits/token 还剩多少？（预期 1.2–1.8 bits/token）
2. $h_{\min}$ 上升对 retry 分布的影响？（预期 low-entropy stall 触发概率上升 → retry 频率上升 → M4 里 trivially separating AUC 变化）
3. aligned slice 的 split claim 在 $h_{\min}=1.0$ 下是否依然成立？如果 Ghostext full 在高 $h_{\min}$ 下也出现 stall，"segmentation + fail-closed" 相对 NLS single-segment 的 advantage 边界需要重新界定。

**这是本轮成本/收益比最高的实验项**。reviewer 对此的耐心已经延续多轮；继续不补会被视为"author 不愿意生成可能削弱 headline 数字的证据"。

### M4. Detector-side（Stage 5）零数据——两处 self-commitment 未兑现

§7.6 第 102 行：

> "the staged detector block treats correlation analysis between $\widehat{B}_{\mathrm{TV}}$ and detector scores as a required output, not an optional add-on."

§7.9 第 135 行：

> "Under the current policy, retry count alone is therefore a trivially separating feature against any zero-retry natural-cover baseline; no learned detector is required to exploit that difference."

这两段构成论文自己写下的**双重 unfulfilled commitment**：§7.6 把 $\widehat{B}_{\mathrm{TV}}$ 与 detector 的相关分析定义为 "required output"；§7.9 把 retry-count trivially separating 识别为"不需要训练 detector 的平凡攻击"。两条都有结论性陈述，但**零测量数据**。

**本轮 minimum viable detector block**（合计 < 4 小时）：

1. **Retry-feature trivially separating AUC**：直接在现有 18 条 Ghostext cover（每条有 `attempts_used` 字段）和 18 条 `--max-encode-attempts=1` 强制单次 natural-cover 对比上算 ROC-AUC。论文自己已经导出结论 AUC=1.0，实测只是**1 行 numpy + 1 行表格**。
2. **$\widehat{B}_{\mathrm{TV}}$ histogram (Stage 3 slice)**：在 `codec.py` 的 encode loop 里加一个 `per_step_log` hook，输出 $\alpha_t, N_t, \beta_t$ per step，per message 聚合为 $\widehat{B}_{\mathrm{TV}} = \sum_t (\alpha_t + N_t/(2F_{\mathrm{tot}}) + \beta_t)$。跑现有 18 条 baseline 一次，出 18 条 $\widehat{B}_{\mathrm{TV}}$ + per-message histogram。这不是 "detector-side" 结果，但兑现了 §7.6 的 "required output"。
3. **fastText binary AUC**（可选，拉高说服力）：18 条 Ghostext cover + 18 条 Qwen 无 retry 的自然 cover（`llama-cli --temp 0.7 --seed 7 --prompt <P>`），fastText `cc.en.300` + logistic head 二分类，报 per-language ROC-AUC。即便 AUC ≈ 0.5 也要报（这反而是 Ghostext 的 positive signal）。

三件合起来不需要新模型、不需要 GPU、不需要 detector 训练。但它们是**从 "promise" 跨到 "initial evidence" 的必要一步**。

### M5. 主基线 vs aligned slice 的 Ghostext encode median 差 37%，文中无解释

| 测量 | $n$ | policy | Ghostext encode median (s) |
|---|---:|---|---:|
| 主 baseline (§8.3 Table 2) | 18 | `top_p=0.995, max_cand=64, min_ent=0.0, F_tot=4096` | **50.56** |
| Aligned slice (§8.4 Table 4) | 6 | 同上 | **31.85** |

同一协议、同一 policy、同一 backend、同一 seed（aligned summary.json 显示 seed=7，主 baseline merged summary 也有 seed=7）、同一 host、同一 platform——encode median 差 **37%**。

**归因假设**：

1. **Message 子集差**：aligned slice 的 6 case（`{en,zh}_{short_01, short_02, mid_01}`）是主 baseline 同 6 case 的子集；主 baseline 18 trial = 6 case × 3 repeat。aligned slice `attempts_used` 全是 1（从 summary.json 的 `"failure_histogram": {}` + 单次 encode 时间推断），主 baseline `attempts_used` mean 1.944 max 5——主 baseline 里有多 attempt 案例把 median 拉高。
2. **时间窗口差**：aligned slice `generated_at_utc: 2026-04-21T13:48:52Z`，主 baseline r1+r2 是早前 merge。WSL2 host 负载可能不同。

**论文 §8.4 第二段其实已经间接解释**（"the lower Ghostext median encode time here relative to the merged 18-trial pilot (31.85 s versus 50.56 s) reflects the short/mid six-case composition and the absence of retry-heavy runs in the slice, not a policy change."）。**这段解释是正确的，但被埋在段落中间**，reviewer 很容易漏读。

**Ask**：

- 将该解释**显式上提到 Table 4 caption 的 footnote**，并在主 baseline Table 2 caption 加对应的反向交叉引用。
- Table 4 增加 `attempts_used` 列（mean / max）：aligned slice 该数据已在 JSONL 中，零新实验成本。
- 最好 Table 2 和 Table 4 共享一致列顺序（目前 Table 2 用 `Metric / Value` 两列长格式，Table 4 用宽格式；两表风格不同导致跨读困难）。

### M6. Qwen provenance + llama.cpp commit SHA：两项分钟级 fix 仍未补

这是本轮**最无理由未补的一项**。检查 `results/real-backend-baseline-summary-merged.json`：

```json
"runtime": {
  ...
  "llama_cpp_commit_sha": null    // ← 字段存在但未填充
}
```

**字段已经在 schema 里——只是没有填**。这说明作者知道这个字段重要，基础设施准备好了，但**某一轮 release 没有把它接上**。

§6.1 第 9 行写：

> "For naming consistency, this paper follows the artifact identifier `Qwen/Qwen3.5-2B` as recorded in the released summaries. The companion implementation documentation points to the third-party GGUF repository `bartowski/Qwen_Qwen3.5-2B-GGUF` ..."

**问题**：Qwen 官方从未发布过 "Qwen3.5-2B"（Qwen 系列公开 release 包含 Qwen2.5-1.5B/3B、Qwen3-1.7B 等，没有 "3.5-2B"）。bartowski 的 GGUF 是第三方打包，上游 base model 可能是 Qwen2.5 或 Qwen3 系的某个 checkpoint。论文 §6.1 / §13.1 都诚实地把这个差异标成 "not as evidence that this string is the canonical upstream model-family tag"。

**两项都是分钟级 fix**：

1. **Qwen 上游 family 解析**：
   ```bash
   llama-gguf-dump /path/to/Qwen_Qwen3.5-2B-Q4_K_S.gguf \
     | grep -E "general\.(architecture|name)|tokenizer\.(ggml\.model|chat_template)|(vocab|n_embd|n_layer|n_head)"
   ```
   把 `general.name` 和 architecture tag 写进 §6.1 正文 + summary JSON 新增 `model.upstream_provenance` 字段。
2. **llama.cpp commit SHA**：在 `scripts/run_real_backend_baseline.py` 入口补：
   ```python
   llama_sha = subprocess.check_output(
     ["git","-C",LLAMA_CPP_REPO,"rev-parse","HEAD"]
   ).decode().strip()
   ```
   写进 `runtime.llama_cpp_commit_sha`（字段已存在、已为 null，只需填值）。

§13.1 第 23 行已经把这两项列为 "two reproducibility upgrades that remain"。**继续不补，reviewer 只能默认：作者在投稿层面对 reproducibility metadata 的优先级低于 narrative 迭代**，这会直接折损论文整体可信度。

### M7. Figure 1 仍是纯文字 `\fbox`，Figure 2 / retry histogram 仍不存在

**Figure 1 (§4)** 当前是 `\fbox{\parbox{0.96\linewidth}{...}}` 的两行文字流程。在 ACM sigconf 双栏下视觉上几乎等同于缩进段落；作为一个 systems protocol paper 的**唯一一张流程图**，信息密度不足以支撑它在论文结构中占据的位置。

**Figure 2 不存在**。主 baseline `attempts_used` histogram 数据（en `{1:7, 2:1, 5:1}`；zh `{1:3, 2:2, 3:3, 5:1}`）目前只在 §8.3 Table 3 的一个文字单元格里。这条 histogram 是：

- 支撑 §7.9 "trivially separating" 结论的**核心证据**；
- 解释 M5 encode median 差异的**直接机制**；
- detector-side trivially separating AUC 实验（M4.1）的**输入数据**。

这么一条一数据多用的 signal，**没有图是 presentation 级的 loss**。

**Ask**：

- Figure 1 升级为 TikZ 双路 flow chart（encode row / decode row），标出 packet 层、bootstrap/body、fail-closed checkpoint 位置。
- Figure 2 新增：per-language × per-method `attempts_used` stacked bar histogram 或 CDF，数据源来自 `real-backend-baseline-summary-merged.json` + `aligned_baseline_runs.jsonl`，**零新实验成本**。
- Figure 3 (可选)：Table 4 的三行 method-level SR + encode median 改成 bar chart with CIs，比三行表格视觉上更能呈现 "Ghostext 6/6, NLS-UTF8 5/6, NLS-AEAD 4/6" 这条差值。

### M8. Table 4 信息密度不足，缺 per-case 展开主表

§8.4 的 split claim 字面依赖 "NLS UTF-8 stalls on `en_mid_01`" / "NLS AEAD stalls on `en_short_01` and `en_mid_01`" 两条 per-case 陈述，但 **Table 4 主表只给 method-level aggregate**，`attempts_used` 列缺失。per-case 数据虽然在 Appendix Table 5 展开，但 reviewer 在正文读 §8.4 时必须跳到附录才能验证。

**Ask**：

- Table 4 增加 `attempts_used` 列（见 M5）。
- §8.4 正文引用 `en_short_01` / `en_mid_01` 时直接附加 Table 5 cross-ref（`(see Appendix Table~\ref{tab:aligned-nls-per-case})` 已经有了；可以在 §8.4 第二段 句首也加一句 "per-case expansion in Appendix Table 5"）。
- 或者把 Appendix Table 5 上移到正文作为 Table 4b，保留 Table 4 作为 aggregate。

### M9. JSONL schema / transparency policy 两类 artifact 不统一

- **主 baseline JSONL 是否包含完整 cover text**：§5.8 第 107 行写 "The current JSONL release logs metrics and metadata but not full cover strings"，但这句话只对主 baseline 成立；aligned slice 的 `aligned_baseline_runs.jsonl` 是否暴露 cover text 未明示。
- **Passphrase policy 措辞不一致**：
  - 主 baseline summary：`"passphrase_policy": "fixed local demo passphrase for reproducible baseline"`
  - Aligned slice summary：`"passphrase_policy": "fixed local demo passphrase for aligned baseline comparison"`
  
  两处都是**固定 passphrase**，但正文（§5.1 / §6 / §8）没有对此做统一说明。读者容易误以为两个 release 使用了不同的 crypto policy。
- **Seed 暴露**：aligned slice 明示 seed=7，主 baseline merged summary 也写 seed=7（检查 JSON 确认），但 §8.3 正文不强调这一点。
- **主 baseline summary 缺失字段**：相比 aligned slice summary，主 baseline merged summary 没有 `paper_git_head`（只有 `git_head`），字段命名不统一。

**Ask**：§5.8 / §6 / §8 的 artifact metadata 段落做一次 cross-release consistency pass，显式列清两个 release 的**共有字段 + 差异字段表**，避免 reviewer 跨 JSON 对比时产生误读。

---

## 4. Minor / Writing Issues

- **Abstract (main.tex L20)**：末句 "carrying AEAD packet bytes directly yields payload-bit entropy essentially at 1.0 yet the corresponding single-segment baseline still stalls on $2/6$ cases" 措辞准确，但 "essentially at 1.0" 对 non-specialist 模糊。可以直接给数字："mean one-bit entropy 1.000 vs raw UTF-8 baseline 0.991"。
- **§2.3 Positioning**：第 25 行 "The core embedding mechanism remains arithmetic-coding style, consistent with prior work" 后面引用 `ziegler2019neural, shen2020near`，但 `huang2026odstega` 没有在此处被重复引用，尽管 §1 / §2.2 / §12 都引用了它。建议此处也交叉引用，强化 "Ghostext 不声称新原语" 这条 scope line。
- **§3.2 第 9 行** "The released 18-trial baseline uses fixed public templates and should therefore be read as a *template-known operational floor*"——"fixed public templates" 建议改成 "fixed narrative/dialog prompt templates reused across trials"，避免 "public" 字面引发 "发布到 public web" 的误读。
- **§4.3 retry 参数**：第 35 行写 $w=32, \tau=0.1$，但 `aligned_baseline_summary.json` 的 codec 字段显示 `low_entropy_window_tokens: 32, low_entropy_threshold_bits: 0.1`——一致。**主 baseline JSONL 是否也用同值未在正文明示**（实际上是，但 reviewer 需要翻 summary 才能确认）。建议 §8.3 baseline config 段落的 codec 字段也显式列出。
- **§5.4 Interval Update**：第 36–38 行的 $L_{t+1}, H_{t+1}$ 更新公式使用 $\mathrm{cdf}_t^{-}(v)$ 和 $\mathrm{cdf}_t^{+}(v)$ 但未定义。建议在 §5.3 末段补一句 "where $\mathrm{cdf}_t^\pm(v) = \sum_{v' : v' \prec v} Q_t(v') \cdot [\text{left/right boundary}]$ under a fixed token-id ordering"。
- **§5.5 Quantization bound**：第 46 行 "$|Q_t(v)-\widetilde{P}_t(v)|\le\frac{1}{F_{\mathrm{tot}}}$"——这是**最坏情况** bound，建议明写 "worst-case per-candidate rounding error"，否则容易被误读为 L1 norm bound。
- **§5.7 第 90 行 "an adversary might search"**：上一轮 review 已指出 "a party" 问题；本轮已改为 "an adversary"，check 通过。但同句后 "adaptive trials against a fixed 64-bit target would still give only about $2^{-24}$" 建议加一条 side note "(idealized uniform-target model; real adversary may exploit structural correlations in $\mathrm{SHA256}(\mathrm{JSON}(\cdot))$ input space)"，避免把 idealized 计算直接等同于实战边界。
- **§7.4 KL bound**：除了 M1 的核心问题外，第 65 行 "it is at most $2.44\times10^{-4}$ nats for quantization alone" 的数字应给推导（$N_t/F_{\mathrm{tot}} = 16/65536 \approx 2.44\times10^{-4}$）；"Under the released baseline setting ($N_t\le64, F_{\mathrm{tot}}=4096$), the corresponding worst-case ceiling is $1.56\times10^{-2}$ nats" 对应 $64/4096 \approx 1.56\times10^{-2}$，也需要显式推导。这两个数字目前对读者是 "接受即可" 状态，检验成本小。
- **§7.6 第 96 行 $\mathrm{Adv}_{\mathrm{censor}}$ 定义**：上一轮已提过，本轮已加 "With $\mathrm{Adv}_{\mathrm{censor}} := |2\Pr[\mathrm{correct}] - 1|$ for a binary hypothesis test"——check 通过。但 "$\mathrm{TV}(Q_{1:T}, P_{1:T}) \le \sqrt{(1/2)D_{\mathrm{KL}}(Q_{1:T} \| P_{1:T})}$" 后面 Pinsker 引用使用 `cover2006elements`，建议改为更精确的引用（Tsybakov Lemma 2.5 或 Csiszár-Körner）。
- **§8.1 第 17 行** baseline config "top_p=0.995, max_candidates=64, min_entropy_bits=0.0, total_frequency=4096" 前面引号风格是 \texttt，建议在 §8.3 Table 2 caption 里也用同样的 `\texttt` 风格，保持引用一致。
- **§8.4 第 124 行** "The slice also reuses the six distinct prompt/message cases from the main baseline before the merged 18-trial release repeats them." ——措辞绕，建议直接写 "The six cases in this slice are the same six used once per $n=18$ merged baseline trial; the merged baseline repeats this case set three times across r1+r2."
- **§12.4 Detector and Watermark Context**：引用 `joulin2017fasttext` 和 `mitchell2023detectgpt`，但 §7.9 "retry count trivially separating" 这条结论缺 side-channel / timing-attack 方向的 prior work 支撑。可考虑加 Ristenpart et al. "Hey, You, Get Off of My Cloud" 或 Felten/Schneider timing 类经典引用。
- **§13.1 第 23 行** "two reproducibility upgrades that remain"——第三轮仍挂单。下一轮 revision 如果仍留在 limitations，reviewer 会**优先**在 reproducibility 维度扣分（见 M6）。
- **Appendix A Table 5** 的 "Released evidence path or anchor" 列已经给到函数级（`scripts/run_real_backend_baseline.py::classify_failure`），cross-check 通过。但 `scripts/merge_real_backend_baseline.py::build_markdown` 和 `scripts/merge_aligned_baselines.py::render_markdown` 两个函数名风格不一致（`build_` vs `render_`）——这是 companion artifact 的 naming concern，不阻塞投稿。

---

## 5. Reproducibility Assessment

**Positive**：

- aligned slice summary.json 是 bundle 里最完整的 provenance 记录（见 §2 Strengths 第 8 条）。
- `reproduce.sh` 脚本命令行与 Python 脚本函数签名对齐，wall-clock cost 在脚本注释里明写。
- JSONL per-run 粒度适合 audit；每条 run 包含 encode/decode latency、attempts_used、failure_class、token counts。
- 双 JSON schema（summary + runs）分离设计合理：summary 给 reviewer 总览，runs 给深度 audit。

**Unresolved**：

- `llama_cpp_commit_sha` 字段已存在、值为 `null`（M6）。
- Qwen 上游 provenance 未 surface（M6）。
- 主 baseline JSONL cover text policy 未明示（M9）。
- 硬件指纹不足：summary 只有 `platform: Linux-6.6.87.2-microsoft-standard-WSL2` + `host: kzoacn-PC`；缺 CPU model、RAM、llama.cpp 编译 flag、BLAS backend 类型。§7.13 承认 "cross-hardware determinism not yet established"，但 artifact 未记录**当前 hardware** 足够的 fingerprint 供未来对比。
- 两个 release 之间字段命名不统一（`git_head` vs `ghostext_git_head` + `paper_git_head`）。

**当前可复现等级**：**Level 2 / 4**（可用同 host 同 llama.cpp 跑出数值一致结果；无法跨 host 验证，也无法精确固定 llama.cpp build）。补上 M6 的两项后可升到 **Level 3**；补齐 hardware fingerprint + 跨 host 验证后可升到 **Level 4**。

---

## 6. Recommended Actions（按 reviewer 实际权重排序）

| 编号 | 项目 | 工作量 | 价值 |
|---:|---|---:|---|
| **1** | **修复 §7.4 KL 中间不等式**（M1）—— 改用 $\chi^2 \ge KL$ 或加上遗漏的 $u$ 项 | **30 min** | **中高（技术诚信）** |
| **2** | **Qwen provenance + llama.cpp SHA** 两项 fix（M6） | **分钟级** | **中高（reproducibility 底线）** |
| **3** | **$h_{\min} \in \{0.0, 0.5, 1.0\}$ sweep**（M3）—— 三档数据、重写 Table 2 + abstract headline | **< 1.5 h wall-clock** | **高（兑现自我承诺）** |
| **4** | **Minimal detector block**（M4）：retry-feature AUC + $\widehat{B}_{\mathrm{TV}}$ histogram + (可选) fastText AUC | **< 4 h** | **高（兑现 §7.6/§7.9 承诺）** |
| **5** | **扩样**（M2）三选一：主基线 n ≥ 100 / aligned slice per-method n ≥ 30 / 明确降级 short paper | **3–6 h 或重定位** | **高（决定 venue-fit）** |
| **6** | **Table 4 + §8.4 encode median 差异显式解释 + attempts_used 列**（M5 + M8） | **< 30 min** | **中（presentation）** |
| **7** | **Figure 1 TikZ 升级 + Figure 2 retry histogram**（M7） | **< 2 h** | **中（presentation）** |
| **8** | **JSONL schema cross-release consistency pass**（M9） | **< 30 min** | **中（reproducibility）** |
| **9** | **Minor writing issues 清洁**（§4 minor）—— 显式标 worst-case / 修 Pinsker cite / 统一 `\texttt` 风格等 | **< 1 h** | **低-中** |

**补齐项目 1–4 是进入 "可发表" 门槛的最小集合**。项目 5 是 venue 选择问题：若扩样到 n ≥ 100 则 main venue 可尝试；若保持当前体量则必须降级为 short paper / workshop。

---

## 7. Overall Assessment

### Strengths summary

- **Scope discipline**：全版最突出的优点。abstract、§1、§3、§7.6、§12.6、§13.1 逐级 self-downgrade，不用没有的证据说话。
- **协议层写法成熟**：§4–§5 encode/decode lifecycle、fail-closed 六类失败、bootstrap/body 分段、fingerprint 讨论、natural tail policy 都覆盖到位。
- **TV bound（§5.6）推导正确**；aligned slice (§8.4) 的 split claim 与 Table 4 数据链闭合；retry leakage (§7.9) 主动 self-expose。
- **Artifact 纪律延续**；aligned slice summary.json 是最完整的一处 provenance。

### Weaknesses summary

- **§7.4 KL 推导有一个在 $u > 0$ 连续区间失败的中间不等式**（M1）—— 最终 bound 正确，但中间步需要修复。
- **Empirical 体量不足**：主基线 n=18 / aligned slice per-method n=6，均不支撑 inferential claim（M2）。
- **四项 self-committed 实验未兑现**：$h_{\min}$ sweep（M3）、detector AUC + $\widehat{B}_{\mathrm{TV}}$ 相关分析 + retry trivially separating AUC（M4）。
- **两项分钟级 reproducibility fix 跨轮未补**：Qwen upstream provenance + llama.cpp commit SHA（M6）；前者字段已存在且值为 null，说明基础设施已就位但未接通。
- **Presentation gap**：Figure 1 信息密度不足，Figure 2 不存在，Table 4 缺 `attempts_used` 列，主/aligned 两个 release 的 encode median 37% 差异未在 Table caption 显式解释（M5、M7、M8）。

### Venue-fit matrix

| 目标场景 | 本版判断 | 补齐后潜在判断 |
|---|---|---|
| Security 顶会（S&P / USENIX Security / CCS） | **Clear Reject**：aligned slice n=6 远不足；detector-side 空白 | 即使补齐 M1-M7 仍不够，需要 n ≥ 100 baseline + detector AUC on ≥ 2 detectors |
| ML 顶会（NeurIPS / ICLR / ACL） | **Clear Reject**：$h_{\min}$ sweep 缺席；bits/token headline 在最激进 op-point | 补齐 M1-M5 后可作为 short paper；full paper 仍需 detector-side 证据 |
| Security / IH workshop（WOOT / IH&MMSec / ACSAC workshop） | **Borderline**，需要至少补 M1 + M6 | 补齐 M1-M6 后 **Borderline Accept** |
| Short paper / poster / demo track | **可投**，但 M1 和 M6 必须先补——M1 是技术严谨性底线，M6 是 reproducibility 底线 | 补齐后 **Accept** |

### Bottom line

**一个 scope-disciplined、诚实、协议工程写法成熟的 draft，但技术核心章节有一个 fixable 但必须修的推导错误，且关键 empirical commitment 全部未兑现。**

**最短可接受路径**（按时间顺序）：

1. **当天**：补 M1（改 $\chi^2$ bound 路线）+ M6（两项 metadata fix）。
2. **次日内**：跑 M3（$h_{\min}$ sweep）+ M4.1（retry trivially separating AUC）+ M4.2（$\widehat{B}_{\mathrm{TV}}$ histogram）。
3. **第三日**：Figure 2 生成 + Table 4 attempts_used 列 + Table 4 caption footnote（M5、M7、M8）。
4. **第四日**：根据 M2 选择：扩样（打主 venue）或显式降级 short paper。

合计 **3–4 个工作日**即可从当前 "Weak Reject" 推到 workshop-level 的 "Borderline Accept"；扩样到 n ≥ 100 + detector AUC on ≥ 2 detectors 后可推到 ML/security main venue 的 "Weak Accept"。

**推荐措辞**：

- 若作者下一轮补齐 M1 + M3 + M4 minimal + M6 + M7 五项 → **Borderline Accept** (workshop) / **Weak Accept** (short paper)。
- 若只补 M1 + M6（最便宜的两项）→ **Borderline Reject** (short paper OK, main venue 仍不够)。
- 若仅措辞调整不补实验、不修 KL 推导 → **Reject**。理由：(i) §7.4 的中间不等式是 sitting duck，会被任何 theoretical reviewer 在 30 秒内发现；(ii) staged-protocol 的承诺兑现率（当前 Stage 3/4/5/6 四项全 pending，Stage 4.5 仅 n=6 initial slice）不足以让 reviewer 对剩余阶段有信心。

**Confidence**：4/5。协议工程、approximation bound derivation、Cachin/Pinsker bridge、aligned slice 数据解读、KL 不等式技术检查均有把握（M1 数值验证已在本轮完成）。detector-side 效果因论文未提交实测数据无法深判——若作者认为当前版本已经具备 detector resistance，应在下一轮提供证据而非措辞。
