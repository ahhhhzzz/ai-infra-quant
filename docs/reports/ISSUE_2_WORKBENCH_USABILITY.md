# Issue #2 工作台可用性维护

日期：2026-09-30。基线 `a07b2723329f6718ac3926d7c43b486882c2f929`（v1.0.0），任务分支 `task/v1-1-workbench-usability`。复用既有 Windows 目录和 `.venv`。本报告对应所在任务提交；不修改产品分支、v1.0.0 标签或 Release。

用户已明确选择：本轮保留独立 M30 开盘证据缺口与严格规则，完成其余四项维护。未增加常驻采集、行情订阅、交易接口、收费模型或 Tavily 调用。

## 实现

| 范围 | 结果 |
| --- | --- |
| A 名称 | 已验证身份的 OpenD snapshot.name 经独立展示类型传递；新建证券直接使用，旧代码占位通过「补全证券名称」更新。原子条件更新保护自定义名称，身份/市场/币种不变。中文、长名称、HTML 按文本展示。 |
| B 数据与解释 | 原始规范化 D1/M1、日历、派生数据和接收时间保存为新 Q 的 source_capture；canonical 摘要及派生成员摘要绑定，成员 OHLCV 和 M30 连续性校验。修复采集窗口外 M30 缺口误计。W1/D1/M30 背景、输入问题、候选阶段、下一条件与证据范围分开呈现。Stage B 缺证据保留同候选 Stage A 价格，已失效候选仅作历史。小数显示使用字符串/BigInt 舍入，完整 Decimal 留在详情。 |
| C 同快照 | 服务端按所选 Q 的证券、snapshot_hash 过滤 E，再限量；完整比较身份校验保留。无记录、异快照、删除、失败分开提示。显式从 Q 新建 E 固定本次不联网，不改变 E 页 Tavily 勾选；成功刷新并选中结果。 |
| D 历史清理 | 0007 仅增加 analysis_visibility；删除/恢复幂等且事务串行化。默认历史、最新及匹配过滤删除项；直接读取 ID 返回 410。内部修订链仍使用原证据。确认框列证券、类型、时间；已删除入口可恢复。请求版本守卫防止删除或切换后旧响应重新显示。 |

## 实际数据链核查

最终有限 OpenD 采集：HK.09698 / 万国数据-SW，Q 记录 `16db5144-001a-4cca-b97a-b84d8924278c`，HTTP 201，冻结摘要 `b23ec46b068a4c50e01faa251c7f1a76e878a5a33022adc5ac3c5e42d3a4d394`。详情见 [真实结果](../evidence/TASK_V1_1/live-opend-final.json)。

| 环节 / 缺口 | 实查与处理 | 周期 / 阶段影响 |
| --- | --- | --- |
| 请求范围与分页 | 保持 1500 D1 / 30 日 M1，请求每页 1000、沿 page_req_key 有界读取；分页成功/失败/上限由适配器回归覆盖。真实取得 1455 D1、7282 M1，没有为消除警告无限增加范围。 | 来源留存全部规范化返回行；快照仍按既有上限使用 156 W1、500 D1、200 M30。 |
| 完成与接收时间 | 原代码把请求前时刻当 retrieved_at；现为成功接收后记录。分钟完成过滤仍使用请求开始时刻，保守排除请求过程中才完成的 K 线。 | 不把现在接收时间作为过去 available_at；未完成分钟不进入 Q。 |
| 来源传递丢失 | 旧 PaqsInputBundle 未保留原始分钟，派生来源诊断固定缺失。新增 capture 保留原始分钟、获取时间、窗口，并验证派生价格及连续成员。 | 新记录可追踪 W1←D1、M30←M1；有来源时去掉该项缺失诊断，不修改旧结果。 |
| 窗口前缺口误计 | 30 日窗口开始于首日收盘后，却按整日算 11 桶缺失。现只计算完整落入请求窗口的桶。 | 真实缺口计数从 33 降至 22；未抹掉窗口内真实不完整区间。 |
| HK 时间标签未能满足现有桶 | 22 个交易日各有 331 个来源标签；常规时段的 13:00 缺失，另有 12:00 和 16:00 标签。现有适配把 time_key 当区间起点，因此每天 13:00–13:30 缺一个成员。 | 完成 M30 为 220；M30 Context 为 INSUFFICIENT / MISSING_EXPECTED_BAR。未臆造 13:00、移位标签、扩展时段或放宽完整性。 |
| ATR 与日历 | W1/D1 Context 均 AVAILABLE，最新 ATR 约 3.18 / 0.99；早期预热不进入当前阻断。日历覆盖完整请求范围和计划闭市事实，当前周的 1 个 W1 partial 正常保留。 | W1 为区间，D1 背景不确定；计划日历不认证临时休市和历史日历版本。 |
| 独立 M30 开盘 | 产品无合格独立源，entry_reference_count=0；已完成 K 线 open、今日 open、最新报价均未代用。 | Stage B 无下一开盘资格。用户已选择保留缺口；Stage A 若存在仍可展示指示性评估。 |
| 严格历史证据 | 当前 QFQ、历史价格/日历 available_at 没有 PIT 证明。 | 保持 OBSERVATIONAL；不宣称 LONG_READY 或严格回放通过。 |

富途 [历史 K 线文档](https://openapi.futunn.com/futu-api-doc/quote/request-history-kline.html) 的 time_key 描述未足以证明该港股边界标签应如何重映射。每天标签缺口是本轮原始数据检查所得，不等同于已证明供应商丢行情。未来若处理，先用可核验供应商口径/逐笔对照确认标签语义，再按版本协议修改归一化与重新验证；本轮不推断移位规则。按实际到达时间重新定义开盘资格或持续采集，也需另行批准。

## 验证

- 最终后端聚焦命令：`.venv\Scripts\python.exe -m pytest tests/unit/test_workbench_capture.py tests/unit/test_paqs_q_product_input.py tests/unit/test_paqs_q_product_analysis.py tests/unit/test_futu_quote_adapter.py tests/unit/test_paqs_market_snapshot.py tests/integration/test_workbench_usability.py tests/integration/test_supported_security_api.py tests/integration/test_paqs_input_api.py tests/integration/test_paqs_q_product_api.py tests/integration/test_paqs_q_e_frozen_api.py tests/integration/test_paqs_q_analysis.py tests/integration/test_paqs_e_narrative_ledger_api.py tests/paqs_q_event/test_registry_artifacts.py tests/architecture/test_task006b1_boundaries.py -q --tb=short`：**143 passed / 164.98s**。
- Windows Chrome：`tests/browser/test_workbench_usability.py tests/browser/test_paqs_q_workbench.py tests/browser/test_dashboard_readability.py`：**14 passed / 19.41s**。覆盖名称、有效观察性/严格资格区别、Stage A 保留、候选结束/多候选、ATR 历史原因、Tavily 开启时独立不联网生成且原勾选保留、取消/删除/恢复、过期对照响应及移动宽度。
- 匹配测试构造超过 20 条较新异快照 E，仍找回旧匹配；同证券异快照不误配。收费链路仅 mock，不代表实际模型验收。
- SQLite/API 验证删除幂等、并发、重建仓储后状态持久、跨证券 409、未知 ID 404、非法输入 422、同源限制 403、直接 ID / compare / run 410；恢复前后 payload、hash、不可变触发器和修订链不变。
- Ruff：变更源代码/相关测试/迁移验证工具通过；Mypy：**169 source files 无错误**；`git diff --check` 通过。
- 三份 Context/Event/Setup manifest 校验通过；**51 个受覆盖文件与基线相同**，见 [manifest 证据](../evidence/TASK_V1_1/manifests.json)。
- 实际页面从最终 Q 历史读取，Chrome **0 page errors、0 写请求**，未运行模型，见 [浏览器记录](../evidence/TASK_V1_1/live-browser.json)。真实 E 同快照列表正确显示尚无 E 分析。

扩展检查曾运行 `tests/architecture` 等：158 passed、7 failed。其中 0005 迁移测试错误地 upgrade head 后仍断言 0005，已改成测试明确的 0005 迁移并复验通过。其余 **6 项旧架构断言仍未通过**：四项迁移白名单止于 0004、一项模型白名单不含基线已有 Q/Tavily、一项全仓禁止 paqs_q（基线早已正式接入）。这些文件未修改；[基线静态核对](../evidence/TASK_V1_1/legacy-test-baseline.json)记录基线已有 0005/0006、Q/external_research。没有将扩展检查称为全绿，也未运行全仓测试或收益研究。

## 数据、环境保护

迁移前用 SQLite backup API 保存本机忽略目录中的 `data/backups/before_issue2_20260930_173721_020431.db`。0006→0007 迁移比对全部 28 张原业务表逐行摘要和原触发器；完整性 ok、外键违规 0，见 [迁移证据](../evidence/TASK_V1_1/migration.json)。最终再核对所有旧行：只允许 HK.09698 的 display_name 和 updated_at 更新，所有旧 Q/E 及共享来源原样保留，原触发器完全一致，见 [最终保护核验](../evidence/TASK_V1_1/preservation-final.json)。

本轮显式验证新增 4 条 Q 记录：2 条初期 provider 未配置/SDK 日志权限不足的真实失败证据、2 条成功读 OpenD 后的分析；不回写或删除旧行。SDK 日志权限问题通过获准的任务验证服务解决，没有修改供应商配置。`.env`、凭据、启动器和用户原有 8000 服务未修改；任务验证服务使用独立本机 8011 端口与进程环境变量。数据库、备份、服务日志和凭据不入 Git。原有未跟踪 `phase1_remediation_commit.txt` 保留。

## 页面截图

均为 Windows Chrome 实际渲染；合成样本已在页面标明，不作为真实市场通过证据。

- [修改前本机页面](../evidence/TASK_V1_1/before-local.png)（当时页面尚在刷新）。
- [修改后真实 HK 名称 / Q 背景与缺口](../evidence/TASK_V1_1/after-local-final.png)。
- [修改后真实同快照入口](../evidence/TASK_V1_1/after-compare-local-final.png)。
- [合成：Stage A 保留、Stage B 缺证据](../evidence/TASK_V1_1/after-stage-a-synthetic.png)、[候选价格详情](../evidence/TASK_V1_1/after-stage-a-prices-synthetic.png)。
- [合成：已删除记录与恢复入口](../evidence/TASK_V1_1/after-deleted-synthetic.png)。

原网页版本徽标仍是已发布的 v1.0.0；本次没有创建新 Release。新 Q 记录的 product_version 为 1.1.0。
