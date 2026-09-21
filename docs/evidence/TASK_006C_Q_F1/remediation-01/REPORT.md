# TASK-006C-Q-F1 Remediation 01 — 交付与验证

日期：2026-09-21。状态：**REMEDIATED / VALIDATION INCOMPLETE / AWAITING FOCUSED REVIEW**。
本报告不宣告独立复核 PASS、F1 收尾或产品整合。

## 基线与授权

- 整改起点：`d0e8dc22b38d85b0d1395cf76fc03f2de1e85122`。
- 整改范围冻结：`81cf97391d682d4025f8691ab4129f73faa5bc66`；[整改合同](../../../../prompts/tasks/TASK-006C-Q-F1_REMEDIATION_01.md)。
- 本轮源码、测试及 manifest 检查点：`5b62a250b93ff35e7a3baa8f65019bec4979e39b`。
- 原 [F1 合同](../../../../prompts/tasks/TASK-006C-Q-F1_VERSIONED_QUANT_EVENT_FRAMEWORK_FOUNDATION.md)
  blob `c2c5448c1eb72fd0ece1572c31ba30246a761b51` 不变。
- 权威产品分支仍为 `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`。

用户在独立审查列出 F01/F02/F03 与旧测试冲突后，指示“进行下一步”。本轮仅落实这些
整改及相应验证；原报告、Windows receipt、研究/golden 证据保持历史身份。

命令行 git push 缺少 GitHub 认证，未改变远程。交付改用已连接 GitHub 接口创建相同内容树，
最后以 force=false 快进原任务分支；没有合并或改写旧历史。提交元数据由 GitHub 生成，
因此本地实测 SHA 与远程镜像 SHA 不同，但对应完整 Git tree 逐一相同：

| 阶段 | 本地实际检查点 | 远程同树镜像 |
|---|---|---|
| 整改范围冻结 | 81cf97391d682d4025f8691ab4129f73faa5bc66 | 9c8c293f30db83db9984c309a01ec86976417495 |
| 源码与测试 | 5b62a250b93ff35e7a3baa8f65019bec4979e39b | 364412ec94c7138480e8e3b0e902d57e4ba55dc3 |

冻结 tree 为 `d1e71f80528de10dfc0ea10eca1555dc4da8e031`；源码/测试 tree 为
`d93c625e1a52b856aa6a0d78e282d10d4cab2da0`。验证记录保留实际执行的本地 SHA，不伪称在
远程镜像 SHA 上重新运行测试。保护工具按冻结合同 blob 核验，不依赖远程没有的本地提交。

## 修正结果

| 项目 | 原复现 | 本轮行为与证据 |
|---|---|---|
| F01 | 删除 price、对象价格、增加未知字段后重算哈希，仍通过结果校验 | Record、工厂及 QResult 解码共享字段/类型检查；验证 canonical Decimal/时间、嵌套行情/日历支持字段与 version ref；校验记录 ID、重复和排序；36 项新增测试中的对应反例拒绝 |
| F02 | OBSERVATIONAL Structure 可以交给 AS_OF Event 输入 | Event 调用前检查 input/as_of/mode/snapshot 与原注册 ID/version/code/capability/status/lineage；拒绝未来证据；用测试 spy 确认拒绝发生于插件调用前，不重跑 Structure |
| F03 | 计算窗口之前混入其他证券或周期仍 AVAILABLE | 整个已选输入先检查证券/周期；B0/A1、AS_OF/OBSERVATIONAL 均返回 INVALID / BAR_IDENTITY_CONFLICT，无成功 payload |
| F1-12 历史断言 | TASK-007B 全仓禁止任何 paqs_q 路径 | 仅替换该过时断言：Q 文件只能在已批准的独立位置，其他产品源码不得引用 Q；原 Ledger/account/order/worker 禁用项全部保留 |

`tests/paqs_q/test_registry.py` 的两处原反例现重算记录 ID，以继续测试“有效历史结果但
实现不存在”及“内部自洽但与传入上游不一致”的原注册表分支。没有删除、跳过或减弱断言。

F02 使用原结果的 config hash，不猜测原参数或替换默认配置。没有可用的原实现时返回
typed SelectionError / UPSTREAM_IMPLEMENTATION_UNAVAILABLE；不会回退到当前实现。
命名 record/support 字段为闭合 schema；legacy、Event evidence、result evidence/lineage
和 display 为插件契约拥有的 canonical 对象，其内部市场语义不由通用框架推断。
哈希证明一致性和身份，不是防止能重建全部哈希者伪造内容的数字签名。

## 实际验证

环境：Linux、Python 3.12.14、pytest 8.4.1、tzdata 2025.2、Ruff 0.12.9、mypy 1.17.1。

| 检查 | 本轮结果 |
|---|---|
| F1 测试 | 91 passed，1 warning（原 55 项加新增 36 项） |
| 原研究及输入测试 | 268 passed，1 warning |
| 与原报告相同的产品回归选择 | 1096 passed，1 warning |
| 浏览器回归 | 分段完成 64 passed、1 failed；该失败在整改前基线完全复现，未豁免 |
| 实际 Uvicorn 启动 | PASS；临时 SQLite 迁移后 /health 与 Dashboard 均为 HTTP 200 |
| Ruff / 格式 | PASS，22 个相关文件；新增验证脚本另行检查 |
| native / win32 strict mypy | PASS，21 个相关源码文件 |
| 修正后 Linux canonical vectors | PASS，28 组 |
| 修正后 Windows 实际执行 | PENDING；当前执行环境没有 Windows executor |

唯一业务测试 warning 为原 Starlette 对 anyio.abc.BlockingPortal 的弃用提示。
native/win32 mypy 均使用 MYPYPATH=src:.，没有关闭严格模式或忽略缺失导入。
首次产品回归使用相对 PYTHONPATH，导致四项切换工作目录的迁移子进程找不到包；改用
绝对 PYTHONPATH 后同一 1096 项全部通过，未修改迁移、产品源码或相关测试。
初始浏览器尝试因恢复的环境缺少可执行 Node/Chrome，在 fixture 阶段报错；未计为 PASS。
临时安装 Playwright 对应 Chromium 后，完整浏览器的 process singleton socket 被容器
拒绝（Operation not permitted），65 项均为 fixture errors，未修改测试或绕过权限。
随后使用同一 Playwright 1.55.0 自带的 Chromium Headless Shell 140.0.7339.16（build 1187），
通过测试原有 TASK007C_BROWSER_CHANNEL 环境设置选择默认 headless 可执行程序。
首次实际运行得到 56 passed、1 failed、8 fixture errors；archive fixture 会覆盖 PYTHONPATH，
使临时 venv 的借用依赖不可见。将同一依赖目录注册到临时 venv 的 .pth 后，单独补跑原来的
8 项 archive 测试全部通过。未修改浏览器/迁移测试，也未重复累计测试数量。

唯一剩余失败为 `test_visual_acceptance_artifacts[390-844-success-True]`：
`#mode-frozen` 的 y=856.03125，不满足 y<844。对整改前 **d0e8dc2** 使用相同 Headless Shell
执行原样测试，得到完全相同的坐标和失败。它是此 Linux 浏览器环境中可复现的既有布局
问题，不是本轮 Q 校验改动引入的差异；原 Windows 报告曾通过该项。未猜测其根因、改动
产品布局或删减断言。**F1-12 的历史全仓 Q 禁用冲突已修正，产品回归通过；浏览器门槛仍未
全部通过，保留 INCOMPLETE 交独立复核，不能自行视为豁免。**

完整命令、分段运行和失败归属见 [验证记录](validation.json)。

保留原 [实现报告](../../../reports/TASK_006C_Q_F1_IMPLEMENTATION_REPORT.md) 的测试范围，
没有宣称全产品 suite 或 PostgreSQL 实库运行。所有数据库测试使用临时合成资源，
没有读取/修改用户数据库、访问 OpenD、模型接口或新市场样本。

## 哈希和跨平台证据

[本轮 Linux 向量](linux-vectors.json)：

- vector digest：`dbcdb54348d004819d58f5c948e8226851f7694113facffb81201314aed36e32`
- B0 code hash：`623f63f622cfdcfe364b121c99e6b35e987054b94ee24c9063f505484c1ff1df`
- A1 code hash：`da1127afc9d76bb8edaa04833cb9f0cce54307fa8f2b50327900d780544ef040`

B0/A1 的 12 个冻结输入和 14 个原案例来源不变，完整 golden 语义 projection 通过。
只有校验规则和实现身份改变；参数、极值/确认、veto、calendar 和研究口径未改。
先前独立复核已在 d0e8dc2 比较原 28 组 Windows/Linux 摘要一致，但这不替代修正后
artifact 的双平台验证。因此本轮 **F1-02 仍 PENDING**，不得复用旧 Windows receipt。

F1 尚未发布/采纳，本轮保留合同中的 B0 1.0.0 与 A1 0.1.0 标识，并通过新的 code hash
区分整改实现。原对象可由父 SHA 恢复，同一注册表继续拒绝相同 ID/version 的内容冲突。
历史结果不得重新解释为新 manifest 的结果。

在本任务最终交付提交的干净 checkout、已有依赖的 Python 3.12 环境中运行 PowerShell：

```powershell
$env:PYTHONPATH = "$(Get-Location)\src;$(Get-Location)"
$env:PYTHONUTF8 = "1"
python -m pytest tests/paqs_q -ra
if ($LASTEXITCODE -ne 0) { throw "F1 tests failed" }
python tools/validation/paqs_q_f1.py --vectors "$env:TEMP\paqs-q-f1-windows-remediation-01.json"
if ($LASTEXITCODE -ne 0) { throw "Vector generation failed" }
python docs/evidence/TASK_006C_Q_F1/remediation-01/verify.py --windows "$env:TEMP\paqs-q-f1-windows-remediation-01.json"
if ($LASTEXITCODE -ne 0) { throw "Protection or cross-platform comparison failed" }
python -m pytest tests/browser/test_paqs_e_ui_cleanup.py tests/browser/test_market_archive_browser.py tests/browser/test_paqs_e_workbench.py -ra
if ($LASTEXITCODE -ne 0) { throw "Browser regression failed" }
```

比较检查 vectors、code_hashes、vector_digest、Python/tzdata 版本及 Windows/Linux 标签。
前两类检查不启动行情、Analyze 或数据库；最后的浏览器测试自动创建临时合成数据库和
本地测试服务，不访问用户数据库或外部提供商。保留终端输出、实际系统及提交 SHA，交独立复核。

## 保护与交付范围

[只读保护验证器](verify.py) 比较起点的每个受保护 Git 对象及工作文件，检查闭合变更范围、
原 F1 合同和链接。只对合同中列出的 14 个现有文件开放修改；其余 **713 个原对象**保持不变。
原始研究、golden、Windows receipt、旧报告、依赖、迁移及已接受产品 runtime 不变。
原 F1 protection 工具保持不变，因其历史范围不包含本次测试例外，本轮使用单独验证器。
精确变更文件列表、对象数量与链接结果见 [保护记录](protection.json)。
本轮相对起点共 21 个文件变更（14 个既有文件、7 个新增文件），224 个相对链接通过，
git diff --check 通过。源码及测试在上述代码检查点之后不再改变。

最终 SHA、精确变更列表及验证记录以本目录交付证据和 Git 提交为准。
仅使用 GitHub 接口快进原任务分支；不合并、不更新权威分支，不启动生产 Event、R06 或 UI/API 接入。
本轮实施者不将本次自测称为独立复核通过。
