# R05 证据入口

本目录只包含独立离线研究。产品、R04 和历史证据未修改；不接入行情服务、账户或用户数据库。

- [中文报告](REPORT.md)：结论、候选对照、验证与限制。
- [冻结计划](PLAN.md)、[数学规格](../../../research/PAQS_Q_PRIOR_RAW_VETO_ABLATION_R05.md)、
  [冻结清单](freeze.json)、[GitHub 冻结读回](freeze-readback.json)。
- [B0 复现对账](baseline-reproduction.json)：21 文件逐字段比较，列出每个获准忽略的运行元数据路径。
- [A/B 汇总](ablation-results.json)、[端点差集](endpoint-delta.json)、
  [依赖税诊断](dependency-audit.json)、[有限枚举](proof-and-enumeration.json)。
- [全部案例判读](case-review.md)、[图表清单](charts/manifest.json)。
- [验证记录](validation.json)；逐文件保护检查见 `protection.json`。

`baseline-study/` 是本轮独立生成的 B0 全量结果；原 study-03 保持原样。
`frames/` 六个 JSON 保存每个 mode/cutoff 的两臂结果、成本、差集、依赖诊断和滚动对照。
`census_ids` 按原始顺序引用 `census_catalog`，数组下标恢复 index，
`index >= active_start` 恢复 active（空数组无 active）；`calendar_view_id` 引用完整 calendar_catalog。
事件仍逐 cutoff 保存；price_refs 指向冻结外部输入的精确原始版本。
支持缺失、被拒绝的中心和失败的 cutoff pair 没有从汇总中隐去。
`cases/` 保存所选截止时点内的精确 Decimal K 线及两臂完整上下文，PNG 仅用于展示。

## 复现条件与命令

需要现有 Python 环境、冻结的三个规范化 AVGO 文件及捕获日历；文件未随本轮重新导出。
路径与 SHA256 见 freeze.json、ablation-results.json。禁止用其他输入替代，禁止访问用户数据库。
Windows 验证环境为 Python 3.12.14；命令执行时 PYTHONPATH/MYPYPATH 包含仓库根与 src。
绘图复用单独的现有 R04 matplotlib 环境，未增加项目依赖。

以下是本轮实际研究命令（在仓库根执行）。输出采用独占新路径；已有结果不能被覆盖。
如独立审查需要重新运行，须将 --output 改为新的目录名，不得复用本目录中的已生成结果。

```text
python -m tools.research.paqs_q.r05.study --data-dir D:/AI_Infra_Quant_Codex_v1/task006b-q-data --calendar D:/AI_Infra_Quant_Codex_v1/task006b-q-r04-source/capture-calendar.json --output docs/evidence/TASK_006B_Q/research-05 --freeze-sha b10e87cbb324442d1fc744d5fa94522802f870c1 --receipt docs/evidence/TASK_006B_Q/research-05/freeze-readback.json
python -m tools.research.paqs_q.r05.charts --cases docs/evidence/TASK_006B_Q/research-05/cases --output docs/evidence/TASK_006B_Q/research-05/charts
python -m pytest tests/research/paqs_q tests/unit/test_paqs_input.py -ra
python -m ruff check tools/research/paqs_q/r05 tests/research/paqs_q/r05
python -m ruff format --check tools/research/paqs_q/r05 tests/research/paqs_q/r05
python -m mypy --strict --explicit-package-bases tools/research/paqs_q/r05 tests/research/paqs_q/r05
python -m mypy --strict --explicit-package-bases --platform win32 tools/research/paqs_q/r05 tests/research/paqs_q/r05
git diff --check
python -m tools.research.paqs_q.r05.protect --freeze-sha b10e87cbb324442d1fc744d5fa94522802f870c1
```

绘图使用 Agg 后端和临时缓存。实际 Python 路径、版本、退出码、计数及网络推送限制见 validation.json。
硬性不变量失败必须保留失败输出并停止；不能看到真实结果后修改冻结计算代码再重跑。
