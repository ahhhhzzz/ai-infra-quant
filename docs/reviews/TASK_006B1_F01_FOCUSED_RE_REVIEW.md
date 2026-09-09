# TASK-006B1-F01 独立聚焦复核

日期：2026-09-09

结论：**FOCUSED CODE / CONTRACT REVIEW PASS。006B1-F01 CLOSED。新增 Critical 0 / Major 0 / Minor 0。**

本轮只复核 F01 整改差异、正常证券状态路径及必要回归，不重复完整初审。结合原独立审查，006B1 已无未关闭的已确认 finding，可进入用户验收和经授权的整合流程。本轮未合并、未改变权威分支、未启动后续任务。

浏览器独立复跑仍在驱动初始化阶段因环境权限失败；本结论不声称独立完成全部浏览器或真实 Windows 验证。具体证据归属见下文。

## 1. 精确对象

| 对象 | 核实值 |
|---|---|
| Repository | ahhhhzzz/ai-infra-quant |
| 任务分支 | task/006b1-local-market-data-store-replay |
| 本轮受审整改 SHA | 2e9889ae9d2587fcfac6d715923f8a791b2333d8 |
| 唯一直接父提交／原受审实现 | dafb73daf4aca6de421a3b330e7e81aa5c368e1f |
| 整改 tree | ca7f5222cd0a9a72caad439f16e5ff5fe51df6fa |
| 原审查提交 | d7bc395168e88fd2edfc68582ecba937d8513491 |
| 权威 roadmap/no-live-trading | 02326a3bb19c2a89352d765f5331670b5f3f466d |
| 本轮报告分支 | review/006b1-f01-focused |

GitHub 提交读取与本地 fetch 后的 Git 对象一致。使用新建干净 detached worktree，PYTHONPATH 显式指向本次受审 src 和仓库根，避免共享虚拟环境的旧 editable checkout 影响测试。

依据：

- [原独立审查及 F01](https://github.com/ahhhhzzz/ai-infra-quant/blob/d7bc395168e88fd2edfc68582ecba937d8513491/docs/reviews/TASK_006B1_INDEPENDENT_REVIEW.md)
- [本次整改报告](../reports/TASK_006B1_F01_REMEDIATION_REPORT.md)
- [原始合同](../../prompts/tasks/TASK-006B1_LOCAL_MARKET_DATA_STORE_REPLAY_FOUNDATION.md)
- [Post-ADC 交接](../../prompts/tasks/TASK-006B1_POST_ADC_HANDOFF_2026_09_09.md)
- 本会话用户授权的 F01 聚焦整改指令及当前项目约束。

原审查保留历史 CHANGES REQUESTED 结论；本文件关闭其中 F01，不改写原报告。

## 2. F01 关闭依据

| 验收项 | 独立复核结果 |
|---|---|
| 移除错误 VERIFIED 前置条件 | capture 保留 resolve_research_security，只移除其后的额外状态判断及无用导入 |
| 不提升证券状态 | seed、Security domain/model/repository 和数据库约束均未修改 |
| 测试不预改状态 | archive_support.install 删除批量 UPDATE，只注入合成行情服务 |
| 正常 seed | AVGO、VRT、HK.09698 通过真实 POST 存档和 GET 离线读回，完整证券详情前后相等 |
| 正常新增 US/HK | 真实 supported-securities API 添加 us/nvda、hk/700，得到 US.NVDA、HK.00700；存档成功且完整详情不变 |
| 原有拒绝条件 | 未知 ID 404；禁用／非 equity 422；币种／时区冲突 409；不支持 provider 422；均无供应商调用和 capture |
| 返回数据不匹配 | bar 证券或 provider 不匹配时返回 503、零存档并释放 context |
| API 错误文案 | 409 改为市场数据身份不一致，不再暗示升级 VERIFIED |
| 浏览器测试状态真实性 | configure 前后及保存／离线读取后比较正常 seed 详情，明确断言原始三个状态；本轮检查代码，浏览器执行限制单列 |

新增 [F01 集成测试](../../tests/integration/test_market_archive_f01.py) 的正向用例不调用通用 install helper，不修改证券行；使用真实 create_app、迁移和路由，只替换外部行情供应商与固定时钟。阴性测试中的显式元数据污染仅用于验证拒绝，没有混入正向路径。

五个正向场景保留 SYSTEM_SEED_UNVERIFIED 或 USER_SUPPLIED_UNVERIFIED，以及 UNVERIFIED / UNAVAILABLE。每次存档仅产生 enter、D1、M1、calendar 调用，context 释放一次。显式添加证券仍使用原有一次 quote 验证；存档不新增 quote。离线读取把存档 provider factory 替换为抛错函数，仍成功读取 capture、列表、D1 1 条、M1 601 条及精确 Decimal。

原合同“已验证 canonical security”与用户整改指令一起落实为现有只读 US/HK 身份与返回事实校验；不改变旧交易元数据语义或赋予可交易性。原来的无效 unverified 拒绝断言被正常路径回归替换，原币种冲突和 context 失败断言保留。

## 3. 本轮实际独立执行

环境：Linux、Python 3.12，使用项目声明依赖；临时 SQLite 和合成行情，无用户数据库、真实供应商或付费模型调用。

聚焦回归命令：

```text
PYTHONPATH=src:. python -m pytest tests/integration/test_market_archive_f01.py tests/integration/test_market_data_archive_api.py tests/integration/test_market_archive_migration.py tests/unit/test_market_data_archive.py tests/architecture/test_task006b1_boundaries.py tests/integration/test_supported_security_api.py -q -ra
```

| 检查 | 本轮结果 |
|---|---|
| 上述六文件聚焦与关联回归 | **56 passed, 1 warning in 9.85s**；exit 0，无 skip |
| Ruff check . | All checks passed |
| Ruff format --check . | 217 files already formatted |
| mypy --platform win32 src tests | 212 source files，无问题；Linux 上 Windows 目标检查 |
| git diff --check dafb73d... HEAD | 通过 |
| 正常 seed 的实际 Uvicorn capture | HTTP 201，完整 seed 详情不变 |
| 停止服务后同库启动正常应用 | capture JSON 完全相等，列表和 M1 500＋101 分页成功 |
| 正常服务 health／首页／archive JS／CSS／OpenAPI | 五项均 HTTP 200；schema head 为 0004_task006b1_market_archive |
| 正常服务不含测试控制路由 | OpenAPI 无 /_fixture 路径 |
| PostgreSQL DDL／类型／FK | 聚焦回归内执行通过；本轮未运行 PostgreSQL 实库 |
| 审查 checkout | 始终为受审 SHA，无文件修改 |

唯一 warning 为 Starlette BlockingPortal 弃用提醒。本轮未重复完整应用测试集；F01 相关及存档版本、A→B→A、partial/error、事务回滚、不可变约束、分页、旧数据迁移保留等已由上述相关测试执行。

### 实际 Uvicorn 重启验证方法

1. 用项目 archive_server fixture 启动真实 Uvicorn，在新临时数据库执行完整迁移和正常 seed，注入本次已移除状态修改的合成供应商。
2. 通过真实 HTTP 保存 US.AVGO，校验 HTTP 201、供应商调用序列及原始 seed 完整详情不变。
3. 终止该进程，在同一临时数据库启动正常 ai_infra_quant.backend.main:app，MARKET_DATA_PROVIDER=none，不注入测试服务。
4. 通过真实 GET 比较完整 capture JSON、列表和 M1 两页；检查五个资源、schema head、无 fixture 路由，以及完整 seed 详情仍相同。
5. 正常关闭本轮进程和临时目录。探针 exit 0。

这验证了服务重启后的实际离线持久化行为；不是浏览器执行，也没有使用真实行情。

## 4. 浏览器和实现者证据归属

本轮尝试：

```text
PYTHONPATH=src:. python -m pytest tests/browser/test_market_archive_browser.py -x -q --tb=short
```

首个场景在 browser fixture 启动 playwright/driver/node 时抛出 PermissionError: [Errno 13] Permission denied。结果 **1 warning, 1 error in 0.15s**，未进入浏览器业务断言。没有绕过环境权限、改动测试、增加 skip/xfail 或将错误计为通过。

独立打开并视觉检查了本次新增的 archive-390-dark.png、archive-1440-light.png。控件、详情和宽表显示与原局部 UI 一致；截图检查不能替代交互执行。

实现者在整改报告提供的 Windows 结果为：

- 完整应用测试 1401 passed / 1 skipped / 1 warning；
- 浏览器单独运行 118 passed / 1 warning；
- 正常证券状态断言、实际 Uvicorn 重启与离线读取；
- PostgreSQL 实库未配置，按合同跳过。

这些保留为实现者执行证据，与本轮 56 项独立通过不相加，不声称已独立重现其全部 Windows／浏览器结果。修复前五个正向用例失败的 red 记录也归属实现者；本轮正常路径通过与上轮独立 409 复现共同支持 F01 关闭。

## 5. 差异和保护核对

相对 dafb73d...：**7 个既有文件修改，8 个文件新增，其余 359 个既有文件 Git mode/type/blob 完全相同，无删除。**

生产修改仅：

- application/market_data_archive.py：移除错误状态门槛、导入整理和说明注释；
- backend/api/v1/market_data_archive.py：修正 409 文案。

其余修改为三份相关测试、两份当前文档。新增为 F01 测试、整改报告和六张独立目录截图。全部变更均已检查，没有扩大 runtime 范围。

完整 database、core、integrations、resources、seed、Security 约束、market_data_queries、当前 Analyze／Research／凭据／Ledger、生产前端、依赖、原迁移与历史合同／证据均不变。当前 ARCHITECTURE 与 API 文档准确描述只读身份语义，保留待聚焦复核的提交时状态，不伪称独立通过。

## 6. 状态

- **006B1-F01：CLOSED。**
- **新增 Findings：0；Critical 0 / Major 0 / Minor 0。**
- **006B1：独立代码／合同审查通过，尚未合并。**
- 用户真实行情验收、授权整合与后续任务启动分别记录；不由本报告自动执行。
- 本轮仅新增本复核报告；权威分支维持 02326a3bb19c2a89352d765f5331670b5f3f466d。
