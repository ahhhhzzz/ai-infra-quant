# TASK-ADC-001 — Architecture / Documentation Consolidation

Status: **APPROVED — DOCS ONLY; before TASK-006B1**
Issued: 2026-09-09
Repository: `ahhhhzzz/ai-infra-quant`
Task branch: `task/adc-001-architecture-documentation-consolidation`

## 1. 目的、授权和精确基线

本任务叫 **Architecture / Documentation Consolidation**，不叫“重构”。
当前代码仍是模块化单体；已确认的问题是当前文档将 007A/B/C 历史形态、C1/R01–R06 增量说明和当前行为混排，且 C2 状态落后于已发生的整合。任务是让文档准确描述当前实现，不设计新的 runtime。

| 引用 | 固定值 |
|---|---|
| 权威分支 | `roadmap/no-live-trading` |
| 用户顺序决策／本任务基线 | `722936984deac652b443eba132c69650653345e1` |
| 决策前已整合基线 | `f78894bceb2900eff6e134bdf61f673309426355` |
| 当前运行代码对应 C2 实现 | `d2d25efc79d2560a7ed09895c7dd7a2c1724aee9` |
| 顺序决策文件 | `docs/decisions/ARCHITECTURE_DOCUMENTATION_CONSOLIDATION_BEFORE_006B1_2026_09_09.md` |
| 暂缓的 006B1 原合同提交 | `d2bc397612a32adb2b5f78fec3ec894b3eacdb38` |

本合同发布提交为 7229369... 的单一直接子提交，仅新增本合同；完整合同 SHA 见交接提示。

用户授权执行本 docs-only 任务并推送任务分支，完成后独立审查；不授权自动合并或同时实现 006B1。先完整阅读 AGENTS.md 要求的文档、本合同和顺序决策；核对 GitHub 引用、父提交、工作区，列出具体文件清单。使用干净独立 worktree，保留用户无关内容，包括 `phase1_remediation_commit.txt`。不 reset/stash/覆盖其他工作。

若 006B1 已有本地未推送实现，保留在原工作区/分支；不能混入 ADC-001。不要合并历史 006B1 草案分支，也不要将当前 006B1 合同误读为本轮代码授权。

## 2. 核心产物

### A. ARCHITECTURE.md 成为当前架构入口

正文按当前系统结构组织，不继续按整改编号追加覆盖说明。至少包含：
1. 当前产品范围和运行形态：FastAPI/Jinja/JS/CSS 模块化单体、只读行情和人工决策辅助。
2. 当前组件职责与依赖方向：API/UI、application orchestration、provider-neutral core ports、provider integrations、数据库 repositories、registry/resources。
3. 当前显式 Analyze 端到端链路及失败分支。
4. 模型选择、凭据边界、optional research、Narrative provider 和证据持久化的独立职责。
5. 当前 UI、Legacy 兼容、数据存储与时间/provenance 边界。
6. 已实现／保留但非默认／计划未实现的明确区分。
7. 历史演进简表和链接。R01–R06 的独立报告、合同、审查继续作为历史证据；正文无需逐轮重复其旧架构描述。

至少一个紧凑 Mermaid 图展示当前请求及 research 分支，不把所有组件挤在同一长行；至少一个职责表给出组件、实际代码路径、输入/输出和依赖边界。图与正文采用相同名称，不创造代码中不存在的服务或队列。

### B. 对齐当前权威文档

以 ARCHITECTURE.md 为架构说明入口，其他文档只保留各自职责需要的信息和链接，避免每份都复制一整段整改日志：
- ROADMAP：真实状态和顺序；007C2 已审查收尾整合 → ADC-001 → 审查整合后重新交接 006B1。
- MASTER_SPEC：当前产品行为和范围，与架构一致。
- STRATEGY_SPEC：策略语义权威及其当前工程消费方式；不修改策略本身。
- REQUIREMENTS_MATRIX：当前能力、实现与验证证据可追溯。
- API_CONTRACTS / DATABASE_SCHEMA：当前真实接口、默认/Legacy 区别、Narrative/Decision 数据及 migration head。
- PAQS_E_MODELS / PAQS_E_WORKBENCH：当前模型、凭据、research 与界面使用口径。
- README / README_FIRST：若有过时概述，只更新相关说明。

不能只在文件顶部加一句“以下历史内容已被覆盖”而保留大量互相矛盾的当前描述。也不能把旧报告改写为当时已经拥有今天的能力。

## 3. 必须按代码核实并写清的事实

以下是核对清单，不是授权修改代码以迎合描述：

### 3.1 Narrative-first 与模型网关

- 普通新 Analyze 请求进入 NarrativeAnalysisService；冻结一份当前 Snapshot，解析注册策略/模型，可选 research，再调用 provider-neutral `PaqsENarrativeProvider.reason_text` / `NarrativeGateway`，最后记录 Narrative evidence。
- Multi-model Gateway 表示从注册模型中选择本次服务/模型，并进行相应协议适配；不表示模型委员会、多模型并行投票、自动 fallback 或无限 provider 扩展。
- `integrations/openai_reasoning/` 当前目录名称不等于只支持 OpenAI。文档准确说明实际职责，不能为修正文档顺手改目录/类名。
- 最终 Narrative 调用 tool-free；最终可见文本不经过旧 structured JSON/schema/语义 validator gate。传输/完成状态/文本完整性等实际检查仍应准确描述，不能简化为“完全不校验”。
- 原文保存、hash 与 lineage 证明所保存的内容及来源，不证明文字中的策略推理、价格目标或 RR 已被机器认证。

### 3.2 Optional research，尤其 DeepSeek

Research 默认 OFF；切模型重置 OFF；刷新、凭据配置、历史读取不触发 Analyze，opt-in 不自动持久化。正常 Analyze 无自动重试/fallback。

区分各 provider 的现有 research 路径，不将 DeepSeek 的状态机套用到全部模型：
- Research OFF：不运行 research，直接以当前请求进入最终 Narrative。
- DeepSeek Research ON：一次 SEARCH；有效 SEARCH 已有最终 factual memo 时直接进入最终 Narrative。
- 只有合法且已完成的 tool-only SEARCH 结果才触发一次 tool-free SYNTHESIS；它是有条件的资料整理步骤，不是失败重试或第二次联网搜索。
- SEARCH 与可选 SYNTHESIS 合计最多两次额外 research HTTP 请求；最终 Narrative 是另一条调用。不要把 HTTP 请求数量与供应商内部 native actions/query 数量混为一谈。
- 使用现有无会话状态传回逻辑，不宣称保存远程 conversation/previous response 状态。
- R06 接受符合规则的部分 action 与 completed evidence 共存；只有已完成且验证通过的证据进入 provenance/pass-back。不要复写已经被取代的“全部 action 必须 completed”或“四个 query 是硬性接收上限”。
- 如果文档列出 parser 数值边界，必须直接核对最新常量、实现和测试；区分 request instruction、acceptance budget 与 provenance capture budget。
- factual memo、来源证据和时间截止保证的真实限制；网页价格不能替代冻结 Snapshot 市场事实。
- 区分 research 前置失败（未进入最终 Narrative，不凭空产生 Run/Result）与最终 provider outcome 的 ledger 记录。具体状态码、诊断 allowlist 和持久化行为按真实代码写。

### 3.3 凭据

Windows 组合使用 provider-neutral CredentialStore 对应的 Windows Credential Manager；按服务槽位共享等行为按实现说明，状态只能确认存在，不能宣称连接/余额/权限验证成功。

明确用户在本地密码输入框提交凭据，与服务端读取接口返回秘密是两回事；不能写“密钥从不经过前端”这类与配置流程矛盾的绝对描述。读取接口不回显密钥，不进入业务 ledger/数据库/日志；保留实际 OpenAI 环境变量回退、不可用平台行为和无 plaintext fallback 语义。不得因文档整理改变凭据优先级、服务槽位或配置接口。

### 3.4 Narrative Ledger 与 Legacy

- 当前 Narrative Run / exact-text Result、冻结 Snapshot/策略/prompt/model/research provenance 等 lineage，以实际数据模型和 repository 为准。
- provider 请求期间不开长数据库写事务；结果存储事务及失败分支按实现描述。
- Legacy structured Run/Decision 历史读取和 validator 保留；旧 POST 的默认 410/OpenAPI 隐藏及内部回归测试开关不能写成面向用户的正常配置。
- migration head 仍为 `0003_task007c1_narrative_ledger`。006B1 的 0004/行情存档只存在于后续计划，当前未实现。
- Narrative 冻结市场证据不等于通用本地行情归档，更不等于严格历史 AsOf 回测能力。
- C2 删除旧管理区及专用前端请求，不等于删掉底层历史数据/账本或移除兼容 API。

### 3.5 明确仍未启用的范围

006B1 存档/回放、严格历史 AsOf/GoldSet、PAQS-Q 后续、Paper Broker/PaperFill/收益统计等按照既有决策列为 deferred/dormant，不因出现接口/骨架就标为当前用户能力。

没有实盘、真实账户连接/观察/导入、真实持仓、下单路由或自主执行。不得借文档重新引入这些范围。

## 4. 证据与允许修改文件

只允许修改：
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/MASTER_SPEC.md`
- `docs/STRATEGY_SPEC.md`
- `docs/REQUIREMENTS_MATRIX.md`
- `docs/API_CONTRACTS.md`
- `docs/DATABASE_SCHEMA.md`
- `docs/PAQS_E_MODELS.md`
- `docs/PAQS_E_WORKBENCH.md`
- `README.md`、`README_FIRST.md`，仅相关当前说明；
- 新增 `docs/reports/TASK_ADC_001_IMPLEMENTATION_REPORT.md`。

不要求每个允许文件都制造 diff；逐项报告已核对/已修改及原因。当前 Phase 1 计划作为背景只读，不因本轮修改历史阶段验收记录。

报告中提供简洁“旧描述 → 当前事实 → 代码/测试证据 → 更新文档”映射。关键事实链接应能定位到基线源码路径及符号；必要时使用精确 commit URL，不能仅引用另一份互相复制的文档。至少核对：
- application/paqs_e_narrative.py、paqs_e_models.py、paqs_e_research.py；
- integrations/openai_reasoning/narrative.py、gateway.py、deepseek_research_flow.py、deepseek_research.py、deepseek_research_diagnostics.py；
- integrations/windows_credentials.py、core/ports/credentials.py；
- backend/api/v1/paqs_e.py、core/domain/paqs_e_narrative.py、database/repositories/paqs_e_narrative.py；
- frontend/static/paqs-e.js、当前 template、model_registry 和实际装配代码；
- 支持这些行为的现有测试、007C1 R06/C2 review 与 closeout。

所有非允许路径保持字节不变，尤其 `src/`、`tests/`、runtime prompt/strategy/model resources、migration、scripts/launcher、依赖和 CI。本合同、历史合同/报告/审查/决策不修改。

发现代码疑点或文档无法确定事实，在报告单列“需后续确认”，给出源证据；不能借机修代码、调整阈值、更新模型、扩大 API、增加测试来实现新行为，不能把猜测写成已实现能力。

## 5. 验收

1. **范围检查**：相对精确基线，除本合同发布文件和第 4 节允许文档之外 diff 为空；全部源码/资源/测试/迁移/依赖/CI 的 Git tree 或逐路径 blob 与基线一致。
2. **当前口径检查**：从 ARCHITECTURE.md 单独阅读即可理解实际正常请求；无需读完 R01–R06 才知道谁覆盖谁。当前说明不再自相矛盾；历史区清晰标记。
3. **状态检查**：007C2 已审查整合且链接正确；ADC-001 实现报告只能写“待独立审查”；006B1 暂缓等待本轮审查整合后的新基线，不能写成已实现/已开工。
4. **追溯检查**：第 3 节每类关键声明都有对应源码/测试依据；没有由新文档反向创造的运行保证。
5. **文档检查**：相对链接存在、标题/锚点有效、Mermaid 语法与图义一致；运行现有文档检查工具（若有）及 `git diff --check`，不为此新增依赖或 CI。
6. **历史完整性**：受保护历史证据 diff 为空，用户验收与独立执行证据不混淆。尤其不能将用户此前显示 C1 分支的 status 改写为已核验精确 C2 运行 SHA。

这是 docs-only 整理，不是新的 runtime/阶段完成认证。无需为无代码变化重复付费调用、完整业务测试或浏览器截图；引用旧执行结果时明确原测试对象和来源，不能冒充本轮执行。若运行现有检查，报告真实结果与环境限制。没有运行某项就如实写未运行，不能填 PASS。

## 6. 交接与停止

只推送本任务分支，读回 GitHub 核验：
- 完整最终 SHA、基线/合同 SHA、全部变更文件；
- 主要口径修正和证据映射；
- 非文档文件完全不变的检查结果；
- 文档检查结果、尚未确认的事实和本轮未执行的 runtime 验证。

等待独立审查，不自行合并、不启动 006B1。下一次 006B1 交接必须采用本任务审查整合后的精确权威基线，并明确原合同继续有效的功能范围；不能直接使用旧开工提示。
