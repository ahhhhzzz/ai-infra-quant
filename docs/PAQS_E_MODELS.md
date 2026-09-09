# Model and credential guide

C1 and C2 are accepted and integrated. Current architecture/lifecycle is documented in
[ARCHITECTURE](ARCHITECTURE.md); status and acceptance attribution are in [ROADMAP](ROADMAP.md).
This catalog describes repository configuration at `722936984deac652b443eba132c69650653345e1`,
not a new live verification of provider availability.

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

Default: **DeepSeek V4 Flash**. The selector is flat, with no provider grouping. The single source
is [model_registry.json](../src/ai_infra_quant/resources/paqs_e/model_registry.json). Model keys currently equal the exact
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
| DeepSeek ON | One native SEARCH; direct valid factual memo, or exactly one tool-free SYNTHESIS for valid completed tool-only SEARCH |
| OpenAI / Alibaba ON | One native search request, source-specific summary normalization; no DeepSeek synthesis flow |
| GLM / Kimi / Hy4 | Research disabled; ordinary Narrative remains available with configured credentials |

DeepSeek accepts recognized partial native actions alongside completed evidence, but requires at
least one completed search. Only accepted completed calls enter stateless pass-back, unchanged;
partial queries/sources never become trusted evidence. Its advisory four-query instruction is not
a four-query acceptance cap. Capture stores only a bounded ordered prefix with total exposed query
count and completeness flag. See [research bounds and diagnostics](ARCHITECTURE.md#5-optional-research-and-provenance)
for the source-verified acceptance/capture limits, provider differences and request counts.

ON can add latency/API cost: DeepSeek uses at most two additional research HTTP requests, final
Narrative is separate. Native search actions/queries are not the number of HTTP attempts or a billing
guarantee. The transport uses a 120-second HTTPX timeout and 2 MB response bound. The browser's
180-second notice leaves the synchronous request guarded; it does not cancel or retry it.

Frozen research is factual auxiliary context, not a strategy answer. Web prices cannot overwrite
Snapshot market facts. Native citations and provider summaries/memos have explicit publication-time
and cutoff limitations; absence of known future timestamps does not prove all statements are
point-in-time safe. Raw native responses and provider reasoning are not persisted. A failed requested
research stage stops before final Narrative and creates no fabricated Run/Result. A terminal final
provider failure after a complete request records a failed Narrative Run without a Result.

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
