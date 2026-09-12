# R05 冻结案例完整判读

日期：2026-09-12。已逐张查看全部 14 张 PNG，并核对对应 JSON。冻结 rubric 的 15 个类别命中，经一个相同焦点合并为 14 图（W1 4、D1 5、M30 5），没有事后替换案例。

全部图为 OBSERVATIONAL / PARTIAL / PROVIDER_QFQ_CURRENT，历史 available_at 未知；不能称为严格历史确认。标题为评估 cutoff；横轴是 UTC bar start，正文 end 坐标对应事件 extreme_time，二者不能混同。三角为极值、下一根空心方块为确认，灰叉为支持不足。截取范围由冻结规则确定，个别图边缘的非焦点上下文事件确认在截取范围之外，其精确 ref/time 仍保留于 JSON；焦点事件的确认均可在图内核对。图中的确认后 K 线也全部早于相应 cutoff，未用于收益、未来方向或结果标签。

各 OBSERVATIONAL 周期五个类别均有命中，无需用其他图填充零类别；三个 AS_OF 的五个类别均为零，因为全部证据不足。hard invariant anomaly 为零。

## D1 · 新增同类对

Case ID：`219c2df8eb70d731e8f1fa9be51a4f1fb81ce0a20d94aed15dc8fd4231a2cda6`；cutoff：`2026-04-16T20:00:00Z`。
[图表](charts/D1.219c2df8eb70d731e8f1fa9be51a4f1fb81ce0a20d94aed15dc8fd4231a2cda6.png) · [精确案例数据](cases/D1.219c2df8eb70d731e8f1fa9be51a4f1fb81ce0a20d94aed15dc8fd4231a2cda6.json)

A1 新增 2025-08-28 HIGH 308.737838559，前一中心为已接受 LOW；它与 2025-09-05 HIGH 353.748043061 形成间隔 5 的 HIGH/HIGH。图内中间三处灰叉显示支持不足。该不利案例直接反驳“去掉 veto 就会强制交替”，但两端均符合既定局部证书，不能把未承诺的交替性作为新阈值。

## D1 · 三观察依赖税（非事件）

Case ID：`270c5807fb5e4a87ed06b37f568d9dd151ed47ab08afbef38eabec8d2011da3b`；cutoff：`2026-04-16T20:00:00Z`。
[图表](charts/D1.270c5807fb5e4a87ed06b37f568d9dd151ed47ab08afbef38eabec8d2011da3b.png) · [精确案例数据](cases/D1.270c5807fb5e4a87ed06b37f568d9dd151ed47ab08afbef38eabec8d2011da3b.json)

2025-04-22 中心的当前三观察可计算，但额外 j-2/日历边仍为 CALENDAR_UNKNOWN；raw 为 false/false。图中灰叉和缺少 A1 标记与原四观察域一致。这是覆盖成本，既不是被恢复的极值，也不能记作成功事件。

## D1 · 最长单位间隔交替链

Case ID：`3704289a60eb0e48b6b672e92cd2705f922c2ef6cce55bebced5c2baa20f6c98`；cutoff：`2026-04-16T20:00:00Z`。
[图表](charts/D1.3704289a60eb0e48b6b672e92cd2705f922c2ef6cce55bebced5c2baa20f6c98.png) · [精确案例数据](cases/D1.3704289a60eb0e48b6b672e92cd2705f922c2ef6cce55bebced5c2baa20f6c98.json)

2026-02-24/25/26 三中心依次 LOW 313.295909697、HIGH 334.677147484、LOW 306.799839317；后两者由 veto 行恢复。三角极值和下一根空心确认清楚分开。这是明显更密集的局部摆动，不能把三个事件称作三个独立样本或直接称作正式 Swing。严格 XOR 和反转尺度并未改变，未见不能归因于 veto 的新增。

## D1 · 首次新增

Case ID：`4e58c20ec138539a5ef04e647f3ccde8f12a882cababe89a36e3a1f162830047`；cutoff：`2026-04-16T20:00:00Z`。
[图表](charts/D1.4e58c20ec138539a5ef04e647f3ccde8f12a882cababe89a36e3a1f162830047.png) · [精确案例数据](cases/D1.4e58c20ec138539a5ef04e647f3ccde8f12a882cababe89a36e3a1f162830047.json)

2025-07-01 LOW 260.744988281 紧随 2025-06-30 HIGH 275.685020762，确认位于 07-02。它不是相对既有同类参考的 more-extreme，因此首次新增本身不能证明结构改善。图中的后续灰叉仍保留，没有放宽支持域。

## D1 · 恢复最大既定遗漏

Case ID：`7cc746b7c92a5428866fee6e879956a17de701b6e89b93ef148004ebeabb0565`；cutoff：`2026-04-16T20:00:00Z`。
[图表](charts/D1.7cc746b7c92a5428866fee6e879956a17de701b6e89b93ef148004ebeabb0565.png) · [精确案例数据](cases/D1.7cc746b7c92a5428866fee6e879956a17de701b6e89b93ef148004ebeabb0565.json)

2026-01-08 LOW 329.287003196，01-09 确认，低于既定 B0 同类参考 393.305854015（2025-12-09）。该参考在局部图外，在 frame 的 baseline_omission_reference 可精确追踪。图中 01-14 另一个新增 LOW 也保留，说明去掉 veto 既补回局部低点，也提高描述密度；未把密度增加本身视为成功。

## M30 · 最长单位间隔交替链

Case ID：`05d3bb5e13a5d4c2977d8dcf02f2fc6d5eab1af9a46566466dd18d4908d67fca`；cutoff：`2026-08-31T16:00:00Z`。
[图表](charts/M30.05d3bb5e13a5d4c2977d8dcf02f2fc6d5eab1af9a46566466dd18d4908d67fca.png) · [精确案例数据](cases/M30.05d3bb5e13a5d4c2977d8dcf02f2fc6d5eab1af9a46566466dd18d4908d67fca.json)

2026-08-13 17:00/17:30 两个 end 坐标依次为 LOW 420.49 与 HIGH 422.64，后一中心新增。两事件链是本周期最大值，不能夸大为持续交替。后面的共享 HIGH 422.15 同时保留，显示局部成对反转与全序列同类连续可以并存。

## M30 · 三观察依赖税（非事件）

Case ID：`755b3089a4fd679ac9a2fcc4886009258c15a70b0940f05b03ca1ce56e955315`；cutoff：`2026-08-31T16:00:00Z`。
[图表](charts/M30.755b3089a4fd679ac9a2fcc4886009258c15a70b0940f05b03ca1ce56e955315.png) · [精确案例数据](cases/M30.755b3089a4fd679ac9a2fcc4886009258c15a70b0940f05b03ca1ce56e955315.json)

2026-08-13 14:30 end 中心当前三观察在同一合格 session，quartet 仍跨越禁止的 segment 边；raw 为 false/false。图上 session 虚线和灰叉明确保留该失败。橙色上下文事件不属于这个诊断中心；该中心在两臂均无事件。

## M30 · 恢复最大既定遗漏

Case ID：`8870f83f7b518ef2088d469938a8bdeb3d71106904bc521071a783da128f37b7`；cutoff：`2026-08-31T16:00:00Z`。
[图表](charts/M30.8870f83f7b518ef2088d469938a8bdeb3d71106904bc521071a783da128f37b7.png) · [精确案例数据](cases/M30.8870f83f7b518ef2088d469938a8bdeb3d71106904bc521071a783da128f37b7.json)

2026-08-17 15:30 end 的 LOW 394.1，16:00 确认，低于原 B0 参考 LOW 420.49（08-13 17:00）。图内前一 HIGH 398.1587 导致原 veto。局部低点与确认可分辨，但原参考跨 session 且并非全局结构真值；这只支持预定遗漏比较。

## M30 · 新增同类对

Case ID：`a3a166ff160bfe54bc038e7792527dae8b304e210dc53c75015b91b0173910bd`；cutoff：`2026-08-31T16:00:00Z`。
[图表](charts/M30.a3a166ff160bfe54bc038e7792527dae8b304e210dc53c75015b91b0173910bd.png) · [精确案例数据](cases/M30.a3a166ff160bfe54bc038e7792527dae8b304e210dc53c75015b91b0173910bd.json)

08-13 新增 HIGH 422.64 与共享 HIGH 422.15，end 坐标 17:30/19:00，间隔 3，构成真实新增 HIGH/HIGH。两个局部峰位于重叠的价格区域，属于必须披露的冗余代价；它们都有完整证书，且本轮冻结规则没有最小间隔或峰合并承诺，不能事后添加这些规则。

## M30 · 首次新增

Case ID：`f48912e4828773c2cae20f67cddd8b107258e674fcd193dcb84ef80315091d35`；cutoff：`2026-08-31T16:00:00Z`。
[图表](charts/M30.f48912e4828773c2cae20f67cddd8b107258e674fcd193dcb84ef80315091d35.png) · [精确案例数据](cases/M30.f48912e4828773c2cae20f67cddd8b107258e674fcd193dcb84ef80315091d35.json)

同一 08-13 HIGH 422.64 的首次新增焦点，与链/同类对案例有重叠，但焦点边界不同，按冻结规则不合并。此前没有可用 B0 同类 omission reference，因此本次新增不被算作 restored-more-extreme。没有为增加独立案例数而重选其他时点。

## W1 · 最长单位间隔交替链

Case ID：`126a6d0770a0aa3ff3dfd03dde00fa3bac6e1455cd483560a9e9ed34e75c88ba`；cutoff：`2024-11-15T21:00:00Z`。
[图表](charts/W1.126a6d0770a0aa3ff3dfd03dde00fa3bac6e1455cd483560a9e9ed34e75c88ba.png) · [精确案例数据](cases/W1.126a6d0770a0aa3ff3dfd03dde00fa3bac6e1455cd483560a9e9ed34e75c88ba.json)

两个周观察 LOW 164.83057898 / HIGH 182.231441273 相邻，后一 HIGH 由 veto 恢复；图中最后一个空心方块表示在 cutoff 当时已完成的下一周确认。前面的 LOW/LOW 仍在图内，说明该两事件链没有消除全局重复同类。

## W1 · 三观察依赖税（非事件）

Case ID：`2f10656e4ac8603141e163f04b2795add10398e84a2bea300f4dbe96d6c7d4d3`；cutoff：`2024-10-11T20:00:00Z`。
[图表](charts/W1.2f10656e4ac8603141e163f04b2795add10398e84a2bea300f4dbe96d6c7d4d3.png) · [精确案例数据](cases/W1.2f10656e4ac8603141e163f04b2795add10398e84a2bea300f4dbe96d6c7d4d3.json)

2022-12-12 end 中心三观察可计算、raw false/false，但额外 j-2 的 CALENDAR_UNKNOWN 使 quartet 不合格。大片灰叉清楚显示既有周历证据不足，A1 没有把它们变成事件。价格看起来连续不能替代日历证书。

## W1 · 首次新增＋恢复最大既定遗漏

Case ID：`8c439c0b149ff513142d183e4b53b2b57da0f88c84185d5c4bcdd802942c103e`；cutoff：`2024-11-15T21:00:00Z`。
[图表](charts/W1.8c439c0b149ff513142d183e4b53b2b57da0f88c84185d5c4bcdd802942c103e.png) · [精确案例数据](cases/W1.8c439c0b149ff513142d183e4b53b2b57da0f88c84185d5c4bcdd802942c103e.json)

HIGH 182.231441273 的 end 为 2024-11-11T05:00:00Z，11-15T21:00:00Z 确认；既定 B0 同类参考为 89.797048056（2023-10-16 end），参考留在完整 frame。该较大的遗漏差距受 B0 稀疏历史参考影响，不是新规则发现了同等跨度的正式结构。两个类别焦点相同，已按冻结规则合并为一图。

## W1 · 新增同类对

Case ID：`fda26c6dedfeee6cd8872e195bf23895ce4ac810f2841ddb39d486e105b6aa12`；cutoff：`2025-08-22T20:00:00Z`。
[图表](charts/W1.fda26c6dedfeee6cd8872e195bf23895ce4ac810f2841ddb39d486e105b6aa12.png) · [精确案例数据](cases/W1.fda26c6dedfeee6cd8872e195bf23895ce4ac810f2841ddb39d486e105b6aa12.json)

新增 HIGH 182.231441273 与共享 HIGH 315.041649732 的 end 为 2024-11-11/2025-08-18，间隔 40 个观察。中间大量灰叉说明日历证书覆盖不足；该长间隔和 HIGH/HIGH 是不利证据，不能称作稳定、完整的市场 Swing。它没有破坏局部证书，且缺失支持在 B0 已存在，因此不足以把单一 veto 消融判成明确的新结构规则失败；跨样本及合法历史可用性验证仍必要。

## 完整案例判读结论

本次局部证书语义下，未发现无法映射到原 veto、越过质量/日历域或发生同支持不稳定的新增事件。新增同类对、D1 三事件密集链、W1 长间隔与非最小 quartet 覆盖代价均已披露。它们不支持产品采用或正式 Swing 定义；本轮也没有新增数值过滤规则来消除它们。

结合冻结决定表：三个周期均有去重的 restored-more-extreme，所有周期同类对比例不升，硬性完整性通过，没有需要覆盖量化结果的明确新结构失败。唯一研究 disposition 为 **RECOMMEND_CROSS_SAMPLE_ONLY**。这仅建议以后另行授权的独立股票验证，不执行后续任务；严格历史确认与广泛市场适用性保持 **INCOMPLETE**。
