# TASK-007C1 model, credential and research guide

Implementation pending independent review. The launcher and workbench remain local-only and
read-only decision support; real trades remain manual in the broker's own client.

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
deleting a local OpenAI credential does not remove it. Unavailable secure storage fails safely.
Never share a screenshot containing a key, and do not put keys in chat, URLs or source files.

## Exact catalog and transports

Default: **DeepSeek V4 Flash**. The selector is flat, with no provider grouping. The single source
is `src/ai_infra_quant/resources/paqs_e/model_registry.json`. Model keys currently equal the exact
provider model IDs; no prefix inference or provider `/models` discovery occurs.

| Display name | Exact model key / provider model ID | Provider identity | Slot | Reasoning | Research |
|---|---|---|---|---|---|
| DeepSeek V4 Flash | `deepseek-v4-flash` | `deepseek` | `deepseek` | responses / json_schema | Responses web_search |
| DeepSeek V4 Pro | `deepseek-v4-pro` | `deepseek` | `deepseek` | responses / json_schema | Responses web_search |
| Qwen3.8 Flash | `qwen3.8-flash` | `alibaba` | `dashscope` | chat / json_schema | Responses web_search |
| Qwen3.8 Max | `qwen3.8-max` | `alibaba` | `dashscope` | chat / json_schema | Responses web_search |
| Qwen3.7 Plus | `qwen3.7-plus` | `alibaba` | `dashscope` | chat / json_schema | Responses web_search |
| GLM-5.2 | `glm-5.2` | `bigmodel` | `bigmodel` | chat / json_object | Disabled |
| Kimi K3 | `kimi-k3` | `kimi` | `moonshot` | chat / json_object | Disabled |
| Hy4 Preview | `hy4-preview` | `tencent` | `tokenhub` | responses / json_schema | Disabled |
| GPT-5.6 Luna | `gpt-5.6-luna` | `openai` | `openai` | responses / json_schema | Responses web_search |
| GPT-5.6 Terra | `gpt-5.6-terra` | `openai` | `openai` | responses / json_schema | Responses web_search |
| GPT-5.6 Sol | `gpt-5.6-sol` | `openai` | `openai` | responses / json_schema | Responses web_search |

Fixed official reasoning endpoints (not exposed as editable configuration):

- DeepSeek: `https://api.deepseek.com/responses`
- Alibaba Model Studio / DashScope (Beijing): `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`
- Zhipu / BigModel: `https://open.bigmodel.cn/api/paas/v4/chat/completions`
- Kimi / Moonshot (China): `https://api.moonshot.cn/v1/chat/completions`
- Tencent TokenHub: `https://tokenhub.tencentmaas.com/v1/responses`
- OpenAI: `https://api.openai.com/v1/responses`

Qwen research uses the same registered Qwen model and DashScope key at
`https://dashscope.aliyuncs.com/compatible-mode/v1/responses`; reasoning uses Chat's explicitly
documented JSON Schema mode. Other enabled research routes use their registered Responses endpoint.
All routes enforce the existing strict Pydantic/domain result schema and deterministic validator.
A malformed result, identity mismatch, refusal or network failure never becomes a strategy judgment.

## Explicit lifecycle and evidence

Only Analyze submits `{security_id, model_key, strategy_id, web_research}`. Model, strategy,
credential, research-toggle, history and market-refresh changes never dispatch analysis.
Each attempt freezes the current Snapshot, resolves its selected model, performs requested research,
normalizes evidence, builds the canonical request, performs tool-free reasoning and commits the
existing terminal Run/validated Decision. Actual provider/model remain immutable audit identities.
Revisions stay keyed by Security + strategy across model changes. Current refresh cannot alter
persisted market or research evidence. Missing credentials disable the button for the selected model.

Research sends one bounded native-search HTTP request, without retries or continuation calls.
The application accepts at most four reported search queries, four search-call records, 64 raw
source records and eight included items. Each source-specific summary is at most 1,600 Unicode
characters; summary plus label/provenance is at most 4,000 per item and 24,000 total. Oversized,
unattributed, malformed, empty or incomplete results fail closed. The HTTP response cap is 2 MB,
research output limit is 6,000 tokens and each transport timeout is 120 seconds. The browser's
180-second timeout is an unknown outcome, not cancellation; it does not retry.

OpenAI also receives `max_tool_calls=4`. DeepSeek documents that this option is ignored and its
server-side auto-continuation limit is ten rounds; Qwen does not document an equivalent request
cap. For these providers four is an **acceptance bound on reported evidence**, not a guarantee of
provider-internal billed searches. One HTTP attempt can contain multiple native searches. The
adapter rejects results exceeding the evidence bound and never continues with silent truncation.
This provider-side cost-control limitation remains visible for independent review and live smoke.

Each item retains native URL/citation identity, title when available (otherwise URL), query/intent,
retrieval time, publication timestamp when supplied, stable content ID and source-specific summary.
Native reasoning traces and chain-of-thought are discarded. Native citation URLs are never fetched
by this application. Generated summaries cannot invent new URLs or publication timestamps.

Known publication timestamps must be timezone-aware and are normalized to UTC. Any included
source explicitly later than the frozen Snapshot As-Of is excluded; retrieval after freeze is
provenance, not publication time. Missing publication time stays `unknown`, with an explicit
limitation that cutoff compatibility cannot be independently confirmed. The unchanged domain
request validation rejects future auxiliary timestamps. Snapshot prices, bars, sessions and
arithmetic facts take precedence over web text; research never writes Snapshot fields.

An unsupported requested route, missing research credentials or incomplete research capsule
returns a typed precondition failure without a fabricated Run ID. The system never proceeds without
requested research. Failures after a complete reasoning capsule retain existing failed-Run semantics.
Prior successful Decisions remain visibly historical. No retry or provider/model fallback occurs.

## Official API evidence and limitations

These primary documents were checked during implementation on 2026-09-07. No required model was
found renamed or removed; no substitute or additional model was introduced.

- [DeepSeek Responses compatibility](https://api-docs.deepseek.com/guides/responses_api/):
  Responses, full `text.format`, native search and stateless behavior; ignored tool-count/include controls.
- [Qwen structured output](https://help.aliyun.com/zh/model-studio/qwen-structured-output):
  Chat JSON Schema for the three required families.
- [Qwen Responses](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-responses) and
  [web search](https://help.aliyun.com/zh/model-studio/web-search): native query/source records.
- [GLM structured output](https://docs.bigmodel.cn/cn/guide/capabilities/struct-output) and
  [GLM-5.2](https://docs.bigmodel.cn/cn/guide/models/text/glm-5.2).
- [Kimi web workflow](https://platform.kimi.ai/docs/guide/use-web-search): the direct workflow
  requires provider-specific tool continuation; that audit path is not enabled by this increment.
- [TokenHub language API overview](https://cloud.tencent.com/document/product/1823/130079):
  Hy4 reasoning route. Auditable native source research is not enabled.
- [OpenAI web search](https://developers.openai.com/api/docs/guides/tools-web-search) and
  [Terra model](https://developers.openai.com/api/docs/models/gpt-5.6-terra).
- [Windows CredWrite](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credwritew):
  current-user credential set and failure behavior.

GLM, Kimi and Hy4 remain usable for reasoning with research disabled. Enabling their direct search
requires separately verified native source normalization. Doubao, MiniMax and every unapproved
model remain absent. No PAQS-Q, backtest, portfolio/PnL, broker, execution, voting, arbitrary URL,
background research or automatic analysis is added. No database migration is added.

## Validation and separate live product acceptance

Install `.[dev]` under Python 3.12 and install Playwright Chromium if needed. Set
`TASK007C_BROWSER_CHANNEL=chromium` when using that browser. Run full pytest, focused model/
credential/research/API/browser tests, `ruff check .`, `ruff format --check .`, and `mypy src tests`.
The browser suite runs actual Uvicorn against a fresh migrated SQLite DB through head
`0002_task007b_paqs_e_ledger`, checks health/OpenAPI/page/configuration over HTTP and uses synthetic
network fixtures for business scenarios. Unit/integration tests inject synthetic credential stores.

No real-provider call is part of ordinary tests. A separate opt-in product acceptance should use a
user key entered through this UI, one supported Security and DeepSeek V4 Flash with research off
first; then explicitly try research if enabled and funded. Record exact code SHA, provider/model,
result class and safe Run/Decision IDs only. This implementation report does not claim that live gate
performed or the task integrated.
