# PAQS-Q Setup/Risk 1.0.0 — 规则与本地使用

当前任务分支的 1.0.1 整改修正 Range Breakdown→Failure 的精确父事件关联，以及迟到
EntryReference 的历史消费时间和 SetupFact 身份；参数及下文 1.0.0 规则来源不变。
详见 [S01/S02 整改报告](reports/TASK_006D_Q_SETUP_RISK_V1_REMEDIATION_01.md)。

本版是用户授权的首个**做多资格**参考 profile，不是交易执行、收益验证或完整 PAQS-Q。
规则优先级为本轮任务指令、已整合 Event 1.0.1、明确采用的 v0.2/v0.3.1/Amendment A。
以下时钟、去重、目标聚类和 Gap 期限为本轮新增工程约定，未经市场优化。

## 多周期和时间

W1 为 Context、D1 为 Setup、M30 REGULAR 为 Trigger，三份独立 QInput 保留原 F1
身份；每周期显式运行 `paqs-q-event-context-reference@1.0.1` 和
`paqs-q-event-reference@1.0.1`。Setup/Risk 有独立 1.0.0 schema、配置/代码 hash 和
上游结果绑定，不写入 F1 的 STRUCTURE/EVENT records。标的、市场、币种、模式、
复权种类及来源版本必须相容；观察模式也不允许混合价格尺度。只选判断时已经完成且
可用的 W1/D1/M30 前缀；当前部分 W1 永不参与确认。缺周期、历史可知时间或复权证据
不得自动降级。OBSERVATIONAL 只能形成带明确限制的观察性资格，不称历史已知的
`LONG_READY`。

同一来源的重叠日历事实须为同一版本；W1/D1、D1/M30 均须有重叠的完成收盘可作
价格尺度检查。同一时刻的收盘价容许不超过 2% 的跨周期来源差异，以容纳不同粒度
的收盘观测；超出则拒绝。这是输入兼容工程约定，非策略参数。W1 仅剔除最后单根
未完成周并保留该动作的原因码；若已完成 W1 过旧（超过下一周窗口）则不使用旧状态。

## Setup 与生命周期

| family / variant | 创建条件 | 冻结 B / buffer |
|---|---|---|
| `TREND_PULLBACK_LONG / SUPPORT_ZONE` 或 `OLD_RESISTANCE_RETEST` | W1 BULL_TREND；D1 非 Bear/Bear Transition；完成 D1 `close < previous close` 且区间触及**触碰前已确认**的支撑 Zone，或同样触及有 D1 Retest HOLD 证据的旧阻力支撑区。随后 M30 必须是 bullish MICRO，Strong 单独不够。`close < previous close` 是本轮工程约定。 | 支撑区下边界 / 0.15 D1 ATR |
| `RANGE_FAILED_BREAKDOWN_LONG / RECLAIM` | W1 RANGE；D1 有已确认 Range；同一冻结 Range 下边界的 bullish FAILED_BREAK 或 BREAKOUT_FAILURE，冻结 excursion 最低点。 | excursion 最低点 / 0.10 D1 ATR |
| `RIGHT_SIDE_BREAKOUT_LONG / FOLLOW_THROUGH` | W1 BULL_TREND、RANGE 或 BULL_TRANSITION；D1 已确认阻力 Zone 或 Range 上边界有效 BREAKOUT；该突破**确认候选**的 D1 FT CONFIRMED。 | 原来源下边界 / 0.15 D1 ATR |
| `RIGHT_SIDE_BREAKOUT_LONG / RETEST` | 相同 W1/来源要求；该 D1 突破的 RETEST HOLD。与 FT 独立记录、关联同一突破。 | 原来源的 Retest Failure 边界（下边界）/ 0.15 D1 ATR |

单个 Major 点不能变成确认 Zone/Range Setup。每个 Setup 冻结来源、创建时刻、
原事件及变体；重复触碰不重置期限。创建日记为 D1 bar `i`，有效至第 `i+15`
个预期交易 D1 日（含端点）；第 `i+16` 日第一根 REGULAR M30 开始前到期。
RETEST 另受原 Breakout `b+15` 限制，以较早期限为准。日历缺失或预期 bar 缺失
返回证据不足，不能把缺口当时间没有流逝。每个状态事实追加，终态不回写；后续
合格 trigger 使用新候选 key。D1 硬失效先于确认，到期同刻确认优先。

每个有效 Setup 可以绑定其创建之后的 M30 `PRICE_PATTERN` 或
`PRICE_TRIGGER_CANDIDATE`，要求 bullish MICRO/STRONG（Trend 仅 MICRO）。形成
独立 SetupTrigger，不伪造 Event anchor，也不把任意邻近 Event FT 当作它的 FT。
本层使用原 Event 公式，对该 trigger 的 High_q 在 M30 完成 bar `q+1..q+3`
验证 `close > High_q + 0.10 × ATR_current`；失效优先 FAILED，延伸首次 CONFIRMED，
末根无延伸 NONE，其余 PENDING。只有 FT CONFIRMED 才进入 Stage A。

## 风险和结构目标

冻结结构锚 `B` 不移动。仅 D1 完成收盘满足
`close < B - k × 当前完成 D1 ATR` 才硬失效；影线或 M30 软弱不等于硬失效。
每次入场评估使用当时最新已完成 D1 ATR，冻结
`S=B-k×ATR`、`R=E-S`、`RR_Tn=(Tn-E)/R`；要求 `S>0`、`R>0`、`T1>E`、
`RR_T1>=2.0`。它是结构价格风险，**非真实止损成交或最大损失保证**，不继承费用、
滑点、仓位或 1% 风险比例。

目标只收集当时已确认且有效的对侧 Range 边界、Major High、阻力 Zone、未填补
REGULAR_SESSION_OPEN_GAP。Zone 用先遇到的下边界；点位 lower=upper。
入场位于阻力区间内时直接阻断。候选按 effective lower price 排序，使用决策时
`0.25×D1 ATR` 容差做**完整直径**聚类（cluster 内最大/最小差不得超过容差，
不做链式传递）；保留所有来源，聚类有效价取最靠近入场的下边界。
T1 最近、T2 下一独立障碍；T1 RR 不足不能跳到 T2。无障碍为
`TARGET_UNAVAILABLE`，数据覆盖不足为 `TARGET_COVERAGE_INSUFFICIENT`，两者不混同。

Gap 仅指每个市场交易日第一个 REGULAR M30 开盘相对前一完整常规时段收盘，
不将 HK 午休视为新日。开盘前已知 D1 ATR 的 `0.25` 为最小 gap；调整/价格尺度
不相容不得识别。Gap 只在首根 M30 **完成并可用**后成立，不用日线最终 OHLC
冒充开盘时证据。下跳 gap 的未填补上方区间可作为阻力：原区间和已知最高回填价
分开保存，剩余下边界为已知回填最高价；全部填补为 FILLED，期限超过 15 个
预期 D1 交易日为 EXPIRED，部分填补为 PARTIALLY_FILLED。上跳 gap 只记为
支持/参考，不充作做多上方 T1。期限、非链式聚类和未填补边界均为本轮工程约定。
Range Failed Breakdown 的冻结来源若因短暂越界不再列为当前 active Range，仍用
原确认 Range 的对侧边界作为候选，并保留原版本；不以更远新 Range 替换来源。

## 两阶段 Entry

Stage A 在 M30 SetupTrigger 的 FT 确认时冻结 Setup、目标、结构失效来源和
收盘参考 E，计算 `indicative_rr`；输出 `ENTRY_PENDING_REVALIDATION`，
无有效 Setup 为 WATCH_LONG/NO_TRADE。绝不从下一开盘提前发 LONG_READY。
Stage B 只看 Stage A 后**第一根**预期 REGULAR M30 bar 的独立 `EntryReference`
（price、price_at、available_at、source、source_ref、security、adjustment）。需要
可信的开盘来源与相同价格依据，且
`available_at<=price_at`；整根 M30 完成后才有的 open 是迟到历史参考，不能回填
开盘资格。独立开盘事实与完整日历已知时，即使该 M30 bar 尚未收完，也可以只用
该开盘事实执行 Stage B；不读取未来 high/low/close。Stage B 用当时已知 D1/W1、
当前障碍和真实开盘 E 重算；原 T1 越过或
入场在其内部不换 T2，新近障碍必须纳入。结构仍有效而 RR 变差为
`VALID_SETUP_BUT_POOR_ENTRY / WAIT_RETEST`；硬条件失败为 NO_TRADE；全部通过才是
`LONG_READY`（OBSERVATIONAL 输出单独标记的观察性等价状态）。缺独立开盘证据
如实停在证据不足，不滚动跳到更晚开盘。

每条追加事实有 `entry_advisory`：前置/观察状态为 `WATCH_LONG`；Stage A 为
`ENTRY_PENDING_REVALIDATION`；最终可能为 `LONG_READY`、
`OBSERVATIONAL_LONG_QUALIFIED`、`VALID_SETUP_BUT_POOR_ENTRY` 或 `NO_TRADE`。
每条事实绑定 family、variant、来源、候选、所用 ATR/失效参考、目标与原因。
Setup 输出另外绑定全部 EntryReference 的 canonical hash；此层不产生成交或持仓。

本版固定参数：`minimum_rr=2.0`、`setup_max_age_d1_bars=15`、普通失效
`0.15×D1 ATR`、Failed Breakdown `0.10×D1 ATR`、目标聚类
`0.25×D1 ATR`、gap 最小 `0.25×前一已知 D1 ATR`。不优化、不扫描。

## Windows 使用

从仓库根目录在 Windows Python 3.12 环境运行。以下一条命令生成三个标注的
**合成**三周期正例；打开新目录的 `index.html`，点击事实可定位 D1/M30 K 线。

```powershell
$env:PYTHONPATH = 'src;.'
python -m tools.research.setup_risk --demo all --output data/setup-risk-demo-new
```

真实输入可分别提供 W1/D1/M30 的 F1 payload 或已有 qstr 文件及共享日历；
默认 AS_OF，观察数据必须显式 `--mode OBSERVATIONAL`。指定全新输出目录，避免
覆盖原 Event/研究报告。若有真实独立开盘事件，另传 `--entry-references opens.json`；
该 JSON 为数组，每项含 `price`（Decimal 字符串）、`price_at`、`available_at`
（均为带时区 ISO 时间）、`source=PROVIDER_OPEN_EVENT`、`source_ref`（独立事件
版本引用）、`security` 和 `adjustment`。缺该文件不会推断最终 M30 OHLC 的 open。
对仅拥有已完成 qstr 的即时开盘前缀，应提供正确 `as_of` 的 F1 canonical QInput；
不得把未来完成 bar 放进该前缀。实际 AVGO 命令、输入身份和阻断项见
[实现报告](reports/TASK_006D_Q_SETUP_RISK_V1_IMPLEMENTATION_REPORT.md)。
