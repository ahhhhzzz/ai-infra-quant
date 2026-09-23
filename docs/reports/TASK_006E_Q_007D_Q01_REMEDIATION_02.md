# TASK-006E-Q / TASK-007D — Q01 增量整改：多候选 Stage B 目标

状态：**本地整改并验证通过 / 等待 Q01 聚焦复核 / 未整合产品分支**。起点为任务分支 `0a3f132541296249094a04b88b609fd2130f9bee`；`roadmap/no-live-trading` 保持 `971c64a86998b2140e2549a1dd44e1f716e30e9e`。本报告只记录第一轮 [Q01 整改](TASK_006E_Q_007D_Q01_REMEDIATION.md) 后发现的剩余边界；[原实现报告](TASK_006E_Q_007D_IMPLEMENTATION_REPORT.md)、Holder 1.0.0/1.0.1 历史身份及其原执行记录均不改写。

## 发现与修复

用户提供的外部 Linux Python 3.12.14 独立复核确认：原始 OHLC 前缀用例及 22 项相关项目测试通过，三个上游 manifest、51 个覆盖文件和原实现报告不变；新增合成 Holder 边界用例失败，故 **Q01 尚未关闭**。这些不是本轮 Windows 本地执行。

本地先以 `demo_bundle()` 的真实 Setup 输出，取同一 Setup 最早两名候选各自的 Stage A 和 `LONG_READY` Stage B。原四个 T1 均为 115.2。仅把第二候选 Stage B 改为 115.1，同步更新上下界、RR（约 3.06344，仍大于 2）及 canonical `fact_key`，重新校验 `SetupFact`；这是**合成事实边界**，不是原始行情自然产生的信号。修复前新回归为 **1 failed、1 passed**：Holder 错报 `THESIS_VALID`，仍绑定第一候选 115.2。

Holder 独立身份升至 `paqs-q-conditional-holder@1.0.2`；规范化源码 SHA256 为 `da0ff98ae26a794a909e8f851cc11a96a0d4bf64fbc02b55f281563d77acf02a`。现在逐候选解析最早有效 Stage A、该候选合格 Stage B 及生效时间，再比较每名候选的最终有效目标。`NO_TRADE` 不替换目标；重复相同目标不重置绑定时间；合法 Stage B 新目标只从自身绑定时刻生效。不同候选有效目标冲突时返回 `UNDETERMINED`、无唯一 `target_binding`，原因是 `MULTIPLE_CANDIDATE_TARGETS_AMBIGUOUS`；目标一致的正例保留最早候选原绑定。硬失效优先、绑定后的完整常规 M30 触价与负向覆盖区间、Entry/Holder 分离均未改。

## 本地 Windows 验证

环境：Windows 11（10.0.26200）、Python 3.12.14、pytest 8.4.1；在整改后源码运行：

| 检查 | 实际结果 |
| --- | --- |
| `tests/unit/test_paqs_q_holder_q01.py`，含原 OHLC 前缀、绑定后触价、跨界 bar、重复目标及新冲突/不冲突回归 | `7 passed` |
| 同一 Q01 文件、Q 输入/分析/快照身份、Q 存储与 Q/E API、架构导入边界聚焦切片 | `27 passed`，1 条 Starlette 弃用提示 |
| `ruff check src tests`、`ruff format --check src tests`、`mypy --strict --follow-imports=silent src/ai_infra_quant/application/paqs_q_holder.py` | 均通过 |
| Context、Event、Setup/Risk 上游 manifest | 分别为 `510ece60c2765bb502a331b31cecf0fd1eab32f313624c2f9926d8ccfc2eedfc`、`67fe4a16e0bfffbed46d53d892e320af466592fffb1ec27df44732db38568cbc`、`849d50f23af1ca572adcbc7a972c61eff6bc61c7cefb6c9cb22c298260d2dac1`，校验通过 |

聚焦切片命令：

```powershell
$env:PYTHONPATH='src;.;tests;tests/unit;tests/integration'
& D:\AI_Infra_Quant_Codex_v1\task007c1-env\Scripts\pytest.exe -q tests/unit/test_paqs_q_holder_q01.py tests/unit/test_paqs_q_product_analysis.py tests/unit/test_paqs_q_product_input.py tests/unit/test_paqs_q_analysis_snapshot_identity.py tests/integration/test_paqs_q_analysis.py tests/integration/test_paqs_q_product_api.py tests/integration/test_paqs_q_e_frozen_api.py tests/architecture/test_import_boundaries.py
```

本轮未重跑 AVGO、付费模型、OpenD 或无关全量测试。原 AVGO `INSUFFICIENT` 和真实服务未验证限制不变。F1、Event 1.0.1、Setup/Risk 1.0.1、上游 manifest、参数、原历史报告和产品分支均未修改；下一步只等待 Q01 剩余边界的独立聚焦复核，不宣称复核 PASS 或整合。
