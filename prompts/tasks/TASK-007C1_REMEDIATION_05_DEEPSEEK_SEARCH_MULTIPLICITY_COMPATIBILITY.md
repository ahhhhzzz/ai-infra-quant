# TASK-007C1 REMEDIATION 05 — DeepSeek Provider-Owned Search Multiplicity Compatibility

Status: **APPROVED REMEDIATION CONTRACT — user-authorized remediation only**

Issued: 2026-09-08

Repository: `ahhhhzzz/ai-infra-quant`

Authoritative branch: `roadmap/no-live-trading`

Authoritative SHA at issuance: `80f089bc2d285cca492c41aaeaf047e177bc2812`

TASK-007C1 branch: `task/007c1-paqs-e-multi-model-web-research`

Exact remediation base / latest reviewed implementation SHA: `a82340db89be0e2a47583b03f97fb28218dd7a09`

Original TASK-007C1 Contract commit: `9f41016b2341e91ad2825b7f731bca4f378b0108`

Remediation 01 Contract commit: `b7316e83f7fd377f4c628db90dee8e3d7b4a5335`

Remediation 02 Contract commit: `ca1b71f94565dee02f0bd43d280a59f3ec15ac6d`

Remediation 03 Contract commit: `5285ed7d4553e7a9d3860b9263135d4d94b2f3e5`

Remediation 04 Contract commit: `e6fe791a5c99033da77a8bc877e772e0c84f55df`

Original Contract:
`prompts/tasks/TASK-007C1_PAQS_E_MULTI_MODEL_SECURE_CREDENTIALS_WEB_RESEARCH.md`

Remediation 01:
`prompts/tasks/TASK-007C1_REMEDIATION_01_LIVE_DOGFOOD_RUNTIME_COMPATIBILITY.md`

Remediation 02:
`prompts/tasks/TASK-007C1_REMEDIATION_02_NARRATIVE_FIRST_REASONING.md`

Remediation 03:
`prompts/tasks/TASK-007C1_REMEDIATION_03_NATIVE_RESEARCH_MEMO_SAFE_MARKDOWN.md`

Remediation 04:
`prompts/tasks/TASK-007C1_REMEDIATION_04_DEEPSEEK_WEB_SEARCH_CONTINUATION_MEMO_SYNTHESIS.md`

This remediation is intentionally narrow. It preserves the Remediation-04 SEARCH → optional SYNTHESIS → final Narrative state machine and fixes only the remaining DeepSeek compatibility rejection caused by application-owned search/query multiplicity assumptions. It also extends safe diagnostics so any remaining parser boundary is observable without exposing provider bodies, model reasoning, prompts, credentials, or research memo text.

---

## 1. Accepted live evidence and current blocker

### 1.1 Existing accepted live evidence remains authoritative

Research-OFF Narrative-first remains accepted from the previously verified real DeepSeek V4 Flash run:

- Security: `US.AVGO`;
- provider: `deepseek`;
- model: `deepseek-v4-flash`;
- strategy: `paqs-e-master`;
- `web_research=false`;
- successful immutable Narrative Run/Result;
- request SHA verified;
- response SHA verified;
- response length 4043 characters;
- elapsed time approximately 235 seconds without browser abort.

Do not redesign this path.

Remediation-03 safe Markdown and explicit research default-OFF behavior remain accepted code behavior.

Remediation-04 code/contract review passed at:

`a82340db89be0e2a47583b03f97fb28218dd7a09`

The remaining blocker is exclusively DeepSeek Research-ON live acceptance.

### 1.2 Exact new live evidence from Remediation 04

On exact implementation SHA:

`a82340db89be0e2a47583b03f97fb28218dd7a09`

with:

- Security: `US.AVGO`;
- provider/model: DeepSeek V4 Flash;
- strategy: `paqs-e-master`;
- user explicitly enabled web research;

real product execution returned:

```text
PAQS_E_RESEARCH_PRECONDITION_FAILED
研究诊断：SEARCH / INVALID_RESPONSE；请求 1，研究动作 20，搜索 6，消息 0。
```

This is safe live evidence that:

- the DeepSeek SEARCH request reached the provider;
- the provider returned a response far enough to count native tool outputs;
- the response contained `20` accepted `web_search_call`-shaped action records at the diagnostic boundary;
- `6` of those actions were native `search` actions;
- no final message was present;
- failure occurred in SEARCH parsing/validation before SYNTHESIS request #2;
- no Narrative Run/Result was fabricated.

### 1.3 Most likely application-owned rejection

At the current exact SHA, the DeepSeek SEARCH parser still performs:

```python
queries.extend(values)
if len(queries) > 4:
    raise ValueError("Query count")
```

Therefore a normal provider-owned execution with more than four exposed search queries can be rejected after the provider has already completed those searches.

The live diagnostic does not expose `provider_exposed_query_count`, so this Contract does **not** claim that the `>4` query check is proven as the only possible failure cause. However:

- `search_action_count=6` is live observed;
- the current parser contains a `len(queries) > 4` hard rejection;
- the failure class is SEARCH / INVALID_RESPONSE;
- the response never reached SYNTHESIS;

so the existing query multiplicity rule is incompatible with the observed provider-owned search behavior and must be removed as a normal acceptance blocker.

This remediation also adds enough numeric diagnostics to identify any remaining source/action/query boundary without further guessing.

---

## 2. Product decision

The product rule for DeepSeek native research becomes:

> Provider-owned search multiplicity is not an application semantic failure.

The application may bound memory, transport, persisted provenance, and parser complexity, but it must not discard a completed paid DeepSeek native SEARCH merely because the provider executed more than four search actions or exposed more than four query strings.

The provider decides how many native search actions are needed inside the bounded provider response. The application decides how much provenance text it retains.

These are separate concerns.

---

## 3. Scope

Implement only:

### R05-A — Remove normal `<=4` query multiplicity rejection

For DeepSeek Research-ON SEARCH parsing:

- do not fail solely because `search_action_count > 4`;
- do not fail solely because the provider exposed more than four query strings;
- do not rewrite, fabricate, or merge provider search actions merely to reduce their count;
- preserve R04 accepted `web_search_call` pass-back behavior.

### R05-B — Bounded query provenance capture

Record truthful provider-exposed query multiplicity without allowing provenance to grow unbounded.

### R05-C — Extend safe diagnostics

Expose bounded numeric diagnostic fields sufficient to identify any remaining parser boundary.

Everything else is out of scope.

---

## 4. Protected R04 architecture

Do not alter the R04 lifecycle:

```text
Explicit Research opt-in
↓
Freeze immutable Snapshot
↓
SEARCH request #1
DeepSeek native web_search
↓
Validate SEARCH
↓
If direct final memo exists:
    freeze memo
Else if valid tool-only SEARCH:
    SYNTHESIS request #2
    pass accepted web_search_call items back as-is
    tools=[]
    reasoning.effort=none
    ↓
    freeze memo
↓
Build immutable NarrativeRequest
↓
Final PAQS-E Narrative
unchanged NarrativeGateway
 tools=[] / tool_choice=none
↓
Narrative Ledger
```

Maximum research-stage provider HTTP requests remains exactly two.

Maximum total provider requests for successful tool-only Research-ON remains exactly three:

1. SEARCH;
2. optional SYNTHESIS;
3. final Narrative.

No retries.

No second SEARCH.

No provider fallback.

No hidden search during final Narrative.

---

# PART A — DEEPSEEK QUERY MULTIPLICITY

## 5. Remove the four-query normal acceptance cap

The current DeepSeek parser must no longer contain a normal success-path rejection equivalent to:

```python
if len(queries) > 4:
    raise ValueError(...)
```

or any equivalent rule that rejects the provider response merely because more than four otherwise valid provider-exposed query strings exist.

The existing SEARCH instruction may continue to **request** concise/bounded research, but such instruction is advisory to the provider. It is not a post-hoc acceptance invariant unless the provider offers an enforceable request parameter that actually guarantees the bound.

Do not claim application cost control from rejecting search multiplicity after the provider has already executed the searches.

---

## 6. Search action multiplicity

Preserve R04 local structural bounds:

- maximum 64 accepted `web_search_call` output items;
- maximum 128 total response output items;
- at least one accepted completed `search` action;
- allowed action types only:
  - `search`;
  - `open_page`;
  - `find_in_page`;
- unknown action types fail closed;
- incomplete/failed action items fail closed.

A live-like response with:

```text
web_search_call_count = 20
search_action_count = 6
message_count = 0
```

must pass the multiplicity layer and reach the R04 tool-only continuation decision if every other SEARCH invariant is valid.

A response with 11, 20, or 64 accepted action records must not fail solely because the count exceeds a provider server-side continuation-round figure.

---

## 7. Provider-exposed query string validation

Individual provider-exposed query values still require safety validation.

Each exposed query, when present, must be:

- a string;
- non-empty after whitespace check;
- bounded to maximum 500 Unicode characters;
- valid UTF-8 encodable;
- free of forbidden control characters used elsewhere in the research safety boundary.

Malformed individual query values fail closed.

Absence of query strings remains allowed when a real completed native `search` action exists.

Do not fabricate missing query strings.

---

## 8. Structural anti-abuse bound for provider-exposed queries

The removal of the four-query business rule does not mean unbounded parser work.

Add a high local structural safety bound that is clearly separate from normal provider multiplicity.

Recommended v1 maximum:

- at most 256 provider-exposed query strings processed from one SEARCH response;
- at most 64,000 total Unicode characters across all provider-exposed query strings before provenance capture.

Equivalent tighter bounds are allowed only if they comfortably admit the observed live case and are documented/tested.

A response exceeding these structural anti-abuse limits may fail closed with safe diagnostics.

Do not describe these limits as provider round limits or strategy semantics.

---

# PART B — BOUNDED QUERY PROVENANCE CAPTURE

## 9. Truthful multiplicity metadata

DeepSeek memo provenance must add:

- `provider_exposed_query_count`: total number of valid provider-exposed query strings observed before capture truncation;
- `query_capture_complete`: boolean;
- `queries`: bounded ordered captured query strings.

The count must reflect the provider response, not the number retained after capture budgeting.

Example:

```json
{
  "provider_exposed_query_count": 6,
  "query_capture_complete": true,
  "queries": ["...", "...", "...", "...", "...", "..."]
}
```

If provider exposes many valid queries:

```json
{
  "provider_exposed_query_count": 37,
  "query_capture_complete": false,
  "queries": ["bounded retained subset in original order"]
}
```

Do not silently present truncated query capture as complete.

---

## 10. Query capture budget

Persist only a bounded ordered prefix of provider-exposed query strings.

Recommended capture budget:

- maximum 16 retained queries;
- maximum 4,000 total Unicode characters across retained query strings.

Equivalent bounds are allowed if documented and kept comfortably within the existing 24,000-character auxiliary-context/provenance budget.

Capture algorithm requirements:

- preserve provider order;
- do not deduplicate before calculating `provider_exposed_query_count`;
- do not fabricate omitted entries;
- do not partially truncate a query string into a misleading fragment;
- if the next complete query would exceed capture budget, omit it and set `query_capture_complete=false`;
- if count exceeds retained-item cap, set `query_capture_complete=false`;
- captured query text remains auxiliary provenance, never strategy input authority.

---

## 11. Existing provenance remains

Preserve existing R03/R04 provenance fields including:

- provider;
- model;
- Snapshot As-Of;
- research intent;
- SEARCH provider response id when safe;
- `search_response_status`;
- `web_search_call_count`;
- `search_action_count`;
- ordered action types;
- safe validated source/citation URLs;
- known valid publication timestamps;
- excluded future source count;
- synthesis used;
- SYNTHESIS provider response id when safe;
- research HTTP request count;
- explicit provenance limitation.

Do not infer URLs from memo prose.

Do not fabricate publication timestamps.

Do not persist raw `web_search_call` objects.

---

# PART C — SOURCE/CITATION BOUNDS REMAIN

## 12. Do not broaden source/citation retention in R05

The following R03/R04 source safety rules remain unchanged:

- maximum 64 raw source/citation records processed for provenance;
- URL maximum 1000 characters;
- `http` / `https` only;
- no embedded credentials;
- no whitespace/control/backslash smuggling;
- syntactically valid hostname and port;
- known future-dated source excluded from trusted provenance;
- arbitrary URL inside memo prose is not trusted provenance.

This remediation does **not** authorize relaxing source-record multiplicity.

If a later live response fails because raw source records exceed 64, the new diagnostic fields must make that visible rather than guessing.

---

# PART D — SAFE DIAGNOSTICS

## 13. Extend ResearchDiagnostic

Extend the existing bounded diagnostic object with numeric/boolean fields sufficient to distinguish remaining SEARCH parser boundaries.

Add, when safely available:

- `provider_exposed_query_count`: integer;
- `raw_source_record_count`: integer;
- `unknown_action_count`: integer;
- optionally `query_capture_complete`: boolean if the failure occurs after valid query capture state is known.

Existing diagnostic fields remain:

- detail version;
- stage;
- failure class;
- provider id;
- model id;
- provider status;
- safe provider response id;
- web search call count;
- search action count;
- message count;
- synthesis attempted;
- research HTTP request count;
- allowlisted incomplete reason.

---

## 14. Diagnostic bounds

Every diagnostic count must be an integer and bounded.

Recommended upper bounds:

- counts up to 1024 for diagnostic representation;
- negative values forbidden;
- booleans must be exact booleans;
- unknown/unavailable fields omitted rather than guessed.

Diagnostics must never contain:

- query text;
- memo text;
- source URLs;
- raw source titles;
- raw provider response;
- raw tool-call objects;
- search result contents;
- chain-of-thought/reasoning;
- provider debug/error body;
- hidden prompts/instructions;
- API key or Authorization material.

Diagnostic object is ephemeral API/UI failure metadata only.

Do not persist it in Narrative Ledger because research precondition failure creates no Narrative Run/Result.

---

## 15. Browser failure projection

Preserve concise Chinese research diagnostics.

If new fields are present and pass strict client validation, browser may render an additional suffix such as:

```text
查询 6，来源记录 24，未知动作 0
```

Do not render:

- query strings;
- source URLs;
- provider response id;
- arbitrary diagnostic object JSON;
- raw API detail;
- hidden/private strings.

If diagnostic shape is invalid, omit it rather than displaying untrusted fields.

---

# PART E — TOOL-ONLY CONTINUATION MUST NOW BE REACHED

## 16. Live-like regression fixture

Add a deterministic fixture closely matching the actual R04 live diagnostic:

```text
status = completed
web_search_call_count = 20
search_action_count = 6
message_count = 0
```

The fixture must expose at least six valid provider query strings so that the previous `len(queries) > 4` implementation would fail.

Expected R05 behavior:

1. SEARCH parser accepts all valid action multiplicity;
2. no failure solely due to six queries;
3. `provider_exposed_query_count == 6`;
4. query capture follows the bounded provenance policy;
5. tool-only SEARCH triggers exactly one SYNTHESIS request;
6. accepted `web_search_call` items are passed back as-is under R04 semantics;
7. SYNTHESIS remains `tools=[]`, `tool_choice=none`, `reasoning.effort=none`;
8. successful synthesis freezes one memo;
9. final Narrative is called only after frozen memo exists.

---

## 17. Preserve direct memo fast path

If SEARCH response already contains a valid final memo:

- do not synthesize;
- query multiplicity compatibility still applies;
- freeze direct memo with accurate provenance;
- continue to final Narrative.

A direct-memo response with six search actions/queries must succeed if all other invariants are valid.

---

## 18. No extra provider calls

R05 authorizes no additional provider request.

Research stage remains:

- SEARCH exactly once;
- SYNTHESIS at most once.

Do not add:

- another SEARCH request;
- retry after SEARCH failure;
- retry after SYNTHESIS failure;
- query-by-query HTTP requests;
- provider-side loop controlled by the application;
- fallback model/provider.

---

# PART F — PROTECTED COMPONENTS

## 19. Do not modify already accepted behavior

This remediation must not alter:

- PAQS-E Context-Free Master Spec;
- PAQS-E Doctrine;
- Narrative runtime prompt;
- `NarrativeGateway.reason_text(...)` behavior;
- Narrative request schema/output version;
- Narrative Ledger schema;
- Narrative revision lineage;
- Narrative response text/hash semantics;
- Narrative request hash semantics;
- migrations 0001/0002/0003;
- migration head `0003_task007c1_narrative_ledger`;
- legacy structured validator;
- legacy structured runtime schema;
- legacy historical reads;
- secure Credential Manager architecture;
- model registry/model list;
- provider endpoints;
- Windows launcher/source-SHA handshake;
- long-running non-aborting guard;
- safe Markdown renderer;
- formatted/raw Narrative toggle;
- research default OFF / explicit opt-in;
- Snapshot construction;
- market-data behavior;
- no-live-trading boundary.

No 0004 migration.

No provider/model addition.

No PAQS-Q/backtest/portfolio/PnL/broker/execution scope.

---

## 20. Other providers unchanged

OpenAI and Alibaba/Qwen research behavior must remain unchanged.

Do not apply DeepSeek multiplicity/capture semantics to other providers unless a tiny shared helper is proven behavior-equivalent for them.

Do not reduce their existing provenance guarantees.

---

# PART G — TEST REQUIREMENTS

## 21. DeepSeek unit tests

Add deterministic tests proving at minimum:

1. six valid search actions with six exposed queries do not fail solely due to query count;
2. direct memo with six exposed queries succeeds;
3. tool-only SEARCH with 20 actions / 6 searches / 6 queries reaches SYNTHESIS;
4. `provider_exposed_query_count` reflects all valid exposed query strings;
5. `query_capture_complete=true` when all queries fit capture budget;
6. more than retained query count budget truncates provenance capture without failing SEARCH;
7. exceeding retained query character budget truncates capture without partial-string truncation;
8. truncated capture sets `query_capture_complete=false`;
9. captured queries preserve provider order;
10. duplicate provider query strings count separately before capture/dedup decisions;
11. malformed individual query type fails closed;
12. empty query fails closed;
13. >500-character individual query fails closed;
14. invalid control/UTF-8 query fails closed;
15. structural anti-abuse query count overflow fails closed with safe diagnostics;
16. structural anti-abuse total query-character overflow fails closed with safe diagnostics;
17. 20 web-search calls remain within R04 local action bound;
18. >64 web-search calls still fail;
19. >128 total output items still fail;
20. no real search action still fails;
21. unknown action still fails;
22. source/citation raw-record bound remains 64;
23. R05 never creates more than two research-stage HTTP requests;
24. no retry occurs;
25. synthesis pass-back remains byte/object-equivalent to accepted R04 `web_search_call` items;
26. final Narrative remains tool-free;
27. query text never enters safe failure diagnostics;
28. source URLs never enter safe failure diagnostics;
29. raw provider body/reasoning/secret never enters diagnostics;
30. other providers' test fixtures remain unchanged/pass.

---

## 22. Diagnostic tests

Add tests proving safe diagnostic counts for at least:

- live-like six-query tool-only response;
- malformed query;
- query structural overflow;
- source-record overflow;
- unknown action;
- synthesis failure.

Diagnostics should expose only numeric/boolean allowlisted values.

Expected examples:

```json
{
  "stage": "SEARCH",
  "failure_class": "INVALID_RESPONSE",
  "web_search_call_count": 20,
  "search_action_count": 6,
  "message_count": 0,
  "provider_exposed_query_count": 6,
  "raw_source_record_count": 0,
  "unknown_action_count": 0,
  "research_http_request_count": 1
}
```

Do not require every field when failure occurs before the count is safely knowable.

---

## 23. Integration tests

Add integration tests proving:

- Research-OFF remains zero research requests + unchanged final Narrative request;
- Research-ON direct memo with >4 valid queries succeeds;
- Research-ON live-like tool-only 20/6/0 SEARCH reaches SYNTHESIS;
- tool-only Research-ON still uses exactly two research calls + one final Narrative call;
- frozen auxiliary context contains memo and truthful bounded provenance;
- request SHA readback remains valid;
- response SHA readback remains valid;
- no failure Run/Result on research precondition failure;
- migration head remains 0003;
- existing DB schema unchanged;
- previous successful Narrative remains untouched.

---

## 24. Browser tests

Browser tests must prove:

- research remains default OFF;
- explicit research ON still sends one Analyze POST only;
- new safe diagnostic numeric suffix can be rendered without showing raw data;
- malformed/untrusted diagnostic fields are ignored;
- prior Narrative remains selected on research failure;
- Markdown formatted/raw behavior unchanged;
- no auto retry.

---

# PART H — IMPLEMENTATION REPORT

## 25. Required implementation report

Create:

`docs/TASK_007C1_REMEDIATION_05_IMPLEMENTATION_REPORT.md`

The report must include:

1. exact starting Contract commit;
2. exact final implementation SHA;
3. complete changed-file list;
4. exact removal/replacement of the old `<=4` query normal acceptance rule;
5. query structural anti-abuse bounds;
6. query capture item/character budgets;
7. provenance fields added;
8. diagnostic fields added;
9. confirmation R04 SEARCH/SYNTHESIS call counts unchanged;
10. confirmation no provider retries/fallbacks added;
11. confirmation other providers unchanged;
12. confirmation NarrativeGateway unchanged;
13. confirmation Markdown/default-OFF unchanged;
14. confirmation migrations 0001/0002/0003 unchanged;
15. confirmation migration head remains 0003;
16. protected-file audit;
17. test commands/results;
18. statement that no paid provider calls were performed by Codex;
19. statement that authoritative branch was not modified;
20. final exact task branch SHA.

---

# PART I — GIT / GOVERNANCE

## 26. Git preconditions

Before editing, Codex must verify:

- repository is `ahhhhzzz/ai-infra-quant`;
- current branch is `task/007c1-paqs-e-multi-model-web-research`;
- current HEAD is the R05 Contract commit created from exact base `a82340db89be0e2a47583b03f97fb28218dd7a09`;
- R05 Contract direct parent is exactly `a82340db89be0e2a47583b03f97fb28218dd7a09`;
- authoritative `roadmap/no-live-trading` is exactly `80f089bc2d285cca492c41aaeaf047e177bc2812`;
- merge base between task and authoritative is exactly `80f089bc2d285cca492c41aaeaf047e177bc2812`;
- task is not behind authoritative.

If any precondition fails, stop without editing.

---

## 27. Branch rules

Codex may commit and push only:

`task/007c1-paqs-e-multi-model-web-research`

Do not merge.

Do not force push.

Do not modify authoritative branch.

Stop for independent review.

---

# PART J — FINAL LIVE ACCEPTANCE

## 28. Paid live acceptance remains user-executed only

Ordinary tests must not call a paid provider.

After implementation receives independent code/contract PASS, the user performs exactly one DeepSeek V4 Flash Research-ON product smoke on the exact reviewed SHA.

Use the same clean comparison target where practical:

- Security: `US.AVGO`;
- model: DeepSeek V4 Flash;
- strategy: `paqs-e-master`;
- research explicitly ON.

If success:

- verify successful Narrative Run/Result;
- verify `web_research=true`;
- verify frozen auxiliary context count > 0;
- verify request SHA;
- verify response SHA;
- verify provenance reports truthful search/query counts and capture-completeness;
- verify synthesis flag/request count;
- final TASK-007C1 may then proceed to final SHA/topology gate.

If failure:

- do not automatically retry;
- report the safe browser diagnostic exactly;
- use `provider_exposed_query_count`, `raw_source_record_count`, and `unknown_action_count` to identify the next parser boundary;
- do not expose or request raw provider responses, API keys, hidden prompts, or reasoning.

---

## 29. Final acceptance matrix

R05 is code/contract complete only when all deterministic validation passes.

TASK-007C1 final product PASS still requires:

```text
Narrative Research-OFF live acceptance       PASS
Narrative Ledger live acceptance             PASS
Long-running non-abort live acceptance       PASS
Safe Markdown code/browser acceptance        PASS
Research default-OFF code/browser acceptance PASS
DeepSeek Research-ON exact-SHA live smoke    PASS
Final Git topology/SHA gate                  PASS
```

Until all gates pass:

- do not merge;
- do not mark TASK-007C1 final PASS;
- do not begin the next implementation task.
