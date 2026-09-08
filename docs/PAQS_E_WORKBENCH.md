# PAQS-E narrative-first workbench — TASK-007C1 Remediation 03

Status: **implemented / pending independent review**. No merge or next-task approval is implied.

The existing FastAPI application serves the workbench at `/`. No frontend build server or Node
production runtime is required. Use the existing documented migration and Uvicorn/Windows launcher
workflow. All API calls use local, fixed same-origin paths. Existing Phase 1 opening facts remain
under a clearly historical/local disclosure; they are not actual holdings or PAQS-E paper state.

## User workflow

1. Select an existing US/HK canonical Security from the watchlist, or add one through the existing
   provider-validated symbol form. Quote/entitlement failures remain explicit. Removing a Security
   invalidates its market, Decision and evidence display; it does not cancel a submitted server run.
2. Read current Daily or completed 1-minute data. Manual refresh and the existing 60-second timer
   only refresh market data. Daily history remains 1,300 sessions and minute history 30 calendar
   days; incremental requests remain five Daily rows / two minute-history days. Cached data and
   viewport are retained on refresh, including errors with previously cached evidence.
3. Select one of the eleven registered model names, initially **DeepSeek V4 Flash**. Model
   changes preserve the chosen primary strategy and never Analyze. Choose **配置此模型 API Key**
   to save/update the selected service's key in Windows Credential Manager. The password input
   clears after successful save or closing the dialog; it is never read back. Models sharing a
   service share its credential status. Presence does not verify balance, entitlement or connectivity.
   OpenAI alone retains an optional read-only server environment fallback. No manual `.env` edit
   is needed for UI-managed credentials. Missing credentials disable Analyze for that model.
4. **联网研究** defaults OFF, including DeepSeek V4 Flash. Every model change resets it OFF;
   unsupported models also disable the checkbox. Explicitly check it only when wanted, then submit **Analyze**
   explicitly. A synchronous page guard captures exactly `{security_id, model_key, strategy_id,
   web_research}` before any asynchronous step. Repeated Enter/click while pending creates no
   extra request, even after changing selections. Research freezes bounded auxiliary
   evidence after the Snapshot cutoff is established; final reasoning has tools disabled.
   Unsupported requested research fails explicitly. There is no retry, queue, provider fallback,
   hidden prior context or idempotency fiction. See `PAQS_E_MODELS.md` for the catalog and limits.
5. A confirmed 201 `SUCCEEDED` response displays its committed Narrative Result and actual identity,
   then uses GET for successful history and the associated Run. Changing form values cannot relabel
   this result. An explicit history selection made while Analyze or another GET is pending remains
   selected when late responses arrive. List reload and list order never force a detail selection.
6. Select a successful history row to read the exact Narrative Result and its Narrative Run input capsule. History
   shows only the latest 20 successful records under the selected strategy filter. Revisions are
   separate per `(Security, strategy_id)` across models and independent of legacy Decision revisions.
   “View list latest” selects the first currently listed Narrative Result and does not run analysis.

At desktop widths, watchlist, chart/history and analysis/results form three columns. At 900px,
watchlist and explicit controls are placed above full-width chart and results. At 390px, the
watchlist has an explicit expand control and the workbench becomes a readable single column.
Labels, focus outlines, real buttons, collapsible semantic sections and live request announcements
support keyboard use. Theme changes affect both charts and text; only the non-secret theme name
is persisted locally.

## Narrative and legacy evidence reading

New Analyze calls `POST /api/v1/paqs-e/narrative-analyses`. The primary result is the exact
persisted final model text. **格式化** is the default local Markdown presentation; **原文** shows
the exact persisted text with preserved whitespace. Toggling views makes no request and changes
neither the selected Result nor its hash. Headings, lists, emphasis, code, rules, blockquotes and
simple pipe tables use locally created DOM elements with text-only content. Raw HTML, links and
images remain inert; no remote renderer is loaded. Malformed syntax remains readable text.
Tables and code can scroll locally on narrow screens. It is model-generated
expert analysis, **not a machine-validated trading instruction**. No Entry/Setup/RR values,
prices or structured judgments are extracted from prose. No JSON result schema or structured semantic
validator is required for a new narrative success. Snapshot facts remain separately auditable.

The heading and audit show actual model, strategy, As-Of, narrative revision, Run/Result IDs and hashes.
A separate disclosure shows the selected Run's frozen research capsule. DeepSeek research is a
provider-native memo with exposed provenance and an
explicit cutoff-verification limitation; its prose URLs are not verified sources. Research opt-in
is never remembered across reloads or restored from history. Enabling research can add latency and
API cost: it may issue up to two additional research requests before final analysis. A research
failure may show bounded stage/class/request/action counts for review, never the raw provider body.
R05 may also show numeric query, source-record and unknown-action counts. Query text and source
URLs never appear in these failure diagnostics. Successful DeepSeek research evidence separately
records total exposed query count and whether the bounded captured query prefix is complete.
It retains the prior Narrative and does not retry. The primary history lists
Narrative Results with a bounded preview. The collapsed **Legacy 结构化 Decision 历史（只读）** section
retains old structured Decisions and their original structured details and frozen evidence. They are
clearly labeled legacy and are never promoted into the narrative revision series. The known-Run
query explicitly distinguishes Narrative and Legacy Run IDs. Historical structured validator behavior
and original records remain unchanged.

Current market and frozen result evidence are separate modes and separate chart instances.
Frozen W1/HTF, D1/STF and M30/TTF data come only from the selected Run's persisted
`request_payload_json.market_snapshot`. The browser compares Result, Run, request and snapshot
Security, hash/As-Of, model/strategy and version identities before association. Backend canonical
hash validation remains authoritative. Failed/malformed/mismatched Run reads clear the frozen
chart and overlays, retaining an independently loaded Decision with an unavailable-evidence label.
There is no current-data or synthetic fallback.

Daily uses the exact market-local session date. W1/M30 retain interval start/end, display IANA
market time including DST, and do not discard completed W1 evidence because its nominal week end
is later than the snapshot. Volume has its own pane; absent volume is omitted, not replaced with
zero. Evidence disclosure retains exact OHLCV, source coverage, excluded partial/unknown counts,
missing-bucket counts, delays, warnings and current-adjustment provenance. These current snapshots
do not claim strict point-in-time replay safety.

Narrative evidence draws no model-derived price lines. In the legacy structured view only,
numeric lines use executable entry price, invalidation calculation reference, and T1/T2
calculation references. Labels preserve exact Decimal strings; finite JavaScript numbers are used
only at the chart drawing boundary. Free-form Key Level/entry/target zones remain text; no regular
expression extracts prices or constructs zone midpoints. Mode/Decision/Security changes and
evidence failures clear old lines. Current quote refresh cannot mutate frozen data or judgment.

## Failure and uncertainty

The numeric Problem `status` is distinct from `analysis_status`. Narrative failures are configuration
error, provider unavailable, refusal, incomplete answer, or invalid final text. A formed failed attempt
commits one safe failed Narrative Run and no Narrative Result; it never uses a semantic-validator gate.
404/409/422 preconditions and 500 ledger/integrity failures do not invent a Run or Decision.
A previous successful Decision stays visible with its own revision/time and an earlier-result
label. Failures never become a new `NO_TRADE`, `UNCERTAIN`, revision or success row.

After 180 seconds, a long-wait notice says the synchronous analysis is still running and must not
be resubmitted. The request remains pending and the Analyze guard remains held. A later terminal
success/provider failure is rendered normally. Disconnect, a real network
failure, non-JSON/malformed/unconfirmed response or identity anomaly is **unknown outcome**.
The server may have committed after disconnection. No
automatic POST retry occurs. Check successful history or a known Run ID before choosing another
explicit attempt. Browser abort/closing the page is not server cancellation.

Known failure responses provide a Run ID for GET detail, and the disclosure accepts a pasted UUID.
This is not a failed-run list/search endpoint. Without a known ID, a successful-history read cannot
prove that no failed run was recorded. No pagination/cursor/exhaustiveness or cancellation API is
invented.

## Reproducible validation

Install the repository's pinned `.[dev]` extra in a Python 3.12 development environment. Playwright
is dev-only and normal application startup does not import it. Browser tests default to an
installed Chrome channel; set `TASK007C_BROWSER_CHANNEL` to another installed Playwright channel
if required. A missing browser is a failed mandatory gate, not a silently skipped test.

```text
python -m pytest tests/integration/test_paqs_e_configuration.py tests/browser -q
python -m pytest -q
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src tests
```

The browser fixture creates a fresh temporary SQLite DB, runs Alembic upgrade to
`0003_task007c1_narrative_ledger`, launches the actual `ai_infra_quant.backend.main:app` via Uvicorn on
an ephemeral loopback port, unsets `OPENAI_API_KEY` and selects provider `none`. It checks real
health/OpenAPI/configuration/page/static HTTP routes before browser scenarios. Only its own
subprocess is terminated during cleanup. No existing user process or database is touched.
Behavioral scenarios run the real owned JavaScript and existing chart library in Chrome, with
test-only intercepted API payloads. They require no Futu service or paid OpenAI call.

Set `TASK007C_SCREENSHOT_DIR` to a local output directory and run:

```text
python -m pytest tests/browser/test_paqs_e_workbench.py -k visual -q
```

Screenshot JSON sidecars record viewport, theme, scenario and synthetic-fixture status. Committed
visual evidence is under `docs/evidence/TASK_007C/`; actual run results and inspected screenshots
are recorded in the implementation report. The accepted optional PostgreSQL smoke remains
environment-dependent; a skip is not a performed PostgreSQL validation.

## Scope and reuse

See `THIRD_PARTY_WORKBENCH.md`. R20 is design-reference-only; vendor bytes/notices are retained.
TASK-007C1 adds model resolution, secure credentials and a pre-reasoning research stage.
Remediation 02 adds only migration 0003 and a distinct narrative prompt/provider/ledger path.
Migrations 0001/0002, legacy validator, accepted strategy, Snapshot, market-data and no-live-trading
boundaries remain unchanged. The source-revision launcher handshake and secure credentials remain
in force. No paid smoke is automatic; final live acceptance is user-executed on the final SHA.
