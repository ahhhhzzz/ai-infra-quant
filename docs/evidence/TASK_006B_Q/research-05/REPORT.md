# TASK-006B-Q-R05 实现与研究报告

状态：**研究执行完成，等待独立审查**。日期：2026-09-12。

唯一研究 disposition：**RECOMMEND_CROSS_SAMPLE_ONLY**。

这只建议在今后另行授权的合同中验证独立股票。实现完整性通过本轮自验；
本轮没有证明正式 Swing/Pivot 语义、严格历史确认或广泛市场适用性，也没有授权产品采用。

## 1. 精确血缘与冻结先后顺序

| 对象 | 精确 SHA |
| --- | --- |
| 产品权威 roadmap/no-live-trading | `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f` |
| 修正 R04 开发基线 | `c4e21a0204cf6cdd7bb139584b02f01792a49f13` |
| R04 原独立审查 | `4906985744512092fc098340f43e8eec1f41c494` |
| R04-F01 实质 focused PASS | `2094118f270e209b5b037162813815886678fdbd` |
| 当前 review 分支（仅后续格式调整） | `56020173b223dcf277ef8f125eeeaaa3fa135bcc` |
| 本任务合同／精确开工 HEAD | `0d8ca48b046325c4d03a1716c806d42a333153ec` |
| 首次实现／预结果冻结提交 | `b10e87cbb324442d1fc744d5fa94522802f870c1` |
| 最终研究实现与计算结果提交 | `3dda84b9653e458ee9a7a3ef2cd3d7643562f9f9` |

合同提交为修正 R04 的直接子提交；首次实现冻结为合同的直接子提交。结果提交以冻结提交为唯一父提交。
本报告与后续保护封包仅追加文档/审计证据。**最终交付分支 SHA** 在所有封包提交完成后从 GitHub 读回，
与本报告的固定提交链接一起列入交付消息；上表的结果 SHA 不冒充随后文档封包的 HEAD。
这是避免把尚未存在、包含本文件的 Git commit SHA 伪写为本文件自引用的血缘区分。

开始时已 fetch，核对远程 task、authority、review、父提交和 merge base；
仅在新建的 `task006b-q-r05-worktree` 检出批准的 R05 分支，初始 HEAD 精确匹配，工作区干净。
原 9 个 worktree 保留。完整读取了 AGENTS、合同指定治理、R04 冻结规格/计划与最终报告、
R04-F01 合同/报告及两个精确审查提交；未合并、cherry-pick 或复制 review 历史。

[冻结读回凭证](freeze-readback.json) 记录 GitHub 在 **2026-09-12 10:59:23 UTC**
确认冻结 SHA、父提交、tree、13 个实施文本哈希、600 个坐标及 57 个分支引用。
B0 真实运行开始于 **10:59:41.357761 UTC**，独立 B0 于 **11:00:40.502297 UTC** 完成；
之后才进入 A1，整个 A/B 与枚举于 **11:01:53.337752 UTC** 完成，进程退出码 0。
结果后没有改动候选、指标、cutoff、案例选择或计算代码。

## 2. 唯一干预、证明与反例

B0 精确保留 R04 `PROPOSED_SEMANTICS:R04-CALENDAR-LOCAL-1`。
A1 为 `PROPOSED_SEMANTICS:R05-NO-PRIOR-RAW-VETO-4SUPPORT-1`。
[A1 数学规格](../../../research/PAQS_Q_PRIOR_RAW_VETO_ABLATION_R05.md) 与 [PLAN](PLAN.md)
完整冻结了原公式、量度、案例排序、有限域及决定表。

实现仅移除 acceptance 中的 prior-raw veto。相同四观察 j-2..j+1、W/A/N、日历、
质量、cutoff、版本可用性、XOR、严格极值和一倍前观察区间反转尺度不变。
A1 从合格的 raw XOR 和 quartet 证书重建事件，不以 B0 的 veto 分类决定 A1 接受；
没有三观察事件路径。额外 j-2 是为配对域保留的非最小依赖，已明确承认其覆盖代价。

- 集合与双射：B0 的布尔合取项多一个 veto，故 B0 endpoint 集合包含于 A1；
  A1 差集恰等于 B0 合格、活跃、当前 XOR 的 PRIOR_RAW_VETO 行。一中心一端点，
  因而是双射。所有 600 个同坐标结果执行断言，274 个共同有效坐标通过。
- 身份：端点键独立于规则 ID。共享端点的 kind、精确 price、extreme/confirmation ref/time、
  price/calendar support、availability、mode 保持相同；B0 identity/support hash 保持原 R04，
  A1 identity 单独包含其规则 ID，未把规则 ID 变化计成事件差异。
- 严格邻居命题：相邻 D 同时成立要求 H(j-1)>H(j) 与 H(j)>H(j-1)，矛盾；
  U 同理。前一 raw 为 dual 也不能与当前 raw 共存。实际新增仍按 opposite/same/dual 分类，
  没有用命题省略诊断。
- 条件滚动稳定：完全相同的有序 quartet 价格版本、日历事实、模式、整体合格输入和活跃端点，
  决定相同 Q/X、端点及完整支持身份，窗口起点不另行参与公式。插入、修订、日历变化、
  缺失支持或 active expiry 不在此命题前提内，不能借此宣称无条件稳定。
- 合成反例保留 ties、current dual、零尺度、missing/unknown j-2、OLD cutoff 与价格/日历修订、
  插入及 active expiry；HIGH110/LOW80/HIGH140/LOW50 反例保留四事件相邻交替链。
  缺失或失败没有通过修改旧夹具状态掩盖。

[有限枚举](proof-and-enumeration.json) 为十个精确 OHLC 字母、四观察、四种既定日历状态，
共 **40,000** 输入；有序输入/输出 SHA256：
`2a765fe99b5138a3bf92f992cb32836956eac4e6c6b48250f4bbdff7dfce3efd`。
COMPLETE 域 10,000 输入中 B0=864、A1=960、veto=96；
其余三个域各 10,000 输入均为零事件。集合/双射失败、相邻同类 raw 反例均为 0，
并保存首个 B0-veto/A1-accept 的精确 OHLC 见证。
这是合成数学实现检查，不是额外真实股票。

## 3. 输入、时钟与 B0 对账

仅只读使用 R04 已冻结的规范化 AVGO W1/D1/M30 外部文件和捕获日历；
未访问用户数据库、OpenD、行情服务、公共网页研究、LLM 或账户接口。
GitHub 的 Git/ref/文档操作仅用于本任务交付。

| 输入 | SHA256 |
| --- | --- |
| W1 | `682aaebb059adb3ed8299b8b145b88b6d3d79ad6203c43716540b7035fa599ba` |
| D1 | `d060a2abc82dceb957c49e607f8308ef6a57bdf0dd291110c8d29a8256435160` |
| M30 | `87f8d630d2e3a321ee2093bc9ba064c426909609b2dd1607b837de1fe768fb09` |
| 捕获日历 | `46c652b3062e4c6aeb43454dbcff5d8deb5f348639766b9e444b21116ebf6b2d` |

三个周期各 100 个 cutoff，各执行 OBSERVATIONAL / AS_OF，共每臂 600 个坐标。
完整值见 [freeze.json](freeze.json)。W/A/N 为 W1 26/104/130，D1 60/252/312，
M30 40/160/200。cutoff 范围分别为 2024-10-11～2026-09-04、
2026-04-16～2026-09-08、2026-08-27～2026-09-08；精确 UTC 时间未改变。

[B0 复现](baseline-reproduction.json) 对全部 21 个 study-03 文件逐字段比较通过；
123 个获准排除的具体元数据路径逐条列出，仅实际 recognition 时间与 summary 的四个运行字段。
没有忽略价格、证书、事件身份、覆盖统计、控制项或案例内容。
配对过程中每个 B0 又与 study-03 的原始 census、events、costs 和标量元数据核对。

OBSERVATIONAL 有效 W1/D1/M30 为 **100/100/74**；M30 另 26 个证据不足。
AS_OF 三周期各 100 个全部 INSUFFICIENT，均无事件，原因为
INSUFFICIENT_HORIZON_OR_AVAILABILITY。总计每臂 274 VALID、326 INSUFFICIENT，
无 INVALID。PARTIAL、current-QFQ 和未知历史可用时间均保留。
实际 recognition 时间使用真实执行时刻，未回填历史；所有选入 price/calendar evidence 的完成/
已知可用时间审计及原 no-lookahead audit 通过。

## 4. A/B 结果与结构成本

以下次数均为**重叠 cutoff 窗口累计出现次数**，不是独立样本。去重端点另列。
完整逐 cutoff/segment/mode 结果在六个 [W1 OBS](frames/W1.OBSERVATIONAL.json)、
[W1 AS_OF](frames/W1.AS_OF.json)、[D1 OBS](frames/D1.OBSERVATIONAL.json)、
[D1 AS_OF](frames/D1.AS_OF.json)、[M30 OBS](frames/M30.OBSERVATIONAL.json)、
[M30 AS_OF](frames/M30.AS_OF.json) 中；全量分类、支持证书、遗漏参考、失败 pair 均可恢复，
没有用汇总代替原始对照。

| OBS 周期 | B0→A1 事件次数 | B0→A1 去重端点 | 新增次数／去重 | 去重 restored-more-extreme | removed |
| --- | --- | --- | --- | --- | --- |
| W1 | 805→977 | 20→23 | 172／3 | 3 | 0 |
| D1 | 4867→5806 | 69→80 | 939／11 | 8 | 0 |
| M30 | 1553→1661 | 30→33 | 108／3 | 1 | 0 |

共享次数分别为 805/4867/1553，共享去重端点为 20/69/30。
[差集明细](endpoint-delta.json) 与 frame 的 rows.delta 保存所有映射及精确原 B0 reason。
新增 172/939/108 次均为 previous raw **opposite**、间隔 1；
same=0、dual=0，全部与原 active veto 行双射。
没有未知、非 veto、双重 raw 或不合格支持的新增。

| 周期 | 事件密度 B0→A1（事件／active centers） | 同类对 B0→A1（同类／全对） | 异类对 B0→A1 |
| --- | --- | --- | --- |
| W1 | 805/10400→977/10400 | 461/705→519/877 | 244→358 |
| D1 | 4867/25200→5806/25200 | 2544/4767→2366/5706 | 2223→3340 |
| M30 | 1553/11840→1661/11840 | 372/1479→337/1587 | 1107→1250 |

同类对比例分别为 0.653900709219858156→0.591790193842645382、
0.533668974197608559→0.41465124430424115、
0.251521298174442191→0.212350346565847511。
决定表使用整数交叉乘法，不靠显示舍入。W1 的**同类对绝对次数反而增加 58**，
没有被比例下降掩盖。

| 周期 | separation=1 对数 B0→A1 | 最长单位间隔交替链事件数 B0→A1 | separation min/下中位/max B0→A1 |
| --- | --- | --- | --- |
| W1 | 0→139 | 0→2 | 2/8/41→1/8/40 |
| D1 | 0→937 | 0→3 | 2/4/15→1/3/15 |
| M30 | 0→105 | 0→2 | 2/7/20→1/6/20 |

完整 HIGH/LOW run-length 频数见 [A/B 汇总](ablation-results.json) 的
kind_run_length_distribution_occurrences，定义为完整事件序列的最大同类 run。
最大 run：W1 HIGH 3→3、LOW 5→5；D1 HIGH 8→4、LOW 7→7；
**M30 HIGH 3→4**、LOW 3→3。同类比例改善不等于所有结构成本改善。

| 周期 | age min/下中位/max B0→A1 | amplitude 下中位 B0→A1 |
| --- | --- | --- |
| W1 | 1/46/103→1/42/103 | 1.682226913820012865→1.375097276317541039 |
| D1 | 1/124/251→1/117/251 | 1.789237668211892643→2.004985754943480736 |
| M30 | 1/71/159→1/76/159 | 2.907828947368421053→2.826771653543307087 |

amplitude 为两相邻事件绝对价差／当前事件的原局部区间，保持 Decimal50 计算。
W1 min/max 两臂均为 0.129297293750864494 / 11.741475765254149595；
D1 均为 0.009852216754237087 / 11.827758270190352985；
M30 min 为 0.511913875598086124→0.38058252427184466，
max 均为 13.589318981577313186。事件 age 数量等于事件出现次数，separation/amplitude
数量等于全对分母；逐值与分段归属保留在 frame 内。

| 周期 | more-extreme omitted／reference opportunities B0→A1 | 完整支持 active／全部 active（两臂相同） |
| --- | --- | --- |
| W1 | 248/437→124/313 | 4292/10400 |
| D1 | 694/930→0/53 | 23807/25200 |
| M30 | 6/67→0/0（比例未定义） | 9056/11840 |

A1 对自身拒绝中心重新寻找此前最近同类事件作参考，故不能把遗漏次数下降全当作
一对一恢复成功；去重 restored-more-extreme 仍严格按原 B0 行判定。
M30 0/0 没有被记成 100% 或成功率。

W1 修正段聚合精确保持 **10400=8479+1921**，后者为 UNRESOLVED_SEGMENT；
两臂每个有效结果的 segment centers、support、events 三项总和均守恒。
非 veto 的分类、质量、选窗、日历 hash 和支持覆盖不变。

## 5. 滚动稳定与保留依赖税

原 endpoint 丢失/重现及 full-support 指标均保留，没有换名。

| 周期 OBS | valid／unavailable cutoff pairs | endpoint及full-support机会 B0→A1 | lost/full-support lost/rediscovered | 新确认 B0→A1 | expiry B0→A1 |
| --- | --- | --- | --- | --- | --- |
| W1 | 99／0 | 785→954 | 两臂均 0/0/0 | 12→15 | 7→7 |
| D1 | 99／0 | 4798→5726 | 两臂均 0/0/0 | 25→29 | 17→19 |
| M30 | 73／26 | 1523→1628 | 两臂均 0/0/0 | 10→10 | 9→12 |

所有实际有效 pair 的 witness change、calendar revision、coverage excluded、
endpoint information excluded 均为 0。AS_OF 每周期另有 99 unavailable pairs，
保留逐 pair 原因，不跨越失败窗口拼接“稳定”。零损失是受限固定输入上的实现证据，
不代表其市场适用性通过。

[TRIPLE_ONLY_ELIGIBLE 诊断](dependency-audit.json) 完全不产生事件：

| OBS 周期 | 全部／active 中心次数 | active current XOR 次数 | 原因 |
| --- | --- | --- | --- |
| W1 | 1462／1133 | 408 | CALENDAR_UNKNOWN、LEFT_SUPPORT_MISSING |
| D1 | 765／436 | 57 | CALENDAR_UNKNOWN、LEFT_SUPPORT_MISSING |
| M30 | 1184／904 | 0 | PROHIBITED_SEGMENT_BOUNDARY、LEFT_SUPPORT_MISSING |

诊断包含 false/false 和 dual，故“triple 可评估”不等于“原始反转成立”。
每行保留 cutoff、中心、active、segment、失败原因和 XOR；缺失段统一规范化。
三个 AS_OF 无合格输入，诊断计数为零，不表示无依赖税。
未运行三观察候选，也未改变 frozen universe 中其余 39 个股票的数据缺失状态。

## 6. 案例与唯一建议

冻结五类 rubric 每周期均命中，W1 首次新增与最大恢复遗漏同焦点合并，
最终 **14/14** 图已实际打开检查；没有为避免不利结果重选 cutoff 或案例。
[全部案例判读](case-review.md) 保存完整 case ID、UTC cutoff、原值和图/JSON 链接。

D1 的三中心 LOW/HIGH/LOW 链、三个周期新增 HIGH/HIGH、M30 最大 HIGH run 增长、
W1 相隔 40 观察的 HIGH/HIGH 和中间大片日历证书缺口均已保留。
这些是局部原始证书作为正式 Swing 的未解决局限。图中没有 cutoff 之后的价格，
不使用确认后方向、收益或人工成功标签。

没有发现无法归因于 veto 的新增或同支持不稳定；局部证书未承诺强制交替/全局最优，
因而不能事后加入最小间隔或峰合并条件来改判。
根据冻结决定表：每个有效周期至少有一个去重恢复遗漏、同类对比例均不升、
所有链与不利案例已披露、硬性不变量通过，给出唯一 disposition
**RECOMMEND_CROSS_SAMPLE_ONLY**。这不是“事件更多所以成功”。

## 7. 验证、环境与保护

[validation.json](validation.json) 记录精确命令、版本、退出码；
[README](README.md) 提供执行命令及独占新输出路径约束。

- Python 3.12.14 / pytest 8.4.1 / Ruff 0.12.9 / mypy 1.17.1；
  图表复用 matplotlib 3.11.1 的现有独立环境，未改依赖。
- 合同测试命令：**268 passed, 1 warning in 29.97s**，退出 0；
  原有 234 加新 34；无 skip、xfail、deselection、failure 或 error。
  唯一 warning 为原 Starlette BlockingPortal 弃用提示。
- Ruff PASS；格式 11 files already formatted；原生和 win32 严格 mypy
  均为 Success: no issues found in 11 source files。
  这些门槛在精确冻结实现文本上、真实 A1 前执行，结果后实现与测试未变化。
- 真实研究与绘图退出码均为 0；枚举 40000 PASS；14 图全部判读。
- git diff --check、相对链接、纯新增白名单、原 612 个 Git mode/type/blob、
  以及冻结 PLAN/freeze/spec/code/tests 14 个对象由冻结 protect 命令核验。
  最后在报告提交后的干净 HEAD 生成 `protection.json`，该文件记录其实际 checked_head、
  空 status、626 个保护身份与完整路径/链接清单；仅追加保护文件封包后再执行干净状态检查。
  自验 PASS 不替代独立审查。
- GitHub 直连推送曾超时/连接重置；现有本地 MyClash 代理的命令级使用解决了问题。
  没有修改 Git 全局设置、代理配置或远程 URL。冻结先推送/读回后研究的门槛未跳过。
- 合同不要求 browser、Uvicorn、PostgreSQL、迁移执行或全产品测试，本轮未运行这些检查，
  不把它们写成通过。

全部旧研究、study-01/02/03、原始诊断、冻结计划、R04-F01 修复与审查证据、
src、PAQS-E、业务测试、依赖、配置和迁移均保持原对象。
用户数据库未访问，不以旧 hash 冒充本轮数据库保护证明。
其他 worktree、未跟踪文件及 phase1_remediation_commit.txt 未删除或覆盖。

## 8. 限制与停止边界

只有 AVGO 一支真实股票，且为 PARTIAL/current-QFQ、未知合法历史 available_at；
AS_OF 全部不足，OBSERVATIONAL 是回顾性描述。严格历史确认与广泛市场适用性
继续 **INCOMPLETE**。有限域枚举与 US/HK 合成测试不补充真实股票样本。

A1 保留非最小 j-2 支持，仍有显著覆盖税；短间隔交替、同类重复、
覆盖缺口及 reference 稀疏造成的遗漏比较依赖尚未解决。
未证明正式 Swing、趋势、方向、收益或任何交易用途。
仅普通推送 R05 任务分支；无 merge、force-push、权威/R04/review 引用更新。
不启动三观察候选、006C-Q、后续任务或产品接入，停等独立审查。

## 9. 全部新增路径

共 81 个文件，纯新增；无修改、删除、重命名、软链接或模式变更。
路径清单按 POSIX 字符串显式排序，详细 Git 身份见 `protection.json`。

```text
docs/evidence/TASK_006B_Q/research-05/PLAN.md
docs/evidence/TASK_006B_Q/research-05/README.md
docs/evidence/TASK_006B_Q/research-05/REPORT.md
docs/evidence/TASK_006B_Q/research-05/ablation-results.json
docs/evidence/TASK_006B_Q/research-05/baseline-reproduction.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/US.AVGO.D1.AS_OF.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/US.AVGO.D1.OBSERVATIONAL.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/US.AVGO.M30.AS_OF.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/US.AVGO.M30.OBSERVATIONAL.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/US.AVGO.W1.AS_OF.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/US.AVGO.W1.OBSERVATIONAL.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/cases/D1.accepted.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/cases/D1.calendar.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/cases/D1.repeated-kind.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/cases/D1.veto.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/cases/M30.accepted.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/cases/M30.calendar.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/cases/M30.repeated-kind.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/cases/M30.veto.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/cases/W1.accepted.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/cases/W1.calendar.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/cases/W1.repeated-kind.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/cases/W1.veto.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/coverage.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/source-calendar-manifest.json
docs/evidence/TASK_006B_Q/research-05/baseline-study/summary.json
docs/evidence/TASK_006B_Q/research-05/case-review.md
docs/evidence/TASK_006B_Q/research-05/cases/D1.219c2df8eb70d731e8f1fa9be51a4f1fb81ce0a20d94aed15dc8fd4231a2cda6.json
docs/evidence/TASK_006B_Q/research-05/cases/D1.270c5807fb5e4a87ed06b37f568d9dd151ed47ab08afbef38eabec8d2011da3b.json
docs/evidence/TASK_006B_Q/research-05/cases/D1.3704289a60eb0e48b6b672e92cd2705f922c2ef6cce55bebced5c2baa20f6c98.json
docs/evidence/TASK_006B_Q/research-05/cases/D1.4e58c20ec138539a5ef04e647f3ccde8f12a882cababe89a36e3a1f162830047.json
docs/evidence/TASK_006B_Q/research-05/cases/D1.7cc746b7c92a5428866fee6e879956a17de701b6e89b93ef148004ebeabb0565.json
docs/evidence/TASK_006B_Q/research-05/cases/M30.05d3bb5e13a5d4c2977d8dcf02f2fc6d5eab1af9a46566466dd18d4908d67fca.json
docs/evidence/TASK_006B_Q/research-05/cases/M30.755b3089a4fd679ac9a2fcc4886009258c15a70b0940f05b03ca1ce56e955315.json
docs/evidence/TASK_006B_Q/research-05/cases/M30.8870f83f7b518ef2088d469938a8bdeb3d71106904bc521071a783da128f37b7.json
docs/evidence/TASK_006B_Q/research-05/cases/M30.a3a166ff160bfe54bc038e7792527dae8b304e210dc53c75015b91b0173910bd.json
docs/evidence/TASK_006B_Q/research-05/cases/M30.f48912e4828773c2cae20f67cddd8b107258e674fcd193dcb84ef80315091d35.json
docs/evidence/TASK_006B_Q/research-05/cases/W1.126a6d0770a0aa3ff3dfd03dde00fa3bac6e1455cd483560a9e9ed34e75c88ba.json
docs/evidence/TASK_006B_Q/research-05/cases/W1.2f10656e4ac8603141e163f04b2795add10398e84a2bea300f4dbe96d6c7d4d3.json
docs/evidence/TASK_006B_Q/research-05/cases/W1.8c439c0b149ff513142d183e4b53b2b57da0f88c84185d5c4bcdd802942c103e.json
docs/evidence/TASK_006B_Q/research-05/cases/W1.fda26c6dedfeee6cd8872e195bf23895ce4ac810f2841ddb39d486e105b6aa12.json
docs/evidence/TASK_006B_Q/research-05/charts/D1.219c2df8eb70d731e8f1fa9be51a4f1fb81ce0a20d94aed15dc8fd4231a2cda6.png
docs/evidence/TASK_006B_Q/research-05/charts/D1.270c5807fb5e4a87ed06b37f568d9dd151ed47ab08afbef38eabec8d2011da3b.png
docs/evidence/TASK_006B_Q/research-05/charts/D1.3704289a60eb0e48b6b672e92cd2705f922c2ef6cce55bebced5c2baa20f6c98.png
docs/evidence/TASK_006B_Q/research-05/charts/D1.4e58c20ec138539a5ef04e647f3ccde8f12a882cababe89a36e3a1f162830047.png
docs/evidence/TASK_006B_Q/research-05/charts/D1.7cc746b7c92a5428866fee6e879956a17de701b6e89b93ef148004ebeabb0565.png
docs/evidence/TASK_006B_Q/research-05/charts/M30.05d3bb5e13a5d4c2977d8dcf02f2fc6d5eab1af9a46566466dd18d4908d67fca.png
docs/evidence/TASK_006B_Q/research-05/charts/M30.755b3089a4fd679ac9a2fcc4886009258c15a70b0940f05b03ca1ce56e955315.png
docs/evidence/TASK_006B_Q/research-05/charts/M30.8870f83f7b518ef2088d469938a8bdeb3d71106904bc521071a783da128f37b7.png
docs/evidence/TASK_006B_Q/research-05/charts/M30.a3a166ff160bfe54bc038e7792527dae8b304e210dc53c75015b91b0173910bd.png
docs/evidence/TASK_006B_Q/research-05/charts/M30.f48912e4828773c2cae20f67cddd8b107258e674fcd193dcb84ef80315091d35.png
docs/evidence/TASK_006B_Q/research-05/charts/W1.126a6d0770a0aa3ff3dfd03dde00fa3bac6e1455cd483560a9e9ed34e75c88ba.png
docs/evidence/TASK_006B_Q/research-05/charts/W1.2f10656e4ac8603141e163f04b2795add10398e84a2bea300f4dbe96d6c7d4d3.png
docs/evidence/TASK_006B_Q/research-05/charts/W1.8c439c0b149ff513142d183e4b53b2b57da0f88c84185d5c4bcdd802942c103e.png
docs/evidence/TASK_006B_Q/research-05/charts/W1.fda26c6dedfeee6cd8872e195bf23895ce4ac810f2841ddb39d486e105b6aa12.png
docs/evidence/TASK_006B_Q/research-05/charts/manifest.json
docs/evidence/TASK_006B_Q/research-05/dependency-audit.json
docs/evidence/TASK_006B_Q/research-05/endpoint-delta.json
docs/evidence/TASK_006B_Q/research-05/frames/D1.AS_OF.json
docs/evidence/TASK_006B_Q/research-05/frames/D1.OBSERVATIONAL.json
docs/evidence/TASK_006B_Q/research-05/frames/M30.AS_OF.json
docs/evidence/TASK_006B_Q/research-05/frames/M30.OBSERVATIONAL.json
docs/evidence/TASK_006B_Q/research-05/frames/W1.AS_OF.json
docs/evidence/TASK_006B_Q/research-05/frames/W1.OBSERVATIONAL.json
docs/evidence/TASK_006B_Q/research-05/freeze-readback.json
docs/evidence/TASK_006B_Q/research-05/freeze.json
docs/evidence/TASK_006B_Q/research-05/proof-and-enumeration.json
docs/evidence/TASK_006B_Q/research-05/protection.json
docs/evidence/TASK_006B_Q/research-05/validation.json
docs/research/PAQS_Q_PRIOR_RAW_VETO_ABLATION_R05.md
tests/research/paqs_q/r05/__init__.py
tests/research/paqs_q/r05/test_ablation.py
tools/research/paqs_q/r05/__init__.py
tools/research/paqs_q/r05/cases.py
tools/research/paqs_q/r05/charts.py
tools/research/paqs_q/r05/enumeration.py
tools/research/paqs_q/r05/freeze.py
tools/research/paqs_q/r05/metrics.py
tools/research/paqs_q/r05/model.py
tools/research/paqs_q/r05/protect.py
tools/research/paqs_q/r05/study.py
```
