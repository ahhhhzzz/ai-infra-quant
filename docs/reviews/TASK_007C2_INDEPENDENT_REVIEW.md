# TASK-007C2 独立审查

日期：2026-09-08

结论：**CODE / CONTRACT REVIEW PASS — 未发现需返工的代码／合同阻断问题。**

本轮完成精确 SHA 的独立代码、合同、文档、提交截图审查，以及非浏览器回归和实际 Uvicorn HTTP 验证。独立浏览器复跑在环境驱动启动阶段失败，未执行其业务断言；因此本记录不声称所有测试已由独立审查者复跑通过。实现者的 Windows 浏览器结果单独归属，见第 4 节。

## 1. 精确审查对象

| 项目 | 核实结果 |
|---|---|
| Repository | ahhhhzzz/ai-infra-quant |
| 实现分支 | task/007c2-workbench-ui-cleanup |
| 精确实现 SHA | d2d25efc79d2560a7ed09895c7dd7a2c1724aee9 |
| 实现树 | 092213b2ea6e40d88487b5fa11a2435dd4d46418 |
| 唯一直接父提交／合同 | c5bd152210ee8b4d071a138867f72d7f8fbd9387 |
| 权威分支 | roadmap/no-live-trading |
| 权威 SHA／merge base | 2cc4eeea3cc31d4fd1f1a4e9c1fbec237f82a2c4 |
| 实现相对权威 | ahead 2 / behind 0 |
| 审查写入分支 | review/007c2-independent |

GitHub 直接读取与本地 Git 对象一致。007C1 已按合同整合到 2cc4eee...；007C2 仍未合并。审查使用干净 detached checkout，没有改动受审代码、合同、测试或原报告。

合同：
[prompts/tasks/TASK-007C2_WORKBENCH_UI_CLEANUP.md](https://github.com/ahhhhzzz/ai-infra-quant/blob/c5bd152210ee8b4d071a138867f72d7f8fbd9387/prompts/tasks/TASK-007C2_WORKBENCH_UI_CLEANUP.md)

## 2. Findings

| 严重性 | 数量 |
|---|---:|
| Critical | 0 |
| Major | 0 |
| Minor | 0 |

以上计数仅表示本次审查范围内没有确认的缺陷，不将未执行的检查算作通过，也不表示整个应用不存在问题。

### 弹窗布局与凭据行为

- `#credential-form` 明确设置 `grid-template-columns: minmax(0, 1fr)`，其 ID 优先级覆盖全局 form 六列和响应式三列规则，直接修复截图中的根因。
- 表单直接子元素限制最小宽度，说明及长字符串换行，输入满宽；标题、说明、输入、状态、操作区按单列排列。
- 弹窗宽度限制为 36rem 与视口宽度减 32px 的较小值，最大高度为视口减 32px，内部纵向滚动，主题变量分别控制主次按钮。
- HTML 添加可访问标题／说明、密码 autofocus 与专用操作组。
- `paqs-e.js` 唯一改动是在既有 close 清空密码之后恢复配置按钮焦点。保存、删除、状态读回、共享槽位与后端凭据路径不变。
- 新浏览器测试检查实际元素几何、顺序、溢出、输入宽度、按钮可达、Escape／关闭／焦点恢复及无隐式分析请求；200% 场景明确是实际计算字体从 16px 变为 32px，不冒称浏览器页面缩放。

### 历史管理区清理

- 旧 local-admin 容器、初始资产卡片、重复 Watchlist administration 与混合 provider 列表已移除。
- `app.js` 相对合同只有 56 行删除：旧自选渲染函数、调用、管理区查询函数和初始化调用。保留主自选加载／添加／删除／切换代码。
- 旧管理区专用 portfolio、performance、brokers、fundamental-data/providers、event-data/providers、market-data/providers 请求退出普通页面初始化。
- 已检查删除 DOM 与代码依赖相匹配，没有遗留对这些旧节点的初始化更新路径；既有当前行情状态、主自选和历史／冻结证据仍保留。
- 无数据库清理、seed 修改或后端 API 退役，符合“界面移除但保留历史数据”的合同边界。

### 保护范围与文档

- 全部 backend/application/core/database/integrations/resources、迁移、seed、依赖、launcher、source identity、vendored chart、Markdown renderer 和历史合同／审查／收尾文件相对合同无差异。
- 29 个新增／变更文件均属于授权的前端、当前文档、测试、报告与合成截图范围。
- 当前五份规格／矩阵更新为 A/B/C 已整合、C1 用户验收并整合、C2 待审查；Narrative-first 与旧结构化历史分开表述。
- 没有把用户 C1 验收重写为助手独立付费测试，也没有改动旧收尾记录当时的未整合事实。
- 原有两处集成测试的旧管理区文案／排序断言被明确的“旧区不存在、主自选／历史／只读标识存在”断言取代；不是通过删除仍需保留的业务行为来取得通过。

## 3. 本轮实际独立验证

环境：Linux，Python 3.12.13；使用项目已声明依赖。所有数据库和进程由本轮创建，仅用于临时验证；没有真实凭据或供应商调用。

| 命令／检查 | 本轮结果 |
|---|---|
| `PYTHONPATH=src:. python -m pytest --ignore=tests/browser -q -ra` | **1234 passed, 7 skipped, 1 warning in 53.78s**；exit 0 |
| `python -m ruff check .` | All checks passed |
| `python -m ruff format --check .` | 201 files already formatted |
| `python -m mypy --platform win32 src tests` | 197 source files，无问题；这是 Linux 上的 Windows 目标类型检查，不是真实 Windows 执行 |
| `git diff --check c5bd152 HEAD` | 通过 |
| 受保护路径 Git diff | 空 |
| 临时 SQLite 全部迁移 | upgrade head 成功；实际启动报告 0003_task007c1_narrative_ledger |
| 实际 Uvicorn／真实 HTTP | /health、首页、OpenAPI、configuration、5 个静态脚本／样式／图表资源共 9 个请求均为 200 |
| configuration 内容 | 11 个注册模型 |
| 实际首页 | 具有 credential-actions，旧管理区文案不存在 |
| 审查前后工作区 | 干净；实现 HEAD 未变 |

7 个跳过项是：1 个未配置 `PHASE1_POSTGRESQL_TEST_URL` 的 PostgreSQL smoke，6 个缺少 PowerShell 的启动器握手场景。唯一 warning 为 Starlette 的 BlockingPortal 弃用提醒。没有把这些项记录为本轮执行通过。

## 4. 浏览器与截图：证据来源分开

本轮尝试：

```text
TASK007C_BROWSER_CHANNEL=chromium
PYTHONPATH=src:.
python -m pytest tests/browser/test_paqs_e_ui_cleanup.py -x -q
```

结果：首个场景在 session browser fixture 初始化时失败，`1 warning, 1 error in 0.17s`，exit 1。错误为：

```text
PermissionError: [Errno 13] Permission denied: '.../playwright/driver/node'
```

没有进入浏览器业务断言。没有修改测试、跳过／xfail 业务门槛或绕过运行环境限制。该错误不能证明弹窗业务失败，也不能当作浏览器通过。

实现者报告在精确提交对应的 Windows 环境：
- 完整测试 1350 passed / 1 skipped / 1 warning；
- 其中 110 个真实 Chromium 浏览器业务场景全部通过；
- 新增 C2 专项 11 个场景；
- 12 张提交 PNG 为真实应用页面配合合成拦截数据。

这是**实现者执行证据**，未冒充本轮独立执行，也不与本轮 1234 个通过相加。

本轮独立打开并视觉检查了以下 8 张提交图片：
- modal-1440x900-light.png
- modal-900x900-dark.png
- modal-390x844-light.png
- modal-390x844-light-actions.png
- modal-390x844-dark-actions.png
- modal-1440x900-text-200-percent.png
- workbench-1440-dark.png
- workbench-390-dark.png

可见弹窗标题与说明恢复横向可读，密码框满宽，长文本正常换行；窄屏滚动后的保存／删除／关闭按钮完整可见；工作台保留主自选、行情、Narrative／Legacy 历史与冻结图，旧资产区消失。未发现截图中的新阻断性重叠或裁切。

截图为 full-page 捕获，图高不等于浏览器视口高；遮罩到视口底部截止不能据此推断应用异常。长模型名、重复错误与惯性保留的 hostile-text 安全测试内容均被明确标为合成场景，不能当作真实模型报告。

来源：
[实现报告](https://github.com/ahhhhzzz/ai-infra-quant/blob/d2d25efc79d2560a7ed09895c7dd7a2c1724aee9/docs/reports/TASK_007C2_IMPLEMENTATION_REPORT.md)；
[截图与场景索引](https://github.com/ahhhhzzz/ai-infra-quant/blob/d2d25efc79d2560a7ed09895c7dd7a2c1724aee9/docs/evidence/TASK_007C2/README.md)。

## 5. 结论与后续

**独立代码／合同审查通过；没有提出功能整改任务。**

判断依据是精确版本／范围、实际源代码、检查到的测试断言、独立非浏览器执行、真实 HTTP 以及提交截图之间一致。建议可将该精确实现提交作为整合候选，整合决策须保留本轮浏览器未独立复跑成功的透明记录；不声称“全部独立验收项目已经执行通过”。

此记录不自行合并，不改变 007C2 实现分支或权威分支，不启动下一任务。后续整合前重新核对实现 SHA、权威 SHA 与祖先关系，保持历史审查与数据完整。
