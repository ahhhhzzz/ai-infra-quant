# TASK-007C1 Remediation 06 — Independent Review

Status: **CODE / CONTRACT REVIEW PASS — DEEPSEEK RESEARCH-ON LIVE ACCEPTANCE PENDING**

Reviewed implementation SHA: `3e98d8c5f9948dcaefe59eb3b7b847bd99ba8908`

Remediation 06 Contract commit / direct implementation parent: `84d5e708a613293bd6edf36e0922b475de2ca368`

Remediation 06 implementation base: `a3cc97d96887d9e31af4c3d56ab7206ef6600032`

Authoritative branch: `roadmap/no-live-trading`

Authoritative SHA during review: `80f089bc2d285cca492c41aaeaf047e177bc2812`

Task branch: `task/007c1-paqs-e-multi-model-web-research`

Review branch: `review/007c1-remediation-06-independent`

Review date: 2026-09-08

This review is independent of the Codex implementation report. GitHub repository contents at the exact reviewed SHA are the source of truth. Claimed local test counts in the implementation report are treated as handoff evidence only and are not represented here as independently executed tests.

---

## 1. Git provenance gate — PASS

GitHub comparison verified:

- `84d5e708... -> 3e98d8c5...`: ahead 1 / behind 0;
- task branch HEAD equals exact reviewed SHA `3e98d8c5...`;
- authoritative `roadmap/no-live-trading` remains exactly `80f089bc...`;
- task branch is ahead 14 / behind 0 relative to authoritative;
- merge base remains exactly `80f089bc...`;
- no authoritative merge was performed during review.

The Remediation 06 implementation diff contains 14 changed files and is limited to:

- DeepSeek partial-action parsing semantics;
- parser-originated safe diagnostic metadata;
- bounded browser diagnostic projection;
- focused unit / integration / browser regressions;
- implementation and architecture/model/workbench/requirements documentation.

The R06 implementation diff does **not** contain:

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

No blocking code/contract defect was found in the Remediation 06 implementation at `3e98d8c5f9948dcaefe59eb3b7b847bd99ba8908`.

The code/contract review therefore passes this exact SHA to the next user-executed DeepSeek V4 Flash Research-ON live acceptance gate.

This is **not final TASK-007C1 PASS** until that live gate succeeds on this exact SHA and a final branch/topology gate confirms the task branch has not mutated.

Do not merge before the live gate.

---

## 3. Accepted prior live evidence remains authoritative

The previously accepted Research-OFF DeepSeek Narrative run remains valid evidence that:

- DeepSeek V4 Flash can produce the Narrative-first final answer;
- the final text can persist successfully in the Narrative Ledger;
- request and response SHA identities can be verified;
- a >180-second provider call can complete without browser abort;
- Research-OFF does not require auxiliary research context.

The previously observed Research-ON failures also remain useful compatibility evidence:

- Remediation 04 live: `SEARCH / INVALID_RESPONSE`, 20 research actions, 6 search actions, 0 messages;
- Remediation 05 live: `SEARCH / INVALID_RESPONSE`, 16 research actions, 7 search actions, 24 exposed queries, 0 sources, 0 unknown actions, 0 messages.

R06 is intentionally scoped to the remaining parser uncertainty exposed by those live observations.

---

## 4. R06-A — Recognized partial native action compatibility — PASS

Reviewed files:

- `src/ai_infra_quant/integrations/openai_reasoning/deepseek_research.py`
- `src/ai_infra_quant/integrations/openai_reasoning/deepseek_research_diagnostics.py`

Verified action status allowlist:

- `completed`;
- `in_progress`;
- `incomplete`;
- `failed`;
- `cancelled`.

Unknown or missing action status fails closed with application boundary `ACTION_STATUS`.

Action type remains restricted to:

- `search`;
- `open_page`;
- `find_in_page`.

Unknown action type still fails closed with `ACTION_TYPE`.

Malformed action objects still fail closed with `ACTION_SHAPE`.

For recognized non-completed actions, the parser:

- counts the status for diagnostics/provenance;
- does not parse query payload;
- does not parse source payload;
- does not add the native item to continuation/pass-back;
- does not persist the raw item;
- does not fail solely because the action is recognized but non-completed.

This matches the R06 trust model: partial actions are observations, not successful evidence.

---

## 5. R06-B — Completed-evidence filtering — PASS

Only `status == "completed"` native calls enter the positive-evidence path.

Verified behavior:

- only completed calls are copied into transient `NativeSearch.calls`;
- only completed `search` actions expose query/source metadata to trusted parsing;
- only completed accepted calls are passed into the optional SYNTHESIS request;
- reasoning items are ignored and never passed back;
- recognized non-completed action payloads are skipped before trusted query/source parsing.

At least one completed native `search` action is mandatory. Zero completed search actions fails closed with `NO_COMPLETED_SEARCH`.

This preserves the required distinction between provider activity and accepted evidence.

---

## 6. R04/R05 lifecycle preservation — PASS

The Remediation 04/05 architecture remains intact:

```text
Explicit user Research opt-in
↓
Freeze Snapshot
↓
SEARCH exactly once
↓
Validate accepted completed native evidence
↓
Direct memo fast path OR one optional SYNTHESIS
↓
Freeze one bounded research memo + provenance
↓
Unchanged final Narrative
↓
Narrative Ledger
```

Verified SEARCH request remains:

- registered DeepSeek endpoint/model/credential;
- `store=false`;
- `stream=false`;
- `reasoning.effort=none`;
- native web-search tool only;
- no retry/fallback/background/conversation/previous-response state.

Verified SYNTHESIS request remains:

- at most one request;
- same endpoint/model/credential;
- `tools=[]`;
- `tool_choice=none`;
- `reasoning.effort=none`;
- no retry/fallback;
- input contains original intent + only completed accepted native calls + synthesis instruction.

The final Narrative provider module is unchanged by R06.

---

## 7. R05 query multiplicity behavior remains preserved — PASS

R06 does not reintroduce the old `<=4` query acceptance cap.

Completed search evidence retains R05 behavior:

- max 256 provider-exposed query strings as a structural safety bound;
- max 64,000 total query characters as a structural safety bound;
- individual query integrity validation;
- max 16 retained query strings;
- max 4,000 retained query characters;
- truthful `provider_exposed_query_count`;
- truthful `query_capture_complete`.

Query/source payload on recognized non-completed search actions is deliberately not parsed or retained.

---

## 8. Source/citation safety remains unchanged — PASS

Trusted source parsing remains limited to accepted completed evidence.

Verified unchanged rules include:

- max 64 raw source/citation records;
- URL max 1000 characters;
- only HTTP/HTTPS;
- no embedded username/password;
- no whitespace/control/backslash smuggling;
- valid hostname/port;
- bounded source title;
- timezone-aware publication timestamps only when parseable;
- future-dated sources excluded from trusted provenance;
- arbitrary URLs in memo prose are never promoted to trusted citations.

R06 does not broaden source authority.

---

## 9. R06-C — Exact parser diagnostics — PASS

Reviewed files:

- `src/ai_infra_quant/application/paqs_e_research.py`
- `src/ai_infra_quant/integrations/openai_reasoning/deepseek_research_diagnostics.py`
- `src/ai_infra_quant/integrations/openai_reasoning/deepseek_research_flow.py`

`ResearchDiagnostic` now has an allowlisted `boundary_code` plus bounded numeric counters.

Allowlisted boundary codes cover the SEARCH and SYNTHESIS rule classes required by the Contract, including:

- envelope/output/action/status/quorum;
- query/source/message integrity;
- pass-back/provenance bounds;
- synthesis envelope/output/message/memo integrity.

`NativeParseFailure` originates at the actual rejecting rule and carries a copied read-only numeric observation map. The adapter projects only the allowlisted boundary and bounded counters.

This is materially stronger than a generic failure followed by best-effort inference.

---

## 10. Diagnostic safety — PASS

Verified diagnostic properties:

- `boundary_code` must be in the application allowlist;
- numeric fields require exact integers, not booleans;
- numeric fields are bounded;
- unknown totals are omitted rather than guessed;
- no query text is projected;
- no memo text is projected;
- no source URL/title is projected;
- no raw native item is projected;
- no provider body/error/refusal text is projected;
- no reasoning text is projected;
- no hidden instructions are projected;
- no credential/Authorization material is projected.

Secret-tainted provider responses fail before detailed reparse; detailed counts/boundary data requiring inspection of the tainted body are omitted.

This satisfies the R06 secret-echo boundary.

---

## 11. Browser projection — PASS

The browser keeps the existing safe failure state and adds only allowlisted diagnostics.

Verified client-side validation covers:

- detail version;
- stage;
- failure class;
- request count;
- primary action/search/message counts;
- allowlisted boundary code;
- bounded optional numeric fields.

The UI does not display arbitrary diagnostic keys, raw JSON, provider response id, query text, URL data or provider detail text.

Research remains default OFF and model changes continue to reset the checkbox to OFF.

---

## 12. Live-like regression — PASS as deterministic code evidence

Synthetic live-like fixture models:

- 16 native calls;
- 7 native search actions;
- 24 query slots on completed searches;
- 0 sources;
- 0 final messages;
- 13 completed actions;
- 1 incomplete search;
- 1 failed open-page action;
- 1 in-progress find action;
- 6 completed searches.

Reviewed tests prove:

- recognized partial actions do not invalidate the whole SEARCH;
- malformed query/source payload inside partial actions is ignored as untrusted;
- only 13 completed items are passed to SYNTHESIS;
- one and only one SYNTHESIS request is used on tool-only success;
- direct memo fast path works with partial actions;
- final Narrative runs only after research memo freezing;
- research precondition failure creates no new Narrative Run/Result;
- SQLite schema remains 0003 in integration fixtures;
- prior rows remain unchanged after failed research attempts.

This is deterministic compatibility evidence, not a substitute for the final real provider smoke.

---

## 13. Exact failure boundary regressions — PASS

Unit tests explicitly exercise and assert the expected application boundary for representative failures, including:

- SEARCH envelope/model/id;
- malformed/unknown output;
- malformed action;
- unknown action type;
- unknown/missing status;
- no completed search quorum;
- malformed/invalid/oversize query;
- source shape/count/URL/title/port/UTF-8;
- message shape/integrity;
- pass-back/provenance bounds;
- action/output bounds;
- SYNTHESIS envelope/output/message/memo failures.

Tests also assert the parser's internal `NativeParseFailure.boundary_code` matches the externally projected diagnostic boundary for a representative query-integrity failure.

---

## 14. Protected-component audit — PASS by GitHub diff

The R06 implementation diff does not modify:

- `src/ai_infra_quant/integrations/openai_reasoning/narrative.py`;
- Narrative domain/schema/repository/ledger files;
- migration 0001;
- migration 0002;
- migration 0003;
- PAQS-E primary strategy;
- Narrative runtime prompt;
- model registry/endpoints;
- credential-store implementation;
- safe Markdown renderer;
- template/CSS;
- launcher/source-revision code;
- legacy validator;
- market-data/Snapshot construction.

No migration 0004 exists in the R06 diff.

---

## 15. Test evidence treatment

Codex reports at the implementation SHA:

- full suite: 1,339 passed, one existing optional PostgreSQL skip;
- browser suite: 99 passed;
- focused suite: 801 passed;
- Ruff / format / mypy / migration / startup / protected-file audits passed.

These results are implementation handoff evidence. They were not independently rerun in this GitHub-only review and therefore are not the basis of the independent PASS conclusion.

The independent PASS is based on exact-SHA Git topology, changed-file scope, inspected source behavior, inspected deterministic tests, and contract correspondence.

---

## 16. Non-blocking observations

### 16.1 SEARCH instruction still asks for at most four search queries

The provider instruction still says `Research with at most four search queries.`

This is an advisory prompt, not a local acceptance invariant. R05 correctly removed the post-hoc four-query rejection. Because the real provider has already exceeded four searches/queries and the implementation now tolerates provider-owned multiplicity within structural safety bounds, this wording is not a blocker.

### 16.2 Generic fallback exception path remains

The adapter retains a generic bounded exception fallback for unexpected Python exceptions. Known parser rules now use `NativeParseFailure` with exact boundary codes. The generic fallback is therefore a safety net rather than the primary diagnostic path and is non-blocking.

---

## 17. Required live acceptance gate

After this independent code/contract PASS, execute exactly one real user-authorized Research-ON smoke on the exact reviewed implementation SHA:

- Security: `US.AVGO`;
- model: DeepSeek V4 Flash;
- strategy: `paqs-e-master`;
- research manually checked ON;
- no automatic or manual immediate retry if it fails.

Before the paid smoke, verify runtime source identity equals:

`3e98d8c5f9948dcaefe59eb3b7b847bd99ba8908`

and migration head remains:

`0003_task007c1_narrative_ledger`.

### If live succeeds

Verify at minimum:

- status `SUCCEEDED`;
- `web_research=true`;
- frozen auxiliary context is non-empty;
- one DeepSeek native research memo is frozen;
- provenance identifies one-stage or two-stage research accurately;
- partial action counts, if exposed, are bounded and truthful;
- final Narrative text is persisted exactly;
- request SHA verifies;
- response SHA verifies;
- revision lineage is correct;
- final Narrative remains tool-free;
- task branch has not mutated after review.

### If live fails

Do not retry immediately. Capture the full safe diagnostic line, especially:

- stage;
- failure class;
- `boundary_code`;
- research request count;
- web-search/action/search/message counts;
- per-status action counts;
- completed/non-completed search counts;
- query/source/unknown-action counters;
- malformed/invalid counters when present.

The purpose of R06 is that any remaining failure should identify the exact local parser boundary without exposing provider bodies or secrets.

---

## 18. Final status

**CODE / CONTRACT REVIEW PASS — DEEPSEEK RESEARCH-ON LIVE ACCEPTANCE PENDING**

Reviewed exact implementation:

`3e98d8c5f9948dcaefe59eb3b7b847bd99ba8908`

Do not merge yet.
