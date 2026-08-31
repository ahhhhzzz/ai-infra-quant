# API Contracts

Status: Phase 0 design freeze candidate

Media types: JSON unless stated otherwise

Base path: `/api/v1`

## 1. Contract rules

- `/api/v1` is the first compatibility boundary. Breaking field/semantic changes require `/api/v2`; additive optional fields may be added to v1.
- Request and response models are versioned Python schemas independent of ORM and vendor SDK models.
- UUIDs are lowercase canonical strings. Timestamps are ISO-8601 UTC strings ending in `Z`; dates are `YYYY-MM-DD`.
- Decimal values are JSON strings matching `^-?(0|[1-9][0-9]*)(\.[0-9]+)?$`. Financial endpoints reject JSON numeric/float values with `INVALID_DECIMAL`. Ratios are fractional (`"0.250000000000"` means 25%); strategy scores are 0-100 strings.
- Signed zero is normalized before comparison, serialization, persistence, and canonical hashing;
  no API decimal string begins with `-` when its numeric value is zero.
- Currency uses uppercase ISO-4217 codes. Enum values are uppercase strings.
- Missing numeric data is `null` plus an explicit status/reason. `0` never means missing.
- Responses never expose credentials, trade passwords, tokens, raw broker payloads, or external account IDs.
- Mutation requests use `Content-Type: application/json`. Financial mutations from Phase 2 onward require `Idempotency-Key`; identical replay returns the first semantic result, while different content returns 409.
- Cursor pagination is stable by `(created_at, id)`. `limit` defaults to 50 and is constrained to 1-200.

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

`status` is one of `AVAILABLE`, `MISSING`, `UNAVAILABLE`, `NOT_SUPPORTED`, or `INVALID`. `value` is non-null only for `AVAILABLE`; `as_of` and `source` may be null when no observation exists.

This is `DataAvailabilityStatus`. Snapshot `quality_status` instead uses
`SnapshotQualityStatus` (`COMPLETE`, `PARTIAL`, `INVALID`), and score coverage uses the separate
`ScoreCoverageStatus` with those same values. Capability fields use only `CapabilityStatus`.

### 2.2 `CapabilityItem`

```json
{
  "name": "MARKET_ORDER",
  "status": "NOT_IMPLEMENTED",
  "reason": "PaperBroker begins in Phase 2"
}
```

Capability status is `SUPPORTED`, `NOT_SUPPORTED`, `NOT_IMPLEMENTED`, `UNAVAILABLE`, or `UNKNOWN`.

### 2.3 `Page[T]`

```json
{
  "items": [],
  "next_cursor": null,
  "has_more": false
}
```

Clients treat cursors as opaque.

### 2.4 `Problem`

Errors use `application/problem+json` and an RFC-7807-compatible model:

```json
{
  "type": "https://local.ai-infra-quant/errors/resource-not-found",
  "title": "Resource not found",
  "status": 404,
  "code": "RESOURCE_NOT_FOUND",
  "detail": "Security was not found.",
  "instance": "/api/v1/securities/00000000-0000-0000-0000-000000000000",
  "request_id": "4d52d4a0-60e1-4ed4-a6f3-2a8a664d2ea0",
  "errors": []
}
```

Validation entries contain `field`, `code`, and a safe `message`. Stack traces, SQL, raw provider responses, and secrets never appear.

## 3. Phase availability

Defining a future contract here does not expose its route.

| Route group | First registered | Phase 1 behavior before registration |
|---|---:|---|
| Health; portfolio/positions/performance reads | 1 | Available, internal/bootstrap data only |
| Canonical user-supplied security creation/read; default watchlist CRUD | 1 | Available; new records remain unverified/non-tradable |
| Strategy definition list | 1 | Available; no strategy run |
| Broker/provider status descriptors | 1 | Available; operational capabilities unavailable/not implemented |
| Indicators, scores, signals, strategy run/recommendations | 3 | Ordinary 404 in Phase 1 |
| Paper deposit/withdraw/FX/orders/cancel/manual simulation fills | 2 | Ordinary 404 in Phase 1 |
| Orders/fills reads | 2 | Ordinary 404 in Phase 1 |
| Backtest requests/results | 4 | Ordinary 404 in Phase 1 |
| Futu read-only account data | 5 | Ordinary 404 or provider descriptor only |
| Live order/approval/kill-switch | 7 | **No route is registered in Phases 1-6** |

In particular, `POST /api/v1/live/orders` and `POST /api/v1/live/kill-switch` do not exist in Phase 1. A disabled handler, UI-only hiding, or handler that accidentally reaches an adapter is not acceptable.

## 4. Phase 1 request/response contracts

### 4.1 `GET /health`

Unversioned process health; it does not probe or connect to a broker.

Response 200:

```json
{
  "status": "OK",
  "app_version": "0.1.0",
  "database": "READY",
  "migration_revision": "0001_phase1_foundation",
  "trading_mode": "PAPER",
  "auto_execution": false
}
```

Readiness is 503 with `DATABASE_NOT_READY` when migrations are missing. External-provider offline status does not make the local process unhealthy.

### 4.2 `GET /api/v1/portfolio`

Returns the configured default portfolio. An optional future `portfolio_id` query parameter is not accepted in Phase 1.

```json
{
  "id": "6c831a02-bb22-4a02-b41c-0aa0f860787f",
  "name": "AI Infra",
  "base_currency": "HKD",
  "inception_date": "2026-08-31",
  "valuation_timezone": "Asia/Hong_Kong",
  "valuation_at": "2026-08-30T16:00:00Z",
  "total_equity": "20000.00000000",
  "cash_value": "20000.00000000",
  "market_value": "0.00000000",
  "cost_basis": "0.00000000",
  "realized_pnl": "0.00000000",
  "unrealized_pnl": "0.000000000000000000",
  "fees": "0.00000000",
  "taxes": "0.00000000",
  "equity_pnl": "0.00000000",
  "fx_pnl": "0.00000000",
  "units_outstanding": "200.000000000000000000",
  "nav": "100.000000000000000000",
  "cash_ratio": "1.000000000000",
  "invested_ratio": "0.000000000000",
  "quality_status": "COMPLETE",
  "missing_data": [],
  "capabilities": {
    "market_data": "UNAVAILABLE",
    "fx_data": "UNAVAILABLE",
    "fundamental_data": "UNAVAILABLE",
    "event_data": "UNAVAILABLE"
  }
}
```

The example IDs are illustrative, not seed constants. With exactly zero positions, unrealized P&L is economically and exactly zero even though market-data capability is unavailable. Capability status is reported separately and does not convert a known zero to missing.

### 4.3 `GET /api/v1/positions`

Query: `cursor`, `limit`.

Response `Page[PositionRead]`. Phase 1 returns an empty page. Future item model:

```json
{
  "id": "uuid",
  "portfolio_id": "uuid",
  "account_id": "uuid",
  "security_id": "uuid",
  "quantity": "10.000000000000000000",
  "settled_quantity": "10.000000000000000000",
  "currency": "USD",
  "average_cost": "100.000000000000000000",
  "cost_basis_local": "1000.00000000",
  "market_price": {"value": null, "status": "UNAVAILABLE", "as_of": null, "source": null, "reason": "Provider unavailable"},
  "market_value_base": {"value": null, "status": "UNAVAILABLE", "as_of": null, "source": null, "reason": "Provider unavailable"},
  "as_of": "2026-08-31T00:00:00Z"
}
```

### 4.4 `GET /api/v1/performance`

Query: `range` one of `1D`, `1W`, `1M`, `3M`, `YTD`, `SINCE_INCEPTION`; optional `frequency` (`DAILY`, `WEEKLY`, `MONTHLY`).

```json
{
  "portfolio_id": "uuid",
  "range": "SINCE_INCEPTION",
  "frequency": "DAILY",
  "summary": {
    "twr": "0.000000000000",
    "daily_return": {"value": null, "status": "UNAVAILABLE", "as_of": null, "source": null, "reason": "At least two valuation points are required"},
    "weekly_return": {"value": null, "status": "UNAVAILABLE", "as_of": null, "source": null, "reason": "Insufficient valuation history"},
    "monthly_return": {"value": null, "status": "UNAVAILABLE", "as_of": null, "source": null, "reason": "Insufficient valuation history"},
    "since_inception_return": "0.000000000000",
    "maximum_drawdown": "0.000000000000",
    "benchmark_return": {"value": null, "status": "UNAVAILABLE", "as_of": null, "source": null, "reason": "No benchmark data source is configured"}
  },
  "points": [
    {"at": "2026-08-30T16:00:00Z", "nav": "100.000000000000000000", "twr_index": "1.000000000000", "quality_status": "COMPLETE"}
  ]
}
```

Phase 1 exposes only the exact inception point. With one point, daily/weekly/monthly returns are unavailable; since-inception return and maximum drawdown are exactly zero. It does not fabricate a second point or a daily return.

### 4.5 `GET /api/v1/watchlist`

Returns the default watchlist and active membership:

```json
{
  "id": "uuid",
  "name": "AI Infra",
  "portfolio_id": "uuid",
  "is_default": true,
  "items": [
    {
      "security": {
        "id": "uuid",
        "market": "US",
        "symbol": "AVGO",
        "display_symbol": "US.AVGO",
        "display_name": "AVGO",
        "exchange": null,
        "currency": "USD",
        "instrument_type": "EQUITY",
        "metadata_status": "UNAVAILABLE"
      },
      "added_at": "2026-08-31T00:00:00Z",
      "display_order": 1
    }
  ]
}
```

Unverified exchange, lot, tick, and name fields remain null/unavailable. Initial display names may equal their symbols rather than claim verified issuer metadata.

### 4.6 `POST /api/v1/watchlist`

Request `WatchlistAddRequestV1`:

```json
{
  "security_id": "uuid"
}
```

- 201 with `{ "created": true, "item": WatchlistItemRead }` when added.
- 200 with `{ "created": false, "item": WatchlistItemRead }` for an identical active membership; this is idempotent.
- 404 `SECURITY_NOT_FOUND` for an unknown ID.
- 409 `SECURITY_DISABLED` when the security is disabled.

This endpoint adds an existing canonical security. A new symbol is first created through `POST /api/v1/securities` and then added by returned `security_id`.

### 4.7 `DELETE /api/v1/watchlist/{security_id}`

Returns 204 whether the active membership existed or was already absent. It tombstones membership and never deletes the security or history. Invalid UUID syntax returns 422.

### 4.8 `GET /api/v1/securities/{security_id}`

Response:

```json
{
  "id": "uuid",
  "market": "HK",
  "symbol": "09698",
  "display_symbol": "HK.09698",
  "exchange": null,
  "currency": "HKD",
  "display_name": "09698",
  "instrument_type": "EQUITY",
  "enabled": true,
  "record_source": "SYSTEM_SEED",
  "verification_status": "SYSTEM_SEED_UNVERIFIED",
  "tradability_status": "UNVERIFIED",
  "trading_rules": {
    "lot_size": null,
    "min_order_quantity": null,
    "quantity_step": null,
    "tick_size": null,
    "min_notional": null,
    "fractional_supported": false,
    "status": "UNAVAILABLE"
  },
  "market_timezone": "Asia/Hong_Kong",
  "trading_calendar": null,
  "provider_mappings": []
}
```

Provider mappings returned here include only non-sensitive symbol mappings.

### 4.9 `POST /api/v1/securities`

Creates a canonical security from user-supplied identity fields; it does not verify tradability or fetch data.

Request `SecurityCreateV1`:

```json
{
  "market": "US",
  "symbol": "EXAMPLE",
  "currency": "USD",
  "instrument_type": "EQUITY",
  "display_name": "Optional user label"
}
```

The server uses a fail-closed market-specific identity canonicalizer. US symbols are trimmed,
uppercased, limited to 32 characters, and accept only ASCII letters, digits, period, and hyphen.
HK symbols must contain one to five trimmed ASCII digits and are left-padded to five (`9698`
becomes `09698`). Markets without a configured canonicalizer return `INVALID_MARKET`. Currency is
trimmed and uppercased; `instrument_type` is one of `EQUITY`, `ETF`, or `UNKNOWN`. `display_name`
is optional, length-limited plain text. Clients cannot submit exchange, calendar, provider
mappings, lot/tick/minimum/fractional rules, verification, metadata, or tradability status.

Response 201 `SecurityReadV1` always includes:

```json
{
  "id": "uuid",
  "market": "US",
  "symbol": "EXAMPLE",
  "display_symbol": "US.EXAMPLE",
  "currency": "USD",
  "display_name": "Optional user label",
  "instrument_type": "EQUITY",
  "enabled": true,
  "record_source": "USER_SUPPLIED",
  "verification_status": "USER_SUPPLIED_UNVERIFIED",
  "tradability_status": "UNVERIFIED",
  "metadata_status": "UNAVAILABLE",
  "market_timezone": null,
  "trading_calendar": null,
  "trading_rules": {"status": "UNAVAILABLE"},
  "provider_mappings": []
}
```

- 409 `SECURITY_ALREADY_EXISTS` returns the existing canonical `security_id` for the normalized `(market,symbol)` and does not create a duplicate.
- 422 `INVALID_MARKET`, `INVALID_SYMBOL`, `INVALID_CURRENCY`, or `INVALID_INSTRUMENT_TYPE` covers validation failures.
- The new security may be added to a watchlist. Strategy runs/recommendations and all order routes fail closed with `SECURITY_NOT_VERIFIED` and the specific missing prerequisites until calendar, FX where required, lot/tick/trading rules, provider mapping, and source provenance are valid.

### 4.10 `GET /api/v1/strategies`

Response `Page[StrategyDefinitionRead]`:

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "AIInfraStrategy",
      "version": "1.0.0",
      "implementation_status": "NOT_IMPLEMENTED",
      "research_status": "RESEARCH_UNVALIDATED",
      "enabled": false,
      "required_data_status": "UNAVAILABLE"
    }
  ],
  "next_cursor": null,
  "has_more": false
}
```

Phase 1 has no run endpoint and cannot produce a score/recommendation.
`implementation_status` is resolved from the build-time strategy registry, `research_status` and
`enabled` are persisted audited configuration, and `required_data_status` is derived at request
time from configured provider capabilities. The implementation status is not persisted.

### 4.11 `GET /api/v1/brokers`

```json
{
  "items": [
    {
      "name": "paper",
      "implementation_status": "NOT_IMPLEMENTED",
      "connection_status": "UNAVAILABLE",
      "environment": "PAPER",
      "capabilities": []
    },
    {
      "name": "futu",
      "implementation_status": "NOT_IMPLEMENTED",
      "connection_status": "UNAVAILABLE",
      "environment": "READ_ONLY",
      "capabilities": []
    }
  ]
}
```

This is registry metadata, not proof that an SDK, OpenD, account, or entitlement exists.

### 4.12 `GET /api/v1/brokers/{broker}/status`

Returns a descriptor without initiating a connection:

```json
{
  "name": "futu",
  "implementation_status": "NOT_IMPLEMENTED",
  "connection_status": "UNAVAILABLE",
  "last_checked_at": null,
  "message": "Futu integration begins in Phase 5",
  "capabilities": []
}
```

Unknown registry key is 404 `BROKER_NOT_FOUND`.

### 4.13 Provider descriptors

Phase 1 registers three independent read routes:

- `GET /api/v1/market-data/providers`
- `GET /api/v1/fundamental-data/providers`
- `GET /api/v1/event-data/providers`

The same descriptor shape is used with independent capability lists. Phase 1 includes `none` as each active provider and reports `UNAVAILABLE`. No provider call occurs, and configuring one registry never selects another.

## 5. Future strategy read contracts (Phase 3)

These schemas are frozen for planning but their routes do not exist in Phase 1.

### 5.1 `GET /api/v1/securities/{security_id}/indicators`

Query requires optional `as_of`; default is latest fully available session. Response pins sources:

```json
{
  "security_id": "uuid",
  "data_as_of": "2026-08-31T20:00:00Z",
  "dataset_hash": "sha256:...",
  "price": {"value": "100.0", "status": "AVAILABLE", "as_of": "...", "source": "approved_provider", "reason": null},
  "ma20": {"value": "98.0", "status": "AVAILABLE", "as_of": "...", "source": "derived", "reason": null},
  "ma50": {"value": "95.0", "status": "AVAILABLE", "as_of": "...", "source": "derived", "reason": null},
  "ma200": {"value": "90.0", "status": "AVAILABLE", "as_of": "...", "source": "derived", "reason": null},
  "atr14": {"value": "3.0", "status": "AVAILABLE", "as_of": "...", "source": "derived", "reason": null},
  "drawdown_60": {"value": "-0.10", "status": "AVAILABLE", "as_of": "...", "source": "derived", "reason": null}
}
```

### 5.2 `GET /api/v1/securities/{security_id}/score`

```json
{
  "strategy_run_id": "uuid",
  "security_id": "uuid",
  "data_as_of": "...",
  "strategy_name": "AIInfraStrategy",
  "strategy_version": "1.0.0",
  "score": "73.500000000000000000",
  "score_lower_bound": "73.500000000000000000",
  "score_upper_bound": "73.500000000000000000",
  "score_status": "COMPLETE",
  "data_coverage": "1.000000000000",
  "components": {
    "m6": {"score": "90.000000000000000000", "coverage": "1.0"},
    "m3": {"score": "70.000000000000000000", "coverage": "1.0"},
    "trend": {"score": "80.000000000000000000", "coverage": "1.0"},
    "drawdown": {"score": "60.000000000000000000", "coverage": "1.0"},
    "valuation": {"score": "50.000000000000000000", "coverage": "1.0"}
  },
  "missing_components": [],
  "action": "ACCUMULATE",
  "confidence": "1.000000000000",
  "confirmation_status": "CONFIRMED",
  "target_weight": "0.150000000000",
  "requires_manual_review": false,
  "reason_codes": ["SCORE_ACCUMULATE", "CONFIRMATION_MA20_RECLAIM"],
  "risk_flags": []
}
```

### 5.3 `GET /api/v1/signals`

Cursor-paged; filters: `security_id`, `strategy_name`, `action`, `from`, `to`. Point-in-time records are immutable.

### 5.4 `POST /api/v1/strategies/run`

This is a synchronous local analysis request in Phase 3, not an order command.

```json
{
  "strategy_definition_id": "uuid",
  "security_ids": ["uuid"],
  "data_as_of": "2026-08-31T20:00:00Z",
  "mode": "ANALYSIS"
}
```

It returns 201 with a completed/invalid run or 503 `PROVIDER_UNAVAILABLE`. `mode=LIVE` and any execution flag are rejected with 422 `UNSUPPORTED_RUN_MODE`.

## 6. Future paper/accounting contracts (Phase 2)

All financial request decimals are strings and require `Idempotency-Key`.

### 6.1 Cash flow

`POST /api/v1/paper/deposit` and `/withdraw`:

```json
{
  "portfolio_id": "uuid",
  "account_id": "uuid",
  "currency": "HKD",
  "amount": "1000.00",
  "effective_at": "2026-09-01T01:00:00Z",
  "reason": "User-directed paper cash flow"
}
```

Response 201 contains cash-flow ID, pre/post units/NAV, applied FX observation if needed, ledger transaction ID, and balances. Withdrawal failures use 409 `INSUFFICIENT_SETTLED_CASH` or `INSUFFICIENT_PORTFOLIO_UNITS`.

When any position exists, request processing must first create/select a complete official `FLOW_PRE` snapshot with a valid point-in-time mark for every position and all required FX rates. If not possible, return 409 `PORTFOLIO_VALUATION_UNAVAILABLE` and create no cash-flow, unit, or ledger rows.

### 6.2 FX

`POST /api/v1/paper/fx`:

```json
{
  "portfolio_id": "uuid",
  "account_id": "uuid",
  "mode": "EXPLICIT_FX",
  "sold_currency": "HKD",
  "sold_amount": "1000.00",
  "bought_currency": "USD",
  "rate_quote": {
    "rate": "0.128000000000000000",
    "source": "MANUAL",
    "observed_at": "2026-09-01T01:00:00Z"
  },
  "spread_rate": "0.000000000000000000",
  "fee_amount": "0.00",
  "fee_currency": "HKD"
}
```

No rate is invented when a provider is unavailable. A manual rate is explicitly labelled and audited.

### 6.3 Paper order

`POST /api/v1/paper/orders` accepts `StandardOrderCreateV1`:

```json
{
  "client_order_id": "user-generated-unique-value",
  "portfolio_id": "uuid",
  "account_id": "uuid",
  "broker_profile_id": "uuid",
  "security_id": "uuid",
  "side": "BUY",
  "order_type": "LIMIT",
  "quantity": "10.000000000000000000",
  "limit_price": "100.000000000000000000",
  "currency": "USD",
  "time_in_force": "DAY",
  "expires_at": null,
  "recommendation_id": null,
  "strategy_run_id": null,
  "auto_fx": false
}
```

Response 201 is a canonical order with state `CREATED`, `RISK_REJECTED`, or `SUBMITTED`. In Phase 2 it cannot become filled from invented or automatic market matching. A submission acknowledgement alone does not alter holdings.

`GET /api/v1/orders` and future `/fills` are cursor-paged. Paper cancellation is `POST /api/v1/paper/orders/{order_id}/cancel` with a reason and required idempotency key. Modification creates a new canonical request/event and never overwrites fill history.

Phase 2 manual simulation fill route: `POST /api/v1/paper/orders/{order_id}/manual-fills`.

```json
{
  "quantity": "10.000000000000000000",
  "price": "100.000000000000000000",
  "currency": "USD",
  "observed_at": "2026-09-01T01:00:00Z",
  "available_at": "2026-09-01T01:00:00Z",
  "source": "User-entered paper simulation observation",
  "actor": "local-user"
}
```

The server records `price_source_type=MANUAL_SIMULATION_PRICE`. It validates order state, remaining quantity, currency, timestamps, and idempotency. It may produce `PARTIALLY_FILLED` or `FILLED` only from this identified observation. Synthetic automatic fill inputs are permitted only in isolated tests. Automatic market/limit matching is absent until Phase 3 has an approved provenance-bearing market-data path.

### 6.4 Canonical order/fill reads (Phase 2+)

`GET /api/v1/orders` returns `Page[OrderReadV1]`:

```json
{
  "id": "uuid",
  "client_order_id": "user-generated-unique-value",
  "portfolio_id": "uuid",
  "account_id": "uuid",
  "broker_name": "paper",
  "security_id": "uuid",
  "side": "BUY",
  "order_type": "LIMIT",
  "quantity": "10.000000000000000000",
  "limit_price": "100.000000000000000000",
  "currency": "USD",
  "time_in_force": "DAY",
  "state": "SUBMITTED",
  "filled_quantity": "0.000000000000000000",
  "average_fill_price": null,
  "created_at": "2026-09-01T01:00:00Z",
  "updated_at": "2026-09-01T01:00:01Z",
  "strategy_run_id": null,
  "recommendation_id": null
}
```

Filters are `portfolio_id`, `account_id`, `security_id`, `state`, `from`, `to`, `cursor`, and `limit`. `GET /api/v1/fills` uses the same filters and returns immutable `FillReadV1` items with fill/order IDs, canonical account/security, side, quantity, price, gross/fee/tax/net Decimal strings, currency, execution/received times, and simulation flag. External broker order/fill/account identifiers and raw payloads are omitted.

### 6.5 Broker account reads (Phase 5 for external accounts)

`GET /api/v1/brokers/{broker}/accounts` is absent in Phase 1. When a read-only adapter is implemented, it returns:

```json
{
  "items": [
    {
      "id": "internal-account-uuid",
      "broker_name": "futu",
      "display_label": "Redacted account",
      "account_type": "CASH",
      "base_currency": "HKD",
      "status": "AVAILABLE",
      "is_read_only": true,
      "observed_at": "2026-09-01T01:00:00Z",
      "cash_balances_status": "AVAILABLE",
      "positions_status": "AVAILABLE"
    }
  ],
  "next_cursor": null,
  "has_more": false
}
```

No call returns the external account ID. Offline/unentitled access returns an explicit provider problem/status and never synthetic balances.

## 7. Live-order contract boundary

There is intentionally no Phase 1-6 live-order request model exposed through FastAPI. The eventual Phase 7 contract must be distinct from paper ordering and include:

- authenticated identity and authorization result;
- immutable order draft and server-generated confirmation challenge;
- a second explicit approval command;
- idempotency key and request hash;
- risk-decision ID and passed-control list;
- market-data observation ID/age, market status, settled cash, currency and connectivity evidence;
- persistent kill-switch state and all configured limits;
- broker acknowledgement separated from confirmed fills;
- reconciliation status.

`TRADING_MODE=LIVE` alone is insufficient. Until every safety prerequisite is satisfied and the user separately authorizes enablement, the server returns 403 `LIVE_TRADING_DISABLED`; missing authentication returns 401 and insufficient authorization 403. Phase 7 must test that no alternate route/use case bypasses these gates.

## 8. Error semantics

| HTTP | Stable code examples | Meaning/retry |
|---:|---|---|
| 400 | `MALFORMED_REQUEST` | Invalid JSON/protocol; fix request |
| 401 | `AUTHENTICATION_REQUIRED` | Future protected endpoint; authenticate |
| 403 | `LIVE_TRADING_DISABLED`, `AUTHORIZATION_DENIED`, `KILL_SWITCH_ACTIVE` | Policy denial; do not blindly retry |
| 404 | `RESOURCE_NOT_FOUND`, `SECURITY_NOT_FOUND`, `BROKER_NOT_FOUND` | Resource/route absent; future-phase routes naturally return 404 |
| 409 | `IDEMPOTENCY_CONFLICT`, `INSUFFICIENT_SETTLED_CASH`, `INVALID_STATE_TRANSITION`, `STALE_VERSION`, `SECURITY_ALREADY_EXISTS`, `PORTFOLIO_VALUATION_UNAVAILABLE` | State conflict; refresh/resolve; incomplete NAV never issues/redeems units |
| 422 | `VALIDATION_ERROR`, `INVALID_DECIMAL`, `CAPABILITY_NOT_SUPPORTED`, `UNSUPPORTED_RUN_MODE`, `INSUFFICIENT_CAPITAL_FOR_MINIMUM_ORDER`, `SECURITY_NOT_VERIFIED`, `REDUCE_NOT_EXECUTABLE_DUE_TO_LOT_SIZE` | Semantically invalid/unsupported or intentionally fail-closed |
| 429 | `RATE_LIMITED` | Future provider protection; respect retry metadata |
| 502 | `PROVIDER_ERROR`, `BROKER_PROTOCOL_ERROR` | External response invalid/failure; no success assumed |
| 503 | `DATABASE_NOT_READY`, `PROVIDER_UNAVAILABLE`, `BROKER_OFFLINE`, `STALE_MARKET_DATA` | Temporarily unavailable; retry only when safe |
| 500 | `INTERNAL_ERROR` | Unexpected server failure; request ID for audit |

Provider errors are mapped to stable platform codes while preserving a redacted internal cause. An uncertain broker submission is not retried automatically as a new order; it becomes an explicit reconciliation/unknown state.

## 9. Concurrency, cache, and security headers

- Mutable resource reads may return `ETag`; updates in future phases use `If-Match` and return 409 `STALE_VERSION` on conflict.
- Financial and status responses use `Cache-Control: no-store`. Static assets may be cached by content hash.
- Loopback Phase 1 CORS is disabled unless an explicit origin is configured; wildcard production CORS is forbidden.
- State-changing browser endpoints in the future require the authentication/CSRF model selected for Phase 7. Phase 1 security creation and watchlist administration are local-only but still validate `Origin` when browser origin enforcement is configured.
- Every response carries `X-Request-ID`; logs use it without sensitive request bodies.

## 10. Contract tests

Phase-relevant tests must prove:

- OpenAPI exposes exactly the Phase 1 allowlist and contains no `/live`, paper-order, deposit, FX, strategy-run, or broker-account route;
- every financial Decimal serializes as a string and float input is rejected;
- inception-only daily/weekly/monthly returns are unavailable, while since-inception return/drawdown and zero-position unrealized P&L are exact zero;
- missing provider/price/benchmark data is null plus an explicit truthful status;
- API schemas do not include external account IDs, secrets, raw payloads, or adapter models;
- watchlist add/delete idempotency and tombstone behavior;
- security creation normalization/uniqueness, forced unverified/tradability state, unavailable mappings/rules, and strategy/order blocking;
- errors use the stable problem shape and request ID;
- provider descriptor reads do not instantiate or connect an adapter;
- later-phase idempotency conflict semantics and fill-versus-submission separation before those routes are accepted;
- Phase 2 manual-fill provenance and absence of automatic price matching;
- `PORTFOLIO_VALUATION_UNAVAILABLE` produces no partial flow/unit/ledger write.
