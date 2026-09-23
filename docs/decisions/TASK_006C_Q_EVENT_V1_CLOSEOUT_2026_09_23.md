# TASK-006C-Q Event 1.0.1 收尾与整合决定 — 2026-09-23

**FOCUSED REVIEW PASS / CLOSED**。本决定所在提交经普通快进成为远程
`roadmap/no-live-trading` 的祖先后，状态为 **INTEGRATED**。整合的是版本化价格 Event
参考实现，不是正式 Setup/Risk、交易资格或产品界面。

## 固定对象与执行归属

- 已独立聚焦复核的任务分支：`task/006c-q-event-engine-v1`，固定 SHA
  [`9c598fdd0dacb51a60edc053143d2b2a21208b00`](https://github.com/ahhhhzzz/ai-infra-quant/commit/9c598fdd0dacb51a60edc053143d2b2a21208b00)。
  其中 Context/Event 均为 1.0.1；[原实现报告](../reports/TASK_006C_Q_EVENT_V1_IMPLEMENTATION_REPORT.md)
  和 [E01/E02 整改报告](../reports/TASK_006C_Q_EVENT_V1_REMEDIATION_01.md)保留原文。
- 产品分支预期整合起点：`5326ff6cfa3cae19ebb186643bc3a16bed88b518`。
  本决定从已审查 SHA 在独立 `integration/006c-q-event-v1-closeout` 分支形成；
  原任务分支不改写。该起点是已审查 SHA 的祖先。
- 下述聚焦审查结果由**用户提供并授权归档**。本轮 Codex 没有执行这些 Linux 审查测试，
  也没有复审整条历史、重算行情或补造审查日志与签名。

## 外部独立聚焦复核（用户提供）

- **FOCUSED REVIEW PASS**；E01、E02 **CLOSED**，本次聚焦范围内无未关闭阻断问题。
- Linux、Python 3.12.14：原 **4** 个独立失败复现现均通过；Event 非浏览器
  **85** 项、F1 兼容 **47** 项通过，按用户提供的分组合计 **4 + 85 + 47 = 136** 项。
- Context/Event 两份 1.0.1 manifest 校验通过；原 F1 的 34 个文件、B0/A1 和 Event
  1.0.0 清单未变。1.0.0 固定提交与证据继续保留，不以 1.0.1 身份覆盖。
- 外部复核未执行 Windows、浏览器或 AVGO。Windows 190 项组合验证及后续 6 项
  定向复查属于上述整改报告中的本地执行；历史 AVGO 仅属于原 1.0.0
  **OBSERVATIONAL** 样本，未以 1.0.1 重跑。

## 边界与整合条件

严格历史可知时间与复权证据要求、固定历史起点敏感性、F1 的用户接受 Linux 布局
限定例外均保持原意。Event 只输出价格事实与触发候选；正式 Setup/Risk、交易资格、
Q/E 比较、产品 API/UI 尚未完成，不据此声称市场有效性或可交易结论。

本轮仅新增本决定并最小更新当前状态文档。源码、测试、参数、依赖、manifest、
历史报告和样本证据不变；本轮不重跑测试或行情。仅当远程产品分支仍处于预期起点、
本提交可由其快进且无未审查代码变化时，才普通推送整合；不 squash、不 force-push，
不更新 master/main。下一功能任务为正式 Setup/Risk，本轮不启动。
