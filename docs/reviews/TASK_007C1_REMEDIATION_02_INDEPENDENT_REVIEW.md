# TASK-007C1 Remediation 02 — Independent Review

Status: **CODE / CONTRACT REVIEW PASS — LIVE PROVIDER ACCEPTANCE PENDING**

Reviewed implementation SHA: `74a19387adc408e9453c30fdbb30e6636ac4e695`

Remediation 02 Contract commit / direct implementation parent: `ca1b71f94565dee02f0bd43d280a59f3ec15ac6d`

Authoritative branch: `roadmap/no-live-trading`

Authoritative SHA during review: `80f089bc2d285cca492c41aaeaf047e177bc2812`

Task branch: `task/007c1-paqs-e-multi-model-web-research`

Review branch: `review/007c1-remediation-02-independent`

Review date: 2026-09-08

This review is independent of the Codex implementation report. GitHub repository contents at the exact reviewed SHA are the review source of truth. The implementation report and its claimed local test counts are supporting handoff evidence only; they are not treated as independently executed validation here.

---

## 1. Git provenance gate

GitHub comparison verified:

- `ca1b71f... -> 74a19387...`: ahead 1 / behind 0;
- task branch HEAD equals exact reviewed SHA `74a19387...`;
- authoritative `roadmap/no-live-trading` remains exactly `80f089bc...`;
- task branch is ahead 6 / behind 0 relative to authoritative;
- merge base remains exactly `80f089bc...`;
- no authoritative merge was performed during review.

The Remediation 02 implementation diff contains the authorized narrative-first additions, including the additive `0003_task007c1_narrative_ledger` migration and does not list the legacy validator source, PAQS-E master strategy source, or migrations 0001/0002 as Remediation-02 changes.

---

## 2. Review conclusion

No blocking code/contract defect was found in the Narrative-first implementation at `74a19387...`.

The code review therefore passes the implementation to the separate user-executed live-provider gate.

This is **not yet final TASK-007C1 PASS**, because Remediation 02 explicitly requires live DeepSeek V4 Flash product acceptance on this exact SHA.

Do not merge until the live gate passes and a final SHA/topology gate confirms the task branch has not changed.

---

## 3. Narrative-first architecture — PASS

The normal Analyze path is now distinct from the legacy structured reasoning path.

Verified behavior:

- browser POST target is `/api/v1/paqs-e/narrative-analyses`;
- new analyses use `NarrativeAnalysisService`;
- a distinct `NarrativeRequest` identity is used;
- narrative output format is `paqs-e-narrative-markdown-v1`;
- narrative prompt is `paqs-e-narrative-prompt-v1`;
- final model text is the analysis result;
- no `PaqsEReasoningResultV1` is required for narrative success;
- no narrative call invokes `validate_reasoning_result(...)`;
- the old structured runtime remains present only for legacy compatibility/tests/history.

The new narrative prompt explicitly states that its report order is a writing guide rather than a machine schema and tells the model to return final visible text directly rather than JSON.

---

## 4. Provider request path — PASS

`NarrativeGateway.reason_text(...)` is provider-neutral and resolves the selected route through the existing controlled model registry and credential system.

For Responses-style final reasoning, the request contains ordinary text instructions/input plus:

- `stream=false`;
- `store=false`;
- `tools=[]`;
- `tool_choice=none`.

It does **not** send the legacy `text.format=json_schema` body.

For Chat-style final reasoning, it sends ordinary messages and does **not** send `response_format=json_schema` or `response_format=json_object` for the PAQS-E result.

Existing no-hidden-search provider controls remain in place for Chat routes that previously required them.

The shared bounded transport still uses:

- fixed registry endpoints;
- no redirects;
- no provider/model fallback;
- no retry middleware;
- `trust_env=false`;
- bounded HTTP response bytes.

---

## 5. Final-text integrity — PASS

Narrative success is based on transport/integrity rather than semantic approval.

Verified checks include:

- non-empty string final text;
- maximum 100,000 Unicode characters;
- UTF-8 encodability;
- rejection of unsafe control characters;
- bounded/safe provider response id when stored;
- selected model identity check when supplied by the provider;
- secret-echo rejection;
- refusal handling;
- failed/incomplete/cancelled response handling;
- unexpected tool/final-content shape rejection;
- internal reasoning output is ignored rather than persisted/displayed.

The final prose is not parsed as JSON, even when the prose itself happens to contain JSON-looking text.

No automatic paid retry is introduced.

---

## 6. Snapshot / strategy / prompt identity — PASS

The narrative request binds:

- Security identity;
- symbol/market/instrument;
- Snapshot hash;
- Snapshot As-Of timestamp;
- current-analysis mode;
- exact model provider/model id;
- primary strategy id and SHA-256;
- narrative prompt version and SHA-256;
- runtime config identity;
- complete frozen market Snapshot;
- ordered auxiliary context;
- web-research flag.

`NarrativeRequest.__post_init__` rejects mismatched Snapshot identity, unsupported request/output/prompt versions, unsupported runtime scope, invalid artifact hashes/identities, duplicate auxiliary ids, non-web auxiliary material in this task, and auxiliary evidence that violates the Snapshot cutoff.

The new narrative prompt does not modify the PAQS-E primary strategy Markdown.

---

## 7. Web research separation — PASS

The accepted R2 architecture remains separate from final reasoning.

`NarrativeAnalysisService` performs requested research before building the final immutable narrative request. When research is disabled, auxiliary context is empty. When enabled, the resulting normalized capsule becomes explicit request evidence.

Final narrative reasoning itself remains tool-free.

No silent continue-without-research path, provider fallback, model fallback or retry was introduced.

Remediation 01's DeepSeek `search/open_page/find_in_page` provenance handling remains outside the narrative final-answer parser and was not weakened by Remediation 02.

---

## 8. Narrative Ledger / migration 0003 — PASS

Migration `0003_task007c1_narrative_ledger` is a direct child of `0002_task007b_paqs_e_ledger` and adds only:

- `paqs_e_narrative_runs`;
- `paqs_e_narrative_results`;
- their indexes/constraints;
- SQLite immutability/lineage triggers.

The migration does not edit 0001 or 0002.

Narrative Runs persist the canonical request payload and SHA-256 plus Snapshot/model/strategy/prompt/runtime/research identities and terminal provider status.

Narrative Results persist exact final text plus SHA-256 and use their own revision series keyed by:

`security_id + strategy_id`

Model/provider changes therefore do not reset narrative revision numbering, while narrative revisions remain independent from the old structured Decision revision series.

The repository serializes revision allocation with SQLite `BEGIN IMMEDIATE`; non-SQLite paths lock the Security row before revision allocation.

SQLite triggers prevent UPDATE/DELETE of Narrative Run/Result evidence and verify successful-parent and predecessor lineage on Result insertion.

A successful Run is verified to have exactly one Result; provider-failed Runs have none.

---

## 9. Legacy structured evidence — PASS

The production app initializes with `legacy_analysis_enabled=False`.

Legacy structured `POST /api/v1/paqs-e/analyses`:

- is absent from normal OpenAPI exposure;
- returns HTTP 410 by default;
- can only be enabled by an explicit in-process constructor argument intended for legacy regression tests.

There is no environment, browser or public API switch enabling legacy Analyze.

Existing structured GET history/Decision/Run reads remain available as legacy evidence.

The UI separates primary Narrative history from a clearly labeled legacy structured history section.

No prose-to-legacy-field extraction is implemented.

---

## 10. Browser rendering / XSS / long-running behavior — PASS

Narrative response text is rendered using DOM `textContent` into a `<pre>` element rather than inserted as HTML.

The browser regression includes hostile model strings containing `<script>`, `<img onerror>` and `javascript:` link syntax and verifies that no executable script/image/link nodes are produced.

The persisted text is displayed exactly, including multiline content.

The 180-second behavior remains informational only:

- it does not abort the request;
- it does not release the global in-flight guard;
- a second submit does not produce a second POST;
- later terminal success/failure remains authoritative;
- genuine network/response ambiguity retains the no-auto-retry unknown-outcome guidance.

Frozen Snapshot evidence remains separate from the model prose and current market refresh does not rewrite the selected historical Snapshot.

---

## 11. Independent test-source inspection

The review inspected the new/modified test sources rather than accepting only the reported counts.

Observed coverage includes:

- all registered models accepting ordinary final text without structured-output request fields;
- exact prose, short prose, JSON-looking prose and the 100k bound;
- empty/whitespace/oversize/control/surrogate/secret/model-id/refusal/incomplete/tool/failed/network/missing/multiple/wrong-role cases;
- no retry and no raw provider diagnostic retention;
- narrative request identity/version guards;
- narrative API/ledger revision and evidence semantics;
- browser exact-text/XSS rendering;
- narrative read-race protection;
- provider/research/unknown failure retention of prior successful narrative;
- explicit Analyze-only POST behavior;
- long-running non-aborting behavior;
- SQLite migration head and preservation of earlier schema/data.

The Codex handoff reports `1,068 passed`, one optional PostgreSQL skip, `65` browser passes and `334` focused passes. Those counts are recorded as implementation-reported evidence, not independently re-executed by this review.

---

## 12. Non-blocking observation

Failed Narrative Runs currently do not retain a provider response id because `NarrativeFailure` carries only a failure kind. A provider may sometimes supply a safe response id even when the final answer is incomplete/refused/invalid.

This does not block the current product acceptance gate because:

- failure evidence remains bounded and truthful;
- no raw provider body or reasoning is retained;
- successful narrative Runs/Results retain the safe provider response id;
- the primary acceptance objective is successful final-text persistence/display.

If failed-call provider correlation becomes operationally important, it should be addressed by a future narrow auditability task rather than reopening Narrative semantics.

---

## 13. Remaining live acceptance gate

Before final PASS and integration, the user must run on exact SHA `74a19387adc408e9453c30fdbb30e6636ac4e695`:

1. DeepSeek V4 Flash, web research **OFF**, one explicit Analyze;
2. if successful, DeepSeek V4 Flash, web research **ON**, one explicit Analyze.

Do not automatically retry either paid call.

For research-OFF success, verify at minimum:

- UI reaches `SUCCEEDED` Narrative;
- final visible model text is shown;
- Narrative Run ID and Narrative Result ID exist;
- persisted response SHA exists;
- no legacy structured Decision is fabricated.

For research-ON success, additionally verify:

- final Narrative succeeds;
- its frozen Narrative Run request contains non-empty `auxiliary_context[]` with `category=web_research`;
- source evidence is visible separately from the narrative prose;
- final reasoning did not perform hidden tool calls.

A provider failure, research precondition failure, corrupted ledger read, or branch mutation blocks final PASS and requires diagnosis before merge.

---

## 14. Final state at this review commit

**CODE / CONTRACT REVIEW: PASS**

**LIVE PRODUCT ACCEPTANCE: PENDING**

**FINAL TASK-007C1 PASS: PENDING**

**MERGE: NOT AUTHORIZED / NOT PERFORMED**

After both live smokes pass, re-confirm:

- task HEAD still equals the exact live-tested implementation SHA;
- authoritative HEAD is unchanged;
- merge base is unchanged;
- task branch remains a clean fast-forward candidate;
- review evidence is finalized against the exact tested SHA.
