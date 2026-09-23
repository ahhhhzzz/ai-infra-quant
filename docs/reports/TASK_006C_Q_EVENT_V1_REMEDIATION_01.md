# TASK-006C-Q Event v1.0.1 聚焦整改记录

状态：**E01/E02 已整改并完成本地 Windows 验证；等待独立聚焦复核；未整合产品分支**。
本轮从任务分支固定提交 `7138c110ec8a6e0877799c9a7a8a040ea69237dd` 开始。
测试在该提交之上的整改工作树执行；本报告随同源码、测试及新 manifest 一起提交。

| 项目 | 整改与证据 |
|---|---|
| E01，严格 AS_OF 的中间 CLOSED 事实 | D1/M30 连续性证明逐日核查使用到的日历事实：最迟必须在下一根依赖该事实的 bar **完成时**可知；晚到返回 `INSUFFICIENT / HISTORICAL_CALENDAR_NOT_KNOWN_AT_COMPLETION`，Event 上游不可用。周末、工作日假日及 M30 午休合法输入通过；W1 原完成时间路径不变。OBSERVATIONAL 仍声明历史可知性未认证。 |
| E02，趋势失效滞后一根 | 每根先取上一帧已知 Major/Range 处理失效、突破、Transition；在该根收盘后，用当前完成价格重评**同一份先前已知结构**的输出 regime。当前根新确认的结构不用于开始前决策。Transition 的两根确认、失效优先、原 Range 恢复路径保留。多空镜像的真实 OHLC 复现从错误的 BULL/BEAR_TREND 改为 UNCERTAIN。 |
| 新身份 | Context/Event 均为 `1.0.1`。新增 `event-context-1.0.1.json` 与 `event-event-1.0.1.json`，每份覆盖 45 个项目文件，包括保留的两个 Event 1.0.0 manifest。新 series/event_key 加入版本域。Context code hash `510ece60c2765bb502a331b31cecf0fd1eab32f313624c2f9926d8ccfc2eedfc`；Event code hash `67fe4a16e0bfffbed46d53d892e320af466592fffb1ec27df44732db38568cbc`。当前 loader 只注册 1.0.1；1.0.0 固定提交与原 manifest 留存。B0/A1 manifest、F1 默认选择均未改。 |

## 本轮实际执行：Windows

环境：Windows 11 `10.0.26200`，Python 3.12.14，pytest 8.4.1，Pydantic 2.11.7，
tzdata 2025.2，Ruff 0.12.9，mypy 1.17.1，Playwright 1.55.0；使用已存在的本地
Chromium 缓存。解释器为 `D:/AI_Infra_Quant_Codex_v1/task007c1-env/Scripts/python.exe`。

整改前在 `7138c110...` 实现上先添加回归用例，定向运行 E01 D1/M30 和 E02 多空镜像：
**4 failed，退出码 1**，与外部审查描述一致。整改后：

| 命令/检查 | 实际结果 |
|---|---|
| `python -m pytest tests/paqs_q_event tests/paqs_q tests/architecture/test_import_boundaries.py tests/architecture/test_task007b_boundaries.py tests/architecture/test_task006b_boundaries.py -q` | **190 passed**，退出码 0：Event 84、F1 91、架构 15；1 个 Starlette/AnyIO 依赖弃用警告。真实 OHLC Transition 两条路径、多空失效及前缀追加不改旧事实均在 Event 范围内。设置 `PYTHONPATH=src;.`、`MYPYPATH=src`、`PLAYWRIGHT_BROWSERS_PATH=D:/AI_Infra_Quant_Codex_v1/playwright-browsers`。 |
| `python -m ruff check` 本轮所改 Python 文件及 Event 测试；`python -m ruff format --check` 同范围 | 均退出码 0；13 个文件格式合格。 |
| `python -m mypy` 本轮 5 个实现/验证 Python 文件 | 0 issues，退出码 0。 |
| 后加等号边界、合法假日及旧版本拒绝断言后，定向 `pytest` 复查 | **6 passed**，退出码 0；所改 3 个测试文件 Ruff check/format 仍通过。源码和 manifest 未再变化，故不重复整套 190 项。 |
| `verify(root, "context")`、`verify(root, "event")` | 两份新 manifest 与当前源码相符；上表记录其 code hash。 |
| `git diff --check`、文档相对链接及旧清单 blob 对照 | 提交前核对通过；B0/A1 及 Event 1.0.0 清单未修改。 |

第一次单独运行 Event 测试时浏览器用例因本次 PowerShell 会话未设置已有缓存路径，
Playwright 在默认目录找不到 Chromium：当次为 **83 passed / 1 failed**，属于启动环境。
设置上述 `PLAYWRIGHT_BROWSERS_PATH` 后单独重跑浏览器用例 **1 passed**；最终组合
验证亦包含该浏览器用例并 **190 passed**。保留这些原始执行结果，不改写为首次全过。

用户提供的**外部 Linux 审查**在原 SHA `7138c110...` 执行 Event 非浏览器 77 项及 F1
47 项均通过，并对 E01/E02 各给出两个独立复现；这不是本轮本地 Windows 执行，亦不表示
外部审查已复核本次 1.0.1 整改。

本轮未重新运行 AVGO 行情，也未覆盖原 Event 1.0.0 的样本输出或
[实现报告](TASK_006C_Q_EVENT_V1_IMPLEMENTATION_REPORT.md)。无调参、收益验证、
Setup/Risk、产品接入或产品分支合并。仍须由独立审查判断整改是否通过。
