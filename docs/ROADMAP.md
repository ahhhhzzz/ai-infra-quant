# EOD Research and Manual-Trading Roadmap

Status: **AUTHORITATIVE — EOD/no-live future scope**

Decision: `EOD-001`, approved 2026-09-01

Product: **Personal End-of-Day Quant Research, Portfolio Accounting and Investment Decision Support Platform**

## 1. Authority and supersession

This Roadmap governs every future phase after the accepted Phase 1 baseline. If older planning
text conflicts with this Roadmap, `EOD-001` controls future scope.

Phase 0 design history and Phase 1 implementation/review evidence remain historical facts. Phase 1
is accepted under its original approved scope at reviewed commit
`f6decf2fbe171c1b9eb46340a9174bc21f293ede` and reviewed tree
`f03d23ededaef37096b508a3040c87ae69d89e32`. This decision does not retrofit functionality into
Phase 1 and does not alter either immutable Phase 1 review.

Earlier abstract broker-write signatures in Phase 1 code are historical contract artifacts. They
are not approved future capabilities and must not be implemented. Removing or replacing them in
code requires a separately approved implementation phase; this Roadmap commit changes no code.

## 2. Product operating model

The product is local-first, single-user, and end-of-day only. Its normal workflow is:

1. A tracked market completes its session.
2. The platform obtains completed daily data for that market.
3. It validates session completeness, provenance, availability, and staleness.
4. It calculates daily indicators and interpretable factor components.
5. It creates one Composite Quant Score for each tracked security.
6. It creates one portfolio-level Daily Portfolio Decision Summary.
7. The user reviews Current Portfolio versus Target Portfolio and Rebalance Suggestions.
8. If the user chooses to trade, the user does so manually in the broker's official client.
9. Completed real trades are entered manually, imported from a file, or optionally observed through
   a read-only broker connection.
10. Accounting and portfolio state update only from confirmed facts.

Manual triggering after market close is sufficient for Core MVP. A future local scheduler may
fetch read-only EOD data, calculate scores, generate reports, and notify the user that a report is
ready. It may perform no broker command and requires no always-on execution service.

## 3. End-of-day data boundary

Approved inputs are:

- completed daily OHLCV bars;
- adjusted daily prices and adjustment provenance;
- completed market-session dates and exchange calendars;
- end-of-day FX rates;
- daily fundamental and valuation snapshots where legitimately available;
- daily event and corporate-action observations;
- source identifiers, retrieval times, availability times, versions, and quality status.

Every calculation uses data whose `available_at` is no later than the report's `data_as_of`.
Missing data is never fabricated or silently forward-filled across a missing session.

Markets may have different completed-session dates at one wall-clock instant. A daily report must
state, for every market input:

- market and completed session date;
- data-as-of and availability timestamps;
- source and provenance;
- quality, stale, and missing status;
- whether cross-market inputs represent different completed sessions.

Incomplete same-day data must never be presented as though all tracked markets had closed.

## 4. Primary decision-support contracts

### 4.1 Composite Quant Score

There is at most one current score per tracked security and completed market session. Its contract
contains:

- a 0–100 Decimal score;
- interpretable component scores and their coverage;
- data-quality status and missing inputs;
- a concise explanation;
- advisory classification such as `STRONG`, `POSITIVE`, `NEUTRAL`, `WEAK`, or `AVOID`;
- target weight and risk flags;
- session date, data-as-of time, generated-at time, and expiration;
- optional suggested buy/sell amount and estimated quantity;
- price, FX, lot-size, minimum-notional, fee, tax, liquidity, and rounding assumptions.

Potential components include trend, absolute momentum, relative momentum, volatility, drawdown,
liquidity, valuation, financial quality, and event/risk penalties. Formulae, weights, thresholds,
and final factor definitions remain unapproved until a separate Phase 3 Strategy Specification is
approved. A score is advisory and makes no promise of profit.

### 4.2 Daily Portfolio Decision Summary

There is one summary per portfolio/report run. It contains:

- portfolio value, cash, positions, and current weights;
- Target Portfolio and target weights;
- Current versus Target deviations;
- concentration, exposure, data-quality, and aggregate risk status;
- positions requiring review;
- Rebalance Suggestions with suggested amounts and estimated quantities;
- estimated cash impact;
- price, FX, lot-size, minimum-notional, fee, tax, liquidity, and stale-data warnings;
- completed-session manifest, assumptions, timestamps, and expiration.

A Recommendation or RebalanceSuggestion is not an order. Acknowledging or rejecting one records
only the user's decision and can never trigger a broker operation.

## 5. Distinct domain concepts

### 5.1 PaperOrder and PaperFill

PaperOrder and PaperFill are internal simulations. They are always marked simulated, never leave
the application, and use an explicit EOD price source plus a versioned execution assumption.
They support lightweight paper bookkeeping, accounting validation, and strategy research.

### 5.2 Recommendation and RebalanceSuggestion

These are advisory records. They may contain side, target weight, amount, and estimated quantity.
They are not pending broker orders. User acknowledgement is non-executing metadata.

### 5.3 ManualRealTradeRecord

This records a real trade already completed outside the platform. It stores actual execution time,
price, quantity, currency, fees, tax, source, import identity, and provenance. It cannot initiate a
trade or represent a pending broker order.

### 5.4 BrokerObservation

This is an immutable read-only external observation of account metadata, cash, positions,
completed orders, completed trades/fills, fees, taxes, or settlements. It is not a command and is
not automatically authoritative until reconciled.

These concepts must remain separate in APIs, persistence, services, and UI language.

## 6. Broker policy

Broker connections are optional and read-only. A connector may import or observe account identity,
cash, positions, completed orders, completed trades/fills, fees, taxes, and settlements. It may
support reconciliation, discrepancy reporting, provenance, and connection/capability status.

Manual entry and CSV/file import are first-class alternatives. The product remains usable with no
broker connection.

A connector may not place, cancel, replace, or modify an order; unlock trading; select an account
for execution; reserve broker buying power; retry or recover a write; run an execution worker; or
expose write-capable credentials to normal application code. If read-only authority cannot be
technically isolated, the connector must be rejected or held behind a separately approved
least-privilege security decision.

## 7. Permanent product exclusions

Decision `EOD-001` permanently removes, rather than defers:

- real-time quotes, tick data, order-book feeds, streaming/WebSocket feeds, and minute bars;
- intraday calculations, intraday rebalancing, and latency-sensitive architecture;
- application-submitted real orders and any real-order API or UI;
- broker-write adapters and real `place_order`, `cancel_order`, or `modify_order` calls;
- live OMS/EMS, broker-side order state machines, and broker-side cash reservation;
- real-order approval/submission, retry, recovery, failover, or execution workers;
- broker trade-password unlock and write-capable credentials;
- kill switches whose purpose is broker execution;
- unattended or autonomous trading;
- EastMoney trading integration;
- microservices, distributed workers, Kafka/message queues, Kubernetes, cloud high availability,
  multi-tenancy, distributed execution locks, and 24/7 execution infrastructure.

These exclusions must not be relabelled optional, disabled, deferred, enterprise, or post-MVP.

## 8. Infrastructure boundary

A local FastAPI application, SQLite database, and manual or simple scheduled EOD batch are
sufficient. SQLite remains the default runtime database through Core MVP. PostgreSQL compatibility
may remain an engineering portability property; PostgreSQL deployment is not a user requirement.

## 9. Authoritative phase model

The authoritative Roadmap contains exactly Phase 0 through Phase 5. No later phase is defined.
A phase starts only after explicit user approval and an implementation plan.

### Phase 0 — Product Definition, Architecture and Contracts

Completed historically. The EOD/no-live decision now supersedes future-scope clauses while
preserving terminology, provenance, accounting principles, safety boundaries, and governance.

### Phase 1 — Foundation and Contracts

Accepted historically. Preserve deterministic migrations, exact Decimal and UTC behavior,
canonical Security identity, opening accounting, read APIs, Security/Watchlist administration,
and inert capability descriptors. Do not change Phase 1 code or retroactively expand its scope.

### Phase 2 — Portfolio Accounting and Lightweight Paper Portfolio

Plan deposits/withdrawals, cash and FX accounting, fees/taxes, positions, weighted-average cost,
realized/unrealized P&L, snapshots, manual paper transactions, deterministic EOD PaperFill
assumptions, reversals, idempotency, and reconciliation foundations. Do not build a real-time
paper exchange, intraday matching, institutional OMS, broker connection, or real broker order.

### Phase 3 — EOD Market Data, Indicators and Composite Score

Plan completed daily OHLCV and adjusted prices, EOD FX, optional daily fundamentals/valuations,
events/corporate actions, point-in-time provenance, calendars/timezones, daily indicators,
interpretable factor components, Composite Quant Score, Target Portfolio, Rebalance Suggestions,
risk flags, and the Daily Portfolio Decision Summary. No intraday calculation is permitted.
Strategy formula approval remains a separate gate.

### Phase 4 — Daily-bar Backtesting and Analytics — Core MVP

Complete Core MVP with deterministic daily-bar backtesting, point-in-time controls, EOD execution
assumptions, costs/fees/taxes, benchmark comparison, attribution, drawdown, volatility, turnover,
exposure, diagnostics, scenarios, stress analysis where justified, and reproducible reports. No
intraday backtest or market-microstructure simulation is planned.

### Phase 5 — Real Portfolio Tracking and Decision Support

Plan ManualRealTradeRecord, manual cash-flow records, CSV/file import, optional read-only broker
synchronization, BrokerObservation, reconciliation/discrepancy handling, Current Portfolio,
Target Portfolio, Current versus Target, Rebalance Suggestions, suggested amounts/estimated
quantities, constraint checks, and a daily portfolio report. The user executes every real trade
manually in the broker's official client.

## 10. Governance and stop conditions

- Phase 1 remains accepted; this decision does not begin Phase 2.
- A future phase requires an explicit approval plus a phase-specific plan.
- Any proposed feature that violates `EOD-001` is rejected, not deferred.
- Documentation, matrix entries, API contracts, and database plans must use the distinct concepts
  in Section 5.
- Each phase reports exact evidence and stops before the next phase.
