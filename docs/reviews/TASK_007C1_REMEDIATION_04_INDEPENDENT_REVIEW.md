# TASK-007C1 Remediation 04 — Independent Review

Status: **CODE / CONTRACT REVIEW PASS — DEEPSEEK RESEARCH-ON LIVE ACCEPTANCE PENDING**

Reviewed implementation SHA: `a82340db89be0e2a47583b03f97fb28218dd7a09`

Remediation 04 Contract commit / direct implementation parent: `e6fe791a5c99033da77a8bc877e772e0c84f55df`

Remediation 04 implementation base: `a9c7eabd1862d491f61843dfc68cbc3a1d9c936f`

Authoritative branch: `roadmap/no-live-trading`

Authoritative SHA during review: `80f089bc2d285cca492c41aaeaf047e177bc2812`

Task branch: `task/007c1-paqs-e-multi-model-web-research`

Review branch: `review/007c1-remediation-04-independent`

Review date: 2026-09-08

This review is independent of the Codex implementation report. GitHub repository contents at the exact reviewed SHA are the source of truth. Claimed local test counts in the implementation report are handoff evidence only and are not represented here as independently executed tests.

---

## 1. Git provenance gate — PASS

GitHub comparison verified:

- `e6fe791a... -> a82340db...`: ahead 1 / behind 0;
- task branch HEAD equals exact reviewed SHA `a82340db...`;
- authoritative `roadmap/no-live-trading` remains exactly `80f089bc...`;
- task branch is ahead 10 / behind 0 relative to authoritative;
- merge base remains exactly `80f089bc...`;
- no authoritative merge was performed during review.

The Remediation 04 implementation diff is limited to research state-machine/diagnostic code, bounded UI diagnostic projection, tests and documentation. It does not contain:

- a database migration;
- edits to migrations 0001/0002/0003;
- Narrative Ledger schema/repository changes;
- PAQS-E primary strategy changes;
- Narrative runtime prompt changes;
- Narrative provider final-text changes;
- safe Markdown renderer changes;
- model registry or provider endpoint changes;
- credential-store changes;
- launcher/source-revision changes;
- broker/trading additions.

---

## 2. Review conclusion

No blocking code/contract defect was found in the Remediation 04 implementation at `a82340db...`.

The code/contract review therefore passes this exact SHA to the final user-executed DeepSeek V4 Flash Research-ON live acceptance gate.

This is **not final TASK-007C1 PASS** until that live gate succeeds on this exact SHA and a final branch/topology gate confirms the task branch has not mutated.

Do not merge before the live gate.

---

## 3. External provider-semantics cross-check — PASS

Current official DeepSeek Responses documentation was checked during review.

The implementation's core compatibility assumptions match the documented provider contract:

- Responses API is stateless;
- `previous_response_id` is unsupported;
- `conversation` is unsupported;
- `web_search_call` is a supported output item and supported input item;
- official compatibility guidance says `web_search_call` may be passed back as-is and the server restores search results;
- `tool_choice={"type":"web_search"}` is supported;
- `tool_choice="none"` is supported;
- `reasoning.effort="none"` disables thinking;
- server-side web-search auto-continuation is capped at 10 rounds, which is not a documented maximum count for returned `web_search_call` output items.

The implementation no longer uses the R03 assumption that 11 returned search-call items must fail.

---

## 4. DeepSeek-only routing — PASS

`ModelGateway.research(...)` now delegates DeepSeek research to the dedicated `research_native(...)` state machine before the legacy source-normalized research body is built.

Consequences verified:

- DeepSeek uses the new bounded SEARCH / optional SYNTHESIS path;
- OpenAI / Alibaba/Qwen continue using the previous research normalization path;
- DeepSeek-specific continuation semantics are not generalized to other providers;
- model registry and provider endpoints remain unchanged.

The old `normalize_research(...)` function still contains a historical DeepSeek-specific count branch, but DeepSeek no longer reaches that function through normal routing. This is dead/redundant compatibility code, not a runtime blocker.

---

## 5. SEARCH request #1 — PASS

The DeepSeek SEARCH request is bounded and deterministic:

- one registered DeepSeek Responses endpoint;
- same selected model and secure credential;
- `stream=false`;
- `store=false` compatibility field;
- `reasoning={"effort":"none"}`;
- `tools=[{"type":"web_search"}]`;
- forced `tool_choice={"type":"web_search"}`;
- `max_output_tokens=6000`;
- original bounded Security / Snapshot As-Of intent;
- factual research-only instructions;
- no PAQS-E trading analysis request;
- no `previous_response_id`;
- no `conversation`;
- no background mode;
- no app retry loop.

The request body itself is bounded before transport.

---

## 6. SEARCH response acceptance — PASS

The first provider envelope is checked before continuation:

- response must be an object;
- top-level status must be `completed`;
- no top-level error;
- provider model must match when supplied;
- provider response id must satisfy a strict safe-id pattern when supplied;
- secret echo fails closed;
- response body remains bounded;
- output list is bounded to 128 total items;
- only `reasoning`, `web_search_call`, and a valid final assistant message are accepted;
- reasoning items are ignored and not retained;
- each search call must be completed;
- action must be one of `search`, `open_page`, `find_in_page`;
- at least one real `search` action is required;
- provider-exposed query strings remain capped at four;
- raw source/citation records remain capped at 64;
- unsafe URLs/userinfo/ports/hostnames fail closed;
- future-dated known citations are excluded from trusted provenance.

The local action bound is now 64, so 11 completed search-call items do not fail merely because the count is 11.

---

## 7. Direct memo fast path — PASS

If SEARCH returns exactly one acceptable final assistant memo in addition to valid search actions:

- that memo is accepted directly;
- no SYNTHESIS request is issued;
- `synthesis_used=false`;
- `research_http_request_count=1`;
- the memo is frozen into one auxiliary-context item;
- final Narrative reasoning remains the next separate provider call.

This preserves the lowest-cost successful path.

---

## 8. Tool-only SEARCH continuation — PASS

If SEARCH is valid and contains real completed search actions but no final memo, the implementation performs exactly one SYNTHESIS request.

The accepted `web_search_call` objects are deep-copied for isolation but otherwise passed back as provider objects without rewriting their fields.

The continuation input contains only:

1. the original research intent as a user message;
2. the accepted completed `web_search_call` items;
3. one final user synthesis instruction.

It does not pass reasoning items back.

It does not pass arbitrary SEARCH message prose through the tool-only path.

It does not use provider-side response state identifiers.

---

## 9. SYNTHESIS request #2 — PASS

The optional synthesis request is strictly tool-free:

- same DeepSeek endpoint/model/credential;
- one request only;
- `stream=false`;
- `store=false` compatibility field;
- `reasoning={"effort":"none"}`;
- `tools=[]`;
- `tool_choice="none"`;
- `max_output_tokens=4000`;
- no `previous_response_id`;
- no `conversation`;
- no background mode;
- no PAQS-E strategy Markdown;
- no final Narrative runtime prompt;
- no web search or other tool is available.

The synthesis instruction is limited to factual memo generation from restored native search results and the original As-Of-bounded intent.

---

## 10. SYNTHESIS acceptance — PASS

The synthesis envelope uses the same top-level safety checks as SEARCH and additionally requires:

- bounded output list;
- no search/function/unknown tool output;
- reasoning output may be ignored but never retained;
- exactly one valid assistant message;
- exactly one visible final text part;
- no refusal;
- non-empty text;
- UTF-8 encodable text;
- no forbidden control characters;
- final memo <= 24,000 Unicode characters;
- final frozen memo + provenance + label must remain inside the existing auxiliary capsule bound.

The memo is not parsed as JSON and is not semantic-validated as a PAQS-E result.

---

## 11. Provider request-count ceiling — PASS

The R04 control flow structurally permits:

- Research OFF: zero research requests + unchanged final Narrative;
- Research ON direct memo: one research request + final Narrative;
- Research ON tool-only: two research requests + final Narrative.

There is no loop in `research_native(...)` and no provider retry middleware was added.

A failed SEARCH stops after one research HTTP request.

A failed SYNTHESIS stops after two research HTTP requests.

No failure path falls through to final Narrative reasoning.

---

## 12. Frozen evidence / persistence boundary — PASS

Raw SEARCH/SYNTHESIS provider bodies are not persisted.

Raw `web_search_call` transport items are transient only.

The frozen auxiliary item contains:

- exact accepted memo text;
- bounded canonical provenance metadata;
- safe provider/model identity;
- search response id when safe;
- search action counts/types;
- bounded queries when exposed;
- safe citations/sources when exposed;
- excluded future-source count;
- synthesis-used flag;
- synthesis response id when safe;
- research HTTP request count;
- explicit provenance limitation.

The frozen evidence does not contain:

- chain-of-thought;
- reasoning item content;
- opaque search restore tokens/items;
- API credential;
- Authorization header;
- raw provider body;
- arbitrary provider exception body.

The final Narrative request receives only this frozen auxiliary item, not raw continuation transport material.

---

## 13. Research diagnostics — PASS

`ResearchFailure` now optionally carries a frozen `ResearchDiagnostic` with allowlisted fields only.

Verified diagnostic vocabulary includes:

- `stage = SEARCH | SYNTHESIS`;
- bounded `failure_class`;
- provider/model identity;
- synthesis-attempted boolean;
- research request count 1 or 2;
- allowlisted provider status;
- safe provider response id;
- search-call/search-action/message counts;
- allowlisted incomplete reason only (`max_output_tokens` / `content_filter`);
- fixed diagnostic version.

The implementation intentionally discards arbitrary provider error strings and exception messages.

Secret-tainted provider envelopes are not inspected for diagnostic metadata.

API projection retains the existing `PAQS_E_RESEARCH_PRECONDITION_FAILED` contract and includes the diagnostic only as safe extra metadata.

Research precondition failure still creates no Narrative Run/Result.

---

## 14. Browser diagnostic projection — PASS

The browser validates diagnostic version/stage/failure class/count ranges before rendering a concise diagnostic suffix.

The normal UI does not render:

- provider raw body;
- arbitrary API `detail` for research failure;
- provider response id;
- reasoning;
- raw JSON diagnostic object.

It displays only stage/class and bounded counts.

The prior Narrative remains selected after research failure.

---

## 15. Cost / explicit intent UX — PASS

R03 explicit research opt-in remains intact:

- research default OFF;
- model changes reset OFF;
- unsupported models remain disabled/OFF;
- no remembered research opt-in;
- only explicit user selection submits `web_research=true`.

The disclosure now says enabling research may add up to two research requests before final analysis and may increase latency/API cost.

---

## 16. Research-OFF path protection — PASS BY DIFF / INTEGRATION DESIGN

Remediation 04 does not modify:

- `NarrativeGateway.reason_text(...)`;
- Narrative result domain;
- Narrative Ledger repository/schema;
- Narrative runtime prompt;
- response-text hashing;
- request hashing.

Integration fixtures explicitly cover Research-OFF, direct-memo Research-ON and tool-only Research-ON with the same final Narrative provider path.

The already accepted real Research-OFF evidence at the earlier exact SHA remains valid historical acceptance evidence. No additional paid Research-OFF call is required by this review because R04 did not modify that protected final-text path.

---

## 17. Database / migrations — PASS

No migration appears in the R04 implementation diff.

Expected migration head remains:

`0003_task007c1_narrative_ledger`

R04 integration tests inspect the SQLite schema before and after failed research attempts and require exact equality.

No research diagnostic is persisted into the Narrative Ledger on precondition failure.

---

## 18. No-live-trading boundary — PASS

No R04 changed file introduces:

- broker account access;
- real brokerage observation;
- order creation/cancellation/modification;
- trade unlock;
- OMS/EMS;
- autonomous execution;
- background Analyze;
- provider fallback;
- model voting;
- PAQS-Q;
- portfolio/PnL or execution scope.

The task remains research/decision-support only.

---

## 19. Test-design review — PASS

The new deterministic tests materially cover the live failure mechanism rather than only happy-path mocks.

Notable covered cases include:

- one direct memo;
- 11 completed calls with direct memo;
- 11-call tool-only response;
- exact pass-back equality of accepted search-call objects;
- no reasoning pass-back;
- max 64 action items;
- max 128 total output items;
- no real search action;
- unknown/incomplete actions;
- wrong model / unsafe id / secret echo;
- transport failure;
- incomplete/failed/cancelled envelope;
- refusal;
- query/source/request bounds;
- synthesis web-tool/unknown output rejection;
- missing/empty/multiple memo rejection;
- oversize/control/invalid UTF-8 memo rejection;
- safe diagnostic redaction;
- no failure rows;
- final request/response SHA readback;
- migration head unchanged;
- browser diagnostic rendering and cost disclosure.

Codex reports 1,203 full tests and 85 browser tests, but those counts were not independently executed by this review environment.

---

## 20. Non-blocking observations

### 20.1 Legacy DeepSeek branch remains inside `normalize_research(...)`

The generic source-normalized normalizer still contains a DeepSeek-specific `max_actions=10` branch from the older architecture. Normal DeepSeek routing now returns through `research_native(...)` before that function is used, so this branch is unreachable for the registered DeepSeek research path.

This is maintainability debt only and should not be removed inside this already-reviewed SHA merely for cleanup.

### 20.2 Live provider shape is still the decisive remaining evidence

Static/code tests can establish that tool-only output is handled correctly *if* the provider returns the documented item shape. They cannot prove DeepSeek's paid endpoint will accept the exact reconstructed continuation body in production or that its live search output will satisfy the bounded parser.

That is precisely what the final live gate must verify.

---

## 21. Final review status

**CODE / CONTRACT REVIEW: PASS**

Exact reviewed SHA:

`a82340db89be0e2a47583b03f97fb28218dd7a09`

Remaining required evidence:

- one user-executed real DeepSeek V4 Flash Research-ON analysis on this exact SHA;
- if successful: verify persisted Narrative Run/Result, `web_research=true`, non-empty frozen auxiliary context, one- or two-stage provenance, request hash and response hash;
- if failed: use the new bounded `research_diagnostic` stage/counts to decide whether any further remediation is justified;
- final Git topology gate before any merge.

Do not merge until the live gate passes.
