# TASK-006C-Q-F1 收尾与整合决定 — 2026-09-21

**FOCUSED REVIEW PASS / USER-ACCEPTED LIMITATION / CLOSED / INTEGRATED**。
本决定随 `roadmap/no-live-trading` 的普通快进生效；整合对象是框架底座，不是正式 Event 策略。

## 固定身份与历史链路

- 已审查任务分支：`task/006c-q-f1-versioned-quant-event-framework`，固定提交
  [`2f7dcd7bfca12a660d2e3fe3f65d3f8b964c7fb4`](https://github.com/ahhhhzzz/ai-infra-quant/commit/2f7dcd7bfca12a660d2e3fe3f65d3f8b964c7fb4)。
- 产品分支整合前起点：`8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`。
- 已核实起点是目标提交祖先，链路保留 R05 `7487cf57161a834d9100f983bab9d8534a1c0488`、
  [独立 R05 PASS](../reviews/TASK_006B_Q_R05_INDEPENDENT_REVIEW.md)、
  [006B-Q 收尾决定](TASK_006B_Q_CLOSEOUT_AND_006C_Q_HANDOFF_2026_09_21.md)、
  F1 交接 `857823a0dc39b4c10a1986c575bcbcd9dda11c85`、实现 `d0e8dc2`、整改
  `364412e` / `8a87150` 及 [closeout-01](../evidence/TASK_006C_Q_F1/closeout-01/REPORT.md)。
- [F1 冻结合同](../../prompts/tasks/TASK-006C-Q-F1_VERSIONED_QUANT_EVENT_FRAMEWORK_FOUNDATION.md)
  blob `c2c5448c1eb72fd0ece1572c31ba30246a761b51`；
  [整改合同](../../prompts/tasks/TASK-006C-Q-F1_REMEDIATION_01.md)
  blob `612197e9763b7708c87b3af2272717c7edb3daad`，均保留原文。

## 外部聚焦审查归属

来源是用户于本日提供并明确授权采用的 **ChatGPT 外部聚焦复核结论**，针对上述固定
`2f7dcd7…` 的 F01/F02/F03 及关联整改源码和差异。此处归档外部结果；本轮执行者没有
独立执行下面的审查测试，也不将这次复核扩称为重新审查整条研究和产品历史。

- F01、F02、F03：**CLOSED**；新增 Critical **0** / Major **0** / Minor **0**。
- 外部独立执行 `tests/paqs_q/test_remediation_01.py` 和 `tests/paqs_q/test_registry.py`：
  **47 passed**。Linux、Python 3.12.14、pytest 8.4.1、tzdata 2025.2。
- 外部审查下载的 43 个相关文件已核对 Git blob 身份；采用 `--confcutdir=tests/paqs_q`，
  是未加载产品级 conftest 的纯框架切片，不等于重新执行全产品回归或 Windows 测试。
- 外部审查独立比对 Windows/Linux canonical vectors、code hashes 和 digest，一致。
  Windows 的 91 项 F1 测试及浏览器结果引用
  [closeout-01 验证记录](../evidence/TASK_006C_Q_F1/closeout-01/validation.json)，不是外部重新运行。

F1-02 保持 **PASS**。其他已有验证按原执行 SHA 和范围引用；旧报告中的待审查/未整合
措辞是历史事实，由本决定更新当前状态，不修改旧报告。

## F1-12：用户接受的限定例外

用户明确表示：“linux就算了，我主要使用的是windows”。用户选择 Windows 为主要使用和
验收平台，接受既有 Linux 环境中以下用例的移动端首屏布局限制，免修复且不再阻塞 F1 整合：

`tests/browser/test_paqs_e_workbench.py::test_visual_acceptance_artifacts[390-844-success-True]`

该环境中 `#mode-frozen` 的 y=856.03125，不满足 844 高度首屏要求；整改前后都能复现。
Windows 同版本浏览器下整改前后均通过，详见原执行记录。原 Linux **FAIL** 保持不变。
F1-12 当前处置为 **USER-ACCEPTED LIMITED EXCEPTION（用户接受的限定例外）**，不称为
所有平台测试全部 PASS，也不推断操作系统是唯一原因。

例外仅限上述已记录的 Linux 布局项；不取消框架正确性、数据完整性、no-lookahead、
PAQS-E 隔离或只读边界要求，不接受其他未知失败。

## 整合与停止边界

本轮在独立 `integration/006c-q-f1-closeout` 分支/worktree 仅新增本决定，最小同步七份当前
状态文档：ROADMAP、MASTER_SPEC、ARCHITECTURE、STRATEGY_SPEC、REQUIREMENTS_MATRIX、
PAQS_ENGINEERING_GUIDE、PAQS_Q_FRAMEWORK。执行文档差异、链接、状态一致性及对象保护检查；
源码、测试、依赖、历史报告、研究证据和冻结合同不变，不重复执行适用的产品测试。
本轮检查结果：PASS；237 个相对链接及文档状态一致性通过，731 个受保护原对象的
Git mode/blob 与工作文件身份不变，`git diff --check` 通过；本轮测试执行数为 0。
只有远程产品分支仍处于预期起点且可快进，才普通快进到包含本决定的提交；不 squash、
force-push、改写任务分支或更新 master/main。最终交付回复提供读回 SHA 和固定文件链接，
避免在文件内制造自引用 SHA。

006B-Q 仍为 **REVIEWED / CLOSED AS REFERENCE RESEARCH**。
`RECOMMEND_CROSS_SAMPLE_ONLY` 仅是可选未来研究建议；严格历史确认和广泛市场适用性仍
**INCOMPLETE**。研究与框架通过不证明盈利、市场有效性或最终结构真理，不重开 R06。
B0 保持默认参考插件；A1 默认禁用且要求显式 ID/version 与 experimental 许可。
生产 Event 仍为 `UNAVAILABLE / EVENT_PLUGIN_NOT_CONFIGURED`。

下一任务为**正式 Event 引擎**；随后才是 Setup/Risk、量化展示与 E/Q 比较及产品接入。
这些后续能力尚未实现，本轮不启动。F1 收尾整合完成后停止。
