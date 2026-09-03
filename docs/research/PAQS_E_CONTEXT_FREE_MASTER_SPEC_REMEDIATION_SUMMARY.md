# PAQS-E Context-Free Master Spec — Focused Remediation Summary

**Status:** RESEARCH REVIEW SUPPORT DOCUMENT  
**Implementation authority:** NONE  
**Remediated file:** `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md`  
**Reviewed baseline:** `64f522f041f430470770c7b90dae0a84746fec65`  
**Independent review:** `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_STRATEGY_REVIEW.md` @ `9f644326f643d9497d6cd05c0ba3006fbe5bb125`

本次 remediation 的目标是：**只修复会让不同 LLM 因合同歧义而产生无意义分歧的运行时语义，不推翻 PAQS-E Naked Price Action 骨架，不增加新的核心 Setup family，不启动任何 implementation。**

保留的核心链：

```text
CONTEXT
→ STRUCTURE
→ KEY LEVEL
→ LOCATION
→ EVENT
→ TRANSITION
→ SETUP
→ TRIGGER
→ FOLLOW-THROUGH
→ STRUCTURAL INVALIDATION
→ STRUCTURAL TARGET
→ RR / ENTRY QUALITY
→ ENTRY ADVISORY + HOLDER ADVISORY
```

保留的初始 Setup families：

```text
A. 趋势回调延续 / 顺大逆小
B. 区间/关键支撑失败突破反转
C. 右侧结构突破
```

---

## F-01 — Current Analysis vs Historical Replay Adjustment Semantics

**Resolution: RESOLVED**

新增显式：

```text
analysis_mode = CURRENT_ANALYSIS | HISTORICAL_ASOF_REPLAY
```

锁定：

- `CURRENT_ANALYSIS` 可使用明确披露且跨周期一致的 current-adjusted 数据，例如 `PROVIDER_QFQ_CURRENT`；
- `historical_replay_safe = false` 只表示不能把当前复权序列冒充严格历史 replay，不是当前分析自动失败理由；
- `HISTORICAL_ASOF_REPLAY` 必须 point-in-time safe；若不安全则 `UNSUPPORTED + INVALID + DATA_UNAVAILABLE`，不得声称严格 As-Of replay。

---

## F-02 — Partial Data Degradation Policy

**Resolution: RESOLVED**

新增 degradation matrix，分别处理：

- W1 不可靠；
- D1 不可靠；
- M30 不可靠/缺失；
- latest quote / current price 不可用；
- calendar/session metadata 部分缺失；
- adjustment provenance warning；
- 跨周期 adjustment inconsistency。

同时明确 canonical 边界：

```text
DATA_UNAVAILABLE = 数据/支持不足，无法安全判断
UNCERTAIN = 数据可用，但价格行为证据冲突
WATCH_LONG / WATCH_SHORT = 候选存在但确认不足
ENTRY_PENDING_REVALIDATION = Setup 已确认但 executable entry / final RR 未完成
NO_TRADE = 分析有效后，策略硬条件明确失败
```

`DATA_UNAVAILABLE` 与 `NO_TRADE` 不再混用。

---

## F-03 — Current Price Reference vs Executable Entry Reference

**Resolution: RESOLVED**

正式拆分：

```text
CURRENT_PRICE_REFERENCE
EXECUTABLE_ENTRY_REFERENCE
```

`CURRENT_PRICE_REFERENCE` 只是观察事实，可来自 stale/delayed/pre/post/closed reference。

`EXECUTABLE_ENTRY_REFERENCE` 必须满足外部 Runtime Configuration 的：

- session policy；
- freshness policy；
- market/session metadata；
- extended-hours permission；
- as-of alignment。

`LONG_READY` 明确要求合法 Executable Entry Reference + final RR revalidation。缺失时必须：

```text
ENTRY_PENDING_REVALIDATION
```

---

## F-04 — Semantic Zone vs Numeric Calculation Reference

**Resolution: RESOLVED**

Structural Invalidation 和 Target 均拆分为：

```text
semantic level/zone
calculation reference
```

例如：

```text
invalidation_level_or_zone
invalidation_calculation_reference

t1_level_or_zone
t1_calculation_reference
```

锁定：

- semantic zone 不因数学需求被强迫成虚假精确单点；
- calculation reference 必须与 semantic geometry 有明确关系；
- 必须在 RR 前选定；
- 随 Decision Ledger 冻结；
- 禁止为了改善 RR 后移；
- 无可信 numeric reference 时 `rr_status = NOT_COMPUTABLE`，不得 `LONG_READY`。

---

## F-05 — Holder Advisory Basis

**Resolution: RESOLVED**

新增：

```text
holder_advisory_basis =
CURRENT_ANALYSIS_THESIS
| PRIOR_DECISION_ID
| NOT_AVAILABLE
```

初始 fresh/stateless Analyze 默认：

```text
CURRENT_ANALYSIS_THESIS
```

含义仅为：

> 如果持有者是基于本次 PAQS-E 当前识别出的 Thesis 持有，这个 Thesis 现在是否仍有效？

禁止隐藏聊天记忆、猜测用户原入场逻辑或反推成本。

未来仅在显式传入 immutable prior decision 时允许 `PRIOR_DECISION_ID`。

---

## F-06 — Strategy Portability vs Runtime-Approved Scope

**Resolution: RESOLVED**

明确：

```text
Strategy portability != Runtime-approved scope
```

Runtime Configuration 至少外部提供：

```text
supported_market_scope
supported_instrument_scope
HTF/STF/TTF mapping
short_execution_allowed
extended_hours_entry_reference_allowed
entry_reference_policy
quote_freshness_policy
optional versioned RR / ATR guardrails
```

LLM 禁止看图后临时换周期或执行权限。

当前推荐 v1：

```text
US / HK
EQUITY
W1 / D1 / M30 REGULAR
short_execution_allowed = false
extended_hours_entry_reference_allowed = false
```

短线做空未授权时仍可识别 Bearish Context，但不得输出 actionable `SHORT_READY`。

---

## F-07 — Canonical Output Vocabulary

**Resolution: RESOLVED**

新增并整理 machine-readable canonical fields：

```text
support_status
input_quality
market_bias
avoid_long_flag
entry_advisory
holder_advisory_basis
holder_advisory
rr_status
```

关键 canonical enums 包括：

```text
support_status = SUPPORTED | UNSUPPORTED
input_quality = COMPLETE | PARTIAL | INVALID
rr_status = FINAL | PENDING_ENTRY_REFERENCE | NOT_COMPUTABLE
```

清理：

- 删除 `SHORT_BIAS / AVOID_LONG` 复合状态；改为 `market_bias` + `avoid_long_flag`；
- `POOR_ENTRY` alias 不再使用，只保留 `VALID_SETUP_BUT_POOR_ENTRY`；
- `OK / PARTIAL / UNAVAILABLE` 不再混在一个 data_quality 文本字段；
- `DATA_UNAVAILABLE`、`UNSUPPORTED`、`INVALID` 分属不同概念字段；
- 一个字段禁止 `"A / B"` 斜杠复合 enum。

---

# Non-blocking clarifications

## R-01 — Location / Target sequencing

**Disposition: ADOPTED**

Location 只评价当前价格相对 Context / Structure / Key Levels / 当前可见最近障碍的位置。

正式 T1/T2 后选；最终 Entry Quality 再结合 Target/RR 对 Location 做升级/降级。

---

## R-02 — “可复现”措辞

**Disposition: ADOPTED**

不再暗示 LLM bit-for-bit deterministic。

改为：

```text
可审计
可比较
受版本控制
可进行重复运行稳定性评估
```

严格可核验的 identity 是 Snapshot、Doctrine、Prompt、Model/provider/request config、Runtime Config、Validator 与 Decision Ledger。

---

## R-03 — Participant-intent narratives

**Disposition: ADOPTED**

将“吸筹式结构”“被套盘逻辑”等改为价格行为描述：

```text
筑底 / 反复承接 / 压缩式价格结构
失败突破后部分参与者可能受困的情形
```

隐藏参与者意图只能作为明确不确定的解释性假设，不能作为 Market Snapshot 事实。

---

## R-04 — User-provided charts

**Disposition: ADOPTED**

明确区分：

```text
Standalone / Manual Reasoning
Product Runtime
```

Product Runtime 只接受 product-controlled immutable Market Snapshot；未来图表必须由同一 `snapshot_hash` 数据/cutoff 确定性生成。

---

## R-05 — SETUP_EXPIRED

**Disposition: ADOPTED**

禁止 LLM 自创统一 N-bar expiry。

允许原因：

```text
PRICE_EXTENDED_OPPORTUNITY_MISSED
SETUP_GEOMETRY_REPLACED
STRUCTURE_INVALIDATED
RUNTIME_CONFIG_EXPIRY
```

---

# 未采纳项

**None.**

Review 中 F-01 ~ F-07 与 R-01 ~ R-05 的方向均被采纳。实施方式尽量保持语义层约束，没有把 PAQS-E 改写为 PAQS-Q deterministic state machine。

---

# 仍然存在但不属于本轮 blocker 的策略开放项

以下保持为有意的版本化/研究开放项，不应由 LLM 临时决定：

1. 具体 `R_min` 是否存在及其值；
2. ATR invalidation buffer 是否启用及具体参数；
3. 各 Setup 是否要求 Follow-through、Retest 或不同 entry variant；
4. quote freshness 的具体秒数/分钟数；
5. future short-side Runtime 是否开放；
6. future A-share / ETF runtime scope 与 timeframe mapping；
7. PAQS-E semantic Key-Level 判断在不同模型间仍可能有合理差异——这是 LLM-native strategy 的研究对象，不应通过机械阈值消灭；
8. T1/Invalidation numeric reference 的最终 validator 细节属于后续产品/runtime contract，不改变本文件的策略语义；
9. prior-decision holder management 模式尚未成为当前 runtime 功能；
10. Gold Set 和 repeated-run stability 的具体 acceptance threshold 尚需独立评审/治理。

这些开放项不妨碍本文件作为 **runtime semantic authority candidate** 接受 focused re-review，因为它们都已被明确放到外部版本化配置、未来 scope 或后续 validator 层，而不是留下隐式 Runtime ambiguity。

---

# Remediation self-assessment

本轮没有：

- 新增第四个核心 Setup family；
- 删除或弱化 Context / Structure / Key Level / Location / Event / Transition / Setup / Trigger / Follow-through；
- 把 PAQS-E 转成 deterministic Pivot/Zone state machine；
- 引入 PAQS-Q 机械规则作为 PAQS-E 隐藏权威；
- 修改 Roadmap / Requirements Matrix；
- 修改 Product code；
- 修改 TASK-006B2 / TASK-007A；
- 启动 OpenAI integration 或 Codex implementation。

**Recommended final status:**

```text
PASS_CANDIDATE
```

含义：Master Spec 已解决已知 blocking runtime semantics，适合进入一次独立 focused re-review，以判断是否正式提升为 PAQS-E runtime semantic authority。`PASS_CANDIDATE` 不等于 implementation approval。
