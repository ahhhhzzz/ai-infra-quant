# TASK-007C1 Remediation 05 — Independent Review

Status: **CODE / CONTRACT REVIEW PASS — DEEPSEEK RESEARCH-ON LIVE ACCEPTANCE PENDING**

Reviewed implementation SHA: `a3cc97d96887d9e31af4c3d56ab7206ef6600032`

Remediation 05 Contract commit / direct implementation parent: `a86efee5801ab4355b27fa6ffa4bbabaab7828c5`

Remediation 05 implementation base: `a82340db89be0e2a47583b03f97fb28218dd7a09`

Authoritative branch: `roadmap/no-live-trading`

Authoritative SHA during review: `80f089bc2d285cca492c41aaeaf047e177bc2812`

Task branch: `task/007c1-paqs-e-multi-model-web-research`

Review branch: `review/007c1-remediation-05-independent`

Review date: 2026-09-08

This review is independent of the Codex implementation report. GitHub repository contents at the exact reviewed SHA are the source of truth. Claimed local test counts in the implementation report are treated as handoff evidence only and are not represented here as independently executed tests.

---

## 1. Git provenance gate — PASS

GitHub comparison verified:

- `a86efee5... -> a3cc97d9...`: ahead 1 / behind 0;
- task branch HEAD equals exact reviewed SHA `a3cc97d9...`;
- authoritative `roadmap/no-live-trading` remains exactly `80f089bc...`;
- task branch is ahead 12 / behind 0 relative to authoritative;
- merge base remains exactly `80f089bc...`;
- no authoritative merge was performed during review.

The Remediation 05 implementation diff contains 14 changed files and is limited to:

- DeepSeek query multiplicity / provenance parsing;
- bounded research diagnostics;
- concise browser diagnostic projection;
- focused unit / integration / browser regressions;
- implementation and architecture/model/workbench/requirements documentation.

The R05 implementation diff does **not** contain:

- a database migration;
- edits to migrations 0001/0002/0003;
- Narrative Ledger schema/repository changes;
- PAQS-E primary strategy changes;
- Narrative runtime prompt changes;
- NarrativeGateway final-text changes;
- safe Markdown renderer changes;
- model registry/provider endpoint changes;
- credential-store changes;
- launcher/source-revision changes;
- broker/trading additions.

---

## 2. Review conclusion

No blocking code/contract defect was found in the Remediation 05 implementation at `a3cc97d96887d9e31af4c3d56ab7206ef6600032`.

The code/contract review therefore passes this exact SHA to the next and final user-executed DeepSeek V4 Flash Research-ON live acceptance gate.

This is **not final TASK-007C1 PASS** until that live gate succeeds on this exact SHA and a final branch/topology gate confirms the task branch has not mutated.

Do not merge before the live gate.

---

## 3. Accepted prior live evidence remains unchanged

The previously accepted Research-OFF DeepSeek Narrative run remains authoritative evidence that:

- DeepSeek V4 Flash can produce the Narrative-first final answer;
- the final text can persist successfully in the Narrative Ledger;
- request and response SHA identities can be verified;
- a >180-second provider call can complete without browser abort;
- Research-OFF does not require auxiliary research context.

The previously observed R04 Research-ON failure remains the direct motivation for R05:

```text
SEARCH / INVALID_RESPONSE
research_http_request_count = 1
web_search_call_count = 20
search_action_count = 6
message_count = 0
```

That live response proved SEARCH reached DeepSeek and returned substantial provider-owned native search activity but was rejected before SYNTHESIS.

R05 correctly treats provider-owned search/query multiplicity as separate from application provenance retention.

---

## 4. R05-A — four-query normal acceptance cap removed — PASS

Reviewed file:

`src/ai_infra_quant/integrations/openai_reasoning/deepseek_research.py`

The previous normal-success invariant equivalent to:

```python
if len(queries) > 4:
    raise ValueError(...)
```

is no longer present in the DeepSeek parser.

Instead, exposed query strings are processed through `capture_queries(...)`.

Verified structural behavior:

- provider-exposed query count may exceed four;
- individual exposed queries remain validated;
- each query must be a string;
- query must be non-empty after whitespace check;
- individual query length is bounded at 500 Unicode characters;
- forbidden control characters are rejected;
- strict UTF-8 encoding is required;
- absence of query strings remains allowed when the native search action itself is valid.

The parser retains a high anti-abuse structural bound:

- maximum 256 provider-exposed query strings processed;
- maximum 64,000 total Unicode query characters processed.

Those bounds are clearly separate from normal provider multiplicity and comfortably admit the observed live case of six search actions/queries.

Result: **PASS**.

---

## 5. R05-B — bounded truthful query provenance — PASS

The DeepSeek memo provenance now includes:

- `provider_exposed_query_count`;
- `query_capture_complete`;
- bounded ordered `queries`.

Verified capture policy:

- provider-exposed multiplicity is counted before retention truncation;
- no deduplication is used to make multiplicity appear smaller;
- captured queries preserve provider-received order;
- maximum 16 complete query strings are retained;
- maximum 4,000 Unicode characters of complete captured query strings are retained;
- the parser never persists a partial query fragment;
- once retention budget is exceeded, `query_capture_complete=false`;
- later queries are still validated and counted even after persistence capture has stopped.

Examples covered by deterministic tests include:

- 6 queries -> all 6 retained, complete = true;
- 16 queries -> all 16 retained, complete = true;
- 37 queries -> first 16 retained, complete = false;
- repeated queries remain repeated and count truthfully;
- 256 valid queries are structurally accepted while persistence remains bounded;
- malformed query values fail even when they occur after capture has already stopped.

This matches the R05 product decision: application provenance size is bounded without pretending the provider performed fewer searches than it did.

Result: **PASS**.

---

## 6. Live-like 20 / 6 / 0 compatibility regression — PASS

Reviewed unit regression:

`tests/unit/test_paqs_e_search_multiplicity.py`

The fixture closely matches the real R04 live diagnostic:

```text
web_search_call_count = 20
search_action_count = 6
provider_exposed_query_count = 6
message_count = 0
```

Verified tool-only behavior:

1. SEARCH parser accepts the 20 allowed web-search-call items;
2. six search actions do not fail because they exceed four;
3. six exposed queries do not fail because they exceed four;
4. provider_exposed_query_count freezes as 6;
5. all six small query strings are captured with `query_capture_complete=true`;
6. absence of a final SEARCH memo selects the R04 tool-only continuation branch;
7. exactly one SYNTHESIS request is issued;
8. original accepted `web_search_call` items are passed back unchanged/as-is under the R04 contract;
9. SYNTHESIS remains `tools=[]`;
10. SYNTHESIS remains `tool_choice="none"`;
11. SYNTHESIS remains `reasoning={"effort":"none"}`;
12. `previous_response_id` and `conversation` remain absent.

The same test also covers the direct-memo fast path with 20 calls / 6 searches / 6 queries and confirms no SYNTHESIS request is made when the SEARCH response already contains the final memo.

Result: **PASS**.

---

## 7. R04 SEARCH -> optional SYNTHESIS architecture preserved — PASS

Reviewed file:

`src/ai_infra_quant/integrations/openai_reasoning/deepseek_research_flow.py`

The R04 state machine remains intact.

SEARCH still uses:

- one registered DeepSeek endpoint/model;
- one SEARCH request;
- `store=false`;
- `stream=false`;
- `reasoning.effort=none`;
- only native `web_search` tool;
- explicit web-search tool choice;
- bounded request and response material.

If SEARCH contains a final memo, the direct fast path freezes it immediately.

If SEARCH is valid and tool-only, the code performs exactly one SYNTHESIS request with:

- same model/endpoint/credential;
- no web tool;
- `tools=[]`;
- `tool_choice=none`;
- `reasoning.effort=none`;
- original bounded research intent;
- accepted `web_search_call` items passed back as stateless input items;
- one final factual-memo instruction.

There is no loop and no retry branch. The research stage remains at most two provider HTTP calls.

R05 did not alter `NarrativeGateway.reason_text(...)`; the frozen research memo continues to be completed before final PAQS-E Narrative reasoning.

Result: **PASS**.

---

## 8. R05-C — extended safe diagnostics — PASS

Reviewed files:

- `src/ai_infra_quant/application/paqs_e_research.py`;
- `src/ai_infra_quant/integrations/openai_reasoning/deepseek_research_flow.py`;
- `src/ai_infra_quant/frontend/static/paqs-e.js`.

`ResearchDiagnostic` now optionally includes bounded numeric fields:

- `provider_exposed_query_count`;
- `raw_source_record_count`;
- `unknown_action_count`.

Validation requires each optional count to be an exact integer within 0..1024.

The diagnostic counting helper:

- counts exposed query slots without copying query text;
- counts raw source/citation records without copying URLs/titles;
- counts unknown action records numerically;
- omits a count when the relevant shape is not safely knowable;
- saturates diagnostic representation at the bounded diagnostic maximum;
- does not project raw provider bodies or model memo text.

The secret-tainted response path intentionally constructs diagnostics without inspecting the tainted response, so query/source/action counts are omitted rather than risking secret projection.

The browser only renders strict numeric allowlisted fields and does not display:

- query strings;
- source URLs;
- provider response ID;
- arbitrary raw diagnostic JSON;
- raw API detail;
- reasoning text.

Result: **PASS**.

---

## 9. Source/citation safety preserved — PASS

R05 does not relax the source/citation safety boundary.

Reviewed behavior remains:

- maximum 64 raw source/citation records;
- URL <= 1000 characters;
- only HTTP/HTTPS;
- no embedded username/password;
- no whitespace/control/backslash-smuggled URL;
- syntactically valid hostname/port;
- known future-dated sources excluded from trusted provenance;
- arbitrary URLs appearing only in memo prose are not promoted as trusted sources.

The new diagnostics can expose `raw_source_record_count` numerically when a source multiplicity failure occurs, which should make any remaining provider mismatch observable in the next live gate.

Result: **PASS**.

---

## 10. Structural safety limits preserved — PASS

R05 continues to enforce the R04 local parser/transport safety limits rather than provider execution semantics:

- max 64 accepted DeepSeek `web_search_call` items;
- max 128 total SEARCH output items;
- max 64 raw source/citation records;
- max 256 exposed query strings;
- max 64,000 total exposed query characters;
- individual query <= 500 characters;
- bounded query persistence <= 16 items / <= 4,000 characters;
- existing 2 MB request/response bound in the DeepSeek research flow;
- exactly one SEARCH request;
- at most one SYNTHESIS request;
- no automatic retry.

Deterministic tests cover query-count, query-character, source-count, unknown-action, action-count, total-output and no-search failures and verify one-request failure behavior with bounded diagnostics.

Result: **PASS**.

---

## 11. API / Ledger integration regression — PASS by source inspection

Reviewed integration regression:

`tests/integration/test_paqs_e_search_multiplicity_api.py`

The regression covers Research-OFF, direct Research-ON and tool-only Research-ON with the live-like 20-call / 6-search shape.

Verified assertions include:

- successful final Narrative response remains exact provider prose;
- response SHA remains computed from exact prose;
- persisted request payload SHA readback remains valid;
- Research-ON freezes auxiliary context before final Narrative;
- frozen provenance records true query count/capture completeness;
- tool-only path records synthesis_used=true and two research HTTP requests;
- direct path records synthesis_used=false and one research HTTP request;
- Research-OFF freezes no auxiliary context;
- successful total provider call counts remain 1 (OFF), 2 (direct ON), or 3 (tool-only ON);
- a subsequent source-count research failure returns 422 without creating a Narrative Run/Result;
- existing successful Run/Result rows remain unchanged after that failure;
- SQLite schema remains unchanged;
- migration head remains `0003_task007c1_narrative_ledger`.

These are deterministic test-source assertions, not independently rerun test results.

Result: **PASS**.

---

## 12. Protected component audit — PASS by implementation diff

The R05 implementation diff from Contract commit `a86efee5...` to implementation `a3cc97d9...` does not modify:

- migrations 0001/0002/0003;
- Narrative database model/repository;
- Narrative domain/request schema;
- Narrative runtime prompt;
- PAQS-E primary strategy;
- Narrative final provider adapter;
- model registry;
- credential store;
- safe Markdown renderer;
- launcher/source revision code;
- market Snapshot construction;
- broker/execution functionality.

The only frontend change is the bounded numeric diagnostic display; research default-OFF and Markdown presentation code are not part of this R05 diff.

Result: **PASS**.

---

## 13. Codex-reported validation — handoff evidence only

The implementation report states:

- full suite: 1,263 passed, 1 existing optional PostgreSQL skip;
- browser suite: 92/92 passed;
- focused suite: 725 passed;
- Ruff check/format, mypy, startup smoke and protected-file audits passed;
- migration head remains 0003;
- no paid provider calls were made.

These numbers are not independently rerun in this review environment and therefore are not the basis of the independent PASS decision.

The independent decision is based on exact-SHA Git topology, implementation diff and direct source/test inspection.

---

## 14. Non-blocking observations

### 14.1 SEARCH instruction still requests at most four queries

The SEARCH prompt still asks the provider to use at most four search queries.

This is intentionally **advisory only** under R05. The application no longer rejects an otherwise valid paid provider response merely because DeepSeek ignored that advisory instruction and executed/exposed more searches.

This is contract-conforming and not a blocker.

### 14.2 `query_capture_complete` is provenance metadata, not failure diagnostic metadata

R05 authorized `query_capture_complete` as optional diagnostic data. The implementation records it in successful frozen provenance but does not expose it in failure diagnostics.

The mandatory diagnostic additions — provider_exposed_query_count, raw_source_record_count and unknown_action_count — are implemented.

This is contract-conforming and not a blocker.

---

## 15. Final acceptance gate

The exact implementation SHA cleared for live acceptance is:

`a3cc97d96887d9e31af4c3d56ab7206ef6600032`

Required live configuration remains:

```text
Security: US.AVGO
Model: DeepSeek V4 Flash
Strategy: paqs-e-master
Web Research: explicitly ON
```

One explicit Analyze only. No automatic or manual retry if the first live attempt fails.

### Success expectation

A successful run must produce a new Narrative Result with:

- `web_research=true`;
- non-empty frozen `auxiliary_context`;
- provider-native DeepSeek research memo content;
- bounded provenance showing actual provider-exposed multiplicity;
- valid request payload hash;
- valid response text hash;
- expected revision lineage from the prior successful AVGO Narrative;
- final Narrative still displayed via the safe Markdown view.

### Failure expectation

If Research-ON still fails, the browser should now expose enough bounded numeric evidence to identify the remaining SEARCH/SYNTHESIS parser boundary, including when available:

- stage;
- failure class;
- request count;
- web search call count;
- search action count;
- message count;
- provider exposed query count;
- raw source record count;
- unknown action count.

Do not retry automatically and do not merge on failure.

---

## 16. Merge decision

**MERGE NOT AUTHORIZED YET.**

Current review state:

```text
Narrative Research-OFF       LIVE PASS
Narrative Ledger             LIVE PASS
Long-running non-abort       LIVE PASS
Safe Markdown                CODE PASS
Research explicit opt-in     CODE PASS
DeepSeek SEARCH execution    LIVE CONFIRMED
R05 code / contract          PASS
DeepSeek Research-ON         LIVE ACCEPTANCE PENDING
Final TASK-007C1             BLOCKED pending live gate
Merge                        BLOCKED pending final PASS
```

After a successful live gate, independently re-check:

1. task branch HEAD still equals exact reviewed implementation SHA;
2. authoritative branch is unchanged;
3. merge base / ahead / behind topology remains valid;
4. live Run/Result request and response hashes verify;
5. frozen research auxiliary context is non-empty and bounded;
6. final review evidence is updated before integration.
