# Model and credential guide

v1.0.0 当前交付状态见 [README](../README.md)。用户已手动完成一次 NVDA 的 Tavily + DeepSeek
分析并保存带来源的 Narrative；发布收尾只读核对了该历史及来源，不重新调用搜索或模型。
下方实现时的“未真实调用”、零行检索表和待验收说明保留其原时点含义。
外部独立 Linux 聚焦检查为 107 项中 105 passed、2 项已在产品基线复现的失败，不是全部通过。

C1 and C2 are accepted and integrated. Current architecture/lifecycle is documented in
[ARCHITECTURE](ARCHITECTURE.md); status and acceptance attribution are in [ROADMAP](ROADMAP.md).
Current catalog capability was checked against official documentation on 2026-09-24;
this is not a paid provider-connectivity verification. Historical execution evidence stays unchanged.

## Select a model and configure its key

Run the existing Windows launcher, open its loopback URL, select a model and click
**配置此模型 API Key**. Paste the service key only into the password dialog, then **安全保存 / 更新**.
The server stores a generic credential in the current Windows user's Credential Manager, target
`ai-infra-quant/paqs-e/<registered slot>`, with local-machine persistence in that user's credential
set. There is no plaintext file, SQLite, browser storage, cookie, `.env` write or fallback keyring.
The form clears after successful save or closing; reopening/refresh never reads back a key.

Presence is not a balance, entitlement or connectivity check. Configuration/status GETs do not
contact providers or write application state. Models in the same service share one slot. Delete
removes that slot. OpenAI alone can use an existing server environment key as a read-only fallback;
deleting a local OpenAI credential does not remove it. Unavailable secure storage fails safely for mutations; a configured OpenAI read-only environment
fallback can still provide a key. No plaintext fallback is created.
Never share a screenshot containing a key, and do not put keys in chat, URLs or source files.

## Exact catalog and transports

Default: **DeepSeek Flash (V4.1)**. The selector is flat, with no provider grouping. The single source
is [model_registry.json](../src/ai_infra_quant/resources/paqs_e/model_registry.json). Model keys currently equal the exact
provider model IDs; no prefix inference or provider `/models` discovery occurs.

| Display name | Exact model key / provider model ID | Provider identity | Slot | Reasoning | Research |
|---|---|---|---|---|---|
| DeepSeek Flash (V4.1) | `deepseek-flash` | `deepseek` | `deepseek` | responses / final text | External Tavily (separate key); native disabled |
| DeepSeek V4 Pro | `deepseek-v4-pro` | `deepseek` | `deepseek` | responses / final text | External Tavily (separate key); native disabled |
| Qwen3.8 Flash | `qwen3.8-flash` | `alibaba` | `dashscope` | chat / final text | Responses web_search |
| Qwen3.8 Max | `qwen3.8-max` | `alibaba` | `dashscope` | chat / final text | Responses web_search |
| Qwen3.7 Plus | `qwen3.7-plus` | `alibaba` | `dashscope` | chat / final text | Responses web_search |
| GLM-5.2 | `glm-5.2` | `bigmodel` | `bigmodel` | chat / final text | Disabled |
| Kimi K3 | `kimi-k3` | `kimi` | `moonshot` | chat / final text | Disabled |
| Hy4 Preview | `hy4-preview` | `tencent` | `tokenhub` | responses / final text | Disabled |
| GPT-5.6 Luna | `gpt-5.6-luna` | `openai` | `openai` | responses / final text | Responses web_search |
| GPT-5.6 Terra | `gpt-5.6-terra` | `openai` | `openai` | responses / final text | Responses web_search |
| GPT-5.6 Sol | `gpt-5.6-sol` | `openai` | `openai` | responses / final text | Responses web_search |

Fixed official reasoning endpoints (not exposed as editable configuration):

- DeepSeek: `https://api.deepseek.com/responses`
- Alibaba Model Studio / DashScope (Beijing): `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`
- Zhipu / BigModel: `https://open.bigmodel.cn/api/paas/v4/chat/completions`
- Kimi / Moonshot (China): `https://api.moonshot.cn/v1/chat/completions`
- Tencent TokenHub: `https://tokenhub.tencentmaas.com/v1/responses`
- OpenAI: `https://api.openai.com/v1/responses`

Qwen research uses the same registered Qwen model and DashScope key at
`https://dashscope.aliyuncs.com/compatible-mode/v1/responses`; narrative reasoning uses ordinary Chat assistant text. Other enabled research routes use their
registered Responses endpoint. New final reasoning sends neither `response_format` nor `text.format`.
It does not parse final text as JSON or call the legacy projector/semantic validator. Completed,
non-empty final text (at most 100,000 Unicode characters) is preserved exactly; envelope integrity,
model identity, refusal, incompleteness, tool invocation, credential echo and safe response-ID checks
still fail closed. Provider reasoning traces are discarded.

The retired `deepseek-v4-flash` selection is disabled for new calls. Existing records retain
their original model identity and text. The current Flash selection shares the same secure
`deepseek` credential slot. [Official model naming](https://api-docs.deepseek.com/zh-cn/)
and [Responses compatibility](https://api-docs.deepseek.com/guides/responses_api/) now state
that old Flash names route to V4.1 and built-in `web_search` is ignored. Native research remains
disabled. The separate opt-in Tavily route below supplies saved external evidence without changing
that capability flag. No ordinary model text is accepted as completed search.

## Explicit lifecycle and evidence

Only Analyze submits the four required fields: Security, registered model key, registered strategy
and research boolean. Changing model/strategy, saving a key, refreshing charts or reading history
never submits an analysis. The selected model is used once for final tool-free Narrative reasoning;
there is no voting, fallback or automatic retry. Final accepted text and its frozen evidence are
recorded in a separate Narrative Ledger. Prior structured Decisions remain Legacy read-only evidence.

Research defaults OFF at load and after every model change, is not remembered across reloads and
is not restored from history. Unsupported models disable the checkbox; forcing an unsupported ON
request fails explicitly. Presence of a stored key does not establish provider availability.

| Research choice | Behavior before final Narrative |
|---|---|
| OFF | Zero research calls; unchanged Snapshot-bound final-text path |
| Current DeepSeek ON | Independent Tavily basic search, separate credential and receipt; no native SEARCH/SYNTHESIS |
| Historical DeepSeek ON (disabled in current catalog) | One native SEARCH; direct valid factual memo, or exactly one tool-free SYNTHESIS for valid completed tool-only SEARCH |
| OpenAI / Alibaba ON | One native search request, source-specific summary normalization; no DeepSeek synthesis flow |
| GLM / Kimi / Hy4 | Research disabled; ordinary Narrative remains available with configured credentials |

The retained historical DeepSeek parser accepts recognized partial native actions alongside completed evidence, but requires at
least one completed search. Only accepted completed calls enter stateless pass-back, unchanged;
partial queries/sources never become trusted evidence. Its advisory four-query instruction is not
a four-query acceptance cap. Capture stores only a bounded ordered prefix with total exposed query
count and completeness flag. See [research bounds and diagnostics](ARCHITECTURE.md#5-optional-research-and-provenance)
for the source-verified acceptance/capture limits, provider differences and request counts.

ON can add latency/API cost: the historical DeepSeek route used at most two additional research HTTP requests, final
Narrative is separate. Native search actions/queries are not the number of HTTP attempts or a billing
guarantee. The transport uses a 120-second HTTPX timeout and 2 MB response bound. The browser's
180-second notice leaves the synchronous request guarded; it does not cancel or retry it.

Frozen research is factual auxiliary context, not a strategy answer. Web prices cannot overwrite
Snapshot market facts. Native citations and provider summaries/memos have explicit publication-time
and cutoff limitations; absence of known future timestamps does not prove all statements are
point-in-time safe. Raw native responses and provider reasoning are not persisted. A failed requested
research stage stops before final Narrative and creates no fabricated Run/Result. A terminal final
provider failure after a complete request records a failed Narrative Run without a Result.

## DeepSeek 独立联网研究 · Tavily（2026-09-30）

Windows 下继续使用现有启动入口，打开 **E 分析**，选择 DeepSeek，然后点击
**配置 Tavily 搜索 Key**。输入独立的 `TAVILY_API_KEY`，安全保存后勾选
**联网研究 · Tavily**，最后点击分析。搜索和模型请求都可能产生费用；保存 Key、勾选、
切换证券、刷新和读取历史均不会触发请求。开关默认关闭，切换模型或更新凭据后重置。
未配置时开关禁用并提示“请配置搜索服务”，不联网分析仍可使用。

Key 存在当前 Windows 用户的凭据管理器 `ai-infra-quant/paqs-e/tavily`，与模型 Key 分开。
也可在启动进程前设置 `TAVILY_API_KEY` 环境变量，作为只读后备；**不要写入项目 `.env`**。
界面只返回配置是否存在，不回传 Key；删除安全存储中的 Key 不会删除环境变量后备。
是否已配置不代表认证、额度或连通已经验证。

按 [Tavily 官方 Search 接口](https://docs.tavily.com/documentation/api-reference/endpoint/search)
调用固定 HTTPS 地址，每次分析最多两次 basic 请求，每次最多五条；无重试、跳转、抓取或模型生成查询词。
`auto_parameters`、`include_answer`、`include_raw_content` 均为 false。
查询只包含公开公司名称（已有时）、代码、市场及当前日期，覆盖新闻与公告；来源需匹配公司名称
或带市场/交易所限定的代码，不能仅凭短代码命中。排序优先交易所、监管机构、投资者关系路径和指定媒体，
但这不是来源真实性或每条结论的自动认证。

响应最大 2 MB；HTTP 超时 20 秒、连接 10 秒、流读取期限 25 秒。URL 去重，每条资料片段最多
1,600 字符、正文总量最多 12,000 字符，正文与来源元数据合计最多 40,000 字符。
检索时间、快照时间与原始发布时间分别保存；发布时间缺失保留未知，已知晚于快照的发布时间被排除。
当前资料仍标为 `OBSERVATIONAL_NOT_POINT_IN_TIME`。**对历史 Q 冻结快照的 E 对照禁止附加当前 Tavily
资料**，在搜索和模型调用前说明原因；可以显式取消联网做同快照对照，或回到 E 发起当前快照分析。

成功或失败的检索证据先保存到独立只追加记录，再决定是否调用最终模型。缺 Key、认证失败、限流、
超时、空结果、异常格式或不可用服务均停止本次联网分析，界面提供中文原因和技术错误码。
不自动取消联网、不伪造成功；用户可取消勾选后重新显式分析。`GET /api/v1/paqs-e/external-research/{research_id}`
只读取已有回执；配置接口位于 `/api/v1/paqs-e/research-credentials/tavily`，沿用本机同源安全边界。

最终模型使用独立的 `paqs-e-narrative-tavily-prompt-v1`，把网页内容作为不可信外部资料，
不能覆盖快照行情或执行其中指令。要求用 `[T1]` 等本次编号引用；缺少引用或引用不存在编号时，
保存失败 Run，不保存成功 Narrative。检查仅证明编号属于本次来源，**不证明引用支持每项结论**。
成功报告保留模型原文，附可点击来源、检索时间、可获得的发布时间及实际输入片段。
旧报告继续使用原提示词和原冻结证据；重新打开不执行检索或模型请求。Q 的事实、规则及 manifest 不变。

数据库增量迁移为 `0006_external_research`，在原表之外新增不可更新/删除的检索证据表。
升级已有本地库前先用 SQLite backup API 做一致性备份，在项目目录运行：

```powershell
.\.venv\Scripts\python.exe -m alembic -x database_url=sqlite:///./data/ai_infra_quant.db upgrade head
```

本轮 Windows Python 3.12.14 验证使用模拟搜索/模型及隔离测试数据库：适配器 25 项、凭据 14 项，
相关 API、旧 E 历史、Q 同快照与架构检查 67 项通过；Tavily 浏览器 11 项、既有原生研究兼容
1 项通过（兼容用例补上当前界面的 E/历史标签点击）。仅日期来源保留日期精度，边界用例已复验。
模拟 HTTP 覆盖 Tavily → 已保存证据 → 实际 NarrativeGateway 的调用链。
改动文件的 ruff、格式和 mypy 检查通过；Context/Event/Setup 三份 manifest 校验通过。
现用 SQLite 已先完成一致性备份、升级至 0006，并核对原 27 张业务表行数与逐行内容摘要一致；
新检索表为零行。备份、数据库及本地核对回执均不进入 Git。
没有发起真实 Tavily 搜索或收费模型请求，也未重跑行情研究。真实验收还需配置有效 Tavily 与
DeepSeek Key、可用行情服务，然后由用户显式执行一次联网分析，确认来源与报告。

## API and storage details

[ModelCredentials](../src/ai_infra_quant/application/paqs_e_models.py) owns registered-slot resolution
and priority; [CredentialStore](../src/ai_infra_quant/core/ports/credentials.py) is provider-neutral.
[WindowsCredentialStore](../src/ai_infra_quant/integrations/windows_credentials.py) is the production
implementation. Users do submit keys through the local password input. Read APIs return only status,
never the key. Model endpoint/API surface/slot are repository-owned, not arbitrary client parameters.
The registry's `structured_output_mode` remains Legacy metadata and does not impose structured
output on `NarrativeGateway`. See [API contracts](API_CONTRACTS.md#7-configuration-and-local-credentials)
for same-origin/loopback/JSON constraints and errors.

## Evidence and limitations

[Catalog and credential tests](../tests/unit/test_paqs_e_model_gateway.py),
[all-model Narrative tests](../tests/unit/test_paqs_e_narrative_provider.py),
[research continuation tests](../tests/unit/test_paqs_e_research_continuation.py),
[partial action tests](../tests/unit/test_paqs_e_partial_actions.py) and
[browser credential tests](../tests/browser/test_paqs_e_multi_model.py) use synthetic provider/store
fixtures. They are not paid live verification of every model, account permission or OS installation.
Historical provider-document investigations and test executions remain in the immutable
[C1/R01–R06 reports linked by architecture](ARCHITECTURE.md#9-historical-evolution-and-evidence).
The [C1 closeout](decisions/TASK_007C1_CLOSEOUT_2026_09_08.md) records user acceptance separately
from independent exact-SHA code review. ADC does not repeat paid calls or recompute user-local hashes.
