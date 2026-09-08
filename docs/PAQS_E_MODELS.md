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
| DeepSeek V4 Flash | `deepseek-v4-flash` | `deepseek` | `deepseek` | responses / final text | Responses web_search |
| DeepSeek V4 Pro | `deepseek-v4-pro` | `deepseek` | `deepseek` | responses / final text | Responses web_search |
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

## Explicit lifecycle and evidence

Only Analyze submits `{security_id, model_key, strategy_id, web_research}`. Model, strategy,
credential, research-toggle, history and market-refresh changes never dispatch analysis.
Each attempt freezes the current Snapshot, resolves its selected model, performs requested research,
normalizes evidence, builds the canonical request, performs tool-free reasoning and commits the
new terminal Narrative Run and exact-text Narrative Result atomically. Actual provider/model remain immutable audit identities.
Narrative revisions are keyed by Security + strategy across model changes, independent of legacy revisions. Current refresh cannot alter
persisted market or research evidence. Missing credentials disable the button for the selected model.

Research defaults OFF on initial load and every model change, and is never remembered across reloads.
Enabling it is explicit and can increase latency and API cost. Research sends one bounded
native-search HTTP request. R04 permits one additional tool-free DeepSeek memo-synthesis request
only for a valid completed tool-only SEARCH response; there are no retries.
For OpenAI and Alibaba, the application accepts at most four reported search queries, 64 raw
source records and eight included items. Each source-specific summary is at most 1,600 Unicode
characters; summary plus label/provenance is at most 4,000 per item and 24,000 total. Oversized,
unattributed, malformed, empty or incomplete results fail closed. The HTTP response cap is 2 MB,
research output limit is 6,000 tokens and each transport timeout is 120 seconds. The browser's
180-second notice leaves the synchronous request pending and guarded until its terminal response
or a real connection failure. It neither aborts nor retries.

Remediation 04 preserves DeepSeek's exact provider-native factual research memo and accepts up to
64 completed native actions in at most 128 output items: `search`, `open_page`, and `find_in_page`, including
at least one search. R05 validates each exposed query (non-empty, UTF-8, control-safe, at most
500 characters) with structural limits of 256 queries and 64,000 total query characters. Missing
queries or native sources alone no longer prevent success. No JSON result or source-array output
is requested. Memo text is capped at 24,000 Unicode characters, and memo + provenance + label
together must fit the existing 24,000-character research budget; excess fails without truncation.
One item freezes the exact memo, a null memo publication timestamp, safe response identity,
retrieval/intent/As-Of, ordered actions, actual queries, optional native sources and an explicit
limitation: cutoff compliance was requested but cannot be independently verified for every statement;
Snapshot market facts take precedence. No hidden reasoning or raw envelope is retained.

More than four searches or exposed queries no longer causes DeepSeek acceptance failure. Query
capture retains only an ordered prefix of at most 16 whole queries / 4,000 characters. The first
query that cannot fit stops capture, even if a later shorter query could fit. All exposed queries
are still validated and counted, including duplicates and entries after capture stops. Native
`query` and `queries` fields, when both exposed, count in their received order. Provenance adds
`provider_exposed_query_count` and `query_capture_complete`; omitted queries are never fabricated
or silently presented as a complete list. The SEARCH instruction's four-query request is advisory,
not a provider billing guarantee or a post-hoc success rule.

SEARCH forces the sole native web-search tool with `reasoning.effort=none` and a 6,000-token cap.
One valid final memo takes the direct path, using one research request. Only a completed valid
tool-only response enters SYNTHESIS: the original intent, accepted `web_search_call` items passed
back unchanged in memory, and a final factual memo instruction form the stateless input.
SYNTHESIS uses the same endpoint/model/credential, `reasoning.effort=none`, `tools=[]`,
`tool_choice=none`, and a 4,000-token cap. Both requests use `store=false`, `stream=false` and
no previous-response/conversation/background state. Serialized research requests and responses
are capped at 2 MB. An invalid SEARCH never triggers SYNTHESIS; neither stage retries.
The final unchanged tool-free Narrative runs only after the exact accepted memo is frozen.
Research-OFF uses zero research calls; ON uses one or two, thus two or three total provider calls.
Safe provenance records SEARCH status/id/counts/actions, optional SYNTHESIS id, synthesis use,
and research HTTP request count. Ten provider continuation rounds do not imply ten output items.

Research precondition errors retain their existing API code and create no Run/Result. Optional
`research_diagnostic` metadata reports a fixed stage/failure class, registered route, safe response
status/id, stage-local action/search/message counts (saturated at 129), synthesis-attempt flag,
HTTP request count, and only allowlisted incomplete reasons. No memo, raw body, hidden prompt,
exception text, reasoning or credential is included. The UI shows only fixed stage/class/count
fields, preserving the prior Narrative and never retrying. Diagnostics are not stored in the ledger.
R05 adds optional `provider_exposed_query_count`, `raw_source_record_count` and
`unknown_action_count`, exact integers saturated at 1024. Failure diagnostics count exposed query
slots, including invalid individual values on rejected envelopes; successful provenance counts
only valid queries. Unknown container shapes omit the affected totals. The client displays only
validated numeric values, never queries, URLs, source titles, raw detail or diagnostic JSON.

Optional native source/citation records are capped at 64 before deduplication. URLs must be explicit
HTTP(S), at most 1,000 characters, with a hostname and no userinfo, whitespace/control characters or
backslashes; titles are at most 500 characters. Only aware publication timestamps are retained.
Known future URLs are excluded even if duplicated elsewhere; the memo remains with its limitation.
Prose URLs and page/find targets are never promoted to trusted provenance. Other providers retain
their existing four-action, search-only source-normalized behavior and source-specific bounds.

OpenAI also receives `max_tool_calls=4`. DeepSeek documents that this option is ignored and its
server-side auto-continuation limit is ten rounds; Qwen does not document an equivalent request
cap. OpenAI/Alibaba retain their four-query acceptance bounds. DeepSeek's normal multiplicity is
provider-owned; its 256-query anti-abuse limit is not a billing guarantee. One HTTP attempt can
contain multiple native searches. The
adapter rejects results exceeding the evidence bound and never continues with silent truncation.
This provider-side cost-control limitation remains visible for independent review and live smoke.

OpenAI/Alibaba items retain native URL/citation identity, title when available (otherwise URL), query/intent,
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

The following R01 behavior remains **legacy structured only**, outside new narrative analyses.
After strict provider parsing, the legacy provider-neutral runtime projects only current quote price,
timestamp, freshness and session from the immutable Snapshot before the unchanged validator.
The same four factual echoes are projected for model-eligible executable entry references; the
eligibility flag and policy text remain model-authored. Identity, support/input quality, semantic
assessments, invalidation, targets, RR and explanation fields are not corrected. Market-open,
freshness, session, RR and semantic rules can still reject the result.

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
background research or automatic analysis is added. Remediation 02 adds only the authorized narrative ledger migration 0003; migrations 0001/0002 are unchanged.

## Validation and separate live product acceptance

Install `.[dev]` under Python 3.12 and install Playwright Chromium if needed. Set
`TASK007C_BROWSER_CHANNEL=chromium` when using that browser. Run full pytest, focused model/
credential/research/API/browser tests, `ruff check .`, `ruff format --check .`, and `mypy src tests`.
The browser suite runs actual Uvicorn against a fresh migrated SQLite DB through head
`0003_task007c1_narrative_ledger`, checks health/OpenAPI/page/configuration over HTTP and uses synthetic
network fixtures for business scenarios. Unit/integration tests inject synthetic credential stores.

No real-provider call is part of ordinary tests. The R03 Contract records successful research-OFF
live acceptance at `74a19387adc408e9453c30fdbb30e6636ac4e695`; this remediation preserves that final
provider/prompt/ledger path. After independent review, the mandatory remaining live check is one
explicit DeepSeek V4 Flash research-ON attempt on the exact reviewed final R05 SHA using the user's locally
entered key. Record safe Run/Result identities, exact response/request hash verification, frozen
memo/provenance and formatted/raw readability. This does not claim that live ON gate or integration.
