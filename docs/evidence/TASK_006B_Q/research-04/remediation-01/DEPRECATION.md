# R04-F01：保留证据的局部勘误

本勘误仅针对保留的 `study-01`、`study-02` 中逐 cutoff 的
`costs.segments["None"].centers`：这些值错误地记录为 0，不能用于 unresolved
segment 的活动中心覆盖统计。两轮原始文件保留，不覆盖、不删除。

原因是枚举键时把 Python `None` 转成字符串，计数比较时却仍使用原值。
统一 sentinel 为 `UNRESOLVED_SEGMENT` 后，冻结 W1 OBSERVATIONAL 的 100 个 cutoff
累计 unresolved 活动中心应为 1,921，resolved 为 8,479，合计 10,400。
原始 census 和 `audit-02` 已保留正确的逐条证据。

本勘误**不废弃**原有 event、transition、reason、support、calendar、case 或整体
market-gate 数据。support/events 的原零值在这些 unresolved 桶内仍为零；本轮只是
使用一致的键表达，并恢复漏计的 centers。原丢失／重现、覆盖成本和研究建议不变。

[study-03](../study-03/summary.json) 是本次新执行的修正输出，
[DELTA](DELTA.json) 保存精确的 100-cutoff 对照与三项守恒核验。
它目前是**等待聚焦复核的候选证据**；只有聚焦审查完成后才成为修正后的 R04
机器可读证据依据。本文件不宣告 F01 已独立关闭，也不宣告市场适用性通过。
