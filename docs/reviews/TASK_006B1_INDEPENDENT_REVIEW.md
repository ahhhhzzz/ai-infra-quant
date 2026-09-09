# TASK-006B1 独立审查

日期：2026-09-09

结论：**CHANGES REQUESTED — 1 Major，未通过合并门槛。**

存档的版本、成员关系和离线读取基础已实现，但正常产品流程创建的证券无法通过新增存档入口。先修复 006B1-F01，再提交精确 SHA 做聚焦复核。本记录不合并任务、不改变权威分支、不启动后续任务。

## 1. 精确对象与范围

| 对象 | 核实结果 |
|---|---|
| Repository | ahhhhzzz/ai-infra-quant |
| 实现分支 | task/006b1-local-market-data-store-replay |
| 受审实现 | dafb73daf4aca6de421a3b330e7e81aa5c368e1f |
| 实现 tree | 3f1067d40cbb95a15654825be137dd57b950704e |
| 唯一直接父提交／更新后交接 | bed9059fd6ce6c0a7cd750376c972070db0a39dd |
| 权威分支 | roadmap/no-live-trading |
| 本轮 GitHub 读回权威 | 02326a3bb19c2a89352d765f5331670b5f3f466d |
| 审查写入分支 | review/006b1-independent |

依据：[原始范围合同](../../prompts/tasks/TASK-006B1_LOCAL_MARKET_DATA_STORE_REPLAY_FOUNDATION.md)、[Post-ADC 交接](../../prompts/tasks/TASK-006B1_POST_ADC_HANDOFF_2026_09_09.md)、当前架构和只读产品边界。
[实现报告](../reports/TASK_006B1_IMPLEMENTATION_REPORT.md)是实现者证据，不替代独立审查。

本地使用精确实现 SHA 的干净 detached worktree。复用的测试环境原本 editable 安装指向另一 checkout，因此正式执行显式设置 PYTHONPATH 指向本次受审 src。首次未设置时的 import collection errors 属于审查环境配置错误，不计为产品 finding。受审 runtime、测试、原报告和历史证据未修改。

## 2. Finding

| ID | 严重性 | 状态 | 问题 |
|---|---|---|---|
| 006B1-F01 | Major / P1 | OPEN | 存档错误依赖现有产品无法获得的 VERIFIED 状态，正常证券全部被 409 拒绝；测试预改状态掩盖该路径 |

### 006B1-F01：正常产品路径无法保存行情

直接位置：[market_data_archive.py](../../src/ai_infra_quant/application/market_data_archive.py) 的 capture，受审提交第 239–244 行，尤其第 241–242 行。

函数已经通过 resolve_research_security 取得并检查 canonical Security／只读市场映射，随后额外要求 security.verification_status == VerificationStatus.VERIFIED，否则在构造供应商前拒绝。

这与现有产品可达状态不相容：

- [seed.py](../../src/ai_infra_quant/database/seed.py) 创建的 AVGO、VRT、HK.09698 为 SYSTEM_SEED_UNVERIFIED。
- [SupportedSecurityService.add](../../src/ai_infra_quant/application/supported_security_service.py) 在行情供应商验证成功后创建／复用本地证券，不提升其原有 verification_status。
- [security repository](../../src/ai_infra_quant/database/repositories/security.py) 将新证券保持为 USER_SUPPLIED_UNVERIFIED。
- [Security domain](../../src/ai_infra_quant/core/domain/security.py) 与 [SecurityModel](../../src/ai_infra_quant/database/models/security.py) 的 user_supplied_fail_closed 约束明确要求用户新增证券保留该状态。直接把它们改为 VERIFIED 还会违反已有领域和数据库约束。
- 生产代码没有正常的 VERIFIED 状态提升入口。只读行情验证成功与旧证券／交易元数据验证状态不是同一件事。

测试为何没有发现：[archive_support.py](../../tests/browser/archive_support.py) 的 install 在第 141–142 行执行对全部证券的 SQL UPDATE，将 verification_status 改成 VERIFIED，然后才注入合成供应商。新增集成测试和真实浏览器 archive server 共用这个 helper。已有截图和通过结果证明的是这套预改状态的 fixture，并未证明普通数据库中的用户流程可用。

### 独立复现

使用全新临时 SQLite，从空库真实迁移到 0004，正常 create_app 初始化，不执行上述 install，不更改任何证券行。仅注入：

1. 原有 SupportedFakeProvider，为正常 supported-securities 接口提供有效 equity quote；
2. SyntheticArchiveProvider，为新存档服务提供正常 D1/M1/calendar；
3. 存档测试固定时钟，匹配合成数据。

通过真实 FastAPI 路由使用 TestClient，peer 与 base URL 为 127.0.0.1，POST 携带匹配的 Origin 与 JSON content type，满足写入边界。先读取默认 watchlist，再调用正常 POST /api/v1/watchlist/supported-securities，最后显式 POST /api/v1/market-data/archive/captures。

| 场景 | 正常添加／供应商验证 | 原样保留的数据库状态 | 存档结果 |
|---|---|---|---|
| 默认 US.AVGO | 正常 seed | SYSTEM_SEED_UNVERIFIED | HTTP 409 |
| 默认 US.VRT | 正常 seed | SYSTEM_SEED_UNVERIFIED | HTTP 409 |
| 默认 HK.09698 | 正常 seed | SYSTEM_SEED_UNVERIFIED | HTTP 409 |
| 再次正常验证并添加 US.AVGO | HTTP 200 / AVAILABLE | SYSTEM_SEED_UNVERIFIED | HTTP 409 |
| 正常验证并新添 US.NVDA | HTTP 201 / AVAILABLE | USER_SUPPLIED_UNVERIFIED | HTTP 409 |

五次存档响应均为：

```json
{"detail":"Archive requires consistent verified Security metadata"}
```

合成存档供应商 calls 始终为空。这排除了供应商不可用、行情权限、无数据、时间边界、真实 OpenD 登录等原因；失败发生在入口身份条件。

影响：当前功能的核心“保存当前行情”在正常新库、现有 seed 和正常新增证券路径不可达。重新添加证券也不能解决。不能要求用户手工改数据库或伪造 verified 状态。

### 修复边界与复核要求

原合同使用“已验证 canonical security”的措辞，但未授权改变 Phase 1 Security 状态和交易元数据语义。此处应结合已接受的只读 US/HK 市场身份校验理解，不能把旧 VERIFIED 字段当作产品中不存在的前置流程。修复须保留 canonical 身份、enabled equity、市场／币种／时区一致性和供应商返回事实校验。

- 在现有只读市场身份路径内使正常 seed 和正常 validated-add 的证券可显式存档；不要通过改 seed、Security verification/tradability 状态、原有领域／数据库约束或旧迁移来绕过。
- 去掉通用 archive fixture 的批量状态提升。合成供应商可注入，但正向用户流程必须从正常初始化和真实 supported-securities API 创建状态。
- 补充默认证券，以及通过正常接口添加 US 和 HK 证券后的存档成功／离线读回回归；断言前后证券原有 verification/tradability/metadata 状态未变化。
- 保留并验证未知 ID、禁用／非 equity、币种／时区冲突、供应商返回证券不匹配等负向拒绝；不增加隐式 quote、账户、模型或后台行为。
- 至少一个真实浏览器存档验收使用未预改证券状态的正常数据库路径；合成行情仍可使用。
- 保持版本去重、A→B→A、partial/error、离线分页、0003→0004 数据保留和当前 Analyze 边界，执行必要回归及项目交付门槛。
- 在原任务分支进行最小修复，新增独立 remediation report；原实现报告和截图保留其历史归属，修复后的新证据使用独立路径。提交／推送后提供精确 SHA，等待聚焦复核；不合并、不启动后续任务。

本 finding 不要求新增交易验证体系，也不授权扩展 006B1 范围。

## 3. 本轮独立验证

Linux、Python 3.12；使用项目已声明的测试依赖。所有验证数据库均为临时库，无用户数据库、真实凭据、付费模型或外部行情调用。

| 检查 | 本轮实际结果 |
|---|---|
| PYTHONPATH=受审src python -m pytest --ignore=tests/browser -q | **1264 passed, 7 skipped, 1 warning in 56.16s**，exit 0 |
| Ruff check | 通过 |
| Ruff format --check | 216 files already formatted |
| mypy --platform win32 src tests | 211 source files，无问题；Linux 上 Windows 目标类型检查 |
| git diff --check bed9059... HEAD | 通过 |
| 正常 seed／validated-add → archive 定向探针 | 复现上述 5 次 HTTP 409，exit 0；不是通过验收 |
| SQLite 0003→0004 内容保留、版本／离线／并发／回滚测试 | 在上述独立非浏览器回归中执行通过；正向 archive fixture 的状态预改限制见 F01 |
| PostgreSQL 双方言 DDL/type/FK | 回归中执行通过；未配置实库，不声称实库通过 |
| 新 archive 浏览器复跑 | 驱动初始化 PermissionError，未执行任何业务断言 |
| 提交截图视觉检查 | 实际打开 archive-390-dark.png、archive-1440-light.png；可见折叠详情、精确值表格和受限区域滚动，不证明正常状态的 capture 路径 |
| 实际 Uvicorn 进程重启／真实 Windows | 本轮未独立复跑；不将实现者报告归为本轮执行 |

7 项跳过为 1 项未配置 PostgreSQL 实库 URL、6 项缺少 PowerShell 的启动器测试。唯一 warning 为 Starlette BlockingPortal 弃用提醒。

浏览器尝试命令：PYTHONPATH=受审src python -m pytest tests/browser/test_market_archive_browser.py -x -q。首个场景在 playwright/driver/node 启动时得到 PermissionError: [Errno 13] Permission denied；结果 1 warning, 1 error in 0.14s。没有绕过限制、修改测试或把未执行计为通过。

实现者报告的 Windows **1388 passed / 1 skipped / 1 warning**、**118 项浏览器通过**及 Uvicorn 重启／离线证据保留原归属，不与本轮数字相加。F01 是这些测试未覆盖的正常状态问题，不能由总通过数排除。

## 4. 其余审查观察与保护范围

- 相对 bed9059... 的 53 个新增／修改路径处于存档应用／领域／port／持久化／API／局部前端、必要测试 allowlist、当前文档及新证据范围。
- 直接检查 integrations、resources、core/strategy、当前 Narrative/runtime、market_data_queries、seed、ExactDecimal types、0001/0002/0003、app.js、paqs-e.js、依赖、历史 prompts/reviews/decisions 等路径，Git diff 为空。
- 已读内容版本与成员关系实现、冻结日历和质量元数据、事务与不可变约束、本地 GET 和分页，以及前端选择 epoch。未在这些已检查路径确认第二个需返工问题；不代表未执行环境已获验收。
- 内容 hash 排除 retrieval，成员保留每次观察时间；保存旧 capture 使用明确 membership，未依赖当前 latest 内容拼接。已有回归覆盖 A→B→A 与精确 Decimal。
- 网络读取先于数据库事务；partial/error 未被写成连续零值。完成观察保守标 PARTIAL，并明确当前 QFQ 不等于严格历史 As-Of。
- GET 仓库没有供应商依赖；归档没有接入当前 Analyze、Research/Synthesis、Narrative Ledger 或交易行为。
- 现有测试修改主要为明确加入获准 0004/schema/model/API 项，未见为旧业务删断言；但新增正向 fixture 的预改状态是本次 Major 的关键验证缺口。

## 5. 当前状态

**006B1：IMPLEMENTED / INDEPENDENT REVIEW CHANGES REQUESTED / F01 OPEN / NOT INTEGRATED。**

本审查仅增加本文件。权威分支仍为 02326a3bb19c2a89352d765f5331670b5f3f466d，原任务实现未被修改。待原任务分支修复后，对新精确 SHA 聚焦复核 F01 与必要回归。
