# TASK-007C — PAQS-E User Dashboard / R20-Inspired Decision Workbench

Status: **APPROVED TASK CONTRACT — user-authorized TASK-007C implementation only**

Issued: 2026-09-07

Repository: `ahhhhzzz/ai-infra-quant`

Authoritative base branch: `roadmap/no-live-trading`

Exact authoritative base SHA: `0db5dd1eb8d9b8f8a2fe49a4e3de5c2d92ed3638`

Dedicated implementation branch: `task/007c-paqs-e-user-dashboard`

Final repository Contract path: `prompts/tasks/TASK-007C_PAQS_E_USER_DASHBOARD.md`

Parent workstream: `TASK-007 — PAQS-E Expert Reasoning Workstream` (umbrella only)

Required predecessor: TASK-007B implementation passed independent review and was integrated into the authoritative base. The reviewed implementation was `7785cdeeacb14f0762f6104ed99f01b5e76d1dd3`, whose parent was the approved TASK-007B Contract commit `2a51b037c07d1c9c992fa88929daf0391112e2fb`. These are evidence identifiers, not substitutes for acceptance or the exact authoritative base above.

R20 reference: `555cute/r20-quantum-trader` at `3840ef1af57c929c081fbe45087225cca1b508f1`.

The authoritative branch was verified at `0db5dd1eb8d9b8f8a2fe49a4e3de5c2d92ed3638` after non-forced fast-forward integration. This documentation-only commit is a direct child of reviewed TASK-007B implementation `7785cdeeacb14f0762f6104ed99f01b5e76d1dd3` and contains `docs/reviews/TASK_007B_INDEPENDENT_REVIEW.md` (PASS) plus the R20 adoption record. The TASK-007B implementation branch was preserved. Verify this lineage at startup; a new independent review of unchanged 007B is not a prerequisite. The launch prompt supplies this Contract commit SHA, whose direct parent must be the exact base above.

## 1. Purpose and adopted authority

Deliver a usable local PAQS-E decision workbench: select a supported US/HK Security, inspect truthful current market data, explicitly enter a model identifier and select a registered strategy, request one analysis, read the validated structured Decision, and inspect earlier immutable revisions and their frozen factual evidence.

Use R20 as a product-design and reviewed presentation-code reference. Preserve the existing HTML/JavaScript/CSS frontend, FastAPI serving path, and locally vendored TradingView Lightweight Charts. This is an additive Phase 2 user experience task, not a whole-repository replacement or a trading-execution task.

Authority, in order relevant to this task:

1. Current explicit user instruction, then `AGENTS.md`, then `docs/ROADMAP.md`, then `docs/MASTER_SPEC.md`, preserving their established precedence.
2. This bounded TASK-007C Contract.
3. Accepted TASK-006B2 snapshot, TASK-007A runtime/output, and TASK-007B API/ledger contracts and their integrated implementation.
4. The approved R20-adoption product-planning record on the authoritative base. It provides design direction; future work packages in that record are not implementation authority here.
5. R20 source solely as a reference for this Contract's authorized presentation scope.

Read the full Roadmap, Master Spec, Architecture, Strategy Spec, Requirements Matrix, current phase plan, engineering guide, accepted TASK-007A/007B contracts and relevant code before editing. Do not reinterpret historical workflow mentions of a future trading adapter/live mode as authorization; the current permanent no-broker boundary governs.

## 2. User-visible deliverable

Build one coherent responsive terminal page served through the existing `/` route:

- top: product identity, selected Security/market/currency, market-data health, manual market refresh and existing refresh countdown;
- left: existing provider-validated US/HK watchlist selection/add/remove flows;
- center: current Daily/1-minute market charts plus an explicitly separate frozen Decision-evidence view for W1/D1/M30;
- right: explicit model/strategy controls, Analyze state, and readable structured analysis;
- accessible history/detail area: successful Decision revisions, selected Decision details, and known Analysis Run status/evidence.

Provide explicit dark/light theme switching with readable chart and text colors in both themes. Persisting a non-sensitive theme preference locally is allowed. Theme changes never request analysis.

At a wide desktop viewport the watchlist, chart/evidence area and analysis area must be visible as three useful columns. At narrower widths collapse/reflow the panels with clear tabs or sections; do not squeeze three unreadable columns or hide essential analysis controls. Preserve keyboard access, visible focus, labels, loading/error announcements and readable contrast. The first viewport should communicate the selected instrument, chart mode, data time, Analyze action and analysis state.

Use concise Chinese user-facing explanations while retaining canonical identifiers/enums in an optional audit view. No fabricated profitability, win-rate, account balance, position, leverage or execution claim is permitted. Holder advice means conditional advice for someone who holds the asset; the application does not know the user's actual holdings.

## 3. In-scope implementation and non-goals

Authorized:

- revise frontend layout/styles and bounded frontend module organization;
- consume accepted watchlist/market-data and TASK-007B Analyze/read APIs;
- add the narrow read-only configuration endpoint defined in section 5;
- add presentation adapters for the accepted structured result and frozen snapshot;
- add deterministic API/browser/architecture tests and reproducible visual evidence;
- update only documentation necessary to describe TASK-007C as implemented and awaiting independent review;
- retain third-party notices for any copied presentation source.

Not authorized:

- changing PAQS-E doctrine, registered strategy content, runtime prompt, schemas, validator/strategy thresholds or TASK-007A reasoning behavior;
- changing TASK-007B Analyze input, revision keys, transaction behavior, payload hashes, persistence/repository behavior, ledger entities or immutable constraints;
- any database migration, schema addition, market-data store, backfill or historical replay engine;
- Vue/Vite/React migration, switching to klinecharts, replacing the chart dependency, or adding a production Node build/runtime requirement;
- provider management, arbitrary base URL, credential entry/storage, model discovery calls, multi-provider adapters or multi-model voting;
- strategy/Prompt editor, registry editor, Python plugins, dynamic execution, shell commands sourced from UI/model fields;
- background/automatic analysis, batch scanning, analysis scheduler, automatic Analyze retries, hidden memory, news/web/search tools or auxiliary context;
- paper portfolio, PaperFill, NAV/P&L/position sizing, real trade entry/import or broker account observation;
- real orders, cancel/modify/unlock, execution workers or autonomous/unattended trading;
- authentication/multi-tenancy, public hosting/deployment, new distributed infrastructure;
- export/import, notifications or backup-management products beyond existing behavior; these remain future work.

Closing/hiding a page starts no analysis. A server request already explicitly submitted may finish and persist after browser disconnection; the UI must not claim browser cancellation stopped it.

## 4. Accepted TASK-007B API contract — consume unchanged

Verify these paths and schemas against the exact integrated base before implementation. The inspected TASK-007B implementation provides:

| Operation | Exact path | Semantics used by 007C |
|---|---|---|
| Explicit Analyze | `POST /api/v1/paqs-e/analyses` | Exactly `security_id`, `model_id`, `strategy_id`; each POST is a new attempt |
| Run detail | `GET /api/v1/paqs-e/analyses/{analysis_run_id}` | Safe terminal status, identity, exact request JSON/hash, typed failure/validation issues |
| Decision detail | `GET /api/v1/paqs-e/decisions/{decision_id}` | Full validated structured result and immutable revision/identity/hash metadata |
| Security history | `GET /api/v1/paqs-e/securities/{security_id}/decisions` | `{items: [...]}`, newest first; optional `strategy_id`; `limit` default 20, allowed 1–100 |

Important actual response details:

- POST success is `201`, with `status=SUCCEEDED`, `analysis_run_id`, `decision_id`, `revision_no`, `supersedes_decision_id`, root `strategy_id`, model/snapshot/runtime metadata and `result`.
- The nested `result.identity` uses `primary_strategy_id` and `primary_strategy_content_sha256`; do not confuse those names with the root ledger fields.
- Run detail uses `analysis_run_id`, `status`, `request_payload_json`, `request_payload_sha256`, `failure_kind`, `failure_reason`, `validation_issues`, timestamps and identity fields.
- Failure Problem documents use numeric root HTTP `status`; analysis state is `analysis_status` and `analysis_run.status`. Never compare the root numeric Problem `status` to `PROVIDER_FAILED`.
- Failures with a complete persisted request have a known `analysis_run_id`; precondition failures have no fabricated run ID.
- History contains only successful Decisions. There is no failed-run collection endpoint, arbitrary run-search endpoint, history pagination cursor, or server cancellation endpoint.

Required failure rendering:

| Actual response | UI outcome |
|---|---|
| `201`, `SUCCEEDED` | Display the committed Decision and its identity; refresh successful history using GET |
| `503`, `PROVIDER_FAILED`, `CONFIGURATION_ERROR` | Configuration missing/unusable; safe server guidance and known run detail, no Decision |
| `503`, `PROVIDER_FAILED`, `PROVIDER_UNAVAILABLE` | Provider unavailable; known failed run, no fabricated judgment |
| `502`, `PROVIDER_FAILED`, `PROVIDER_REFUSAL` | Provider refused; preserve refusal distinction |
| `502`, `PROVIDER_FAILED`, `INVALID_STRUCTURED_OUTPUT` | Invalid structured output; no successful Decision |
| `502`, `VALIDATION_FAILED` | Show validator version and safe issue code/field/message; no successful Decision |
| `404`, `409`, `422` precondition Problem | Show truthful not-found/metadata/support/package/input error; do not invent a run |
| `500`, ledger/integrity Problem | Evidence could not be committed or verified; no fabricated success or new Decision ID |
| Timeout, disconnect, aborted fetch, malformed/non-JSON response or otherwise unconfirmed outcome | Result unknown; no automatic POST retry; advise checking successful history/known run before deciding on another explicit Analyze |

Do not erase an earlier successful Decision when a new attempt fails, but keep it visibly labeled as an earlier result with its own timestamp/revision. A failure must never be presented as `NO_TRADE`, `UNCERTAIN`, a new revision, or a successful zero-confidence answer.

## 5. Narrow configuration endpoint

Add only:

```text
GET /api/v1/paqs-e/configuration
```

Use an explicit bounded response equivalent to:

```json
{
  "model_provider": "openai",
  "api_key_configured": false,
  "default_strategy_id": "paqs-e-master",
  "strategies": [
    {
      "strategy_id": "paqs-e-master",
      "display_name": "server-loaded registered display name",
      "content_sha256": "exact registered content hash"
    }
  ]
}
```

Requirements:

- enumerate only actual server-registered strategies using the accepted registry and existing strategy-loading/validation semantics; do not hard-code fake options in the browser;
- reuse existing package loaders for verification; a narrow read-only application/configuration helper is allowed, without modifying runtime behavior or registry files;
- preserve the registry's actual default strategy identity;
- corrupt/unavailable registry metadata must return a truthful safe non-success Problem; do not synthesize an apparently usable default or silently discard invalid entries;
- expose no strategy Markdown body, runtime prompt, secret value, secret prefix/suffix, environment dump, arbitrary path or provider transport configuration;
- `api_key_configured` is only non-empty effective server credential presence according to the same configured source used by the existing adapter; it is not a key-validity, connectivity, entitlement or model-availability claim;
- GET must make zero OpenAI/OpenD/provider calls and perform no application writes;
- no models list, recommended-model inventory, model validation network call, price estimate, quota estimate or invented provider readiness;
- changing server environment configuration follows the existing restart/configuration semantics; this endpoint is not a hot-reload feature;
- safe errors contain no raw exception or filesystem/environment details.

`model_id` is an explicit user input. Start with no invented usable model value. A non-submittable example placeholder or concise instruction is allowed. Preserve a user's current text while navigating the page, but never infer a model from prior Decisions or silently trim/replace an invalid identifier. Existing server-side validation remains authoritative: non-empty and no whitespace. No silent fallback after a rejected/unavailable model.

When the server key is absent, display how to configure `OPENAI_API_KEY` on the server without an API-key input control. The UI may disable Analyze with this explanation; provider failure views must still correctly handle actual typed responses if configuration changes or a request reaches the API.

## 6. Explicit Analyze lifecycle and concurrency

Maintain separate state for market-data requests, an explicit Analyze request, successful history reads, and selected Decision/run details. Do not reuse the existing market-refresh AbortController or timer as an analysis controller.

An Analyze operation must:

1. validate the user-selected Security and explicit model/registered strategy input locally for usability;
2. capture `security_id`, `model_id`, `strategy_id` in an immutable request-local object;
3. synchronously acquire the page's in-flight Analyze guard before its first asynchronous step;
4. issue exactly one POST with exactly those three fields;
5. render the server-confirmed terminal state under the captured identity;
6. use only GET to load resulting run evidence/history;
7. release the in-flight state in all success/failure paths without triggering another Analyze.

Use one in-flight Analyze per page in this MVP, including while the user selects another Security. This is a UI guard, not server-side deduplication or cross-tab idempotency. Keep the original request's target visibly identified while it is pending. Repeated explicit POSTs remain distinct attempts under TASK-007B.

Required race behavior:

- rapid repeated clicks/form submission produce at most one POST while that page request is in flight;
- changing Security cannot relabel the pending request or let its late response overwrite the newly selected Security;
- changing model/strategy cannot relabel a previously submitted result as produced by the new inputs;
- a stale GET for an old Security/history filter/Decision cannot overwrite the current view;
- a newly returned current Decision cannot force the user out of a historical Decision they explicitly opened while waiting;
- history list order and selection are independent; reloading the list must not silently replace the selected historical detail;
- empty watchlist/removing the selected Security clears associated current display state and invalidates late display writes, without claiming to cancel server analysis;
- response Security/Decision/run/model/strategy/snapshot associations must match the captured request or selected record before rendering; mismatches yield a truthful presentation/evidence error.

No Analyze POST may result from initialization, setting defaults, watchlist load, Security selection, model or strategy change, current chart timeframe change, snapshot timeframe change, theme change, market manual/automatic refresh, history filter/read/detail selection, configuration GET, visibility restoration, timer, or a GET failure.

Network uncertainty is not proof of server rollback. Do not automatically retry, replay queued actions, or recreate a request after page reload. A later explicit user Analyze is a new attempt/revision, never a transparent retry of an unknown attempt. Do not add server idempotency keys or cancellation routes in this task.

## 7. Frozen evidence acquisition and view identity

A committed POST result does not contain the full snapshot bars. For a successful Decision, obtain its associated Run through the accepted run-detail GET and parse:

```text
AnalysisRunRead.request_payload_json
    -> complete TASK-007A request
    -> market_snapshot
```

For an earlier Decision, first GET that Decision, then GET its `analysis_run_id`. Use the exact persisted `market_snapshot.w1_bars`, `d1_bars` and `m30_bars`; never fetch a new current snapshot to impersonate historical evidence.

Before attaching evidence to a Decision, compare Security identity, snapshot hash/As-Of, run ID and model/strategy identity across the selected Decision, Run and parsed request. The backend remains responsible for canonical hash verification; the browser must not recompute a different canonical representation and claim it supersedes backend verification. An optional digest check may hash the exact returned UTF-8 request text only.

If the run is unavailable, corrupt, malformed or mismatched, retain any independently loaded Decision as a Decision with unavailable input evidence, clear/withhold its snapshot chart, and state that evidence could not be verified. Never reuse another Decision's bars, current bars, stale previous-selection bars or synthetic candles. Do not claim valid historical evidence merely because a Decision summary exists.

Every evidence view must visibly identify its Security, Decision revision, snapshot As-Of and whether it is the currently selected historical Decision. The model/strategy used by that Decision remains visible even if form selections have changed.

## 8. Current market and frozen snapshot chart contract

Preserve current Daily and 1-minute charts and their accepted refresh/history behavior. Add an explicitly distinct frozen analysis-evidence chart mode with W1/HTF, D1/STF and M30/TTF choices.

- Current Daily/1m uses the existing read-only market-data API/cache path.
- Frozen W1/D1/M30 uses only the selected Run's evidence capsule.
- Quote refresh may update the separate current-price header; it cannot change frozen candles, levels, invalidation, targets, RR or advisory.
- Show a clear mode label and independent current-data and snapshot timestamps; never call a latest quote a completed daily close.
- Daily evidence uses `session_date` as a market-local date, not a UTC instant that can shift one day in the browser timezone.
- W1/M30 use their accepted `interval_start`/`interval_end` and market timezone semantics. W1 nominal interval-end geometry may extend past As-Of under accepted TASK-006B2 rules; do not independently discard such bars or redefine snapshot eligibility from the interval end.
- Display only supplied completed evidence; preserve evidence quality, excluded/partial counts, missing-data warnings, provider delay and adjustment limitations.
- Do not imply `PROVIDER_QFQ_CURRENT` is strict historical point-in-time corporate-action-safe history.
- Retain a separate volume pane. Null/unavailable values remain absent/unknown, never zero-filled.
- Preserve chart pan/zoom during automatic current-market refresh. When switching a Security/Decision/timeframe, an explicit reasonable viewport reset is allowed.
- Reuse the vendored Lightweight Charts asset and notices without changing its bytes/version.

Overlay rules follow the actual output schema:

| Source | Permitted display |
|---|---|
| `key_levels[].price_or_zone` | Exact text cards/annotations with role/timeframe/rationale/state change; this is free text, not an exact numeric coordinate |
| `price_references.executable_entry_reference.price` | Numeric line only when present, with its eligibility/session/reference meaning retained |
| `invalidation.calculation_reference` | Numeric structural-invalidation reference line when present; condition/timeframe remains in the card |
| `targets.t1_calculation_reference`, `t2_calculation_reference` | Numeric T1/T2 reference lines when present, labeled from the selected Decision |
| Zone/condition prose without a numeric field | Render the original text; do not invent a midpoint, range or exact line |

Do not extract arbitrary numbers from `price_or_zone` or other prose with regex and call them authoritative levels. Do not change the result schema to make charting easier. Do not derive new pivots/setups/triggers or convert structural invalidation into an actual exchange stop order.

Clear old overlays before a Security/Decision change, failed evidence load or current-market mode change. This task need not project frozen structural lines onto continuously refreshed current-market charts.

## 9. Structured analysis presentation

Render actual `PaqsEReasoningResultV1` fields, rather than a generic model paragraph or a newly invented score. Group them for reading:

| User-facing group | Existing result source |
|---|---|
| Thesis and support | `one_line_thesis`, `support.support_status/input_quality/data_quality_reasons` |
| Higher/structure/trigger timeframe context | `context.htf/stf/ttf.states/evidence`, regime summary, trend quality, market bias, avoid-long flag |
| Key levels and location | `key_levels`, `current_location` |
| Event and transition | `price_action.current_event/transition_states`, impulse/correction and channel/exhaustion context |
| Setup and readiness | `setup.family/direction/stage`, qualification, missing confirmation, expiry reason |
| Trigger versus follow-through | Separate `price_action.trigger_status` and `followthrough_status` |
| Entry condition | `entry.advisory/reference_or_zone/chase_risk/wait_condition` and eligible executable reference |
| Structural invalidation | `invalidation` condition, timeframe, reference/zone, reason and strength |
| Targets and RR | T1/T2 zones/references/reasons, nearest-obstacle flag, `risk_reward.rr_status`, exact risk/RR fields and quality |
| Conditional holder advice | `holder.advisory_basis/advisory/prior_decision_id`, with no inferred real holding |
| Uncertainty and alternative view | `uncertainty`, `setup.alternative_interpretation` |
| What to watch next | `next_evidence_needed`, `reason_codes`, `explanation` |

Keep Event, Setup, Trigger, Follow-through and advisory distinguishable. `NO_TRADE`, `WATCH`, `WAIT_RETEST`, `UNCERTAIN`, missing confirmation and unavailable RR are legitimate displayed outcomes, not UI errors to repair. Do not invent a universal numeric score or substitute confidence for calibrated win probability. Never translate a readiness advisory into an executed position.

Advanced audit details may be collapsed but must expose the selected run/Decision IDs, revision/supersedes, Security, snapshot hash/As-Of, actual model/provider, strategy ID/hash, prompt version/hash, runtime/output/request/validator versions, result hash, input request hash and relevant timestamps. Do not fetch or expose full strategy/prompt artifact bodies merely for this UI.

## 10. Successful history and known failed runs

Load bounded successful history for the selected canonical Security UUID. Default to 20 items and offer a bounded limit/strategy filter if useful. Do not invent pagination or claim an exhaustive all-time list when showing the server's limited response.

- Each row identifies time, strategy, actual model, advisory and revision.
- Revision series are `security_id + strategy_id`; model change does not restart them. Do not compare revision numbers across strategies as if they shared one series.
- Selecting a row performs GET only and preserves that record until another explicit selection.
- Provide a clear return-to-latest or return-to-current-market action; neither invokes Analyze.
- No update/delete/overwrite/recompute controls for ledger rows.

For failures, show the latest attempt returned to this page and allow opening its known `analysis_run_id`. A user may enter/paste a known Run UUID into a bounded run-detail lookup. This is a GET detail lookup, not a fabricated failed-run history/list. After reload, do not claim to recover unknown failed runs; the available backend has no failed-run collection API. After an ambiguous disconnect without a run ID, successful history can help the user inspect new Decisions but cannot prove that no failed attempt was recorded.

## 11. Decimal, timestamp and untrusted-text safety

- Preserve backend Decimal strings in result/detail/card text and raw evidence. Do not calculate financial values, RR, target distances, allocations or returns using JavaScript binary numbers.
- Conversion to a finite JavaScript number is allowed only at the chart drawing boundary. Keep the original exact string available for labels/detail; reject unusable chart values without replacing financial text or evidence.
- Do not reserialize canonical audit payloads through Number or recompute backend hashes from a rounded representation.
- Format aware timestamps with explicit market IANA timezone (`America/New_York` or `Asia/Hong_Kong`) and an identifiable timezone label; provide the original UTC timestamp in audit details. Test both US DST offsets and a browser timezone different from the market.
- Distinguish snapshot As-Of, run started/completed, record creation and current quote/bar timestamps.
- Treat every Security name, model/strategy metadata value, model-generated string, provider message and historical value as untrusted text.
- Use DOM text APIs such as `textContent`; do not add `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval`, `Function` or equivalent unsafe interpretation for dynamic content.
- Do not auto-render model Markdown/HTML, activate model-generated links, or embed provider strings as executable attributes/selectors. Use fixed same-origin API paths with validated/encoded identifiers.
- Keep browser runtime requests same-origin to the local application; the browser never contacts OpenAI/Futu/OKX directly. No new external CDN, telemetry, font fetch or remote executable asset.
- No actual API key in DOM, form, JS state/config payload, URL, localStorage/sessionStorage, logs, screenshots or fixtures. Clearly synthetic secret sentinels are allowed only in test cases that assert non-disclosure. No environment dump or raw server trace.

## 12. Preserve existing application behavior

Retain:

- canonical provider-validated US/HK watchlist identity and add/remove behavior;
- initial AVGO/VRT/09698 seed behavior where already present, without restoring a hard-coded instrument universe;
- existing Daily history approximately 1300 sessions and minute history recent 30 market-local days;
- existing US Session.ALL and HK session semantics, volume, status/reason and entitlement behavior;
- incremental Daily/minute refresh limits, dedupe/sort/pruning, no overlapping market requests;
- approximately 60-second visible-page market refresh, countdown, hidden-page pause and visibility-restored refresh;
- empty-watchlist clearing and stale market-request guards;
- existing accepted API paths, health/startup, local administration and Windows one-click launcher.

Existing Phase 1 opening-accounting facts may remain in a secondary collapsed area. They must remain labeled historical/local opening facts and must not become the workbench's apparent current broker assets, live NAV or PAQS-E performance. Do not add new calls to real-account interfaces or fabricate replacement portfolio values.

## 13. Bounded file and dependency scope

Expected primary areas:

- `src/ai_infra_quant/frontend/templates/index.html`;
- `src/ai_infra_quant/frontend/static/app.js`, `app.css`;
- bounded new owned JS/CSS modules under that same frontend tree, if useful;
- `backend/api/v1/paqs_e.py`, `backend/schemas/paqs_e.py` for the GET configuration addition only;
- a narrow read-only `application/paqs_e_configuration_queries.py` or equivalent helper, plus necessary composition wiring;
- focused frontend/configuration/API/architecture/browser tests and clearly test-only fixtures;
- UI engineering/testing documentation, API contracts for configuration, Architecture, Requirements Matrix, Roadmap and launcher/user instructions only as needed;
- third-party attribution/reuse manifest if copied source is used.

Do not edit runtime/domain/reasoning/ledger/migration/market-data-provider modules to obtain a visually convenient response. Use adapters in presentation code. If the actual approved backend contract cannot support a required behavior, report the precise mismatch instead of inventing endpoints or widening scope.

No new production frontend framework/build dependency. If no existing browser test harness is available, a small reproducible dev-only browser harness and its explicitly pinned development dependencies may be added; document how to run it. Keep the user's application launch independent of that test tooling. Do not change production dependency versions as incidental cleanup.

Before editing, list exact planned files. Use an isolated task checkout if an existing work directory is occupied by another task. Never terminate another Codex process, stash/reset unrelated changes or move an active user's branch.

## 14. Exact allowance for obsolete task-stage tests

TASK-007B correctly prohibited a frontend Analyze action during its own scope. The new authorized UI necessarily supersedes only that stage-specific exclusion.

In `tests/architecture/test_task007b_boundaries.py`, the existing `test_frontend_and_market_refresh_have_no_analyze_action_or_hidden_dispatch` scans all HTML/JS/CSS for `paqs-e`/`paqs_e`. This Contract authorizes narrowly replacing its **frontend blanket prohibition** with:

- a preserved backend prohibition on hidden Analyze dispatch from `application/market_data_queries.py`, `application/paqs_market_snapshot_queries.py` and `backend/api/v1/market_data.py`;
- TASK-007C browser behavior tests proving zero Analyze POSTs for initialization, polling, refresh, history and selection changes;
- a test that the only production UI Analyze POST source is the explicit Analyze action.

Do not delete the entire B architecture test suite or weaken core/framework/provider/storage, ledger immutability, no-broker, no-scheduler or secret tests. Explain the bounded amendment and its new enforcing tests in the implementation report.

The exact TASK-007B OpenAPI path-set test in `tests/integration/test_paqs_e_analysis_api.py` and any whole-API allowlist may be expanded only for `GET /api/v1/paqs-e/configuration`. Retain every existing Analyze/read method, three-field POST schema, response/failure, limit and secret assertion.

Existing frontend source-string/layout tests may receive minimal equivalent updates when presentation modularization or new UI structure makes an exact text assertion obsolete. Preserve the behavior, not an accidental filename/string. Extend frontend-security scans to every new owned JS module; do not move unsafe code outside the current `app.js` scan. Enumerate each changed older test and its replacement evidence. Do not relax unrelated historical expectations merely to make the suite green.

## 15. Required deterministic tests

Use test-only synthetic fixture data and fake/intercepted provider boundaries; no real paid OpenAI request or live Futu connection is required by the ordinary suite. Test artifacts must be labeled synthetic and must never be installed as production market/analysis fallback data.

API/configuration tests:

- actual registered strategies/default/hash metadata only;
- zero network/provider requests and zero application writes from configuration GET;
- absent/empty/whitespace credential versus present credential reports only a boolean;
- no secret value/prefix/body/transport details in configuration/API/OpenAPI/logs;
- registry invalid/unavailable produces safe truthful failure;
- existing B Analyze/read behavior and exact failure distinctions remain unchanged;
- exact API allowlist includes only the one additional GET.

Browser behavior tests must execute the real owned frontend JavaScript in a browser, not merely search source strings:

1. Initialization, 60-second tick, visibility restoration, manual market refresh, timeframe/theme change, model/strategy change, history list/detail/filter and known-run GET produce zero POSTs to `/api/v1/paqs-e/analyses`.
2. One explicit Analyze sends exactly one three-field POST with the captured canonical Security UUID/model/strategy; rapid double-click and Enter/click combination cannot duplicate it.
3. Response delay plus Security change cannot replace the new Security view; model/strategy changes cannot relabel a result; history/detail out-of-order responses are ignored.
4. Opening an older revision while an Analyze/history request is pending retains the explicit historical selection when newer responses arrive.
5. All typed failure rows from section 4, malformed/non-JSON response and transport uncertainty render correctly with zero automatic Analyze retries.
6. Failure retains any previous successful result with a visible earlier-result label; it creates no fabricated Decision/history row.
7. Success loads the associated Run and draws frozen bars from its request capsule only. Current quote refresh changes neither selected snapshot bars nor Decision lines/cards.
8. Missing/corrupt/mismatched Run evidence clears the frozen chart and shows unavailable evidence instead of fallback bars.
9. Key-level prose containing multiple numbers does not become fabricated numeric chart geometry; only explicit numeric reference fields create overlay lines. Old overlays do not survive a Decision/Security/mode change.
10. Exact Decimal strings round-trip through displayed cards/audit; null RR/price stays unavailable; non-finite chart conversion does not draw fake values.
11. D1 session dates, W1/M30 times, US DST and HK labels remain correct when browser and market timezones differ.
12. Script/HTML payloads in model prose, names, metadata and failure reasons render as inert text; no JavaScript execution, unsafe external request or injected element occurs.
13. Empty watchlist, add/remove/select supported security, entitlement/provider-error states, Daily/1m and incremental-refresh viewport behavior remain functional.
14. History uses success-only list semantics, strategy-specific revision identity, bounded limits and known run detail; it never manufactures failed-run listing/pagination.

Where behavior can be verified by stable UI/accessibility selectors and network interception, prefer that over implementation-coupled text assertions. Do not introduce fixtures that short-circuit production safety conditions merely to force screenshots green.

## 16. Real server and visual acceptance gate

Both are required:

1. **Actual application startup:** run the actual Uvicorn application entrypoint on loopback with a temporary database upgraded through the existing migration head. Check `/health`, `/openapi.json`, `/`, configuration GET and static assets over HTTP. This must exercise normal app/container composition, not only TestClient or a replacement mock web server. Keep provider credentials unset for this smoke and show truthful unconfigured/unavailable behavior.
2. **Visual/browser acceptance:** capture and inspect real browser screenshots of the workbench served by the app at a wide desktop viewport (for example 1440×900) and a narrow viewport (for example 900×900, plus 390×844 if supported). Success/immutable-history scenarios may use clearly labeled test-only network fixtures against the actual page. They are UI evidence, not live-provider validation.

Required visual states across the screenshot set: initial/unconfigured or no-result, a successful structured Decision with frozen evidence, an explicitly selected prior revision, and a typed failure or uncertain transport outcome. At least one wide and one narrow screenshot must contain substantial real rendered UI content, not an empty loading page. Cover both dark and light themes across the screenshot set.

Inspect the screenshots for clipping, panel overlap, unusable chart width, horizontal page overflow, concealed buttons/errors, incorrect Security/revision labels and unreadable card hierarchy; correct issues before delivery. Record viewport, scenario, fixture/live status and screenshot path. Screenshots must contain no credentials or private account data.

If a necessary browser/runtime dependency genuinely cannot run, document the exact attempted command and error and report the remaining acceptance gap. Do not replace visual evidence with a claim of verification or mark the task ready for integration with a mandatory check unperformed.

## 17. Standard validation and regression

Run and report exact repository-standard equivalents of:

```text
pytest focused TASK-007C configuration/UI/browser tests
pytest full suite
ruff check
ruff format --check
mypy
browser behavior/visual harness command
actual Uvicorn startup and HTTP smoke
```

Also verify:

- no new migration; current accepted head remains `0002_task007b_paqs_e_ledger` unless the approved authoritative base explicitly carries a separately accepted revision;
- existing database upgrade/startup path and Windows launcher tests pass;
- prior accepted Analyze/read/API and market-data paths still work;
- chart vendor hash/notices preserved;
- configuration and history reads make zero provider calls; initialization makes zero reasoning-provider calls, while the existing explicit market-data initialization/refresh path may obtain quote-only data;
- no production secret or private data staged in Git.

Reuse existing fixture infrastructure and proportional tests. Do not amend protected history or add unapproved production dependencies to resolve an unrelated environment problem. A missing configured PostgreSQL smoke environment can retain its already-accepted environmental skip; do not falsely describe it as a performed test.

## 18. Source reuse and licensing

R20 is a reference, not runtime authority. No live request to a deployed R20 service is required. If copying substantial source, use the fixed reference commit above and record:

```text
upstream repository
exact commit
original file/path
local target file/path
copied/adapted scope
removed behavior and local API adaptation
applicable license and preserved notices
```

Preserve the full applicable MIT license and `Copyright (c) 2026 R20 Quantum Trader Team` for copied R20 code. Record actual reuse in an owned third-party manifest/notice file; if no source is copied, state design-reference-only accurately. Verify third-party chart/icon/font/media licenses independently; do not assume R20's repository MIT covers every bundled asset.

Do not copy R20's OKX CLI/OAuth/account/order/OCO/execution code, model-output-to-shell path, arbitrary Python plugin loader, public account/log aggregator, unrestricted provider endpoints, secret backup behavior, synthesized-market-data fallback, trading scheduler, or strategy thresholds. All current market and analysis data must come through this project's accepted interfaces.

## 19. Protected files, documentation and completion semantics

Do not change:

- `docs/phases/PHASE_1_PLAN.md`;
- `src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py`;
- `0002_task007b_paqs_e_decision_ledger.py` and all accepted ledger/runtime/schema semantics;
- accepted independent review evidence;
- signed TASK-007A/TASK-007B contracts and remediation contracts;
- `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md`, registered strategy Markdown, runtime prompt, strategy registry or their hash/LF rules;
- unrelated user changes or local `phase1_remediation_commit.txt` if present.

Document the actual UI workflow, exact configuration response, failure/unknown behavior, known failed-run lookup limitation, frozen versus current chart semantics, third-party reuse and test commands. Update Requirements Matrix and Roadmap only to the truthful state **implemented / pending independent review**. No self-issued independent PASS or integrated status.

This task delivers the current-analysis PAQS-E MVP user interface. It does not approve TASK-006B1, TASK-007D, PAQS-Q, Phase 3/4 or the rest of the R20-adoption plan.

## 20. Git preconditions and stop condition

Before modifying files, verify:

```text
current branch = task/007c-paqs-e-user-dashboard
current HEAD = exact issued TASK-007C Contract commit
Contract commit parent = 0db5dd1eb8d9b8f8a2fe49a4e3de5c2d92ed3638
origin/roadmap/no-live-trading = 0db5dd1eb8d9b8f8a2fe49a4e3de5c2d92ed3638 when implementation begins
merge base with authoritative branch = 0db5dd1eb8d9b8f8a2fe49a4e3de5c2d92ed3638
TASK-007B independent acceptance/integration evidence exists in that lineage
```

Use a clean isolated task checkout/worktree if needed. Preserve unrelated changes. Do not amend the issued Contract or move the authoritative branch. Do not start implementation from the old 007B candidate solely because its tests were reported passing.

Use targeted staging; commit and push only `task/007c-paqs-e-user-dashboard`. No merge, force-push, remote/global Git reconfiguration, automatic next-task execution, public deployment or real paid provider smoke is authorized by this Contract. Push authorization here is limited to this task branch's approved implementation and reviewable artifacts.

Stop after the task implementation/report is pushed for independent GitHub review.

## 21. Required final implementation report

Report:

1. Exact authoritative base, Contract SHA, implementation HEAD, parent/merge-base/ahead-behind, task-branch push verification and no-merge confirmation.
2. Every changed file; identify backend configuration-only changes, each amended older test and its replacement behavior evidence.
3. Actual user workflow, wide/narrow layout, current versus frozen chart sources, structured-field presentation and unsupported/unavailable states.
4. Analyze POST origin/count, pending/race handling, unknown-outcome/no-retry behavior, successful history and known failed-run detail behavior.
5. Exact added GET configuration schema; no invented model options/key validation/provider probing; secrecy confirmation.
6. Actual test commands/results, existing regression results, real Uvicorn/HTTP smoke and any environmental skip.
7. Browser screenshot paths with viewport/scenario/fixture labels and visual QA outcome.
8. Third-party code/asset reuse manifest and notices, or truthful design-reference-only statement.
9. Confirmation of no runtime/strategy/ledger/migration change, no hidden/background analysis, no broker/real account/real-order/paper capability and no protected-history changes.
10. Any unresolved issue or unmet mandatory gate. Do not call the work independently approved; stop for review.

**End — TASK-007C**
