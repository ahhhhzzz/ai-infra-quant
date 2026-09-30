# AI INFRA QUANT v1.0.0

**Windows 本地决策工作台 · 功能冻结，进入使用与维护。**

支持 US/HK 自选、只读行情、PAQS-Q 规则分析、PAQS-E 模型报告、不可变历史和同快照 Q/E 对照。
本次发布固定已有功能，不新增策略、自动交易、EXE 打包或跨机器部署能力。
所有真实交易均由用户在券商官方客户端手工完成；应用不连接交易账户或读取实际持仓。

## 日常启动

当前已配置的固定目录：

```text
D:\AI_Infra_Quant_Codex_v1\ai_infra_quant_codex_v1
```

1. 使用该目录已有的 Python 3.12 环境 `.venv`，不要另建项目副本或虚拟环境。
2. 安装富途官方 Futu OpenD，并在 OpenD 窗口完成登录和行情权限配置。
3. 双击目录内的 **`启动AIInfraQuant.cmd`**。它使用本机 `.local-runtime/launch.ps1`，固定指向该目录、`.venv\Scripts\python.exe` 和原数据库；按需启动 OpenD，等待 `127.0.0.1:11111`，再打开工作台。
4. 浏览器地址：[本地 Dashboard](http://127.0.0.1:8000/)。只读运行状态：[health](http://127.0.0.1:8000/health)。

`启动AIInfraQuant.cmd` 和 `.local-runtime/` 是本机已配置、被 Git 忽略的入口，**不随源码发布**。
仓库保留通用入口 [start_dashboard.bat](start_dashboard.bat)，它使用所在目录的 `.venv`，
启动 OpenD 和独立 Dashboard 控制台。两种入口都会核对已运行服务的源码版本，避免误用旧服务。
看到版本不一致时，先关闭旧 Dashboard 服务再启动；不要批量结束 Python 或 OpenD 进程。

若未找到 OpenD，可一次性设置其实际安装路径，随后重新打开启动入口：

```powershell
setx FUTU_OPEND_EXE "C:\实际安装路径\Futu_OpenD.exe"
```

启动器不会代为登录或取得行情权限。端口未就绪时先完成 OpenD 登录；行情显示 `UNAVAILABLE`、
缺权限或服务错误时按原错误处理，不把空行情当成有效输入。

## Q、E 和历史怎么用

- **Q · 规则分析**：选择证券，点击“分析当前快照 · Q”。先读右侧中文结论，再到“分析详情”查看市场背景、事件、候选、入场资格和“若已持有”。`INSUFFICIENT` 表示证据不足，不能理解为看空；`LONG_READY` 仅表示符合规则，不代表成交。
- **E · 专家分析**：选择模型，点击“配置此模型 API Key”保存对应模型凭据，再显式点击分析。报告可切换格式化/原文，不把模型叙述转换为自动交易结论。
- **联网研究 · Tavily**：选择 DeepSeek，另点“配置 Tavily 搜索 Key”，保存独立搜索 Key，勾选联网后点击分析。DeepSeek 原生搜索仍未支持，Tavily 是独立后端搜索。
- **历史记录**：选择当前证券的已保存 Q/E 记录重新打开；读取原结果和冻结证据，不重新分析。行情刷新、页面重载、切换证券/标签和保存 Key 均不调用搜索或模型。
- **Q/E 对照**：从选中的 Q 记录读取同快照 E 历史，或显式运行同快照 E。两边必须是同一快照，不合成评分或统一买卖结论。历史 Q 快照禁止附加今天的 Tavily 资料，需取消联网再运行。
- **本地行情存档**：仅点击“保存当前行情”才创建观测存档；历史读取不调用 OpenD。存档与分析历史分开，不能自动作为严格历史回测输入。

联网默认关闭。**只有显式提交 E 分析，才可能产生模型费用；勾选 Tavily 后还可能产生搜索费用。**
每次最多两次 basic 搜索、每次最多五条结果。缺 Key、认证失败、限流、超时、空结果或异常响应时，
停止本次联网分析，不自动改成不联网成功。用户可取消勾选后再次显式分析。
报告保留可点击来源、检索时间、实际传入模型的片段及可获得的发布时间；未知时间不补造，
仅有日期时不虚构具体时刻。来源编号检查不等于逐项事实核验。

更多：[Dashboard 使用](docs/DASHBOARD_WORKBENCH.md)、[E 模型、凭据及 Tavily](docs/PAQS_E_MODELS.md)、
[E 工作台](docs/PAQS_E_WORKBENCH.md)、[Q 产品边界](docs/PAQS_Q_PRODUCT_COMPARE_V1.md)。

## 数据、配置与备份

| 内容 | 当前固定环境的位置 / 行为 |
|---|---|
| Python | `.venv\Scripts\python.exe`，Python 3.12 |
| SQLite 历史 | `data\ai_infra_quant.db`；当前迁移为 `0006_external_research` |
| 行情输入、研究报告和备份 | 本地 `data\` 及用户指定的导入/输出目录，不随 Git 发布 |
| 本地配置 | 现有环境变量及 `.env`；保留原配置，勿上传或输出敏感内容 |
| 模型 / Tavily Key | 当前 Windows 用户的凭据管理器；两者独立保存，浏览器只读回“是否已配置” |

Tavily 也支持启动进程的 `TAVILY_API_KEY` 环境变量作为只读后备；不要写进项目 `.env`。
删除界面保存的 Key 不会删除该环境变量。凭据存在不代表额度、认证或连通已经验证。
若自行设置 `DATABASE_URL`，备份和迁移必须使用实际数据库路径，不创建空库替代原历史。

以下 PowerShell 命令对当前固定库执行 SQLite 一致性备份，生成带时间戳的新文件并检查完整性；
**不覆盖已有备份，也不直接复制正在使用的 SQLite 文件**：

```powershell
Set-Location 'D:\AI_Infra_Quant_Codex_v1\ai_infra_quant_codex_v1'
@'
from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3

source = Path("data/ai_infra_quant.db").resolve()
assert source.is_file(), "Existing history database not found"
target = source.parent / "backups" / ("ai_infra_quant_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".db")
target.parent.mkdir(exist_ok=True)
target.touch(exist_ok=False)
with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as src, closing(sqlite3.connect(target)) as dst:
    src.backup(dst)
    assert dst.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "Backup check failed"
print(target)
'@ | .\.venv\Scripts\python.exe -
```

升级前先完成备份。需要迁移时，关闭旧 Dashboard 服务，在同一目录显式使用原库：

```powershell
.\.venv\Scripts\python.exe -m alembic -x database_url=sqlite:///./data/ai_infra_quant.db current
.\.venv\Scripts\python.exe -m alembic -x database_url=sqlite:///./data/ai_infra_quant.db upgrade head
```

不要提交数据库、行情、报告副本、本机配置或凭据。更换 Windows 用户时，原用户的凭据管理器不会自动迁移。

## 已有离线研究入口

使用同一 Python 环境，按现有文档运行；不是日常启动前置步骤，不在本次发布重新研究或调参。

| 工具 | 规则、输入与运行命令 |
|---|---|
| D1 单形态研究与固定风险预算对照 | [单形态使用说明](docs/PAQS_Q_SINGLE_PATTERN.md) |
| 版本化 Context/Event | [Event 规则与 CLI](docs/PAQS_Q_EVENT_V1.md) |
| Setup/Risk 及 Entry 资格 | [Setup/Risk 规则与 CLI](docs/PAQS_Q_SETUP_RISK_V1.md) |

本地真实样本不会随仓库提供。合成演示不等于真实市场回测；单形态结果保留
`EXPLORATORY_NOT_POINT_IN_TIME`，固定风险预算不能保证跳空损失不超预算。

## v1.0 变更与验证归属

本次固定已有行情/历史工作流、中文 Q 摘要与原因归属、已接受的 Q 版本、同快照 Q/E 对照，
以及 DeepSeek + Tavily 独立研究；不改策略参数或重写历史。功能基线为
`2810c1e0da3c97a82983cd3ad779d5faae316bf3`，正式发布身份以 `v1.0.0` 标签为准。
应用版本来自安装包元数据（`pyproject.toml` / `application_version.py`），用于页面、API 与健康状态；
manifest 覆盖的历史包常量不作为发布版本。策略及 artifact 身份独立保留，不随应用版本改写。

- **用户手动使用记录**：用户报告 NVDA 的 Tavily + DeepSeek 联网分析成功；这是用户验收信息，不是 Codex 本轮重新执行的真实调用。
- **本次发布收尾核对**：Windows Python 3.12.14 下，版本/启动器相关 18 项通过；3 个改动 Python 文件的 ruff、格式和 mypy 检查通过，三份上游 manifest 校验通过。仅只读检查已有 NVDA 报告、Run、检索回执及历史接口，均返回 HTTP 200，关联摘要一致；没有再次发起真实搜索或模型调用。
- **用户提供的外部 Linux 复核**：共 107 项，105 passed、2 项基线失败；保留失败事实，不能写成全部通过。本轮未独立运行浏览器验收。
- **历史本地验证**：[Tavily 文档](docs/PAQS_E_MODELS.md#deepseek-独立联网研究--tavily2026-09-30)、[Dashboard 验证](docs/DASHBOARD_WORKBENCH.md)及各原实现报告保留其 Windows、模拟服务和浏览器执行归属，不作为本次重跑记录。
- **保留限制**：当前采集/研究是观察性的；缺证据返回 `INSUFFICIENT`，尚无真实数据正式 Entry 资格；AVGO 原结论、严格历史证据要求及 F1 用户接受的 Linux 布局限定例外不变。

用户单次使用、代码验证和来源保存均不证明市场有效性、稳定盈利、严格 PIT 或全平台通过。
后续以日常使用、备份和针对具体问题的维护为主；新功能需另行授权。
开发入口：[AGENTS](AGENTS.md)、[路线图](docs/ROADMAP.md)、[架构](docs/ARCHITECTURE.md)、[需求矩阵](docs/REQUIREMENTS_MATRIX.md)。
