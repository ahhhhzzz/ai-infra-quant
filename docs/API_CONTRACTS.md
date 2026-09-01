# API Contracts

Status: **AUTHORITATIVE — daily + 1-minute read-only API direction**

Decision: `MTF-001` in `docs/ROADMAP.md`

Media type: JSON unless stated otherwise

Base path: `/api/v1`

## 0. Scope and historical boundary

Phase 1 routes remain accepted exactly as implemented. This document describes future read-only
market-data/dashboard, research, simulated paper, and analytics directions. It registers no route
and changes no runtime code. Phase 2 has not begun.

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

Availability/status values include explicit `AVAILABLE`, `MISSING`, `DELAYED`, `STALE`,
`UNAVAILABLE`, `INVALID`, and `ERROR` semantics. Exact enums require the Phase 2 API Task Contract.

## 3. Phase availability

Defining a future direction does not expose a route.

| Route group | First phase | Before registration |
|---|---:|---|
| Accepted health/portfolio/identity/watchlist/status reads | 1 | Available from accepted foundation |
| Market state, daily/minute bars, dashboard refresh, first approved score/ranking/risk state | 2 | Ordinary 404 |
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

## 5. Phase 2 market data and dashboard direction

Exact route names and schemas require a Phase 2 Task Contract. The following groups describe the
required behavior, not implemented endpoints.

### 5.1 Independent Market Data Provider status

A provider-status response must report configuration/capability, entitlement, US/HK coverage,
source delay, last success, last error, and freshness without exposing secrets. Market-data status
contains no brokerage-account concept.

No concrete provider is selected by this document.

### 5.2 Latest quote and market status

A future latest-market-state response includes Security identity, latest Decimal price, currency,
market status, `latest_quote_at`, retrieval time, provider delay, and explicit availability/error
state. It must not claim the price is the final daily close.

### 5.3 Daily bars

A future daily-bars response includes completed sessions, Decimal OHLCV, adjustment provenance,
market timezone/calendar, source timestamps, and freshness/quality status. Daily data remains
supported for AVGO, VRT, and HK.09698.

### 5.4 Current-session completed 1-minute bars

A future minute-bars response includes only completed 1-minute bars for the requested current
trading day. Each item includes interval start/end, Decimal OHLCV, `is_completed=true`, source
timestamps, and quality status. Unfinished bars are excluded.

Daily and minute responses remain separate and are rendered in separate chart coordinate systems.
Full historical minute replay, ticks, and order-book history are not MVP contracts.

### 5.5 Dashboard refresh response

A coherent dashboard refresh may aggregate:

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

### 5.6 Composite Quant Score

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

- Phase 1 OpenAPI remains its accepted allowlist;
- future routes are absent before approval;
- Decimal strings, UTC, explicit missing states, and stable errors;
- daily and minute series remain separate;
- only completed current-session minute bars are returned;
- latest quote and daily close cannot be conflated;
- polling cadence and provider latency are distinct;
- no overlapping client polling, hidden-page pause, visible-page refresh, manual refresh/countdown;
- score provenance exposes all four required time semantics;
- paper records remain simulated;
- no route or schema represents brokerage-account access or a broker write.
