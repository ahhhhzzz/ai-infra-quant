# TASK-007C1 — PAQS-E Multi-Model Gateway + Secure Local Credentials + Auditable Web Research

Status: **APPROVED TASK CONTRACT — user-authorized TASK-007C1 implementation only**

Issued: 2026-09-07

Repository: `ahhhhzzz/ai-infra-quant`

Authoritative base branch: `roadmap/no-live-trading`

Exact authoritative base SHA: `80f089bc2d285cca492c41aaeaf047e177bc2812`

Dedicated implementation branch: `task/007c1-paqs-e-multi-model-web-research`

Final Contract path: `prompts/tasks/TASK-007C1_PAQS_E_MULTI_MODEL_SECURE_CREDENTIALS_WEB_RESEARCH.md`

Parent workstream: current-analysis PAQS-E MVP, after accepted/integrated TASK-007A, TASK-007B and TASK-007C.

This task is an additive post-MVP usability and model-access upgrade. It does not reopen accepted strategy semantics, Snapshot-on-Demand, Decision Ledger immutability, or the permanent no-broker/no-live-trading boundary.

---

## 1. Purpose

Make the current PAQS-E workbench usable with multiple mainstream reasoning models without requiring the user to edit `.env`, know provider/base-URL details, or manually type model IDs.

The normal user experience must expose **one flat model selector containing model names only**. Provider/company routing is internal infrastructure and must not become a second normal-user dropdown.

The user must be able to:

1. select a model by human-readable model name;
2. configure the API credential needed for that model from the local web UI;
3. have the credential stored securely on the local machine rather than in browser storage or plaintext application data;
4. optionally enable auditable web research before PAQS-E reasoning;
5. explicitly click Analyze once;
6. receive the same strict PAQS-E structured result, deterministic validation, immutable Analysis Run and Decision semantics already accepted in TASK-007A/007B;
7. inspect the actual model/provider identity and frozen research evidence in audit/detail views.

The architecture must remain provider-neutral even though each concrete model route has an internal provider.

---

## 2. Permanent product boundaries preserved

The following remain unchanged and are not negotiable in this task:

- local-first, single-user decision-support application;
- loopback-only local server;
- real trades are performed manually in an official broker client;
- no broker account connection or observation;
- no broker-write API;
- no `place_order`, `cancel_order`, `modify_order`, `unlock_trade`;
- no live OMS/EMS;
- no autonomous or unattended trading;
- no automatic PAQS-E analysis from quote refresh, timers, model changes, credential changes, history reads or web-research refreshes;
- one explicit Analyze action creates one new attempt;
- strict Snapshot-on-Demand / As-Of factual boundary remains primary for market facts;
- PAQS-E Doctrine/strategy semantics and deterministic validator remain authoritative and provider-independent.

No part of web research may override the immutable market Snapshot as the source of truth for current price, completed W1/D1/M30 structure, trigger, follow-through or deterministic RR arithmetic.

---

## 3. Accepted predecessor state

The exact authoritative base already contains:

- TASK-006B2 immutable Snapshot-on-Demand market snapshot;
- TASK-007A PAQS-E reasoning request/result schema, strict output parsing, provider port, runtime prompt, strategy package and deterministic validator;
- TASK-007B on-demand Analyze service and immutable Decision Ledger;
- TASK-007C PAQS-E user dashboard/workbench;
- final TASK-007C independent review PASS evidence.

Do not replace those layers. Extend their existing ports and data model deliberately.

Current accepted facts relevant to this task:

- `PaqsEReasoningRequestV1` already stores `model_provider`, `model_id` and `auxiliary_context[]`;
- `ResultIdentity` already stores `model_provider` and `model_id`;
- TASK-007B tables already store `model_provider` and `model_id` as unrestricted audit fields;
- Decision revision lineage remains `security_id + strategy_id`, not provider/model;
- the full canonical reasoning request is already persisted for every completed Analysis Run where a complete request exists;
- therefore web evidence can be frozen into `auxiliary_context[]` and persisted inside the existing request capsule;
- no new Decision-Ledger schema is required merely to support new providers or web evidence.

---

## 4. User-visible model selector — flat names only

Replace the free-text model-ID input with one controlled model selector.

The normal dropdown must show **model names only**, without provider/company section headers and without a separate provider selector.

Required first catalog, in this order unless a documented UX reason requires a different stable order:

```text
DeepSeek V4 Flash
DeepSeek V4 Pro
Qwen3.8 Flash
Qwen3.8 Max
Qwen3.7 Plus
GLM-5.2
Kimi K3
Hy4 Preview
GPT-5.6 Luna
GPT-5.6 Terra
GPT-5.6 Sol
```

The default model for a fresh user is:

```text
DeepSeek V4 Flash
```

The dropdown must not contain company headings such as `DeepSeek`, `Alibaba`, `Zhipu`, `Moonshot`, `Tencent`, `OpenAI`, or `Provider` as grouping UI. Company/provider identity may appear only where technically necessary in credential setup help or advanced audit metadata.

Do not expose arbitrary model-ID entry in the normal UI.

Do not infer a provider from a user-entered string. The server resolves a selected stable `model_key` through a controlled registry.

---

## 5. Controlled model registry

Add a repository-owned, version-controlled model catalog, for example:

`src/ai_infra_quant/resources/paqs_e/model_registry.json`

The exact location may differ if an existing resource pattern makes another location clearly superior, but there must be a single authoritative registry and no duplicated hard-coded model lists in Python and JavaScript.

Each model descriptor must include enough internal information to resolve:

- stable application `model_key`;
- user-visible `display_name`;
- internal `provider_id`;
- exact provider model identifier;
- credential slot;
- fixed server-side API endpoint/route identity;
- API surface used by the adapter (`responses` or `chat_completions` or another explicitly reviewed equivalent);
- structured-output capability mode;
- web-research capability mode;
- whether the model is enabled in the normal selector.

Provider IDs, base URLs, protocol details and credential slot names are infrastructure/audit facts, not normal selector labels.

The browser must receive only the bounded model projection it needs. It must not receive arbitrary base URLs, filesystem paths, prompt content, strategy content or secret values.

No production user-supplied provider URL is allowed in this task.

---

## 6. Required model routing at issuance

The following routes were verified against official provider documentation on 2026-09-07 and form the intended first implementation target.

### 6.1 DeepSeek direct

Display names:

- `DeepSeek V4 Flash`
- `DeepSeek V4 Pro`

Provider model IDs:

- `deepseek-v4-flash`
- `deepseek-v4-pro`

Official OpenAI-compatible base URL:

- `https://api.deepseek.com`

DeepSeek currently documents Responses API support, JSON Schema structured output and server-side `web_search`.

Credential slot: DeepSeek API key.

### 6.2 Qwen through Alibaba Cloud Model Studio / DashScope

Display names:

- `Qwen3.8 Flash`
- `Qwen3.8 Max`
- `Qwen3.7 Plus`

Provider model IDs:

- `qwen3.8-flash`
- `qwen3.8-max`
- `qwen3.7-plus`

Use the current official OpenAI-compatible Alibaba Model Studio/DashScope API surface. The standard Beijing compatible endpoint is allowed; business-space-specific endpoints are not user-configurable base URLs in this task.

Qwen currently documents Responses/Chat compatibility, structured output and web search for these families.

Credential slot: Alibaba Model Studio / DashScope API key.

### 6.3 GLM direct

Display name:

- `GLM-5.2`

Provider model ID:

- `glm-5.2`

Use the current official Zhipu/BigModel API endpoint and documented JSON structured-output path. Web Search capability may be used only through the official documented tool path and only if the adapter can capture bounded auditable evidence under section 13.

Credential slot: Zhipu/BigModel API key.

### 6.4 Kimi direct

Display name:

- `Kimi K3`

Provider model ID:

- `kimi-k3`

Use the official Kimi/Moonshot OpenAI-compatible API endpoint for the China-local product path unless repository deployment policy explicitly selects the documented international endpoint.

Kimi currently documents OpenAI-compatible Chat/Responses, JSON output and a built-in web-search workflow.

Credential slot: Kimi/Moonshot API key.

### 6.5 Tencent TokenHub

Display name:

- `Hy4 Preview`

Provider model ID:

- `hy4-preview`

Use the current Tencent Cloud TokenHub OpenAI-compatible endpoint. TokenHub currently documents Responses API and structured output for Hy4 Preview.

Web research must be marked supported only if the exact implemented TokenHub path can produce auditable source/citation evidence satisfying section 13. Otherwise the model remains usable for PAQS-E reasoning with web research disabled.

Credential slot: Tencent TokenHub API key.

### 6.6 OpenAI retained

Display names:

- `GPT-5.6 Luna`
- `GPT-5.6 Terra`
- `GPT-5.6 Sol`

Provider model IDs:

- `gpt-5.6-luna`
- `gpt-5.6-terra`
- `gpt-5.6-sol`

Retain the accepted OpenAI Responses adapter behavior and credential compatibility unless a small provider-neutral refactor is needed.

Credential slot: OpenAI API key.

### 6.7 Additional mainstream models

Do not silently add unreviewed models simply because a provider model-list endpoint returns them.

Doubao/Volcengine, MiniMax and later model families are intentionally left as catalog-extension work unless the implementation can point to a stable official exact model identifier, a supported production API route, and a structured-output path that passes the same strict PAQS-E acceptance tests. They are not allowed to delay or weaken the required first catalog above.

If an issued required model becomes unavailable or renamed during implementation, stop and report the exact official change rather than guessing a replacement.

---

## 7. Provider-neutral runtime architecture

Refactor the current OpenAI-only composition into a provider-neutral model gateway.

Conceptually:

```text
ModelRegistry
    ↓
ModelDescriptor
    ↓
CredentialStore
    ↓
ReasoningProviderRegistry / Adapter Factory
    ↓
PaqsEReasoningProvider
    ↓
PaqsEReasoningRuntime
    ↓
existing Pydantic/domain conversion
    ↓
existing deterministic validator
```

Avoid six copy-pasted adapters if the providers share an OpenAI-compatible protocol. Prefer a bounded generic OpenAI-compatible transport with explicit provider descriptors and small provider-specific hooks where protocol differences are real.

Do not make provider-specific code modify PAQS-E strategy judgments, validator thresholds or market facts.

Every successful provider response must still become the exact accepted PAQS-E domain result and pass the same deterministic validator before a Decision exists.

Provider-native JSON Schema enforcement is preferred where available. For a provider that only offers JSON Object mode, strict local Pydantic/schema validation is mandatory; invalid or missing fields map to the existing `INVALID_STRUCTURED_OUTPUT` failure and never create a Decision.

No provider may be allowed to return free-form text and bypass the accepted structured-result contract.

---

## 8. Analyze API change — model key, not provider/model strings

The normal Analyze request must no longer accept arbitrary provider/model strings from the UI.

Replace the current three-field request with the following bounded request:

```json
{
  "security_id": "<canonical UUID>",
  "model_key": "<registered stable key>",
  "strategy_id": "paqs-e-master",
  "web_research": true
}
```

The exact application `model_key` values are implementation details from the controlled registry. The browser submits only registered values obtained from the configuration endpoint.

The server resolves:

```text
model_key
→ provider_id
→ provider model_id
→ credential slot
→ adapter/API surface
→ web-research capability
```

The immutable reasoning request and ledger continue to store the actual resolved:

- `model_provider`;
- `model_id`.

Do not persist only the user-facing display label as model identity.

Do not guess provider identity from a model-name prefix.

Do not silently substitute another model if the selected model is unavailable or its credential is missing.

The old arbitrary `model_id` POST input is superseded for the normal TASK-007C1 API contract. Update only the bounded older tests whose exact three-field requirement is intentionally superseded, preserving all other TASK-007B failure, immutability and ledger assertions.

---

## 9. Decision Ledger semantics stay unchanged

Do not modify:

- `0001_phase1_foundation.py`;
- `0002_task007b_paqs_e_decision_ledger.py`;
- existing immutable ledger table semantics;
- Decision revision key.

No `0003` migration is expected or authorized for model-provider support, credential storage or web evidence.

The existing database already stores `model_provider` and `model_id`.

Revision chain remains:

```text
security_id + strategy_id
```

Example:

```text
AVGO + paqs-e-master
rev1  deepseek / deepseek-v4-flash
rev2  alibaba / qwen3.8-max
rev3  kimi / kimi-k3
```

Changing model/provider does not reset revision numbering.

Failed Analysis Runs do not consume Decision revision numbers.

---

## 10. Web-based API credential management

The user must not be required to edit `.env` for normal operation.

Add a local API-key management experience accessible from the PAQS-E workbench.

The normal interaction may be model-centric:

```text
Selected model: DeepSeek V4 Flash
Credential: not configured
[Configure API Key]
```

The credential dialog may identify the actual service whose key is required, because the user must know which API key to paste. This exception does not change the requirement that the model selector itself shows model names only.

After a key is stored, the UI shows only a bounded status such as:

```text
Stored locally · not yet verified
```

The UI must never read the secret back.

Required mutation operations:

- save/update the credential used by a registered model;
- delete the locally stored credential;
- read only configured/not-configured status.

No endpoint may return the API key, key prefix, key suffix, environment value, decrypted secret or credential-store raw record.

Saving a credential must not automatically issue a paid provider request. It records the secret locally; validity/entitlement is proven only by a later explicit provider operation unless a separately explicit non-paid verification action is added and reviewed.

Existing `OPENAI_API_KEY` environment fallback may remain supported for backwards compatibility, but web UI writes must never modify `.env` or process/user environment variables.

---

## 11. Secure local credential storage

API keys must not be stored in:

- browser `localStorage`;
- browser `sessionStorage`;
- IndexedDB;
- cookies;
- HTML/JS source;
- query strings;
- SQLite plaintext columns;
- Decision Ledger payloads;
- logs;
- screenshots/test fixtures;
- `.env` written by the web UI;
- Git.

Introduce a provider-neutral `CredentialStore` port.

Production Windows behavior must use an operating-system-protected local secret store, e.g. Windows Credential Manager / DPAPI-backed storage, directly or through a reviewed library that fails closed when secure storage is unavailable.

No plaintext fallback is permitted.

Tests may use an injected fake/in-memory credential store containing synthetic sentinels.

On a platform where the production secure credential backend is unavailable, the credential mutation API must fail truthfully and safely; it must not silently write plaintext.

Store only the minimum provider credential needed for API access. Non-secret status metadata may be held in application memory/configuration if useful; do not create a new database merely for credential status.

---

## 12. Credential mutation security

Credential mutation endpoints are sensitive even on localhost.

Requirements:

- loopback server boundary remains enforced;
- mutations use JSON request bodies, never query parameters;
- reject cross-origin credential mutation using same-origin/Origin/Fetch-Metadata or an equivalent explicit CSRF defense;
- no GET changes credential state;
- no secret value in errors;
- no raw exception/trace in browser response;
- reject unknown/unregistered model keys and credential slots;
- bounded secret length and basic non-empty validation;
- secret is redacted before any logging layer;
- browser input uses a password-type control and clears the in-memory form value after successful submission;
- page refresh or history navigation cannot repopulate the secret value.

Normal read-only model/configuration endpoints remain provider-network-free.

---

## 13. Auditable web research

Add one user-facing toggle near Analyze:

```text
[✓] 联网研究
```

Default: enabled for a fresh page/model when the selected model route supports the accepted research path.

Changing the toggle does not run research and does not run Analyze.

### 13.1 Lifecycle

When the user explicitly clicks Analyze with web research enabled:

```text
freeze immutable Market Snapshot
↓
resolve exact selected model/provider
↓
run bounded web-research stage
↓
normalize/freeze research evidence
↓
build PaqsEReasoningRequest with auxiliary_context[]
↓
run PAQS-E reasoning with research tools disabled
↓
strict parse + deterministic validator
↓
immutable Analysis Run / Decision
```

The reasoning stage must consume frozen research evidence. It must not perform hidden additional web searches after the request capsule is finalized.

### 13.2 Same selected model route

For this task, web research uses the selected model/provider's reviewed native search capability where supported. Do not silently switch to another paid provider or another model for research.

If the selected model route does not support an auditable research path, the UI must state this truthfully. If `web_research=true` is submitted anyway, reject the attempt before reasoning rather than silently disabling research.

### 13.3 Evidence normalization

Normalize research into bounded `AuxiliaryContextItem` entries using category `web_research` (or the repository's canonical equivalent).

Each included evidence item must preserve, where the provider makes it available:

- stable context ID;
- source title/label;
- source URL/citation identity;
- publication/source timestamp;
- retrieval/provenance metadata;
- bounded excerpt or factual summary;
- query/research intent;
- uncertainty/limitation if publication time or source metadata is incomplete.

The exact provider-native tool transcript may be retained in bounded provenance only if it contains no secret and is needed for audit. Do not persist chain-of-thought/reasoning traces.

### 13.4 Bounds

Research must be bounded and cost-conscious.

Recommended hard limits for v1:

- no more than 4 search queries;
- no more than 8 included evidence items;
- no more than 4,000 UTF-8 characters of normalized content per evidence item;
- no more than 24,000 UTF-8 characters across web-research auxiliary content;
- no automatic retries that create another paid research attempt after an ambiguous network outcome.

Equivalent tighter limits are allowed if tests prove they preserve useful evidence.

### 13.5 As-Of

The market Snapshot `as_of_timestamp` remains the decision cutoff.

- exclude any source explicitly timestamped after the Snapshot As-Of;
- preserve source timestamps as UTC when known;
- unknown publication timestamps remain explicitly unknown rather than fabricated;
- an unknown timestamp may be included only with provenance/limitation making that uncertainty visible;
- no auxiliary context may set a known future `source_timestamp` and still claim `as_of_compatible=true`;
- the existing TASK-007A request validation remains authoritative.

Research retrieval naturally occurs after Snapshot freeze; retrieval time is provenance, not the source's publication time.

### 13.6 Market-fact precedence

Web evidence may inform context such as company news, earnings, analyst developments and public fundamental/event context.

It may not overwrite Snapshot-bound:

- current/reference price;
- completed W1/D1/M30 bars;
- market/session state;
- completed-bar trigger/follow-through facts;
- deterministic arithmetic inputs.

If web text conflicts with Snapshot market facts, Snapshot facts win and the conflict may be noted as uncertainty.

### 13.7 Research failure

If the user explicitly requested web research and the research stage fails:

- do not silently continue without it;
- do not fabricate evidence;
- do not create a successful Decision;
- return a truthful typed failure;
- persist a failed Analysis Run if and only if a complete canonical attempted request can truthfully be formed under existing TASK-007B semantics;
- otherwise retain the existing precondition-failure behavior with no fabricated Run ID.

---

## 14. Provider capability rules

At issuance, intended research support is:

- DeepSeek V4 Flash: supported if native `web_search` evidence can be normalized;
- DeepSeek V4 Pro: supported if native `web_search` evidence can be normalized;
- Qwen3.8 Flash: supported;
- Qwen3.8 Max: supported;
- Qwen3.7 Plus: supported;
- GLM-5.2: supported only through the official web-search tool path if evidence normalization is auditable;
- Kimi K3: supported through the official web-search tool path if evidence normalization is auditable;
- Hy4 Preview: disabled unless exact TokenHub research-source evidence satisfies this Contract;
- GPT-5.6 Luna/Terra/Sol: retain reviewed OpenAI web-search capability only through the new bounded research stage, not hidden inside final reasoning.

Do not claim web research support based only on marketing text. The adapter must prove a deterministic, testable evidence-normalization path.

---

## 15. Configuration API / model catalog projection

Extend the existing PAQS-E configuration endpoint rather than adding a broad provider-management API.

The browser needs a bounded projection conceptually equivalent to:

```json
{
  "default_model_key": "deepseek-v4-flash",
  "models": [
    {
      "model_key": "deepseek-v4-flash",
      "display_name": "DeepSeek V4 Flash",
      "credential_configured": true,
      "web_research_supported": true
    }
  ],
  "default_strategy_id": "paqs-e-master",
  "strategies": []
}
```

Normal configuration response must not expose:

- secret values;
- secret fragments;
- provider base URLs;
- arbitrary transport configuration;
- environment dumps;
- strategy/prompt bodies;
- filesystem paths.

Advanced Decision audit may continue to show actual `model_provider` and provider model ID because they are immutable analysis identity facts.

Configuration GET makes zero paid provider calls and zero application writes.

---

## 16. UI behavior

Update the existing TASK-007C workbench, not a new frontend application.

The right-side analysis panel should conceptually become:

```text
新的当前分析

模型
[ DeepSeek V4 Flash ▼ ]

主策略
[ PAQS-E Context-Free Master Spec ▼ ]

[✓] 联网研究

凭据状态：已安全保存 / 未配置
[配置此模型 API Key]

[ Analyze · 分析当前快照 ]
```

Requirements:

- one model dropdown only;
- dropdown options show the required display names exactly and without company/provider grouping headings;
- no arbitrary model text input in normal mode;
- model changes never trigger Analyze;
- credential save/delete never triggers Analyze;
- web-research toggle never triggers Analyze;
- strategy change never triggers Analyze;
- current market refresh never triggers Analyze;
- user must explicitly press Analyze;
- keep one in-flight Analyze guard per page;
- capture model_key, strategy_id, web_research and security_id before the first async operation;
- later UI changes cannot relabel the pending result;
- successful result/history rows show the human-readable model name;
- advanced audit shows actual provider/model identity stored in the Decision/Run;
- a missing credential disables Analyze for that model with a clear configure action;
- `credential_configured=true` means only securely stored/present, not validated entitlement or balance;
- no API key in screenshots.

Preserve the existing responsive wide/narrow layouts and dark/light themes.

---

## 17. Reasoning and output integrity

The existing PAQS-E runtime prompt, strategy package and deterministic validator remain unchanged unless a strictly provider-neutral transport adaptation is necessary.

Do not modify:

- PAQS-E Doctrine/master strategy content;
- strategy registry semantics;
- prompt semantic instructions;
- setup definitions;
- key-level requirements;
- Trigger/Follow-through mapping;
- invalidation/target semantics;
- RR arithmetic;
- short-execution guardrails;
- Snapshot market fact validation.

Every provider must produce the same domain `PaqsEReasoningResultV1`.

Every result must contain identity matching the resolved actual `model_provider` and `model_id`.

Any identity mismatch or malformed structured output fails before Decision persistence.

Do not expose provider reasoning chain-of-thought. Provider reasoning tokens/traces may be discarded; only final structured result and safe usage metadata, if implemented, may be retained.

---

## 18. Existing failure semantics preserved

Retain the accepted failure kinds:

- `CONFIGURATION_ERROR`;
- `PROVIDER_UNAVAILABLE`;
- `PROVIDER_REFUSAL`;
- `INVALID_STRUCTURED_OUTPUT`;
- deterministic `VALIDATION_FAILED`.

A missing credential is a configuration problem, not `NO_TRADE`.

Provider billing/quota/network failures are provider failures, not strategy judgments.

A web-research failure requested by the user is not `NO_TRADE` and does not create a Decision.

No automatic paid retry after an ambiguous network outcome.

No fallback to a different model/provider after a selected provider fails.

The UI must keep the prior successful Decision visibly historical when a new attempt fails.

---

## 19. Expected code areas

Expected primary areas include, subject to actual repository architecture:

- `src/ai_infra_quant/resources/paqs_e/model_registry.json` or equivalent;
- `src/ai_infra_quant/core/ports/paqs_e_reasoning.py` only if provider registry abstraction requires a bounded change;
- new credential-store port under core/application boundary;
- provider-neutral model catalog/configuration application service;
- `application/paqs_e_analysis.py` for model resolution + research orchestration;
- `application/paqs_e_runtime.py` for removing OpenAI hard-code from request construction;
- provider adapter/composition modules under `integrations/`;
- `backend/dependencies.py` composition wiring;
- `backend/api/v1/paqs_e.py` and schemas for bounded model/credential/analyze API changes;
- frontend `paqs-e.js`, template and CSS;
- `.env.example` only for backwards-compatible server-side env fallbacks if retained; never insert real keys;
- focused unit/integration/browser/security tests;
- user/API/architecture docs necessary to describe the new model and credential workflow.

Do not edit database migrations or accepted review evidence.

---

## 20. Bounded older-test supersession

TASK-007B/007C tests intentionally fixed the then-current API/UI, including:

- exact three-field Analyze POST;
- free-text model ID;
- OpenAI-only configuration projection;
- no model catalog/provider management.

This Contract authorizes only the minimum test changes needed to supersede those stage-specific expectations with:

- registered `model_key` Analyze input;
- one flat model selector;
- secure credential status/mutations;
- bounded web-research flag;
- provider-neutral identity audit.

Do not weaken unrelated immutable ledger, Snapshot, no-broker, no-automatic-analysis, secret-nondisclosure, history, race, Decimal, timezone or frontend-injection tests.

Enumerate every modified older test and the replacement assertion in the final implementation report.

---

## 21. Required deterministic tests

### 21.1 Model registry

Test:

- exact required display-name catalog;
- one flat selector projection;
- unique model keys;
- unique/valid provider mappings;
- default DeepSeek V4 Flash;
- invalid registry rejected safely;
- unknown model key rejected;
- no arbitrary base URL from browser/user input;
- model display name never becomes provider identity.

### 21.2 Provider adapters

For every required model route, using fake clients/HTTP boundaries:

- exact provider/model identity in request/result;
- strict structured output accepted when valid;
- malformed JSON/schema rejected;
- provider refusal mapped correctly;
- provider/network error mapped correctly;
- no secret in error/log;
- no provider-specific strategy semantic changes;
- no store/conversation/background state where the provider API offers such options and stateless operation is possible.

### 21.3 Credentials

Test:

- save/update/delete with synthetic keys;
- API never returns secret value or fragments;
- secret absent from DB, ledger, logs, DOM persistence and browser storage;
- secure-store unavailable fails closed;
- environment fallback, if retained, is read-only and never written by UI;
- model credential status updates correctly when models share one credential slot;
- cross-origin mutation rejected;
- GET never writes;
- unknown model key cannot create arbitrary secret records.

### 21.4 Analyze API

Test exact bounded request:

- `security_id`;
- `model_key`;
- `strategy_id`;
- `web_research`.

Reject arbitrary provider/model/base-url fields.

Confirm resolved actual provider/model reach the immutable request and ledger.

Confirm revision chain remains security + strategy across model changes.

### 21.5 Web research

Test:

- no research when toggle false;
- exactly one bounded research stage per explicit Analyze when true;
- no automatic research on market refresh/model selection/credential save/history reads;
- search query/source/item/character bounds;
- explicit future source timestamps excluded;
- unknown source timestamp remains unknown and visibly limited;
- normalized evidence becomes `auxiliary_context[]`;
- persisted canonical request contains the exact frozen evidence;
- final reasoning uses frozen evidence with tools disabled;
- research failure does not silently continue;
- no research evidence can override Snapshot price/bar facts;
- current market refresh after Decision does not alter frozen research evidence.

### 21.6 Browser

Real browser tests must cover:

- exact flat model dropdown names;
- no provider/company grouping headings in the dropdown;
- switching models produces zero Analyze POSTs;
- model with missing credential cannot Analyze and offers credential configuration;
- credential save clears input and never renders secret;
- delete credential updates status;
- browser storage does not contain secret;
- web-research toggle behavior;
- exact Analyze POST with model_key and web_research;
- stale/racing result identity protection still works;
- history selection remains stable;
- provider/model audit identity visible in advanced details;
- successful Decision using synthetic provider route;
- typed provider/research failures;
- dark/light and narrow/wide layout remains usable.

---

## 22. Live-product smoke gate

Ordinary automated tests must not require paid real-provider calls.

However, because this task exists to make the MVP usable with domestic API access, final product acceptance should include at least one opt-in real-provider smoke in an environment where the user has supplied a real credential through the new UI.

Preferred first smoke:

```text
DeepSeek V4 Flash
web research disabled first
one supported Security
one explicit Analyze
→ successful immutable Decision
```

Then, if the selected route's native search is enabled and funded:

```text
same or another explicit Analyze
web research enabled
→ frozen auxiliary web evidence
→ successful immutable Decision
```

Do not commit, print, screenshot or transmit the real API key.

A reviewer without access to user credentials may independently review the deterministic implementation and treat the real-provider smoke as separate execution evidence, analogous to the accepted TASK-007C browser-evidence workflow.

---

## 23. Documentation requirements

Update only documentation necessary to explain:

- single flat model selector;
- exact first model catalog;
- secure local web credential configuration;
- configured vs verified credential meaning;
- web-research toggle and As-Of/evidence semantics;
- provider/model audit identity;
- no automatic retries/fallbacks;
- no brokerage behavior;
- how to run the local product without manually editing `.env` for supported UI-managed credentials.

Do not falsely mark future Doubao/MiniMax/etc. model routes implemented unless they are actually implemented and independently reviewed.

Do not rewrite historical accepted contracts/reviews.

---

## 24. Official external references fixed for this Contract

These URLs were checked on 2026-09-07 as design evidence, not runtime dependencies:

DeepSeek:

- `https://api-docs.deepseek.com/`
- `https://api-docs.deepseek.com/api/create-response/`
- `https://api-docs.deepseek.com/quick_start/pricing/`

Alibaba Cloud Model Studio / Qwen:

- `https://help.aliyun.com/zh/model-studio/text-generation-model`
- `https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-responses`
- `https://help.aliyun.com/zh/model-studio/qwen-structured-output`
- `https://help.aliyun.com/zh/model-studio/web-search`
- `https://help.aliyun.com/zh/model-studio/base-url`

Zhipu / GLM:

- `https://docs.bigmodel.cn/api-reference/模型-api/对话补全`
- `https://docs.bigmodel.cn/cn/guide/capabilities/struct-output`
- `https://docs.bigmodel.cn/cn/guide/models/text/glm-5.2`

Kimi:

- `https://platform.moonshot.cn/docs`
- `https://platform.kimi.ai/docs/guide/use-web-search`

Tencent TokenHub / Hy4:

- `https://cloud.tencent.com/document/product/1823/130078`
- `https://cloud.tencent.cn/document/product/1823/130051`
- `https://cloud.tencent.com/document/product/1823/130079`
- `https://cloud.tencent.cn/document/product/1823/132252`

OpenAI:

- `https://platform.openai.com/docs/models`

If official behavior materially changes before implementation, report it; do not substitute third-party undocumented assumptions.

---

## 25. Explicit non-goals

This task does not implement:

- PAQS-Q;
- TASK-006B1 market-data store/replay;
- historical Gold Set/backtest;
- portfolio/PnL/positions;
- broker account connectivity;
- execution/order routing;
- automatic model voting/ensemble;
- simultaneous multi-model Analyze;
- automatic provider fallback;
- user-defined provider base URLs;
- arbitrary model-ID text input;
- provider marketplace/model discovery from unreviewed `/models` responses;
- prompt editor;
- strategy editor;
- news scheduler/background monitoring;
- periodic research jobs;
- authentication/multi-user hosting;
- public deployment;
- mobile native app;
- storing secrets in application DB.

---

## 26. Protected files and history

Do not change:

- `docs/phases/PHASE_1_PLAN.md`;
- `src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py`;
- `src/ai_infra_quant/database/migrations/versions/0002_task007b_paqs_e_decision_ledger.py`;
- accepted independent review evidence;
- accepted TASK-007A/007B/007C contracts;
- `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md`;
- runtime strategy Markdown or prompt content unless a separate approved semantic task authorizes it;
- unrelated local user files including `phase1_remediation_commit.txt` if present.

No force-push.

No merge by Codex.

---

## 27. Git preconditions

Before editing, Codex must verify:

```text
repository = ahhhhzzz/ai-infra-quant
current branch = task/007c1-paqs-e-multi-model-web-research
current HEAD = exact issued TASK-007C1 Contract commit
Contract commit parent = 80f089bc2d285cca492c41aaeaf047e177bc2812
origin/roadmap/no-live-trading = 80f089bc2d285cca492c41aaeaf047e177bc2812
merge base with authoritative = 80f089bc2d285cca492c41aaeaf047e177bc2812
```

If any precondition is false, stop without implementation changes and report the mismatch.

Use an isolated clean checkout/worktree if another process is using the repository.

Do not stash/reset/terminate unrelated work.

---

## 28. Validation and stop condition

Run and report repository-standard validation, including at minimum:

```text
pytest focused TASK-007C1 model/credential/provider/web-research/API/browser tests
pytest full suite
ruff check
ruff format --check
mypy
fresh SQLite migration/startup smoke through accepted migration head
actual Uvicorn + /health + /openapi.json + / + PAQS-E configuration over HTTP
browser workbench suite
```

Confirm migration head remains `0002_task007b_paqs_e_ledger`.

Confirm Windows launcher tests remain green.

Confirm no real secret/private data is staged.

If a live domestic-provider smoke is performed, report only provider/model, exact code SHA, success/failure class and safe IDs; never report the credential.

Commit and push only the dedicated task branch.

Stop for independent review.

Do not move `roadmap/no-live-trading`.

Do not start another task.

---

## 29. Required final implementation report

The report must include:

1. authoritative base SHA;
2. Contract commit SHA;
3. final implementation SHA;
4. parent / merge base / ahead-behind;
5. exact changed-file list;
6. model-registry entries and exact internal provider model IDs;
7. any official API behavior that changed since Contract issuance;
8. credential-store implementation and security boundary;
9. exact Analyze API supersession;
10. web-research lifecycle and bounds;
11. how As-Of filtering is enforced;
12. every changed older test and replacement evidence;
13. full validation results;
14. browser results;
15. live-provider smoke evidence if performed;
16. explicit statement that no database migration was added;
17. explicit statement that no broker/live-trading scope was added;
18. explicit statement that no real API key was committed/logged/persisted in browser/application DB;
19. remaining limitations and deferred model routes;
20. final branch HEAD and confirmation that no merge was performed.
