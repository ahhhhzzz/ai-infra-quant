# API Contracts

Status: **AUTHORITATIVE — EOD/no-live API direction**

Decision: `EOD-001` in `docs/ROADMAP.md`

Media type: JSON unless stated otherwise

Base path: `/api/v1`

## 0. Scope and historical boundary

Phase 1 routes remain accepted exactly as implemented. This document plans future EOD research,
paper accounting, daily-bar analytics, and completed real-trade tracking. It does not register a
route or change runtime code.

Earlier future real-order concepts are superseded. No API request may place, cancel, replace,
modify, approve, retry, recover, or otherwise transmit a real broker operation.

## 1. Contract rules

- `/api/v1` is the compatibility boundary.
- Schemas are independent of ORM and provider SDK types.
- UUIDs are lowercase canonical strings.
- Instants are UTC `Z` strings; completed sessions are `YYYY-MM-DD` plus timezone/calendar.
- Financial Decimal values serialize as strings; JSON floats are rejected.
- Signed zero normalizes to positive zero.
- Missing numeric facts are `null` plus status/reason, never fake zero.
- Point-in-time responses identify `data_as_of` and source availability.
- Responses never expose credentials, private external account IDs, or raw provider payloads.
- Financial mutations require `Idempotency-Key` where applicable.
- Recommendation acknowledgement/rejection is non-executing metadata.
- Paper, advisory, completed real-trade, and broker-observation schemas are distinct.

## 2. Common models

### 2.1 `DataValue[T]`

```json
{
  "value": "100.00",
  "status": "AVAILABLE",
  "as_of": "2026-08-31T08:00:00Z",
  "source": "internal_ledger",
  "reason": null
}
```

Availability status is `AVAILABLE`, `MISSING`, `UNAVAILABLE`, `NOT_SUPPORTED`, or `INVALID`.
Snapshot/score quality and capability status use their own taxonomies.

### 2.2 `CompletedSessionRef`

```json
{
  "market": "US",
  "session_date": "2026-08-31",
  "market_timezone": "America/New_York",
  "calendar_id": "XNYS@version",
  "data_as_of": "2026-09-01T00:15:00Z",
  "available_at": "2026-09-01T00:10:00Z",
  "source": "approved_eod_source",
  "quality_status": "COMPLETE",
  "stale": false
}
```

### 2.3 `AssumptionSet`

Used by scores, suggestions, and backtests:

```json
{
  "price_observation_id": "uuid",
  "price": "100.000000000000000000",
  "fx_observation_id": "uuid",
  "fx_rate": "7.800000000000000000",
  "lot_size": "1.000000000000000000",
  "minimum_notional": null,
  "fee_policy_id": "policy-id",
  "tax_policy_id": "policy-id",
  "liquidity_status": "AVAILABLE",
  "rounding_rule": "FLOOR_TO_LEGAL_INCREMENT",
  "expires_at": "2026-09-02T00:00:00Z"
}
```

### 2.4 `Problem`

Errors use `application/problem+json` with stable `code`, safe detail, request ID, and field errors.
No stack trace, SQL, secret, or raw external payload is exposed.

## 3. Phase availability

Defining a future contract does not expose its route.

| Route group | First phase | Before registration |
|---|---:|---|
| Health, portfolio/positions/performance reads | 1 | Available from accepted foundation |
| Security create/read and default-watchlist CRUD | 1 | Available |
| Strategy/broker/provider inert descriptors | 1 | Available |
| Paper/accounting mutations and paper reads | 2 | Ordinary 404 |
| Completed EOD data, indicators, scores, targets, suggestions, daily summary | 3 | Ordinary 404 |
| Daily-bar backtest requests/results | 4 | Ordinary 404 |
| Manual completed real trades, file import, BrokerObservation sync, reconciliation | 5 | Ordinary 404 |

No route group exists after Phase 5.

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

### 4.1 Health

`GET /health` checks local process/database/migration readiness and never connects to an external
source.

### 4.2 Portfolio, positions, and performance

`GET /portfolio` returns the opening portfolio with HKD 20,000, 200 units, NAV 100, zero positions,
and separate capability statuses. `GET /positions` is empty. `GET /performance` returns the one
inception point; daily/weekly/monthly return is unavailable while since-inception return and
drawdown are exact zero.

### 4.3 Security and watchlist

`POST /securities` creates only a canonical user-supplied unverified identity. It cannot accept
exchange/calendar, provider mapping, lot/tick rules, verification, or tradability claims.
Watchlist add/remove is idempotent and preserves history.

### 4.4 Descriptor reads

Strategy, broker, and provider descriptors are inert. They report truthful
`NOT_IMPLEMENTED`/`UNAVAILABLE` status and cause no connection.

The accepted Phase 1 contract is historical; this Roadmap refactor neither expands nor removes a
runtime route.

## 5. Phase 2 paper/accounting contracts

All records are internal paper/accounting facts.

### 5.1 Cash flows

```text
POST /api/v1/paper/deposits
POST /api/v1/paper/withdrawals
POST /api/v1/paper/fx
```

Requests include portfolio/account, currency, Decimal amount, effective time, reason, and explicit
FX/fee/tax assumptions as needed. With positions, an incomplete `FLOW_PRE` valuation returns
`PORTFOLIO_VALUATION_UNAVAILABLE` and writes nothing.

### 5.2 PaperOrder and PaperFill

```text
POST /api/v1/paper/orders
GET  /api/v1/paper/orders
POST /api/v1/paper/orders/{paper_order_id}/cancel
POST /api/v1/paper/orders/{paper_order_id}/fills
GET  /api/v1/paper/fills
```

PaperOrder requests are always internal simulations. The response includes
`is_simulated=true`, execution-assumption ID, completed-session reference, and no external
broker-order identifier.

PaperFill requests identify quantity, price, currency, completed session, source, observed/available
times, fee/tax assumptions, and actor. They may update paper accounting only. Paper cancellation
changes only an internal simulated object.

There is no real-time paper exchange, automatic intraday matching, or broker connection in Phase 2.

## 6. Phase 3 EOD research and decision-support contracts

### 6.1 Completed daily data

```text
GET  /api/v1/eod/securities/{security_id}/bars
GET  /api/v1/eod/fx
POST /api/v1/eod/import
```

Only completed daily observations are accepted. Each response includes `CompletedSessionRef`,
provenance, quality, and version/hash. Incomplete daily data cannot be official.

### 6.2 Analysis run

`POST /api/v1/eod/analysis-runs` is a synchronous local analysis request or a report-only scheduled
job target. Input identifies portfolio/securities, completed sessions, strategy definition, and
`data_as_of`. No execution flag or broker destination exists.

### 6.3 Indicators

`GET /api/v1/eod/securities/{security_id}/indicators` returns completed-session indicators,
dataset hash, source row IDs, availability, and quality.

### 6.4 Composite Quant Score

`GET /api/v1/eod/securities/{security_id}/composite-score` returns:

```json
{
  "id": "uuid",
  "strategy_run_id": "uuid",
  "security_id": "uuid",
  "session": {"market": "US", "session_date": "2026-08-31"},
  "data_as_of": "2026-09-01T00:15:00Z",
  "generated_at": "2026-09-01T00:16:00Z",
  "expires_at": "2026-09-02T00:00:00Z",
  "score": "73.500000000000000000",
  "classification": "POSITIVE",
  "coverage_status": "COMPLETE",
  "data_coverage": "1.000000000000000000",
  "components": [],
  "missing_components": [],
  "explanation": "Advisory EOD output",
  "target_weight": "0.150000000000000000",
  "risk_flags": [],
  "suggested_side": "BUY",
  "suggested_base_amount": "1000.000000000000000000",
  "estimated_quantity": "1.000000000000000000",
  "assumptions": {},
  "dataset_hash": "sha256:..."
}
```

Classification vocabulary is advisory. Formulae/weights remain subject to separate Strategy
Specification approval. The output is not a promise and cannot become a real order.

### 6.5 Target Portfolio

`GET /api/v1/portfolios/{portfolio_id}/target` returns target weights/values, optional estimated
quantities, methodology, quality, assumptions, session manifest, generated-at, and expiration.

### 6.6 Rebalance Suggestions

`GET /api/v1/portfolios/{portfolio_id}/rebalance-suggestions` returns Current versus Target
deviations and advisory actions. Each suggestion includes current/target weight, suggested amount,
estimated quantity, expected cash impact, risk/data warnings, `AssumptionSet`, and expiration.

### 6.7 Daily Portfolio Decision Summary

`GET /api/v1/portfolios/{portfolio_id}/daily-decision-summary` returns:

- portfolio value, cash, positions, and current weights;
- target weights and Current versus Target deviations;
- concentration/exposure and aggregate risk;
- positions requiring review;
- Rebalance Suggestions and estimated cash impact;
- price, FX, lot-size, minimum-notional, fee/tax, liquidity, and stale-data warnings;
- per-market completed-session manifest;
- provenance, generated-at, expiration, and quality.

### 6.8 Recommendation decision

```text
POST /api/v1/rebalance-suggestions/{suggestion_id}/acknowledge
POST /api/v1/rebalance-suggestions/{suggestion_id}/reject
```

These routes store the user's review decision and optional note. They cannot create PaperOrder,
ManualRealTradeRecord, BrokerObservation, accounting fact, or external operation.

## 7. Phase 4 daily-bar backtest contracts

```text
POST /api/v1/backtests
GET  /api/v1/backtests/{backtest_id}
GET  /api/v1/backtests/{backtest_id}/report
```

Inputs select completed daily data, strategy/parameter version, EOD execution assumption, costs,
calendar, benchmark, and date range. Reports expose reproducibility hashes, return before/after
costs, drawdown, turnover, exposure, cash, diagnostics, and warnings. Intraday or
market-microstructure modes are rejected.

## 8. Phase 5 completed real-portfolio tracking

### 8.1 ManualRealTradeRecord

```text
POST /api/v1/real-portfolio/trades
GET  /api/v1/real-portfolio/trades
POST /api/v1/real-portfolio/trades/import
```

Create requests record a trade already completed outside the platform:

```json
{
  "portfolio_id": "uuid",
  "account_id": "uuid",
  "security_id": "uuid",
  "side": "BUY",
  "quantity": "10.000000000000000000",
  "price": "100.000000000000000000",
  "currency": "USD",
  "executed_at": "2026-09-01T14:30:00Z",
  "fee_amount": "1.000000000000000000",
  "tax_amount": "0.000000000000000000",
  "source": "MANUAL",
  "source_record_id": null,
  "note": "Already executed in broker official client"
}
```

The server rejects pending/future intent. Recording the fact does not contact a broker.

### 8.2 BrokerObservation

```text
POST /api/v1/broker-observations/sync
GET  /api/v1/broker-observations
GET  /api/v1/broker-observations/status
```

Sync invokes only an approved read-only connector and returns immutable observations of account
metadata, cash, positions, completed orders, completed trades/fills, fees, taxes, or settlements.
Manual/CSV import remains available when no connector exists.

The request has no account-selection-for-execution, write credential, or command field.

### 8.3 Reconciliation

```text
POST /api/v1/reconciliation-runs
GET  /api/v1/reconciliation-runs/{run_id}
POST /api/v1/reconciliation-discrepancies/{id}/resolve
```

Resolution records match, reasoned ignore, or a separately approved accounting adjustment.
It never changes an external system or silently overwrites ledger facts.

## 9. Permanent endpoint exclusions

The following are forbidden, not future placeholders:

- any `/live` or real-order submission route;
- any endpoint mapped to `place_order`, `cancel_order`, or `modify_order`;
- trade-password unlock or broker buying-power reservation;
- execution kill-switch, retry, recovery, or worker control;
- streaming/WebSocket, tick, order-book, minute-bar, or intraday strategy routes;
- recommendation acknowledgement that triggers another operation.

## 10. Error semantics

Representative stable codes:

| HTTP | Codes | Meaning |
|---:|---|---|
| 400 | `MALFORMED_REQUEST` | Invalid protocol |
| 404 | `RESOURCE_NOT_FOUND`, `ROUTE_NOT_AVAILABLE` | Missing resource or unregistered phase route |
| 409 | `IDEMPOTENCY_CONFLICT`, `STALE_VERSION`, `PORTFOLIO_VALUATION_UNAVAILABLE`, `RECONCILIATION_DISCREPANCY` | State/provenance conflict |
| 422 | `INVALID_DECIMAL`, `INVALID_SESSION`, `INCOMPLETE_EOD_DATA`, `SECURITY_NOT_VERIFIED`, `UNSUPPORTED_OPERATION` | Invalid or permanently unsupported |
| 502 | `PROVIDER_ERROR`, `BROKER_OBSERVATION_ERROR` | Read-only source returned invalid/failure |
| 503 | `DATABASE_NOT_READY`, `PROVIDER_UNAVAILABLE`, `STALE_EOD_DATA` | Required local/read-only input unavailable |

Provider-read retry is bounded and read-only. No uncertainty can create a write.

## 11. Local security and headers

- Financial/status responses use `Cache-Control: no-store`.
- CORS defaults to disabled/loopback allowlist.
- State-changing local endpoints validate origin and future auth requirements proportionally.
- Every response carries a request ID.
- Logs redact connector configuration, external account IDs, and private import content.
- A Phase 5 connector must prove least-privilege read-only authority before use.

## 12. Contract tests

Phase-relevant tests must prove:

- Phase 1 OpenAPI remains its accepted allowlist;
- future routes are absent before their approved phase;
- Decimal strings, UTC, explicit missing status, and stable errors;
- EOD imports reject incomplete/intraday granularity;
- cross-market session manifests preserve different completed dates;
- one score per security/session/run and one summary per portfolio/run;
- suggested quantities expose all assumptions and expiration;
- acknowledgement/rejection has no paper, accounting, or external side effect;
- PaperOrder/PaperFill remain simulated;
- ManualRealTradeRecord requires an already completed trade;
- BrokerObservation sync is read-only and reconciliation cannot silently overwrite;
- no route, schema, or connector capability represents a real broker write.
