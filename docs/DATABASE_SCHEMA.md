# Database Schema Specification

Status: **AUTHORITATIVE — EOD/no-live logical schema**

Decision: `EOD-001` in `docs/ROADMAP.md`

Default runtime database through Core MVP: SQLite

Engineering portability: PostgreSQL-compatible logical semantics

## 0. Scope and historical boundary

This document distinguishes:

- the accepted Phase 1 schema and opening facts already implemented by revision
  `0001_phase1_foundation`;
- future logical schema planned for Phase 2 through Phase 5;
- permanent exclusions imposed by `EOD-001`.

It does not change a migration or claim that a future table exists. The accepted Phase 1 reviews
remain immutable. Earlier generic order/execution designs are superseded for future migrations:
paper simulation, completed real-trade records, and broker observations use separate tables.

## 1. Common conventions and invariants

### 1.1 Keys and names

- Table/column names use `snake_case`.
- Platform primary keys are UUIDs.
- External identifiers are private provenance, never platform primary keys.
- Foreign keys used in lookups are indexed; delete behavior defaults to `RESTRICT`.
- Mutable projections carry a version and update timestamp.
- Immutable facts are corrected by reversal or supersession, not update/delete.

### 1.2 Time and completed sessions

- Instants are timezone-aware UTC.
- Completed market observations carry `session_date`, `market_timezone`, and `calendar_id`.
- Point-in-time selection requires `available_at <= data_as_of`.
- A report stores a session manifest for all markets used.
- Incomplete same-day data cannot be promoted to an official EOD report.

### 1.3 Decimal storage

Binary float is forbidden for financial values.

The v1 logical exact type is precision 38, scale 18. Semantic aliases such as
`DECIMAL_AMOUNT`, `DECIMAL_PRICE`, `DECIMAL_QUANTITY`, `DECIMAL_RATE`,
`DECIMAL_RATIO`, and `DECIMAL_SCORE` use this logical type.

| Dialect | Physical type | Behavior |
|---|---|---|
| SQLite | `TEXT` with TEXT affinity | `ExactDecimal(38,18)` writes validated fixed-scale canonical text and parses directly to Decimal |
| PostgreSQL | `NUMERIC(38,18)` | Native exact numeric binding/result through the same domain type |

SQLite financial arithmetic and ledger balance occur in Python Decimal inside one Unit of Work.
Do not use SQLite numeric casts or lexical ordering as exact financial arithmetic. Signed zero
normalizes to positive zero.

Required round-trip vectors remain:

- `100.000000000000000001`
- `12345678901234567890.123456789012345678`
- `0.123456789012345678`

### 1.4 Status taxonomies

- availability: `AVAILABLE`, `MISSING`, `UNAVAILABLE`, `NOT_SUPPORTED`, `INVALID`;
- snapshot/score quality: `COMPLETE`, `PARTIAL`, `INVALID`;
- capability: `SUPPORTED`, `NOT_SUPPORTED`, `NOT_IMPLEMENTED`, `UNAVAILABLE`, `UNKNOWN`;
- reconciliation: `PENDING`, `MATCHED`, `DISCREPANCY`, `ACCEPTED`, `REJECTED`.

Do not reuse one taxonomy for another purpose.

## 2. Relationship overview

```text
securities --< provider_symbol_mappings
          \--< watchlist_items >-- watchlists -- portfolios
          \--< strategy_assignments >-- strategy_definitions
          \--< market_daily_bars / daily_fundamental_records / daily_valuation_snapshots
          \--< composite_quant_scores

portfolios --< ledger_accounts --< ledger_entries >-- ledger_transactions
           \--< cash_flows / unit_transactions / portfolio_snapshots
           \--< positions / cash_balances
           \--< target_portfolios --< target_portfolio_items
           \--< daily_portfolio_decision_summaries
           \--< rebalance_suggestions

paper_orders --< paper_fills -> paper accounting facts

manual_real_trade_records -> reconciliation -> accounting facts
broker_observations        -> reconciliation -> accounting facts
```

No relation turns a Recommendation or RebalanceSuggestion into a real broker command.

## 3. Accepted Phase 1 schema

Revision `0001_phase1_foundation` remains immutable historical schema. It contains the foundation
tables needed for identity, configuration, opening accounting, and read APIs.

### 3.1 `securities`

Core fields:

- canonical UUID;
- unique `(market, symbol)`;
- currency, optional verified exchange/calendar/timezone;
- instrument type, enabled status;
- optional lot/minimum/quantity-step/tick/minimum-notional facts;
- metadata, record-source, verification, and tradability status;
- audit/version fields.

User-created rows are forced to `USER_SUPPLIED_UNVERIFIED`/`UNVERIFIED` and receive no invented
provider mapping or trading rule.

### 3.2 `provider_symbol_mappings`

Mappings keep provider type/name/symbol, validity, provenance, and status separate from Security.
Phase 1 guards prevent a mapping onto a user-supplied unverified Security.

### 3.3 `watchlists` and `watchlist_items`

The default portfolio watchlist supports tombstoned membership. Removal preserves history.

### 3.4 Strategy identity

`strategy_definitions` and `strategy_assignments` store versioned definitions and assignments.
Implementation status is registry-derived. The accepted AIInfra definition remains disabled and
`RESEARCH_UNVALIDATED`.

### 3.5 Portfolio/account identity

`broker_profiles` and `broker_accounts` in Phase 1 are inert descriptors/identities. They provide
no connector and no execution authority. `portfolios` and `portfolio_accounts` separate internal
portfolio grouping from account identity.

### 3.6 Opening accounting

Phase 1 retains `ledger_accounts`, `ledger_transactions`, `ledger_entries`, `cash_flows`,
`unit_transactions`, `cash_balances`, `portfolio_snapshots`, and non-secret `settings` needed for
the deterministic opening state.

The accepted bootstrap creates:

- configurable AVGO, VRT, and HK.09698 identities and watchlist membership;
- one internal portfolio, HKD base currency, inception date 2026-08-31;
- one inert paper descriptor/account;
- HKD 20,000 balanced opening contribution;
- 200 units at NAV 100;
- a complete inception snapshot at local midnight in Asia/Hong_Kong.

Stable identity and configuration fingerprinting make identical reruns idempotent and drift fail
atomically.

## 4. Phase 2 — accounting and lightweight paper portfolio

Future Phase 2 migrations may add the following logical records after a separate approved plan.

### 4.1 Ledger and cash

Retain append-only `ledger_transactions`/`ledger_entries` and add general behavior for:

- deposit, withdrawal, explicit FX, fee, tax, dividend, corporate action, settlement, reversal,
  adjustment, paper buy, and paper sell facts;
- `cash_flows` and `unit_transactions`;
- `fx_transactions` with explicit rate direction/source/time;
- `cash_balances` and settlements;
- `positions` with weighted-average cost;
- official `portfolio_snapshots` and `performance_series`.

External flows preserve unitized NAV/TWR. With positions, a complete `FLOW_PRE` snapshot is required
or the mutation fails atomically.

### 4.2 `paper_orders`

PaperOrder is simulated only:

- internal ID and idempotency key;
- portfolio/account/security;
- side, simulated order type, quantity, optional paper limit;
- created/expiration session and versioned execution assumption;
- state limited to internal paper lifecycle;
- optional Recommendation/RebalanceSuggestion provenance;
- `is_simulated=true` required.

It has no external broker-order ID and cannot be submitted outside the application.

### 4.3 `paper_fills`

PaperFill is immutable and simulated only:

- paper order, portfolio/account/security;
- side, quantity, price, currency;
- fee/tax/cost assumptions;
- completed session and simulated execution time;
- EOD or explicit manual paper-price source;
- price/source availability and manifest identity;
- `is_simulated=true`;
- linked paper ledger transaction.

One PaperOrder may have multiple PaperFills. Quantity cannot exceed the paper target. EOD execution
assumptions are labelled and versioned; no intraday matching engine is represented.

## 5. Phase 3 — EOD observations and decision support

### 5.1 `market_daily_bars`

- Security/provider/source/version;
- completed `session_date`, timezone, calendar;
- raw OHLCV, split-adjusted OHLC, total-return-adjusted close;
- currency, observed/available/retrieved timestamps;
- adjustment provenance, content hash, quality status;
- unique provider/security/session/version.

The interval is always completed daily. No quote, tick, minute, order-book, or stream table is
planned.

### 5.2 `eod_fx_rates`

- base/quote currencies and Decimal rate;
- completed valuation/session date;
- observed/available/retrieved timestamps;
- provider/source/version/hash/quality.

### 5.3 Daily fundamentals, valuations, and events

`daily_fundamental_records`, `daily_valuation_snapshots`, and `daily_event_observations` preserve
source, period/effective time, publish/available/retrieved time, version, supersession, currency,
and quality. Missing metrics remain null plus status.

### 5.4 `strategy_runs`

- portfolio/strategy/version/parameters;
- mode limited to `ANALYSIS`, `PAPER`, or later `BACKTEST`;
- completed-session manifest and `data_as_of`;
- provider/data hashes;
- status/error code.

No run mode authorizes a real transaction.

### 5.5 `composite_quant_scores`

One row per run/security/completed session:

- score 0–100, lower/upper bound if provisional;
- component breakdown and component coverage;
- quality/coverage status and missing inputs;
- advisory classification and explanation;
- target weight, risk flags;
- session date, data-as-of, generated-at, expiration;
- dataset/parameter/strategy hashes.

### 5.6 `target_portfolios` and `target_portfolio_items`

The header stores portfolio/run/session manifest, generated-at, expiration, methodology, quality,
and assumptions. Items store security, target weight, target value, optional target quantity, and
constraint/warning details.

### 5.7 `rebalance_suggestions`

- portfolio/target/current-snapshot/security;
- advisory side;
- current/target weight and deviation;
- suggested base amount and estimated quantity;
- price, FX, lot, minimum-notional, fee/tax, liquidity, and rounding assumptions;
- risk/data-quality warnings;
- expiration;
- status `OPEN`, `ACKNOWLEDGED`, `REJECTED`, `EXPIRED`, or `SUPERSEDED`.

Acknowledgement has no external effect.

### 5.8 `daily_portfolio_decision_summaries`

One row per portfolio/run stores:

- Current and Target Portfolio references;
- value, cash, concentration, exposure, aggregate risk;
- positions requiring review and Rebalance Suggestion IDs;
- estimated cash impact;
- session manifest, provenance, warnings, assumptions;
- generated-at, expiration, and quality status.

## 6. Phase 4 — daily-bar backtest and analytics

Future tables may include:

- `backtest_runs` with strategy/data/assumption hashes;
- `backtest_daily_points`;
- `backtest_paper_fills` using explicit daily-bar price assumptions;
- benchmark/attribution/diagnostic summaries.

Backtest facts are isolated from production paper and real-portfolio accounting. No intraday or
market-microstructure table is planned.

## 7. Phase 5 — completed real-trade tracking and broker observations

### 7.1 `manual_real_trade_records`

This immutable record describes a trade already completed outside the platform:

- portfolio/account/security and side;
- actual quantity, price, currency, execution time;
- fees, tax, settlement facts;
- source `MANUAL` or `FILE_IMPORT`;
- source/import ID, row hash, recorded-at, actor;
- provenance/status and optional superseded record;
- reconciliation and optional approved ledger transaction reference.

It cannot represent a pending order.

### 7.2 `broker_observations`

Immutable read-only facts:

- connector/profile/account scope;
- observation type: account metadata, cash, position, completed order, completed trade/fill, fee,
  tax, or settlement;
- external source ID/hash kept private;
- observed/available/retrieved times;
- redacted raw payload hash and canonical normalized data;
- capability/source/version/quality;
- reconciliation status.

No field is a handle for a broker command.

### 7.3 Reconciliation

`reconciliation_runs` and `reconciliation_discrepancies` compare internal projections with manual
records and BrokerObservation. Resolution records `MATCHED`, `IGNORED_WITH_REASON`, or an explicit
approved accounting adjustment. It never silently overwrites ledger facts.

## 8. Database-level rules

Minimum future constraints include:

- positive quantities/amounts with explicit direction enums;
- currency/rate consistency;
- Decimal range/scale validation;
- immutable-fact update/delete rejection;
- point-in-time and source-family supersession integrity;
- uniqueness for active mappings/assignments/memberships;
- unique Composite Quant Score per run/security/session;
- unique official target/summary per portfolio/run;
- PaperOrder/PaperFill require simulated status and cannot carry external command identifiers;
- ManualRealTradeRecord must be completed and cannot carry a pending state;
- BrokerObservation is immutable and non-command;
- Recommendation/RebalanceSuggestion acknowledgement cannot create another domain object through a
  database trigger.

High-use indexes cover completed daily bars, point-in-time daily fundamentals/valuations, ledger
sequence, paper facts, scores/session, targets/summaries, manual-trade fingerprints, observations,
and reconciliation status.

## 9. Future migration allocation

Future migrations are planned only after phase approval:

- Phase 2: accounting behavior and paper-only records;
- Phase 3: completed-daily observations, score, target, suggestion, and summary records;
- Phase 4: daily-bar backtest/analytics records;
- Phase 5: completed real-trade import, BrokerObservation, and reconciliation.

No migration is planned for broker writes, real-order submission, intraday/streaming data, or any
phase after Phase 5.

## 10. Acceptance properties

- exact Decimal round trips and Python-Decimal ledger balance;
- deterministic rebuild of cash/positions/NAV;
- external-flow NAV/TWR continuity;
- incomplete `FLOW_PRE` valuation rejects atomically;
- immutable facts reject update/delete;
- idempotent replay and conflicting replay behavior;
- point-in-time queries exclude later-available/restated facts;
- PaperOrder/PaperFill remain simulated and source-labelled;
- score/target/summary uniqueness by completed session/run;
- suggestion acknowledgement has no accounting or broker effect;
- ManualRealTradeRecord requires completed facts and provenance;
- BrokerObservation remains read-only until reconciled;
- cross-market session manifests expose differing completed-session dates.
