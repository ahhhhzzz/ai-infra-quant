# TASK-006B-Q — implementation and structural stability report

状态：**研究原型实现和工程验证完成，等待独立审查；真实行情门槛 INCOMPLETE；不建议直接采纳到产品。**
本报告不宣告 PAQS-Q 策略完成，不评价预测能力、交易收益或与 PAQS-E 的一致率。

## 1. Git authority and scope

| Object | Exact SHA |
|---|---|
| Authoritative `roadmap/no-live-trading` | `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f` |
| Starting task HEAD / issued contract | `3e547189fa446bb04913e5fecc73720e424cc240` |
| Contract parent and merge base | `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f` |
| Profile/universe freeze | `6285fe319e6a1af07715455d404d3ec81bbd640c` |
| Executable source and tests | `e67575f3de064f9badb2fd06791e7fc803251bb9` |

已 fetch 并从 GitHub 远程引用核验上述对象；提交实现前再次 `ls-remote`，任务分支仍为开工 SHA，
权威分支仍为指定基线。使用独立 worktree `D:\AI_Infra_Quant_Codex_v1\task006b-q-worktree`。
最终证据提交是上述实现的后代；其准确 SHA 由交付响应和 GitHub 分支读回给出，避免在提交中自引用自身哈希。
仅正常推送 `task/006b-q-structure-formalization`；不修改或合并权威分支。

开工已完整阅读 AGENTS、当前治理/架构/策略/需求文档、双分支决定、006B1 closeout、原 006B 合同及整改、
基线结构源码，以及精确历史研究提交 `01000900861d4506fb35fbf423901a5b9a306499` 的稳定性审查与 Lite 候选。
当前权威文档通过既有完整读取与全部后续 Git 差异核对确认；未采用其他工作区的未提交内容作为权威。

## 2. Deliverable and mathematics

[数学规格](../research/PAQS_Q_STRUCTURE_MATH_CANDIDATE_V1.md) 从候选 V1 明确为执行澄清 1.1，
在真实结构诊断之前提交冻结。数值参数未根据行情表现调优。新增的明确内容为：canonical wire schema、
Decimal/UTC/空值/数组序列化、可用版本选择、UNKNOWN availability 的观察模式、四臂边界区间和语义比较投影。

原型为独立计算：没有调用旧引擎来生成新 Pivot。旧引擎只在诊断模块进行基线比较；存档适配器只复用
不可变领域类型及已接受的 006A 聚合。D1 聚类的 complete-link、ATR 归一化距离、独立触点、median/MAD、
clamp 和合并规则来源于基线纯算法，移植到候选的 active-only 单层 Pivot 输入。不存在产品 import/wiring。

| Timeframe | Warm / Active / N | Lambda | Decision scope |
|---|---|---|---|
| W1 | 26 / 104 / 130 | 1.8 | 单层 Pivot、独立 Regime |
| D1 | 60 / 252 / 312 | 1.8 | Pivot、最多四个 confirmed zones、最近区间、Regime |
| M30 | 40 / 160 / 200 | 1.0 | 常规时段完整桶、Pivot、独立 Regime |

金融运算使用独立 Context(50, HALF_EVEN)；TR、EMA-TR14、median、比例和几何按 1e-18 量化。
Pivot 的 lambda×ATR 阈值使用完整 context-50 乘积比较。没有二进制浮点金融运算。
UNSEEDED 双向反转同时成立时保持不确定；更新极值在前，同根不能自确认，同价取最早，后续极值间隔至少两根。
warm 触点不能形成 active zones 或暗中支持方向；方向需要两个 active HIGH 和两个 active LOW 的最新比较。
最新 Close 跌破 HL/升破 LH 时只移除趋势，不制造事件或交易建议。

D1 独立触点间隔五根，寿命从极值计 126 根，不能被迟到确认刷新。每侧选最近两个 zone，不翻转角色。
区间的反应和 Close 必须来自同一最近 L=40 窗口，两侧各至少两次反应、至少四次交替、inside>=0.70，
中心间距在同窗 median ATR 的 [2,12] 内，最新 Close 仍在区间内。内容版本 ID 与连续 RANGE 状态分别统计。

输出含独立 input status、结构充分性、Regime、操作数/比较符/阈值及 bar 引用；冻结对象/JSON 文本不可变。
semantic hash 只包含有界观测、cutoff、规则/参数及决策证据。完整源包哈希、获取时间、诊断、运行时间分离。
未知可用时间不会伪造成历史发布时间；AS_OF 排除未知版本，OBSERVATIONAL 明示其限制。

## 3. Real data, quota and reproducibility

按用户授权调查本地仓库，找到唯一真实 AVGO Capture：

- 数据库：`D:\AI_Infra_Quant_Codex_v1\ai_infra_quant_codex_v1\data\ai_infra_quant.db`。
- Capture：`2babba19-e0ce-4bfa-aab9-93061a95818c`，完成于 `2026-09-09T08:29:35.187519Z`。
- 原始归档：D1 1500 根（2020-09-17 至 2026-09-08）、M1 30239 根、日历 1501 条。
- Provider：`futu_opend_quote`；`PROVIDER_QFQ_CURRENT`，adjustment epoch 未知，非历史信息集安全。
- 源库读前/读后 SHA256：`81b32a5f0f74e5549e99414456f189d5111435e3601b00bcd3e43c41ee2f1034`。

仅 SQLite `mode=ro` / `query_only=ON` / BEGIN 快照，校验 Capture、行情版本、成员关系和精确数值列。
未启动应用、未查询账户/凭据、未调用 OpenD；本次历史额度消耗 **0**。没有网络获取行情、补造日历、填价或供应商 M30 替换。
归档批次本来为 PARTIAL，保持 PARTIAL；D1/日历的 missing_count=0 只针对返回的日历，不代表已独立认证完整性。
沿用 006A 派生，排除首个不完整日历周和未完成/不完整桶。规范化得到 1500 D1、312 W1（311 可用）、273 M30。

价格从存储的 Decimal 文本读取，保留其字节数值；不能追溯认证原 SDK 是否已损失二进制浮点精度，故真实输入属于
近似的研究观察，不是精确 Decimal 测试 oracle。日历来源为原 Capture，未独立核验历史节假日/半日细节。
US exchange mapping 是供应商的 `US.<symbol>` 市场映射；原 Capture 没有 primary-listing MIC，未冒称完成交易所上市地点认证。
完整字段、请求/实际覆盖、源哈希及限制见 [source manifest](../evidence/TASK_006B_Q/source-manifest.json)。

冻结 universe 是 24 US / 16 HK 共 40 只、固定行业抽样、固定 not-after 和最后 100 个连续完成终点。
没有看结果后换股或选有利日期。单只 AVGO 不能替代其余 39 只。

| Timeframe | AVGO eligible bars | Valid terminal cutoffs | 40-symbol result | Shortfall |
|---|---:|---:|---|---|
| W1 | 311 | 100 | 1 valid / 0 insufficient / 39 unavailable | 3900 / 4000 cutoffs unavailable |
| D1 | 1500 | 100 | 1 valid / 0 insufficient / 39 unavailable | 3900 / 4000 cutoffs unavailable |
| M30 | 273 | 74 | 0 valid / 1 insufficient / 39 unavailable | 3926 / 4000 cutoffs missing |

US 各 timeframe 分母 24，HK 分母 16；HK 全部 unavailable。M30 的最初 26 个计划终点不能提供 N=200，
保留为 insufficient，不拼接成虚假连续样本。M30 达到 100 个有效终点需要 299 根，当前少 26 根。
真实门槛是 **INCOMPLETE**，与是否通过合成测试无关。

[证据 README](../evidence/TASK_006B_Q/README.md) 给出不联网的 archive/example/analyze/study/benchmark/verify 命令。
原库完整保留，规范化文件保存在 worktree 外的 `task006b-q-data`，不提交数据库或批量行情。
拥有同一 Capture 或完全相同导出文件的审查者可以重跑；没有这些文件的审查者只能重跑合成验证。
不能保证未来从供应商重新获取的 QFQ 字节相同，不以哈希替代这种实际可用性说明。

## 4. Stability results and unresolved semantics

| Metric | W1 | D1 | M30 |
|---|---:|---:|---:|
| Valid cutoffs | 100 | 100 | 74 |
| BULL / BEAR / RANGE / UNCERTAIN | 13 / 0 / 0 / 87 | 4 / 0 / 0 / 96 | 20 / 3 / 0 / 51 |
| State changes / adjacent transitions | 6 / 99 | 1 / 99 | 9 / 73 |
| Churn per 100 | 6.060606 | 1.010101 | 12.328767 |
| Origin violations / future references | 0 / 0 | 0 / 0 | 0 / 0 |
| Material LEFT_ONLY cases | 4 | 1 | 7 |
| Direct BULL ↔ BEAR flips | 0 | 0 | 0 |
| Old bounded vs new regime disagreements | 0 / 100 | 75 / 100 | 36 / 74 |

低 churn 不等于结构有用：D1 的 UNCERTAIN 比例为 96%，不能凭不变化宣告稳定性采纳。
所有源质量仍为 PARTIAL。没有真实 RANGE，故其实际持续性、zone cap 是否压制附近有效区间、寿命/区间参数的稳定性
在此样本中缺乏辨识力；零分歧不是这些参数已经得到真实市场验证。

OFAT 没有选择最优参数。W1 lambda=1.7/1.9 的 Regime 分歧为 4/100、35/100，结构分歧为 57/100、55/100；
D1 1.7/1.9 为 0/100、4/100，结构分歧 0/100、38/100；M30 0.9/1.1 为 2/74、1/74，结构分歧 44/74、45/74。
D1 epsilon=.45/.55、age=100/160、L=30/60 各有 100 对，当前观察均无结构分歧，不能外推。
全部 239 个参数分歧记录和 27 个 material boundary 记录保留在各 timeframe JSON，无阈值调优或删案例。

12 个 material LEFT_ONLY 已逐项读回四臂、参考时间及 Regime，详见
[boundary case review](../evidence/TASK_006B_Q/boundary-case-review.json)。
W1 为 2025-05-30、08-15、08-22、08-29；D1 为 2026-08-03；M30 为 2026-09-01 16:00/16:30、
09-02 17:00、09-04 18:00/18:30、09-08 17:00/18:00，均为 UTC。
OLD=RIGHT、LEFT=BOTH 的观察成立：部分是 active 极值退出，其余是左端重播使原先确认的结构出现/消失。
M30 有 UNCERTAIN 与 BEAR/BULL 之间的来回变化，即使不存在直接 BULL↔BEAR，也不应称为已解决的市场稳定性。
这些是操作性归因，不是因果或经济解释；在更广样本和语义审查前不建议采纳。

同输入旧/新比较包含每个有效终点的旧 Major bounded Regime，以及最后终点的旧 full/旧 bounded。
旧参数保持基线值，不冒称其与候选 lambda 或单层设计相同。合成 `path_lock` 在早期 bar 13 设置同时满足双向反转的
高低价；旧 full 得到 0 Pivot，新有界窗口得到 21 个 active Pivot，证明远端路径依赖可被有界设计隔离，
不证明当前窗口内的 UNSEEDED 模糊已经消失。合成涨/跌漂移旧引擎分别保留 12/11 个寿命超过 126 的 confirmed zones，
新决策按 active/age/cap 排除；价格搬迁案例旧有 2 个过期 confirmed zones，新只保留两条当前 zone。
真实历史 AVGO 的完整、逐字节原研究输入未提供，因此没有声称复现旧研究截图或每个历史案例。

待解决的语义问题：两高两低 active 证据是否过严；warm 起点导致的双向模糊/ATR 重播是否可接受；W1 参数微调的较大分歧；
zone 寿命/上限和最近 range 在真实样本中的作用；当前 QFQ、未知发布时点及来源日历对结论的影响。
这些问题应在独立研究审查与所有者语义决策中处理，本轮未擅自加滞回、平滑、重试或策略分支。

## 5. Validation and performance

在 Python 3.12.14、pytest 8.4.1、Ruff 0.12.9、mypy 1.17.1 的既有环境中执行；项目依赖/锁/配置保持不变。

```text
python -m pytest tests/research/paqs_q -ra
52 passed, 1 warning in 1.81s

python -m pytest tests/unit/test_paqs_structure.py tests/unit/test_paqs_input.py tests/integration/test_paqs_structure_api.py tests/integration/test_paqs_input_api.py tests/architecture/test_task006a_boundaries.py tests/architecture/test_task006b_boundaries.py -ra
59 passed, 1 warning in 15.37s

python -m ruff check tools/research/paqs_q tests/research/paqs_q
All checks passed!
python -m ruff format --check tools/research/paqs_q tests/research/paqs_q
17 files already formatted
python -m mypy --explicit-package-bases tools/research/paqs_q tests/research/paqs_q
Success: no issues found in 17 source files
python -m mypy --explicit-package-bases --platform win32 tools/research/paqs_q tests/research/paqs_q
Success: no issues found in 17 source files
git diff --check
```

唯一 pytest warning 是既有 Starlette 的 `anyio.abc.BlockingPortal` alias 弃用。
没有 skip/xfail/弱化断言。开发期曾修正不正确的合成路径锁样例与半日日历 fixture；最终保留完整回归，失败原因和修正
均与本原型相关。`--explicit-package-bases` 解决新增 namespace 目录的模块寻址，不放宽 strict mypy。
合同第 5 节明确本隔离研究不要求无关全业务/浏览器/Uvicorn，因此未运行这些检查，也不宣称通过。

性能测于 Windows 11 build 26200、Intel Core i7-14650HX，Python 3.12.14。每种最大窗口十次，固定三角波周期 24，
实际 Pivot 数 W1=10、D1=25、M30=16；D1 候选 zone=2，pair distance=100、range pair=2。

| Timeframe | p50 ms | p95 ms (nearest rank) | Peak Python allocation bytes |
|---|---:|---:|---:|
| W1 | 234.5106 | 303.8223 | 236877 |
| D1 | 641.38395 | 738.7547 | 558347 |
| M30 | 381.7842 | 449.2360 | 360734 |

原始 p50/p95、Python 分配峰值见 [performance.json](../evidence/TASK_006B_Q/performance.json)，包含 tracemalloc 开销、
有界序列化与源哈希。不是服务 SLA，也不是极限 Pivot 密度 benchmark；峰值不等于进程 RSS。
CPU 通过系统 registry 只读信息确认；CIM 的额外机器信息查询被系统拒绝，未把不可用内存信息编造为测量值。
计算 ATR/Pivot O(N)，complete-link O(P²)，重复 merge 最坏 O(P³)，range O(Z²·(L+P))；全历史的读取/版本选择/源哈希
仍有 O(M) 成本。参数对照复用同一组已选择的 N 个观察，避免重复解析全历史，不引入服务缓存。

## 6. Changed files and protection

所有变更在合同允许清单中，完整机器列表见 [protection.json](../evidence/TASK_006B_Q/protection.json)。

- `docs/research/PAQS_Q_STRUCTURE_MATH_CANDIDATE_V1.md`：规则澄清与冻结引用。
- `tools/research/paqs_q/`：`__init__.py`、`types.py`、`engine.py`、`zones.py`、`fixtures.py`、`io.py`、
  `__main__.py`、`diagnostics.py`、`study.py`、`verify.py`、`integrations/__init__.py`、`integrations/local_archive.py`。
- `tests/research/paqs_q/`：`test_engine.py`、`test_zones.py`、`test_diagnostics.py`、`test_inputs.py`、`test_scope.py`。
- 本报告及 `docs/evidence/TASK_006B_Q/`：README、profile、universe、protected-base-tree、rule-matrix、source-manifest、
  coverage、三份 AVGO diagnostics、synthetic-cases、boundary-case-review、performance、validation、protection。

保护核验：377 个非允许文件维持基线 Git mode/type/blob；工作树 diff 同时核验未暂存内容；issued contract 单独按起始提交
blob 核对。工具检查全部十二项规则引用和 26 个新增文档本地链接。产品源码、现有测试、配置、迁移 0001–0004、PAQS-E、
Narrative/Legacy、行情刷新/Analyze、原报告和历史审查证据未变。没有新 API/UI、数据库写入、自动扫描或后台 worker。

其他 worktree、未跟踪文件、用户数据库和 `phase1_remediation_commit.txt` 保留。后者前后 SHA256 为
`c791ba73b41c4e7719957607e025105a8110fa54a2e1a67f3c5b142da8030440`。
没有 Event/Setup/RR、EMA/ROC 确认、交易建议、P&L/回测优化、券商或模型调用。

## 7. 给使用者的解释与交接

机器只能说明：在固定的一段已完成行情中，哪些高低点由随后收盘价确认、哪些仍在当前证据窗口内、
是否有足够的两侧结构支持趋势，或是否存在近期反复反应的 D1 区间。它会把依据对应到具体 K 线和阈值。
数据不足、ATR 为零、极值确认有歧义、active 比较不够、方向冲突或最新价破坏原方向时，返回 UNCERTAIN。
它不判断该买卖什么，也不保证滚动下一根时先前图形不会重算。

工程执行：**PASS（限定本报告验证范围）**。真实行情门槛：**INCOMPLETE**。
结构鲁棒性：**有已记录的左边界敏感性，等待语义审查；不建议直接产品采纳**。
预测/交易表现：**未评估**。停止于独立审查；不合并、不接产品、不启动 006C-Q。


## 8. Delivery transport blocked

本地最终内容已提交，但本次正常推送尚未成功。普通 HTTPS push 和仅单次生效的 HTTP/1.1 push
均失败，错误为：`Failed to connect to github.com:443 after 21095 ms: Could not connect to server`
（第二次 21093 ms）。再次只读 `ls-remote` 也出现 curl 28 连接超时。
这不是自动审批拒绝，没有改 Git 配置、重建远程提交、强推或覆盖引用。

通过独立 GitHub connector 读回，远程任务分支仍为
`3e547189fa446bb04913e5fecc73720e424cc240`，权威分支仍为
`8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`。尚不能提供包含本实现的有效 GitHub 报告链接，
也不能声称最终 SHA 已在 GitHub 核验。需恢复这台机器对 GitHub 的连接后完成已授权的正常推送和读回；
本地提交、证据、数据库及其他工作区均保留。交付传输状态：**BLOCKED_BY_NETWORK**。
