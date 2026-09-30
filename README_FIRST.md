# AI INFRA QUANT v1.0.0 · 从这里开始

当前状态：**功能冻结，进入使用与维护**。这是已配置的 Windows 本地只读决策工作台，
不是新的初始化工程，也不包含 EXE 安装包、跨机器部署或自动交易能力。

1. 打开 `D:\AI_Infra_Quant_Codex_v1\ai_infra_quant_codex_v1`，双击本机 `启动AIInfraQuant.cmd`。
   保留现有 `.venv`、配置和数据库；不需要新的 worktree 或环境。该入口被 Git 忽略，
   仓库通用入口为 [start_dashboard.bat](start_dashboard.bat)。
2. 在 Futu OpenD 完成登录，确认 `127.0.0.1:11111` 可用；浏览器打开 [Dashboard](http://127.0.0.1:8000/)。
3. 按 [README](README.md) 配置独立的模型/Tavily Key，使用 Q/E 分析、历史、来源和备份。
   搜索与模型调用只在显式提交时发生，可能产生费用；读取历史不重新分析。
4. 使用现有功能，遇到具体问题再维护。代码变更先读 [AGENTS](AGENTS.md)、
   [ROADMAP](docs/ROADMAP.md) 和适用规则，不复用过时的启动/开发提示词。

用户报告的 NVDA 联网成功、外部 Linux 105 passed / 2 基线失败（107 项）及历史 Windows
记录均分别归属，见 README。观察性数据、正式 Entry 证据不足、F1 Linux 限定例外不变；
不宣称全部真实数据路径、全平台或市场有效性已通过。
