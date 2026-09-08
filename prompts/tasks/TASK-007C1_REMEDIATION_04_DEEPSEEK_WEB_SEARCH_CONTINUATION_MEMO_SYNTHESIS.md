# TASK-007C1 REMEDIATION 04 — DeepSeek Web Search Continuation + Memo Synthesis

Status: **APPROVED REMEDIATION CONTRACT — user-authorized remediation only**

Issued: 2026-09-08

Repository: `ahhhhzzz/ai-infra-quant`

Authoritative branch: `roadmap/no-live-trading`

Authoritative SHA at issuance: `80f089bc2d285cca492c41aaeaf047e177bc2812`

TASK-007C1 branch: `task/007c1-paqs-e-multi-model-web-research`

Exact remediation base / latest reviewed implementation SHA: `a9c7eabd1862d491f61843dfc68cbc3a1d9c936f`

Original TASK-007C1 Contract commit: `9f41016b2341e91ad2825b7f731bca4f378b0108`

Remediation 01 Contract commit: `b7316e83f7fd377f4c628db90dee8e3d7b4a5335`

Remediation 02 Contract commit: `ca1b71f94565dee02f0bd43d280a59f3ec15ac6d`

Remediation 03 Contract commit: `5285ed7d4553e7a9d3860b9263135d4d94b2f3e5`

Original Contract:
`prompts/tasks/TASK-007C1_PAQS_E_MULTI_MODEL_SECURE_CREDENTIALS_WEB_RESEARCH.md`

Remediation 01:
`prompts/tasks/TASK-007C1_REMEDIATION_01_LIVE_DOGFOOD_RUNTIME_COMPATIBILITY.md`

Remediation 02:
`prompts/tasks/TASK-007C1_REMEDIATION_02_NARRATIVE_FIRST_REASONING.md`

Remediation 03:
`prompts/tasks/TASK-007C1_REMEDIATION_03_NATIVE_RESEARCH_MEMO_SAFE_MARKDOWN.md`

This remediation is intentionally narrow. It preserves the successful Narrative-first reasoning path, the safe Markdown presentation, explicit research opt-in, the Narrative Ledger, and all permanent no-live-trading boundaries. It fixes only the remaining DeepSeek Research-ON compatibility blocker and adds bounded safe research diagnostics.

---

## 1. Accepted live evidence and current status

### 1.1 Narrative Research-OFF — LIVE PASS

On exact implementation SHA:

`74a19387adc408e9453c30fdbb30e6636ac4e695`

real local dogfooding for:

- Security: `US.AVGO`;
- provider: `deepseek`;
- model: `deepseek-v4-flash`;
- strategy: `paqs-e-master`;
- `web_research=false`;

produced a successful Narrative result.

Verified evidence:

- Narrative Run: `b45f2209-54ae-464a-80e4-651c2ffb40d6`;
- Narrative Result: `7db32fc2-fb2a-4849-8b84-cded2239079d`;
- status: `SUCCEEDED`;
- revision: `1`;
- provider response id: `c3fda397-5a60-479c-b326-6d11515caa6f`;
- response characters: `4043`;
- response SHA-256 verified true;
- request SHA-256 verified true;
- frozen auxiliary context count: `0`;
- elapsed time approximately 235 seconds without browser abort.

This path is protected. Do not redesign or replace it.

### 1.2 Remediation 03 — CODE / CONTRACT REVIEW PASS

Exact reviewed Remediation-03 implementation SHA:

`a9c7eabd1862d491f61843dfc68cbc3a1d9c936f`

Independent review branch:

`review/007c1-remediation-03-independent`

Independent review commit:

`8952e3cbd96f8588ab18cd82badb845baff6f998`

Remediation 03 successfully implemented:

- provider-native DeepSeek research memo normalization;
- safe local Narrative Markdown rendering with exact raw-text view;
- web research default OFF / explicit opt-in.

No code/contract blocker was found in those changes.

### 1.3 DeepSeek Research-ON — LIVE FAIL remains

On exact SHA:

`a9c7eabd1862d491f61843dfc68cbc3a1d9c936f`

the user explicitly enabled web research for:

- `US.AVGO`;
- DeepSeek V4 Flash;
- `paqs-e-master`.

The product again returned:

`PAQS_E_RESEARCH_PRECONDITION_FAILED`

with:

`Requested web research could not produce a complete auditable capsule.`

No Narrative Run/Result was fabricated. This is correct fail-closed behavior.

The remaining blocker is therefore isolated to DeepSeek research lifecycle compatibility, before final Narrative reasoning.

Current task status:

```text
Narrative final text / research OFF    LIVE PASS
Narrative Ledger                        LIVE PASS
Long-running non-abort guard            LIVE PASS
Safe Markdown                           CODE PASS
Research explicit opt-in/default OFF    CODE PASS
DeepSeek research ON                    LIVE FAIL
Final TASK-007C1 PASS                   BLOCKED
Merge                                   BLOCKED
```

---

# PART A — CURRENT PROVIDER CONTRACT BASIS

## 2. DeepSeek Responses semantics verified for this remediation

As of issuance, current official DeepSeek Responses API documentation establishes the following relevant behavior for `deepseek-v4-flash` / `deepseek-v4-pro`:

1. Responses API is stateless.
2. `previous_response_id` is not supported.
3. Multi-turn use requires the client to send the needed conversation/input history again.
4. `web_search` / `web_search_2025_08_26` are supported server-side tools.
5. A provider response can contain `web_search_call` output items.
6. `web_search_call` is also a supported input-item type.
7. Official compatibility guidance states that a `web_search_call` may be passed back as-is and the server restores the associated search results.
8. Server-side web-search auto-continuation is capped at 10 rounds.
9. The 10-round cap is a provider execution-round limit, not a documented guarantee that the final `response.output` list contains at most 10 `web_search_call` items.
10. `reasoning.effort = "none"` is supported and disables thinking mode.
11. `tool_choice = "none"` is supported for a tool-free synthesis request.
12. `max_output_tokens` includes visible output and reasoning tokens.

Implementation and tests must follow the official semantics above rather than infer an undocumented output-item count contract from the 10-round server-side continuation limit.

Do not use `previous_response_id`, `conversation`, background mode, or provider-side stored state.

---

## 3. R04 supersession scope

This Contract supersedes only the following Remediation-03 assumptions for DeepSeek research:

- research must complete in exactly one application HTTP request;
- a completed first Responses call must itself contain the final memo;
- `<=10` server-side continuation rounds implies `<=10` returned `web_search_call` output items.

For DeepSeek only, this remediation authorizes at most **two bounded research-stage provider HTTP requests**:

1. native web-search request;
2. optional tool-free memo-synthesis continuation request, used only when the first response does not already contain an acceptable final research memo.

The existing final PAQS-E Narrative reasoning remains a third, separate tool-free provider request after the frozen research capsule is complete.

Therefore a user-authorized Research-ON analysis may use:

```text
minimum: 1 research request + 1 final Narrative request = 2 provider requests
maximum: 2 research requests + 1 final Narrative request = 3 provider requests
```

No retries are authorized beyond this deterministic two-stage research lifecycle.

---

# PART B — DEEPSEEK RESEARCH STATE MACHINE

## 4. Required lifecycle

For `provider_id == "deepseek"` and `web_research=true`:

```text
Explicit user opt-in
↓
Freeze immutable Snapshot
↓
SEARCH request #1
  DeepSeek Responses + native web_search
↓
Validate completed search envelope and capture safe search-call items
↓
If one acceptable final memo already exists:
  normalize/freeze memo directly
Else if search completed but response is tool-only:
  SYNTHESIS request #2
  pass accepted web_search_call items back as-is
  tools disabled
  ask only for factual research memo
↓
Validate synthesis final memo
↓
Normalize/freeze auxiliary_context
↓
Build immutable NarrativeRequest
↓
Final PAQS-E Narrative reasoning
  unchanged existing NarrativeGateway
  tools=[] / tool_choice=none
↓
Persist Narrative Run + Result atomically
```

If any research-stage requirement fails:

- do not call final Narrative reasoning;
- do not create a Narrative Run/Result;
- do not silently continue without research;
- do not retry automatically;
- preserve prior successful Narrative in the UI.

---

## 5. SEARCH request #1

Use the registered DeepSeek model and fixed registered DeepSeek Responses research endpoint.

Required request behavior:

- exactly one HTTP request for SEARCH;
- same selected DeepSeek model as the final analysis route;
- same configured secure credential;
- `stream=false`;
- `store=false` may remain for compatibility even though DeepSeek is stateless;
- `reasoning={"effort":"none"}`;
- `tools=[{"type":"web_search"}]`;
- force native search with supported provider-equivalent tool choice, preferably `tool_choice={"type":"web_search"}`; `required` is acceptable only if tests prove it cannot select an unintended tool because no other tool exists;
- no function/custom/other tools;
- bounded `max_output_tokens`, no higher than the existing 6000 unless a smaller value is justified;
- no `previous_response_id`;
- no `conversation`;
- no background mode;
- no automatic retry;
- no app-side pagination/loop;
- no second SEARCH request.

SEARCH instructions must request factual company/news/earnings/public-event context only, bounded to the selected Security and Snapshot As-Of cutoff.

SEARCH must not ask for PAQS-E trading analysis.

SEARCH must not request chain-of-thought.

SEARCH must state that Snapshot market facts take precedence over web prices.

---

## 6. SEARCH response acceptance

The first provider response may be accepted as a valid search-stage envelope when:

- top-level response is a dict/object;
- provider status is `completed`;
- no top-level error exists;
- model identity matches the selected model when supplied;
- safe response id is present or null;
- credential secret is absent from retained/processed response content;
- `output` is a bounded list;
- at least one completed `web_search_call` exists;
- at least one completed `web_search_call.action.type == "search"` exists;
- every accepted web-search action type is one of:
  - `search`;
  - `open_page`;
  - `find_in_page`;
- unknown tool/output item types fail closed unless explicitly allowed below;
- provider refusal fails closed;
- failed/incomplete/cancelled search action fails closed.

Reasoning items, if unexpectedly returned despite `reasoning.effort=none`, must never be stored, displayed, logged, hashed into user-visible evidence, or passed into the final Narrative request.

They may be ignored for validation. Do not rely on their content.

---

## 7. Do not equate 10 rounds with 10 output items

Remove the DeepSeek-specific R03 rejection rule that fails solely because more than 10 `web_search_call` items are present.

A response with 11 completed allowed `web_search_call` items must not fail merely because the count is 11.

Use local structural safety bounds instead:

- maximum 64 `web_search_call` output items;
- maximum 128 total response output items;
- existing transport response cap remains 2 MB;
- maximum four provider-exposed search query strings retained in provenance;
- maximum 64 raw source/citation records retained/processed for provenance.

These are local parsing/storage safety bounds, not claims about provider server-side continuation rounds.

If provider output exceeds these local structural bounds, fail closed with safe diagnostics.

---

## 8. Direct memo fast path

If SEARCH response #1 already contains exactly one acceptable completed assistant message with exactly one bounded non-empty final factual memo text:

- use that final memo directly;
- do not issue SYNTHESIS request #2;
- normalize/freeze the memo under the existing provider-native research memo semantics;
- set provenance `synthesis_used=false`;
- set `research_http_request_count=1`;
- continue to unchanged final Narrative reasoning.

This preserves cost efficiency when DeepSeek already produces the final memo in the search response.

A direct final memo must satisfy the same final memo integrity/bounds as a synthesized memo.

---

## 9. Tool-only continuation trigger

If SEARCH response #1:

- is otherwise valid and completed;
- contains at least one valid completed search action;
- contains no acceptable final assistant memo message;

then and only then issue exactly one SYNTHESIS request #2.

Do not treat absence of a message as immediate research failure if the native search operation completed successfully.

Do not issue SYNTHESIS if the SEARCH response was failed, incomplete, refused, malformed, secret-tainted, wrong-model, or lacked a real search action.

---

# PART C — PASS-BACK CONTINUATION

## 10. Safe web_search_call pass-back

For SYNTHESIS request #2, use official stateless pass-back semantics.

The continuation input must reconstruct only the minimum required safe context:

1. the original bounded research intent/user message;
2. the accepted completed DeepSeek `web_search_call` output items from SEARCH response #1, passed back **as-is** as supported input items;
3. one final user message instructing the model to synthesize a concise factual research memo from the restored search results.

Do not use `previous_response_id`.

Do not use `conversation`.

Do not assume provider-side persistent state.

Do not create or fabricate `web_search_call` items.

Do not rewrite the provider `web_search_call` item contents before pass-back except that an implementation may deep-copy the object for isolation.

The exact pass-back items are in-memory transport material only. They must not be persisted as raw provider-response dumps.

Before pass-back, enforce:

- item is a dict/object;
- `type == "web_search_call"`;
- item status is completed;
- action is an object;
- action type is one of `search/open_page/find_in_page`;
- total serialized pass-back material is bounded under the existing 2 MB response and request constraints;
- credential secret is absent.

Do not pass back reasoning items.

Do not pass back arbitrary message text from SEARCH when the tool-only path is used.

---

## 11. SYNTHESIS request #2

SYNTHESIS is research summarization, not final PAQS-E reasoning.

Required behavior:

- exactly one HTTP request;
- same registered DeepSeek endpoint/model/credential;
- `stream=false`;
- `store=false` may remain;
- `reasoning={"effort":"none"}`;
- `tools=[]`;
- `tool_choice="none"` or provider-equivalent explicit no-tool setting;
- bounded `max_output_tokens`, recommended 4000 or less if sufficient;
- no `previous_response_id`;
- no `conversation`;
- no background mode;
- no retry;
- no web-search tool available in this request;
- no function/custom tools;
- no PAQS-E strategy Markdown;
- no PAQS-E final Narrative runtime prompt.

SYNTHESIS instructions must require:

- one concise factual research memo;
- use only the restored native search results and original intent;
- respect the Snapshot As-Of cutoff requested during search;
- do not claim current web prices override Snapshot facts;
- do not output chain-of-thought;
- do not produce trading advice or PAQS-E Setup/Trigger/entry analysis;
- do not output application JSON merely to satisfy a schema.

---

## 12. SYNTHESIS response acceptance

A SYNTHESIS response succeeds only when:

- top-level status is `completed`;
- no top-level error exists;
- model identity matches selected route when supplied;
- safe response id is valid or null;
- no credential secret appears;
- no provider refusal occurs;
- no function/tool/web-search call occurs;
- exactly one final assistant message exists;
- exactly one final visible text is extracted;
- final memo is non-empty after trimming;
- final memo is valid UTF-8;
- final memo contains no forbidden control characters;
- final memo is at most 24,000 Unicode characters;
- total frozen auxiliary capsule remains within the existing 24,000-character/serialized-size policy after provenance and label are included, or a clearly documented equivalent bound consistent with existing Narrative request constraints.

Do not parse the memo as JSON.

Do not semantic-validate memo content as a PAQS-E result.

Do not store provider reasoning traces.

---

# PART D — RESEARCH PROVENANCE AND EVIDENCE

## 13. Frozen memo remains one auxiliary context item

Continue using the existing Narrative auxiliary-context representation.

Preferred representation:

```text
category = web_research
source_label = DeepSeek native web research memo
content = exact accepted factual research memo
source_timestamp = null unless one authoritative memo-level timestamp exists
as_of_compatible = true with explicit limitation
provenance = bounded canonical JSON
```

The final Narrative request must freeze this item before calling `NarrativeGateway.reason_text(...)`.

The final Narrative provider must remain tool-free and must receive the frozen memo as part of `auxiliary_context`.

---

## 14. Required provenance metadata

DeepSeek memo provenance must include bounded safe metadata sufficient to audit whether one- or two-stage research was used.

Include at minimum:

- provider id;
- exact model id;
- Snapshot As-Of cutoff;
- original bounded research intent;
- research retrieval/start timestamp(s) as currently available;
- SEARCH provider response id when safely available;
- `search_response_status`;
- total `web_search_call_count`;
- `search_action_count`;
- ordered accepted action types;
- provider-exposed bounded queries when actually available;
- safe native source/citation URLs when actually exposed and validated;
- known valid publication timestamps when exposed;
- excluded future citation/source count;
- `synthesis_used` boolean;
- SYNTHESIS provider response id when safely available;
- `research_http_request_count` equal to 1 or 2;
- explicit provenance limitation.

Retain the existing limitation concept:

> Provider-native web research memo. Source URLs and/or publication times were not fully exposed by the provider response; cutoff compliance was requested but cannot be independently verified for every memo statement. Frozen Snapshot market facts take precedence.

Equivalent concise wording is allowed.

Do not fabricate query strings, URLs, source titles, timestamps, or memo-level publication dates.

Do not infer URLs from memo prose.

---

## 15. Native source validation remains

When source/citation records are exposed in SEARCH response #1, preserve R03 safety rules:

- maximum 64 raw source/citation records;
- URL maximum 1000 characters;
- only `http` / `https`;
- no embedded username/password;
- no whitespace/control/backslash-smuggled URL;
- syntactically valid hostname/port;
- deduplicate only after raw-count enforcement;
- publication timestamp retained only when timezone-aware and parseable;
- known future-dated sources excluded from trusted provenance;
- future source exclusion does not by itself destroy an otherwise valid provider-native memo;
- arbitrary URLs occurring only in memo prose never become trusted citations.

---

# PART E — SAFE RESEARCH FAILURE DIAGNOSTICS

## 16. Current diagnostic problem

The current user-visible research failure collapses all research compatibility failures to:

`Requested web research could not produce a complete auditable capsule`

This is insufficient for live provider acceptance because it does not reveal whether failure occurred at:

- SEARCH transport;
- SEARCH envelope validation;
- missing search action;
- tool-only response requiring synthesis;
- SYNTHESIS transport;
- SYNTHESIS completion;
- final memo integrity.

R04 authorizes bounded safe diagnostic metadata without persisting raw provider responses.

---

## 17. ResearchFailure diagnostic extension

`ResearchFailure` may be extended with a provider-neutral bounded diagnostic object or equivalent immutable safe fields.

Allowed diagnostic fields include:

- `stage`: one of `SEARCH`, `SYNTHESIS`;
- `failure_class`: bounded application enum/string;
- `provider_id`;
- `model_id`;
- `provider_status` when safely available;
- `provider_response_id` when safely available;
- `web_search_call_count` integer;
- `search_action_count` integer;
- `message_count` integer;
- `synthesis_attempted` boolean;
- `research_http_request_count` integer;
- `incomplete_reason` only when it is a short provider enum/value such as `max_output_tokens` / `content_filter`, maximum 80 characters and strict character whitelist;
- `detail_version`, e.g. `paqs-e-research-diagnostic-v1`.

Do not include:

- raw provider response;
- provider message/memo text;
- source article body;
- reasoning text;
- chain-of-thought;
- hidden prompt/instructions;
- API key;
- Authorization header;
- arbitrary provider exception body;
- request body dump;
- user secrets.

Diagnostic values must be fixed/bounded/sanitized before returning through API or logs.

---

## 18. API failure projection

The existing `PAQS_E_RESEARCH_PRECONDITION_FAILED` API contract remains.

When safe diagnostic metadata exists, add it under a bounded extra field such as:

```json
{
  "research_diagnostic": {
    "detail_version": "paqs-e-research-diagnostic-v1",
    "stage": "SEARCH",
    "failure_class": "TOOL_ONLY_REQUIRES_SYNTHESIS",
    "provider_status": "completed",
    "web_search_call_count": 11,
    "search_action_count": 4,
    "message_count": 0,
    "synthesis_attempted": true,
    "research_http_request_count": 2
  }
}
```

The exact failure classes may differ, but they must be stable, bounded, and test-covered.

Do not add a database migration merely to store failed precondition diagnostics.

Research precondition failure still creates no Narrative Run/Result.

The browser may show a concise safe diagnostic suffix/detail in the failure state so a live user can report the exact stage/counts without running SQLite or exposing provider payloads.

---

# PART F — COST AND EXPLICIT USER INTENT

## 19. Research remains default OFF

Preserve Remediation-03 behavior exactly:

- initial checkbox unchecked;
- selecting DeepSeek keeps it unchecked;
- selecting another model resets it unchecked;
- unsupported model disables it unchecked;
- reload does not remember opt-in;
- no localStorage/sessionStorage/cookie persistence;
- only explicit user check may submit `web_research=true`.

Do not regress this behavior.

---

## 20. Cost disclosure update

Update the concise user-facing research disclosure to reflect the new bounded lifecycle.

It should communicate in Chinese that:

- research is optional and default OFF;
- enabling it may make up to two additional research requests before the final analysis;
- it may increase latency and API cost.

Do not expose implementation jargon such as `web_search_call`, continuation item, Responses state machine, or pass-back in the normal control label.

---

# PART G — PROTECTED COMPONENTS

## 21. Do not modify already accepted behavior

This remediation must not alter:

- PAQS-E Context-Free Master Spec;
- PAQS-E Doctrine;
- Narrative runtime prompt semantic content;
- successful Narrative final-text provider path;
- `NarrativeGateway.reason_text(...)` request/acceptance semantics except an internal refactor proven byte/behavior equivalent;
- Narrative request schema version;
- Narrative output format version;
- Narrative Ledger schema;
- Narrative revision lineage;
- Narrative response text/hash semantics;
- request hash semantics;
- migrations 0001/0002/0003;
- database migration head `0003_task007c1_narrative_ledger`;
- legacy structured validator;
- legacy structured runtime schema;
- legacy historical read behavior;
- secure Credential Manager architecture;
- model registry/model list;
- provider endpoints;
- stale-backend source revision handshake;
- long-running non-aborting Analyze guard;
- safe Markdown implementation and raw-view audit semantics;
- no-live-trading/product boundary;
- Snapshot construction;
- market-data provider behavior.

No 0004 migration is authorized.

No model/provider addition is authorized.

No PAQS-Q/backtest/portfolio/PnL/broker/execution scope is authorized.

---

## 22. Other providers remain unchanged

OpenAI and Alibaba/Qwen research behavior must remain as implemented before R04.

Do not apply the DeepSeek pass-back/synthesis lifecycle to all providers.

Do not reduce existing provenance guarantees for other providers.

A tiny shared helper refactor is allowed only if behavior remains identical and tests prove it.

---

# PART H — TEST REQUIREMENTS

## 23. DeepSeek lifecycle unit tests

Add deterministic tests proving at minimum:

1. SEARCH response with one search action and one final memo succeeds with exactly one research HTTP request.
2. SEARCH response with 11 completed `web_search_call` items and a final memo succeeds; it must not fail solely due to count 11.
3. SEARCH response with 11 completed allowed `web_search_call` items and **no final message** triggers exactly one SYNTHESIS request.
4. Tool-only SEARCH + successful SYNTHESIS returns one frozen memo.
5. SYNTHESIS input contains the original bounded research intent.
6. SYNTHESIS input passes accepted `web_search_call` items back as-is.
7. SYNTHESIS input does not contain `previous_response_id`.
8. SYNTHESIS input does not contain `conversation`.
9. SYNTHESIS uses `tools=[]` and explicit `tool_choice=none` or equivalent.
10. SEARCH uses `reasoning.effort=none`.
11. SYNTHESIS uses `reasoning.effort=none`.
12. SEARCH permits 11 action items.
13. More than 64 `web_search_call` items fails closed.
14. More than 128 total output items fails closed.
15. SEARCH with no real `search` action fails closed.
16. SEARCH unknown action type fails closed.
17. SEARCH wrong model/unsafe id/secret echo fails closed.
18. SEARCH incomplete/cancelled/failed/refusal fails closed.
19. Tool-only SEARCH never falls through directly to final Narrative without SYNTHESIS.
20. SYNTHESIS network error fails without retry.
21. SYNTHESIS incomplete/failed/refusal fails without retry.
22. SYNTHESIS unexpected tool call fails closed.
23. SYNTHESIS missing/empty/multiple final messages fails closed.
24. SYNTHESIS oversize memo fails closed.
25. Direct memo fast path does not issue SYNTHESIS.
26. R04 never performs more than two research-stage HTTP requests per explicit Analyze.
27. No automatic retry occurs after either stage.
28. Reasoning items are not persisted or included in frozen auxiliary context.
29. Safe provenance identifies one-stage vs two-stage research.
30. Safe diagnostic object never contains memo text, raw response, secret, hidden prompt, or reasoning.

---

## 24. Integration tests

Add integration tests proving:

- Research-OFF still uses zero research requests and unchanged final Narrative path;
- Research-ON direct-memo path freezes non-empty auxiliary context then invokes final Narrative;
- Research-ON tool-only path uses two research-stage calls then one final Narrative call;
- maximum provider call count for tool-only successful Research-ON = 3 total;
- final Narrative call remains `tools=[]` and receives the frozen memo;
- successful Narrative request payload/hash readback remains valid;
- successful Narrative response/hash readback remains valid;
- research failure at SEARCH creates no Narrative Run/Result;
- research failure at SYNTHESIS creates no Narrative Run/Result;
- prior successful Narrative remains unchanged;
- diagnostics are returned only in safe API failure metadata;
- existing migration head remains 0003;
- no migration/schema mutation occurs.

---

## 25. Browser tests

Preserve all R03 safe Markdown and explicit-opt-in tests.

Add/adjust browser tests proving:

- research checkbox remains default OFF;
- user explicitly checks research before Research-ON POST;
- cost disclosure mentions possible additional research requests/cost without implementation jargon;
- safe research diagnostic fields may be displayed in bounded form after a synthetic research failure;
- raw diagnostic JSON/provider body is never rendered;
- failure does not trigger automatic retry;
- prior successful Narrative remains selected/visible after research failure;
- no model/security/refresh/history/credential event dispatches Analyze;
- Markdown formatted/raw behavior is unchanged.

---

## 26. Regression tests for the exact observed risk

Create a deterministic fixture representing the compatibility shape motivating R04:

```text
response.status = completed
response.model = deepseek-v4-flash
output:
  web_search_call x 11
  no message
```

At least one of the 11 calls must be `action.type=search`; remaining allowed calls may be `open_page/find_in_page`.

The test must prove:

- this response is not rejected merely because there are 11 calls;
- it enters SYNTHESIS exactly once;
- the accepted web_search_call items are passed back as input items;
- SYNTHESIS has no tools;
- successful synthesis freezes a memo;
- final Narrative runs afterward;
- no raw search response is persisted.

Also test a direct-memo response with 11 calls to prove SYNTHESIS is skipped when unnecessary.

---

# PART I — REQUIRED VALIDATION

## 27. Deterministic validation before handoff

At minimum run:

- full pytest suite;
- full browser suite;
- focused DeepSeek SEARCH/SYNTHESIS tests;
- focused Narrative provider tests;
- focused Narrative API/Ledger tests;
- focused research failure/diagnostic tests;
- focused source-revision launcher tests;
- R03 safe Markdown/XSS tests;
- R03 explicit research-opt-in tests;
- Ruff check;
- Ruff format check;
- mypy;
- fresh SQLite migration/health smoke confirming head remains exactly `0003_task007c1_narrative_ledger`;
- real local Uvicorn/OpenAPI/root/configuration smoke using synthetic/no-paid provider behavior;
- secret/private-artifact audit;
- protected-file hash/diff audit.

Ordinary automated tests must not call a real paid provider.

---

# PART J — LIVE ACCEPTANCE

## 28. Final user-executed live gate

After independent code/contract review passes on an exact implementation SHA, perform one user-authorized paid live Research-ON acceptance using:

- exact reviewed implementation SHA;
- Security: `US.AVGO` unless unavailable;
- model: DeepSeek V4 Flash;
- strategy: `paqs-e-master`;
- explicit `web_research=true`.

No additional Research-OFF paid smoke is required unless R04 modified the protected Research-OFF final Narrative path.

Before the paid call confirm:

- `/health.source_revision` equals exact reviewed SHA;
- migration head is still `0003_task007c1_narrative_ledger`;
- research checkbox initially OFF;
- user manually opts in.

The live gate passes only if:

1. no `PAQS_E_RESEARCH_PRECONDITION_FAILED` occurs;
2. final Narrative returns `SUCCEEDED`;
3. a new Narrative Result is durably persisted;
4. AVGO narrative revision increments from the prior Narrative revision where applicable;
5. `web_research=true` in persisted Run/Result identity;
6. frozen `auxiliary_context` is non-empty;
7. frozen research item content is non-empty;
8. provenance contains provider/model and one-stage/two-stage research metadata;
9. request payload SHA verifies;
10. response text SHA verifies;
11. no secret/reasoning/raw response appears in persisted evidence;
12. final Narrative remains tool-free.

If live research fails again:

- do not automatically retry;
- capture the safe `research_diagnostic` metadata from the UI/API;
- stop for evidence-based review;
- do not merge.

---

# PART K — IMPLEMENTATION REPORT AND STOP CONDITIONS

## 29. Required implementation report

Create:

`docs/TASK_007C1_REMEDIATION_04_IMPLEMENTATION_REPORT.md`

The report must include:

1. exact starting SHA;
2. exact Contract commit;
3. final implementation SHA;
4. parent SHA of final implementation commit;
5. authoritative SHA and merge base;
6. ahead/behind state;
7. complete changed-file list;
8. exact DeepSeek SEARCH request shape;
9. exact direct-memo fast-path behavior;
10. exact tool-only continuation trigger;
11. exact SYNTHESIS request shape;
12. pass-back semantics and proof no `previous_response_id`/conversation is used;
13. local action/output safety bounds;
14. safe diagnostics schema/fields;
15. proof no raw provider body/reasoning/secret is persisted;
16. cost/request-count bound;
17. proof Research-OFF protected path remains unchanged;
18. proof R03 Markdown/default-OFF behavior remains unchanged;
19. proof migrations 0001/0002/0003 unchanged and head remains 0003;
20. proof Narrative Ledger/schema unchanged;
21. proof strategy/Narrative prompt/legacy validator unchanged;
22. all deterministic test/lint/type/startup results;
23. any older test supersession and why;
24. explicit statement that no paid live provider call was made by Codex;
25. explicit statement that no merge occurred.

---

## 30. Forbidden changes

Do not:

- merge the task branch;
- force-push;
- move authoritative branch;
- add a migration;
- edit migrations 0001/0002/0003;
- alter the Narrative Ledger schema;
- alter PAQS-E strategy semantics;
- alter Narrative runtime prompt semantics;
- alter legacy validator semantics;
- add provider/model fallback;
- add automatic retry;
- add background jobs/polling;
- add hidden web search to final Narrative reasoning;
- add new models/providers;
- add broker/trading/order/execution behavior;
- add PAQS-Q/backtest/portfolio scope;
- persist raw DeepSeek provider responses;
- persist/pass/display reasoning or chain-of-thought;
- use `previous_response_id` or conversation state;
- infer trusted sources from arbitrary memo prose.

---

## 31. Completion condition

Implementation is complete only when:

- all R04 deterministic validation passes;
- task branch is pushed only to `task/007c1-paqs-e-multi-model-web-research`;
- final SHA is reported;
- implementation report is committed;
- authoritative branch remains unchanged;
- Codex stops for independent review;
- no live paid provider acceptance is claimed unless the user executes it separately.

Final TASK-007C1 PASS and merge remain gated on:

1. independent review of exact final implementation SHA;
2. successful user-executed DeepSeek Research-ON live acceptance;
3. final branch/SHA/topology verification;
4. explicit fast-forward integration only after PASS.
