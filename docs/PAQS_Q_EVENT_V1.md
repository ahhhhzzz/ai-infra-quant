# PAQS-Q Event reference v1 — 规则与使用

本轮用户明确恢复 TASK-006C-Q，采用以下参考约定，直接实现，不新增审批层级。
这是一版正式 F1 协议插件，不是市场有效性证明或完整 PAQS-Q。
正式 Setup/Risk、交易资格、LONG_READY、收益计算、产品 API/UI/数据库均不在范围内。

## 结构与身份

当前显式绑定为 `paqs-q-event-context-reference@1.0.1` 与
`paqs-q-event-reference@1.0.1`。1.0.0 的固定提交与清单保留作历史证据，当前 loader
不再注册该版本。
复用旧 `paqs_structure.py` 的纯 ATR/Pivot/Swing/Zone/Range 算法；它们保持研究参考含义，
初始化等待、历史起点敏感性没有被解决。B0/A1、旧 manifest 和包初始化文件不修改。
新 loader 保持默认 B0、Event 未配置；只有显式 ID/version 才运行新插件，B0 不具备
上下文 capability 时拒绝 Event，不自动换插件。新 manifest 覆盖完整项目内导入依赖。

固定参数：ATR 14 TR 均值播种、EMA α=2/15；Micro λ=1、Major λ=1.8；
收盘反转 ≥λATR，极值早于确认，极值间隔 ≥2，同价保留最早，初始化双向成立则等待。
Swing 容差 0.25ATR，等号 EH/EL。Zone 同类 Major complete-link ≤0.50ATR，
触碰极值间隔 ≥5，至少两次才确认；中心简单中位数，半宽
min(max(MAD,0.15×参考ATR),0.75×参考ATR)，同角色确认 Zone IoU≥0.50 按旧稳定规则合并。
最后有效触碰确认后超过 250 bars 不再开启新事件。Range 两侧各至少两触碰、
至少四组交错反应；40 根 ATR-ready 窗口，inside ratio≥0.70，宽度 [2,12] ATR。
多候选按触碰数降序、inside ratio 降序、宽度升序、稳定 ID 升序。

来源为确认 Zone、活动 Range 的上下边界和每侧最新 Major Swing（点区间，不称 Zone）。
上行使用 resistance/high，下行使用 support/low；Range 边界与同一底层 Zone 按 Zone 身份
去重，保留 Range 归属。来源在该 bar 开始前已确认才可使用，逐前缀计算并冻结版本、
区间和支持引用；不从最终结构快照回填历史。W1/D1/M30 分别计算，不合成多周期资格。
外侧价格周期在首次 Attempt 冻结来源；轻微外侧收盘导致 Range 暂不活动时，后续有效
Breakout 仍保留该周期的原 Range 归属。已开启周期不因来源更新/过龄而移动锚；新周期
必须使用当时仍可用的来源。收盘回边界内且无待回收 excursion 后，下一 bar 才重启。

## 六类事件

下表为上行，空头完全镜像。A 为当前完成 bar 的 ATR，[L,U] 为冻结来源。
严格 `>`/`<` 的等号不成立；`≥`/`≤` 的等号成立。区间窗口包含端点。

| 类别 | 固定首版规则 |
|---|---|
| Attempt / Breakout | H>U 每来源/方向/bar 一条 Attempt；C>U+0.15A 确认 Breakout。同一外侧 excursion 只确认一次；首次激活已在外侧不补造突破，C≤U 后最早下一 bar 重启。 |
| Failed Break | 下探 Low<L−0.10A 后，C>L+0.05A 为 bullish reclaim；窗口 [e,e+3]，可同根回收；重复 excursion 不重置期限，确认前累计极值。上探回落为 bearish 镜像。 |
| Breakout Failure | 已有效突破时仅在 [b+1,b+3] 检查相反回收；上破失败为 C<U−0.05A，下破失败镜像。保留 Breakout，失败不重复归类 wick fakeout。 |
| Retest | [b+1,b+15] 内 Low≤U+0.25A 且 High≥L−0.20A 开始；C<L−0.15A 或父 Breakout Failure 优先失败。Start 之后另一 bar 的同向 Micro/Strong 候选且 C>U 才 Hold；不使用最初 Event Confirmation 自证。无 Start 的窗口可到期但不捏造 Start；末根失败/确认先于过期。Hold 后另有一根 C>U+0.25A，随后再次触碰才递增编号，期限不重置。 |
| Transition | 活动 Range 上破，或 BEAR_TREND 的最后 Major LH 被 C>LH+0.15A 突破，进入 BULL_TRANSITION。两条路径都要突破后新极值的 Major HL→HH；Range 还要突破候选的 FT CONFIRMED，或 Retest Hold 后另一根 C>High_b+0.10A。结构已知后连续两根条件成立才确认趋势；失效优先取消，恢复仍有效原 Range，否则当时 Major 状态/UNCERTAIN。相同方向突破不重置，无任意超时。 |
| Trigger | 最近 Micro 为 LH/LL 且 C>MicroLH+0.05A；或 C>O、实体/振幅≥0.60、CLV≥0.75、振幅/A≥0.80。空头 HH/HL 镜像、CLV≤0.25；零振幅不 Strong。同一 Micro Pivot 首次有效越界才记录。同锚/方向/bar 合并原因。无锚为 PRICE_PATTERN、有有效锚为 PRICE_TRIGGER_CANDIDATE；突破/reclaim 可附 EVENT_CONFIRMATION 原因。 |
| Follow-through | 候选 q 后 [q+1,q+3]，绑定事件未失效且 C>High_q+0.10A 首次 CONFIRMED；先失效 FAILED；末根无延伸 NONE，此前 PENDING。终态不可改写，后来事件失效单独记录；缺 bar 不当作到期。 |

Breakout/Retest 的 event_guard 为冻结 L 和当前 0.15A；bullish failed breakdown 的
event_guard 为冻结 excursion 最低点和当前 0.10A。空头镜像。guard 不叫交易止损。
同一时点：输入错误 → 失效 → 正向确认 → 窗口过期。只记录完成 OHLC 的价格事实，
不推断盘中顺序。同一有效事件锚的所有候选各自保留 FT 生命周期，不据此输出交易建议。

## 数据与时间约定

使用固定输入起点；调整起点、历史价格/版本/日历变更产生不同计算来源。F1 record_id
绑定完整输入/结果；另设稳定 event_key 及来源版本关联生命周期。PENDING 与后续终态
是各自时间的事实，追加未来只添加事实，不改旧事实。输出原始输入 hash、配置、代码、
上游结构结果 hash 和支持版本引用。

AS_OF 默认且不降级：保留 QInput.problem、F1 价格校验、实际可知时间及调整证据要求。
逐 bar 历史回放要求用于该收盘判断的价格/日历当时已知；延迟提供或缺失的历史证据
返回 INSUFFICIENT，不把晚得数据倒填成当时确认。OBSERVATIONAL 必须显式选择，
始终 strict_confirmation=false，按同版本前缀计算位置并保留历史时点/当前复权限制。
1.0.1 对 D1/M30 连续性证明中实际用到的中间闭市日，也要求其日历事实最迟在后续
第一根依赖该事实的 bar 完成时可知；否则返回 INSUFFICIENT。合法周末、假日、午休
和 W1 的事实完成时刻按原有规则处理。OBSERVATIONAL 不获得历史可知性认证。
非合成 AS_OF 输入还须提供 `provenance.historical_evidence` 的三个非空证据引用：
`price_versions`、`adjustment_as_of`、`calendar_versions`。`POINT_IN_TIME_ADJUSTED`
标签本身不充分；必须保留可核查的原始历史档案。这是声明及时间一致性校验，工具不
联网认证档案真实性。SYNTHETIC 的严格标志仅表示合成事实满足校验，不代表真实市场验证。
ATR 为零时价格不等式仍按 A=0 判断，Strong 的振幅/ATR 比值不可计算、不会生成 Strong；
ATR 组件标为未就绪，不以零充当有效波动率。

无 bar/历史证据不足为 INSUFFICIENT；非法输入为 INVALID；可计算但无事件为 AVAILABLE
且空事件列表。ATR/Micro/Major/Zone/Range 逐组件报告准备度；缺 Zone 不抹掉价格形态。
缺少已列入日历的预期 bar 则全次返回 INSUFFICIENT，不跳过、不填造、不推进期限。
Event 的每根 bar 先以先前已确认的结构处理失效、突破和 Transition，再用当前完成
收盘价重评这份先前已知的 Major/Range，输出该根结束时的 regime。当前根新确认的
结构不参与其开始前决策；有效趋势若被当前收盘击穿，输出 UNCERTAIN，不滞后一根。
D1/M30 可正常跨隔夜、午休、假日；M30 桶本身不可跨午休。W1 使用日历事实完成时刻，
名义周末只是区间几何。AS_OF 要求完整日历；明确的 OBSERVATIONAL 可按提供的交易日
清单核对，未列日期不构成完整性证明；缺少周内日历证据不得认证 W1 完成。

来源：本轮用户明确采用的公式为本版权威；[v0.2](research/PAQS_V0.2_CORE_DEFINITION_LOCK.md)
提供参数和价格事件定义，[v0.3.1](research/PAQS_V0.3.1_COMPLETENESS_LOCK.md)及
[Amendment A](research/PAQS_V0.3.1_REVIEW_AMENDMENT_A.md)提供完成时间、调整及冻结边界原则。
上述输入、候选与 event_guard 的工程约定不把历史研究、价格候选或 FT 解释为 Setup/Risk。

## Windows 运行与查看

在仓库目录、已有 Python 3.12 环境中运行（依赖不变）：

```powershell
$env:PYTHONPATH = "src;."
python -m tools.research.event_engine --demo --output data/event-demo-new
Start-Process data/event-demo-new/report.html
```

真实观察样本使用原 qstr 行情和 capture-calendar 文件，显式选择 OBSERVATIONAL：

```powershell
$env:PYTHONPATH = "src;."
python -m tools.research.event_engine --input ../task006b-q-data/US.AVGO.D1.json --calendar ../task006b-q-r04-source/capture-calendar.json --mode OBSERVATIONAL --output data/avgo-event-new
Start-Process data/avgo-event-new/report.html
```

输出目录必须尚不存在，防止覆盖旧输入/报告。运行失败/证据不足退出码为 2，若已形成
F1 结果，仍输出原因供查看；不会自动降级。`report.html` 内嵌全部数据，不依赖 CDN 或
网络，可过滤类别/状态、点击事件定位 K 线并查看 event_key、冻结来源、guard 和关联证据。
`input.json` 为实际 QInput，`structure.json`/`events.json` 是精确 F1 canonical 结果，
`summary.json` 包含参数、配置/代码摘要、模式、数据限制和事件状态计数；全部 UTF-8/LF。
数字均以十进制字符串导出，图形坐标转为浏览器数值只用于绘图。

本地输入支持两种现成格式：

- `qstr-observations-v1` 配套 capture-calendar（保留 FULL/MORNING_ONLY/AFTERNOON_ONLY
  session segments，不把 retrieval time 当历史 available_at，不补闭市日期）。
- F1 `paqs-q-input-v1` 完整 payload：包含 security_id/market/currency/timezone/timeframe、
  as_of/qualification_mode/quality、bars/calendar/provenance；bar 提供完成/可知时间及
  Decimal OHLCV 字符串、复权依据和版本引用。导出的 `input.json` 即可作为可复制样例。
  内含日历时不再传 `--calendar`，CLI 模式须与 payload 一致；W1、D1、M30 均支持。

F1 接入使用新增 `application.paqs_q_event_artifacts.load_event_registry(root)`，显式调用
`registry.structure(data, "paqs-q-event-context-reference", "1.0.1")`，再将同一 QInput
及该结果传给 `registry.event(data, structure, "paqs-q-event-reference", "1.0.1")`。
闭合 schema 位于新增 `core/domain/paqs_q/event_reference.py`；F1 record 顶层不扩字段。
上下文 evidence 保留每根 bar 的准备度及前缀来源版本，事件 evidence 为追加式时间事实。

当前 manifest 为 `event-context-1.0.1.json`、`event-event-1.0.1.json`；覆盖项目内传递依赖、
包初始化文件以及原 B0/A1 和 Event 1.0.0 manifest 的身份。1.0.1 的 series/event_key
与 1.0.0 分离。`tools/validation/paqs_q_event.py --write-artifacts` 只创建当前版本的新清单，
拒绝覆盖已有文件。原 Event 1.0.0 固定提交和清单保留；当前 loader 对显式旧版本
返回 UNKNOWN_PLUGIN_VERSION，不冒充原结果，也不重生成 B0/A1 清单。
