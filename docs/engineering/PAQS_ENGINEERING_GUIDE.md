# PAQS Engineering Guide — through TASK-006B Structure

## Authority and boundary

Implementation authority flows from `AGENTS.md`, `docs/ROADMAP.md`, `docs/MASTER_SPEC.md`, and the
approved TASK-006A and TASK-006B contracts. The PAQS v0.3.1 research lock and Review Amendment A
provide adopted semantics where a contract says so. TASK-006B stops after ATR, Pivot, Swing, Key
Level, Zone, Range, and four-state Base Regime. It contains no later Event, setup, advisory,
target/risk-reward, score, or ranking behavior.

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
an AVAILABLE quote whose returned canonical symbol/currency exactly match and whose provider-neutral
classification explicitly confirms equity. Futu maps this from `equity_valid`; false, missing, or
invalid classification fails closed. Only after validation does one unit of work create/reuse the
Security and add/reactivate the default Watchlist membership.

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

## TASK-006B normalized structure input

`core/strategy/paqs_structure.py` consumes only the provider-neutral `PaqsInputBundle`. It converts
completed W1, D1, and complete-coverage M30 inputs into one immutable `StructureBar` shape. D1 keeps
its session date; W1/M30 keep their actual interval references. No exchange-close timestamp is
invented. Partial/unfinished inputs cannot enter confirmed structure.

The three engines run independently:

```text
W1  -> CONTEXT
D1  -> SETUP
M30 -> TRIGGER
```

Input quality `INVALID` suppresses all structure calculation. Insufficient per-timeframe history
keeps ATR unavailable and Base Regime `UNCERTAIN`.

## Parameter registry and deterministic arithmetic

`PaqsStructureConfig` is frozen. Defaults are: ATR period 14; Micro/Major Pivot lambda 1.0/1.8;
minimum Pivot separation 2; equal-Swing tolerance 0.25 ATR; Zone cluster epsilon 0.50 ATR; touch
separation 5 bars; Zone halfwidth clamp 0.15–0.75 ATR; Zone merge IoU 0.50; Range lookback 40;
inside ratio 0.70; Range width 2.0–12.0 ATR. Constructor validation enforces the contract's research
ranges and rejects binary float parameters. ATR period is fixed at 14 because this task adopts no
research range for that value. A zero ATR remains an explicit zero-volatility fact, but cannot act
as a Pivot reversal threshold or Range-normalization divisor.

The `config_hash` is SHA-256 over sorted compact JSON. Decimal values use scale-insensitive
canonical strings, so `1.0` and `1.00` hash identically. Structure IDs hash explicit type,
timeframe, config and sorted source IDs/references. All boundary arithmetic uses `Decimal` inside a
local precision-50 `ROUND_HALF_EVEN` context. Exposed and recursively reused values are quantized
to 18 places; the process-global Decimal context is never mutated.

## ATR

True Range uses High minus Low on the first bar. Later bars use the maximum of High–Low,
`abs(High-previous Close)`, and `abs(Low-previous Close)`. ATR is `None` for the first 13 values.
The fourteenth is the arithmetic mean of the first 14 TR values. Later values use
`alpha = 2/(14+1)` and `ATR[t] = alpha*TR[t] + (1-alpha)*ATR[t-1]`. ATR supplies scale only.

## Independent Pivot and Swing engines

Micro and Major are separate directional-change runs; neither promotes or rewrites the other.
After ATR becomes ready, `UNSEEDED` maintains both High and Low candidates. Exactly one
close-reversal direction must meet its lambda and have an earlier extreme. If both directions
qualify on one bar, neither confirms. `SEEK_HIGH` tracks the greatest High and confirms only when a
later completed Close is at least lambda×current ATR below it; `SEEK_LOW` is symmetric. A new
extreme must be at least `pivot_min_bars` from the prior Pivot extreme. Each Pivot keeps both source
references, confirmation ATR/lambda, a stable ID, and explanation.

Labels compare confirmed Pivots of the same hierarchy and type. Current confirmation ATR times
0.25 is epsilon. Highs become HH/LH/EH and lows become HL/LL/EL using strict outside-tolerance
comparisons. Prefix tests recompute with future bars and require all earlier confirmed records to
remain byte-for-byte equivalent.

## Key Levels and Zones

Each confirmed Major Low/High creates a point SUPPORT/RESISTANCE `MAJOR_SWING` Key Level. High and
Low observations are clustered separately. Inputs are sorted by price, extreme key, confirmation
key and Pivot ID. Complete-link admission requires compatibility with every cluster member; an
eligible-cluster tie uses normalized median-center distance then stable ID.

Touches are selected chronologically and must be five source bars apart by default. One produces a
`CANDIDATE`; two produce `CONFIRMED`. Center and reference ATR are simple medians. Width uses median
absolute deviation, clamped to 0.15–0.75 reference ATR. Same-role confirmed Zones repeatedly merge
at the configured IoU, selecting highest IoU, lower bound and stable IDs in that order. The merged
geometry is recomputed from the union of accepted source observations. Candidate Zones never force
a merge. Confirmed Zone geometry also appears as `PIVOT_CLUSTER` Key Levels.

## Range and Base Regime

Range pairs require separated confirmed support/resistance Zones and at least two independent
touches per side. Chronological touches map to L/H; same-side runs compress and at least four
alternating groups are required. The latest 40 completed bars must all have ready ATR. At least
70% of closes must lie inside `[support.lower_bound, resistance.upper_bound]`; center width divided
by median lookback ATR must be 2.0–12.0. A valid Range is active only if the latest close is inside.
Multiple active candidates select by total touches, inside ratio, narrower width, then stable ID.
Range-boundary Key Levels reference geometry without mutating Zones.

Base Regime precedence is invalid/insufficient -> `UNCERTAIN`, active Range -> `RANGE`, then coherent
Major HH+HL -> `BULL_TREND` or LH+LL -> `BEAR_TREND`; everything else is `UNCERTAIN`. Bull coherence
also requires the latest close not below the latest labelled HL, and Bear coherence requires it not
above the latest labelled LH. Micro structure cannot set Base Regime.

## Structure snapshot and API

`PaqsStructureQueries` composes the current 006A bundle and immutable default config. The read-only
`GET /api/v1/strategies/paqs/securities/{security_id}/structure` endpoint has no replay/config
parameter. Its snapshot carries versions/hash, input and adjustment metadata, calculation/as-of
times, per-timeframe ATR/Pivots/labels/levels/Zones/Ranges/Regime, source references, explanations,
and warnings. Decimal values serialize as strings. Nothing is persisted.

Synthetic fixtures S01–S15 cover bull, bear, Range, insufficient history, delayed and ambiguous
Pivot confirmation, equal labels, candidate/confirmed/merged Zones, invalid/multiple Ranges,
prefix invariance, and completed M30 filtering. They are deterministic semantics tests, not market
or profitability evidence.

## Future extension points

TASK-006C–006E may add events, setup/risk, and advisory/dashboard behavior only after separate
approval and the required human review of real structure. They must not change input or structure
facts based on desirable later outcomes. Broader historical replay requires a separate
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
