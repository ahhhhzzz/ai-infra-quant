# AI INFRA QUANT · 决策工作台

本次仅调整展示层；基线 `1d10a47ec4f0635520d0a004a5f940d35df1d627`。
未修改 Context、Event、Setup/Risk、Holder、manifest、参数、数据库或历史结果。

## 使用

固定目录：`D:\AI_Infra_Quant_Codex_v1\ai_infra_quant_codex_v1`。
本机双击既有 `启动AIInfraQuant.cmd`；运行中页面为 `http://127.0.0.1:8000/`。
启动器使用原 `.venv` 与 `data/ai_infra_quant.db`，会等待 OpenD；需完成 OpenD 登录。
本次无新增迁移。页面已打开时刷新即可加载新界面。

- 左侧搜索自选并展开添加入口；中间保留当前行情及既有 E 冻结图表。
- 右侧默认 Q，显式分析才生成新记录；「历史记录」只读取已保存结果。
- 摘要显示中文状态、时点、快照报价、直接原因及关键限制；各候选价格独立展示。
- 「分析详情」分为市场背景、价格事件、候选形态、入场资格、若已持有。
  Stage A 指示性评估与下一常规 M30 开盘 Stage B 分开，缺失值不补零、不推算。
  结束形态不沿用历史资格；NO_TRADE 几何不作为有效目标。Holder 展示原绑定及触价证据。
- 技术身份、枚举及 JSON 默认折叠，可展开复制。未知原因保留原码；输入限制不自动当作直接失败原因。
- 「Q/E 对照」从所选 Q 出发，在最近 20 条 E 成功历史中筛选快照摘要匹配项，读取时由既有接口再核对完整身份；更早记录保留高级 ID 入口。
  读取不调用模型；显式运行 E 前显示模型、策略、联网选项和费用提示。保留 E 原文，不生成统一交易结论。
- 查看 Q 不切换图表数据。当前报价、最近完成日线收盘、分析快照报价分开；接口未提供涨跌幅，不从其他价格推算。

## 本轮验证（2026-09-24）

Windows 11、Python 3.12.14、现有 Chrome 153；复用原环境。实际执行：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/browser/test_dashboard_readability.py tests/browser/test_paqs_q_workbench.py -q
.\.venv\Scripts\python.exe -m pytest tests/integration/test_market_dashboard.py tests/integration/test_paqs_q_product_api.py tests/integration/test_paqs_q_e_frozen_api.py -q
.\.venv\Scripts\python.exe -m ruff check tests/browser/test_dashboard_readability.py tests/browser/test_paqs_q_workbench.py tests/integration/test_market_dashboard.py
$env:MYPYPATH = 'src'
.\.venv\Scripts\python.exe -m mypy tests/browser/test_dashboard_readability.py tests/browser/test_paqs_q_workbench.py tests/integration/test_market_dashboard.py
```

浏览器 **9 passed**；接口/行情兼容 **19 passed**；Ruff、Mypy 通过。
浏览器使用实际 Uvicorn、临时数据库和明确标注的拦截样本，未向真实服务提交分析。
检查 1920×1080、1366×768 的正常/证据不足首屏，以及 390×844 窄屏、深浅主题截图。
覆盖无历史、请求失败、迟到响应不串证券、候选价格隔离、缺失开盘证据、JSON 复制、
同快照列表、异快照拒绝、E 原文安全保留及既有图表切换。
截图及本机冒烟记录保存在忽略目录 `data/dashboard-ui-review/`，没有改写历史证据。

本机 `8000` 服务健康、迁移 `0005_task006e_q_analysis`；既有 AVGO Q 历史可读取，
实际仍为 INSUFFICIENT / OBSERVATIONAL。冒烟读取没有 POST、没有脚本错误，历史记录数未增加
（Q 1 条；E 成功结果 3 条、Run 4 条）。OpenD `11111` 未监听，实时行情刷新等待 45 秒仍未完成，实时服务连通不计通过。
没有调用付费模型、运行真实数据新分析、历史策略研究或无关全量回归。
合成 LONG_READY 只用于展示测试，不代表真实资格或成交；AVGO 原结论及 F1 限定例外不变。

修改保留在当前仓库任务分支 `task/dashboard-q-readable-workbench`，未合并产品分支。


## 真实使用排障增量（2026-09-24，保留上文执行记录）

- 运行目录仍为本仓库，`.venv` Python 3.12.14，原 `data/ai_infra_quant.db`，迁移 0005。
  已核对 8000 的父进程位于本仓库 `.venv`、实际静态文件一致、既有 VRT 记录可读取。
- VRT 旧 Q 记录 `51ef57b5-8b27-4bf0-a81f-56ad5f08bc26` 的 W1 需要
  2023-09-25 至 2026-09-20 全日期；缺 343 日（312 周末、31 工作日闭市日期）。
  原 D1/M30 Context/Event 已 AVAILABLE，只有 W1 日历阻断后续 Setup。
- 修复采集范围证据：只有声明完整计划日历范围的成功响应才可取其日期补集作为 CLOSED；
  不由缺 K 线推断，不把 UNKNOWN 交易日转换为 CLOSED，不补历史 available_at。
  W1 完成时点继续采用最后一个 OPEN 常规时段收盘，日历保留市场时区、原检索时间、
  查询范围、原列举交易日期和来源语义。旧捕获缺范围时仍按原证据拒绝。
  [OpenD 日历协议](https://openapi.futunn.com/futu-api-doc/quote/request-trading-days.html)
  不包含临时休市；已增加可见限制。产品适配身份 1.0.1，上游引擎与 manifest 不改。
- Windows 真实 OpenD 只读内存验证：2026-09-24 08:21:30 UTC 新 VRT 快照，
  W1/D1/M30 Context 和 Event 全部 AVAILABLE；Setup AVAILABLE，6 条事实。
  没有正式 LONG_READY；历史行情版本、复权时点、日历历史可知时间及独立开盘证据仍不足。
  结果只存本机忽略目录 `data/runtime-analysis-fix/`，未回填旧历史、未运行收益研究。
- E 根因：当前 DeepSeek Responses 接口忽略内置 web_search，旧配置仍宣称支持；旧 Flash
  模型名亦已转向 V4.1。现采用官方 `deepseek-flash` 新入口，Flash/Pro 联网能力明确禁用。
  不联网分析需用户点击，仍可能收费；凭据槽不变。原始错误码和受限诊断保留在折叠详情。
  截图 SEARCH_ENVELOPE 只留有计数，未留存原响应；不能事后确定是哪一个顶层字段被拒绝。
  本机另有 07:59:30 UTC 不联网 INVALID_FINAL_TEXT 失败记录，同样未留原响应；不冒称已
  从历史记录证明其具体字段，也不放宽模型身份/文本完整性检查。
- 本轮没有付费模型调用。新模型最终文本链路仅通过合成 transport/API 验证；实际连通性
  须用户在 E 选择 DeepSeek Flash (V4.1)，保持联网关闭，显式点击一次分析来确认。
  Q 则选择 VRT →「分析 Q 当前快照」。刷新/历史读取不会重算；旧 INSUFFICIENT 保持原结论。
- 历史原文与数据库未修改；重启及只读页面检查前后三个 Q/E 分析表的完整内容摘要一致。
  OpenD 曾停止监听，已启动现有本机程序并成功取得数据；未接入任何交易接口。


本次实际验证（Windows Python 3.12.14）：日历新回归、原报价/Q 输入适配、Q 产品 API、
E 当前模型能力/文本传输/配置/历史 API 及必要架构检查通过；Chrome 聚焦 **5 passed**。
历史原生搜索协议使用明确隔离的旧能力合成目录继续检查，生产目录不启用它；
最后该兼容切片加跨模型历史链 **24 passed**。保留拒绝、失败不存成功结果和无自动回退断言。
Ruff、5 个变更 Python 源文件 Mypy、diff 检查通过；三份上游 manifest 校验通过，51 个覆盖文件未变。
未运行研究/浏览器全矩阵；真实 E 调用仍未执行。先前测试中暴露的目录权限、已退休模型的
测试目录假设、旧迁移号及测试导入问题已调整并针对失败项复验，不是策略阈值整改。

VRT 所缺的 31 个工作日日期（其余为上述区间全部周末；完整清单在本机 summary.json）：

2023-11-23, 2023-12-25, 2024-01-01, 2024-01-15, 2024-02-19, 2024-03-29, 2024-05-27, 2024-06-19, 2024-07-04, 2024-09-02, 2024-11-28, 2024-12-25, 2025-01-01, 2025-01-09, 2025-01-20, 2025-02-17, 2025-04-18, 2025-05-26, 2025-06-19, 2025-07-04, 2025-09-01, 2025-11-27, 2025-12-25, 2026-01-01, 2026-01-19, 2026-02-16, 2026-04-03, 2026-05-25, 2026-06-19, 2026-07-03, 2026-09-07。

### Q 原因归属修正（2026-09-24）

AVAILABLE 的 `setup.reasons` 是整段回放的汇总诊断，不能用作最新候选的失败原因。
摘要现分开显示当前模块缺证据、未结束候选的最新规则事实、历史形态失效数量。
候选摘要与详情使用相同事实身份、阶段与时间；早期原因保留在候选事实时间线。
无候选或时间关联的汇总放入折叠的“历史回放诊断”，不补造绑定；技术原文完整保留。

本机 VRT 冻结记录中，最新 D1 ATR 为 11.58133628411984225；前 13 根日线
（2024-09-25 至 2024-10-11 UTC）ATR 未形成，而 6 条 Setup 事实均未携带该原因。
页面据此展示早期 Context 时间范围供核对，不把这些行情时间冒充诊断绑定时间。
最新帧确实缺 ATR 时仍展示当前字段缺失，不按原因码一律隐藏。

Windows Python 3.12.14 / Chrome：相关展示测试 10 passed（包含本次 2 项新增回归）；
真实 Dashboard 仅重开同一冻结记录，逐一核对 6 条事实的形态身份与时间；Q 历史表
读取前后完整内容摘要一致。Ruff、配置源码路径后的 Mypy、diff 检查通过。
截图和本机检查记录位于忽略目录 `data/q-summary-scope/`。
未改策略、manifest 或数据库，未重新分析、未调用模型。
