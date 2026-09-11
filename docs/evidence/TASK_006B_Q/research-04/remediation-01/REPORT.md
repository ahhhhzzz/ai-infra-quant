# TASK-006B-Q R04-F01 聚焦整改报告

状态：**整改实现与验证完成，等待独立聚焦复核。** 本报告不宣告 F01 独立关闭。
本轮只纠正 segment 聚合；原研究建议、严格历史确认和广泛市场适用性
`INCOMPLETE` 均不变。未启动 no-veto 实验、产品接入或 006C-Q。

## 1. 起点与血缘

| 对象 | 精确 SHA |
|---|---|
| 受审 R04 实现 | `30fa67bcf4521600030ce76bf953fdff87d2e668` |
| 本轮合同／修改前精确 HEAD | `0215d687b0ece28dee4b7854226b3e8916420518` |
| 独立审查 | `4906985744512092fc098340f43e8eec1f41c494` |
| 最终修复代码与回归测试实现提交 | `151f0fb285f35b35ddbc5840f0920e65c5c17bf6` |
| 冻结计划／规格／输入清单 | `ce53cc86f358590b1778ebd486f91efcb6adc62a` |
| 产品权威 | `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f` |

本报告和 study-03 为实现提交后的追加交付证据。包含这些文档的最终交付提交 SHA
在正常推送后从 GitHub 读回并在交付回复给出；它与上表的代码实现 SHA 分开记录，
不把尚未形成的自引用提交哈希写入本报告。

已 fetch，并从 GitHub 精确读取
[整改合同](../../../../../prompts/tasks/TASK-006B-Q_R04_F01_SEGMENT_COVERAGE_REMEDIATION.md)
及 [独立审查](https://github.com/ahhhhzzz/ai-infra-quant/blob/4906985744512092fc098340f43e8eec1f41c494/docs/reviews/TASK_006B_Q_R04_INDEPENDENT_REVIEW.md)。
合同直接父提交为受审 R04；任务／权威 merge-base 等于上表权威 SHA。
修改前任务远程 HEAD 精确为合同 SHA，review 与 authority 远程也分别等于指定值。
已完整阅读 AGENTS、ROADMAP、MASTER_SPEC、ARCHITECTURE、STRATEGY_SPEC、阶段计划，
以及原 R04 合同、冻结规格／计划、最终 R04 报告和精确审查记录。

沿用干净隔离的 `task006b-q-r04-worktree`，只检出原 R04 任务分支。开工时该工作区位于
受审实现，正常快进到合同后才修改。没有合并或复制 review 提交，没有重置或强推。
其他 worktree、未跟踪文件及 `phase1_remediation_commit.txt` 未被本轮操作改写。

## 2. 根因与最小修复

旧 `costs()` 枚举 segment 时使用 `str(None)`，计数时却比较原始 `None` 和字符串。
因此 unresolved W1 活动中心没有进入任何计数，输出虚假的 `"None": {"centers": 0, ...}`。

只在 `study.py` 内新增类型明确的 `_segment_key(str | None) -> str`：仅当值
`is None` 时返回 `UNRESOLVED_SEGMENT`，其他 segment 原样保留。
枚举和 centers/support/events 比较共同调用它，不用 truthiness，不事后改写输出。
原始 census 的 null、reason、active、raw、support_hash 以及事件均不被修改；
Decimal 计算、canonical 序列化、模型和支持身份都未改变。

新增 9 项回归，保留原 225 项及原断言：一个公开 evaluate 的合成 W1 未知周用例、
六组冻结 census 解码核验、两个无效／不足输入用例。合成 W1 有一个 unresolved 中心
和一个已接受事件，核验统计后整个 evaluate 结果仍完全相同。
六组回归覆盖原 600 个 mode/cutoff，并校验 D1/M30 原分段数据。

先在未修改的旧聚合代码上执行针对性测试：`2 failed, 5 passed, 9 deselected`。
失败分别是合成 W1 仍出现 `"None"`，以及冻结 W1 首 cutoff 的 segment 合计
`84 != 104`。这两项实际暴露旧缺陷；修复后全量执行没有 deselection、skip 或 xfail。

## 3. 冻结输入与 study-03 对照

使用原外部 AVGO W1/D1/M30 文件及 `capture-calendar.json`，由未修改的 loader 校验
原冻结哈希。`source-calendar-manifest.json` 与 study-02 字节相同，输入、日历及 cutoff
清单没有变化。本轮没有打开用户数据库，没有行情采集，也没有 OpenD 历史请求。

| W1 OBSERVATIONAL，100 个重叠 cutoff 累计 | 旧逐 cutoff 聚合 | 修正后 |
|---|---:|---:|
| 活动中心 | 10,400 | 10,400 |
| resolved segment 中心 | 8,479 | 8,479 |
| unresolved segment 中心 | 错误记录为 0 | 1,921 |
| segment 中心合计 | 8,479 | 10,400 |
| 完整支持中心 | 4,292 | 4,292 |
| 事件出现次数 | 805 | 805 |

100 个 W1 VALID cutoff 全部含 `UNRESOLVED_SEGMENT`，无 `"None"` 键；每个 unresolved
计数均从该 cutoff 的 census 独立解码得到。完整计数序列保存在 [DELTA.json](DELTA.json)。
新 unresolved 桶的 support/events 均仍为 0，没有把未知日历升级为有效见证。
这些累计值来自重叠窗口，不是独立事件样本数。

全部 **274 个 VALID cutoff**（W1 100、D1 100、M30 74）满足三项守恒：

```text
sum(segments[*].centers) = active_centers
sum(segments[*].support) = complete_support_active
sum(segments[*].events) = events
```

其余 326 个不足结果（300 个 AS_OF、26 个 M30 OBSERVATIONAL）保留空 segment map，
没有新增覆盖。AS_OF 三份文件、coverage、source-calendar-manifest 及 12 份案例 JSON
与 study-02 字节相同。

[reconcile.py](reconcile.py) 不调用修正后的 `costs()` 作为 oracle：从目录解码 census，
分别计数 active/support/event，再核对新聚合。随后对全部 21 个文件逐字段比较，
仅允许 100 处分段映射修正，以及实际运行的 started_at、finished_at、runtime_seconds、
serialized byte-size、逐事件 recognized_at 和 audit checked_at。
每一个忽略路径都列在 DELTA，未忽略 scheduled cutoff、first_seen_scheduled_cutoff、
reversal、available_at 或任何策略指标。其他字段有差异即失败。

实际结果：**其他语义差异 0**。所有 event catalog、census、支持哈希、端点／完整支持
transition、loss/rediscovery、status/reason、veto/omission、baseline/H1 对照均相同；
D1/M30 的 segment keys/counts 全部不变。原 study-01/02 保留，仅追加
[局部勘误](DEPRECATION.md)，没有扩大废弃范围。

[audit-03](audit-03.json) 检查 600 条 cutoff 及 12 个案例，除实际 checked_at 外与
audit-02 全字段相同。所有使用证据的已知时间边界继续符合；未知历史可用时间保持未知。
12 份案例 JSON 字节相同，复用受保护的 charts-02 原图；DELTA 记录全部图像 SHA256，
保护检查确认其原始 Git blob 不变。未生成重复截图，也未改变原逐图解释。

## 4. 验证与运行结果

Windows；Python 3.12.14、pytest 8.4.1、Ruff 0.12.9、mypy 1.17.1。
解释器为 `D:/AI_Infra_Quant_Codex_v1/task007c1-env/Scripts/python.exe`；
从工作区根目录运行，`PYTHONUTF8=1`，`PYTHONPATH` 与 `MYPYPATH` 均为根目录及 `src`。

| 命令／检查 | 结果 |
|---|---|
| `python -m pytest tests/research/paqs_q tests/unit/test_paqs_input.py -ra` | **234 passed, 1 warning in 78.52s**，exit 0 |
| `python -m ruff check tools/research/paqs_q/r04 tests/research/paqs_q/r04` | PASS，exit 0 |
| `python -m ruff format --check tools/research/paqs_q/r04 tests/research/paqs_q/r04` | 15 files already formatted，exit 0 |
| `python -m mypy --strict --explicit-package-bases tools/research/paqs_q/r04 tests/research/paqs_q/r04` | 15 files 无问题，exit 0 |
| 上一命令增加 `--platform win32` | 15 files 无问题，exit 0 |
| 新增 reconcile.py/protect.py 的 Ruff、格式、严格 mypy 原生及 win32 | PASS |
| fresh study-03、audit-03、独立 DELTA | PASS，各 exit 0 |
| `git diff --check`、暂存区 diff、保护／路径／链接检查 | PASS |

唯一 warning 为原有 Starlette 对 `anyio.abc.BlockingPortal` 弃用别名的引用。
本机即 Windows，mypy 两个配置不冒称两种独立 OS 环境。
新增证据脚本初次 Ruff 发现三处长字符串，已换行修正并复查；无规则放宽。
浏览器、Uvicorn、PostgreSQL、迁移和完整产品套件在本合同中不要求，本轮未执行。

本次原始 study CLI 实际耗时 **272.49982889999956 秒**，600 次候选计算并核对固定旧算法；
summary/plots 之前输出 **7,535,176 字节**。运行开始／结束为
`2026-09-11T12:14:29.386780Z` / `2026-09-11T12:19:01.889813Z`。
这是本次执行记录，不是性能改进或生产 SLA。
精确命令、退出码、红测结果和版本见 [validation.json](validation.json)。

复现时运行 validation 中的 study、audit、reconcile 命令，输出必须选**新的独占路径**。
仓库内 study-03/audit-03/DELTA 已存在，直接重复原路径会安全拒绝，不能删掉或覆盖它们。
新的对照目录可在离线副本中按同样输入执行；本次交付不改旧复现脚本。

## 5. 文件与保护范围

仅修改两个既有文件：`tools/research/paqs_q/r04/study.py`、
`tests/research/paqs_q/r04/test_study.py`。

新增路径均位于 `docs/evidence/TASK_006B_Q/research-04/` 下：

- `study-03/`：`US.AVGO.{W1,D1,M30}.{OBSERVATIONAL,AS_OF}.json` 共6份，
  `cases/{W1,D1,M30}.{accepted,calendar,repeated-kind,veto}.json` 共12份，
  `summary.json`、`coverage.json`、`source-calendar-manifest.json`，合计21份。
- `remediation-01/`：`REPORT.md`、`DEPRECATION.md`、`DELTA.json`、`audit-03.json`、
  `validation.json`、`protection.json`、`reconcile.py`、`protect.py`、`remote-heads-before.json`。

`protection.json` 记录逐对象核验：受审580文件排除两项可改文件，加不可改合同，
共 **579 个 mode/type/blob 身份**，同时核对 HEAD、index、工作区内容。
`protect.py` 另检查新增路径白名单，无删除／重命名／symlink／mode 改变、相对链接、
diff 与正常后继血缘。最终提交后再次运行只读检查。
原 study-01/02、charts-01/02、原报告、CASE_REVIEW、audit、冻结 PLAN/spec/freeze、
此前研究／参数／universe、产品/runtime、业务测试、依赖及迁移均受上述保护。

本轮只读取冻结外部 JSON，不打开、不迁移、不 checkpoint、不 bootstrap 用户数据库。
没有改写用户数据，也不以旧哈希宣称外部运行中的整个数据库绝对静止。
其他 worktree 保留；仅在本任务目录写入获准文件。

首次 fetch 遇连接 reset，使用单次 `http.version=HTTP/1.1` 后 fetch 成功；后续一次
ls-remote 也遇 reset，改由 GitHub API 读取全部56个 heads，保存在
[推送前远程引用](remote-heads-before.json)。没有修改 Git 配置。
仅正常推送原任务分支；推送后读回最终 SHA、报告及全部 heads，核对权威、review、
此前各任务分支不变。该提交不合并研究、不更新任何权威或独立审查分支。

## 6. 保留限制与停止

AVGO 仍为唯一可用的开发股票样本，current-QFQ/PARTIAL，历史 available_at 未知。
没有新增独立股票或 HK 实际样本，也没有补齐 M30 历史覆盖。
严格真实历史确认及广泛市场适用性继续 **INCOMPLETE**；合成回归不充作真实市场验证。

本轮不调整冻结规则、参数、日历政策、窗口、阈值或 prior-raw veto；保留原结构丢失／
重现和覆盖代价指标。原“另行修改具体规则后实验”的研究建议仍是未实施的未来建议。
此次只完成 R04-F01 聚合整改，交付后停止，等待独立聚焦复核。
