# R03-F01 — M2 保留状态、外部重放输入与 lineage 澄清

日期：2026-09-10。状态：**文档整改完成，等待 R03-F01 独立聚焦复核**。
依据：[本轮合同](CONTRACT.md)及
[精确独立审查第2节](https://github.com/ahhhhzzz/ai-infra-quant/blob/8338c2b61cd60dc5c1079a3648b66d9643b19031/docs/reviews/TASK_006B_Q_R03_INDEPENDENT_REVIEW.md#2-finding-r03-f01--frozen-m2-state-definition-needs-an-additive-clarification)。
本附录是针对该状态保留差异的**后续权威澄清**；不改写冻结计划、原报告或代码，也不自行关闭审查发现。

## 1. 字面差异与适用口径

[冻结 PLAN 的原文第49–50行](https://github.com/ahhhhzzz/ai-infra-quant/blob/2e048607414021e12984871db3a888cba7f20557/docs/evidence/TASK_006B_Q/research-03/PLAN.md#L49-L50)写道：

> State includes the entire supplied snapshot sequence and grows O(total recognized events + steps); it is extra input.

但受审实现中的
[History / advance 第156–183行](https://github.com/ahhhhzzz/ai-infra-quant/blob/7044bb1d3a4e9752bbad0417b753b706723d5b8b/tools/research/paqs_q/r03/models.py#L156-L183)
没有保留整个输入快照序列。[最终数学规格第4节](https://github.com/ahhhhzzz/ai-infra-quant/blob/7044bb1d3a4e9752bbad0417b753b706723d5b8b/docs/research/PAQS_Q_CONFIRMATION_AND_ROLLING_STABILITY_R03.md#4-m2--immutable-first-recognition-record-comparator)
描述的实际保留状态、O(K+N)界限和外部日程限制与代码一致。

**完整快照序列保留未实现。**按计划字面要求，受审实现偏离了这一状态保留要求。
现有证据不能确定冻结时究竟意图完整存储，还是误把概念上的历史依赖写成了对象实际保留的数据；
本附录不补造此前意图，也不把原文重新解释为早已与实现相同。
本轮依据整改合同记录现有受审模型的“识别记录＋最新 cutoff＋摘要＋计数”口径，不补实现全历史存储。

[原报告第1节](https://github.com/ahhhhzzz/ai-infra-quant/blob/7044bb1d3a4e9752bbad0417b753b706723d5b8b/docs/evidence/TASK_006B_Q/research-03/REPORT.md#1-精确依据与执行顺序)
关于模型未调整以及中间只修正类型／格式的概括，**不能作为冻结状态定义与最终模型完全一致的证明**。
应明确附带本项例外：完整序列保留的冻结描述没有落实，最终规格采用了实际记录状态解释，
该差异直到本附录才作显式追认说明。此限定不证明发生过按枚举结果调参，也不证明此前已批准这一差异。
原提交顺序与原文继续作为历史证据保留；本附录仅就此处文档主张优先适用。

## 2. 实际保留、概念依赖、外部输入是三类对象

| 类别 | 内容 | 不应推断的能力 |
|---|---|---|
| History.records | 不可变 Recognition tuple；每条包含 Event、实际 recognized_at 和 lineage_before。Event 保留类型、价格、两端时间／引用、可用时间、支持／版本引用及 identity | 这些引用和选中事件不是全部 OHLCV，也不是每一步完整 Snapshot |
| History.cutoff | 最近一次成功 advance 的 snapshot.cutoff | 不能还原此前全部 cutoff 或未产生新事件的调用 |
| History.lineage | 最近一步的确定性链式摘要 | 不含可供取回的快照序列或原始证据 |
| History.steps | 已成功处理的步数；无新事件的合法步骤也计数 | 计数不包含各步输入、顺序细节或时刻 |
| 概念上的历史依赖 | 生成当前记录／摘要所依赖的初态及过去有序输入 | “曾影响计算”不等于“仍存储在 History 中” |
| 外部重放材料 | 初态、完整有序快照／cutoff 日程、固定规则及配置；必要时还包括重建快照的原始版本证据 | 不是由最终 History 自动提供的内置存档服务 |

临时集合 `seen`、当前 `snapshot` 和 `additions` 用于单步更新；返回的 History 不存放 Snapshot 列表，
也没有完整的最近 Snapshot 字段。记录内的 lineage_before 只出现在产生新识别记录的步骤，不能补齐
那些没有新记录的步骤。调用者若自行保留旧 History 或全部快照，那是外部保留行为，不能计作模型已实现。

## 3. 怎样提供足够的外部重放输入

从头重放的明确初态是代码的 `History()`：records=空 tuple、cutoff=None、steps=0、
lineage=`digest("PROPOSED_SEMANTICS:R03-RECORD-1", "EMPTY")`。
必须按原顺序提供每一个成功接受的 Snapshot，包括没有新事件、UNCERTAIN 或 INVALID 的步骤；
cutoff 严格递增。被 advance 拒绝的调用不进入状态更新序列；若要审计拒绝尝试，仍需额外外部材料。

有两种不同层次的重放：

1. **状态转移重放**：提供完整初始 History 和完全相同的有序 Snapshot 对象，按固定版本的 advance
   逐步更新。需要 Snapshot 的所有字段及 tuple 顺序，包括 rule、cutoff、warm、status、reason、
   events、refs、versions、active_refs；只提供事件列表或最终 cutoff 不够。保持已审代码及其 canonical
   序列化／digest 规则、Decimal 与 aware-UTC 表达。M1 rule 为 R03-LOCAL-1，M2 为 R03-RECORD-1，
   两者保留 `PROPOSED_SEMANTICS:` 前缀。N=8，每步原选 W=0 或2必须明确，不能猜测或替换。
2. **从源数据重建快照再重放**：还需外部保存对应原始行情版本、身份／时区、完成／可用时间、质量、
   调整／session 等 evaluator 输入，以及每一步 cutoff 和配置。按同一已审 M1 evaluate、
   prepare/validate、Decimal Context(50, HALF_EVEN)、canonical observation/version identity 规则重建。
   后来的最新行情不能替代旧时点版本，未知可用时间不能补造成已知。History 的支持引用不能还原这些值。

只从显式 checkpoint 继续时，必须提供它的全部四个字段，不能只有 lineage。继续计算不等于审计了
checkpoint 以前的历史；验证那段历史仍需原初态和此前完整外部输入。改变初态、遗漏无新事件的步骤、
改变 warm/config 或日程，都是不同的重放输入，不能冒充同一次原始运行。
本轮只说明前提，不新增存档、重放服务或执行重放实验。

## 4. 实际界限与 lineage 能说明什么

设 K 为此前已保留的识别事件数，N 为当前快照的有界规模（模型中固定8），S为成功步骤数。
按最终规格的对象／记录计数口径，当前 History 保留 O(K) 条记录及固定数量元数据；
单步 advance 工作和临时内存为 O(K+N)：构建 seen、扫描当前事件、复制／连接 tuple、编码当前快照摘要。
当前状态加单步工作内存为 O(K+N)，没有自动保留 O(S) 个快照。
若严格按位计数，Python 的 steps 整数还需 O(log(S+1)) 位；这不等于 S 个历史对象。
调用者另外保留全部快照、旧状态或源数据的空间成本必须另计。K可随日程增长，模型不是有界历史存储。

每个接受步骤执行 `new_lineage = digest(RECORD, (old_lineage, snapshot))`；
即使没有新识别记录，快照也参与摘要。给定固定初态、规则和完整外部序列，可以确定性重算并与记录的
摘要比较；同时比较最终 records、cutoff 和 steps 才能核对完整状态结果。
摘要链并不单独编码初态 records/cutoff/steps，不能把任意同 lineage 的 checkpoint 当作已验证初态。

匹配的摘要是给定输入和实现下的一致性检查，受摘要碰撞等通常限制；它不是可逆序列、来源签名或
历史时间见证。它不能恢复先前快照，不能独立证明当时证据可用，也不能证明输入行情或时间声明真实。
advance 的有限 rule／顺序／事件时间检查并不替代源数据校验与来源审计；外部构造的快照不能仅因获得
lineage 就被认证为真实、完整或当时可得。

## 5. 受影响与不受影响的结论

本轮修正的是**状态保留范围、可恢复性及原报告冻结一致性主张**。没有改变任何可执行规则或历史结果：

- P2 的显式历史依赖依然成立：相同当前窗口配合不同 records/初态仍可有不同输出；证明不要求
  History 存储每个过去快照。完整外部日程是从头重现该状态的条件，不是隐藏的已存字段。
- P6 的 append-only 归纳只使用旧记录 tuple 加新记录，保持旧 Event 和 recognized_at；不要求保存
  每一步完整 Snapshot。未出现新事件的步骤不追加识别记录，但仍更新 cutoff、lineage、steps。
- recognized_at 仍是首次接受该未见 identity 的实际 supplied cutoff，不回填极值、反转完成或可用时间；
  同 identity 再出现不重写首次识别时间。迟到／修订的解释及其限制不变。
- 已提交的 M2 历史反例、M1 双视图、19,683项枚举与 H1 的13个旧 Pivot 重现证据均保持原 blob。
  旧口径的丢失／重现、覆盖代价和条件证明没有因本附录重算、改名或变成更强的保证。

这些是对未变代码及已有证据的文档核对，**不是本轮重新执行测试／枚举所得的结果**。
数学保证继续以已声明前提为限；真实行情完整性 INCOMPLETE，产品采用及006C-Q NOT AUTHORIZED。
参见[整改交付记录](REPORT.md)。
