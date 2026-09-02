# PAQS Engineering Guide — TASK-006A Input Foundation

## Authority and boundary

Implementation authority flows from `AGENTS.md`, `docs/ROADMAP.md`, `docs/MASTER_SPEC.md`, and the
approved TASK-006A contract. The PAQS v0.3.1 research lock and Review Amendment A provide adopted
input semantics where the contract says so. TASK-006A stops before ATR, pivots, structure, events,
setups, advisory, targets, risk/reward, scores, or ranking.

Phase 1 migration and review evidence remain immutable. No calendar, W1, M30, or PAQS input bundle
is persisted.

## Data flow and module boundaries

```text
stored canonical Security UUID
  -> dynamic US/HK equity market contract
  -> read-only Market Data Provider port
  -> canonical quote / completed D1 / completed 1m / trading days
  -> provider-agnostic PAQS input preparation
  -> summary-only input-status API
```

Futu SDK enums, DataFrames, and quote contexts stop inside `integrations/futu_quote/`. Core domain
types contain only Python dates/times, aware UTC datetimes, IANA timezone names, Decimal OHLCV, and
canonical enums. The composition root is the only place that selects provider mode.

## Dynamic Security mapping and validation

The market contract is:

| Market | Currency | Timezone | Initial regular session |
|---|---|---|---|
| US | USD | `America/New_York` | 09:30–16:00 |
| HK | HKD | `Asia/Hong_Kong` | 09:30–12:00, 13:00–16:00 |

Canonical provider code equals canonical display symbol (`US.NVDA`, `HK.00700`). This mapping is a
request, not proof of provider support. `POST /api/v1/watchlist/supported-securities` first requires
an AVAILABLE quote whose returned canonical symbol exactly matches. Only after validation does one
unit of work create/reuse the Security and add/reactivate the default Watchlist membership.

New identities remain `USER_SUPPLIED`, `USER_SUPPLIED_UNVERIFIED`, and tradability `UNVERIFIED`.
Research eligibility requires an enabled US/HK equity, matching market currency, and legitimate
market data. It deliberately does not call `strategy_and_orders_allowed` or require brokerage
tradability verification. A stored currency/timezone conflict fails explicitly.

## Trading-calendar port

The provider-neutral operation is `get_trading_days(market, start_date, end_date)`. A canonical row
retains market date, IANA timezone, canonical and raw provider day type, known session segments,
provider, and retrieval time. Futu `WHOLE`, `MORNING`, and `AFTERNOON` are mapped inside the adapter.
Unknown types keep their raw label and have no guessed segments. The Futu calendar excludes regular
weekends/holidays but may not reflect temporary closure anomalies; actual completed-bar coverage is
therefore measured separately.

## W1 finalization

Completed D1 bars are grouped by market-local ISO week and aggregated with first open, maximum
high, minimum low, last close, and Decimal volume sum. A candidate is finalized only when evidence
available at the cutoff shows one of:

1. the final scheduled calendar session ended;
2. a legitimately available D1 exists in a later ISO week; or
3. live market-local time passed the end of the ISO week.

Calendar source dates are compared with D1 source dates. Missing sessions make coverage PARTIAL
and keep the bar out of `completed_w1_bars`. A holiday-shortened week uses its actual last scheduled
session and does not wait for a fictional Friday. Source rows with retrieval times after the cutoff
are excluded, preventing future-bar injection.

## M30 regular-session aggregation

M30 is derived only from canonical completed 1-minute bars. Buckets are anchored independently at
each canonical session-segment start. US extended-session observations are ignored. Hong Kong lunch
is never crossed. IANA timezone conversion supplies DST behavior.

Every normal bucket expects exactly 30 distinct one-minute intervals with correct one-minute ends.
OHLCV uses first open, maximum high, minimum low, last close, and Decimal volume sum. A missing
minute produces PARTIAL coverage and cannot enter `completed_30m_bars`. Zero-fill, forward-fill,
and interpolation are forbidden. Calendar short sessions produce only buckets that fit wholly in
their mapped segment; unknown schedules produce none. Buckets whose end is after the cutoff are not
evaluated as completed.

## Adjustment, quality, and errors

The Futu path labels both source histories `PROVIDER_QFQ_CURRENT`, sets adjustment time to the
calculation cutoff, and sets `historical_replay_safe = false`. No point-in-time corporate-action
claim is inferred.

The input bundle carries source counts, complete/partial derived counts, calendar status, warnings,
and COMPLETE/PARTIAL/INVALID quality. Provider unavailable, error, entitlement, invalid response,
unknown calendar type, currency conflict, and missing bucket coverage remain distinct. Missing
prices are never represented as zero.

The diagnostic endpoint returns only counts, latest completed timestamps, adjustment/calendar
metadata, quality, and warnings. It accepts no public historical `as_of` parameter and emits no
strategy conclusion.

## Future extension points

TASK-006B may consume the provider-agnostic bundle for structure only after separate approval.
TASK-006C–006E may add events, setup/risk, and advisory/dashboard behavior in order. They must not
change input facts based on desirable later outcomes. Broader historical replay requires a separate
point-in-time adjustment/data contract.

## Common misinterpretations

| Misinterpretation | Correct meaning |
|---|---|
| Provider quote validation = brokerage tradability verification | It proves only an exact read-only quote response. |
| User-added Security = real broker instrument/account state | It is a local canonical identity with no account link. |
| Latest quote = final D1 close | Intraday/latest and completed Daily facts are separate. |
| 30m = provider-native 30m requirement | M30 is deterministically derived from completed 1m. |
| US `Session.ALL` = PAQS M30 structural session | Initial PAQS M30 filters to 09:30–16:00 regular time. |
| QFQ = automatically point-in-time-safe historical replay | Current QFQ is explicitly marked replay-unsafe. |
| PAQS input endpoint = trading recommendation | It exposes input health only and has no advisory output. |
