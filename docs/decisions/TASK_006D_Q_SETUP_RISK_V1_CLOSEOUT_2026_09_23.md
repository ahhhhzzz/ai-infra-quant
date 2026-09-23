# TASK-006D-Q Setup/Risk 1.0.1 收尾与整合决定 — 2026-09-23

**FOCUSED REVIEW PASS / CLOSED**。本决定所在提交经普通快进成为远程
`roadmap/no-live-trading` 的祖先后，状态为 **INTEGRATED**。整合的是独立的
PAQS-Q Setup/Risk 与 Entry 资格参考层，不是产品接入、成交或市场有效性认证。

## 固定对象与审查归属

- 已独立聚焦复核的任务分支 `task/006d-q-setup-risk-v1` 固定在
  [`65c23f0b2b38182b2adf0f61dc7c311ee1c53f7a`](https://github.com/ahhhhzzz/ai-infra-quant/commit/65c23f0b2b38182b2adf0f61dc7c311ee1c53f7a)。
  Setup/Risk 版本为 `paqs-q-setup-risk-reference@1.0.1`，S01/S02 整改见
  [整改报告](../reports/TASK_006D_Q_SETUP_RISK_V1_REMEDIATION_01.md)。
  [1.0.0 原实现报告](../reports/TASK_006D_Q_SETUP_RISK_V1_IMPLEMENTATION_REPORT.md)
  及两版 manifest、历史证据保留原文与原身份。
- 产品分支预期起点为 `c35632638f310509babfea903c6d42dbb4092492`。
  本收尾提交从已审查 SHA 在独立分支形成，原任务分支不改写。
- 下述 Linux 聚焦审查结论由**用户提供并授权归档**，不是本轮 Codex 执行。
  本轮仅修改收尾文档、核对差异和链接，不重跑测试或行情。

## 外部独立聚焦复核（用户提供）

- 结论 **PASS**；S01、S02 **CLOSED**。Linux Python 3.12.14 下，原 3 个失败
  回归现均通过，Setup 非浏览器测试 27 项、所选 Event/F1 兼容测试 9 项通过，
  合计 **39 passed**。
- 新 1.0.1 manifest 代码摘要
  `849d50f23af1ca572adcbc7a972c61eff6bc61c7cefb6c9cb22c298260d2dac1` 一致；
  47 个既有上游依赖文件、旧 manifest、
  原实现报告和 `setup_targets.py` 未变。1.0.0 固定提交及证据不以新身份覆盖。
- 外部复核没有执行 Windows、浏览器或 AVGO。本地 Windows 验证和离线浏览器
  结果仅归属[整改报告](../reports/TASK_006D_Q_SETUP_RISK_V1_REMEDIATION_01.md)
  记录的原执行，不归属本轮收尾。

## 保留限制与整合边界

AVGO 未以 1.0.1 重跑，原 `INSUFFICIENT` 结论不变；合成演示不是市场回测，
尚未建立真实数据 Entry 资格。`LONG_READY` 只是规则资格，不代表开仓、成交、
持仓或收益。严格历史可知时间、复权版本及日历证据要求继续适用；F1 用户接受的
Linux 移动端布局限定例外及原 FAIL 记录保持原意。

本轮仅新增本决定并最小同步当前状态文档。源码、测试、策略参数、依赖、manifest、
历史报告及样本证据不变。仅当远程产品分支仍在预期起点、已审查 SHA 为收尾提交
祖先且无未审查源码变化时，才普通快进整合；不 squash、不 force-push，不更新
master/main。产品接入、Holder 建议、历史展示和 Q/E 比较留待后续独立任务。
