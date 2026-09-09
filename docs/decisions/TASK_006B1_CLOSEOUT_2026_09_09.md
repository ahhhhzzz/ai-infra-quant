# TASK-006B1 用户验收、收尾与整合

日期：2026-09-09
状态：**REVIEWED PASS / USER-ACCEPTED / CLOSED / INTEGRATED**。

## 1. 授权与精确对象

用户在完成本地验收后明确要求“现在先做006B1的收尾吧”。本次据此整合已复核实现及两份审查记录，更新当前状态；不启动后续任务，不修改 runtime。

| 对象 | SHA |
|---|---|
| 整合前权威 roadmap/no-live-trading | 02326a3bb19c2a89352d765f5331670b5f3f466d |
| 原实现 | dafb73daf4aca6de421a3b330e7e81aa5c368e1f |
| 接受的 F01 整改实现 | 2e9889ae9d2587fcfac6d715923f8a791b2333d8 |
| 接受的 runtime 所属 tree | ca7f5222cd0a9a72caad439f16e5ff5fe51df6fa |
| 原独立审查提交 | d7bc395168e88fd2edfc68582ecba937d8513491 |
| F01 聚焦 PASS 提交 | c6f172b22e21d26fb0b1a34cd1f0c8840ebd3ead |

整合提交以旧权威为第一父提交、聚焦 PASS 为第二父提交、原审查为第三父提交；因此完整保留实现、整改和审查历史，不 squash/rebase/force-push。两份审查分支的正常合并树为 5293ae72943b2ff16cec0e769111d875be188b77，收尾仅在该内容上更新当前文档并增加本记录。最终整合提交 SHA 由 GitHub 读回与交接消息给出，不在文件中自嵌自身 SHA。

## 2. 用户本地验收

以下是用户报告及所提供截图的证据，不是助手直接操作其 Windows 电脑所得的独立测试。

- 联网状态下，用户使用 OpenD 保存 US.AVGO；首张截图显示 capture 时间 2026-09-09T08:29:35.187519Z，D1 1500 条、M1 30239 条、calendar 1501 条；已读取 M1 500 条且存在下一页。
- 用户明确澄清首张截图是在 OpenD 和行情供应商开启时取得，因此首张截图只用于保存／本地读取证据，不将其称为断源验收。
- 随后按指引关闭 OpenD、停止服务并以 MARKET_DATA_PROVIDER=none 重启，执行已存 Capture 的读取／周期切换／分页检查。用户回复“正常的”，第二张截图仍显示同一 Capture、D1 1500 / M1 30239，并显示 D1 本地读取 500 条和下一页入口。
- Capture ID：2babba19-e0ce-4bfa-aab9-93061a95818c。这是内部存档标识，不是券商账户标识。
- PARTIAL 表示未认证完整历史覆盖，不是保存失败；缺口 0 仅限实现检查的观察／日历范围，不证明严格历史数据完整。

本机验收目标为 2e9889ae9d2587fcfac6d715923f8a791b2333d8。用户提供的启动器日志显示 checkout 为该 SHA，但当时 running=missing-or-invalid。原因是此前助手提供的手动 Uvicorn 命令漏传启动版本环境变量；随后已给出从 git rev-parse HEAD 设置 AI_INFRA_SOURCE_REVISION 的正确重启命令。本次同步 README 手动启动说明。

没有收到修正后 /health 的 source_revision 读回或完整 git status，因此这里不把用户截图称为独立核实了精确 SHA 的运行证据。验收据用户操作确认和存档截图记录；实现精确 SHA 的代码／API／持久化独立证据由下面两份审查支持。本轮不上传用户数据库或原始行情数据集。

## 3. 独立审查与实现者测试归属

- [原独立审查](../reviews/TASK_006B1_INDEPENDENT_REVIEW.md)：发现 1 Major，正常证券因错误 VERIFIED 前置条件无法存档。
- [F01 聚焦复核](../reviews/TASK_006B1_F01_FOCUSED_RE_REVIEW.md)：F01 CLOSED；新增 Critical 0 / Major 0 / Minor 0。
- [整改报告](../reports/TASK_006B1_F01_REMEDIATION_REPORT.md)：实现者 Windows 完整测试 1401 passed / 1 skipped / 1 warning；单独浏览器 118 passed / 1 warning。PostgreSQL 实库未配置，双方言检查通过。
- 独立聚焦复核：56 passed / 1 warning，Ruff/格式/Windows 目标 mypy 通过；实际 Uvicorn 保存、正常应用重启后的精确内容读取和 M1 500＋101 分页通过，正常证券状态保持不变。
- 独立浏览器复跑在 Playwright driver/node 初始化时受环境权限限制，未执行业务断言；没有将实现者 Windows／浏览器结果改称独立执行通过。

上述结果不相加。原报告、原截图、审查文件和历史合同保持原字节，收尾不改写其当时待审查／未整合状态。

## 4. 本次整合范围和验证

只将已审查实现带入权威分支；收尾追加两份原字节审查记录、更新 10 份当前入口／状态／规格文档并增加本记录。生产源码、测试、所有迁移、依赖、策略、资源和历史实现证据相对接受实现完全不变。

收尾验证包括：精确分支／父提交检查、正常合并树检查、Git mode/type/blob 保留检查、当前文档相对链接检查、git diff --check，以及推送后的 GitHub tree／提交父链／权威 ref 读回。此次没有 runtime 变更，不重复执行已充分验证的业务／浏览器测试，也不声称本次重新完成那些测试。

本次不访问用户 Windows 数据库，不切换或清理其工作区，不删除未跟踪文件；不停止任何用户进程。远程任务分支和审查分支保留，权威分支只正常向前推进。

## 5. 已完成能力与待办边界

006B1 已完成显式保存有界 D1/M1/calendar、不可变观察版本与成员关系、去重和历史版本保留、重启后的本地列表／详情／分页读取。F01 使正常 seed 和正常新增 US/HK 证券可用，无证券验证／交易状态提升。

当前 K 线和 Analyze 继续使用原有当前行情路径；本地 Capture 不会自动成为图表或分析输入。存档不构成严格历史 As-Of 数据或策略有效性／收益证明。

用户曾考虑使用缓存加快行情读取，随后明确需求是低频的“OpenD 离线时手工选择存档显示 K 线，并分析该存档”。记录为未启动待办，不给出新任务编号或实现授权：

- 不启动自动缓存、后台监测、增量同步或加速改造；
- 未来若做存档 K 线／Analyze，需独立合同，明确 Capture ID、采集时间、历史模式与新分析证据关联；
- 读本地图表可完全断网，模型 API 分析仍需其网络连接；研究默认关闭，并明确模型知识／外部研究的历史信息限制；
- 不启动 PAQS-Q 后续、007D、严格 As-Of/GoldSet、Paper/PnL、Phase 3/4 或实盘／账户行为。

本次仅收尾 006B1。Phase 2 仍是当前工程阶段，下一项任务尚未授权启动。
