# 固定风险预算仓位对照 v1 — 2026-09-22

状态：**IMPLEMENTED / WINDOWS VALIDATED / AWAITING FOCUSED REVIEW**。
任务分支 `task/paqs-q-risk-sizing-comparison-v1`，基线
`d1d669032a5eb32c2992e2323f9a22d7a21e9cbb`；未合并产品分支。
本报告记录本次 Codex 实际执行，不是独立审查或用户验收结论。
单形态 v1 原收尾不重开，历史报告及证据不改写。

## 实现与边界

新增独立 `SizingConfig`/`plan_entry`，沿用 Decimal 50 位上下文。
E、S、P_stop、L、B 及风险/现金整手上限按[使用说明](../PAQS_Q_SINGLE_PATTERN.md)计算。
预算取买入前空仓现金，不用当日收盘；非法值拒绝，零数量记录原因。
默认 cash 路径保留；新增 `fixed-risk` 和 `compare` 显式入口。
对照输出每笔计划损失、实际损益及其入场前权益比例、约束来源和跳过记录。
未平仓和实际费用单独处理，买入持有不应用固定风险算法。

代码/测试提交（真实对照执行时为干净工作树）：
`a72047e438da23ceadf4ead17f45c817ebfac067`。
规范化研究代码 SHA256：
`99020c7cb43aa57c37428d2f74273a265c0f1520231cbeacc48566fe03628019`。
此后提交仅补充文档。不是旧 v1 的 `a7b80eb4…` 摘要；输出保留逐文件摘要清单。

## 实际数据与一次运行

现成本地文件在执行前重新核对：

| 输入 | SHA256 |
|---|---|
| `../task006b-q-data/US.AVGO.D1.json` | `d060a2abc82dceb957c49e607f8308ef6a57bdf0dd291110c8d29a8256435160` |
| `../task006b-q-r04-source/capture-calendar.json` | `46c652b3062e4c6aeb43454dbcff5d8deb5f348639766b9e444b21116ebf6b2d` |

US.AVGO，1500 根 D1，2020-09-17 至 2026-09-08，USD。
`REAL_OBSERVATIONS / EXPLORATORY_NOT_POINT_IN_TIME`；当前 QFQ、原质量 PARTIAL，
1500 根历史可知时间未知、日历未经独立完整认证。没有新取行情或认证严格 PIT。

Windows worktree 根目录实际执行一次下列对照（退出码 0）：

```powershell
& ../task007c1-env/Scripts/python.exe -m tools.research.single_pattern --input ../task006b-q-data/US.AVGO.D1.json --calendar ../task006b-q-r04-source/capture-calendar.json --sizing-mode compare --risk-fraction 0.01 --output data/avgo-risk-comparison-v1
Start-Process data/avgo-risk-comparison-v1/report.html
```

第一行为实际计算命令；第二行是用户打开报告的命令，本次自动化通过 Chromium file URL
打开。通用安装环境可将解释器替换为有仓库依赖的 `python`（Python 3.12）。输出目录必须
不存在，复跑改用新目录。真实输入及本地输出不提交；旧 v1 报告和输入未覆盖。

## 结果（只比较预先指定的 1%，未扫描或优化）

初始资金 100000，allocation 0.95，单边费率 0.001，滑点 0.0005，每手 1；
信号规则、目标 2R、最大持有 20 根均为原值。

| 指标 | 原 cash | fixed-risk 0.01 |
|---|---:|---:|
| 最终权益（精确） | 91869.4809306673337332843103572 | 100501.279371210054069738639777475 |
| 总收益 | −8.130519% | +0.501279% |
| 最大收盘回撤 | 28.547655% | 3.952200% |
| 入场 / 平仓 / 未平仓 | 12 / 12 / 0 | 12 / 12 / 0 |
| 胜率 | 41.666667% | 41.666667% |
| 总费用（精确） | 2363.0424429701571148481324428 | 475.488687642813299369107747525 |

原模式与已有 `paqs-q-single-pattern-worktree/data/avgo-research-v1-final/results.json`
逐项核对：行情、Config、局部点/事件/信号、signal_id、全部原交易/决策/权益/summary
业务字段精确一致。对照新增风险字段及新代码摘要不要求等同旧元数据。
这次重新执行的是新对照中的 cash 路径，旧记录作为比较基准；未重跑旧源码研究。

两模式共享 12 个信号、止损及 12 笔入场，全部共同成交的时间、价格、目标、退出时段/原因
一致；没有仅单边成交或跳过的信号。fixed-risk 12 笔均由 RISK 上限决定：
数量依序为 `424,385,313,725,373,256,425,403,239,80,153,59`；cash 为
`2777,2660,2527,2205,1978,1773,1606,1176,1177,697,657,334`。
所有 fixed-risk 计划净止损 ≤ 该笔预算，现金非负；最大计划权益比例约 0.999983%。
数量与成本金额不同，改变净损益及权益，不改变信号或证明市场有效性。

原买入持有曲线完全一致：收益 +1022.873503%，最大收盘回撤 40.874275%，
首日按原 allocation/成本建仓，末日按市值，不含股息、没有策略止损；不是等风险对照。

## 本次验证

真实环境：Windows 11 build 26200，Python 3.12.14 AMD64，pytest 8.4.1，tzdata 2025.2，
Jinja2 3.1.6，Ruff 0.12.9，mypy 1.17.1，Playwright 1.55.0，Chromium 140.0.7339.16。
测试执行于提交前、与 `a72047e` 相同的代码和测试内容；真实 CLI/导出检查执行于该提交。

| 实际执行 | 结果 |
|---|---|
| `python -m pytest tests/research/single_pattern -q` | 23 passed，含原 15 项、新增 8 项（两个离线浏览器用例总计） |
| `python -m pytest tests/architecture/test_import_boundaries.py -q` | 3 passed |
| `python -m ruff check tools/research/single_pattern tests/research/single_pattern` | PASS，退出码 0 |
| `python -m mypy tools/research/single_pattern` | 10 个源码文件无问题，退出码 0 |
| 合成 CLI：compare 和 fixed-risk 各一次 | 退出码 0；各模式 3 入场、2 平仓、1 未平仓 |
| 真实 AVGO compare，一次 | 退出码 0；以上精确结果 |
| 已生成真实报告读取检查，未重新计算策略 | JSON/CSV 逐字段一致、HTML 指标与精确导出一致；24 个交易表行 |
| Chromium 离线报告（1440×1000） | 图表和基准切换可用；0 JS 错误、0 HTTP 请求；截图已检查 |

pytest 使用 `PYTHONPATH=src;.`，mypy 使用 `MYPYPATH=src`，浏览器使用既有
`PLAYWRIGHT_BROWSERS_PATH=D:/AI_Infra_Quant_Codex_v1/playwright-browsers`，没有安装新依赖。
首次新增断言曾用默认 Decimal 精度计算预期回撤，修正为模拟器同一 50 位上下文后通过；
未放宽断言或改变成交模型。保留既有 Starlette/AnyIO deprecation warning，无失败。

聚焦覆盖不同止损距离、成本计入 L、整手/现金/零数量/非法配置、下一开盘成交、
同根止损优先、跳空实际亏损超过预算、前缀决定稳定、信号身份不受仓位参数影响、
现金模式兼容、未平仓费用和离线导出。未重跑 F1、全产品回归或 Linux 浏览器矩阵；
本轮不声称这些项目重新通过，也不声称跨平台验证。

本地 `data/avgo-risk-comparison-v1/` 包含 HTML、精确 JSON、五份 CSV、截图和
`verification.json`（环境、代码摘要、输出哈希及读回检查）。主要文件 SHA256：

- `results.json`: `155cfe3994f82fa6752a7dfa894738d3f7008d4dbdce6276254fd2b831e1c0ea`
- `report.html`: `a4df0e6f701661642f2f973431994ee76fcc75fecee5bb9a58c26e497ad44e97`
- `trades.csv`: `aba3c3c58b5fa955f7d4f38274fcc0ed184c3e10280abe4310208cb32b32602c`

## 保护检查与限制

仅修改独立研究模拟/报告/入口，新增 sizing/comparison 和聚焦测试；更新使用说明、
roadmap 当前任务状态、requirements matrix 及本报告。
`src/`、依赖、F1/PAQS-E、研究输入适配器、原 Config/strategy、既有测试、冻结合同和
历史证据未改；普通任务分支提交，不更新产品或其他远程分支。
收尾 `git diff --check` 通过，四份本轮文档的 133 个本地链接目标存在；
变更路径符合本轮白名单，原实现与原收尾 worktree 保持干净。

本轮实现无已知未解决测试失败；等待聚焦独立审查，不宣称已审查或整合。
固定风险只是计划止损损失，跳空可超预算；前复权/历史时点、名义股数、日历及成交量/税费
局限继续保留，结果不是投资建议、盈利验证或完整 PAQS-Q。
F1 用户接受的 Linux 限定例外保持原意。完整 Event、正式 Setup/Risk、Q/E 比较、
正式界面与实盘均未启动。
