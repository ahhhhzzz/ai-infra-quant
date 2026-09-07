# TASK-007C1 Remediation 01 — Independent Re-Review

Status: **CODE / CONTRACT REVIEW PASS — FINAL ACCEPTANCE PENDING USER-EXECUTED LIVE DEEPSEEK SMOKES**

Reviewed repository: `ahhhhzzz/ai-infra-quant`

Authoritative branch at review: `roadmap/no-live-trading`

Authoritative SHA: `80f089bc2d285cca492c41aaeaf047e177bc2812`

TASK-007C1 branch: `task/007c1-paqs-e-multi-model-web-research`

Original TASK-007C1 Contract SHA: `9f41016b2341e91ad2825b7f731bca4f378b0108`

Original TASK-007C1 implementation SHA: `fc527c61fcdc2b4f54506dc5622f0b1faa6945d5`

Remediation 01 Contract SHA: `b7316e83f7fd377f4c628db90dee8e3d7b4a5335`

Exact remediation implementation SHA reviewed: `6681fc6a934f44d29879c2ef1152891c3bd3a0d5`

Review branch: `review/007c1-remediation-01-independent`

This review is independent of the implementation report. GitHub repository contents, exact refs and commit comparisons are the source of truth. The implementation report was read only as a claimed-validation inventory after the code review findings were established.

---

## 1. Git / scope verification

GitHub compare and ref evidence confirms:

- `6681fc6a934f44d29879c2ef1152891c3bd3a0d5` is exactly the current TASK-007C1 task-branch HEAD at this review point;
- its sole parent is the Remediation 01 Contract commit `b7316e83f7fd377f4c628db90dee8e3d7b4a5335`;
- the remediation implementation is exactly one commit ahead of that Contract;
- the task branch is 4 ahead / 0 behind `roadmap/no-live-trading`;
- merge base remains exact authoritative SHA `80f089bc2d285cca492c41aaeaf047e177bc2812`;
- authoritative HEAD remains unchanged;
- the remediation diff contains only the approved R1-R4 implementation/docs/tests plus the remediation report;
- no database migration, accepted review evidence, model registry, PAQS-E strategy Markdown, Doctrine or runtime prompt semantic content was changed by the remediation implementation.

No merge or integration claim is accepted at this stage.

---

## 2. Review conclusion

No remediation code blocker was found in the GitHub implementation of R1-R4.

The four real dogfood defects are addressed within the authorized scope:

1. **R1 stale-backend launcher reuse:** corrected with a startup-frozen source-revision handshake.
2. **R2 DeepSeek native web-search actions:** corrected to support documented `search`, `open_page`, and `find_in_page` actions without weakening native-source provenance.
3. **R3 180-second browser abort:** corrected to a non-aborting long-wait notice while the single synchronous Analyze remains guarded.
4. **R4 deterministic Snapshot fact echo mismatch:** corrected by provider-neutral deterministic projection after strict provider parsing and before the unchanged deterministic validator.

The implementation therefore passes independent static contract/code review on exact SHA `6681fc6a934f44d29879c2ef1152891c3bd3a0d5`.

**This is not yet final TASK-007C1 PASS.** The Remediation Contract and original TASK-007C1 acceptance model require live product evidence on this exact final SHA using the user's real DeepSeek credential. Final acceptance remains gated on the two live smokes in section 8.

---

## 3. R1 — startup-frozen source revision handshake

Implementation reviewed:

- `src/ai_infra_quant/backend/runtime_identity.py`
- `src/ai_infra_quant/backend/main.py`
- `scripts/dashboard_runtime.ps1`
- `start_dashboard.bat`
- `tests/integration/test_runtime_source_revision.py`

The application captures `AI_INFRA_SOURCE_REVISION` once during `create_app()` and exposes only a validated 40-character lowercase Git SHA or `unknown` in `/health`. It does not reread Git or the environment on later health requests.

The launcher resolves the current checkout SHA before deciding whether an existing port-8000 service is reusable. The PowerShell helper accepts an existing backend only when health is good **and** the running service's startup-captured revision exactly equals the current checkout revision.

A healthy but stale/missing/invalid source revision returns a dedicated mismatch status and instructs the user to close/restart the old dashboard. The launcher does not automatically terminate a process. An unrelated/unhealthy service retains the existing port-conflict behavior.

This closes the exact observed dogfood fault: switching or updating code can no longer be masked merely because an older AI Infra Quant process still returns healthy on `/health`.

The implementation does not attempt to fingerprint uncommitted working-tree changes. That is not a blocker under the approved clean-checkout/task-governance model; source-revision equality is the Remediation Contract boundary.

**R1 result: PASS.**

---

## 4. R2 — DeepSeek web-search action compatibility

Implementation reviewed:

- `src/ai_infra_quant/integrations/openai_reasoning/gateway.py`
- `tests/unit/test_paqs_e_remediation_01.py`

For DeepSeek only, `normalize_research()` now accepts completed native `web_search_call` actions of:

- `search`
- `open_page`
- `find_in_page`

This matches current official DeepSeek Responses API documentation reviewed independently on 2026-09-08.

The compatibility change remains bounded:

- DeepSeek accepts at most 10 `web_search_call` action records, matching the documented server-side auto-continuation cap;
- at least one real `search` action and 1-4 reported search queries are still mandatory;
- `open_page` / `find_in_page` do not contribute query count or source authority;
- URLs/source-like fields attached to page/find actions are ignored for evidence trust;
- included evidence must still resolve to URLs grounded in native search sources and/or native URL citations;
- generated summary JSON cannot introduce an unverified URL;
- raw source/citation records remain bounded before deduplication;
- existing source/item/character limits, publication-time filtering, unknown-time limitation, no-retry behavior and final reasoning `tools=[]` boundary remain intact;
- other providers remain on their previously reviewed behavior and are not automatically broadened.

The deterministic regression fixtures explicitly test page/find URL smuggling, missing native search, unknown action types, >4 search queries, >10 DeepSeek action records, future sources and frozen-evidence delivery into tool-free reasoning.

A remaining provider-side cost limitation is correctly documented: application acceptance bounds do not prove that DeepSeek internally performed no more than four billed searches inside one server-side operation.

**R2 result: PASS subject to final real DeepSeek web-research smoke.**

---

## 5. R3 — long synchronous Analyze

Implementation reviewed:

- `src/ai_infra_quant/frontend/static/paqs-e.js`
- `tests/browser/test_paqs_e_long_running.py`
- bounded update to `tests/browser/test_paqs_e_workbench.py`

The old `AbortController` 180-second terminal timeout is removed. The 180-second timer is now only a UI notice. It does not abort fetch, release the global `inFlight` guard, retry, resubmit or create another paid call.

The request remains pending until a real terminal HTTP response or an actual network/browser failure. A later successful/provider-failed/validation-failed terminal result can therefore be rendered even if the provider operation lasts longer than three minutes.

The browser regression uses fake-clock delayed responses and covers terminal `SUCCEEDED`, `PROVIDER_FAILED` and `VALIDATION_FAILED`, confirms only one Analyze POST exists after 241 seconds, confirms the button remains guarded, and confirms the long-wait notice cannot overwrite a later terminal result. The retained unknown-outcome path is now exercised by an actual synthetic connection failure rather than the removed application timeout.

This preserves the synchronous TASK-007B model and no-retry / no-background-worker boundary.

**R3 result: PASS.**

---

## 6. R4 — deterministic Snapshot fact projection

Implementation reviewed:

- `src/ai_infra_quant/application/paqs_e_runtime.py`
- `tests/unit/test_paqs_e_remediation_01.py`

Normal runtime now performs this order:

`strict provider schema/domain parse -> deterministic Snapshot fact projection -> existing validator`

The projector is provider-neutral. It replaces only the approved factual echo fields of `current_price_reference` with values derived directly from the immutable request Snapshot:

- price
- timestamp
- freshness status using the existing availability mapping
- session type using the existing canonical market-state mapping

For an executable entry already marked `eligible=true` by the model, only the same four factual echoes are projected. The projector does not make an entry eligible, does not change policy basis and leaves ineligible entry fields untouched.

The implementation does **not** normalize identity, support/input quality, context, bias, key levels, events, trigger/follow-through, setup, entry advisory, eligibility, invalidation, targets, holder advisory, uncertainty, explanation, reason codes or RR fields.

The deterministic validator remains authoritative. Direct validation of an unprojected bad result still produces the original current-price mismatch errors, while normal runtime receives corrected immutable facts before validation. Market availability/session restrictions can still reject a model-eligible entry after projection. RR arithmetic is not repaired by the projector and can still fail independently.

This is the correct remediation for the observed real Run `038920ac-8bf6-4d2c-97f5-e78f803f0f2f`, which had reached strict DeepSeek provider success and failed only `CURRENT_PRICE_FRESHNESS_MISMATCH`.

**R4 result: PASS.**

---

## 7. Validation evidence assessment

The remediation implementation report claims final validation of:

- 255 focused tests passed;
- 751 passed / 1 optional PostgreSQL skipped / 1 Starlette deprecation warning in the full suite;
- 54 browser tests passed;
- Windows launcher tests passed;
- Ruff check, Ruff format and mypy passed;
- fresh SQLite migration and real Uvicorn/HTTP smoke passed;
- migration head remained `0002_task007b_paqs_e_ledger`;
- protected-file and secret audits passed.

This independent review did not treat those numbers as proof by themselves. The changed implementation and the newly added regression tests were inspected directly from the exact GitHub SHA. The reported validation inventory is consistent with the reviewed test files and no test weakening, migration edit, strategy-semantic edit or new prohibited scope was found in the remediation diff.

The optional PostgreSQL skip is non-blocking for this SQLite local-first product path. The Starlette `BlockingPortal` warning is non-functional.

---

## 8. Remaining mandatory live acceptance gates

Final TASK-007C1 acceptance requires user-executed live product smoke on **exact SHA**:

`6681fc6a934f44d29879c2ef1152891c3bd3a0d5`

The user must first ensure no stale prior backend remains, launch this exact checkout, and verify `/health` reports the exact same `source_revision`.

### Live Smoke A — reasoning only

- Model: `DeepSeek V4 Flash`
- Web research: OFF
- One supported Security
- One explicit Analyze

Required acceptance evidence:

- terminal response is confirmed by the UI even if execution exceeds 180 seconds;
- Analysis Run reaches `SUCCEEDED`;
- exactly one Decision is created;
- Run/Decision audit identity records `model_provider=deepseek` and `model_id=deepseek-v4-flash`;
- the previous `CURRENT_PRICE_FRESHNESS_MISMATCH` dogfood defect does not recur solely because the model echoes a different freshness value.

If a different semantic validator issue occurs, it must be reported as such and not hidden by relaxing the validator.

### Live Smoke B — auditable web research

- Model: `DeepSeek V4 Flash`
- Web research: ON
- One explicit Analyze

Required acceptance evidence:

- research no longer fails merely because the provider uses legal `open_page` / `find_in_page` actions;
- final Run reaches `SUCCEEDED` and creates a Decision;
- persisted canonical request contains non-empty frozen `auxiliary_context[]` entries of category `web_research`;
- included evidence contains safe source URL/provenance and no raw chain-of-thought or credential;
- final reasoning still consumes frozen evidence rather than hidden additional web tools.

Do not send, commit or screenshot the API key. Do not automatically retry a failed paid call.

---

## 9. Current acceptance state

```text
TASK-007C1 original implementation           IMPLEMENTED
Remediation 01 R1-R4 code review             PASS
Exact reviewed remediation SHA               6681fc6a934f44d29879c2ef1152891c3bd3a0d5
Final live DeepSeek reasoning smoke           PENDING
Final live DeepSeek web-research smoke        PENDING
Final independent TASK-007C1 acceptance       PENDING
Authoritative integration                     NOT PERFORMED
```

No further code remediation is requested at this point. Do not merge yet. Do not start another task. If both required live smokes pass on this exact SHA without branch mutation, update this independent review with the live evidence and perform the final SHA gate before integration.