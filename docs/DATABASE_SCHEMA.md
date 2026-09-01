# Database Schema Specification

Status: **AUTHORITATIVE — daily + 1-minute read-only logical schema**

Decision: `MTF-001` in `docs/ROADMAP.md`

Default runtime database: SQLite

Engineering portability: PostgreSQL-compatible logical semantics

## 0. Scope and historical boundary

This document distinguishes the accepted Phase 1 schema from future logical records for Phases 2
through 4. It changes no migration and claims no future table exists. Revision
`0001_phase1_foundation`, Phase 1 tests, and review evidence remain unchanged.

Future schema has no brokerage-account observation, real-trade import, real-position tracking, or
real-account matching model. Earlier plans for those capabilities are superseded and removed.

## 1. Common conventions and invariants

### 1.1 Keys and provenance

- Table and column names use `snake_case`.
- Platform primary keys are UUIDs.
- Provider identifiers are provenance, never platform primary keys.
- Foreign keys used for lookups are indexed; delete defaults to `RESTRICT`.
- Immutable observations/facts are corrected by supersession or reversal.
- No raw provider payload may contain credentials or private account data.

### 1.2 Decimal storage

Binary float is forbidden for financial values. The logical exact type uses precision 38 and scale
18. SQLite stores validated fixed-scale canonical `TEXT` with no numeric affinity and parses
directly to `Decimal`; PostgreSQL portability uses `NUMERIC(38,18)`.

SQLite financial arithmetic occurs in Python Decimal inside one Unit of Work. Signed zero
normalizes to positive zero. The accepted Phase 1 round-trip vectors remain unchanged.

### 1.3 Time and market-data status

- Instants are timezone-aware UTC.
- Daily observations carry session date, market timezone, and calendar identity.
- Minute observations carry interval start/end and completion status.
- Point-in-time selection requires `available_at <= data_as_of` where applicable.
- Availability, delay, staleness, invalidity, and source errors are explicit.
- Polling cadence and provider latency are stored/reported as different facts.
- An unfinished minute bar cannot be stored or returned as a completed minute bar.
- A latest/intraday price cannot be stored or described as a final daily close.

At minimum, queryable market/score state distinguishes:

```text
latest_quote_at
latest_completed_minute_bar_at
latest_completed_daily_session
score_calculated_at
```

## 2. Relationship overview

```text
securities --< provider_symbol_mappings
          \--< watchlist_items >-- watchlists
          \--< market_quotes
          \--< market_daily_bars
          \--< market_minute_bars
          \--< composite_quant_scores

strategy_runs --< composite_quant_scores

portfolios --< accepted Phase 1 opening accounting facts
           \--< later simulated paper facts

paper_orders --< paper_fills -> simulated research bookkeeping

backtest_runs --< backtest_daily_points / backtest_results
```

No relation represents a real brokerage account or turns advisory output into an external command.

## 3. Accepted Phase 1 schema

Revision `0001_phase1_foundation` remains immutable historical schema. It includes canonical
Security identity and provider symbol mappings, Watchlist, strategy identity, Portfolio identity,
opening ledger/cash/unit/snapshot facts, settings, and inert capability descriptors. Historical
broker/profile-shaped tables or abstract fields in revision 0001 confer no future account-access
authority and are not changed by this documentation task.

The accepted bootstrap remains:

- AVGO, VRT, and HK.09698 identities and watchlist membership;
- one internal portfolio with HKD base currency and inception date 2026-08-31;
- HKD 20,000 balanced opening contribution;
- 200 units at NAV 100;
- complete inception snapshot;
- stable identity and drift-safe idempotency.

## 4. Phase 2 — market data, dashboard, and score MVP

Future migrations require a separately approved Phase 2 plan.

### 4.1 Provider configuration and symbol mapping

Logical configuration may record a selected independent Market Data Provider, capability/entitlement
status, safe non-secret settings, and provider-neutral symbol mappings. Credentials remain outside
the database or are referenced through an approved external-secret mechanism.

No concrete provider or interface is approved by this document.

### 4.2 `market_quotes`

Latest-quote observations may store:

- Security and provider/source/version;
- Decimal price and currency;
- quote/source event time (`latest_quote_at`);
- retrieved time;
- provider latency/delay metadata;
- market status;
- availability/quality/error status and provenance hash.

A quote is not a final daily close unless a separately sourced completed daily bar says so.

### 4.3 `market_daily_bars`

- Security/provider/source/version;
- completed session date, timezone, and calendar;
- Decimal OHLCV and approved adjustment provenance;
- observed/available/retrieved timestamps;
- content hash and quality status;
- unique provider/security/session/version.

Daily data remains a first-class supported timeframe.

### 4.4 `market_minute_bars`

The first implementation supports only completed 1-minute bars from the current trading day:

- Security/provider/source/version;
- market-local session date and timezone/calendar;
- one-minute interval start and end;
- Decimal OHLCV;
- `is_completed=true` enforced;
- available/retrieved timestamps;
- source latency, content hash, and quality status;
- unique provider/security/interval/version.

Retention policy is deferred to the Phase 2 plan. No tick, order-book, or full historical minute
replay table is an MVP requirement.

### 4.5 Dashboard market state

Dashboard state may be computed rather than persisted. Any cache/projection must preserve latest
quote time, latest completed minute-bar time, latest completed daily session, polling cadence,
provider delay, and explicit error/freshness status. Daily and minute chart series remain separate.

### 4.6 `strategy_runs` and `composite_quant_scores`

`strategy_runs` record strategy/version/parameters, input dataset hashes, timestamps, status, and
errors. `composite_quant_scores` may record:

- Security and run;
- Daily Base Score component;
- Intraday Minute Adjustment component;
- combined score and explanation;
- component coverage/missing inputs;
- reference/risk state and ranking inputs;
- `latest_completed_daily_session`;
- `latest_completed_minute_bar_at`;
- `score_calculated_at`;
- dataset/parameter/strategy hashes.

The exact score formula, weights, thresholds, bands, normalization, and sizing are not approved.
Schema implementation waits for a separate strategy Task Contract.

## 5. Phase 3 — research expansion and lightweight paper tracking

Later approved schema may add richer factor/signal history, ranking/risk analytics, simulated
paper portfolios, `paper_orders`, `paper_fills`, and paper performance series.

PaperOrder and PaperFill are internal simulations only. They are explicitly marked simulated,
carry approved research price/fee assumptions, have no external order identifier, and cannot leave
the application. Paper positions update only from confirmed PaperFill facts.

No Phase 3 table stores real cash, real positions, real trades, external account observations, or
account-matching state.

## 6. Phase 4 — backtesting and analytics

Future tables may include:

- `backtest_runs` with strategy/data/assumption hashes;
- `backtest_daily_points`;
- simulated `backtest_fills` under explicit transaction-cost assumptions;
- benchmark, attribution, exposure, drawdown, volatility, turnover, and diagnostic results;
- strategy comparison and parameter-analysis reports.

Daily-bar backtesting is baseline. Current live-session minute display does not require historical
minute replay or tick-level simulation.

## 7. Database-level rules

Minimum future constraints include:

- Decimal range/scale validation;
- immutable observation/fact update/delete rejection;
- point-in-time and source/version supersession integrity;
- uniqueness for active mappings and watchlist membership;
- unique completed bar per provider/security/interval/version;
- `is_completed=true` for returned/persisted MVP minute bars;
- quote and daily-close concepts remain distinct;
- score timestamp/component provenance and deterministic run identity;
- PaperOrder/PaperFill require simulated status and no external command identifier;
- advisory acknowledgement cannot create another domain object through a trigger.

## 8. Future migration allocation

- Phase 2: independent market data, daily/current-minute observations, dashboard projections, and
  the separately approved first score model;
- Phase 3: richer research/signal history and simulated paper records;
- Phase 4: backtest and analytics records.

No migration is planned for brokerage-account access, real-trade import, real-position tracking,
real-account matching, broker writes, real-order submission, or any phase after Phase 4.

## 9. Acceptance properties

- exact Decimal round trips and accepted Phase 1 invariants remain intact;
- missing/delayed/stale/error market data is explicit;
- unfinished minute bars are excluded from completed results;
- daily close and latest/intraday price cannot be conflated;
- polling cadence and source latency are distinct;
- daily and minute series are queryable as separate timeframes;
- score provenance identifies daily/minute inputs and calculation time;
- paper facts remain simulated;
- no schema models a real brokerage account or external execution command.
