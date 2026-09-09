# TASK-006B-Q F01/F02 focused remediation report

状态：**整改实现完成，等待独立聚焦复核。真实行情门槛 INCOMPLETE；结构鲁棒性/语义采纳未通过。**

## 1. Authority and exact commits

| Object | SHA |
|---|---|
| Remediation start / original task branch | `a29d2d6e0195ed4509cfa8daa9223a41c3d6fcf0` |
| Authoritative base | `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f` |
| Independent review | `e4bf4cb6092e48c98732bd7d355d31affbf8a332` |
| Additive remediation contract | `04a5a688b6785cafa13dfae4c3844bf31bf727ce` (parent is exact start above) |
| Core F01/F02 implementation | `cfa0dd13579c2e934b866681ba6aebb0d5d8b51f` |
| Final executable source and tests | `9de7381d7440215e729fbf67103eb2ac55f44181` |

Fetch/ls-remote confirmed exact task, authority and review references. Review is a direct child of
the start and adds only the report/reproducer; it was read at that exact commit without merging.
Task/authority merge base is the authority SHA. The existing isolated worktree was clean and remains
on `task/006b-q-structure-formalization`; no unknown commits were overwritten.

AGENTS, original contract, current governance and exact review evidence were read. Governance bytes
were checked against the already-read unchanged authority. The historical Phase 1 plan remains
historical, not a restarted phase. [CONTRACT.md](CONTRACT.md) was written before implementation.
The original report's network blockage is preserved as history: this remediation's initial fetch
confirmed that a29d2d6 had subsequently reached GitHub, as the independent review also records.

The final delivery commit includes this report/evidence and descends from the executable source
above. Its exact SHA is returned after normal task-branch push and GitHub readback, avoiding a
self-referential commit hash inside this report. No review or authority merge is authorized.

## 2. F01 — quality cannot become clean evidence by omission

根因：D1 `coverage` 没有枚举校验，也没有与整体质量核对；W1/M30 在版本选择前过滤 coverage，
还可能让新的 PARTIAL 版本被忽略后重新使用旧 COMPLETE 版本。

修复：`engine.quality_error` 定义逐条合法值 COMPLETE/PARTIAL/UNKNOWN；INVALID、未知字符串、空值和其他类型
均不能进入有界计算。整体质量允许比逐条质量保守，但不能更确定，采用 COMPLETE < PARTIAL < UNKNOWN：

| Aggregate / used bar | Result |
|---|---|
| COMPLETE / PARTIAL or UNKNOWN | INVALID / UNCERTAIN |
| PARTIAL / UNKNOWN | INVALID / UNCERTAIN |
| PARTIAL / COMPLETE or PARTIAL | 保留 PARTIAL |
| UNKNOWN / any legal bar quality | 保留 UNKNOWN |
| Any / invalid bar coverage | INVALID / UNCERTAIN |

合法 D1 PARTIAL/UNKNOWN 的计算不变成 clean-market 认证。整体 INVALID 继续失败。
W1/M30 先按 cutoff 选择最新可用版本，再排除合法且整体一致的非 COMPLETE 桶；坏质量或矛盾质量不能靠过滤消失。
正常 N 窗口外的历史仍不参与当前计算；未来、不可用、未完成的记录仍先隔离。
JSON 路径保留源标志，使用同一公开 evaluator 验证，没有批量把 fixture 或行情改成 COMPLETE。

审查相同反例的前后结果：

| Same input | Before a29d2d6 | Corrected |
|---|---|---|
| Bull fixture with INVALID D1 coverage | COMPLETE / BULL_TREND | INVALID / UNCERTAIN |
| Failure reason | none | BAR_COVERAGE_INVALID |

新增 35 个质量回归覆盖 D1/W1/M30 的非法枚举/类型、整体矛盾、合法 PARTIAL/UNKNOWN、公开 evaluate、
JSON round trip 和实际 CLI，以及未来/不可用/未完成坏质量隔离和派生行情版本选择。
详见 [quality tests](../../../../tests/research/paqs_q/test_remediation_quality.py)。

## 3. F02 — reconstruct each information set from raw versions

根因：boundary 将新 cutoff 已经扁平化的版本集合替代原始 dataset，并在旧 cutoff 下直接算 OLD/LEFT。
这样以后才可用的修订进入旧时点，原 `future_references` 只检查当前 Pivot 完成时间，未发现越界。

修复后的四臂规则已冻结在候选规格的
[Boundary clarification 1.2](../../../research/PAQS_Q_STRUCTURE_MATH_CANDIDATE_V1.md#14-boundary-clarification-12--f01f02-remediation)：

| Arm | Version choice / calculation | Information cutoff |
|---|---|---|
| OLD | 原始版本数据上独立 public evaluate，正常 N | old |
| LEFT | OLD 已选 N 移除首条，原 warm 索引 W | old |
| RIGHT | 原始数据按 new 选版本，从 OLD 左端至新终点；须 N+1 | new |
| BOTH | 原始版本数据上独立 public evaluate，正常 N | new |

传入的 N+1 只标识转移，必须与原始数据在新 cutoff 的选择一致；不会替代原始版本集合。
OLD/BOTH 返回的 decision hash 与对应独立 evaluate 相同。低层 calculate_window 也拒绝完成时间或
已知 available_at 越过自身 cutoff 的输入；AS_OF 不接受未知可用时间。

实验范围内的历史内容/可用时间修订、新到达的历史 key 或消失的 key 分别计数；任何变化强制
`REVISION_CONFOUNDED`，即使几何没有变化，也不叫 LEFT_ONLY。缺失旧版本保持缺失，不从后来数据重建。
OLD 缺少正常 N，或 RIGHT 因延迟到达出现非 N+1 时，明确给出不可用对照窗口，不偷偷调整策略窗口。

每个 CURRENT/OLD/RIGHT/LEFT/BOTH 对所有行情输入做完成时间与可用时间审计，包括 ATR warm-up 输入。
记录各自 cutoff、数量、违规计数、未知时间计数和有序时间证据哈希。OBSERVATIONAL 的 null 可用时间标为
OBSERVATIONAL_UNKNOWN，不能用零违规宣称严格历史 As-Of 通过。
汇总层另列 `revision_confounded_cutoffs`；`material_left_only` 仅取真实 LEFT_ONLY 且 material 的案例，
不能再把通用 review_required 当成纯左边界原因。

审查相同修订反例（index 290 的 High=9999，available_at 为 new cutoff）：

| Check | Before | Corrected |
|---|---|---|
| Independent OLD pivot count | 21 | 21 |
| Boundary OLD pivot count | 19 | 21 |
| Boundary OLD == independent OLD | false | true (decision hash also equal) |
| Classification | LEFT_ONLY | REVISION_CONFOUNDED |
| `future_references` | 0, current Pivot-only | 0, all actual arm inputs checked |

新零值因为非法版本已经不再进入 OLD/LEFT，而非删掉检查。检查口径变化在新证据明确记录，原证据不改。
[Same-input reproducer comparison](reproducer-before-after.json) 记录旧脚本实际执行和修复后结果。
审查脚本没有修改，也没有把它断言旧缺陷的条件作为新验收预期。
新增 10 个 [temporal tests](../../../../tests/research/paqs_q/test_remediation_temporal.py) 覆盖修订、同价但
晚可用的新版本、延迟到达、缺失旧版本、普通无修订、未来坏 payload、观察模式及所有 warm 输入的时间检查。

## 4. Same AVGO observations — before/after

使用原先在工作区外保留的三份规范化 AVGO 文件，SHA256 与原 coverage manifest 一致，没有扩大股票样本、
调用 OpenD、获取新行情或修改数据库。所有重算输出写入本目录的 `corrected-study/`。
核心修复下重跑完整 study；随后用最终 `boundary_case_lists` 对已保存 outliers 生成最终汇总字段，
没有改动计算结果。流程和来源在 [real-before-after.json](real-before-after.json) 明确记录。

| Timeframe | Valid cutoffs | Decision/status/hash/classification differences | Material four-arm differences | Checked input uses |
|---|---:|---:|---:|---:|
| W1 | 100 | 0 | 0 | 65000 |
| D1 | 100 | 0 | 0 | 156000 |
| M30 | 74 | 0 | 0 | 73200 |

共 274 个有效终点、1366 个 CURRENT/arm 集合、294200 次行情使用（重复使用计次，不是独立行情数量）。
完成/已知可用时间越界计数为 0；294200 次使用的历史可用时间均 UNKNOWN，因此不能宣称严格历史信息集认证。
原有 27 个 material boundary 案例、12 个 material LEFT_ONLY 案例保持相同，不因本整改而宣告已解决。
该单 Capture 没有历史版本流，所以 F02 的行为变化主要由新增的版本反例验证；真实输入未受此反例污染。

股票分母仍为 40（24 US / 16 HK），只有 AVGO。W1/D1 各 100 个有效终点；M30 只有 74，仍缺 26 根
才能达到 100 个有效终点。其余 39 只 unavailable。**真实行情门槛继续 INCOMPLETE**。
原 D1 96/100 UNCERTAIN、左端重播敏感性、W1 参数分歧及无真实 RANGE 的辨识力限制全部保留。
没有重新定义 ATR、Pivot、Zone、Range 或 Regime 来提高表面通过率。

## 5. Validation

Environment: Windows / Python 3.12.14, pytest 8.4.1, Ruff 0.12.9, mypy 1.17.1.
Existing declared dependency environment; `PYTHONPATH=<repo>/src;<repo>`, `MYPYPATH=<repo>/src`.

| Command | Actual result |
|---|---|
| `python -m pytest tests/research/paqs_q -ra` | **97 passed, 1 warning in 19.79s** |
| Same six existing regression files (below) | **59 passed, 1 warning in 14.53s** |
| `python -m ruff check tools/research/paqs_q tests/research/paqs_q` | All checks passed |
| `python -m ruff format --check tools/research/paqs_q tests/research/paqs_q` | 20 files already formatted |
| `python -m mypy --strict --explicit-package-bases tools/research/paqs_q tests/research/paqs_q` | Success, 20 source files |
| Same mypy command with `--platform win32` | Success, 20 source files |
| `git diff --check` | No errors |
| Existing task verifier + exact start protected identity checks | PASS; evidence below |

```text
python -m pytest tests/unit/test_paqs_structure.py tests/unit/test_paqs_input.py tests/integration/test_paqs_structure_api.py tests/integration/test_paqs_input_api.py tests/architecture/test_task006a_boundaries.py tests/architecture/test_task006b_boundaries.py -ra
```

原 52 个研究测试完整保留，新增 45 个；无 skip/xfail、删断言或更改 fixture 标志来绕过问题。
唯一 warning 是既有 Starlette 的 `anyio.abc.BlockingPortal` alias 弃用。
没有改生产运行路径；无关浏览器/全业务/Uvicorn 按原研究合同不要求，未冒称运行。
[validation.json](validation.json) 和 [README](README.md) 提供完整命令与新证据入口。

## 6. Preservation and changed files

相对整改起点，408 个受保护文件的 Git mode/type/blob 相同；仅允许的四个既有文件发生变化：
`engine.py`、`diagnostics.py`、`study.py`、候选规格。权威基线的 377 个文件仍相同。
ATR/Pivot/labels/Regime 函数 AST 单独比对相同；`zones.py`、`types.py`、fixtures、冻结 profile/universe
及全部原始证据保持原 Git blob。工作树 diff 同时检查未暂存修改；详见 [protection.json](protection.json)。

新增研究文件：`tools/research/paqs_q/temporal.py`；新增两份专用测试。候选规格仅追加质量与诊断版本澄清，
计算 rule ID 和参数未改。本目录新增 CONTRACT、REPORT、README、规则矩阵、复现前后比较、真实输入比较、
validation/protection 和 corrected-study。全部处于本轮授权允许清单。

原合同、原实现报告、原诊断、原冻结文件、独立审查提交/脚本、src、已有业务测试、配置、依赖、迁移 0001–0004、
PAQS-E/Narrative/Legacy 均未修改。review 提交不是本任务 HEAD 的祖先，未合并 review。
其他 worktree 和未跟踪文件保留。

数据库 SHA256 仍为 `81b32a5f0f74e5549e99414456f189d5111435e3601b00bcd3e43c41ee2f1034`；
`phase1_remediation_commit.txt` 仍为 `c791ba73b41c4e7719957607e025105a8110fa54a2e1a67f3c5b142da8030440`。
本轮实际研究读取已有规范化文件；数据库只作只读哈希核验，没有写入或重新采集。

## 7. Stop condition

F01/F02 的修复与回归已交付，**等待独立聚焦复核**，不是自行宣告审查通过。
真实行情门槛 INCOMPLETE；已知结构鲁棒性和语义问题仍未采纳；预测/交易表现未评估。
仅正常推送原任务分支并读回，不强推、不合并、不接入产品、不启动 006C-Q。
