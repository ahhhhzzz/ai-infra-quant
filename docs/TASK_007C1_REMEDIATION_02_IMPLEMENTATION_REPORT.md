# TASK-007C1 Remediation 02 — implementation report

Implementation submitted for independent review. No acceptance verdict, integration, merge or next task is claimed.

## 1–4. Authoritative identity and ancestry

- Repository: `ahhhhzzz/ai-infra-quant`; GitHub Git-data API is authoritative.
- Authoritative `roadmap/no-live-trading`: `80f089bc2d285cca492c41aaeaf047e177bc2812`.
- Exact R02 base: `6681fc6a934f44d29879c2ef1152891c3bd3a0d5`.
- Contract/start HEAD: `ca1b71f94565dee02f0bd43d280a59f3ec15ac6d`.
- The Contract commit has exactly one parent, the R02 base; its sole added file is the R02 Contract.
- Pre-edit task ref, authoritative ref, Contract parent and merge base were independently checked on GitHub before editing. The clean isolated checkout matched the Contract SHA/tree.
- Final implementation is the single commit containing this version-bound report. Its literal SHA and final GitHub ref verification are included in the submission accompanying this report; `git rev-parse HEAD` identifies it after checkout. Its parent is the Contract SHA above, merge base is the authoritative SHA, and expected/verified final comparison is **6 ahead / 0 behind**.

All three Contracts were read in full. Only R02 narrative supersession was implemented; R01 source handshake, research normalization and long-running guard remain.

## 5. Exact changed files relative to the Contract commit

```text
docs/API_CONTRACTS.md
docs/ARCHITECTURE.md
docs/DATABASE_SCHEMA.md
docs/PAQS_E_MODELS.md
docs/PAQS_E_WORKBENCH.md
docs/REQUIREMENTS_MATRIX.md
docs/TASK_007C1_REMEDIATION_02_IMPLEMENTATION_REPORT.md
src/ai_infra_quant/application/bootstrap.py
src/ai_infra_quant/application/paqs_e_narrative.py
src/ai_infra_quant/backend/api/v1/paqs_e.py
src/ai_infra_quant/backend/dependencies.py
src/ai_infra_quant/backend/main.py
src/ai_infra_quant/core/domain/paqs_e_narrative.py
src/ai_infra_quant/core/ports/paqs_e_narrative.py
src/ai_infra_quant/database/migrations/versions/0003_task007c1_narrative_ledger.py
src/ai_infra_quant/database/models/__init__.py
src/ai_infra_quant/database/models/paqs_e_narrative.py
src/ai_infra_quant/database/repositories/paqs_e_narrative.py
src/ai_infra_quant/frontend/static/app.css
src/ai_infra_quant/frontend/static/paqs-e.js
src/ai_infra_quant/frontend/templates/index.html
src/ai_infra_quant/integrations/openai_reasoning/narrative.py
src/ai_infra_quant/resources/paqs_e/runtime_prompt_narrative_v1.md
tests/architecture/test_task006a_boundaries.py
tests/architecture/test_task006b2_boundaries.py
tests/architecture/test_task006b_boundaries.py
tests/architecture/test_task007a_boundaries.py
tests/architecture/test_task007b_boundaries.py
tests/browser/conftest.py
tests/browser/test_paqs_e_long_running.py
tests/browser/test_paqs_e_multi_model.py
tests/browser/test_paqs_e_narrative.py
tests/browser/test_paqs_e_workbench.py
tests/browser/workbench_support.py
tests/integration/test_api_surface.py
tests/integration/test_paqs_e_analysis_api.py
tests/integration/test_paqs_e_ledger_migrations.py
tests/integration/test_paqs_e_narrative_ledger_api.py
tests/integration/test_postgresql_migrations.py
tests/unit/test_paqs_e_narrative_provider.py
```

## 6–10. Versions, schema, architecture and ordinary-text transport

Request `paqs-e-narrative-request-v1`; output `paqs-e-narrative-markdown-v1`; new prompt
`paqs-e-narrative-prompt-v1`. The prompt is a writing guide for Chinese final analysis, grounded in
the selected strategy hash, frozen Snapshot and explicit research. It distinguishes Context,
Structure, Location, Event, Transition, Setup, Trigger, Follow-through, invalidation, targets,
RR/entry quality, conditional holder advice and uncertainty. It requires neither a JSON result nor
particular headings. Master strategy and legacy prompt content are unchanged.

`NarrativeAnalysisService` resolves the accepted strategy and Snapshot, uses the unchanged model
registry and requested bounded research, builds the immutable request, invokes `reason_text`, then
records its terminal outcome. The core-facing provider and ledger ports introduce no provider SDK
or persistence dependency into the application. The legacy projector and validator are not called.

`NarrativeGateway` dispatches exactly once to the selected fixed endpoint/model. Responses uses
instructions/input, `store=false`, `tools=[]`, `tool_choice=none`, `stream=false`; it sends no
`text.format`. Chat uses ordinary assistant completion with no `response_format`, empty tools and
`tool_choice=none`; existing provider-specific search/thinking-disable flags are retained. Neither final
path sends JSON Schema/JSON Object requirements, hidden history, previous-response, conversation,
background or fallback state. Final text is never JSON-parsed. Research still uses the existing
bounded native-source normalization before the tool-free final stage.

New migration revision **`0003_task007c1_narrative_ledger`**, direct parent
`0002_task007b_paqs_e_ledger`, adds only:

- `paqs_e_narrative_runs`: full canonical request and SHA; Security/Snapshot/As-Of and actual model,
  strategy/prompt/runtime/request/output identities; immutable artifact FKs; research flag; terminal
  status, fixed safe failure, optional response ID, UTC start/completion/creation timestamps.
- `paqs_e_narrative_results`: unique successful Run FK and identical audit bindings, exact final text
  and SHA, narrative revision and direct predecessor, creation time.

The existing immutable runtime-artifact store is reused additively. No legacy Run/Decision or
artifact is rewritten. New indexes support bounded Security/strategy history. Downgrade drops only
new narrative tables/triggers/indexes and retains historical tables and artifact rows.

Protected migration proof (GitHub base bytes compared to implementation):

| Migration | Git blob SHA | SHA-256 |
|---|---|---|
| 0001 | `add8f78b786482f1598824bde9df6df695a87a3f` | `aa46ffadabb227b86124e396b66a5fe6a0839a7439ad10ab4a726e4f6788daf8` |
| 0002 | `ce61b7a8789385cf4df9d0550d196e27fa969e7b` | `36441501046bd5594401c989bbf7424e997bb6b687fdafd71c34c3e663eaefe3` |

## 11–13. Success, failures and immutable revision semantics

Success checks are transport/text integrity only: exact selected provider/model and strategy/prompt
binding, completed envelope, one assistant final-text item, non-empty string, at most 100,000 Unicode
characters, valid UTF-8 and no C0 controls except LF/CR/tab. Whitespace and all final characters are
preserved. JSON-looking text is ordinary text. Refusals, unexpected tools, mismatched exposed model,
missing/multiple final items and credential echoes fail closed. Optional response IDs match
`[A-Za-z0-9_.:-]{1,256}`. Provider reasoning items are discarded, never persisted or displayed.

Failure kinds are `CONFIGURATION_ERROR`, `PROVIDER_UNAVAILABLE`, `PROVIDER_REFUSAL`,
`PROVIDER_INCOMPLETE`, `INVALID_FINAL_TEXT`. Only fixed safe reasons are stored; raw provider
errors, headers, credentials and reasoning traces are not. A formed failed attempt has one
`PROVIDER_FAILED` Run and no Result. Research/precondition failures before a formed request create
no invented Run. Persistence failure is non-success and rolls back the atomic pair/artifacts.

SQLite rejects UPDATE/DELETE of both narrative tables and rejects results whose successful parent,
frozen identities or consecutive same-series predecessor do not match. Application transactions use
SQLite `BEGIN IMMEDIATE` (Security-row serialization on PostgreSQL). Success is returned only after
commit of exactly one Run/Result pair; reads reject inconsistent success cardinality. Revisions are
`security_id + strategy_id` across all models, independent of legacy structured revisions. Failure
does not consume a successful revision. Reads verify request canonical bytes/hash, runtime artifact
bodies/hash, exact result hash, parent and lineage. Concurrent revision tests exercise serialization.

## 14–16. API, UI and legacy evidence

Normal Analyze is only `POST /api/v1/paqs-e/narrative-analyses`, with exactly the four accepted fields.
A committed 201 includes terminal success, Narrative Run/Result IDs, exact text/hash, frozen identity,
revision/predecessor and timestamps. New GETs read a known narrative Run, Result, or bounded Security
history (limit 1..100; default20; optional strategy; 160-character preview). Configuration/unavailable
failures are 503; refusal/incomplete/invalid-text are 502 with safe failed-Run identity. Existing
precondition/ledger error semantics remain explicit.

The old structured POST is absent from normal OpenAPI and returns 410 by default. An explicit
in-process `create_app(..., legacy_analysis_enabled=True)` exists solely for retained backward tests;
there is no environment, configuration, API or UI control exposing that mode. Legacy GETs remain.

The primary result uses `textContent` with `white-space: pre-wrap`, never HTML/Markdown parsing or
structured extraction. Metadata shows actual model, strategy, As-Of, narrative revision and research
state; audit includes Run/Result IDs and hashes. Primary history is narrative, with inert bounded
previews. Selecting it restores exact text plus frozen Snapshot/research evidence. Current refresh
cannot change them. Narrative charts use only deterministic frozen OHLCV and no prose-derived lines.
Legacy structured Decisions remain clearly labeled in a collapsed read-only history section; their
structured details, numeric reference overlays and original frozen request remain accessible.

Existing one-in-flight and navigation/read-generation guards remain. The 180-second notice does not
abort or retry. A typed failure keeps the previous result visibly earlier/historical. Unknown outcome
requires checking history/known Run before an explicit new attempt. The source-SHA handshake, flat
11-model selector, secure credential dialog and exact pre-await research toggle capture remain.

## 17. Bounded older-test supersessions

The following inventory names every edited older test body plus shared fixtures/helpers whose
changes affect their setup. No old test is skipped, xfailed or deleted. Unmodified structured
validator tests and structured ledger/API business assertions remain. New narrative tests separately
cover the normal workflow rather than relabeling legacy structured fixtures as production narratives.

| Older file / test or helper | Superseded assumption and replacement |
|---|---|
| `tests/architecture/test_task006a_boundaries.py::test_migration_set_contains_only_the_approved_foundation_and_decision_ledger` | The closed migration set gains only authorized 0003; the no-market-data-storage boundary remains. |
| `tests/architecture/test_task006b2_boundaries.py::test_snapshot_has_no_separate_market_data_storage_migration` | The closed migration set gains only authorized 0003; Snapshot remains unpersisted by its own module. |
| `tests/architecture/test_task006b_boundaries.py::test_structure_remains_unpersisted_with_only_approved_migrations` | The closed migration set gains only authorized 0003; Structure remains unpersisted. |
| `tests/architecture/test_task007a_boundaries.py::test_task007a_runtime_remains_independent_of_task007b_api_and_persistence` | The closed migration set gains only authorized 0003; legacy runtime API/storage independence assertions remain. |
| `tests/architecture/test_task007b_boundaries.py::test_task007b_adds_only_analysis_evidence_tables` | The model-module allowlist gains paqs_e_narrative.py; the sole explicit-form POST ownership assertion now names /narrative-analyses. Legacy table and forbidden-scope assertions remain. |
| `tests/architecture/test_task007b_boundaries.py::test_frontend_analyze_post_is_owned_only_by_explicit_form` | The model-module allowlist gains paqs_e_narrative.py; the sole explicit-form POST ownership assertion now names /narrative-analyses. Legacy table and forbidden-scope assertions remain. |
| `tests/browser/conftest.py::workbench_server` | Fresh normal Uvicorn startup now requires head 0003, retaining actual Chromium execution and all readiness checks. |
| `tests/browser/test_paqs_e_long_running.py::test_analyze_remains_guarded_after_180_seconds_until_terminal_response` | Held POST targets narrative-analyses; successful Narrative replaces Decision, and PROVIDER_INCOMPLETE replaces new-attempt VALIDATION_FAILED. The >180s notice, duplicate prevention, eventual terminal handling and no retry remain asserted. |
| `tests/browser/test_paqs_e_multi_model.py::test_web_toggle_is_captured_before_await_and_advanced_identity_remains_visible` | Only the held Analyze URL changes to narrative-analyses; exact pre-await research/model capture and immutable audit identity assertions remain. |
| `tests/browser/test_paqs_e_workbench.py::test_explicit_capture_double_enter_guard_and_security_switch` | New Analyze URL and success label become narrative; empty selection uses the neutral analysis-result label. Typed-failure fixture replaces INVALID_STRUCTURED_OUTPUT/VALIDATION_FAILED with INVALID_FINAL_TEXT/PROVIDER_INCOMPLETE, asserting safe Narrative Run lookup. All prior-retention, no-retry, capture, race, viewport and screenshot checks remain. |
| `tests/browser/test_paqs_e_workbench.py::test_history_selection_survives_pending_analyze_and_refresh` | New Analyze URL and success label become narrative; empty selection uses the neutral analysis-result label. Typed-failure fixture replaces INVALID_STRUCTURED_OUTPUT/VALIDATION_FAILED with INVALID_FINAL_TEXT/PROVIDER_INCOMPLETE, asserting safe Narrative Run lookup. All prior-retention, no-retry, capture, race, viewport and screenshot checks remain. |
| `tests/browser/test_paqs_e_workbench.py::test_typed_failures_unknown_no_retry_and_prior_decision_retention` | New Analyze URL and success label become narrative; empty selection uses the neutral analysis-result label. Typed-failure fixture replaces INVALID_STRUCTURED_OUTPUT/VALIDATION_FAILED with INVALID_FINAL_TEXT/PROVIDER_INCOMPLETE, asserting safe Narrative Run lookup. All prior-retention, no-retry, capture, race, viewport and screenshot checks remain. |
| `tests/browser/test_paqs_e_workbench.py::test_empty_watchlist_removal_add_error_and_current_viewport` | New Analyze URL and success label become narrative; empty selection uses the neutral analysis-result label. Typed-failure fixture replaces INVALID_STRUCTURED_OUTPUT/VALIDATION_FAILED with INVALID_FINAL_TEXT/PROVIDER_INCOMPLETE, asserting safe Narrative Run lookup. All prior-retention, no-retry, capture, race, viewport and screenshot checks remain. |
| `tests/browser/test_paqs_e_workbench.py::test_changed_form_does_not_relabel_captured_success` | New Analyze URL and success label become narrative; empty selection uses the neutral analysis-result label. Typed-failure fixture replaces INVALID_STRUCTURED_OUTPUT/VALIDATION_FAILED with INVALID_FINAL_TEXT/PROVIDER_INCOMPLETE, asserting safe Narrative Run lookup. All prior-retention, no-retry, capture, race, viewport and screenshot checks remain. |
| `tests/browser/test_paqs_e_workbench.py::test_visual_acceptance_artifacts` | New Analyze URL and success label become narrative; empty selection uses the neutral analysis-result label. Typed-failure fixture replaces INVALID_STRUCTURED_OUTPUT/VALIDATION_FAILED with INVALID_FINAL_TEXT/PROVIDER_INCOMPLETE, asserting safe Narrative Run lookup. All prior-retention, no-retry, capture, race, viewport and screenshot checks remain. |
| `tests/browser/workbench_support.py::Workbench` | Synthetic normal POST returns a distinct narrative fixture and frozen Narrative Run. Existing structured-history tests explicitly open the collapsed legacy section and choose legacy Run lookup. New narrative fixtures cover primary history separately; no production response fields are fabricated from prose. |
| `tests/integration/test_api_surface.py::test_openapi_has_exact_approved_allowlist` | Exact OpenAPI allowlist replaces old normal POST with the four narrative operations; all other route restrictions remain. |
| `tests/integration/test_paqs_e_analysis_api.py::analysis` | Only the legacy regression fixture explicitly enables the in-process non-default legacy POST. Existing structured business assertions are unchanged; the OpenAPI test expects normal narrative operations and preserved legacy GETs. |
| `tests/integration/test_paqs_e_analysis_api.py::test_openapi_exposes_bounded_read_only_ledger_contract_without_secret_fields` | Only the legacy regression fixture explicitly enables the in-process non-default legacy POST. Existing structured business assertions are unchanged; the OpenAPI test expects normal narrative operations and preserved legacy GETs. |
| `tests/integration/test_paqs_e_ledger_migrations.py::test_fresh_sqlite_head_has_only_task007b_objects` | Fresh/upgrade current head is 0003 and only its two narrative tables extend the exact table set. Old trigger, Decimal and complete Phase 1 schema/data preservation checks remain. |
| `tests/integration/test_paqs_e_ledger_migrations.py::test_existing_0001_upgrade_downgrade_preserves_all_phase_one_objects_and_data` | Fresh/upgrade current head is 0003 and only its two narrative tables extend the exact table set. Old trigger, Decimal and complete Phase 1 schema/data preservation checks remain. |
| `tests/integration/test_postgresql_migrations.py::test_postgresql_16_fresh_upgrade_downgrade_reupgrade_and_invariants` | Conditional PostgreSQL head/table allowlist gains 0003 and its two tables only; no environmental skip condition or other invariant is changed. |

The OpenAPI file's closed `EXPECTED_PATHS` constant changes for its named test. The long-running
parameter set replaces only the superseded semantic-failure terminal case. The original
`fixture_pair` structured fixture and all legacy result/validator fields remain unchanged; new
`narrative_pair` supplies independently authored synthetic final text. The existing Workbench fixture
explicitly opens legacy history for its historical chart/XSS/race assertions. Its mocked normal POST
uses the captured research flag and a separately frozen narrative capsule. New primary-history tests
exercise narrative races, exact inert text, no overlays, research disclosure and failure retention.

## 18. Validation evidence

| Validation | Result |
|---|---|
| Full `python -m pytest -ra --basetemp ../task007c1-test-tmp/r02-full` | **1068 passed, 1 skipped, 1 warning in543.02s**; exit0 |
| Final browser `python -m pytest tests/browser -ra --basetemp ../task007c1-test-tmp/r02-browser-final` | **65 passed, 1 warning in101.52s**; exit0; no skips/xfails/deselections |
| Final focused narrative provider/ledger/API/browser plus source/launcher tests | **334 passed, 1 warning in82.10s**; exit0 |
| `python -m ruff check .` | All checks passed |
| `python -m ruff format --check .` |184 files already formatted |
| `python -m mypy src tests` | Success: no issues in180 source files |
| Fresh SQLite Alembic upgrade/current/heads and upgrade-from-0002 regression | Passed; sole head0003; legacy byte/value preservation and new-table-only downgrade passed |
| Actual Uvicorn HTTP + real PowerShell same/stale source handshake | Passed; HTTP200; handshake exits0/2 respectively |

Focused command:

```text
python -m pytest tests/unit/test_paqs_e_narrative_provider.py tests/integration/test_paqs_e_narrative_ledger_api.py tests/browser/test_paqs_e_narrative.py tests/integration/test_runtime_source_revision.py tests/integration/test_windows_launcher.py -ra --basetemp ../task007c1-test-tmp/r02-focused-final
```

All commands used the isolated declared-dependency environment. Browser channel was `chromium`;
`PLAYWRIGHT_BROWSERS_PATH` selected the already-installed isolated Chromium runtime. `PYTHONUTF8=1`
was set for Windows output. Logs and temporary databases remain outside the repository.

The sole full-suite skip is the pre-existing optional PostgreSQL smoke:
`PHASE1_POSTGRESQL_TEST_URL is not configured` (test_postgresql_migrations.py:67).
The sole warning is Starlette's deprecated `anyio.abc.BlockingPortal` alias.
No test failures, errors, xfails or browser skips remain. The final browser rerun includes the
additional captured research-flag response identity check made during the full run; final focused
validation also includes the completed-envelope and secret-persistence cases. No required check is
replaced by a static substitute.

Environment: Windows, Python3.12.14; pytest8.4.1; Playwright1.55.0; Chromium140.0.7339.16;
Ruff0.12.9; mypy1.17.1. Declared dependencies were used; no dependency/configuration changes.
Chromium launched normally. Browser tests execute the owned JavaScript and chart library in real
Chromium against actual Uvicorn/static pages and deterministic intercepted business responses.
No paid model, live market entitlement, real key or user database is needed by those tests.

Fresh SQLite upgrade/current/heads reports exactly 0003. Upgrade-from-0002 regression compares old
schema/triggers and complete stored values before/after; downgrade also preserves them. Actual
Uvicorn `/health`, `/openapi.json`, `/`, `/api/v1/paqs-e/configuration` return200; catalog has11 models
and default DeepSeek V4 Flash. The real PowerShell HTTP handshake exits0 for the matching SHA and2
for a stale SHA. Only the created smoke process is terminated. The final published clean checkout
is also rechecked with the same startup smoke and literal final source SHA in the submission.

Wide dark (1440px) and narrow light (390px) narrative screenshots were inspected locally; narrative
text wraps, markup stays inert, primary/legacy history is distinguishable and controls remain usable.
Browser assertions also cover900px and both narrow themes. These are synthetic evidence, not live
market/model-quality claims; no private screenshot or log is committed.

## 19–22. Audit, live gate, limitations and handoff

The protected audit compares71 pre-existing files: migrations, accepted reviews, all prior task
Contracts, registry, strategy/prompt resources, core/Snapshot and Doctrine, Phase1 plan and master
spec. They remain unchanged. The complete legacy `validate_reasoning_result` function is byte-equivalent;
its SHA-256 is `1f52c6c6094ce9b25fe0a7a22ddfdea0e52d8484eb5032ab4bac5e8b9ff1d271`.
The staged text scan finds no real key/token/private-key, database, log, environment file or private
artifact. Synthetic credential-echo tests verify no secret or provider reasoning trace reaches new
tables, API or logs; retained credential/browser tests prohibit plaintext browser/database storage.
No protected 0001/0002 or accepted evidence changes; no broker/live-trading, PAQS-Q, backtest,
portfolio/PnL, voting, new model, arbitrary endpoint, retry, fallback or background work is added.

**Live Smoke A and B remain user-executed acceptance evidence.** No paid provider call was made.
On the exact final SHA, the user must explicitly run DeepSeek V4 Flash once with research OFF, then
once with research ON on a supported Security. Record only SHA/model/research flag, terminal status,
Narrative Run/Result IDs, response hash and frozen-source presence for B. Do not repeat automatically
after ambiguous failure. No API key or provider reasoning trace belongs in evidence.

Limitations: prose is not semantically validated and can be wrong; it is preserved for comparison
with frozen facts. Real endpoint entitlement, quota and final live output remain unverified until
those user smokes. GLM/Kimi/Hy4 research remains disabled; unknown publication time remains explicitly
limited under existing As-Of policy. Current-adjusted Snapshot data is not strict historical replay.
SQLite immutability/lineage is deterministically tested; optional PostgreSQL smoke is reported as
conditional, not falsely claimed. Known failed Run lookup is supported, not an unbounded failed-run
search or background job monitor. Closing a browser is not server-side cancellation.

Only `task/007c1-paqs-e-multi-model-web-research` is published by a non-force fast-forward. GitHub
final ref, parent and merge-base verification accompany the literal final SHA in the submission.
`roadmap/no-live-trading` stays at the authoritative SHA above. **No merge. Stop for independent review.**
