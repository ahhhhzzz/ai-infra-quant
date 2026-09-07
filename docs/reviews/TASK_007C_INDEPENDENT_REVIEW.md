# TASK-007C 独立审查记录

日期：2026-09-07

## 结论

**代码审查未发现阻断问题；独立验证受浏览器运行环境限制。**

本记录不宣称完整独立验收 PASS。非浏览器回归、静态检查和真实 Uvicorn HTTP 启动检查已独立通过；46 项浏览器专项在本审查环境中未进入业务断言。实现者报告的浏览器通过结果保留为实现证据，不转换为审查者的复跑结果。当前没有依据要求功能代码返工；完整独立浏览器验证仍待可运行 Chromium 的环境完成。

本次仅新增审查记录，不合并 TASK-007C、不移动权威分支、不启动下一任务。

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

## 独立验证结果

| 验证 | 本次实际结果 |
|---|---|
| `PYTHONPATH=src python -m pytest --ignore=tests/browser -ra` | **453 passed, 1 skipped**；30.70s |
| 上述测试中的配置接口专项 | 包含全部 **15 项**，通过 |
| `python -m ruff check src tests` | 通过 |
| `python -m ruff format --check src tests` | 161 files already formatted |
| `PYTHONPATH=src python -m mypy src tests` | 158 个文件，无问题 |
| 新建 SQLite 数据库及迁移 | 0001 → 0002 成功 |
| 实际 Uvicorn 与真实 HTTP | health、首页、OpenAPI、configuration、3 个自有静态资源、图表资源、自选列表、行情状态、snapshot、Decision history 均返回 200；默认配置与空历史断言通过 |
| 浏览器专项 `pytest tests/browser -ra` | **46 项均在共享 fixture 初始化阶段报错，未执行业务断言** |
| 已提交的 1440 / 900 / 390 首屏 PNG | 人工查看；身份、操作区、图表模式及响应式布局可读；属于实现者的合成 API 场景截图 |

非浏览器测试使用 Python 3.12.13 和项目锁定依赖；跳过项是未配置 `PHASE1_POSTGRESQL_TEST_URL` 的既有 PostgreSQL smoke。HTTP 检查使用禁用 provider、空模型密钥和临时数据库，无模型请求。

浏览器复跑使用 Playwright 1.55.0 / Chromium 140，启动出现：

```text
TargetClosedError: BrowserType.launch
FATAL chrome/browser/process_singleton_posix.cc:292
socket() failed: Operation not permitted (1)
```

受支持的云浏览器访问本地审查服务也返回 `net::ERR_BLOCKED_BY_CLIENT`。这些结果不足以判定应用浏览器行为失败，也不能计为浏览器通过。没有绕过运行环境限制。

实现报告另称完整测试 **499 passed, 1 skipped**、浏览器 **46 passed**，并记录 Python 3.12.14 / Chrome 152。该来源与本次独立运行分开计数，不能相加或冒充同一环境的结果。当前精确实现提交的 GitHub check-runs 查询返回 0；本记录不声称已有可核验的 CI 浏览器 PASS。

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

如需完整独立验收，在能够启动 Chromium 的隔离环境中，对 **同一实现 SHA** 运行现有 46 项浏览器专项并保留日志；不要为适应审查环境删减、跳过或改写测试。合成 API 场景应继续明确标注。若出现业务断言失败，再按实际失败发出有界返工任务。

未验证真实 Futu、付费 OpenAI、PostgreSQL 或真实 Windows 启动；Windows 相关现有回归已包含在非浏览器测试中。本审查不评估策略收益或真实交易适用性。007C 仍未整合，本记录不会自动授权后续任务。

## 固定来源

- [实现报告](https://github.com/ahhhhzzz/ai-infra-quant/blob/9e276ca163b1611a4253db5d953716f0acfb4c5f/docs/reports/TASK_007C_IMPLEMENTATION_REPORT.md)
- [批准合同](https://github.com/ahhhhzzz/ai-infra-quant/blob/70a3b246172e93dff7071308a9fce95bb2c32380/prompts/tasks/TASK-007C_PAQS_E_USER_DASHBOARD.md)
- [实现变更](https://github.com/ahhhhzzz/ai-infra-quant/compare/70a3b246172e93dff7071308a9fce95bb2c32380...9e276ca163b1611a4253db5d953716f0acfb4c5f)
