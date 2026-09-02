# PAQS v0.2 — Core Definition Lock
## Pivot → Zone → Regime → Failed Breakout → Retest → Follow-through

**Status:** Draft for user review; not yet an implementation contract  
**Purpose:** 将 PAQS v0.1 中最关键、最容易产生歧义的六个价格行为模块锁定为可编码、无未来函数、可回测的定义。  
**Design rule:** 把“语义规则”与“可调参数”严格分离。语义规则不能为了提高历史收益而改写；参数只能在预先声明的范围内通过 walk-forward 优化。

---

# 1. Definition Lock 的基本原则

本文件把所有规则分为三类。

## 1.1 FIXED — 语义固定规则

这些规则定义“这个概念到底是什么”，不得通过回测优化改变。

例如：

- Pivot 必须先确认后才能被策略使用。
- Failed Breakout 必须包含“越界 + 回收”，单纯触碰边界不算假突破。
- Retest 必须发生在 Breakout 之后。
- Follow-through 必须发生在 Trigger 之后，不能反向用未来 K 线证明过去信号。
- Market Regime 必须在 Setup 之前确定。
- 结构止损必须对应可明确描述的 invalidation level。
- 质量评分不是概率。

如果某个回测结果不好，不能把这些定义偷偷改掉。

## 1.2 TUNABLE — 可回测参数

这类参数只决定“多大才算有效”，例如：

- Pivot 反转幅度：1.2 ATR 还是 1.8 ATR
- Zone 聚类距离：0.4 ATR 还是 0.6 ATR
- Breakout buffer：0.1 ATR 还是 0.2 ATR
- Follow-through 确认窗口：2 根还是 3 根 K

它们必须：

1. 进入 Parameter Registry；
2. 有 default / min / max；
3. 只能在 walk-forward 中调；
4. 所有 backtest 保存 config hash。

## 1.3 VARIANT — 策略分支

有些差异不是参数，而是不同交易思想，必须分别回测。

例如：

- breakout immediately enter
- breakout + retest 才入场
- failed breakout reclaim 立即入场
- failed breakout + signal bar + follow-through 才入场

这些不能混在一起优化为一个模糊策略。

---

# 2. 时间与信息可用性

## 2.1 Bar 时点

对于时间周期 \(T\) 的 bar：

```text
bar t:
open_t
high_t
low_t
close_t
```

只有在该 bar 完成之后，`high_t / low_t / close_t` 才视为完整可知。

默认信号计算时点：

```text
DECISION_TIME(t) = bar t close
```

默认成交：

```text
ENTRY_TIME = next tradable bar open
```

## 2.2 Event Timestamp

每个事件至少保存：

```text
event_start_timestamp
event_confirmation_timestamp
```

例：

一个最高点可能出现在 10 月 1 日，但直到 10 月 4 日回撤达到阈值才确认为 Pivot High。

系统只能在 10 月 4 日之后使用该 pivot。

## 2.3 No-Lookahead Invariant

任何测试都必须满足：

```text
feature[t] = f(data <= t)
```

禁止：

```text
feature[t] = f(data > t)
```

---

# 3. ATR 标准化

所有跨资产价格距离优先转换为 ATR 单位。

\[
ATR_t = EMA(TR_t, n_{ATR})
\]

默认：

```text
n_ATR = 14
```

距离：

\[
D_{ATR}(P_1,P_2,t)
=
\frac{|P_1-P_2|}{ATR_t}
\]

ATR 不负责预测方向，仅负责：

- 去噪
- 距离归一化
- zone 宽度
- breakout buffer
- retest tolerance
- stop buffer
- volatility sizing

---

# 4. Pivot Engine — Definition Lock

## 4.1 目标

Pivot 不是“未来 N 根 K 线回看得到的局部最高/最低点”，而是实时可确认的 Swing Turning Point。

## 4.2 FIXED：Directional Change Pivot

系统维护两个状态：

```text
SEEK_HIGH
SEEK_LOW
```

### 4.2.1 从 Confirmed Pivot Low 开始

状态：

```text
SEEK_HIGH
```

维护：

\[
CandidateHigh_t
=
\max(H_i)
\]

以及该最高点对应时间。

当收盘价从该 candidate high 向下回撤达到：

\[
CandidateHigh_t - C_t
\ge
\lambda_{pivot}\cdot ATR_t
\]

则在 bar t 收盘后确认：

```text
PIVOT_HIGH
```

Pivot price：

```text
candidate_high_price
```

Extreme timestamp：

```text
candidate_high_timestamp
```

Confirmation timestamp：

```text
t
```

然后状态切换：

```text
SEEK_LOW
```

### 4.2.2 从 Confirmed Pivot High 开始

维护：

\[
CandidateLow_t
=
\min(L_i)
\]

当：

\[
C_t-CandidateLow_t
\ge
\lambda_{pivot}\cdot ATR_t
\]

确认：

```text
PIVOT_LOW
```

随后切换到 `SEEK_HIGH`。

## 4.3 为什么确认使用 Close 而不是 Intrabar Low/High

FIXED：

反转阈值使用收盘确认。

原因：

- 日线/小时线 OHLC 无法知道 bar 内先创新高还是先暴跌；
- 使用 close 降低 wick noise；
- 更符合“等待 K 线确认”的右侧思想；
- 便于跨市场一致回测。

Extreme 仍然使用真正的 High/Low。

## 4.4 TUNABLE：Pivot Threshold

```text
pivot_atr_lambda
default = 1.5
range   = [1.0, 2.5]
```

大于 2.5 ATR 会过度稀疏；小于 1 ATR 容易把噪声识别成 swing。

## 4.5 TUNABLE：Minimum Pivot Separation

为了避免一两根 K 反复确认：

```text
pivot_min_bars
default = 2
range   = [1, 5]
```

若反转阈值已满足但距离上一 pivot 不足，则继续等待。

## 4.6 Hierarchy

V0.2 允许同一时间周期建立两个层级：

```text
MICRO_PIVOT
MAJOR_PIVOT
```

其中：

```text
micro lambda default = 1.0 ATR
major lambda default = 1.8 ATR
```

但两者是不同实例，不允许事后把 micro 升级成 major 并回写历史。

用途：

- Major Pivot：Regime / Range / Structural Stop
- Micro Pivot：Trigger / micro LH break / micro HL break

## 4.7 Swing Label

只有 confirmed pivots 参与。

设最近两个 confirmed highs：

\[
H_{i-1}, H_i
\]

最近两个 confirmed lows：

\[
L_{i-1}, L_i
\]

定义结构容差：

\[
\epsilon_s = k_s ATR
\]

### HH

\[
H_i > H_{i-1} + \epsilon_s
\]

### LH

\[
H_i < H_{i-1} - \epsilon_s
\]

### EH — Equal High

\[
|H_i-H_{i-1}| \le \epsilon_s
\]

低点同理：

```text
HL
LL
EL
```

TUNABLE：

```text
structure_equal_tolerance_atr
default = 0.25
range   = [0.10, 0.50]
```

## 4.8 Pivot Acceptance Tests

### Case P1

上涨过程中创新高，随后只回撤 0.6 ATR。

Expected：

```text
NO PIVOT HIGH CONFIRMATION
```

### Case P2

随后回撤达到 1.5 ATR。

Expected：

```text
PIVOT HIGH CONFIRMED NOW
```

不得把 confirmation timestamp 写成最高点当天。

### Case P3

最高点后同一 bar 高低波动超过阈值，但 close 仍在高位。

Expected：

```text
NO CONFIRMATION
```

---

# 5. Zone Engine — Definition Lock

## 5.1 核心思想

Support / Resistance 是价格区域，不是假定精确到一分钱的水平线。

Zone 必须由市场真实重复反应形成，而不是人为随意画。

## 5.2 Zone Candidate

每个 confirmed major pivot 都创建一个 candidate observation：

```text
pivot_type
pivot_price
pivot_timestamp
confirmation_timestamp
atr
timeframe
```

## 5.3 FIXED：同类 Pivot 聚类

High pivots 只能直接构成 resistance candidate。

Low pivots 只能直接构成 support candidate。

Role Flip 后才能转换角色。

## 5.4 Zone Distance

两个 pivot 可视为同一价格区：

\[
\frac{|P_i-P_j|}
{Median(ATR_i,ATR_j)}
\le
\epsilon_{zone}
\]

TUNABLE：

```text
zone_cluster_epsilon_atr
default = 0.50
range   = [0.25, 0.90]
```

## 5.5 FIXED：独立 Touch

同一区域连续相邻 K 线反复擦边不能算多个有效测试。

两次 touch 必须至少间隔：

```text
zone_min_touch_separation_bars
```

TUNABLE：

```text
default = 5 STF bars
range   = [3, 20]
```

## 5.6 Candidate / Confirmed

### Candidate Zone

```text
valid_touch_count = 1
```

### Confirmed Zone

FIXED：

```text
valid_touch_count >= 2
```

Range boundary 的要求更高，见 Regime 部分。

## 5.7 Zone Center

使用确认 pivot 价格的加权中位数：

\[
Center =
WeightedMedian(P_i,w_i)
\]

权重：

```text
timeframe_weight × rejection_strength
```

V0.2 默认：

```text
same-timeframe weight = 1
higher-timeframe observation = 1.5
```

这些权重属于 TUNABLE，但建议 V0.2 暂时固定不优化，防止过拟合。

## 5.8 Zone Width

计算：

\[
MAD =
Median(|P_i-Center|)
\]

\[
HalfWidth =
\max(
MAD,
k_{min}\cdot ATR
)
\]

同时：

\[
HalfWidth
\le
k_{max}\cdot ATR
\]

TUNABLE：

```text
zone_min_halfwidth_atr = 0.15
range = [0.10, 0.30]

zone_max_halfwidth_atr = 0.75
range = [0.50, 1.00]
```

最终：

```text
zone_low  = center - halfwidth
zone_high = center + halfwidth
```

## 5.9 Role Flip

FIXED：

Resistance 被有效向上突破后，不立即变成 Support。

必须经历至少：

```text
BREAKOUT_CONFIRMED
```

之后才建立：

```text
POTENTIAL_SUPPORT_FLIP
```

如果随后 retest 并 hold：

```text
CONFIRMED_SUPPORT_FLIP
```

向下对称。

## 5.10 Zone Decay

旧 zone 不应永久有效。

TUNABLE：

```text
zone_max_age_bars
default = 250 STF bars
range   = [100, 500]
```

但更高周期 zone 可以单独配置更长寿命。

如果旧 zone 仍被新 touch 使用，age reset 到最后一次有效 reaction。

## 5.11 Zone Merge

若两个 confirmed zones 重叠超过：

\[
IoU \ge threshold
\]

则可 merge。

TUNABLE：

```text
zone_merge_iou
default = 0.50
range   = [0.30, 0.70]
```

Merge 必须生成新 `zone_version`，旧定义保留用于审计。

---

# 6. Range Construction — Definition Lock

Range 不是“看起来横盘”。

## 6.1 Preconditions

必须同时存在：

```text
confirmed support zone
confirmed resistance zone
```

且：

\[
ResistanceLow > SupportHigh
\]

## 6.2 FIXED：最少有效反应

默认语义：

```text
support touches >= 2
resistance touches >= 2
```

并要求 touch 在时间上交错，而不是所有 highs 在一边、所有 lows 在另一段。

推荐至少形成：

```text
H-L-H-L
or
L-H-L-H
```

类型的结构序列。

## 6.3 Inside Ratio

设 lookback N：

\[
InsideRatio =
\frac{
\#\{C_i \in [RangeLow,RangeHigh]\}
}{N}
\]

TUNABLE：

```text
range_lookback_bars
default = 40
range   = [20, 80]

range_inside_ratio
default = 0.70
range   = [0.60, 0.85]
```

## 6.4 Range Width

\[
RangeWidthATR =
\frac{ResistanceCenter-SupportCenter}
{MedianATR}
\]

必须：

```text
min_range_width_atr <= RangeWidthATR <= max_range_width_atr
```

TUNABLE：

```text
min_range_width_atr = 2.0
range [1.5, 4.0]

max_range_width_atr = 12.0
range [8.0, 20.0]
```

上限主要防止把两个无关结构强行连成“箱体”。

---

# 7. Regime Engine — Definition Lock

## 7.1 状态枚举

V0.2 固定为：

```text
BULL_TREND
BEAR_TREND
RANGE
BULL_TRANSITION
BEAR_TRANSITION
UNCERTAIN
```

`EXPANSION` 作为属性，不作为一级 regime，避免状态过多。

另保存：

```text
volatility_state
channel_state
```

## 7.2 FIXED：Bull Trend

最低结构定义：

最近 Major Pivot 序列满足：

```text
HH + HL
```

且：

```text
price has not closed below the major HL invalidation zone
```

为了降低一次微小 break 导致误判，正式 `BULL_TREND` 还要求：

```text
至少一个 HH 已被确认
AND
至少一个 HL 已被确认
```

如果只有：

```text
旧 Bear Trend 被打破
但 HH-HL 尚未完整
```

则进入：

```text
BULL_TRANSITION
```

## 7.3 Bear Trend

完全对称：

```text
LH + LL
```

## 7.4 FIXED：Range 优先条件

如果一个已确认 Range 仍有效，且价格尚未完成有效 structural breakout：

```text
regime = RANGE
```

不能因为箱体内部出现几个小周期 HH-HL 就标成 Bull Trend。

这对应价格行为中的重要原则：

> 区间内部的小趋势不能自动推翻大区间定性。

## 7.5 Range → Bull Transition

触发：

```text
close breaks above resistance zone
```

进入：

```text
BULL_TRANSITION
```

只有进一步满足以下任一确认路径，才进入 BULL_TREND。

### Path A — Follow-through confirmation

```text
breakout
→ bullish follow-through
→ no close back into invalid zone
```

### Path B — Retest confirmation

```text
breakout
→ retest
→ hold
→ new continuation high
```

## 7.6 Bear Trend → Bull Transition

至少发生：

```text
break last major LH zone
```

但在完成：

```text
new HL + subsequent HH
```

之前，保持 `BULL_TRANSITION`。

## 7.7 Hysteresis

FIXED：

Regime 不允许因为一根边界 K 来回跳。

TUNABLE：

```text
regime_confirmation_bars
default = 2
range   = [1, 4]
```

这不是简单要求两根阳线，而是确认状态必须持续满足 invalidation-free 条件。

## 7.8 Regime Precedence

固定顺序：

```text
1 INVALID DATA
2 ACTIVE CONFIRMED RANGE
3 CONFIRMED BULL/BEAR TREND
4 TRANSITION
5 UNCERTAIN
```

但 confirmed range 在完成 structural breakout 后立即进入 transition，不再继续压制新状态。

---

# 8. Breakout Engine — Definition Lock

虽然本轮核心是 Failed Breakout，但必须先定义 Breakout。

## 8.1 Bullish Break Attempt

FIXED：

只要：

\[
H_t > ZoneHigh
\]

就产生：

```text
BREAK_ATTEMPT_UP
```

注意：Attempt ≠ Breakout。

## 8.2 Bullish Breakout

必须：

\[
C_t >
ZoneHigh + b_{close}\cdot ATR_t
\]

TUNABLE：

```text
breakout_close_buffer_atr
default = 0.15
range   = [0.05, 0.35]
```

## 8.3 Quality Attribute

记录但不作为语义条件：

```text
body_ratio
close_location
range_atr
relative_volume
```

用于 Quality Score 和研究。

## 8.4 Structural Breakout

只有突破：

```text
major zone
or
major swing level
```

才称：

```text
STRUCTURAL_BREAKOUT
```

突破 micro pivot 只能叫：

```text
MICRO_BREAK
```

---

# 9. Failed Breakout — Definition Lock

这是 PAQS 的核心事件之一。

## 9.1 事件与交易 Setup 必须分开

FIXED：

```text
FAILED_BREAKOUT_EVENT
```

只说明突破失败。

它不是自动买卖信号。

交易需要：

```text
Failed Breakout
+
Context
+
Trigger
+
RR
```

## 9.2 Failed Breakdown — Bullish Event

以 support zone 为例。

### Stage 1 — Excursion

价格向下越界：

\[
L_t <
ZoneLow - e_{min}\cdot ATR_t
\]

TUNABLE：

```text
failed_break_min_excursion_atr
default = 0.10
range   = [0.00, 0.40]
```

如果设置为 0，任何下破都算 excursion；建议初始 0.10 去除单 tick noise。

### Stage 2 — Reclaim

在最多 W 根 bar 内：

\[
C_j >
ZoneLow + r_{buffer}\cdot ATR_j
\]

其中：

```text
j ∈ [t, t+W]
```

注意：

- 如果同一根 K 下影刺破后收回，可在 t 收盘确认 reclaim。
- 如果几天后才重新站回，则 confirmation timestamp = j。

TUNABLE：

```text
failed_break_reclaim_window_bars
default = 3
range   = [1, 5]

failed_break_reclaim_buffer_atr
default = 0.05
range   = [0.00, 0.20]
```

### Stage 3 — Event Confirmation

满足 excursion + reclaim：

```text
FAILED_BREAKDOWN_CONFIRMED
```

## 9.3 Failed Breakout Up — Bearish Event

完全镜像：

\[
H_t >
ZoneHigh + e_{min}ATR
\]

随后：

\[
C_j <
ZoneHigh - r_{buffer}ATR
\]

得到：

```text
FAILED_BREAKOUT_UP_CONFIRMED
```

## 9.4 Failure after Initially Valid Breakout

如果价格已经满足 breakout close，但在 `failed_break_window` 内重新收回区间，也允许定义：

```text
BREAKOUT_FAILURE
```

区别：

```text
FAKEOUT_WICK:
未形成有效 close breakout

BREAKOUT_FAILURE:
曾形成有效 close breakout，随后失败
```

必须分别记录。

TUNABLE：

```text
breakout_failure_window_bars
default = 3
range   = [1, 5]
```

## 9.5 Failed Breakout Invalidation

Bullish failed breakdown 事件形成后，如果价格随后：

```text
close < failed_break_extreme - buffer
```

则：

```text
FAILED_BREAK_SETUP_INVALIDATED
```

这里的 buffer：

```text
failed_break_stop_buffer_atr
default = 0.10
range   = [0.05, 0.30]
```

## 9.6 Failed Breakout Quality Features

保存：

```text
excursion_atr
reclaim_speed_bars
reclaim_close_location
reversal_bar_body_ratio
volume_ratio
distance_to_opposite_zone
rr_to_opposite_zone
```

用于后续研究，不改变事件定义。

---

# 10. Retest — Definition Lock

## 10.1 FIXED：Retest 必须发生在 Breakout 后

不存在：

```text
先 retest
后 breakout
```

那只是普通 support/resistance test。

## 10.2 Bullish Retest Start

已存在：

```text
STRUCTURAL_BREAKOUT_UP
```

随后价格回落至旧 resistance 的 expanded zone：

\[
L_t
\le
OldZoneHigh + \tau_{outer}ATR_t
\]

并且：

\[
H_t
\ge
OldZoneLow - \tau_{inner}ATR_t
\]

即 bar 与 retest band 有重叠。

TUNABLE：

```text
retest_outer_tolerance_atr
default = 0.25
range   = [0.10, 0.50]

retest_inner_tolerance_atr
default = 0.20
range   = [0.05, 0.40]
```

## 10.3 Retest Window

TUNABLE：

```text
retest_max_window_bars
default = 15
range   = [5, 30]
```

超过后不再称为“该次突破的第一次 retest”。

## 10.4 Retest Hold

FIXED：

Retest 不能仅凭“碰到了”就判断成功。

需要：

1. Retest start；
2. 没有发生 structural invalidation；
3. 后续出现重新向 breakout 方向的 trigger。

Bullish：

```text
Retest touched old resistance
AND
no decisive close below retest failure boundary
AND
micro LH is broken or bullish trigger bar confirms
```

则：

```text
RETEST_HOLD_CONFIRMED
```

## 10.5 Retest Failure

若 bullish breakout 后：

\[
C_t <
OldZoneLow - f_{retest}ATR_t
\]

则：

```text
RETEST_FAILED
```

TUNABLE：

```text
retest_failure_buffer_atr
default = 0.15
range   = [0.05, 0.35]
```

## 10.6 Multiple Retests

固定记录：

```text
retest_number = 1,2,3...
```

默认策略优先只交易：

```text
retest_number == 1
```

是否允许第二次 retest 属于 VARIANT，必须单独回测。

---

# 11. Trigger — Definition Lock

Follow-through 必须有 trigger 作为参考，因此在此先锁定 Trigger。

## 11.1 Trigger 类型

V0.2 使用两个核心 trigger：

```text
MICRO_STRUCTURE_BREAK
STRONG_SIGNAL_BAR
```

不允许仅凭 RSI / MACD 触发。

## 11.2 Micro Structure Break

Bullish：

最近 confirmed micro pivots 显示小周期仍为：

```text
LH / LL
```

当：

\[
C_t >
MicroLHPrice + b_{micro}ATR_t
\]

得到：

```text
BULL_MICRO_STRUCTURE_BREAK
```

TUNABLE：

```text
micro_break_buffer_atr
default = 0.05
range   = [0.00, 0.15]
```

## 11.3 Strong Bull Signal Bar

候选：

\[
C_t > O_t
\]

\[
BodyRatio_t \ge B_{min}
\]

\[
CLV_t \ge CLV_{min}
\]

\[
Range_t/ATR_t \ge R_{min}
\]

TUNABLE：

```text
signal_body_ratio_min
default = 0.60
range   = [0.50, 0.75]

signal_clv_min
default = 0.75
range   = [0.65, 0.90]

signal_range_atr_min
default = 0.80
range   = [0.50, 1.20]
```

但 FIXED：

Strong Signal Bar 只有发生在有效 Context / Location / Setup Stage 才能成为交易 trigger。

---

# 12. Follow-through — Definition Lock

“没有跟随”是公开 Price Action 语言里非常重要的判断。

## 12.1 定义对象

Follow-through 必须针对明确的 prior event：

```text
breakout
trigger bar
failed breakout reclaim
```

不能脱离 context 单独存在。

## 12.2 Bullish Follow-through

设 Trigger bar 为 t，Trigger High 为 \(H_t\)。

在最多 W 根完整 bar 内，只要出现某个 j：

\[
C_j >
H_t + f_{ext}ATR_j
\]

同时截至 j 没有发生 setup invalidation：

```text
FOLLOW_THROUGH_CONFIRMED
```

TUNABLE：

```text
followthrough_window_bars
default = 3
range   = [1, 5]

followthrough_extension_atr
default = 0.10
range   = [0.00, 0.30]
```

## 12.3 Bearish Follow-through

对称：

\[
C_j <
L_t - f_{ext}ATR_j
\]

## 12.4 No Follow-through

如果在 W 根内没有满足 extension：

```text
FOLLOW_THROUGH_NONE
```

但这本身不是立即反向交易信号。

## 12.5 Follow-through Failure

如果 trigger 后先发生反方向 structural invalidation，再发生 extension：

```text
FOLLOW_THROUGH_FAILED
```

即 invalidation 优先。

## 12.6 Follow-through Strength

额外记录：

\[
FTDisplacementATR =
\frac{
MaxDirectionalClose - TriggerClose
}{ATR}
\]

以及：

```text
bars_to_followthrough
close_persistence
body_persistence
```

这些属于 scoring feature，不改变语义。

---

# 13. 六模块依赖关系

固定依赖：

```text
ATR
 ↓
Pivot
 ↓
Zone
 ↓
Regime
 ↓
Breakout / Failed Breakout / Retest
 ↓
Trigger
 ↓
Follow-through
 ↓
Setup
 ↓
RR
 ↓
Trade Decision
```

禁止：

```text
先生成 Buy
再回头寻找 structure 解释
```

---

# 14. Core State Machines

## 14.1 Right-Side Breakout

```text
RANGE
  ↓
BREAK_ATTEMPT_UP
  ↓
BREAKOUT_CONFIRMED
  ↓
BULL_TRANSITION
  ├───────────────┐
  ↓               ↓
FOLLOW_THROUGH    RETEST_START
  ↓               ↓
TREND_READY       RETEST_HOLD
                  ↓
               TREND_READY
```

### Conservative Variant

```text
只允许 RETEST_HOLD → ENTRY
```

### Moderate Variant

```text
FOLLOW_THROUGH 或 RETEST_HOLD → ENTRY
```

两者必须分别回测。

## 14.2 Failed Breakdown Long

```text
RANGE / SUPPORT_CONTEXT
  ↓
DOWN_EXCURSION
  ↓
RECLAIM
  ↓
FAILED_BREAKDOWN_CONFIRMED
  ↓
BULL_TRIGGER
  ↓
FOLLOW_THROUGH
  ↓
RR CHECK
  ↓
LONG_READY
```

## 14.3 Trend Pullback Long

```text
HTF BULL_TREND
  ↓
STF CORRECTION
  ↓
SUPPORT / OLD BREAKOUT ZONE
  ↓
MICRO BEAR STRUCTURE
  ↓
MICRO LH BREAK
  ↓
FOLLOW_THROUGH
  ↓
RR CHECK
  ↓
LONG_READY
```

---

# 15. Fixed vs Tunable Summary

| Item | Type | Default | Search Range / Rule |
|---|---|---:|---|
| Pivot uses confirmation timestamp | FIXED | — | 不可优化 |
| Pivot reversal uses close | FIXED | — | 不可优化 |
| `pivot_atr_lambda` | TUNABLE | 1.5 | 1.0–2.5 |
| `pivot_min_bars` | TUNABLE | 2 | 1–5 |
| Equal high/low tolerance | TUNABLE | 0.25 ATR | 0.10–0.50 |
| Zone requires repeated reaction | FIXED | ≥2 touches | 不可改成单点 zone |
| `zone_cluster_epsilon_atr` | TUNABLE | 0.50 | 0.25–0.90 |
| `zone_min_touch_separation_bars` | TUNABLE | 5 | 3–20 |
| Range requires support + resistance | FIXED | — | 不可优化 |
| Range min alternating reactions | FIXED | 2+2 | 不可删除 |
| `range_inside_ratio` | TUNABLE | 0.70 | 0.60–0.85 |
| Regime before setup | FIXED | — | 不可优化 |
| Active range suppresses internal micro-trend | FIXED | — | 不可优化 |
| Break attempt uses wick crossing | FIXED | — | 不可优化 |
| Breakout requires close outside buffer | FIXED | — | buffer 可调 |
| `breakout_close_buffer_atr` | TUNABLE | 0.15 | 0.05–0.35 |
| Failed breakout = excursion + reclaim | FIXED | — | 不可优化语义 |
| `failed_break_reclaim_window_bars` | TUNABLE | 3 | 1–5 |
| Retest only after breakout | FIXED | — | 不可优化 |
| `retest_max_window_bars` | TUNABLE | 15 | 5–30 |
| Retest hold needs new directional trigger | FIXED | — | 不可仅“碰到” |
| Follow-through occurs after trigger | FIXED | — | 不可回写 |
| `followthrough_window_bars` | TUNABLE | 3 | 1–5 |
| `followthrough_extension_atr` | TUNABLE | 0.10 | 0–0.30 |
| RR is hard gate | FIXED | — | 阈值可调 |
| Quality score != probability | FIXED | — | 永久原则 |

---

# 16. 参数优化限制

## 16.1 禁止全空间暴力搜索

不允许：

```text
20 个参数 × 20 个候选值
```

然后挑历史最赚钱组合。

## 16.2 分层优化

建议顺序：

### Layer 1 — Geometry

```text
pivot
zone
range
```

目标不是收益，而是与人工标注结构一致。

评价：

```text
pivot match
zone distance
regime accuracy
```

### Layer 2 — Event

```text
breakout
failed breakout
retest
follow-through
```

目标：

```text
event precision / recall
```

### Layer 3 — Trading

最后才优化：

```text
minimum_rr
entry variant
stop buffer
```

评价：

```text
expectancy
profit factor
max drawdown
```

这可以避免为了赚钱把“结构定义”调得面目全非。

---

# 17. Hand-Labeled Dataset Specification

下一阶段在编码前/编码初期建立 Gold Set。

## 17.1 每个案例至少标记

```text
symbol
market
timeframe
as_of_timestamp

major_pivots
micro_pivots

support_zones
resistance_zones

regime

breakout_events
failed_breakout_events
retests
triggers
followthrough

setup_type
setup_stage

invalidation_level
```

## 17.2 严格 As-Of 标注

标注者只能看到：

```text
data <= as_of_timestamp
```

不能用后面的走势决定当时是否是底部。

## 17.3 第一批目标

建议：

```text
120 cases
```

分布：

```text
30 Bull Trend
20 Bear Trend
30 Range
20 Transition
10 Failed Breakout
10 True Breakout + Retest
```

之后扩大到 300+。

---

# 18. Core Unit Test Matrix

## T01 — Pivot No Lookahead

Expected：

```text
extreme at t
confirmation at t+3
strategy cannot use pivot before t+3
```

## T02 — Range Internal Micro Trend

箱体内部连续产生 micro HH-HL。

Expected：

```text
regime = RANGE
not BULL_TREND
```

## T03 — Wick Fakeout

Low 低于 support 0.2 ATR，但收盘回到 zone 内。

Expected：

```text
DOWN_EXCURSION
RECLAIM
FAILED_BREAKDOWN_CONFIRMED
```

## T04 — True Breakdown

Close 跌破 zone 0.4 ATR，随后 3 bar 继续创新低。

Expected：

```text
BREAKDOWN_CONFIRMED
FOLLOW_THROUGH_CONFIRMED
not FAILED_BREAKDOWN
```

## T05 — Breakout Failure

先 close 突破 resistance，2 bar 后重新收回。

Expected：

```text
BREAKOUT_CONFIRMED
then BREAKOUT_FAILURE
```

不能删除第一个事件。

## T06 — Retest Hold

Breakout → 回踩旧 resistance → 不破 → micro LH break。

Expected：

```text
RETEST_START
RETEST_HOLD_CONFIRMED
```

## T07 — Retest Failure

Breakout → 回踩 → close 明确回到旧区间深处。

Expected：

```text
RETEST_FAILED
```

## T08 — No Follow-through

Strong bull trigger 后 3 根 bar 横盘，无一根 close 超过 trigger high。

Expected：

```text
FOLLOW_THROUGH_NONE
```

## T09 — Follow-through

第二根 K 收盘超过 trigger high + buffer。

Expected：

```text
FOLLOW_THROUGH_CONFIRMED at second bar
```

## T10 — Structure Good, RR Bad

Expected：

```text
NO_TRADE
reason = INSUFFICIENT_RR
```

---

# 19. 决策：哪些规则现在锁定，哪些暂不锁死

## 19.1 现在锁定

以下进入 PAQS 核心语义，不再讨论是否存在：

1. Confirmed directional-change pivot
2. HH/HL/LH/LL + equal tolerance
3. Zone 是 pivot cluster，不是单点
4. Range 优先于其内部 micro trend
5. Break Attempt 与 Breakout 分离
6. Failed Breakout = 越界 + 回收
7. Retest = breakout 之后的回测
8. Retest Hold 必须再次向突破方向触发
9. Follow-through 必须在 trigger 之后确认
10. Transition 是一级必要状态
11. RR 是 hard gate
12. Event 与 Trade Setup 分离
13. Signal Ledger 不覆盖历史状态
14. Quality Score 不冒充 Probability

## 19.2 现在不锁死数值

以下全部保持 H/TUNABLE：

```text
pivot ATR threshold
zone width
zone clustering threshold
range inside ratio
breakout buffer
failed-break excursion distance
reclaim window
retest tolerance
follow-through window
follow-through extension
signal bar geometry
minimum RR
stop ATR buffer
```

## 19.3 必须作为独立 Variant

```text
breakout immediate entry
breakout + follow-through entry
breakout + retest entry

failed-break reclaim entry
failed-break trigger entry
failed-break trigger + follow-through entry

partial take-profit
no partial take-profit
```

禁止在一个回测里动态挑选哪个看起来更好。

---

# 20. 与公开交易语言的映射

程序概念对应人工语言：

| 人工语言 | PAQS |
|---|---|
| “现在定性还是区间” | `regime = RANGE` |
| “大周期多头趋势” | `HTF = BULL_TREND` |
| “顺大逆小” | `HTF trend + STF correction + TTF reversal` |
| “能突破再说” | `BREAKOUT / RIGHT_SIDE_CONFIRMATION` |
| “信号K” | `STRONG_SIGNAL_BAR / TRIGGER` |
| “大阴线没有跟随” | `FOLLOW_THROUGH_NONE` |
| “假突破” | `FAILED_BREAKOUT_EVENT` |
| “跌破就跑路” | `STRUCTURAL_INVALIDATION` |
| “区间交易” | `RANGE setup family` |
| “1小时突破做多” | `TTF structural break trigger` |
| “走一步看一步” | `TRANSITION / reduced confidence` |
| “always-in / 窄通道” | 后续 channel module |

---

# 21. Definition Lock 结论

当前 PAQS 的核心不再是“哪些指标权重更高”，而是明确形成以下计算顺序：

```text
Confirmed Pivot
      ↓
Support / Resistance Zone
      ↓
Regime
      ↓
Break Attempt / Breakout / Failed Breakout
      ↓
Retest
      ↓
Trigger
      ↓
Follow-through
      ↓
Setup Qualification
      ↓
Structural Stop
      ↓
Structural Target
      ↓
RR Gate
      ↓
Signal
```

V0.2 的关键原则是：

> **几何结构参数可以回测，但 Price Action 语义不能为了历史收益而漂移。**

这将使后续代码既能够优化，也不会优化到最后变成一个完全不同的策略。

---

# 22. 下一工程步骤

Definition Lock 经确认后，下一步应创建正式 Task Contract，范围只覆盖：

```text
Phase PA-1: Structure Foundation
```

建议只实现：

1. ATR / candle primitives
2. Directional-Change Pivot Engine
3. Swing labels
4. Incremental Zone Engine
5. Range detection
6. Regime state machine
7. No-lookahead tests
8. Synthetic unit tests
9. Signal/structure debug output

**暂时不实现：**

```text
Failed Breakout trading
Retest trading
Follow-through trading
Position sizing
Probability
UI
Live trading
```

原因是必须先证明机器能够稳定“看懂结构”，再进入交易逻辑。

---

**End — PAQS v0.2 Core Definition Lock**