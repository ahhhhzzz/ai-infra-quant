# PAQS-Q 单形态研究 v1

本轮用户授权优先交付独立、离线的研究闭环；完整 Event Context/六类 Event 方案暂缓。
本文同时固定本实验规则和使用方式，不新增审批合同。单标的 D1 做多；不连接账户、
模型或订单，不更新产品 PaperFill/持仓。不是正式 Event、Setup/Risk 或 LONG_READY。

## 固定规则（实现前记录）

形态：**局部高点突破 → 首次回踩 → 后续强阳线确认**，ID `local-high-retest-v1`。

- 复用 F1 `local.raw` 的纯价格不等式及 B0 的 prior-raw veto/双向排除：中心 j 的
  高点严格高于 j−1/j+1，且 H[j]−C[j+1] ≥ H[j−1]−L[j−1] > 0；前中心无任一 raw。
  需要 j−2..j+1 四根完整连续日线；最早 j+1 收盘才可知，j+2 才能用于突破。
  **这是 B0 算术的新的实验用途，不是 B0 插件结果或完整 Major/Micro/Confirmed Zone**。
  不复制其 312 根窗口或日历证书身份；保留 F1 算法、版本、身份和证据。
- 只跟踪最新已确认局部高点 P；新点替换未突破点；突破后冻结 P 和来源。
  ATR 复用旧纯函数 EMA14（首 14 个 TR 均值，后续 α=2/15）。不足 14 根不发信号。
- 突破：前收盘 ≤ P，当前 C > P+0.15 ATR；严格大于，等号不成立。
- 回踩：突破后第 1..15 根，L ≤ P+0.25 ATR 且 H ≥ P−0.20 ATR。
- 确认：首次回踩之后另一根完成日线，C>P、C>O、实体/振幅≥0.60、
  (C−L)/振幅≥0.75、振幅/ATR≥0.80，且仍在突破后第 15 根以内。
  失败优先：窗口内 C<P−0.15 ATR 则取消；末日先判断，再过期。零振幅不确认。
- P 只是点价位。上述 ATR 缓冲、15 根窗口、强信号比例来自
  [v0.2 第 8/10/11 节](research/PAQS_V0.2_CORE_DEFINITION_LOCK.md)。把点代替 Zone、
  前收盘穿越、延后一根确认，以及下列完整成交规则均为**新增研究假设**，不是原始 PAQS Setup。
- 同一局部点只消费一次突破机会（失败/过期/成交均不重置）；一次只观察一个回踩。
  完成或取消后等待之后新确认的点；不回溯选择旧点。信号流与资金/持仓独立计算；
  持仓期信号保留在报告但不排队、不加仓，退出当日收盘的新信号可供下一日。
- 信号收盘冻结止损 S=min(首次回踩至信号所有 Low)−0.15 ATR(signal)。S≤0 则取消。
  下一行必须是日历中的下一交易日；下一开盘若 O≤S 或 O≤P，取消入场。
  否则按 O×(1+滑点) 买入。样本末信号保留 PENDING_NEXT_OPEN，不造下一根。
- 固定初始止损不放宽；目标=实际入场价+2×(入场价−S)。止损/目标为盘中触价假设。
  已持仓开盘≤S 按开盘卖出；开盘≥目标按目标卖出（不计有利跳空）；否则先判断
  Low≤S，再判断 High≥目标，同根两者都到时止损优先；入场当根也同样检查。
  卖出均乘 (1−滑点)，触价相等算成交。盘中成交只记录所在 bar 和时段，不伪造精确时刻。
  持有 20 根完成日线后安排下一开盘退出；该开盘止损跳空优先。没有下一根则仍为未平仓。
- 默认初始资金 100000、每次使用可用现金 95%、整股/手数单位 1、单边费率 0.001、
  单边滑点 0.0005、目标 2R、最大持有 20 根；均可配置，无杠杆、无做空。
  成交量限制/最低佣金/税费/停牌涨跌停/股息现金流不模拟，不保证真实成交。
  数量向下取整，费用包含于预算，资金不足不成交。金融计算 Decimal，精度 50，
  中间值遵循复用 ATR 的 18 位量化，成交金额不额外伪装成券商分币规则。
- 权益=现金+股数×收盘；包括初始资金点，回撤=1−权益/历史最高权益。
  未平仓不强制末日平仓，总收益包含未实现损益但不虚计末日卖出费用。
  胜率分母仅已平仓交易，无已平仓时为 null；报告显示已平仓/未平仓/总入场次数。
  同期买入持有在第一根开盘买入，使用相同资金比例、费用、滑点、手数，末日同样按市值；
  不含股息，不是 total-return benchmark，起始投资时间与策略暖机不同。

## 输入与数据限制

复用现有 `qstr-observations-v1` 本地 JSON（D1）和 006B1 日历导出；另支持普通 UTF-8 CSV。
CSV 每行字段：`security,start,end,open,high,low,close,volume,completed,coverage,adjustment`。
时间必须含 UTC offset；start 为常规开盘、end 为完成收盘；completed 必须 `true`，
coverage 必须 `COMPLETE`。价格/成交量为有限十进制文本，OHLC 合法、同标的、按日递增，
同一时区市场日唯一、同一复权基准；不接受混合/未知/缺失复权标识或重复版本。
JSON 保留原始 provenance/时间/哈希，不将 retrieved_at 改成历史 available_at。

必须提供日历：006B1 `capture-calendar.json` 或 CSV `date,open,close`（含 offset）。
日历为**预期交易日清单**，须覆盖输入首末日，每行开收盘必须与 K 线一致；
若日历存在某交易日而 K 线缺失，整个运行报错；不填造、不跨缺口成交。
非交易日不用列入；用户必须提供完整清单。归档日历本身不完整认证时会显著提示，
只能核对已知清单，不把“未发现缺口”说成完整性证明。不允许由 OHLC 行自动推断完整日历。
未完成/坏行直接拒绝，不静默删行；先在导出端明确选择已完成、同版本日线。

本入口始终是 `EXPLORATORY_NOT_POINT_IN_TIME`（合成样例另标 SYNTHETIC）。
按行前缀模拟完成时序，无未来价格/枢轴回填，但不认证真实历史版本/复权可知时间。
已知 available_at 晚于历史收盘也会作为限制计数展示，而非绕过 F1 AS_OF。
研究输出绑定输入文件 SHA256、配置、代码摘要及原始结构支持行；追加数据不改变既有信号。
当前 QFQ 历史数量为复权价格下的名义模拟股数，不还原真实拆股账户路径。

## Windows 使用

在任务 worktree 根目录，用已安装本仓库依赖的 Python 3.12：

```powershell
python -m tools.research.single_pattern --demo --output data/single-pattern-demo
Start-Process data/single-pattern-demo/report.html
```

现成本地真实样本（该文件不随仓库发布）：

```powershell
python -m tools.research.single_pattern --input ../task006b-q-data/US.AVGO.D1.json --calendar ../task006b-q-r04-source/capture-calendar.json --output data/avgo-single-pattern
Start-Process data/avgo-single-pattern/report.html
```

普通 CSV 增加 `--timezone America/New_York --currency USD`（HK 可用 Asia/Hong_Kong/HKD）。
`--help` 列出资金、成本和规则参数。无网络/CDN，无 OpenD/数据库/模型调用；
HTML 可离线直接打开，配套 `results.json`、`trades.csv`、`signals.csv`、`equity.csv`。
输出目录必须不存在，避免覆盖先前研究。图表数字转换仅用于绘图，金融结果来自 Decimal。
真实样本不存在时用 demo 验证程序，不能声称真实市场验证完成。

## 固定风险预算仓位对照 v1（2026-09-22）

原命令默认仍为 `--sizing-mode cash`，资金比例、信号和成交规则不变。
新增仓位配置独立于原 `Config`，不进入 signal_id 的生成；不修改局部点、事件、
信号止损、取消条件、2R 目标、持有期限或成本假设。它是单形态研究扩展，不是正式 Setup/Risk。

在持仓为空、下一开盘满足原入场条件时，使用**买入前现金（即当时权益）**计算：

- E=开盘×(1+买滑点)，S=信号已经冻结的止损，P_stop=S×(1−卖滑点)。
- f=原单边费率；每股计划净损失 L=E×(1+f)−P_stop×(1−f)，必须有限且大于零。
- B=买入前权益×risk_fraction；风险允许手数为 floor(B/(L×每手股数))。
- 现金允许手数仍为 floor(现金×allocation/(E×(1+f)×每手股数))。
- 两者取小值，整手向下取整。RISK/CASH/BOTH 表示风险/现金/两者股数上限相同；
  零股数分别记录 ZERO_RISK_QUANTITY、INSUFFICIENT_CASH 或 ZERO_CASH_AND_RISK_QUANTITY。
  不借款、不移动止损、不用当天尚未知晓的收盘权益。

`risk_fraction` 必须是 (0,1] 内有限 Decimal，显式非法值直接拒绝。
本轮仅使用用户预先指定的 **0.01**，不是优化结果或投资建议；计划风险不是最大损失保证，
跳空实际亏损可超过预算。cash 模式没有风险预算（null），但对照中仍显示其计划止损损失。
买入持有始终使用原 allocation、费用、滑点、手数；没有策略止损、不套用 fixed-risk，
不代表两者承担相同风险。

Windows Python 3.12，在仓库根目录用一条命令读取同一份行情和日历，运行两种模式：

```powershell
python -m tools.research.single_pattern --input ../task006b-q-data/US.AVGO.D1.json --calendar ../task006b-q-r04-source/capture-calendar.json --sizing-mode compare --risk-fraction 0.01 --output data/avgo-risk-comparison-v1
Start-Process data/avgo-risk-comparison-v1/report.html
```

目录必须不存在；复跑请选择新目录，不覆盖 v1 或输入。没有本地行情时，以 `--demo`
替代 `--input` 和 `--calendar`，输出明确标为 SYNTHETIC。
`--sizing-mode fixed-risk --risk-fraction 0.01` 可单独运行风险模式；默认 cash 下传入
`--risk-fraction` 会拒绝，避免静默忽略。对照不修改两种模式共享的信号配置。

`report.html` 可离线打开，展示两种模式的权益曲线、指标、逐笔计划风险和实际结果，
支持切换显示原买入持有曲线。`results.json` 保留精确 Decimal 文本；`summary.csv`、
`trades.csv`（包括未平仓）、`equity.csv`、`decisions.csv`（包括跳过原因）、`signals.csv`
可逐项核对。HTML 金额/比例为两位显示，精确值以导出为准；图形转换仅用于绘图。
计划及实际损益比例的分母均为该笔入场前权益。未平仓只报告截至末日的未实现损益，
不虚计卖出费用；总费用为所有已发生的入场费用与已平仓退出费用。
输出代码摘要包含新增研究文件，与 v1 旧摘要不同；F1/B0/A1 身份未变。
本次 Windows 运行和指定 AVGO 对照见[实现报告](reports/PAQS_Q_RISK_SIZING_COMPARISON_V1.md)。
