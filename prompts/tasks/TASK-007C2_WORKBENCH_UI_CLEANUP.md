# TASK-007C2 — API Key 配置弹窗与遗留管理区清理

Status: **APPROVED SCOPE — staged implementation after the exact 007C1 integration prerequisite**
Issued: 2026-09-08
Repository: `ahhhhzzz/ai-infra-quant`
Task branch: `task/007c2-workbench-ui-cleanup`
Contract path: `prompts/tasks/TASK-007C2_WORKBENCH_UI_CLEANUP.md`

用户已确认上一轮提出的三个范围：API 弹窗修复、旧管理区清理、当前状态文档同步。
本合同将已同意的范围具体化。配套启动提示明确授权一次限定的 007C1 基线整合，再在独立分支实现本任务。
本合同不授权下一任务，也不因 007C1 的历史陈述缺少逐项本地证据而重开已经由用户接受的功能验收。

## 1. 精确引用与整合前置

| 引用 | 固定值 |
|---|---|
| 整合前权威分支 | `roadmap/no-live-trading` |
| 整合前权威 SHA | `0c1713d4409c69a45f8ce5e37951bba72d73d819` |
| 007C1 实现分支 | `task/007c1-paqs-e-multi-model-web-research` |
| 007C1 精确受审实现 | `3e98d8c5f9948dcaefe59eb3b7b847bd99ba8908` |
| R06 审查分支 | `review/007c1-remediation-06-independent` |
| R06 审查提交 | `2240024cb361d79f57fc2eb0d65c2e5aa8697e33` |
| 已准备整合分支 | `integration/007c1-user-accepted` |
| 整合候选／007C2 实现基线 | `2cc4eeea3cc31d4fd1f1a4e9c1fbec237f82a2c4` |
| 整合候选树 | `52554f97d401c81d1f110f76dd6623d464b26820` |
| 整合候选父提交（按顺序） | `0c1713d4409c69a45f8ce5e37951bba72d73d819`、`2240024cb361d79f57fc2eb0d65c2e5aa8697e33` |
| 整合草稿 PR | https://github.com/ahhhhzzz/ai-infra-quant/pull/1 |

合同提交是整合候选的单一直接子提交，仅新增本合同；完整合同 SHA 由发布交接给出，不能在文件内自嵌自身提交哈希。

开始时直接从 GitHub 校验：
1. 用户工作区状态、远程引用、合同 SHA/父提交及文件差异。使用干净独立 worktree/checkout；不得清理、stash 或覆盖其他工作。
2. 007C1 实现与 R06 审查仍对应上表。审查相对实现只多审查文档；收尾提交相对原权威 80f089bc2d285cca492c41aaeaf047e177bc2812 只多用户收尾文档。
3. 整合候选包含实现、审查与收尾的完整祖先关系；相对受审实现只增加以下两个文件：
   - `docs/reviews/TASK_007C1_REMEDIATION_06_INDEPENDENT_REVIEW.md`
   - `docs/decisions/TASK_007C1_CLOSEOUT_2026_09_08.md`
4. 所有应用源码、资源、测试、依赖、迁移与受审实现字节一致。候选树与正常无冲突 Git 合并的树一致。

在配套启动提示授权下，只允许这一次限定前置整合：
- 权威 HEAD 若仍为 0c1713d...，以普通快进更新到精确候选 2cc4eee...；不强推、不 squash、不 rebase。
- 权威 HEAD 若已为 2cc4eee...，验证后跳过重复整合。
- 其他 HEAD、候选变动或树不一致：停止发布并报告实际差异，不猜测新基线。
- 整合前再次读取权威 HEAD；整合后读回核验。使用已准备的候选，不生成其他代码合并方案。
- 然后从已有的 `task/007c2-workbench-ui-cleanup` 合同 HEAD 实现；其 merge base 必须为 2cc4eee...。
- 007C2 实现只能推送自己的任务分支；本任务不能把自己的改动再次合入权威分支。

007C1 用户使用验收、代码审查与技术执行证据的归属以原收尾记录为准。不能将用户确认改写为本次助手完成过付费验收或独立复算本地运行哈希。

## 2. 问题与预期结果

### A. API Key 弹窗

已核实根因：`#credential-form` 没有定义自己的列布局；全局 `form` 及其媒体规则定义六列／三列网格，弹窗标题、说明、输入与按钮挤在不同窄列。

要求：
- 设置凭据弹窗独立单列内容布局和专用按钮区；全局规则不能改变其预期列数。
- 标题、模型／服务说明、存储说明、密码输入和状态上下排列；主保存按钮清晰，删除与关闭可辨认。
- 窗口在视口内合理居中，宽度有上限，窄屏不越界；高度超出时内部可滚动，关闭与操作区可达。
- 密钥输入框占满内容宽度，长模型名、中文说明、错误文案正常换行；不靠固定超宽或隐藏溢出来掩盖错排。
- 深浅主题均可读；键盘可操作，打开后焦点在合理位置，Escape／关闭后焦点回到配置按钮，秘密字段按既有逻辑清空。
- 保留保存／更新／删除的既有后端行为、Windows Credential Manager、仅存在布尔投影、同源／loopback 检查、共享服务槽位、OpenAI 环境密钥回退语义。
- UI 修复不得添加模型探测或付费调用，不把“凭据存在”改成“连接验证成功”。

### B. 历史管理区

正常工作台移除：
- `Portfolio facts and local administration · Phase 1 历史本地开仓事实` 容器／入口；
- Portfolio equity、Cash、NAV、Units、Invested、Since inception 等初始账本卡片；
- 该区域的重复旧 Watchlist administration 表与混合 broker/provider 描述符列表。

保留并验证：
- 当前左侧／窄屏主自选股添加、选择、删除、状态与行情加载能力；
- 当前行情状态、延迟、来源和数据质量披露；
- 当前 Narrative 历史、Legacy 结构化 Decision 历史、已知 Run 查询、冻结证据图；
- 当前分析区域与注册模型／策略选择。

同步处理 JavaScript：
- 退役仅服务于旧管理区的 DOM 更新、初始化调用与事件处理；
- 页面正常加载及刷新不再为被移除管理区读取 `/portfolio`、`/performance`、`/brokers`、`/fundamental-data/providers`、`/event-data/providers`；
- `/market-data/providers` 如仍被有效行情状态需要可保留，须有真实当前消费者；不能只为旧混合列表保留；
- 分清旧管理区与主自选共享的 helper／接口，保留主自选所需请求；
- 不出现空 DOM 访问、重复事件注册、未处理 promise rejection 或隐藏失败阻断行情初始化；
- 不新增诊断中心或后台管理页面来迁移已无当前用户价值的旧列表。

这里的 HKD 20,000 / 200 units / NAV 100 是 Phase 1 本地初始化值，不是券商持仓。用户“不搞实盘”不授权删除数据库。
保留所有现存数据库、seed 行为、旧后端兼容 API、迁移与数据；不删表、不清库、不将旧账本转换为交易记录，不改初始化资金。
后端结构退役如将来必要，另立迁移任务。

### C. 状态文档同步

至少核对 ROADMAP、MASTER_SPEC、STRATEGY_SPEC、ARCHITECTURE、REQUIREMENTS_MATRIX 的当前状态，并按本任务真实结果更新：
- 007A／007B／007C 已验收整合；
- 007C1 用户功能验收通过，以及实际执行完的整合 SHA；
- 007C2 已实现待独立审查，不提前宣称 PASS 或整合；
- 普通新 Analyze 是 Narrative-first，完整文字保存不等于机器对全部策略语义／RR 的认证；旧结构化记录仍可读；
- 只读行情与决策终端目标，正常 UI 不再展示初始资产账本；
- 模拟盘、PaperFill、收益统计、006B1、PAQS-Q、007D、Phase 3／4 均不因本任务自动启用。

原合同、实施报告、审查、用户收尾记录是历史证据，保持原文。使用新的当前状态描述和链接解释历史，不把历史“未合并”直接改写成当时“已合并”。

## 3. 允许修改的文件

生产界面：
- `src/ai_infra_quant/frontend/templates/index.html`
- `src/ai_infra_quant/frontend/static/app.css`
- `src/ai_infra_quant/frontend/static/app.js`
- `src/ai_infra_quant/frontend/static/paqs-e.js`：仅限弹窗焦点／布局所需 DOM 或已移除旧区的直接兼容调整；其余分析生命周期保持。

当前文档：
- `README.md`、`README_FIRST.md`（需要时）
- `docs/ROADMAP.md`
- `docs/MASTER_SPEC.md`
- `docs/STRATEGY_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/REQUIREMENTS_MATRIX.md`
- `docs/PAQS_E_WORKBENCH.md`
- `docs/PAQS_E_MODELS.md`
- 新增 `docs/reports/TASK_007C2_IMPLEMENTATION_REPORT.md`

验证：
- 新增 `tests/browser/test_paqs_e_ui_cleanup.py`；
- 必要的旧 DOM 断言调整限于 `tests/browser/`、`tests/integration/test_market_dashboard.py`、`tests/integration/test_offline_startup.py`、`tests/architecture/test_frontend_security.py`，逐项列明旧断言为何过时、替代断言验证什么。
- 新证据可置于 `docs/evidence/TASK_007C2/`，只提交合成数据截图及简短场景说明；不能提交真实密钥、用户原图中的私有数据、日志或数据库。
- 合同文件在实现过程中保持不变。

若需要越出上述范围，先说明具体不可替代的依赖，不擅自扩展后端／数据库任务。无需为常规布局选择反复确认。

## 4. 保护范围

以下保持 Git 字节不变：
- 全部后端 API、application、core、database 与 integrations；
- model/strategy registry、PAQS-E 主策略／Doctrine 与 runtime prompts；
- NarrativeGateway、research parser/flow、凭据后端、运行时 source revision 与 Windows launcher；
- 迁移 0001/0002/0003、seed、依赖声明、vendored chart、Markdown renderer；
- 已接受审查／收尾文件和以往任务合同。

不得改变：联网默认 OFF、切模型回到 OFF、只有显式 Analyze 才发 POST、单请求守卫、长请求不在 180 秒自动中断、无自动重试／fallback、历史选择与迟到响应身份保护、冻结证据和精确文本／哈希语义。
不得引入实盘、账户连接／观察／导入、真实持仓、下单、PaperFill、PnL、扫描器、模型委员会、框架迁移或额外外部依赖。

## 5. 验收与证据

必须有真实浏览器中的弹窗验收，不能仅用 DOM 字符串匹配宣称排版已修复：
1. 在 1440×900、900×900、390×844，深／浅主题下打开弹窗，使用长说明／错误文案；验证弹窗和输入宽度、元素垂直顺序、不重叠、不越界、按钮可达。
2. 至少一个桌面场景验证 200% 页面缩放或等效放大文本场景，明确记录采用的方式；保持窄屏可滚动。
3. 保存／更新、删除、失败、关闭、Escape、焦点恢复，以及密码清空；使用测试用内存凭据／合成拦截，不使用真实服务密钥。
4. 断言旧金融卡片／旧管理区消失，正常加载不请求其专用接口；主自选添加／删除／切换、行情刷新、Narrative/Legacy 历史与冻结图保持工作。
5. 打开／关闭弹窗、配置凭据、自选操作、刷新与历史读取都不会产生分析 POST 或供应商调用。
6. 检查实际页面错误／console error，无新增 JavaScript 初始化错误。
7. 截图必须展示打开状态的弹窗和清理后的完整工作台，不以旧首屏截图替代。

执行现有完整测试与静态检查，报告环境、数量、skip 和失败原因：
```text
python -m pytest -ra
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
```

正式 Windows 运行环境的 mypy 结果单独记录；如只在 Linux 检查 `--platform win32`，必须注明不等同于真实 Windows 执行。
PowerShell/PostgreSQL 的既有环境 skip 不冒充通过。浏览器准备失败不允许删除／跳过该业务门槛。
运行实际 Uvicorn，验证健康、首页、配置及自有静态资源可用；用临时 SQLite 进行启动，不能使用或修改用户生产数据库。
验证迁移 head 仍为 0003；检查受保护路径 diff 为空。
不重新进行付费 Research-ON/OFF 验收；本任务不修改已接受的 provider 或 research 行为。

## 6. 完成交接与停止

实施报告须包含：
- 精确整合前／后权威 SHA、合同／实现 SHA、merge base 和远程引用核验；
- 全部变更文件、旧测试替换说明；
- 关键 UI 验收截图与浏览器执行结果；
- 被移除的后台请求和被保留的主自选／行情／历史行为；
- 受保护路径字节不变、无数据库／迁移变更、无付费调用；
- 完整测试、静态检查、Uvicorn 验证与环境限制。

只推送 `task/007c2-workbench-ui-cleanup`，核对 GitHub SHA 与测试对象一致，然后等待独立审查。
不自行合并 007C2，不启动后续任务。本合同的前置整合例外只覆盖上表精确 007C1 候选。
