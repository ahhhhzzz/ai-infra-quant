# API Contracts

Status: **AUTHORITATIVE — dynamic US/HK market data and PAQS input diagnostics**

Decision: `MTF-001` in `docs/ROADMAP.md`

Media type: JSON unless stated otherwise

Base path: `/api/v1`

## 0. Scope and historical boundary

Phase 1 routes remain accepted exactly as implemented. This document describes the implemented
read-only market-data routes, Dashboard client, TASK-006A supported-security workflow and PAQS
input diagnostics, plus later separately approved directions.

No API may connect to a brokerage account; read/import real-account cash, positions, orders, or
trades; match real-account state; or transmit a broker operation.

## 1. Contract rules

- `/api/v1` remains the compatibility boundary.
- Schemas are independent of ORM and provider SDK types.
- UUIDs are lowercase canonical strings.
- Instants are UTC `Z` strings; sessions also carry market-local date/timezone/calendar.
- Financial Decimal values serialize as strings; JSON floats are rejected.
- Missing numeric facts are `null` plus explicit status/reason, never fabricated zero.
- Responses distinguish source event time, retrieval time, polling cadence, and source latency.
- Responses never expose credentials, private account IDs, or raw provider payloads.
- Daily and 1-minute bars are distinct collections and chart timeframes.
- An unfinished minute bar is never returned as completed.
- Latest/intraday price is never labelled a final daily close.
- Paper, advisory, and market-data schemas remain distinct.

## 2. Common market-time model

Future market/score responses distinguish at minimum:

```json
{
  "latest_quote_at": "2026-09-01T14:35:12Z",
  "latest_completed_minute_bar_at": "2026-09-01T14:35:00Z",
  "latest_completed_daily_session": "2026-08-31",
  "score_calculated_at": "2026-09-01T14:35:15Z",
  "polling_interval_seconds": 60,
  "provider_delay_seconds": 900,
  "data_status": "DELAYED"
}
```

`polling_interval_seconds` is local cadence; `provider_delay_seconds` describes source latency.
They are not interchangeable.

Availability/status values include explicit `AVAILABLE`, `DELAYED`, `STALE`, `MISSING`,
`UNAVAILABLE`, `NOT_ENTITLED`, `PROVIDER_ERROR`, `NOT_SUPPORTED`, and `INVALID` semantics.

## 3. Phase availability

Defining a future direction does not expose a route.

| Route group | First phase | Before registration |
|---|---:|---|
| Accepted health/portfolio/identity/watchlist/status reads | 1 | Available from accepted foundation |
| TASK-004 market state and daily/minute bars | 2 | Available from TASK-004 |
| TASK-006A supported-security add and PAQS input diagnostics | 2 | Available from TASK-006A |
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

A provider-status response must report configuration/capability, entitlement, US/HK coverage,
source delay, last success, last error, and freshness without exposing secrets. Market-data status
contains no brokerage-account concept.

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

### 5.7 Composite Quant Score

The response architecture is:

```json
{
  "security_id": "uuid",
  "daily_base_score": null,
  "intraday_minute_adjustment": null,
  "composite_quant_score": null,
  "latest_completed_daily_session": "2026-08-31",
  "latest_completed_minute_bar_at": "2026-09-01T14:35:00Z",
  "score_calculated_at": "2026-09-01T14:35:15Z",
  "coverage_status": "UNAVAILABLE",
  "missing_components": [],
  "explanation": null,
  "risk_flags": [],
  "dataset_hash": null
}
```

Nulls above demonstrate truthful unavailability and are not an implemented payload. Formulae,
weights, thresholds, bands, normalization, sizing, and classification vocabulary require a
separate strategy Task Contract. No output indicates whether the user traded.

## 6. Phase 3 research and simulated paper direction

Later approved APIs may expose richer factor/risk analytics, signal history, simulated portfolios,
PaperOrder/PaperFill research records, and paper performance. Every paper record is labelled
simulated, has no external account/order identifier, and cannot contact a broker. Paper positions
update only from confirmed PaperFill facts.

## 7. Phase 4 backtest and analytics direction

Future backtest requests/results may select historical daily data, strategy/parameter version,
transaction-cost assumptions, calendar, benchmark, and date range. Results expose reproducibility
hashes, before/after-cost return, drawdown, volatility, turnover, attribution, exposure,
diagnostics, strategy comparison, parameter analysis, and warnings.

Daily-bar backtesting is baseline. Current-session minute display does not make historical minute
replay or tick-level simulation an API requirement.

## 8. Permanent endpoint exclusions

Forbidden endpoint concepts include:

- brokerage-account discovery, cash, positions, orders, trades, imports, synchronization, or
  matching/discrepancy workflows;
- any `/live` or real-order submission route;
- endpoints mapped to `place_order`, `cancel_order`, or `modify_order`;
- trade-password unlock, buying-power reservation, execution retry/recovery/worker/kill-switch;
- autonomous or unattended trading;
- recommendation acknowledgement that triggers another operation.

Read-only minute market data and intraday score recalculation are allowed analysis endpoints when
separately implemented; they are not execution.

## 9. Error semantics

Representative future stable codes may include:

| HTTP | Codes | Meaning |
|---:|---|---|
| 400 | `MALFORMED_REQUEST` | Invalid protocol |
| 404 | `RESOURCE_NOT_FOUND`, `ROUTE_NOT_AVAILABLE` | Missing resource or unregistered phase route |
| 409 | `IDEMPOTENCY_CONFLICT`, `STALE_VERSION` | State/provenance conflict |
| 422 | `INVALID_DECIMAL`, `INVALID_SESSION`, `INCOMPLETE_MINUTE_BAR`, `SECURITY_NOT_VERIFIED`, `UNSUPPORTED_OPERATION` | Invalid or unsupported input |
| 502 | `PROVIDER_ERROR` | Independent market-data source failure/invalid response |
| 503 | `DATABASE_NOT_READY`, `PROVIDER_UNAVAILABLE`, `MARKET_DATA_STALE` | Required local/read-only input unavailable |

Provider-read retry is bounded and read-only. No uncertainty can create an external write.

## 10. Contract-test direction

Phase-relevant tests must prove:

- the OpenAPI allowlist expands only through approved task routes;
- future routes are absent before approval;
- Decimal strings, UTC, explicit missing states, and stable errors;
- daily and minute series remain separate;
- only completed minute bars inside the requested bounded window are returned;
- latest quote and daily close cannot be conflated;
- polling cadence and provider latency are distinct;
- no overlapping client polling, hidden-page pause, visible-page refresh, manual refresh/countdown;
- score provenance exposes all four required time semantics;
- paper records remain simulated;
- no route or schema represents brokerage-account access or a broker write.
