# TASK-006B1 F01 聚焦整改报告

状态：**整改完成，等待聚焦复核**。本报告不是独立审查通过结论，不授权整合或后续任务。

## 1. 起点和审查依据

- 仓库：`ahhhhzzz/ai-infra-quant`。
- 唯一推送目标：`task/006b1-local-market-data-store-replay`。
- Fetch 后任务分支/受审实现/本次起始 HEAD：`dafb73daf4aca6de421a3b330e7e81aa5c368e1f`。
- 该实现的父提交：`bed9059fd6ce6c0a7cd750376c972070db0a39dd`。
- 权威 `roadmap/no-live-trading`：`02326a3bb19c2a89352d765f5331670b5f3f466d`，也是任务与权威的 merge base。
- 独立审查提交：`d7bc395168e88fd2edfc68582ecba937d8513491`，父提交正是受审实现；
  [完整审查报告](https://github.com/ahhhhzzz/ai-infra-quant/blob/d7bc395168e88fd2edfc68582ecba937d8513491/docs/reviews/TASK_006B1_INDEPENDENT_REVIEW.md)
  直接按此精确提交读取，没有合并 review 分支。
- 已阅读根 `AGENTS.md`、当前 ROADMAP/MASTER_SPEC/ARCHITECTURE/STRATEGY_SPEC、阶段计划、
  [原合同](../../prompts/tasks/TASK-006B1_LOCAL_MARKET_DATA_STORE_REPLAY_FOUNDATION.md)和
  [post-ADC 交接](../../prompts/tasks/TASK-006B1_POST_ADC_HANDOFF_2026_09_09.md)。
  最新用户指令仅授权修复 006B1-F01。

远程任务分支没有超出受审实现的新提交。在
`D:\AI_Infra_Quant_Codex_v1\task006b1-f01-worktree` 创建干净、隔离、detached worktree；
原任务分支已经在另一 worktree 检出，因此不移动其本地引用、不覆盖其文件。
最终提交从该起点直接产生，正常推送 HEAD 到原任务远程分支；准确最终 SHA 在交接消息列出，
不在报告中自嵌自身提交 SHA。

## 2. 根因与具体修复

`MarketDataArchiveService.capture` 在完成现有 `resolve_research_security` 之后额外要求
`verification_status == VERIFIED`。正常 seed 是 `SYSTEM_SEED_UNVERIFIED`，正常
supported-security 添加是 `USER_SUPPLIED_UNVERIFIED`，因此两条真实路径都会返回 409。
通用 `archive_support.install` 预先批量 UPDATE 为 VERIFIED 掩盖了这个产品缺陷；原实现报告
中的测试通过不能作为正常证券路径已通过的证据。原报告和截图仍作为历史记录保留。

本次只移除额外状态门槛及无用导入，保留既有只读行情身份校验。API 的 409 提示改为行情
Security identity 冲突，避免暗示必须升级证券验证状态。通用 fixture 只注入合成行情供应商，
不再写证券表。旧测试中“unverified 必须拒绝”的错误断言由真实正常路径回归替代；原货币
冲突和 provider context 失败断言保留。

校验责任没有转交给交易元数据：

| 边界 | 仍使用的既有实现 |
|---|---|
| canonical UUID、US/HK symbol/market | Security 领域规范化及存储读取 |
| enabled equity、市场、货币和时区一致性 | `MarketDataQueries.resolve_research_security` / `market_data_security_for_equity` |
| 合法只读供应商身份 | 既有 canonical US/HK 代码和 Futu 映射；存档 provider allowlist |
| 返回证券、provider、完成状态、时间、精确数值 | 原 `_batch`、`freeze_bars`、calendar 校验，未改动 |
| 写入/读取 | 原不可变版本、capture/membership 和本地分页，未改动 |

没有修改 seed、Security 领域、证券 repository、数据库约束或迁移。没有提升
`verification_status`、`tradability_status`、`metadata_status`，也不赋予证券可交易性。
`strategy_and_orders_allowed` 及其原有 VERIFIED 语义保持原样。

## 3. 能在受审实现上失败的正常路径回归

新增 [test_market_archive_f01.py](../../tests/integration/test_market_archive_f01.py) 直接使用
正常 `create_app`、迁移后的临时 SQLite 和正常 seed；不调用旧 install helper、不写证券状态。
所有保存均走真实 POST archive API，读回走真实 GET 和 SQLAlchemy repository。

在尚未修改生产文件的受审实现上执行：

```text
python -m pytest tests/integration/test_market_archive_f01.py -k 'normal_seed or validated_add' -ra
5 failed, 8 deselected, 1 warning in 10.13s
```

这五个失败分别是三个 seed 参数和 US/HK validated-add 参数。共同失败位置为
`save_and_read_offline` 的 `assert response.status_code == 201`：

```text
AssertionError: {"detail":"Archive requires consistent verified Security metadata"}
assert 409 == 201
```

筛选仅用于修复前故障复现；修复后的聚焦和完整运行没有 deselection。

修复后证据：

| 真实产品路径 | 保存前状态（verification / tradability / metadata） | 结果 |
|---|---|---|
| 正常 seed US.AVGO | SYSTEM_SEED_UNVERIFIED / UNVERIFIED / UNAVAILABLE | POST 201、离线 D1/M1/详情/列表读回 |
| 正常 seed US.VRT | SYSTEM_SEED_UNVERIFIED / UNVERIFIED / UNAVAILABLE | 同上 |
| 正常 seed HK.09698 | SYSTEM_SEED_UNVERIFIED / UNVERIFIED / UNAVAILABLE | 同上 |
| POST supported-securities：`us/nvda` → US.NVDA | USER_SUPPLIED_UNVERIFIED / UNVERIFIED / UNAVAILABLE | 添加 201/AVAILABLE，然后存档 201、离线读回 |
| POST supported-securities：`hk/700` → HK.00700 | USER_SUPPLIED_UNVERIFIED / UNVERIFIED / UNAVAILABLE | 添加 201/AVAILABLE，然后存档 201、离线读回 |

每个用例比较操作前后的完整 Security detail，相应状态以及其他字段保持不变；添加前后的原
seed 详情也相同。每次存档只调用一个 context 内的 D1、M1、calendar，context 释放一次。
只有显式 supported-add 使用其既有一次合成 quote 验证；存档/离线读取不新增 quote 调用。
离线读取时 provider factory 被设置为抛错，仍读回 D1 1 条、M1 601 条、准确 Decimal 字符串及证券 ID。

新增负向回归：未知 ID 404、禁用/非 equity 422、货币/时区冲突 409、不支持 provider 422，
均在供应商调用前拒绝且无 capture。返回 bar 证券或 provider 不匹配时无合法 bar，返回 503、
零存档并释放 context。原 bar 完成状态、UTC/窗口、Decimal、重复冲突等负向测试保留。

## 4. 验证环境与结果

真实 Windows 11，CPython 3.12.14（AMD64），pytest 8.4.1、Playwright 1.55.0、
Chromium 140.0.7339.16、Ruff 0.12.9、mypy 1.17.1、Uvicorn 0.35.0、
SQLAlchemy 2.0.43、Alembic 1.16.5、psycopg 3.2.9。复用已安装的声明依赖；不改依赖或配置。

命令从整改 worktree 执行，`python` 实际为
`D:\AI_Infra_Quant_Codex_v1\task007c1-env\Scripts\python.exe`。
设置 `PYTHONUTF8=1`、`PYTHONPATH=<整改worktree>\src;<整改worktree>`，保证使用本次源码，
不依赖该共享虚拟环境以前的 editable checkout。
Chromium 使用 `PLAYWRIGHT_BROWSERS_PATH=D:\AI_Infra_Quant_Codex_v1\playwright-browsers`、
`TASK007C_BROWSER_CHANNEL=chromium`，正常 headless 启动。

| 检查/命令 | 实际结果 |
|---|---|
| 聚焦 pytest：F01 API、原 archive API、迁移、domain、双方言/边界五个文件 | 43 passed, 1 warning in 57.80s；exit 0 |
| `python -m pytest -ra` | 1401 passed, 1 skipped, 1 warning in 776.49s (0:12:56)；exit 0，collected 1402 |
| `python -m pytest tests/browser -ra` | 118 passed, 1 warning in 183.15s (0:03:03)；exit 0，无 skip/xfail/deselection |
| `python -m ruff check .` | All checks passed；exit 0 |
| `python -m ruff format --check .` | 217 files already formatted；exit 0 |
| `python -m mypy src tests` | Success: no issues found in 212 source files；exit 0 |
| `git diff --check` | 无 whitespace error；exit 0 |

聚焦命令完整文件集：

```text
python -m pytest tests/integration/test_market_archive_f01.py tests/integration/test_market_data_archive_api.py tests/integration/test_market_archive_migration.py tests/unit/test_market_data_archive.py tests/architecture/test_task006b1_boundaries.py -ra
```

原去重、A→B→A、partial/error、事务回滚、不可变约束、分页绑定、重建 repository 离线读取、
HK 午间/半日历、0003→0004 非空数据保留均由原用例真实执行。
SQLite TEXT 与 PostgreSQL NUMERIC(38,18)、FK/membership 双方言 DDL 编译检查已执行。
未配置 `PHASE1_POSTGRESQL_TEST_URL`，实库 PostgreSQL 检查不冒充通过。
唯一已知 warning 为 Starlette 对 `anyio.abc.BlockingPortal` 别名的弃用提示。

完整测试唯一 skip：

```text
SKIPPED [1] tests/integration/test_postgresql_migrations.py:67:
PHASE1_POSTGRESQL_TEST_URL is not configured
```

完整运行和单独浏览器运行均未出现 failure/error/xfail/deselection；118 个浏览器测试实际执行
业务断言。源码/测试的 232 文件 SHA256 清单在测试后与提交前核对一致。

### 真实浏览器与实际 Uvicorn

[浏览器用例](../../tests/browser/test_market_archive_browser.py) 使用临时迁移数据库和实际
`uvicorn tests.browser.archive_server:create_archive_test_app --factory --host 127.0.0.1 --port <临时端口>`。
该 factory 调用正常 `create_app` 和正常 seed，仅注入明确标记的合成行情供应商。
通过实际 Security GET 在 configure 前、后及保存/离线读取后断言全部三个 seed 保持原状态，
不预设成功的存档响应，不替换存档 API 或数据库。

六个宽度/主题组合（390/900/1440 × dark/light）执行实际保存、D1 精确文本读取、断开 provider
后 reload/known-ID/M1 500+101 分页、键盘展开和横向表格滚动、页面无横向溢出、零 Analyze POST。
另两个用例验证重复提交/晚到结果和失败恢复。六张新截图均已查看；完整精度宽表在自身容器内
横向滚动，移动端控件可见。新截图目录：
[TASK_006B1_F01](../evidence/TASK_006B1_F01/)，原截图未覆盖。

该服务实际 GET `/health`、`/`、`/static/market-data-archive.js`、`/static/app.css`、
`/openapi.json` 均为 200，head 为 `0004_task006b1_market_archive`，新增 API 出现在 OpenAPI。

另外执行本地辅助脚本 `D:\AI_Infra_Quant_Codex_v1\task006b1-f01-restart-smoke.py`：
先用真实浏览器保存并切换证券验证晚到结果隔离，停止该测试 Uvicorn，随后以同一临时数据库
启动正常 `uvicorn ai_infra_quant.backend.main:app --host 127.0.0.1 --port <临时端口>`。
正常应用未配置行情供应商，也没有 `/_fixture` 路由；原 capture 详情、列表和证券详情保持一致。
浏览器仅模拟 watchlist 初始化 503（没有模拟 archive 成功），依然由真实存档 GET/数据库
完成 known-ID 和 500+101 分页，重启后新增 POST 为 0、page error 为 0。

辅助脚本首轮在清理自己启动的进程时遇到 `taskkill` exit 1，继而临时日志出现
`PermissionError: [WinError 32]`；该轮未记为通过。核对 PID/命令行后以所需权限结束本次测试
进程，并完整重跑成功（exit 0）。所有重跑测试进程已结束。运行源码是起始 SHA 加本次工作树
补丁；辅助检查的 source-revision 标签仍为起始 SHA，不把该标签误称为最终提交运行证据。

## 5. 变更清单和保护核对

修改：

- `src/ai_infra_quant/application/market_data_archive.py`：移除错误状态门槛。
- `src/ai_infra_quant/backend/api/v1/market_data_archive.py`：409 提示与实际身份冲突一致。
- `tests/browser/archive_support.py`：删除批量 VERIFIED UPDATE。
- `tests/browser/test_market_archive_browser.py`：正常状态及前后详情断言。
- `tests/integration/test_market_data_archive_api.py`：替换错误 unverified 拒绝预期，保留冲突和异常验证。
- `docs/ARCHITECTURE.md`、`docs/API_CONTRACTS.md`：仅同步本次存档身份语义和待聚焦复核状态。

新增：

- `tests/integration/test_market_archive_f01.py`：13 个真实 API/数据库回归。
- 本报告。
- `docs/evidence/TASK_006B1_F01/archive-{390,900,1440}-{dark,light}.png`：六张合成行情截图。

相对于起始实现，生产代码仅修改上述两个文件。数据库目录（含所有 models/repositories 和
0001/0002/0003/0004）、core、integrations、resources、seed、Security 约束、行情 query、
当前刷新、Analyze/Snapshot、Research/Synthesis、凭据、Narrative Ledger、Legacy validator、
策略/运行提示和前端生产文件均无 diff。迁移 head 保持 0004，无新增迁移。
原合同、原实现报告、独立审查证据及历史截图未修改；没有新增采集、历史 Analyze、回测、
交易、账户或模型请求。

其他 worktree 的 HEAD 和文件保留，未 reset/clean/stash；未访问或升级用户数据库。
`phase1_remediation_commit.txt` 保留，前后 SHA256 均为
`C791BA73B41C4E7719957607E025105A8110FA54A2E1A67F3C5B142DA8030440`。

环境限制：行情和添加验证为明确标记的合成供应商，没有真实 OpenD 行情抽查，没有付费模型、
账户连接或实盘行为；PostgreSQL 实库未配置，不作实库结论。首次 GitHub fetch 连接重置后重试
成功；没有通过删除断言、增加 skip/xfail、放宽数据约束来规避失败。

只向原任务远程分支正常推送；不 force-push、不修改权威分支、不合并。推送后读回 GitHub
核对最终提交及本报告，交接给独立聚焦复核后停止。
