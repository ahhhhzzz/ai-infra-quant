# TASK-006C-Q-F1 — 最小收尾验证

日期：2026-09-21。**REMEDIATED / VALIDATION INCOMPLETE / AWAITING FOCUSED REVIEW**。
本轮补齐整改后 Windows 验证，仅交付证据与当前状态更新。框架已实现并整改，正式 Event
策略尚未实现；本报告不宣告独立审查 PASS、用户验收完成、F1 全部通过或合并。

## 身份与证据适用性

- 任务分支：`task/006c-q-f1-versioned-quant-event-framework`。
- fetch 后任务起点及本轮 Windows 实测：`8a87150685c123bcf9e67288d81ac50a0697a54b`。
- 产品分支 `roadmap/no-live-trading`：`8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`。
- [原合同](../../../../prompts/tasks/TASK-006C-Q-F1_VERSIONED_QUANT_EVENT_FRAMEWORK_FOUNDATION.md)
  blob：`c2c5448c1eb72fd0ece1572c31ba30246a761b51`；
  [整改合同](../../../../prompts/tasks/TASK-006C-Q-F1_REMEDIATION_01.md)
  blob：`612197e9763b7708c87b3af2272717c7edb3daad`，均未修改。
- 独立 detached worktree 从该起点建立；原任务 worktree 的 `d0e8dc2` 及其他工作区保留。
  本轮交付提交仅改文档和证据，实际测试 SHA 不改称交付提交。

[Linux 历史验证](../remediation-01/validation.json) 的实际执行 SHA 是
`5b62a250b93ff35e7a3baa8f65019bec4979e39b`，远程同树镜像为
`364412ec94c7138480e8e3b0e902d57e4ba55dc3`。已核实镜像的完整 tree 为历史记录中的
`d93c625e1a52b856aa6a0d78e282d10d4cab2da0`，且其 `src`、`tests`、`tools` 和
`pyproject.toml` 对象与本轮实测起点完全相同。本轮不声称重跑了这些 Linux 测试。
完整对象、依赖及命令归属见 [机器记录](validation.json)。

## 本轮新执行

真实 Windows 11（10.0.26200），Python 3.12.14；pytest 8.4.1、tzdata 2025.2、
Playwright 1.55.0。现有 Python 环境的全部 runtime/dev 精确版本符合 `pyproject.toml`；
已记录完整已安装包版本。未安装依赖或部署其他平台。

| 检查 | 实测 SHA | 结果 / 退出码 |
|---|---|---|
| `python -m pytest tests/paqs_q -ra --tb=short` | `8a871506…` | 91 passed、1 warning，98.22s / 0 |
| `python tools/validation/paqs_q_f1.py --vectors <新文件>` | `8a871506…` | 28 组 Windows 向量 / 0 |
| `python docs/evidence/TASK_006C_Q_F1/remediation-01/verify.py --windows <新文件>` | `8a871506…`，文档修改前 | 跨平台比较、713 个历史保护对象、224 个链接通过 / 0 |
| 指定移动端浏览器用例 | `8a871506…` | 1 passed、1 warning，11.12s / 0 |
| 同环境同用例整改前对照 | `d0e8dc22b38d85b0d1395cf76fc03f2de1e85122` | 1 passed、1 warning，9.70s / 0 |
| 本轮文档 diff、链接、闭合变更范围及保护检查 | 本轮文档工作树，以 `8a871506…` 为基线 | PASS，见 [保护记录](protection.json) |

warning 均为现有 Starlette 引用 anyio.abc.BlockingPortal 的弃用提示。测试使用临时合成
资源；浏览器 fixture 创建临时 SQLite、迁移并启动自己的 Uvicorn。未读取用户数据库、
调用行情或模型服务。原验证器有固定整改变更范围，因此在新增本目录之前执行，历史脚本未改。

## F1-02：PASS

[新 Windows receipt](windows-vectors.json) 与 [整改后 Linux receipt](../remediation-01/linux-vectors.json)
的完整 `vectors`、`code_hashes`、`vector_digest`、Python/tzdata 版本逐项相等，平台分别为
Windows / Linux。28 组条目包含 input/result hash、canonical 输出 bytes SHA-256、record IDs
和状态；共同 digest 为：

`dbcdb54348d004819d58f5c948e8226851f7694113facffb81201314aed36e32`

B0 code hash：`623f63f622cfdcfe364b121c99e6b35e987054b94ee24c9063f505484c1ff1df`。
A1 code hash：`da1127afc9d76bb8edaa04833cb9f0cce54307fa8f2b50327900d780544ef040`。

两平台 F1 suite 均包含相同的三个固定预期 canonical 内容/摘要向量及 Decimal、UTC、Unicode、
LF/CRLF 检查。Linux receipt 保留结果字节摘要而非完整结果字节，本轮比较的是完整向量内容及
其中每个输出摘要，没有虚称重新取得 Linux 原始输出。未将整改前 Windows receipt 或 win32
mypy 当成本轮执行。B0/A1 golden parity 通过，A1 仍须显式 ID/version 与逐次 experimental
许可；默认仅 B0，生产 Event 仍为 `UNAVAILABLE / EVENT_PLUGIN_NOT_CONFIGURED`。

## F1-12：FAIL / INCOMPLETE

唯一未满足项仍是历史 Linux 记录中的
`tests/browser/test_paqs_e_workbench.py::test_visual_acceptance_artifacts[390-844-success-True]`。
在 390×844、success、light 配置下，`#mode-frozen` 的 y=856.03125，不满足 y<844。
Linux 在整改代码实测 SHA 和整改前 `d0e8dc2` 均失败，原失败没有豁免。

本轮仅为补足平台差异，使用现有 Chromium **Headless Shell 140.0.7339.16 / build 1187**，
`TASK007C_BROWSER_CHANNEL=""`，在 Windows 对当前及整改前 SHA 各执行一次原样用例，均通过。
两次 Windows 执行共用同一 Python/依赖/浏览器、视口、fixture 和配置；前端、浏览器测试及
依赖声明的 Git 对象也完全相同。Linux 记录的 Python、pytest、Playwright、浏览器版本匹配；
历史记录没有完整传递依赖和字体清单，因此不推断操作系统是唯一原因。

这是既有 Linux 环境中的移动端首屏控件可见性问题，证据不显示由本轮 Q 整改引入。
Windows PASS 不替代 Linux FAIL，不能据此将完整浏览器验收记为 PASS。影响范围是该
移动端首屏验收项；现有证据不证明其他视口或全部平台不存在问题。未重跑 Linux、修改 UI、
删除测试或放宽断言。是否另行修复或由用户接受限制，交独立聚焦复核判断。

## 引用的历史验证与停止范围

引用 [整改报告](../remediation-01/REPORT.md) 及其机器记录：Linux 91 项 F1、268 项研究/输入、
1096 项选定产品回归通过；浏览器为 64 passed / 1 failed（分段去重，最终无 fixture errors）；
Ruff/format、native/win32 strict mypy、临时服务启动及保护检查通过。主实测 SHA 均为上述
`5b62a250…`，Linux 浏览器失败的整改前对照为 `d0e8dc2`。这些是引用结果，没有本轮重跑。
不宣称全产品 suite 或 PostgreSQL 实库通过。

本轮新增本目录四个文件：`REPORT.md`、`windows-vectors.json`、`validation.json`、
`protection.json`；仅同步七份当前状态文档：ROADMAP、MASTER_SPEC、ARCHITECTURE、
STRATEGY_SPEC、REQUIREMENTS_MATRIX、PAQS_ENGINEERING_GUIDE、PAQS_Q_FRAMEWORK。
完整路径见保护记录。源码、测试、golden、manifest、依赖、历史报告及两个合同均不变。
PAQS-E、Analyze、旧结构、前端/API、数据库和迁移无改动。

具备提交独立聚焦复核的证据条件，但 F1-12 尚未全部满足，不具备自行宣布完整验收通过的条件。
保持原任务分支普通快进交付；不更新产品分支、不合并、不启动正式 Event、Setup/Risk 或产品接入。
