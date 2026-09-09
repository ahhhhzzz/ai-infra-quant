# API Contracts

Status: current API at `722936984deac652b443eba132c69650653345e1`; Narrative-first default.
Architecture and lifecycle: [ARCHITECTURE](ARCHITECTURE.md).

Decision: `MTF-001` in `docs/ROADMAP.md`

Media type: JSON unless stated otherwise

Base path: `/api/v1`

## 0. Scope and historical boundary

Phase 1 routes remain accepted exactly as implemented. This document describes the implemented
read-only market-data routes, Dashboard client, TASK-006A supported-security/input workflow, and
the retained TASK-006B structure snapshot, current Narrative APIs and Legacy structured reads.
C2 UI cleanup does not delete foundation compatibility routes.

No API may connect to a brokerage account; read/import real-account cash, positions, orders, or
trades; match real-account state; or transmit a broker operation.

## 1. Contract rules

- `/api/v1` remains the compatibility boundary.
- Schemas are independent of ORM and provider SDK types.
- UUIDs are lowercase canonical strings.
- Instants are aware UTC strings (`Z` or `+00:00` as serialized by the route); sessions also carry market-local date/timezone/calendar.
- Financial Decimal values serialize as strings; JSON floats are rejected.
- Missing numeric facts are `null` plus explicit status/reason, never fabricated zero.
- Responses distinguish source event time, retrieval time, polling cadence, and source latency.
- Responses never expose credentials, private account IDs, or raw provider payloads.
- Daily and 1-minute bars are distinct collections and chart timeframes.
- An unfinished minute bar is never returned as completed.
- Latest/intraday price is never labelled a final daily close.
- Paper, advisory, and market-data schemas remain distinct.

## 2. Common market-time model

Market responses distinguish quote time, latest completed minute, latest completed daily session,
retrieval time, polling cadence and provider delay; consult each route's schema rather than assuming
one aggregate payload. `polling_interval_seconds` and `provider_delay_seconds` are not interchangeable.
Scores/rankings remain deferred and no current `score_calculated_at` endpoint is implied.

## 3. Phase availability

Defining a future direction does not expose a route.

| Route group | First phase | Before registration |
|---|---:|---|
| Accepted health/portfolio/identity/watchlist/status reads | 1 | Available from accepted foundation |
| TASK-004 market state and daily/minute bars | 2 | Available from TASK-004 |
| TASK-006A supported-security add and PAQS input diagnostics | 2 | Available from TASK-006A |
| TASK-006B current PAQS structure snapshot | 2 | Available from TASK-006B |
| Current Narrative Analyze/history and model/credential configuration | 2 | Registered by C1; see below |
| Legacy structured reads / old POST | 2 | Reads retained; POST normally 410, hidden from OpenAPI |
| Aggregate dashboard refresh and first approved score/ranking/risk state | 2 | Ordinary 404 |
| Expanded research and simulated paper tracking | 3 | Ordinary 404 |
| Backtest and analytics | 4 | Ordinary 404 |

No route group exists after Phase 4.

## 4. Accepted Phase 1 contracts

The accepted runtime allowlist remains:

```text
GET    /health
GET    /api/v1/portfolio
GET    /api/v1/positions
GET    /api/v1/performance
GET    /api/v1/watchlist
POST   /api/v1/watchlist
DELETE /api/v1/watchlist/{security_id}
POST   /api/v1/securities
GET    /api/v1/securities/{security_id}
GET    /api/v1/strategies
GET    /api/v1/brokers
GET    /api/v1/brokers/{broker}/status
GET    /api/v1/market-data/providers
GET    /api/v1/fundamental-data/providers
GET    /api/v1/event-data/providers
```

The health response includes `source_revision`: exactly 40 lowercase hexadecimal characters
captured once when the application is created from `AI_INFRA_SOURCE_REVISION`, or `unknown` when
manual startup has no valid launcher identity. It exposes no paths or environment values. The
Windows launcher resolves the checkout HEAD and passes this dedicated variable to its new process;
only an exact valid match permits reuse. Health never dynamically rereads Git after startup.

These routes retain their reviewed Phase 1 behavior. Inert historical descriptors do not authorize
a future brokerage-account connection. This documentation task neither expands nor removes the
allowlist.

## 5. Phase 2 market data backend and dashboard direction

TASK-004 registers exactly these application-facing market-data routes:

```text
GET /api/v1/market-data/securities/{security_id}/state
GET /api/v1/market-data/securities/{security_id}/daily-bars
GET /api/v1/market-data/securities/{security_id}/minute-bars
```

They resolve the stored canonical Security UUID dynamically for enabled US/HK equities whose
currency matches the market contract. `US.AVGO`, `US.VRT`, and `HK.09698` remain initial data but
are not a whitelist. A missing Security returns `404 SECURITY_NOT_FOUND`; an unsupported type or
disabled Security returns `422 MARKET_DATA_SECURITY_NOT_SUPPORTED`; incompatible stored metadata
returns `409 SECURITY_METADATA_CONFLICT`. Expected provider failures remain structured HTTP 200
responses. All responses use `Cache-Control: no-store`.

### 5.1 Independent Market Data Provider status

Provider descriptor reads report implemented capability/configuration status without connecting.
Per-security market responses carry actual availability/delay/provenance. A descriptor does not
prove entitlement or connectivity and contains no brokerage-account state.

TASK-003 selected Futu OpenD quote-market-data APIs. TASK-004 makes provider modes `none` and
`futu` available at the application composition boundary; `none` is the safe default.

### 5.2 Latest quote and market status

`GET /market-data/securities/{security_id}/state` returns Security identity, provider, latest
Decimal price, currency, canonical/provider market state, canonical `market_timezone`,
`latest_quote_at`, `retrieved_at`, truthful optional `provider_delay_seconds`, independent
`quote_status` and `market_status`, and a safe optional reason. `latest_price` is never labelled or
represented as the final daily close. Daily and minute responses expose the same canonical IANA
`market_timezone` for display without a fixed UTC offset.

### 5.3 Daily bars

`GET /market-data/securities/{security_id}/daily-bars` accepts `limit` from 1 through 1500, default
120. The Dashboard full load requests 1300 completed sessions, an approximation of five trading
years. It returns provider/status/retrieval metadata, `latest_completed_daily_session`, and completed
bars with market-local `session_date`, Decimal-string OHLCV, UTC `provider_time`, and
`is_completed=true`. A current market-local session is included only when provider market state
authoritatively identifies the regular session as closed; its UTC calendar date alone is never
completion evidence.

### 5.4 Recent completed 1-minute bars

`GET /market-data/securities/{security_id}/minute-bars` accepts `lookback_days` from 1 through 31,
default 30, and returns completed provider bars in that rolling market-local calendar window. It
includes provider/status, the compatibility `session_date` (the retrieval market-local date),
`lookback_calendar_days`, UTC `window_start`/`window_end`, `retrieved_at`,
`latest_completed_minute_bar_at`, and bars with UTC interval start/end, Decimal-string OHLCV, and
`is_completed=true`. Unfinished bars are excluded. US history uses Futu `Session.ALL`; HK history
uses normal HK provider sessions. Historical K-line pages are bounded, combined chronologically,
and deduplicated without returning partial history as AVAILABLE after a later-page error.

Daily and minute responses remain separate and are rendered in separate chart coordinate systems.
Unbounded historical minute replay, ticks, and order-book history are not MVP contracts.

### 5.5 Dashboard refresh behavior

TASK-005B keeps the same three direct routes. Initial load and Security switch request 1300 Daily
bars and 30 calendar days of minute bars. Ordinary manual, automatic, and visibility-restored
refreshes request only five Daily bars and two minute-history days, merge by `session_date` and
`interval_start`, and prune the caches to their approved bounds. Refresh does not reset manual
chart pan/zoom. The timeframes remain separate and use `market_timezone` for IANA market-local
labels. No aggregate dashboard endpoint is registered.

A future coherent aggregate dashboard response may include:

- page market state;
- latest price and market status;
- daily chart status/data;
- incremental completed minute bars;
- Composite Quant Score and component timestamps;
- tracked-security ranking;
- reference/risk state;
- explicit missing/delayed/stale/error status.

The client requests it approximately every 60 seconds while visible, never overlaps requests,
pauses while hidden, refreshes immediately when visible again, and supports manual
`刷新最新行情`. The UI displays the refresh countdown. Closing the page requires no background job.

MVP uses ordinary HTTP/REST polling. No WebSocket contract is required.

### 5.6 TASK-006A supported-security and PAQS input endpoints

```text
POST /api/v1/watchlist/supported-securities
GET  /api/v1/strategies/paqs/securities/{security_id}/input-status
```

The add request contains only `market` (`US` or `HK`) and `symbol`. US/HK normalization is
canonical; currency/timezone/EQUITY are inferred. The application validates an exact matching
read-only quote before database mutation, then atomically creates/reuses a `USER_SUPPLIED`
Security and adds/reactivates the default Watchlist membership. The response includes
`created_security`, `created_watchlist_item`, the Watchlist item/Security summary, and provider
validation status/provenance. Duplicate success returns 200; a created/reactivated result returns
201.

Stable failures distinguish `INVALID_MARKET`/`INVALID_SYMBOL`,
`MARKET_DATA_PROVIDER_NOT_CONFIGURED`, `MARKET_DATA_PROVIDER_UNAVAILABLE`,
`MARKET_DATA_PROVIDER_ERROR`, `MARKET_DATA_NOT_ENTITLED`, `SYMBOL_VALIDATION_FAILED`,
`SECURITY_METADATA_CONFLICT`, and `SUPPORTED_SECURITY_PERSISTENCE_ERROR`. Validation failure never
mutates Security or Watchlist state.

The input-status route returns current summary metadata only: Security identity, as-of time,
timezone/provider, COMPLETE/PARTIAL/INVALID quality, calendar status/counts, truthful adjustment
basis, `historical_replay_safe`, D1/W1/1m/M30 source/completed/partial counts, latest completed
timestamps, and warnings. It returns no derived OHLCV arrays and no structure, event, setup,
advisory, target, risk/reward, score, or ranking. It has no public historical `as_of` parameter.

### 5.7 TASK-006B structure endpoint

```text
GET /api/v1/strategies/paqs/securities/{security_id}/structure
```

This read-only route builds a current provider-neutral structure snapshot from the TASK-006A input
bundle. It accepts only the Security UUID path parameter: there is no historical `as_of`, config
override, or mutation parameter. The response includes strategy/structure versions, stable
`config_hash`, canonical parameters, Security/provider/as-of/calculation metadata, input quality
and warnings, adjustment metadata, and independent W1/D1/M30 structures.

Each timeframe reports its role, latest legitimate completed source reference, bar count, ATR
readiness/latest ATR, confirmed Micro/Major Pivots with extreme and confirmation references,
Swing labels, Key Levels, Zones and their accepted touches, valid/active Range geometry, Base
Regime, explanations, and warnings. Decimal values serialize as strings. Invalid input suppresses
calculation and returns explicit `UNCERTAIN` structure rather than fabricated numeric values.

The route contains no event, setup, risk/reward, advisory, score, ranking, persistence, account, or
execution behavior.

### 5.8 Current Snapshot

`GET /api/v1/paqs/securities/{security_id}/market-snapshot` returns the current
TASK-006B2 Snapshot with canonical hash, cutoff, completed W1/D1/M30 and truthful source quality.
It is not an arbitrary historical As-Of query. See the actual
[PAQS routes](../src/ai_infra_quant/backend/api/v1/paqs_market_snapshot.py) and Snapshot schemas.

## 6. PAQS-E Narrative API

Source authority: [paqs_e.py](../src/ai_infra_quant/backend/api/v1/paqs_e.py) `analyze_narrative`,
`get_narrative_run`, `get_narrative_result`, `narrative_history`, and
[AnalyzeCreate](../src/ai_infra_quant/backend/schemas/paqs_e.py).

| Method/path under `/api/v1/paqs-e` | Current behavior |
|---|---|
| POST `/narrative-analyses` | Explicit current Analyze; 201 only after successful Run/Result commit |
| GET `/narrative-analyses/{run_id}` | Immutable terminal Run, canonical request/hash, frozen identity and safe outcome |
| GET `/narrative-results/{result_id}` | Exact persisted text/hash, identity, revision and predecessor |
| GET `/securities/{security_id}/narrative-results` | Newest-first successful history, limit 1..100 default 20, optional strategy filter; metadata plus first 160 Unicode characters as preview |

The POST body has exactly four required fields: canonical `security_id`, registered `model_key`,
registered `strategy_id`, strict boolean `web_research`. Unknown fields and caller-supplied provider,
URL, secret, arbitrary model ID, prompt or As-Of override are rejected. Research defaults OFF in
the UI; the API requires an explicit boolean. A fresh Snapshot and optional accepted research form
the canonical request. No prior history is hidden input and no automatic POST retry occurs.

201 includes `status=SUCCEEDED` and the complete Narrative Result: Run/Result IDs, exact
`response_text`/hash, provider/model, Security/Snapshot/As-Of, strategy/prompt artifact identities,
versions, revision/predecessor, research boolean and creation time. No schema-derived PAQS-E result
fields or semantic validator success are implied. Run identity fields are defined in
[NarrativeIdentity](../src/ai_infra_quant/core/domain/paqs_e_narrative.py).

| HTTP / code | Meaning / evidence |
|---|---|
| 404 `SECURITY_NOT_FOUND` | Missing Security before reasoning; no fabricated Run |
| 409 `SECURITY_METADATA_CONFLICT` | Stored identity conflict before reasoning |
| 422 `PAQS_E_NARRATIVE_PRECONDITION_FAILED` | Unsupported Security/package/model/request cannot form a valid request |
| 422 `PAQS_E_RESEARCH_PRECONDITION_FAILED` | Requested research failed; no final Narrative call or Run/Result; typed research failure and optional safe diagnostic |
| 503 `PAQS_E_NARRATIVE_PROVIDER_FAILED` | Complete request recorded as failed Run: `CONFIGURATION_ERROR` or `PROVIDER_UNAVAILABLE` |
| 502 `PAQS_E_NARRATIVE_PROVIDER_FAILED` | Complete request recorded as failed Run: `PROVIDER_REFUSAL`, `PROVIDER_INCOMPLETE`, `INVALID_FINAL_TEXT` |
| 500 `PAQS_E_LEDGER_ERROR` | Evidence cannot commit or verify; no claimed success |

Provider-failure problems include `narrative_run_id`, `analysis_status=PROVIDER_FAILED`,
`failure_kind`; Problem `status` stays numeric HTTP status. Research retains its existing
research failure taxonomy (including `INVALID_STRUCTURED_OUTPUT`), distinct from final Narrative
failure kinds. Invalid request schemas are rejected before dispatch. Missing read IDs return
`NARRATIVE_RUN_NOT_FOUND` / `NARRATIVE_RESULT_NOT_FOUND`; corrupt evidence returns safe ledger error.
No ledger UPDATE/DELETE, failed-run search, background job, cancel or retry endpoint exists.

DeepSeek's optional `research_diagnostic` is allowlisted by
[ResearchDiagnostic](../src/ai_infra_quant/application/paqs_e_research.py): stage/class, registered
route, safe response identity/status, request count, action/search/message and bounded optional
counts, plus parser boundary code. It contains no provider body, query/source text, memo, secret or
reasoning and is not persisted. See [research architecture](ARCHITECTURE.md#5-optional-research-and-provenance).

## 7. Configuration and local credentials

`GET /api/v1/paqs-e/configuration` returns `default_model_key`, flat `models`,
`default_strategy_id`, registered `strategies`. Each model exposes only `model_key`, `display_name`,
`credential_label`, `credential_configured`, `web_research_supported`. No secret or editable endpoint
is returned. GET performs no provider call/application write; credential presence is dynamic,
strategy configuration is restart-scoped. Unavailable configuration returns safe 503.

| Method/path | Body / response |
|---|---|
| GET `/api/v1/paqs-e/credentials/{model_key}` | Status only |
| PUT same path | JSON object with write-only `secret` |
| DELETE same path | Empty JSON object `{}` |

Responses contain only `credential_configured`, `credential_source` (`secure_store`,
`server_environment_read_only`, `missing`), `secure_storage_available`. Registered models sharing
a slot share status. Presence is not a connection/balance/permission test. The password form does
submit the secret; reads never echo it. Windows Credential Manager is the only production store.
Stored credentials take precedence over OpenAI's optional read-only environment fallback;
deleting the slot leaves that fallback intact. Unavailable OS storage has no plaintext fallback.

Host and peer must be loopback; query parameters are rejected. Mutations require literal matching
Origin, JSON content type, absent/same-origin Fetch Metadata and a bounded request body. The secret
is a `SecretStr`, 1–1024 non-whitespace ASCII characters. Invalid model/value yields safe 422;
store failure safe 503. Boundary violations retain 400/403/413 behavior. No database/ledger/log or
browser-storage secret persistence. See [model guide](PAQS_E_MODELS.md).

## 8. Legacy structured compatibility

| Method/path under `/api/v1/paqs-e` | Behavior |
|---|---|
| POST `/analyses` | Normally 410 `PAQS_E_STRUCTURED_ANALYZE_DISABLED`; absent from OpenAPI |
| GET `/analyses/{analysis_run_id}` | Original terminal structured Run and validator evidence |
| GET `/decisions/{decision_id}` | Original validated structured result and immutable identity |
| GET `/securities/{security_id}/decisions` | Original bounded newest-first Decision history, limit 1..100 default 20, optional strategy filter |

The explicit `create_app(legacy_analysis_enabled=True)` switch is for in-process regression
fixtures only, with no user/env/API setting. Legacy success/`VALIDATION_FAILED`/provider-failure
semantics and the validator are retained. Legacy and Narrative revisions do not share counters;
no historical records are rewritten. See [Legacy review](reviews/TASK_007B_INDEPENDENT_REVIEW.md)
for that implementation's original contract, and [DATABASE_SCHEMA](DATABASE_SCHEMA.md) for storage.

## 9. Deferred and forbidden routes

No current market archive/replay/006B1, strict historical As-Of/GoldSet, score/ranking, PAQS-Q
successor, 007D comparison, PaperOrder/PaperFill/performance or backtest endpoint is introduced.
Future scope requires its own approved contract. Broker accounts, real cash/positions/trades,
import/synchronization, order submission/cancellation/modification and autonomous execution are
permanently excluded. Inert foundation descriptors are not broker connectivity.

## 10. Verification references

[API surface tests](../tests/integration/test_api_surface.py),
[Narrative ledger/API tests](../tests/integration/test_paqs_e_narrative_ledger_api.py),
[model/credential API tests](../tests/integration/test_paqs_e_multi_model.py) and
[partial-action API tests](../tests/integration/test_paqs_e_partial_actions_api.py) provide
existing executable specifications. ADC inspects these sources without claiming a new runtime run.
