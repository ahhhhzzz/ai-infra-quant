# TASK-006E-Q / TASK-007D — 产品接入与最小 Q/E 对照实现报告

状态：**IMPLEMENTED / WINDOWS LOCAL VALIDATION PASS / AWAITING FOCUSED INDEPENDENT REVIEW / NOT INTEGRATED**。起点为 `roadmap/no-live-trading` 的 `971c64a86998b2140e2549a1dd44e1f716e30e9e`；交付分支 `task/006e-q-007d-product-compare`。本报告只记录本任务分支实现及本轮验证，不宣布独立复核或产品分支整合。

## 可操作结果

在现有 Windows Python 3.12 安装中先运行 `python -m alembic upgrade head`（新 head 为 `0005_task006e_q_analysis`），再按 [README](../../README.md) 的现有 `start_dashboard.bat` 或 Uvicorn 步骤启动。选择证券后，在 **PAQS-Q · 当前快照分析** 点击 **分析当前快照 · Q**。页面显示冻结快照、时间/质量/覆盖、三周期 Context/Event、Setup/Entry 的确认评估与下一开盘资格、条件式 Holder、原因和补证据步骤。Q 历史可重新打开，页面刷新不重新采集或运行 Q。

要做同快照对照，先在原 E 控件显式选择模型、主策略及联网研究，再点击 **用选定模型分析这份 Q 快照 · E**；或输入既有 E Narrative Result UUID 只读对照。E 仍是一次单独的显式模型调用，Q 操作、行情刷新和历史读取不会调用模型。仅完整冻结 Snapshot 身份相同才显示“同一快照”；E 原文不经关键词提取或结构化 Entry/Holder 推断。原 E Analyze 入口、模型选择和研究选项保留。

Q 产品入口从同一次采集冻结 Snapshot 与其来源集合，适配成已完成 W1/D1/M30 `OBSERVATIONAL` QInput，显式选择 Context/Event 1.0.1 并运行 Setup/Risk 1.0.1。记录保存完整 Snapshot、各周期 canonical 输入及 hash、Context/Event/Setup 原始结果和身份、Stage A/Stage B 摘要、Holder 与缺证据说明。Stage B 只配给同一候选的 Stage A；迟到开盘事实保持拒绝，不标记为当时已有独立开盘价。新 Q 适配和 Holder 各有独立版本/代码 hash，不覆盖 F1/B0/A1、Event 或 Setup manifest。Q 表只增不改；旧结果不因刷新或升级重新计算。Holder 只给“若持有这个 Setup”的条件建议；Entry 不合格不是退出指令。只有明确的 D1 冻结边界失效才给条件式退出；W1 Context 失效和不能证明的 M30 连续覆盖返回无法判断。具体状态证据与优先级见 [规则](../PAQS_Q_PRODUCT_COMPARE_V1.md)。

## 真实数据、合成样本和模型来源

本机 Windows 未发现 OpenD `127.0.0.1:11111` 监听；没有执行新的实时真实行情分析或付费模型调用。原 AVGO 实盘行情归档的 **`INSUFFICIENT`** 是[此前 Setup 实现报告](TASK_006D_Q_SETUP_RISK_V1_IMPLEMENTATION_REPORT.md)中的历史执行（缺 W1 CLOSED 日事实），本轮未复跑、未将其改称新版本结果。现有产品快照不保存逐日 CLOSED 日历事实；当前前复权缺历史版本，逐根 `available_at` 和独立下一根 M30 开盘事实也不可用。适配层不以抓取时间、已完成 K 线 open 或“获取成功”补造它们。Windows 合成 provider 的完整产品 API 路径实际保存 `OBSERVATIONAL / INSUFFICIENT`、缺证据代码及补证据动作，且无 `LONG_READY`。要使真实 Q 严格资格可评估，需为同一价位依据补齐历史版本的逐根可知时间、包含闭市日的版本化日历、连续完成的 W1/D1/M30 与真正独立的开盘事件；这不是调低阈值可解决的问题。

正向合成验证使用仓库既有 `demo_bundle()` 的完整三周期 OHLC/日历/开盘证据，调用原 Setup 1.0.1 及新 Holder，得到 `AVAILABLE` 的 Setup 和逐 Setup `TARGET_REACHED_REVIEW`；这是**合成规则路径**，不代表当前产品采集已经具备相同证据。E 模型集成使用测试替身，验证同快照请求不再抓行情、原文逐字保存；真实付费提供方未调用。浏览器测试使用真实 Windows FastAPI/SQLite/Chromium 页面及拦截的行情/模型响应，验证显式操作、历史、同/异快照和 390px 布局；拦截数据不是市场观察。

## 实际验证

环境：Windows 11，Python 3.12.14，pytest 8.4.1，FastAPI 0.116.1，SQLAlchemy 2.0.43，Pydantic 2.11.7，tzdata 2025.2。测试使用临时数据库；没有修改用户现有数据库或工作区。以下是本轮本地 Windows 执行，非独立审查：

| 范围 | 结果 |
|---|---|
| Q 输入/分析、0005 持久化、Q/E API、架构聚焦切片 | `19 passed`；覆盖同候选 Stage A/B、迟到开盘、Holder 硬失效来源、日历/M30 缺口与正常目标证据序列化 |
| Q 页面 Chromium 实际浏览器 | `1 passed`；刷新/历史无 POST，显式 Q/E 调用、同/异快照、原文 inert 展示 |
| 既有 E Narrative ledger/API 兼容 | `26 passed`；首次命令遗漏 `tests/unit` 路径使一个测试的跨目录 import 失败，按项目测试导入路径重跑后全通过 |
| 既有 E Narrative 浏览器回归 | `11 passed` |
| 新增服务端异快照拒绝直比回归 | `1 passed` |
| 代理切片额外聚焦检查 | Q 输入/快照 `22 passed`；迁移切片 `14 passed`；E-from-Q API `3 passed`，均有重叠，不相加为总数 |
| Ruff、格式、JavaScript、类型 | `ruff check src tests`、`ruff format --check src tests`、`node --check paqs-q.js`、9 个受影响源码文件 `mypy --strict` 通过；`git diff --check` 通过 |
| 上游 artifact | Context `510ece60…eedfc`、Event `67fe4a16…68cbc`、Setup `849d50f2…0d2dac1` 的 1.0.1 manifest 现场校验通过；上游覆盖文件无差异 |

仓库级 `mypy src tests` 在此环境先遇到 `paqs_q.support` 的双模块映射；加 `--explicit-package-bases` 后又把本地可编辑包误当无 `py.typed` 的已安装第三方包，产生大量导入噪声。未据此声称全仓库 mypy 通过；改用与本次范围相符的 9 个源码文件严格检查并通过。此限制不涉及运行时测试结论。

## 边界与待复核

本批次没有新交易策略、参数优化、Scanner、账户/订单/真实持仓、回测收益、Q/E 综合评分或自动付费请求。OBSERVATIONAL 不升级成严格 AS_OF；即使将来有观察性 Entry 结果也不会称正式 LONG_READY。Holder 的多 Setup 聚合状态保持无法合并判断，逐项仍可查看。F1、Event 1.0.1、Setup/Risk 1.0.1 已有结论、AVGO 原不足和用户接受的 Linux 限定例外维持原意。下一步为一次聚焦独立审查；本任务分支不合并产品分支。
