# TASK-007C 独立审查记录

日期：2026-09-07

## 结论

**PASS — TASK-007C 最终独立验收通过。**

最终审查实现固定为 `9e276ca163b1611a4253db5d953716f0acfb4c5f`。原审查记录 `d1518008919171a8ef4be59942a4e0618127839b` 的代码、非浏览器回归、静态检查和真实 Uvicorn HTTP 结论继续有效。新增的独立、干净、detached 浏览器执行在同一精确 SHA 上取得 **46 passed, 1 warning in 35.03s**，退出码 **0**，全部 46 项进入并通过业务断言，关闭原审查唯一未完成的强制验收项。没有新增阻断问题，也不因既有非阻断文档状态不一致要求功能返工。

本次仅在既有 `independent-review/task-007c-9e276ca` 分支更新本审查记录；不修改受审实现，不移动实现或权威分支，不合并 TASK-007C，不启动下一任务。原审查及其环境错误保留为历史证据。

## 精确对象与隔离

| 项目 | SHA / 引用 |
|---|---|
| 仓库 | ahhhhzzz/ai-infra-quant |
| 审查实现 | `9e276ca163b1611a4253db5d953716f0acfb4c5f` |
| 实现父提交／合同 | `70a3b246172e93dff7071308a9fce95bb2c32380` |
| 权威基线／merge base | `0db5dd1eb8d9b8f8a2fe49a4e3de5c2d92ed3638` |
| 任务分支 | `task/007c-paqs-e-user-dashboard` |
| 权威分支 | `roadmap/no-live-trading` |

GitHub 比较核对：实现相对合同 1 个提交、44 个变更文件；相对基线为合同与实现 2 个提交。审查读取固定 SHA，不以浮动分支替代审查对象。

审查在单独的源码快照和 Python 环境运行；242 个文本文件按 Git blob SHA 核对，另读取并核对 3 张原始首屏截图。没有操作实现者原工作目录、未跟踪文件或工作进程。保留既有 007B 独立审查结论，未重新发起 007B 返工。

## 原独立验证结果（历史记录，结论仍有效）

| 验证 | 原审查实际结果 |
|---|---|
| `PYTHONPATH=src python -m pytest --ignore=tests/browser -ra` | **453 passed, 1 skipped**；30.70s |
| 上述测试中的配置接口专项 | 包含全部 **15 项**，通过 |
| `python -m ruff check src tests` | 通过 |
| `python -m ruff format --check src tests` | 161 files already formatted |
| `PYTHONPATH=src python -m mypy src tests` | 158 个文件，无问题 |
| 新建 SQLite 数据库及迁移 | 0001 → 0002 成功 |
| 实际 Uvicorn 与真实 HTTP | health、首页、OpenAPI、configuration、3 个自有静态资源、图表资源、自选列表、行情状态、snapshot、Decision history 均返回 200；默认配置与空历史断言通过 |
| 原环境浏览器专项 `pytest tests/browser -ra` | **46 项均在共享 fixture 初始化阶段报错，未执行业务断言**；历史环境限制，已由下述同 SHA 独立执行关闭 |
| 已提交的 1440 / 900 / 390 首屏 PNG | 人工查看；身份、操作区、图表模式及响应式布局可读；属于实现者的合成 API 场景截图 |

非浏览器测试使用 Python 3.12.13 和项目锁定依赖；跳过项是未配置 `PHASE1_POSTGRESQL_TEST_URL` 的既有 PostgreSQL smoke。HTTP 检查使用禁用 provider、空模型密钥和临时数据库，无模型请求。

原审查环境的浏览器复跑使用 Playwright 1.55.0 / Chromium 140，启动出现：

```text
TargetClosedError: BrowserType.launch
FATAL chrome/browser/process_singleton_posix.cc:292
socket() failed: Operation not permitted (1)
```

受支持的云浏览器访问本地审查服务也返回 `net::ERR_BLOCKED_BY_CLIENT`。这些结果不足以判定应用浏览器行为失败，也不能计为浏览器通过。没有绕过运行环境限制。

实现报告另称完整测试 **499 passed, 1 skipped**、浏览器 **46 passed**，并记录 Python 3.12.14 / Chrome 152。该来源与本次独立运行分开计数，不能相加或冒充同一环境的结果。原审查时该精确实现提交的 GitHub check-runs 查询返回 0；新增证据是独立本地浏览器执行，不声称 GitHub CI 浏览器通过，也不把不同环境结果拼接为一次完整运行。

## 最终浏览器验收与 GitHub 复核（2026-09-07）

最终判定前重新读取 GitHub，确认：

| 项目 | GitHub 核实结果 |
|---|---|
| `task/007c-paqs-e-user-dashboard` | 仍为 `9e276ca163b1611a4253db5d953716f0acfb4c5f` |
| `roadmap/no-live-trading` | 仍为 `0db5dd1eb8d9b8f8a2fe49a4e3de5c2d92ed3638` |
| 原审查分支 `independent-review/task-007c-9e276ca` | 更新前为 `d1518008919171a8ef4be59942a4e0618127839b` |
| 原审查提交相对实现 | ahead 1、behind 0；唯一差异为新增本审查文件，merge base 即受审实现 |
| 实现相对权威基线 | ahead 2、behind 0；merge base 为精确权威基线 |

因此受审代码、浏览器测试、依赖声明及合同均未变化，原代码与非浏览器结论仍适用于同一对象。本次仅补齐原记录明确要求的浏览器执行，未重新运行或冒称重新运行原非浏览器检查。

### 独立执行来源与环境

本次接受的证据来自本会话前一轮实际命令工具执行及其 `execution-evidence.txt` 转录记录，并非实现报告中的 Chrome 152 结果。浏览器执行使用从 GitHub 获取的精确实现提交、干净 detached checkout 和全新隔离 Python 环境；运行前后 `git rev-parse HEAD` 一致，`git status --porcelain` 为空，`git diff --exit-code HEAD` 返回 0。Python 优化标志为 0，断言未禁用。

本地执行转录文件 `execution-evidence.txt` 的 SHA-256 为 `677fa454441bd83f3a7d95f8f50c07c85ee145e17e1dadf679479e36b25ff0d8`。它是命令工具输出的转录证据，不冒充完整原始终端日志；上表环境与下列结果在本记录中直接保留，新增本地截图未冒充仓库中旧的实现者截图。

| 项目 | 实际值 |
|---|---|
| 实现 SHA | `9e276ca163b1611a4253db5d953716f0acfb4c5f` |
| 平台 | Windows / win32 |
| Python | 3.12.14 |
| pytest | 8.4.1 |
| Playwright | 1.55.0（仓库 dev extra 固定版本） |
| Chromium | 140.0.7339.16，Playwright build v1187；正常启动 |
| 命令 | `pytest tests/browser -ra` |
| 收集与执行 | 46 项；全部执行业务断言并通过 |
| 结果 | **46 passed, 1 warning in 35.03s** |
| 退出码 | **0** |
| skip / xfail / deselection / failure / error | 均为 0 |

唯一警告来自 Starlette `testclient.py:51`：

```text
DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
======================= 46 passed, 1 warning in 35.03s ========================
```

环境按 README 使用 `pip install -e ".[dev]"`，并安装 Playwright 自带 Chromium。使用 fixture 已支持的 `TASK007C_BROWSER_CHANNEL=chromium`；进程级 `PYTHONPATH` 指向精确 checkout 根目录，`TEMP`/`TMP` 指向新建可写临时目录；浏览器二进制和截图输出位于 checkout 外。这些是环境准备，不是代码、测试、文档或仓库配置修改。未跳过、重写、xfail、弱化或替换任何浏览器测试，浏览器运行者没有提交或推送。

前置尝试如实保留：第一次因共享临时目录访问被拒（`PermissionError: [WinError 5]`）得到 46 个 setup error；第二次因非 editable 安装的资源定位及 checkout 根目录导入路径问题得到 46 failed（configuration HTTP 503，以及其余场景 `ModuleNotFoundError: No module named 'tests'`）。完成上述环境准备后，以完全相同命令执行全部 46 项并通过。前置错误没有被计为成功，也没有通过改动被测代码或断言解决。Chromium 在独立 Windows 执行中已成功启动。

### 浏览器证据覆盖与视觉复核

既有 suite 使用正常 Uvicorn 入口、临时迁移数据库和真实页面/自有 JavaScript；行为场景使用明确标注的合成 API fixtures，无真实 Futu 或付费模型请求。通过的场景覆盖显式 Analyze 与零隐式 POST、并发和历史选择、失败/未知结果及禁止自动重试、冻结 Run 证据、Decimal/时区、文本注入安全、自选列表与行情回归，以及六个视觉场景。

本次额外查看独立执行生成的以下六张首屏图，均有实质 UI 内容；宽屏三列、窄屏重排、Security/修订身份、Analyze 与成功/未知状态可读，未发现新增阻断性裁切、重叠或隐藏错误。它们均为真实应用页面配合合成 API 的验收图，不是实时市场或策略收益证据：

| 视口 | 场景 / 主题 | 本次本地截图文件名 |
|---|---|---|
| 1440×900 | 未配置 / dark | `1440x900-unconfigured-dark-viewport.png` |
| 1440×900 | 成功 / dark | `1440x900-success-dark-viewport.png` |
| 1440×900 | 历史修订 / light | `1440x900-historical-light-viewport.png` |
| 900×900 | 成功 / light | `900x900-success-light-viewport.png` |
| 900×900 | 结果未知 / dark | `900x900-unknown-dark-viewport.png` |
| 390×844 | 成功 / light | `390x844-success-light-viewport.png` |

原审查已完成代码、非浏览器、真实 HTTP 和已提交截图检查；新增同 SHA 的 46/46 结果及截图复核关闭唯一强制缺口。弃用警告、环境准备和既有文档状态差异均未提供新的功能阻断依据。最终结论为 **PASS**，含义是该精确 TASK-007C 实现通过独立验收，不代表已经整合。

## 代码与边界审查

1. **显式 Analyze 与并发。** POST 位于明确表单提交入口；同步的页面级 in-flight 守卫、提交前捕获的 Security/model/strategy 和结果身份检查共同限制误触发与跨标的覆盖。行情刷新、选项变更和历史查询不触发 Analyze。历史与详情读取有代次控制；迟到结果不覆盖用户已经明确选择的历史记录。
2. **成功、失败和未知结果。** 201 成功验证返回身份；HTTP 状态与分析状态分开处理。超时、非 JSON、身份冲突等保留未知结果且不自动重试；先前成功 Decision 保持历史语义。已知 Run 查询没有扩展成失败 Run 搜索接口。
3. **冻结证据。** W1/D1/M30 取自持久化 Run request；Decision、Run、request 与 snapshot 身份、hash 和时间字段需一致。证据缺失或冲突清除图形证据，保留独立读取的 Decision 文本。当前行情刷新不会改写冻结证据。
4. **显示与文本安全。** 金额与比率文本保留十进制字符串；仅绘图转换为有限数值。文本价位不推断为数字线。服务器与模型文本通过文本节点呈现；未发现动态 HTML 执行路径。只在本地持久化主题偏好。
5. **配置接口。** 唯一新增后端接口是只读 GET configuration；复用既有策略加载器并在启动时建立有界投影。仅返回 provider、密钥是否存在的布尔值、默认策略与已注册策略元数据；不返回密钥、提示词、文件路径或传输配置，不探测供应商，不写数据库。
6. **保护边界。** 既有策略语义、分析 runtime、账本、迁移、注册表、提示词与 vendored 图表字节未变；没有加入交易、后台分析、新闻、prompt editor、额外 provider 或市场数据持久化。
7. **测试调整。** 旧 UI 禁令替换为显式提交约束与浏览器场景；旧市场读取不调度分析的后端约束保留。API allowlist 只增加 configuration GET；敏感字段例外限定为密钥存在布尔值。未发现以删除核心断言掩盖行为回归的修改。
8. **R20 引用。** 检查变更与引用记录，采用其布局和交互参考，没有引入 R20 runtime 或新的外部前端依赖；既有 Lightweight Charts 保留。此项不构成对上游 R20 产品整体安全性的认证。

## 非阻断文档问题

- `docs/MASTER_SPEC.md` 与 `docs/STRATEGY_SPEC.md` 仍存在“007C not yet implemented”的旧状态，而本分支已有实现报告。后续整合时统一为与实际审查、合并状态一致的表述。
- `docs/REQUIREMENTS_MATRIX.md` 使用 `IMPLEMENTED_PENDING_REVIEW`，状态图例定义的是 `PENDING_REVIEW`。建议统一词汇或补充定义。

上述为文档一致性问题，不作为功能代码返工依据。本次未改写受审提交。

## 后续边界

原记录要求的同 SHA、未删改 46 项浏览器专项已在可正常启动 Chromium 的隔离环境完成，强制浏览器验收缺口已关闭。保留合成场景标识、原环境失败历史及原非阻断文档意见；本次不发出功能返工任务。

未验证真实 Futu、付费 OpenAI、PostgreSQL 或真实 Windows 启动；Windows 相关现有回归已包含在非浏览器测试中。本审查不评估策略收益或真实交易适用性。007C 仍未整合，本记录不会自动授权后续任务。

## 固定来源

- [原独立审查记录（固定历史提交）](https://github.com/ahhhhzzz/ai-infra-quant/blob/d1518008919171a8ef4be59942a4e0618127839b/docs/reviews/TASK_007C_INDEPENDENT_REVIEW.md)
- [原审查提交相对实现的唯一文档差异](https://github.com/ahhhhzzz/ai-infra-quant/compare/9e276ca163b1611a4253db5d953716f0acfb4c5f...d1518008919171a8ef4be59942a4e0618127839b)

- [实现报告](https://github.com/ahhhhzzz/ai-infra-quant/blob/9e276ca163b1611a4253db5d953716f0acfb4c5f/docs/reports/TASK_007C_IMPLEMENTATION_REPORT.md)
- [批准合同](https://github.com/ahhhhzzz/ai-infra-quant/blob/70a3b246172e93dff7071308a9fce95bb2c32380/prompts/tasks/TASK-007C_PAQS_E_USER_DASHBOARD.md)
- [实现变更](https://github.com/ahhhhzzz/ai-infra-quant/compare/70a3b246172e93dff7071308a9fce95bb2c32380...9e276ca163b1611a4253db5d953716f0acfb4c5f)
