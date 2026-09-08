# TASK-007C1 REMEDIATION 02 — PAQS-E Narrative-First Reasoning

Status: **APPROVED ARCHITECTURAL SUPERSESSION — user-authorized remediation only**

Issued: 2026-09-08

Repository: `ahhhhzzz/ai-infra-quant`

Authoritative branch: `roadmap/no-live-trading`

Authoritative SHA at issuance: `80f089bc2d285cca492c41aaeaf047e177bc2812`

TASK-007C1 branch: `task/007c1-paqs-e-multi-model-web-research`

Exact remediation base / latest reviewed implementation SHA: `6681fc6a934f44d29879c2ef1152891c3bd3a0d5`

Original TASK-007C1 Contract commit: `9f41016b2341e91ad2825b7f731bca4f378b0108`

Remediation 01 Contract commit: `b7316e83f7fd377f4c628db90dee8e3d7b4a5335`

Original Contract:
`prompts/tasks/TASK-007C1_PAQS_E_MULTI_MODEL_SECURE_CREDENTIALS_WEB_RESEARCH.md`

Remediation 01 Contract:
`prompts/tasks/TASK-007C1_REMEDIATION_01_LIVE_DOGFOOD_RUNTIME_COMPATIBILITY.md`

This Contract is an explicit user-approved architectural supersession of the **new-analysis output path only**. The user has decided that PAQS-E should return the LLM's final narrative answer directly instead of requiring strict JSON Schema / Pydantic semantic output before an analysis can succeed.

This Contract does **not** delete or rewrite accepted historical structured Decisions. It introduces a new narrative-first analysis ledger and makes that path the only normal user-facing Analyze workflow.

---

## 1. Product decision

The new product rule is:

> The LLM's final visible text is the PAQS-E analysis result.

For new user-initiated analyses:

- do not require JSON Schema structured output;
- do not require the provider to emit `PaqsEReasoningResultV1`;
- do not run the existing semantic `validate_reasoning_result(...)` as a success gate;
- do not reject an otherwise valid provider answer because it failed an enum, echo field, RR, trigger/follow-through, or other structured semantic field;
- do not fabricate old structured fields from prose merely to fit the legacy Decision schema.

A successful new analysis means:

1. a valid immutable market Snapshot was frozen;
2. requested web research, if enabled, completed into a bounded auditable frozen evidence capsule;
3. the selected registered model completed one explicit final reasoning request;
4. the provider returned one bounded, non-empty final user-visible text answer;
5. the answer passed only transport/safety/integrity checks required to store and display text safely;
6. the immutable narrative Run/Result was durably committed.

The new success criterion is **not** semantic approval by the application.

---

## 2. Permanent boundaries preserved

All permanent product safety boundaries remain unchanged:

- local-first, single-user;
- loopback-only server;
- read-only quantitative research / decision support;
- real trades are manual in the official broker client;
- no broker account connection or observation;
- no broker write;
- no `place_order`, `cancel_order`, `modify_order`, `unlock_trade`;
- no live OMS/EMS;
- no autonomous or unattended trading;
- no automatic Analyze on quote refresh, model change, credential change, history reads, timers or background jobs;
- no model voting/ensemble;
- no automatic retry after ambiguous paid-provider outcomes;
- no automatic provider/model fallback;
- no PAQS-Q, backtest, 006B1, portfolio/PnL, positions or execution scope;
- market Snapshot remains the source of truth for local market facts displayed by the application;
- web research remains separate from final reasoning and cannot mutate the frozen Snapshot;
- credentials remain local and secret-safe under the accepted TASK-007C1 architecture;
- R1 stale-backend source-revision handshake remains in force;
- R3 long-running Analyze remains non-aborting and single-in-flight;
- R2 bounded web-research provenance remains in force.

---

## 3. Accepted live evidence motivating this supersession

Real local dogfooding demonstrated that DeepSeek V4 Flash API connectivity is functional, but the strict structured-output path is an unnecessary reliability bottleneck for the product goal.

### 3.1 First live reasoning run

On implementation SHA `fc527c61fcdc2b4f54506dc5622f0b1faa6945d5`, a real DeepSeek V4 Flash request reached:

- provider success;
- strict schema/domain parsing;
- deterministic validator;

and then failed only with:

`CURRENT_PRICE_FRESHNESS_MISMATCH`

Run:
`038920ac-8bf6-4d2c-97f5-e78f803f0f2f`

This showed that an otherwise useful model answer could be discarded because a model-authored echo of a deterministic fact differed from the application's semantic schema.

### 3.2 Post-Remediation-01 live reasoning run

On SHA `6681fc6a934f44d29879c2ef1152891c3bd3a0d5`, with web research disabled, a real DeepSeek V4 Flash request completed in about 38 seconds but failed before validation with:

- Run: `28435f5b-d669-4030-85a5-7598eccc69da`
- `status = PROVIDER_FAILED`
- `failure_kind = INVALID_STRUCTURED_OUTPUT`
- `failure_reason = Provider output failed strict PAQS-E parsing`
- `validation_issues_json = []`

The provider connection and paid request were real; the application rejected the provider result because the exact structured contract could not be confirmed.

The user has explicitly chosen not to continue spending engineering effort making the LLM satisfy a strict structured semantic envelope for the primary PAQS-E experience.

---

## 4. Narrative-first architecture

The normal current-analysis path becomes:

```text
User selects Security
↓
Explicit Analyze
↓
Freeze immutable Market Snapshot
↓
Optional bounded auditable Web Research
↓
Build immutable Narrative Request Capsule
↓
Selected LLM receives PAQS-E strategy + narrative runtime prompt + frozen request evidence
↓
LLM returns final visible text
↓
Transport/text integrity checks only
↓
Persist immutable Narrative Run + Narrative Result
↓
Display exact persisted text safely
```

The LLM is responsible for the expert interpretation and prose analysis.

The application remains responsible for:

- exact Snapshot capture;
- As-Of/provenance boundaries;
- model/provider identity;
- strategy/prompt identity and hashes;
- credential security;
- research provenance;
- safe bounded transport;
- durable immutable audit evidence;
- safe rendering;
- no-auto-retry/no-auto-analysis behavior.

The application is **not** responsible for approving the semantic content of the narrative answer before showing it.

---

## 5. Preserve legacy structured PAQS-E history

Do not delete, rewrite or reinterpret any existing structured TASK-007B Decision Ledger data.

Keep existing tables and historical read behavior intact:

- `paqs_e_runtime_artifacts`;
- `paqs_e_analysis_runs`;
- `paqs_e_decisions`.

Do not modify:

- migration `0001_phase1_foundation.py`;
- migration `0002_task007b_paqs_e_decision_ledger.py`;
- immutable triggers or old rows;
- prior structured `request_payload_json` or `result_payload_json`;
- previous revision numbers;
- accepted review evidence.

Historical structured Decisions remain truthful historical artifacts produced by the superseded structured workflow.

Do not convert prose into fake `entry_advisory`, `setup_stage`, `market_bias`, `rr_t1` or other legacy fields.

---

## 6. New Narrative Ledger — migration 0003 is authorized

This remediation **does authorize one new additive migration**.

Expected migration head after implementation:

`0003_task007c1_narrative_ledger`

Exact revision identifier may follow repository naming conventions, but it must be a direct child of:

`0002_task007b_paqs_e_ledger`

No existing migration may be edited.

### 6.1 Narrative Runs

Add an append-only table conceptually equivalent to:

`paqs_e_narrative_runs`

Required evidence includes at minimum:

- canonical UUID id;
- `security_id` FK;
- symbol;
- market;
- instrument type;
- snapshot hash;
- snapshot As-Of timestamp;
- narrative request schema version;
- narrative output format/version identity;
- model provider;
- exact provider model id;
- strategy id;
- strategy content SHA-256;
- strategy artifact id or equivalent immutable artifact binding;
- narrative prompt version;
- narrative prompt content SHA-256;
- narrative prompt artifact id or equivalent immutable artifact binding;
- full canonical narrative request payload JSON;
- request payload SHA-256;
- terminal status;
- provider response id when safely available;
- bounded failure kind/reason when failed;
- started/completed/created timestamps.

The full canonical request payload must include the exact frozen market Snapshot and exact frozen auxiliary web-research context supplied to the model.

### 6.2 Narrative Results

Add an append-only table conceptually equivalent to:

`paqs_e_narrative_results`

Required fields include at minimum:

- canonical UUID id;
- narrative run id FK;
- security id;
- symbol/market/instrument identity;
- snapshot hash / As-Of;
- model provider/model id;
- strategy id / strategy SHA;
- prompt version / prompt SHA;
- narrative revision number;
- supersedes narrative result id;
- exact final response text;
- response-text SHA-256;
- response format/version identity;
- created timestamp.

A successful narrative Run has exactly one Narrative Result.

A failed narrative Run has no Narrative Result.

### 6.3 Narrative revision lineage

Narrative results use their own independent append-only lineage:

```text
security_id + strategy_id
```

Changing model/provider does not reset narrative revision numbering.

Do **not** interleave narrative revision numbers with legacy structured Decision revision numbers.

Example:

```text
Legacy structured Decisions:
AVGO + paqs-e-master: structured rev1, rev2

Narrative Results:
AVGO + paqs-e-master: narrative rev1, rev2, rev3
```

The UI must label them clearly enough that users do not mistake the two independent historical series.

### 6.4 Immutability

Narrative Run and Result tables must be append-only under SQLite in the same spirit as the accepted 007B ledger.

Add immutable UPDATE/DELETE protection and lineage checks where practical and tested.

Do not create secret fields.

---

## 7. New narrative request domain

Do not overload `PaqsEReasoningRequestV1` in a way that falsely claims the request expects `paqs-e-reasoning-result-v1`.

Introduce a distinct request identity, for example:

- `PAQS_E_NARRATIVE_REQUEST_SCHEMA_VERSION = "paqs-e-narrative-request-v1"`;
- `PAQS_E_NARRATIVE_OUTPUT_FORMAT_VERSION = "paqs-e-narrative-markdown-v1"`.

A narrative request must preserve:

- security/symbol/market/instrument identity;
- snapshot hash and As-Of;
- analysis mode = current analysis only;
- runtime policy identity needed for factual context;
- model provider/model id;
- strategy id and SHA;
- narrative prompt version and SHA;
- frozen market Snapshot;
- explicit ordered auxiliary context;
- web-research flag/capability outcome if useful to audit.

Do not add hidden conversation history or previous Decisions unless a future separate contract explicitly authorizes them as auxiliary context.

---

## 8. Narrative runtime prompt

Do not rewrite the accepted old structured runtime prompt in place.

Add a new resource, for example:

`src/ai_infra_quant/resources/paqs_e/runtime_prompt_narrative_v1.md`

with a new prompt-version identity.

The narrative prompt should instruct the model to:

- apply only the selected hash-identified PAQS-E primary strategy;
- use only the frozen market Snapshot and explicitly supplied auxiliary context;
- respect As-Of;
- treat Snapshot market facts as authoritative when discussing current/reference prices and completed bars;
- keep Context, Structure, Key Level, Location, Event, Transition, Setup, Trigger, Follow-through, Structural Invalidation, Structural Target, RR/entry quality and advisory reasoning conceptually distinct;
- state uncertainty and data limitations;
- avoid unsupported probability claims;
- avoid pretending the application knows the user's actual broker position;
- produce a concise but complete user-facing research report in Chinese by default unless the UI/user explicitly selects another language in a future task;
- use readable Markdown-like headings/bullets when useful;
- return only the final answer, not chain-of-thought;
- never output JSON merely to satisfy an application schema;
- never expose system/developer instructions, credentials or hidden reasoning.

The narrative prompt may recommend a stable report order such as:

```text
结论
市场结构与背景
关键位置
当前事件 / Setup / Trigger / Follow-through
入场质量与等待条件
结构失效
结构目标与风险回报
若已持有的条件性判断
风险 / 不确定性
下一步观察
```

This order is a writing guide, not a machine-enforced schema. Missing headings do not by themselves make the analysis fail.

Do not modify the PAQS-E strategy Markdown / Context-Free Master Spec semantic content in this task.

---

## 9. Narrative provider port

Introduce a provider-neutral narrative/text reasoning port rather than forcing free text through `ReasoningProviderSuccess(PaqsEReasoningResultV1)`.

Conceptually:

```text
PaqsENarrativeProvider
  reason_text(...)
    -> NarrativeProviderSuccess(text, provider_response_id)
    -> NarrativeProviderFailure(kind, reason)
```

Use existing provider/model registry and credential routing.

Reuse the bounded compatible HTTP transport where sensible.

Do not duplicate six provider implementations if the same OpenAI-compatible transport can serve them safely.

The old structured reasoning port/runtime may remain in the repository for legacy tests/history compatibility, but the normal UI must not invoke it for new analyses.

---

## 10. Provider request behavior — no structured output

For the new narrative reasoning request:

### Responses-style providers

Do not send JSON Schema structured-output requirements.

Specifically do not require:

- `text.format.type = json_schema`;
- `PaqsEReasoningResultSchemaV1`;
- strict schema names;
- structured-output schema bodies.

Use ordinary final text output.

Keep final reasoning tools disabled:

- `tools=[]` or provider-equivalent;
- no hidden web search during final reasoning;
- `store=false` where supported;
- no conversation / previous-response state;
- no background mode;
- no automatic retry middleware.

### Chat-completions-style providers

Do not send:

- `response_format=json_schema`;
- `response_format=json_object` solely to satisfy PAQS-E output structure.

Request ordinary assistant content.

Keep tools/search/thinking side-effects bounded according to the existing provider-specific no-hidden-search policy.

Provider-native reasoning/thinking may occur internally if the provider/model uses it, but chain-of-thought/reasoning traces must not be stored or displayed. Only final visible answer text is accepted.

---

## 11. Narrative success checks — transport/integrity only

Do not semantic-validate the narrative answer.

A provider success may be accepted when all of the following hold:

- provider request completed successfully;
- final answer text exists;
- text is a string;
- text is non-empty after trimming;
- response is not a provider refusal;
- provider envelope is not failed/cancelled/incomplete under the provider's documented semantics;
- no unexpected final reasoning tool call occurred;
- no credential secret appears in the retained response envelope/text;
- provider model identity matches the selected route when the provider supplies reliable model identity;
- provider response id, if retained, is bounded and safe;
- final text is within a documented local storage/display size bound.

Recommended local final-text bound for v1:

- maximum 100,000 Unicode characters.

A tighter bound is allowed if justified and tested; it must still be large enough for useful PAQS-E analysis.

Do not parse the narrative text as JSON.

Do not run `PaqsEReasoningResultSchemaV1.model_validate_json(...)`.

Do not run `validate_reasoning_result(...)` on the narrative text.

Do not invent a strategy judgment from transport failure.

---

## 12. Failure semantics

Use explicit narrative-provider failure categories sufficient to distinguish:

- configuration/missing credential;
- provider unavailable/network/quota/billing;
- provider refusal;
- incomplete/cancelled provider response;
- invalid/unsafe final text envelope.

Names may reuse safe existing `ReasoningFailureKind` values where semantically accurate, but `INVALID_STRUCTURED_OUTPUT` must not remain the normal label for narrative output because there is no structured-output contract.

If a new bounded failure enum/version is needed, add it without modifying historical stored legacy values.

Failure reasons must remain safe and not contain:

- API keys;
- full provider raw responses;
- model chain-of-thought;
- hidden prompts;
- arbitrary provider body dumps.

No automatic paid retry.

---

## 13. Web research remains separate and auditable

Keep Remediation 01 R2 architecture.

When `web_research=false`:

- no research provider/tool call occurs;
- final narrative reasoning receives empty web-research auxiliary context.

When `web_research=true` and the selected route supports accepted research:

- run the bounded research stage first;
- normalize and freeze verified evidence;
- if research fails, do not silently continue without research;
- final reasoning receives frozen `auxiliary_context[]`;
- final reasoning tools remain disabled.

Do not relax existing source provenance, As-Of or DeepSeek `search/open_page/find_in_page` protections.

The narrative answer may discuss web evidence, but the application should continue to expose frozen research evidence separately in audit/detail views so the user can distinguish sources from model prose.

---

## 14. Analyze API — narrative becomes the normal path

Introduce a bounded new normal endpoint:

`POST /api/v1/paqs-e/narrative-analyses`

Request remains conceptually:

```json
{
  "security_id": "<canonical UUID>",
  "model_key": "deepseek-v4-flash",
  "strategy_id": "paqs-e-master",
  "web_research": false
}
```

The browser must use this endpoint for all new Analyze actions.

Success returns a bounded Narrative Result representation including at minimum:

- narrative result id;
- narrative run id;
- security/symbol/market;
- snapshot hash / As-Of;
- model provider/model id;
- strategy id;
- narrative revision number;
- supersedes narrative result id;
- response text;
- response SHA-256;
- created time;
- terminal success status.

Add read endpoints sufficient for:

- retrieve a known narrative Run by id;
- retrieve a narrative Result by id;
- list recent narrative results for a Security with optional strategy filter.

Exact paths should be consistent and bounded.

### Legacy structured POST

The old strict structured `POST /api/v1/paqs-e/analyses` is superseded for normal product use.

Preferred behavior:

- remove its POST operation from the normal OpenAPI/UI path, or return a clear deprecation/disabled response;
- preserve existing GET read paths needed to inspect historical structured Runs/Decisions;
- do not allow the normal browser to accidentally spend money through the old structured path.

If retaining callable legacy POST is required solely for internal backward tests, it must be explicitly non-default, not invoked by UI, and documented as legacy. Prefer disabling it rather than maintaining two user-facing Analyze modes.

---

## 15. UI — narrative result is primary

Update the existing workbench rather than creating a new application.

The normal right-side Analyze controls remain:

```text
模型
[ DeepSeek V4 Flash ▼ ]

主策略
[ PAQS-E Context-Free Master Spec ▼ ]

[✓] 联网研究

凭据状态
[配置此模型 API Key]

[ Analyze · 分析当前快照 ]
```

Keep:

- one flat model selector;
- secure credential dialog;
- no provider selector;
- no automatic Analyze;
- one in-flight guard;
- R3 long-running wait notice without abort/retry.

### Narrative result rendering

Primary result display becomes a narrative report.

Display the exact persisted response text safely.

Preferred minimal rendering:

- use DOM `textContent` / escaped text;
- preserve newlines and readable whitespace (`white-space: pre-wrap` or equivalent);
- do not introduce unsafe HTML injection;
- do not require a Markdown parser dependency.

If Markdown rendering is added, it must be sanitized and tested against XSS, but plain escaped text is preferred for this remediation.

Show clear metadata around the text:

- model display name;
- strategy;
- snapshot time;
- narrative revision;
- whether web research was enabled;
- Run/Result ids in advanced audit.

Do not parse headings from the text into semantic application state.

### Narrative history

Make recent Narrative Results the primary success history.

History rows should show at minimum:

- created time;
- narrative revision;
- model display name;
- strategy id;
- a safe bounded preview of the first line or first N characters.

Selecting a historical narrative result must restore:

- exact persisted response text;
- exact frozen market request evidence;
- exact frozen research evidence;
- immutable model/strategy identity.

### Legacy structured history

Keep legacy structured Decisions accessible as clearly labeled historical/legacy evidence, preferably under a collapsed details section such as:

`Legacy structured Decisions (pre Narrative-first)`

Do not present an old structured Decision as if it were the latest narrative result.

---

## 16. Snapshot display remains deterministic application evidence

Removing structured semantic validation does not mean the application should stop displaying deterministic Snapshot facts.

The center/frozen evidence UI remains authoritative for:

- W1/D1/M30 bars;
- reference/current quote;
- market/session status;
- snapshot hash / As-Of;
- provider/data-quality evidence.

The narrative prose is an expert interpretation layered on top of that evidence.

If narrative prose conflicts with displayed Snapshot facts, do not silently rewrite the prose. The application may label the narrative as model-generated analysis and keep the frozen factual evidence visible for user comparison.

Do not add an automatic semantic correction layer in this remediation.

---

## 17. Structured validator status after supersession

The existing structured validator remains historical/legacy code and testable behavior.

Do not weaken or rewrite it merely because the normal analysis path no longer uses it.

Keep structured-domain tests green unless a bounded old-POST deprecation requires explicit test supersession.

The normal narrative path must not call:

- `PaqsEReasoningResultSchemaV1` for the final answer;
- `project_snapshot_price_facts(...)` as a prerequisite to narrative success;
- `validate_reasoning_result(...)` as a prerequisite to narrative success.

Legacy structured code may still use them.

---

## 18. Migration and upgrade tests

Required database tests:

1. fresh database upgrades from zero through new migration head;
2. database already at 0002 upgrades to 0003 without altering existing structured Runs/Decisions;
3. existing structured rows remain byte/value equivalent after upgrade;
4. narrative Run/Result insert succeeds under correct lineage;
5. narrative Result cannot exist for failed Run;
6. update/delete immutability is enforced;
7. revision chain is `security + strategy` and independent of provider/model;
8. structured and narrative revision numbering are independent;
9. no secret is persisted in new tables;
10. downgrade behavior, if repository policy requires it, removes only new narrative objects and never damages legacy tables.

Optional PostgreSQL smoke may remain conditional under the existing repository convention.

---

## 19. Provider tests

For every registered model route using deterministic fake transport boundaries, test:

- final reasoning request contains correct model/provider identity;
- no JSON Schema response format for narrative path;
- no JSON Object response format solely for PAQS-E schema;
- no final reasoning web tools;
- no conversation/background/previous-response hidden state;
- non-empty final text succeeds;
- ordinary prose with headings/bullets succeeds;
- prose containing braces/JSON-like fragments is still treated as text, not parsed;
- provider refusal fails;
- provider network/quota failure fails;
- incomplete/cancelled provider envelope fails;
- empty/oversized text fails safely;
- secret echo fails safely;
- reasoning traces are discarded;
- provider response id is retained safely when available;
- no automatic retry or model fallback occurs.

Include a DeepSeek Responses fixture with reasoning items plus a normal final `message/output_text` and prove the narrative path accepts the visible text without attempting JSON parsing.

---

## 20. Browser tests

Real browser tests must cover:

- exact flat model dropdown remains;
- credential workflow remains;
- web research toggle remains;
- no non-explicit action creates a narrative Analyze POST;
- Analyze posts only to the narrative endpoint;
- one-in-flight guard remains;
- >180-second wait notice does not abort/retry;
- successful prose is rendered verbatim/escaped;
- multiline text remains readable;
- `<script>`, `<img onerror>`, HTML and Markdown-like content remain inert unless a separately sanitized renderer is explicitly implemented;
- history lists narrative results;
- selecting history restores exact persisted text and frozen evidence;
- current market refresh does not alter historical narrative text or frozen evidence;
- provider failure keeps prior narrative result visibly historical;
- web-research failure creates no successful Narrative Result;
- legacy structured Decision history remains accessible but clearly legacy;
- dark/light and narrow/wide layouts remain usable.

---

## 21. Bounded supersession of older tests

This Contract authorizes only the test changes necessary to supersede the old normal strict-output workflow with narrative-first behavior.

Expected bounded changes include tests that previously required:

- `POST /paqs-e/analyses` as the only Analyze route;
- strict Pydantic result schema on every normal analysis;
- deterministic validator success before every user-visible successful result;
- structured Decision as the primary UI result/history.

Do not weaken unrelated tests for:

- Snapshot immutability;
- As-Of;
- credentials;
- source-revision handshake;
- no-auto-analysis;
- no-auto-retry;
- no broker/live trading;
- history race guards;
- XSS safety;
- Decimal/chart evidence;
- research provenance;
- model registry;
- provider identity;
- migrations/immutability.

The implementation report must enumerate every modified older test and the exact superseded assumption.

---

## 22. Documentation

Update only documentation necessary to explain the new product behavior:

- PAQS-E is narrative-first for new analyses;
- model output is displayed as model-generated expert analysis, not machine-validated trading instruction;
- Snapshot/research evidence remain auditable and separate;
- old structured Decisions are legacy history;
- new Narrative Results have independent revisions;
- no automatic retries/fallbacks;
- API keys remain local secure credentials;
- launcher source-revision handshake remains;
- migration head changes to the new 0003 narrative ledger;
- no broker/trading behavior.

Do not falsely claim that narrative prose is deterministically validated.

---

## 23. Protected content

Do not modify:

- `docs/phases/PHASE_1_PLAN.md`;
- `src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py`;
- `src/ai_infra_quant/database/migrations/versions/0002_task007b_paqs_e_decision_ledger.py`;
- accepted independent review evidence;
- original TASK-007A/007B/007C contracts;
- original TASK-007C1 Contract;
- Remediation 01 Contract;
- `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md`;
- registered PAQS-E primary strategy Markdown;
- legacy structured runtime prompt content.

A **new** narrative runtime prompt resource is authorized.

A **new** migration 0003 is authorized.

No force-push.

No merge by Codex.

---

## 24. Git preconditions

Before editing, Codex must verify:

```text
repository = ahhhhzzz/ai-infra-quant
current branch = task/007c1-paqs-e-multi-model-web-research
current HEAD = exact Remediation 02 Contract commit
Remediation 02 Contract parent = 6681fc6a934f44d29879c2ef1152891c3bd3a0d5
origin/roadmap/no-live-trading = 80f089bc2d285cca492c41aaeaf047e177bc2812
merge base with authoritative = 80f089bc2d285cca492c41aaeaf047e177bc2812
```

If any precondition is false, stop without implementation changes and report the mismatch.

Use an isolated clean checkout/worktree if needed.

Do not reset/stash/terminate unrelated work.

---

## 25. Required deterministic validation

Run and report at minimum:

```text
pytest focused narrative runtime/provider/ledger/API/browser tests
pytest full suite
ruff check .
ruff format --check .
mypy src tests
fresh SQLite alembic upgrade head
upgrade-from-0002 narrative migration regression
actual Uvicorn /health /openapi.json / root / configuration smoke
Windows launcher/source-revision tests
browser workbench suite
```

Confirm:

- migration head is the new 0003 narrative ledger;
- 0001/0002 hashes/content unchanged;
- accepted review evidence unchanged;
- strategy/master spec unchanged;
- no real secret/private artifact staged;
- no browser/database plaintext credential leakage;
- no broker/live-trading code added;
- task branch only is pushed;
- authoritative branch is untouched.

---

## 26. Live product acceptance gate

Ordinary automated tests must not require paid provider calls.

Final product acceptance of Narrative-first requires the user to execute on the exact final implementation SHA:

### Smoke A — reasoning only

```text
Model: DeepSeek V4 Flash
Web Research: OFF
One supported Security
One explicit Analyze
Expected:
- successful Narrative Run
- successful Narrative Result
- non-empty user-visible prose
- no structured-output or validator failure
```

### Smoke B — research + reasoning

```text
Model: DeepSeek V4 Flash
Web Research: ON
One supported Security
One explicit Analyze
Expected:
- bounded frozen web evidence
- successful Narrative Run
- successful Narrative Result
- persisted narrative text
```

Do not automatically repeat a paid smoke after ambiguous failure.

Record only safe evidence:

- exact code SHA;
- selected model;
- research on/off;
- terminal status;
- Run id;
- Result id;
- response SHA if useful;
- confirmation that frozen web evidence exists for Smoke B.

Never record or share the API key or provider chain-of-thought.

---

## 27. Explicit non-goals

This remediation does not implement:

- structured extraction from the narrative response;
- automatic parsing of Entry/Setup/RR from prose;
- semantic scoring/validator of prose;
- automatic trading;
- portfolio position awareness;
- broker connectivity;
- PAQS-Q;
- backtest/replay;
- model voting;
- simultaneous multi-model analysis;
- prompt editor;
- user-editable strategy;
- arbitrary model IDs;
- arbitrary provider URLs;
- model discovery marketplace;
- automatic provider fallback;
- retries;
- background jobs;
- public/multi-user deployment;
- mobile native app;
- storing API keys in SQLite/browser storage.

---

## 28. Stop condition and implementation report

Commit and push only:

`task/007c1-paqs-e-multi-model-web-research`

Do not merge.

Do not move `roadmap/no-live-trading`.

Stop for independent review.

The final implementation report must include:

1. authoritative SHA;
2. Remediation 02 Contract SHA;
3. final implementation SHA;
4. parent / merge-base / ahead-behind;
5. exact changed-file list;
6. narrative request/output version identities;
7. exact new migration revision and schema summary;
8. proof 0001/0002 unchanged;
9. narrative provider/runtime architecture;
10. proof normal final reasoning sends no strict JSON Schema/JSON Object requirement;
11. exact transport/text-only success checks;
12. failure semantics;
13. narrative ledger immutability/revision semantics;
14. Analyze API supersession;
15. UI/history supersession;
16. legacy structured history preservation;
17. every modified older test and replacement assertion;
18. focused/full/browser/lint/format/mypy/migration/Uvicorn/launcher results;
19. secret/protected-file audit;
20. live smoke evidence if performed, otherwise explicit statement that it remains user-executed acceptance evidence;
21. remaining limitations;
22. final branch HEAD and explicit no-merge confirmation.
