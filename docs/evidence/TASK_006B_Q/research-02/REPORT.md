# TASK-006B-Q-R02 — 结构稳定性研究报告

状态：**研究实现与验证完成，等待独立审查。建议保留基线作为研究对照，拒绝将 H1 认定为稳定替代方案。**
H1 解决了一个可复现的候选初始化陷阱，并在已知 AVGO 样本上消除了仍有效 Pivot 的丢失/重现；
但合成宽幅初始行情仍能触发同类重建问题。真实行情完整性仍为 **INCOMPLETE**，无产品采纳。

## 1. 精确来源与执行顺序

| 对象 | SHA |
|---|---|
| 产品权威基线，保持不变 | `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f` |
| 开发基线，全部文件保护 | `d50d73eea28005bc96e5ed0721b6a8e385ecedf5` |
| R02 合同/开工提交 | `47e7020609e5655927c6aac11a3b1f35b03c96aa` |
| F01/F02 独立聚焦 PASS | `fcdf69e5714ad32ddd8b526759e802d20c53f70a` |
| Phase A 证据及假设冻结提交 | `251f2a2ea9609ddd875c5aff03f5758c81914c84` |
| 实验代码、最终诊断与测试 | `36357c99809f44756c27035060edc3801d94ef67` |

Fetch 和 GitHub 远程引用核验：R02 开工 HEAD 精确为合同提交，其唯一父提交为开发基线；与产品权威
的 merge-base 是上述产品基线。聚焦审查为开发基线的独立子提交，未合并审查分支。独立 worktree：
`D:/AI_Infra_Quant_Codex_v1/task006b-q-r02-worktree`；其他工作区、旧任务分支及未跟踪文件保留。
已读 AGENTS、治理文档、历史 phase plan、原合同/候选、remediation-01 CONTRACT/REPORT 和两份精确审查。
Phase 1 历史停止指令不启动/阻止本轮显式授权的研究任务。

执行顺序为：核验 → 原 AVGO 哈希校验 → Phase A 根因/100-row census → 冻结唯一 H1、参数和 cutoff →
实现/独立合成预期 → 原样本全量比较及公开数据尝试 → 补充几何归因/反例 → 完整验证与报告。
比较运行使用随后提交的 H1 算法；后续只完善诊断标签、类型/格式及测试，未根据结果调整 H1 或参数。
最终交付 SHA 在报告/证据提交后通过 GitHub 读回并返回，不在本文件嵌入自引用提交哈希。

## 2. Phase A：不是统一的“旧 Pivot 过期”

[12 个完整记录](phase-a-cases.json)包含 Capture/时间框架/cutoff、窗口哈希、退出 warm/active 条目，
其源时间和市场本地 session 时间、初始正 ATR、候选 High/Low、down/up 距离与阈值、确认与分离门槛、
最早状态/谓词分歧、四臂结构和可用性审计，以及共同活动域的丢失/重现事件。
`trace.py` 记录有界逐步状态；`phase_a.case` 断言其事件序列与实际 evaluator 的 Pivot 引用一致。
RIGHT/LEFT 是诊断 N+1/N-1；正常 OLD/BOTH 始终独立选原始版本，保留 F02 的时间隔离。

诊断 2×2 干预固定 OLD 行情与共同活动引用，分别改变首个正 ATR 可种子位置（旧 local13→14）与
共同位置 ATR 序列。仅改变 seed 即重现差异而改变 ATR 不改变结果，才归为 SEED_PATH。
两者皆影响或组合才影响的情况保留 INTERACTING_OR_UNRESOLVED，不声称唯一因果。
这些 ATR/seed 干预从未进入正常 H1 输出。

| 原案例（UTC cutoff） | 最早谓词分歧 UTC | 共同活动域丢失/重现 | 归因 |
|---|---|---:|---|
| W1 2025-05-30 20:00 | 2023-03-24 20:00 | 0 / 0 | 实际活动 Pivot 过期 |
| W1 2025-08-15 20:00 | 2023-05-26 20:00 | 0 / 9 | seed 路径 |
| W1 2025-08-22 20:00 | 2023-06-02 20:00 | 9 / 0 | seed 路径 |
| W1 2025-08-29 20:00 | 2023-06-09 20:00 | 0 / 9 | seed 路径 |
| D1 2026-08-03 20:00 | 2025-05-28 20:00 | 0 / 0 | 实际活动 Pivot 过期 |
| M30 2026-09-01 16:00 | 2026-08-12 14:00 | 0 / 17 | seed 路径 |
| M30 2026-09-01 16:30 | 2026-08-12 14:30 | 17 / 0 | seed/ATR 交互，未唯一归因 |
| M30 2026-09-02 17:00 | 2026-08-13 15:00 | 0 / 18 | seed 路径 |
| M30 2026-09-04 18:00 | 2026-08-17 16:00 | 21 / 0 | 组合干预才改变，未唯一归因 |
| M30 2026-09-04 18:30 | 2026-08-17 16:30 | 0 / 21 | seed 路径 |
| M30 2026-09-08 17:00 | 2026-08-18 16:00 | 20 / 0 | seed 路径 |
| M30 2026-09-08 18:00 | 2026-08-18 16:00 | 0 / 20 | seed 路径 |

两例过期即使 warm 中也有早期状态分歧，共同活动事件仍一致，故不能把早期分歧一律解释为近期结构损失。
另外十例的变化事件极值和确认仍同时有效，不能用自然过期解释。冻结案例为开发样本，非未知验证集。

### D1 的 96/100 UNCERTAIN

[完整 census](phase-a-d1-census.json)逐终点保存 active pivots、labels、资格、操作数及原因：

- 96 次 `ACTIVE_TWO_SIDED_HISTORY_INSUFFICIENT`；4 次 `DIRECTIONAL_EVIDENCE`。
- 真实冲突/等高低导致的终局原因 0；收盘破坏方向的终局原因 0；未种子终局 0；双向种子歧义 0。
- 活动 Pivot 数：0 个的 26 次、1 个的 36 次、2 个的 3 次、3 个的 31 次、4 个的 4 次。
- 74 次存在陈旧活动 Pivot 警告。100 次无符合规则的当前 Range，不能用历史触点补造。
- 有些最新标签为 HH/HL，但比较对象仍在 warm 区，不能满足四个活动 Pivot 的方向门槛。
- 输入为 PARTIAL/OBSERVATIONAL；100 次均满足 N=312，没有缺失窗口造成的计算失败。
  这不等于行情/历史信息集完整。

[分离门槛跟踪](phase-a-separation.json)显示所有 100 次末态为 SEEK_LOW，候选 LOW 的极值 index
仅在上一 HIGH 后 1 根。后续 close 反弹即使通过距离门槛，也会因 2 根分离门槛失败；更高的后续低点
不能替代已保存的较低候选，导致长期锁定。这解释了活动比较证据枯竭，但并不意味着原 96 个 UNCERTAIN
应当被人工重标为趋势：原规则下的保守拒绝是正确输出，修订候选定义有明确语义代价。

## 3. 唯一冻结候选 H1

[数学规格](../../../research/PAQS_Q_STRUCTURE_R02_CANDIDATES.md)：`QSTR-R02-ELIGIBLE-SEED-1`。
确认 Pivot 后，只从 `i - previous_extreme >= 2` 的条目初始化/更新对侧候选。确认条目不满足间隔时，
候选保持 null，等待首个合法条目；之后仍按最早相等极值、原 lambda×ATR 和 completed close 确认。
保持 UNSEEDED 的 XOR 规则，双向歧义不强制输出。

W/A/N、EMA_TR_14、Decimal(50)/1e-18、lambda、分离数值=2、等价阈值、zone/range/age/cap 和
two-high/two-low 方向门槛全部不变。H1 独立计算 Pivot/几何/Regime，复用原纯函数；没有重标基线结果。
版本和 config/Pivot identity 独立，结构比较排除版本驱动 ID。

语义变化：极值定义限于允许间隔后的候选域；`s+1` 处可能出现更低 Low/更高 High，但不进入该域。
它们仍保留在行情/ATR 中，未被删除或改价。是否接受这种 swing 定义必须独立审查/语义决策。
本轮只做一个候选，没有继续针对 AVGO 或公开数据调参/追加第二个候选。

独立合成预期覆盖：高110 在 i1 确认 HIGH0；低90@i1 被排除后，低95@i2 在 i3 close97 确认 LOW2；
镜像场景、精确等式/相等极值、同条禁止、单调/平坦/交替/宽幅/时间隔离/实际过期均有断言。
另有手算 ATR 干预：首 TR=30、其后 TR=2，则 ATR13=4、ATR14=3.733333333333333333；
退出首条后 ATR13=2，固定距离4的反转谓词会不同。它是诊断 oracle，不是另一套正常 ATR。

## 4. 全部原始 AVGO 终点：同输入对照

三份 normalized 文件 SHA256 与原 manifest 完全一致。基线在 274 个有效终点的 decision hash 均与
remediation-01 corrected-study 相同；每框架仍调度100个终点，M30的26个不足窗口保留。

可比较机会：每个 OLD Pivot 的极值及确认引用仍在新活动集。事件 identity 为类型/精确价格/两端源引用，
不含 config ID。已在 OLD cutoff 前确认却新出现的事件计为“重现”；新确认和自然过期分别计数。

| Frame | 有效终点 | 基线丢失/机会 → H1 | 基线重现 → H1 | 自然过期 基线/H1 | 重要 LEFT_ONLY 基线/H1 |
|---|---:|---|---:|---:|---:|
| W1 | 100 | 9/556 → 0/987 | 18 → 0 | 7 / 9 | 4 / 0 |
| D1 | 100 | 0/147 → 0/2454 | 0 → 0 | 4 / 7 | 1 / 6 |
| M30 | 74 | 58/870 → 0/2066 | 76 → 0 | 8 / 10 | 7 / 0 |

| Frame | 基线 Bull/Bear/Range/Uncertain | H1 Bull/Bear/Range/Uncertain | 状态变化 基线/H1 / 相邻比较数 |
|---|---|---|---|
| W1 | 13 / 0 / 0 / 87 | 21 / 0 / 0 / 79 | 6 / 8 / 99 |
| D1 | 4 / 0 / 0 / 96 | 28 / 17 / 12 / 43 | 1 / 12 / 99 |
| M30 | 20 / 3 / 0 / 51 | 23 / 14 / 0 / 37 | 9 / 10 / 73 |

H1 仍保留有效不确定性：W1冲突/等价73、收盘跌破HL6；D1冲突24、收盘跌破HL19；
M30冲突36、收盘越过LH1。H1陈旧活动Pivot警告0，而基线W1/D1为33/74。
直接 Bull↔Bear 翻转两者均0；H1 D1有11个相邻几何变化超过0.5 ATR，完整记录保留四臂分类、
几何幅度、touch引用及选区数量变化，不能因为不属于 LEFT_ONLY 就宣称没有几何变化。
趋势增多、UNCERTAIN降低和新出现12次Range都只是结果，不是成功标准。

### 六个 H1 LEFT_ONLY 标记的最终解释

日期为 2026-07-22、07-27、07-30、07-31、08-03、08-17（均20:00 UTC）。
[逐例干预](refined-causes/h1-geometry-causes.json)保留 LEFT 的种子域，只替换共同观察的 ATR 序列，
六例均恢复 OLD 的 zone/range 几何；原生差异属于 ATR 舍入传播。最大对应 zone 边界距离约
`2.13e-16` 个 ATR，远低于既有0.5标记阈值。确切 range bound 不等仍触发继承的 material 规则，
没有改容差、删标记或改为相等。08-03还伴随一个真实活动 Pivot 过期，其他五例没有活动事件变化。

首轮 `comparison/*material-causes.json` 的 `cause` 仅比较共同活动 Pivot，把无事件变化过宽地称为
LEGITIMATE_ACTIVE_EXPIRY；该标签不足以解释几何。原输出保留，最终解释使用上述独立补充文件；
最终 `phase_a.case` 对无事件变化且无过期明确要求几何诊断，不再使用该过宽标签。

### OFAT 没有被用来选优

全部冻结变体见 [summary](comparison/summary.json)。H1 W1 lambda1.9仍有35/100 Regime分歧，
D1 lambda1.9为31/100，D1 L60为22/100；这些是参数敏感性警示。原无Range样本中多项分歧为0不代表
参数稳健；H1带来可观察Range以后，range窗口差异显现。本轮没有修改默认参数或选择“最好”变体。

## 5. 为什么拒绝“稳定替代方案”结论

[合成反例](refined-causes/h1-rejection-counterexample.json)用201根 M30，index13是一根宽幅行情，
使初始上下反转同时成立。H1按保留的规则不强制种子；滚动一条后该宽幅条离开正ATR种子域，
在仍有效的共同活动域内重新发现13个早已完成的 Pivot。诊断2×2归因为 SEED_PATH。
这不是未来数据泄漏，却是有限窗口重建的结构不稳定；工程回归明确断言此反例仍存在。

因此：H1对“过早对侧极值永久占位”的修订有解释力，但没有解决所有初始种子/窗口机制，
**拒绝鲁棒性采纳**。保留基线作为研究控制，不等于认为基线语义已通过。具体下一决策是：
先独立决定是否接受“admissible-extreme域”语义，并为持续双向种子歧义/有限窗口重建制定
可证伪的约束或额外合同；本任务不自行加重置、投票、无界状态或第二轮候选。

## 6. 真实数据尝试与限制

冻结的额外验证 ceiling 是2026-09-09T14:00Z，早于公开获取；仍用原40成员，24US/16HK。
显式研究 adapter 使用标准库、不在导入/测试/普通计算联网；OpenD历史请求0、自动重试0。

- [Stooq 历史页](https://stooq.com/q/d/?s=nvda.us)及条款入口：实际HTTP200为JavaScript浏览器验证页，
  没有取得价格/许可正文；没有绕过验证或把响应当CSV。
- [Alpha Vantage 官方文档](https://www.alphavantage.co/documentation/)要求API key；公开demo的NVDA/full请求
  实际仅返回领取key提示，没有行情。未注册账户、读取用户key或购买服务。
- [Yahoo官方帮助](https://in.help.yahoo.com/kb/SLN2311.html)说明历史下载需要Gold订阅；本轮未取得该授权，
  不调用其他未批准接口规避订阅。这不是声称所有公开数据源都不可获得。

[尝试元数据](acquisition-attempt.json)记录命令入口、URL、UTC获取时刻、原始响应字节hash/外部路径及错误。
原始响应保留在 `D:/AI_Infra_Quant_Codex_v1/task006b-q-r02-public-raw/`，未入Git。
实际额外可比较股票0，因此没有额外行情 normalization/calendar/adjustment可认证；未编造日历、
把D1充当M30、填补缺口或把供应商未知精度升级。未迭代候选以适配额外样本。

原始 Capture `2babba19-e0ce-4bfa-aab9-93061a95818c` 为当前QFQ、PARTIAL、历史 available_at未知。
三框架分别311/1500/273个可用bars，W1/D1有100终点，M30只有74（目标299 bars尚缺26）。
每框架原分母40；39只股票完全不可用。额外覆盖与原始覆盖分列于[coverage](coverage.json)，
**真实门槛INCOMPLETE**，不能声称40股票/24US/16HK通过。
每算法1366个CURRENT/四臂输入集、294200次行情使用的时间检查为0违规，但这些使用的历史可用时间
全部未知；这只是计算隔离/观察性研究，不是严格历史信息集或corporate-action-safe认证。
没有本地原始文件的审查者不能仅凭hash复算AVGO；合成实验可独立运行。

## 7. 验证、性能与保护

环境：Windows11 build26200、Python3.12.14、pytest8.4.1、Ruff0.12.9、mypy1.17.1，已有声明依赖环境。

| 检查 | 实际结果 |
|---|---|
| 原97项研究 + 新35项R02 | **132 passed, 1 warning in 8.77s** |
| 同六文件业务相关回归 | **59 passed, 1 warning in 10.48s** |
| Ruff / format | PASS；12个新增Python文件 |
| strict mypy/native + win32 | 两者PASS；12个文件 |
| diff、链接、开发基线mode/type/blob、合同及假设冻结 | PASS，见protection.json |

唯一warning为既有Starlette/AnyIO BlockingPortal alias弃用。没有skip/xfail、降低阈值、批量改quality或
修改原测试。范围不要求无关业务全套、浏览器/Uvicorn，未宣称执行。完整命令见[README](README.md)，
结果见[validation](validation.json)。

[性能](comparison/performance.json)：Intel64 Family6 Model183 Stepping1，单进程7次固定合成最大窗口。
W1 p50基线7.841ms/H1 7.9123ms；D1 19.5619/20.3139ms；M30 12.7434/12.3437ms。
H1各框架p95最近秩为8.295/22.7097/13.6631ms；tracemalloc峰值233571/615847/360952字节。
每次Pivot访问N条；D1该fixture pair_distance100/range_pairs2，两算法一致。输出膨胀可能随Pivot数变化；
这是声明硬件/fixture的测量，不是服务SLA或收益指标。

实现相对合同开工提交只新增授权路径；开发基线429个文件及另行签发的R02合同均保持不变。
src、已有业务/研究测试、原原型、原候选/报告/全部旧证据、冻结参数/universe、
依赖/配置、迁移0001–0004、PAQS-E及用户数据库均保持。独立R02 verifier保护全部开发基线文件，
没有修改原 verifier 添加豁免。[protection](protection.json)列出完整变更路径/模式类型blob核验与本地链接。
用户数据库SHA256仍为 `81b32a5f0f74e5549e99414456f189d5111435e3601b00bcd3e43c41ee2f1034`；
`phase1_remediation_commit.txt`仍为 `c791ba73b41c4e7719957607e025105a8110fa54a2e1a67f3c5b142da8030440`。
本轮研究直接读取已规范化文件，对数据库仅作只读hash核验。

## 8. 合同矩阵与停止点

| ID | 证据/结论 |
|---|---|
| R02-01 | 12/12复现，最早分歧/干预；2交互保留不唯一归因 |
| R02-02 | 100/100 D1原因与活动证据census，无UNCERTAIN比例目标 |
| R02-03 | 1个冻结H1、完整数学/合成预期，原文件未改 |
| R02-04 | F01/F02新旧测试、四臂所有warm输入时间检查；未知信息集不认证 |
| R02-05 | 跨进程/Decimal context/任意额外旧行情，274真实终点origin一致 |
| R02-06 | 双端活动资格、warm比较不可充当方向、过期/未完成/单调/flat回归 |
| R02-07 | 机会分母、丢失/重现/新确认/过期、状态/几何/充分性完整对照 |
| R02-08 | 六例H1左边界几何干预已解释；合成近期结构重现仍在，拒绝鲁棒性采纳 |
| R02-09 | 原分母完整保留，额外0，真实门槛INCOMPLETE |
| R02-10 | 全部冻结小OFAT，不按回报/标签选择参数 |
| R02-11 | 硬件、7次p50/p95、内存、比较计数与N边界 |
| R02-12 | 工程验证完成待审；结构鲁棒性REJECT H1；市场INCOMPLETE；产品NOT AUTHORIZED |

仅正常推送 `task/006b-q-r02-structure-stability` 并从GitHub读回。没有合并、修改产品权威/原Q任务分支、
接入产品或启动006C-Q。预测与交易表现未评估。停止，等待独立审查。
