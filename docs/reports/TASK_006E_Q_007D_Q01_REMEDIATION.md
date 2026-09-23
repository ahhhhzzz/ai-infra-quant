# TASK-006E-Q / TASK-007D — Q01 Holder 目标绑定聚焦整改

状态：**Q01 LOCALLY REMEDIATED / WINDOWS FOCUSED VALIDATION PASS / AWAITING Q01 INDEPENDENT RE-REVIEW / NOT INTEGRATED**。整改起点为任务分支 `task/006e-q-007d-product-compare` 的 `06748540d67f2c120f8dfecc46a342db9f1c6aaf`；产品分支保持 `971c64a86998b2140e2549a1dd44e1f716e30e9e`。这是后续增量记录；[原实现报告](TASK_006E_Q_007D_IMPLEMENTATION_REPORT.md)的正文、原测试归属和原 Holder 1.0.0 身份均保留，不将原结论改写为整改后执行。

## 审查发现与修复

用户提供的外部聚焦审查结论为 **NEEDS REVISION，Q01 Major**。外部 Linux Python 3.12.14 执行 17 项 Q 与 26 项 E 测试通过，另新增 Q01 回归失败；三份上游 manifest 校验通过，所覆盖的 51 个文件未变。该外部审查没有执行 Windows、浏览器、OpenD 或付费模型；这些结果不是本轮本地测试。

本地 Windows 先用原 `demo_bundle()` 截至 `2025-05-23T15:30:00Z` 的 W1/D1/M30 完成 bar 和已收到的开盘参考重跑 Setup。整改前新增回归 **1 failed**：13:30–14:00 的 M30 high 为 110.32，而目标 110.2 到 15:30 的新候选 `NO_TRADE` 事实才首次出现；两个 Holder 项却都报 `TARGET_REACHED_REVIEW`。根因是把目标来源结构的 `known_at` 当作该 Setup 的目标绑定时间，并从最新任何带 `target1` 的事实取目标。

Holder 独立身份升至 `paqs-q-conditional-holder@1.0.1`，规范化源码 SHA256 为 `48f30d1c225f6f6e403543d23d0c2e6099c8cfb5980697f4f5ec13defd0fb1e8`。每个 Setup 选其最早有效 Stage A 的候选及冻结事实作为条件式参考；同候选合格 Stage B 若改选不同 T1，则只从 Stage B 事实生效时刻使用新目标。重复相同目标不重置原绑定时刻；其他候选的 `NO_TRADE` 目标不能替换，多个有效候选目标冲突则 `UNDETERMINED`。完成常规 M30 必须整体位于绑定时刻之后、截至 `as_of` 已完成且可用；无触价时的日历与 M30 覆盖证明也从同一时刻开始。输出保留 Setup、候选、绑定事实、绑定时间、结构 `known_at`、目标来源，以及命中 bar 的版本引用、来源和时间。硬失效优先及 Entry/Holder 分离不变。

修复后上述原始 OHLC 前缀的两项条件式 Holder 均为 `THESIS_VALID`，参考目标仍为先前有效的 115.2，**没有**把 15:30 `NO_TRADE` 的 110.2 或此前触价回填。另在原合成 OHLC 的 16:00 常规 M30 将 high 明确改为 115.5、同步调整所属 D1/W1 high 以保持跨周期一致，再重新运行完整 Setup；绑定后的完成 bar 触及会给 `TARGET_REACHED_REVIEW`，且记录该 bar 的 `version_ref`。这是合成规则验证，不是新市场研究。跨界 bar、同候选 Stage B 新目标、重复同一目标及不同候选冲突亦有聚焦回归。

## 本轮本地 Windows 验证

环境：Windows 11，Python 3.12.14，pytest 8.4.1。以下均在整改后的源码上执行：

| 检查 | 实测 |
| --- | --- |
| Q01 原始 OHLC 与边界回归、Q 输入/产品分析、Q 存储/API、架构聚焦切片 | `24 passed` |
| 现有 Q 页面 Chromium 冒烟 | `1 passed`，使用测试替身行情/模型，不是付费服务执行 |
| 代码与类型 | `ruff check src tests`、`ruff format --check src tests`、Holder 源码 `mypy --strict --follow-imports=silent` 通过 |
| 上游身份 | Context `510ece60…eedfc`、Event `67fe4a16…68cbc`、Setup `849d50f2…0d2dac1` manifest 校验通过；本次未修改其覆盖文件 |

本轮没有重跑 E 的 26 项历史兼容测试或原浏览器矩阵；外部 Linux 17/26 与此前 Windows 执行分别保持原归属。原 AVGO `INSUFFICIENT` 未重跑且不变。当前真实采集仍缺严格历史可知时间、完整 CLOSED 日历及独立开盘证据；本机未做 OpenD/真实模型调用。未更改上游策略、参数、manifest、原历史证据、数据库或界面功能；未更新产品分支。下一步仅为 Q01 聚焦独立复核。
