# TASK-006B1 — 本地行情存储与回放基础

Status: **APPROVED SCOPE — implement on task branch; independent review required before merge**
Issued: 2026-09-08
Repository: `ahhhhzzz/ai-infra-quant`
Task branch: `task/006b1-local-market-data-store-replay`
Contract path: `prompts/tasks/TASK-006B1_LOCAL_MARKET_DATA_STORE_REPLAY_FOUNDATION.md`

## 1. 授权、基线与开工检查

用户已报告界面验收成功并指示“进行下一步”。007C2 已依据独立代码审查和用户推进授权收尾；用户本地运行版本的证据限制见收尾记录，不得补写为精确 SHA 验收。

| 引用 | 固定值 |
|---|---|
| 权威分支 | `roadmap/no-live-trading` |
| 已整合基线 | `f78894bceb2900eff6e134bdf61f673309426355` |
| 007C2 实现 | `d2d25efc79d2560a7ed09895c7dd7a2c1724aee9` |
| 007C2 独立审查 | `2fc8105a77cf0adf5946aeaac0a148ae20e47fc5` |
| 基线收尾文件 | `docs/decisions/TASK_007C2_CLOSEOUT_AND_006B1_HANDOFF_2026_09_08.md` |
| 历史 006B1 草案 | `fe1e9497e62f1f9b48ba42c2e59e53a0c31989d1` 上的 `docs/roadmap/TASK-006B1_LOCAL_MARKET_DATA_STORE_REPLAY_FOUNDATION.md` |

本合同发布提交是已整合基线的单一直接子提交，仅新增本文件；其完整 SHA 由交接提示提供，不在文件中自嵌。

开始前：
1. 按 AGENTS.md 完整阅读权威文档、当前计划及本合同；检查工作区和 GitHub 精确引用。
2. 校验基线相对 007C2 实现只增加独立审查、收尾两份文档，源码、依赖、测试与资源一致。
3. 使用干净独立 worktree/checkout，从已发布合同 HEAD 开工。保留用户其他分支、未跟踪文件及数据库；不得删除或暂存 `phase1_remediation_commit.txt` 等无关内容。
4. 核对合同父提交和任务分支 merge base；如权威已发生其他更新，先报告差异并确定兼容性，不能悄悄改用旧草案或强推。
5. 列出实际计划修改文件及 schema 设计后实施。常规实现选择无需重复询问。

历史草案只作为需求来源，不整分支合并，不恢复旧 PAQS-Q 推进顺序。旧 006B 结构评估整改不是本任务的隐含前置；本任务也不能将其宣称解决。

本次授权实现、验证并推送自己的任务分支；不授权合并本任务或启动下一阶段。

## 2. 本轮交付目标

用户能对当前自选证券显式保存一份已完成 D1/M1 行情观察，查看已保存记录，并在 OpenD 不可用或断网时读取同一份记录。已合法获取的数据不因供应商滚动窗口变化而丢失；供应商修订复权历史时，旧记录仍可重现。

这是“本地已保存观察的回放基础”。不是历史交易回测、历史 LLM 分析、收益评估，也不是严格历史时点复权。

范围：
- 以现有 provider-neutral DailyBar、MinuteBar、TradingDay 和只读行情端口为输入。
- 显式归档 D1/M1 及日历和必要 provenance；精确 Decimal、UTC、证券身份、来源和质量信息持久化。
- 不可变 capture、行情版本去重和 capture 成员关系；离线按 capture ID 重建。
- 同一应用数据库中的增量迁移、有限 API 和简洁折叠 UI。
- 当前 Analyze、图表实时读取、自选刷新和 Narrative ledger 保持原工作流；不自动改为读缓存。

本轮不承诺减少现有实时刷新请求；只有存档列表、详情和回放读取必须完全本地化。

## 3. 数据模型与时间语义

### 3.1 Capture 与版本

区分三个概念：
- capture：一次显式存档操作的不可变观察记录，包含服务器开始/完成/记录时间、证券、请求范围、来源、各批次状态与覆盖说明；
- bar version：规范化行情内容的不可变版本；
- capture membership：该次观察实际返回了哪些版本及其稳定顺序。

保存 canonical security ID 和不可变的当时 symbol/market/currency 身份信息，避免依赖当前自选股成员关系才能回放。移除自选不能级联删除存档。

D1 主身份包含证券、provider、timeframe、session_date 和复权/来源语义；M1 使用 UTC interval_start/end。OHLCV、已完成标志、原始 provider 时间、质量等影响内容解释的字段必须保存。capture/批次关联保存 retrieved_at，不得为了去重丢弃多次观察时间。

版本 hash 使用明确版本号的 canonical serialization；禁止 float、进程随机 hash、依赖字典偶然顺序。重复且同内容不增加 bar version；新 capture 可以复用版本。财务值使用现有精确 Decimal 方案，超精度应显式拒绝，不能静默四舍五入。

相同 bar 身份但内容变化时新增版本；A→B→A 三次观察必须都按各自 membership 正确读取。不得用一个 mutable latest 行或 first_seen/last_seen 区间替代真实成员关系。并发归档通过数据库唯一约束和事务保持一致，不依赖进程内字典去重。

日历事实同样随 capture 冻结或采用不可变版本引用，保存 market、IANA timezone、day_type、session segments、provider 原始日型与获取时间；不得回放时读取最新日历替换旧证据。

### 3.2 已知时间与复权限制

严格区分 bar 市场时间、provider retrieved_at、服务器归档时间。今天取得的旧 K 线，不能标为历史当天已知。

当前供应商的前复权历史是当前观察到的复权值。沿用现有已核实 adapter/source contract 声明；无法证明的 adjustment basis/epoch 标为 UNKNOWN，不创造不存在的 provider 字段或历史复权因子。

不同抓取请求即使同为 QFQ，也不证明使用同一个 corporate-action epoch。capture 内分别保留 D1、M1、calendar 批次时间/状态，不宣称是供应商原子快照。

回放只按指定 capture 的成员关系读取。不得把旧 capture 的远端尾部与新 capture 的近端数据自动拼成一套“同复权连续历史”。跨 capture 拼接、知识截止选择器、任意历史 AsOf 分析留给后续合同。

W1/M30 继续是既有规则下的派生数据，不建第二套独立权威行情表。本任务不修改其算法、不新增结构引擎或让回放直接进入 Analyze。

## 4. 显式采集与质量处理

复用现有 MarketDataQueries / ReadOnlyMarketDataProvider 的只读能力；不得在 core/application 导入 Futu SDK，也不得保存 SDK DataFrame 或原始对象。

单次显式操作针对一个已验证 canonical security，固定有界窗口：D1 最多 1500 根、M1 最近 30 天，单次最多 50,000 根 M1；返回较少数据时如实披露。日历请求覆盖实际返回行情的必要日期范围，限制最大跨度/记录数并遵守既有 provider 限制。不得扫描所有自选股或后台无限补历史。

每种行情能力单次请求，无自动重试/fallback。日历只有确需供应商分页/按市场分批时才允许有明确上界的调用，报告实际计数。共享现有 request-scoped 生命周期，所有失败路径释放资源。不得访问券商账户、调用付费模型或触发 research。

入库前验证：
- 证券、来源、D1 日期/M1 精确 60 秒区间、UTC aware 时间、有效 Decimal OHLCV、完成状态及既有 domain invariants。
- US 跨 UTC 日期、DST、HK 午休/半日市保留既有时间与交易日语义；不能用本机日期、固定 UTC offset 或美股固定 390 分钟重写数据。
- 同批次重复且完全相同的 bar 可以去重；相同身份不同内容拒绝该批次并明确报错，不任意挑最后一条。
- 未完成、非法值、缺失字段不能补零或猜值。无可靠 calendar 时不得生成“完整交易日”。
- AVAILABLE 不等于覆盖请求区间全部应有 bar；状态与覆盖分别表达，缺口不冒充连续完整历史。

capture 对 D1/M1/calendar 分别记录 AVAILABLE/PARTIAL/UNAVAILABLE/ERROR 等清晰结果；定义汇总状态，PARTIAL 记录允许读取真实已保存部分并显式说明不足。供应商请求失败和入库失败要区分。所有批次失败时报告失败，不生成看似成功的空存档。

最终 capture metadata、有效版本及成员关系在一个短数据库事务中提交；先完成外部读取，不在 provider 等待期间持有写事务。DB 失败回滚，不留下半个成功 capture。不得在持久化日志或 API 错误中泄露凭据、账户资料、SDK 原始异常或私有路径。

## 5. 有限 API 与 UI

新增独立 archive 模块，建议使用以下固定路由形状：

| Method / route | 行为 |
|---|---|
| POST /api/v1/market-data/archive/captures | 显式采集当前 security_id；返回 capture ID、真实状态、各批次数量/范围/质量 |
| GET /api/v1/market-data/archive/securities/{security_id}/captures | 本地列表，稳定排序、有界 limit（默认 20，最大 50）及分页 |
| GET /api/v1/market-data/archive/captures/{capture_id} | 本地详情与冻结日历/provenance，不查询 provider |
| GET /api/v1/market-data/archive/captures/{capture_id}/bars | timeframe=D1 或 M1；稳定顺序、游标分页（默认 500，最大 1000）；完全本地 |

可按现有路由约定调整命名，但不得增加交易/批量扫描/任意远程导入接口。分页游标必须绑定 capture/timeframe，非法游标返回明确 4xx；不得重复漏行或随最新采集结果变化。

保留现有 loopback/same-origin 和写请求防护习惯。非法 UUID、未知证券/capture、参数越界、有冲突的身份、provider unavailable 均需明确定义响应；不能因异常返回 200 和 fabricated 数据。

UI 在当前工作台新增默认折叠的“本地行情存档”小区块：
- “保存当前行情”是唯一采集入口，显式点击、请求中禁用重复操作。
- 显示保存时间、证券、D1/M1 数量、实际覆盖、来源/复权说明与失败/缺口。
- 可选择存档查看本地详情和有界行情表，翻页读取已冻结记录；不需要新回放图表、自动播放或历史 Analyze。
- 证券切换/删除、迟到响应不得把 A 证券结果显示成 B。已保存记录不因退出/重启丢失。
- 断网状态仍可通过列表及 capture ID 查询已存数据，不被实时行情初始化失败阻断。
- 明示“本地存档；当前观察到的复权数据；不等于严格历史时点回测”。
- 不恢复 007C2 删除的资金/NAV/本地开仓事实/混合 provider 管理区。
- 页面加载、折叠展开、列表查询和回放均不触发采集 POST、Analyze POST、模型或 research。
- 深浅主题、390/900/1440 像素宽可读；空态/错误可恢复，键盘可操作。

## 6. 数据库与允许修改范围

本任务明确允许为行情存档增加生产持久化；仅在本合同范围内取代旧文档“行情尚无生产持久化”的状态描述，不授权扩大账本/交易范围。

在现有同一数据库中新增 additive Alembic revision 0004，父 revision 保持当前真实 head 0003。具体 revision identifier 遵循项目既有格式。禁止改写 0001/0002/0003，禁止删除/重建用户库、修改现存业务表语义或 seed 金额。SQLite 保持 canonical fixed-scale TEXT、PostgreSQL 使用既有 NUMERIC(p,s) 设计；必要索引和唯一约束须迁移化。

实现范围限于：
- 新 `core/domain/market_data_archive.py`、`core/ports/` 下存档 repository 协议和新 application 存档服务；
- 现有 `database/` 内新增 archive models/repository、模型注册及 additive 0004 迁移；
- 新 backend archive schemas/routes，必要 router/dependencies/bootstrap 装配；
- 现有市场数据查询模块仅允许提取/复用必要只读身份和 provenance 功能，保持原端点行为；
- frontend index.html、app.css 及独立 archive JS；app.js 仅必要初始化/当前证券接线，不能重构其他流程；
- 因 schema head 变为 0004 必需的启动/launcher head 检查和对应测试常量，逐项报告；不改变启动操作或自动修复策略；
- 新 unit/integration/architecture/browser tests；旧测试仅必要 head/模型数量/UI 接线断言调整；
- 当前 README/README_FIRST、ROADMAP、MASTER_SPEC、ARCHITECTURE、STRATEGY_SPEC、REQUIREMENTS_MATRIX、API_CONTRACTS、DATABASE_SCHEMA、PAQS_E_WORKBENCH 的真实相关状态；
- 新 `docs/reports/TASK_006B1_IMPLEMENTATION_REPORT.md`、`docs/evidence/TASK_006B1/README.md` 和合成数据截图。

目录实际名称按仓库现状对应；不得以上述类别为由通改整个目录。开工先给出具体文件清单。不得新增第三方依赖、分布式服务、外部数据库服务或队列。必要小 helper 可置于上述模块附近并解释依赖。

保护：
- 不改变模型/策略注册表、PAQS-E 主策略/Doctrine/runtime prompts、Narrative/research/credential backend、账户/portfolio/accounting/risk/performance 业务；
- 不改变 PAQS 快照序列化、哈希、冻结证据、已保存 Narrative 精确文本或历史 ledger；
- 不改变联网默认 OFF、显式 Analyze、请求身份/迟到响应保护、无自动重试/fallback 等已验收语义；
- 不改变 Futu 的 US Session.ALL、HK session 规则和复权参数；如发现源契约无法支撑存档，先报告具体事实，不能顺手修 adapter；
- 不提交真实数据库、日志、行情大导出、凭据、用户截图或真实账户资料；
- 本合同、旧合同、报告、审查和决策记录保持历史原文，以新当前状态链接说明。

## 7. 必须证明的验收结果

| 场景 | 通过标准 |
|---|---|
| 首次存档与重启 | 临时 SQLite 真落库，销毁/重建服务后同 capture 内容/顺序/来源不变 |
| 去重与修订 | 两次相同观察复用版本；A→B→A 保留三个正确 membership，无静默覆盖 |
| 滚动窗口变化 | 后续 provider 不再返回旧 bar，旧 capture 仍完整可读 |
| 离线回放 | provider factory 设置为一调用就失败；列表/详情/每页 bars 仍成功且调用数为零 |
| 精度与时间 | 精确 Decimal 往返；US DST/跨日、HK 午休/半日市语义保留；未完成/非法 bar 被真实拒绝 |
| 覆盖与失败 | 缺口、缺日历、D1 成功 M1 失败、全部失败均不冒充完整成功 |
| 事务与并发 | 注入入库失败全回滚；并发同内容 capture 不产生重复版本或串证券成员 |
| 分页/身份 | 超过一页的数据不重不漏，游标不能跨 capture/timeframe，未知/越界请求明确 4xx |
| 原功能回归 | 实时图表、自选、API 弹窗、Analyze、Narrative 历史、Research 默认行为保持 |
| 浏览器流程 | 合成 provider 下显式存档、进度/失败/切股迟到、选择存档/分页、断网读取可用，无 console error |
| 数据升级 | 从带代表性 0003 既有 ledger/watchlist 数据的临时库升至 0004，原数据精确保留且原历史读取正常 |
| 数据边界 | 不保存 W1/M30 作为独立真源，不拼接不兼容复权批次，不触发模型/账户调用 |

版本重建和升级测试必须验证实际数据库内容，不仅 mock repository。浏览器验收使用真实 Chromium，不以字符串匹配代替；截图仅用合成数据。

执行现有完整 pytest、Ruff、format、mypy，记录命令/环境/数量/skip：
```text
python -m pytest -ra
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
```

按项目既有方式验证 Windows；Linux `--platform win32` 结果明确标注，不冒充 Windows 执行。PostgreSQL 有连接配置时运行真实 dialect/migration/roundtrip 门槛，无配置可如实 skip，但 SQLite 运行和双方言类型约束/编译测试不能省略。不得用真实用户库验证升级。

用临时数据库运行实际 Uvicorn，验证健康、首页、静态资源、OpenAPI、0004 schema head 及新增 API 的真实服务路径。无需付费模型验收或账户/OpenD 登录；provider 合成测试应证明归档流程，真实行情人工抽查可另行报告，不能冒充已完成。

遇到环境阻塞如浏览器无法运行，记录阻塞和未执行项；不删除门槛、不伪造 PASS。修复全部本任务引入的失败后再交接。

## 8. 文档、交接与停止

报告必须说明：
- 精确基线、合同与最终实现 SHA，全部变更文件和保护路径检查；
- schema、版本/hash 规则、capture 状态、来源/复权不确定性和已知时间定义；
- API 请求/响应、上界、分页、UI 使用方法及断网读取方式；
- 请求计数：一次显式采集调用哪些行情能力，GET 回放零 provider/模型调用；
- 首次落库、重启、去重/修订、并发/回滚、0003→0004 数据保留证据；
- 完整测试/浏览器/静态/Uvicorn 结果及环境限制；
- 当前 Analyze 仍沿用原快照流程，严格历史 AsOf/GoldSet、PAQS-Q、Paper Broker/收益统计仍未启用。

当前状态文档将 007C2 标为已审查整合；006B1 只能标为“已实现待独立审查”，不能自封验收完成。报告内不可自嵌自身最终提交 SHA，可在交接消息列出准确值。

只推送 `task/006b1-local-market-data-store-replay`，读回 GitHub 核验提交与被测试代码一致，然后提交简洁实现报告并等待独立审查。不得更新权威分支、自动合并或启动后续任务。
