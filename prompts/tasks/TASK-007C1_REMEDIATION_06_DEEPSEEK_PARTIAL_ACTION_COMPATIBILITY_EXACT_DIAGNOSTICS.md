# TASK-007C1 REMEDIATION 06 — DeepSeek Partial Search-Action Compatibility + Exact Parser Diagnostics

Status: **APPROVED REMEDIATION CONTRACT — user-authorized remediation only**

Issued: 2026-09-08

Repository: `ahhhhzzz/ai-infra-quant`

Authoritative branch: `roadmap/no-live-trading`

Authoritative SHA at issuance: `80f089bc2d285cca492c41aaeaf047e177bc2812`

TASK-007C1 branch: `task/007c1-paqs-e-multi-model-web-research`

Exact remediation base / latest reviewed implementation SHA:

`a3cc97d96887d9e31af4c3d56ab7206ef6600032`

Original TASK-007C1 Contract commit:

`9f41016b2341e91ad2825b7f731bca4f378b0108`

Remediation 01 Contract commit:

`b7316e83f7fd377f4c628db90dee8e3d7b4a5335`

Remediation 02 Contract commit:

`ca1b71f94565dee02f0bd43d280a59f3ec15ac6d`

Remediation 03 Contract commit:

`5285ed7d4553e7a9d3860b9263135d4d94b2f3e5`

Remediation 04 Contract commit:

`e6fe791a5c99033da77a8bc877e772e0c84f55df`

Remediation 05 Contract commit:

`a86efee5801ab4355b27fa6ffa4bbabaab7828c5`

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

Remediation 05:

`prompts/tasks/TASK-007C1_REMEDIATION_05_DEEPSEEK_SEARCH_MULTIPLICITY_COMPATIBILITY.md`

This remediation is intentionally narrow.

It preserves:

- the successful Narrative-first Research-OFF path;
- the Remediation-04 SEARCH -> optional SYNTHESIS -> final Narrative lifecycle;
- the Remediation-05 provider-owned search/query multiplicity compatibility;
- safe Markdown presentation;
- explicit research opt-in/default OFF;
- the immutable Narrative Ledger;
- all no-live-trading product boundaries.

It fixes only:

1. DeepSeek SEARCH compatibility when a top-level completed response contains a mixture of completed and recognized non-completed native `web_search_call` action records;
2. exact bounded parser diagnostics so any remaining SEARCH rejection identifies the application boundary without guessing or exposing provider bodies.

No other product behavior is authorized.

---

# 1. ACCEPTED LIVE EVIDENCE

## 1.1 Existing accepted live evidence remains authoritative

Research-OFF Narrative-first remains accepted from the previously verified real DeepSeek V4 Flash run for:

- Security: `US.AVGO`;
- provider: `deepseek`;
- model: `deepseek-v4-flash`;
- strategy: `paqs-e-master`;
- `web_research=false`.

Verified previously:

- successful immutable Narrative Run/Result;
- request SHA verified;
- response SHA verified;
- provider response id retained safely;
- response length 4043 characters;
- approximately 235 seconds elapsed without browser abort.

Do not redesign or revalidate this paid path unless implementation unexpectedly changes it.

Remediation-03 safe Markdown and research default-OFF behavior remain protected.

Remediation-04 stateless continuation architecture remains protected.

Remediation-05 query multiplicity behavior remains protected.

## 1.2 Exact new Research-ON live evidence after Remediation 05

On exact implementation SHA:

`a3cc97d96887d9e31af4c3d56ab7206ef6600032`

with:

- `US.AVGO`;
- DeepSeek V4 Flash;
- `paqs-e-master`;
- explicit `web_research=true`;

the browser returned:

```text
PAQS_E_RESEARCH_PRECONDITION_FAILED
SEARCH / INVALID_RESPONSE
research_http_request_count = 1
web_search_call_count = 16
search_action_count = 7
message_count = 0
provider_exposed_query_count = 24
raw_source_record_count = 0
unknown_action_count = 0
```

Safe conclusions from this live evidence:

- the SEARCH request reached DeepSeek;
- a provider response was received far enough for bounded diagnostic parsing;
- there were 16 `web_search_call`-shaped records;
- 7 were `search` action types;
- 24 provider-exposed query slots were observed;
- source-record multiplicity was not the blocker in this run;
- unknown action type multiplicity was not the blocker in this run;
- no final message was present;
- failure occurred before SYNTHESIS request #2;
- no Narrative Run/Result was fabricated.

This live result also demonstrates that Remediation-05 removed the previous ordinary `<=4` query multiplicity blocker: 24 exposed query slots passed far enough to produce the new diagnostic instead of failing solely because the count exceeded four.

## 1.3 Remaining parser uncertainty

At the current exact SHA, SEARCH parsing still contains a hard rule equivalent to:

```python
if item.get("status") != "completed" or not isinstance(action, dict):
    raise ValueError("Incomplete action")
```

Therefore one recognized native search action whose item-level status is not exactly `completed` can invalidate the entire otherwise top-level completed SEARCH response before SYNTHESIS is attempted.

The current diagnostic does **not** expose per-action status counts or the exact parser boundary code.

The same live response could also still fail at another strict SEARCH boundary, for example:

- malformed individual query value;
- malformed action object;
- missing/unknown action status;
- unexpected output item type;
- source URL integrity;
- local pass-back/provenance size.

Therefore this Contract does **not** claim partial action status is proven as the only remaining root cause.

The remediation decision is:

1. make recognized partial action states compatible without trusting them as evidence;
2. make the exact parser boundary observable through safe application-owned enums and counts.

---

# 2. PRODUCT DECISION

For DeepSeek native web research:

> A top-level completed SEARCH response may contain recognized native search actions that did not themselves complete successfully. Such partial actions are not trusted evidence and are not passed back for synthesis, but they do not invalidate the entire SEARCH if enough completed native search evidence remains.

The application must still require at least one completed native `search` action.

A failed/incomplete/in-progress/cancelled native action is not treated as successful evidence.

The application must not fabricate success from failed actions.

The application must not silently use partial action payloads as provenance.

The application must not persist raw partial action objects.

---

# 3. SCOPE

Implement only:

### R06-A — Partial native action compatibility

For DeepSeek SEARCH response parsing, recognize a bounded allowlist of native action item statuses and distinguish completed vs non-completed actions.

### R06-B — Completed-evidence filtering

Only completed recognized native search calls may:

- contribute positive research provenance;
- expose query/source metadata for trusted parsing;
- be passed back as native continuation input during SYNTHESIS.

### R06-C — Exact parser diagnostics

Extend the existing bounded safe diagnostic model with:

- application-owned parser boundary code;
- per-status action counts;
- completed-search vs non-completed-search counts;
- bounded malformed/invalid counters sufficient to identify the remaining parser boundary.

Everything else is out of scope.

---

# 4. PROTECTED ARCHITECTURE

Do not alter the R04/R05 lifecycle:

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
If direct final memo exists and completed search evidence exists:
    freeze memo
Else if valid tool-only SEARCH and completed search evidence exists:
    SYNTHESIS request #2
    pass only accepted completed web_search_call items
    tools=[]
    tool_choice=none
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

Maximum research-stage provider HTTP requests remains exactly two:

1. SEARCH exactly once;
2. SYNTHESIS at most once.

Maximum total provider calls for a successful tool-only Research-ON analysis remains exactly three:

1. SEARCH;
2. SYNTHESIS;
3. final Narrative.

No retry.

No second SEARCH.

No provider fallback.

No hidden search during final Narrative.

---

# PART A — PARTIAL ACTION STATUS COMPATIBILITY

## 5. Recognized item-level statuses

For a `web_search_call` output item whose action object and action type are otherwise well-shaped, recognize these bounded item-level status values:

- `completed`;
- `in_progress`;
- `incomplete`;
- `failed`;
- `cancelled`.

This is an application compatibility allowlist, not a claim that every provider version necessarily emits every status.

Unknown non-null status values fail closed.

Missing status / null status fails closed unless current provider fixtures and official route behavior already establish a safe equivalent. Do not silently map missing status to `completed`.

## 6. Completed action semantics

Only `status == "completed"` counts as successful native evidence.

For a completed action:

- action must be an object;
- action type must be one of:
  - `search`;
  - `open_page`;
  - `find_in_page`;
- the action is eligible for bounded pass-back;
- a completed `search` action is eligible for query/source parsing;
- optional trusted source/citation parsing remains under R03/R05 safety rules.

## 7. Non-completed recognized action semantics

For recognized status values:

- `in_progress`;
- `incomplete`;
- `failed`;
- `cancelled`;

require:

- item is an object;
- action is an object;
- action type is one of `search/open_page/find_in_page`.

Then:

- count the action in safe diagnostic/status metadata;
- do **not** treat it as successful evidence;
- do **not** parse its query strings into trusted provenance;
- do **not** parse its source records into trusted provenance;
- do **not** add it to continuation/pass-back input;
- do **not** persist the raw item;
- do **not** fail the entire SEARCH solely because the recognized action was non-completed.

This avoids trusting partial output while preserving a completed SEARCH response that still has sufficient successful native search evidence.

## 8. Completed-search quorum

SEARCH may proceed only if at least one completed native action has:

```text
action.type == "search"
status == "completed"
```

Required behavior:

- at least one completed search + any number of recognized non-completed search/open/find actions -> potentially valid SEARCH;
- zero completed search actions -> fail closed;
- completed open/find actions without a completed search -> fail closed;
- non-completed search actions do not satisfy the quorum.

Use an exact safe boundary code such as `NO_COMPLETED_SEARCH` for this failure.

Equivalent stable application enum naming is allowed.

## 9. Direct memo fast path with partial actions

If the top-level SEARCH response contains:

- at least one completed `search` action;
- one valid final memo;
- zero unknown output/action/status shapes;

then the direct memo fast path may succeed even if other recognized native actions are `in_progress/incomplete/failed/cancelled`.

Only completed actions contribute positive provenance.

Status counts should remain available in provenance if safely useful, but raw partial action bodies must never be frozen.

## 10. Tool-only continuation with partial actions

If the top-level SEARCH response contains:

- at least one completed `search` action;
- no final memo;
- only recognized output/action/status shapes;

then it must reach exactly one SYNTHESIS request.

SYNTHESIS continuation input must contain:

1. original bounded research intent;
2. only completed accepted `web_search_call` items, passed back as-is/deep-copied without semantic rewrite;
3. final synthesis user instruction.

Do not pass back:

- reasoning items;
- incomplete actions;
- failed actions;
- in-progress actions;
- cancelled actions;
- arbitrary SEARCH messages;
- unknown items.

## 11. Unknown action type remains fail closed

R06 does not relax action-type safety.

Any `web_search_call.action.type` outside:

- `search`;
- `open_page`;
- `find_in_page`

fails closed, regardless of item status.

Do not silently ignore arbitrary tools.

## 12. Malformed action object remains fail closed

A `web_search_call` whose `action` is missing or is not an object fails closed.

Do not interpret malformed action bodies as partial-but-safe.

---

# PART B — QUERY / SOURCE BEHAVIOR REMAINS R05

## 13. Query multiplicity remains compatible

Do not reintroduce any normal acceptance rule equivalent to:

```text
provider_exposed_query_count <= 4
search_action_count <= 4
```

Preserve R05 structural bounds:

- maximum 256 provider-exposed query strings processed from completed search actions;
- maximum 64,000 total Unicode characters across those valid exposed query strings;
- maximum 16 retained query strings;
- maximum 4,000 retained query characters;
- truthful `provider_exposed_query_count`;
- truthful `query_capture_complete`.

## 14. Query parsing applies only to completed search actions

A recognized non-completed `search` action is not trusted evidence.

Therefore query/source payload inside a non-completed search action must not become a normal acceptance blocker unless the outer action/status/type shape itself is malformed.

Do not parse or retain arbitrary query/source fields from non-completed search actions.

This is intentional: failed/incomplete tool payloads are not research evidence.

## 15. Completed search query integrity remains strict

For each exposed query belonging to a completed search action, preserve R05 validation:

- string;
- non-empty after whitespace check;
- <=500 Unicode characters;
- UTF-8 encodable;
- no forbidden control characters.

Malformed query values on completed search actions still fail closed.

Do not fabricate missing query values.

Absence of query strings remains allowed if the completed native search action exists.

## 16. Source/citation rules remain unchanged

Preserve:

- maximum 64 raw source/citation records from completed trusted evidence;
- URL <=1000 characters;
- `http`/`https` only;
- no embedded credentials;
- no whitespace/control/backslash smuggling;
- valid hostname/port;
- known future sources excluded from trusted provenance;
- arbitrary memo prose URLs never promoted to trusted sources.

Do not relax source safety in R06.

---

# PART C — EXACT SAFE PARSER DIAGNOSTICS

## 17. Diagnostic objective

After R06, another Research-ON failure must identify the exact **application parser boundary class** without requiring raw provider dumps or further speculation.

Diagnostics remain ephemeral API/UI metadata only.

Do not persist diagnostics in the Narrative Ledger.

## 18. Add stable parser boundary code

Extend `ResearchDiagnostic` with an optional application-owned bounded enum/string such as:

`boundary_code`.

Allowed values should be stable, short and test-covered.

Recommended SEARCH boundary codes include:

- `SEARCH_ENVELOPE`;
- `SEARCH_OUTPUT_SHAPE`;
- `ACTION_SHAPE`;
- `ACTION_TYPE`;
- `ACTION_STATUS`;
- `NO_COMPLETED_SEARCH`;
- `QUERY_STRUCTURE`;
- `QUERY_INTEGRITY`;
- `QUERY_STRUCTURAL_BOUND`;
- `SOURCE_STRUCTURE`;
- `SOURCE_BOUND`;
- `SOURCE_URL`;
- `MESSAGE_SHAPE`;
- `MESSAGE_INTEGRITY`;
- `PASSBACK_BOUND`;
- `PROVENANCE_BOUND`.

Recommended SYNTHESIS boundary codes include:

- `SYNTHESIS_ENVELOPE`;
- `SYNTHESIS_OUTPUT_SHAPE`;
- `SYNTHESIS_MESSAGE`;
- `SYNTHESIS_MEMO_INTEGRITY`.

Exact naming may differ, but:

- it must be application-owned;
- it must be allowlisted;
- it must never include provider text;
- it must never include exception messages;
- it must never include request/response bodies.

## 19. Prefer parser-originated safe boundary metadata

Avoid relying only on a second best-effort reparsing pass after failure.

Preferred design:

- SEARCH parser raises/returns an internal bounded parse-failure object containing:
  - boundary code;
  - numeric counters only;
- research adapter converts it into `ResearchFailure` / `ResearchDiagnostic`;
- raw exception strings are never projected.

Equivalent architecture is allowed if tests prove the diagnostic boundary exactly matches the actual failing parser rule.

## 20. Add per-status action counts

Add bounded integer diagnostic fields, when safely known:

- `completed_action_count`;
- `in_progress_action_count`;
- `incomplete_action_count`;
- `failed_action_count`;
- `cancelled_action_count`;
- optionally `missing_or_unknown_status_count` if shape permits safe counting.

Also add:

- `completed_search_count`;
- `non_completed_search_count`.

Keep existing:

- `web_search_call_count`;
- `search_action_count`;
- `message_count`;
- `provider_exposed_query_count`;
- `raw_source_record_count`;
- `unknown_action_count`.

## 21. Add bounded malformed/invalid counters

When safely known, add numeric fields such as:

- `invalid_query_value_count`;
- `malformed_action_count`;
- `unexpected_output_item_count`.

Equivalent minimal counters are allowed if `boundary_code` already identifies the exact failure and the counter adds meaningful confirmation.

Do not add arbitrary string detail.

## 22. Diagnostic value bounds

All new numeric diagnostic fields must:

- be exact integers, not booleans;
- be >=0;
- have bounded maximum, recommended <=1024;
- be omitted when unknown rather than guessed.

`boundary_code` must have a strict application allowlist.

Diagnostics must never contain:

- query text;
- memo text;
- source URLs;
- source titles;
- raw provider response;
- raw tool-call items;
- search result contents;
- reasoning/chain-of-thought;
- provider exception body;
- provider refusal text;
- hidden prompts/instructions;
- API key;
- Authorization material;
- arbitrary user/private strings.

## 23. Secret-tainted response behavior

If a provider response is secret-tainted under the existing credential-echo guard:

- fail closed;
- do not inspect/reparse tainted body for detailed counters;
- omit counters/boundary details that would require inspecting tainted payload;
- keep diagnostic generic and safe.

Do not weaken the existing secret-echo protection.

---

# PART D — BROWSER FAILURE PROJECTION

## 24. Concise safe UI diagnostics

Preserve the current Chinese research failure status.

If valid new diagnostic fields are present, render a concise suffix such as:

```text
边界 ACTION_STATUS；
动作 completed 13 / incomplete 2 / failed 1；
完成搜索 6，未完成搜索 1；
查询 24，来源记录 0，未知动作 0。
```

Equivalent compact wording is allowed.

Do not render:

- raw JSON;
- query strings;
- provider response id;
- source URLs;
- provider detail strings;
- exception messages;
- arbitrary diagnostic keys.

If `boundary_code` or counts fail strict client validation, omit those fields rather than displaying untrusted data.

## 25. Prior Narrative must remain visible on failure

Research failure remains a precondition failure.

It must:

- create no new Narrative Run/Result;
- preserve the previously selected successful Narrative;
- mark it as earlier content under existing UI semantics;
- never auto-retry;
- never auto-run after refresh/model/history actions.

---

# PART E — PROVENANCE

## 26. Positive provenance uses completed actions only

Successful DeepSeek memo provenance may include bounded safe status/count metadata, but positive evidence fields must derive only from completed accepted actions.

Recommended additional provenance fields:

- total `web_search_call_count`;
- `completed_action_count`;
- `non_completed_action_count` or per-status counts;
- `search_action_count`;
- `completed_search_count`;
- existing R05 query metadata;
- existing validated source metadata.

Do not freeze raw failed/incomplete action payloads.

## 27. Continuation pass-back remains transient

Completed accepted `web_search_call` objects used for SYNTHESIS pass-back remain transient transport material only.

They must not be:

- written to DB as raw objects;
- logged as full objects;
- exposed in API response;
- shown in UI;
- hashed into Narrative result text.

Frozen auxiliary context remains:

- final bounded factual memo;
- bounded canonical provenance only.

---

# PART F — PERMANENT PROTECTED COMPONENTS

## 28. Do not modify already accepted behavior

This remediation must not alter:

- PAQS-E Context-Free Master Spec;
- PAQS-E Doctrine;
- Narrative runtime prompt;
- `NarrativeGateway.reason_text(...)` behavior;
- Narrative request schema version;
- Narrative output format version;
- Narrative Ledger schema;
- Narrative revision lineage;
- Narrative response-text hash semantics;
- Narrative request hash semantics;
- migrations 0001/0002/0003;
- migration head `0003_task007c1_narrative_ledger`;
- legacy structured validator;
- legacy structured runtime schema;
- legacy historical read behavior;
- secure Credential Manager architecture;
- model registry/model list;
- provider endpoints;
- stale-backend source-revision handshake;
- long-running non-aborting Analyze guard;
- safe Markdown renderer;
- formatted/raw Narrative toggle;
- research default OFF / explicit opt-in;
- Snapshot construction;
- market-data provider behavior;
- no-live-trading boundary.

No 0004 migration.

No provider/model addition.

No PAQS-Q/backtest/portfolio/PnL/broker/execution scope.

## 29. Other providers remain unchanged

OpenAI and Alibaba/Qwen research behavior must remain unchanged.

Do not apply DeepSeek partial-action semantics globally.

Do not reduce their existing provenance guarantees.

A shared diagnostic helper is allowed only if provider behavior remains unchanged and tests prove it.

---

# PART G — REQUIRED UNIT TESTS

## 30. Live-like partial-action regression

Add a fixture based on the exact latest live shape:

```text
top-level status = completed
web_search_call_count = 16
search_action_count = 7
message_count = 0
provider_exposed_query_count = 24
raw_source_record_count = 0
unknown_action_count = 0
```

At least one recognized `open_page` or `find_in_page` action must be non-completed.

At least one `search` action must remain completed.

Expected behavior:

1. partial recognized action does not invalidate the SEARCH;
2. completed search quorum is satisfied;
3. only completed accepted actions enter pass-back;
4. tool-only response reaches exactly one SYNTHESIS;
5. SYNTHESIS remains tool-free;
6. frozen memo is created only after SYNTHESIS success.

## 31. Partial status matrix

Test at minimum:

- completed search + incomplete open_page -> succeeds/reaches synthesis;
- completed search + failed open_page -> succeeds/reaches synthesis;
- completed search + in_progress find_in_page -> succeeds/reaches synthesis;
- completed search + cancelled find_in_page -> succeeds/reaches synthesis;
- completed search + incomplete search + completed search -> succeeds/reaches synthesis;
- only incomplete/failed search actions and no completed search -> fails `NO_COMPLETED_SEARCH`;
- no search action at all -> fails closed.

## 32. Unknown/malformed status tests

Test:

- unknown status string -> fail `ACTION_STATUS` or equivalent;
- missing status -> fail closed;
- null status -> fail closed;
- non-string status -> fail closed;
- malformed action object -> fail `ACTION_SHAPE` or equivalent.

## 33. Pass-back filtering tests

Given mixed completed/non-completed actions:

- completed `web_search_call` items are passed back unchanged/deep-copied;
- non-completed items are absent from SYNTHESIS input;
- order of retained completed items is preserved;
- reasoning items are absent;
- no `previous_response_id`;
- no `conversation`;
- `tools=[]`;
- `tool_choice=none`;
- `reasoning.effort=none`.

## 34. Direct memo tests

Test direct SEARCH memo response with:

- at least one completed search;
- one incomplete open/find action;
- one valid final memo.

Expected:

- no SYNTHESIS request;
- memo freezes successfully;
- only completed evidence contributes provenance;
- provider request count remains one research call plus final Narrative.

## 35. Query trust-boundary tests

Test that:

- malformed query on completed search still fails `QUERY_INTEGRITY` or equivalent;
- malformed query inside a recognized non-completed search action is not treated as positive evidence and does not itself fail normal SEARCH acceptance;
- R05 24-query multiplicity remains compatible;
- R05 256/64,000 structural bounds remain unchanged for completed evidence.

## 36. Source trust-boundary tests

Test that:

- source records on completed search retain existing validation;
- malformed source on completed trusted evidence fails exact source boundary;
- source payload inside non-completed search is ignored/not trusted/not persisted;
- >64 trusted raw source records still fails with safe source-bound diagnostic.

## 37. Exact boundary diagnostic tests

For each representative parser failure, assert exact safe `boundary_code`, not only generic `INVALID_RESPONSE`.

At minimum cover:

- envelope status/model/id failure;
- output shape failure;
- action shape failure;
- action type failure;
- action status failure;
- no completed search;
- completed-query structure failure;
- completed-query integrity failure;
- query structural bound;
- source structure/bound/URL failure;
- message shape/integrity failure;
- pass-back bound;
- provenance bound;
- synthesis envelope/message failure.

## 38. Diagnostic count tests

Assert safe counts for a mixed fixture, for example:

```text
web_search_call_count = 16
search_action_count = 7
completed_action_count = 13
incomplete_action_count = 1
failed_action_count = 1
in_progress_action_count = 1
cancelled_action_count = 0
completed_search_count = 6
non_completed_search_count = 1
provider_exposed_query_count = 24
raw_source_record_count = 0
unknown_action_count = 0
```

Exact fixture counts may differ, but tests must prove counters match the actual parser input and never include raw text.

## 39. Secret/privacy diagnostics tests

Prove diagnostics never contain:

- API key;
- query text;
- memo text;
- source URL;
- provider raw error body;
- reasoning trace;
- hidden prompt;
- raw action object.

A secret-tainted response must not be deeply inspected to produce detailed counts.

---

# PART H — REQUIRED INTEGRATION TESTS

## 40. Research-OFF regression

Prove Research-OFF:

- performs zero research requests;
- uses unchanged final Narrative path;
- preserves exact result text/hash semantics;
- auxiliary context remains empty.

## 41. Research-ON partial-action success

Using the latest live-like mixed-status fixture, prove:

- one SEARCH request;
- parser accepts recognized partial actions;
- exactly one SYNTHESIS request for tool-only response;
- only completed calls are passed back;
- one frozen auxiliary context memo exists;
- final Narrative is called only after freeze;
- final Narrative remains `tools=[]` / `tool_choice=none`;
- successful request SHA readback verifies;
- successful response SHA readback verifies.

## 42. Research-ON failure behavior

For parser failure at an exact boundary:

- API returns existing `PAQS_E_RESEARCH_PRECONDITION_FAILED`;
- safe diagnostic includes exact `boundary_code` and bounded counters;
- no Narrative Run/Result is created;
- prior successful Narrative remains unchanged;
- no provider retry occurs.

## 43. Schema/migration invariance

Prove:

- migration head remains `0003_task007c1_narrative_ledger`;
- SQLite schema unchanged;
- no 0004 migration;
- no Narrative Ledger schema/repository mutation.

---

# PART I — REQUIRED BROWSER TESTS

## 44. Safe exact diagnostic display

Browser tests must prove:

- valid boundary code appears in concise Chinese failure status;
- valid per-status counts appear;
- completed/non-completed search counts appear when present;
- existing query/source/unknown-action counts remain supported;
- invalid/unknown boundary code is omitted;
- invalid count types/ranges are omitted;
- no raw JSON displayed;
- no private provider fields displayed;
- prior Narrative remains visible;
- no automatic retry;
- exactly one Analyze POST per explicit click.

## 45. Research default OFF remains

Reconfirm existing R03/R04 browser behavior:

- initial checkbox unchecked;
- model change resets unchecked;
- reload does not remember opt-in;
- only explicit check can send `web_research=true`.

Do not regress this behavior.

---

# PART J — VALIDATION

## 46. Required deterministic validation

At minimum run:

- full pytest suite;
- full browser suite;
- focused R04 continuation tests;
- focused R05 multiplicity tests;
- focused R06 partial-action tests;
- focused Narrative provider tests;
- focused Narrative API/Ledger tests;
- source-revision launcher tests;
- Ruff check;
- Ruff format check;
- mypy;
- fresh SQLite migration/health smoke confirming head remains 0003;
- local Uvicorn/OpenAPI/root/configuration smoke using synthetic/no-paid provider behavior only;
- protected-file diff/hash audit;
- secret/private-artifact audit.

No ordinary automated test may call a paid provider.

## 47. Implementation report

Create:

`docs/TASK_007C1_REMEDIATION_06_IMPLEMENTATION_REPORT.md`

The report must include:

- exact starting Contract SHA;
- exact final implementation SHA;
- changed-file list;
- precise parser-status semantics;
- precise completed-action pass-back filtering;
- diagnostic boundary-code design;
- validation commands/results;
- protected-file audit;
- migration head confirmation;
- explicit statement that no paid provider call was made;
- explicit statement that final Research-ON live acceptance remains user-executed.

---

# PART K — LIVE ACCEPTANCE

## 48. No paid provider call during implementation/review

Codex and ordinary deterministic tests must not call real paid DeepSeek/OpenAI/Alibaba provider APIs.

## 49. Final live gate after independent review

Only after independent review passes the exact final implementation SHA, the user may perform one real Research-ON smoke:

- `US.AVGO`;
- DeepSeek V4 Flash;
- `paqs-e-master`;
- explicit `web_research=true`;
- exactly one Analyze click;
- no automatic retry.

### Success acceptance

Expected:

- Research-ON succeeds;
- frozen research memo exists;
- final Narrative succeeds;
- request/response SHA verify;
- revision lineage is correct;
- evidence shows one- or two-stage research accurately;
- no raw native action bodies persisted.

### Failure acceptance

If it still fails:

- do not retry;
- provide the full safe UI diagnostic;
- diagnostic must identify an exact `boundary_code` plus bounded counters;
- no further remediation should be designed by guessing a hidden parser rule.

---

# PART L — GIT / GOVERNANCE

## 50. Implementation branch

Implement only on:

`task/007c1-paqs-e-multi-model-web-research`

Starting HEAD must equal the R06 Contract commit created from exact base:

`a3cc97d96887d9e31af4c3d56ab7206ef6600032`

Before editing, verify:

- task branch HEAD == expected Contract commit;
- Contract commit direct parent == exact R06 base;
- authoritative branch still == `80f089bc2d285cca492c41aaeaf047e177bc2812`;
- task branch remains behind 0 relative to authoritative;
- merge base remains exact authoritative SHA;
- worktree conditions comply with existing task instructions;
- local `phase1_remediation_commit.txt`, if present, remains untouched/untracked/uncommitted.

## 51. Do not merge

Codex must:

- implement;
- test;
- commit;
- push only the task branch;
- stop for independent review.

Do not merge to `roadmap/no-live-trading`.

Do not force push.

Final PASS applies only to the exact independently reviewed SHA plus successful required live acceptance.

---

# 52. DEFINITION OF DONE FOR REMEDIATION 06

Remediation 06 implementation is ready for independent review only when all are true:

1. exact Git/SHA preconditions verified;
2. DeepSeek top-level completed SEARCH can tolerate recognized non-completed native actions;
3. non-completed actions are never trusted as evidence;
4. non-completed actions are never passed back to SYNTHESIS;
5. at least one completed native `search` remains mandatory;
6. direct memo path works with partial recognized actions;
7. tool-only path reaches exactly one SYNTHESIS with partial recognized actions;
8. R05 query multiplicity behavior remains intact;
9. query/source parsing applies only to completed trusted search actions;
10. exact application-owned parser `boundary_code` exists;
11. per-status action counts are safely available;
12. completed vs non-completed search counts are safely available;
13. representative invalid query/action/output counters are safely available;
14. no raw provider/private material appears in diagnostics;
15. Research failure creates no Narrative Run/Result;
16. Research-OFF path remains unchanged;
17. NarrativeGateway remains unchanged;
18. Markdown/default-OFF behavior remains unchanged;
19. migration head remains 0003;
20. full required deterministic validation passes;
21. implementation report exists;
22. final implementation SHA is committed and pushed only to task branch;
23. no merge occurred;
24. user-run Research-ON live acceptance remains pending until independent review passes.
