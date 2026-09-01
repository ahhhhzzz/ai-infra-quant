# AI Infra Quant Platform — Master Specification v2.0

Status: **AUTHORITATIVE — EOD/no-live direction**

Superseding decision: `EOD-001` in `docs/ROADMAP.md`, approved 2026-09-01

## 0. Authority, precedence, and history

This specification defines the product and engineering boundary. Instruction precedence is:

1. the current explicit user instruction;
2. root `AGENTS.md`;
3. `docs/ROADMAP.md`;
4. this specification;
5. the current explicitly approved phase plan;
6. other documentation.

Decision `EOD-001` supersedes older future-scope clauses that contemplated real-time data,
broker-write execution, or phases beyond the current Roadmap. It does not rewrite history:

- Phase 0 design work remains completed historical evidence;
- Phase 1 remains accepted under its approved historical scope;
- the two Phase 1 review files remain immutable;
- Phase 1's abstract broker-write signatures are historical contract artifacts, not future
  implementation authority.

The accepted Phase 1 review object is commit
`f6decf2fbe171c1b9eb46340a9174bc21f293ede` with tree
`f03d23ededaef37096b508a3040c87ae69d89e32`.

## 1. Product objective

Build a **Personal End-of-Day Quant Research, Portfolio Accounting and Investment Decision Support
Platform**.

The platform is local-first and single-user. It analyzes completed daily market sessions, maintains
reproducible paper and real-portfolio accounting facts, and explains portfolio decisions. It does
not execute a real trade.

Primary outputs are:

- one Composite Quant Score for each tracked security and completed session;
- one Daily Portfolio Decision Summary per portfolio/report run;
- Current Portfolio versus Target Portfolio;
- Rebalance Suggestions;
- suggested buy/sell amounts and estimated quantities;
- explicit data-quality, risk, cost, FX, liquidity, and assumption warnings.

The user reviews the output and manually trades in the broker's official client. Completed real
trades enter the platform later by manual entry, file import, or an optional read-only broker
observation.

Initial tracked securities remain configurable:

- `US.AVGO`
- `US.VRT`
- `HK.09698`

Accepted opening facts remain configurable:

- base reporting currency `HKD`;
- initial capital `20000`;
- inception date `2026-08-31`;
- initial NAV `100` and 200 units.

## 2. Operating model

The daily workflow is:

1. wait for each required market session to complete;
2. obtain completed daily OHLCV and other approved EOD observations;
3. validate calendar/session completeness, provenance, availability, and staleness;
4. calculate daily indicators and factor components;
5. calculate Composite Quant Scores;
6. derive Target Portfolio and Rebalance Suggestions;
7. generate the Daily Portfolio Decision Summary;
8. stop after the report is available;
9. let the user decide and manually act outside the platform;
10. update accounting only from confirmed paper facts or completed real-trade facts.

Manual triggering after market close is sufficient for Core MVP. A local scheduler may later run
read-only EOD ingestion, analysis, report generation, and report-ready notification. It can never
perform a broker command.

## 3. Scope and permanent non-goals

The operating scope is:

- single-user;
- local-first;
- single-process modular monolith;
- completed daily data only;
- long-only portfolio research and accounting;
- SQLite runtime through Core MVP;
- FastAPI backend and local HTML/CSS/JavaScript frontend;
- optional read-only broker reconciliation;
- manual real-trade execution outside the application.

Decision `EOD-001` permanently excludes:

- real-time quotes, tick/order-book feeds, streaming/WebSocket feeds, and minute bars;
- intraday calculations, intraday rebalancing, or latency-sensitive design;
- application-submitted real orders or any real-order UI/API;
- broker-write adapters or `place_order`, `cancel_order`, `modify_order` calls;
- live OMS/EMS, broker-side order state machines, or broker buying-power reservation;
- real-order approval/submission, retry, recovery, failover, and execution workers;
- trade-password unlock or write-capable credentials;
- execution kill switches;
- unattended/autonomous trading and autonomous trading agents;
- EastMoney trading integration;
- microservices, Kafka/message queues, Redis/Celery workers, Kubernetes, multi-tenancy,
  distributed execution locks, cloud high availability, and 24/7 execution infrastructure.

These items are outside product scope, not disabled or deferred features.

## 4. Engineering principles

1. Strategy, Portfolio, Accounting, Risk, Performance, and Backtest remain broker-agnostic.
2. External adapters live only under `integrations/`.
3. Broker observations and market/fundamental/event data use separate read-only ports.
4. Paper simulation, advisory output, real-trade records, and broker observations are distinct.
5. Financial values use Python `Decimal`, never binary float.
6. SQLite persists exact financial values as validated fixed-scale canonical `TEXT` with no
   numeric affinity; PostgreSQL portability uses `NUMERIC(p,s)`.
7. External cash flows are separate from investment return.
8. Accounting is reproducible from immutable facts.
9. Missing/stale data is explicit and never fabricated.
10. All timestamps are aware UTC; market sessions also retain local date, timezone, and calendar.
11. Point-in-time records require `available_at <= data_as_of`.
12. A recommendation acknowledgement is metadata only and has no broker effect.
13. Real portfolio state changes only from a reconciled ManualRealTradeRecord or approved
    accounting fact.
14. Every phase is approved, implemented, verified, and stopped independently.

## 5. Target architecture

```text
Browser
  -> local FastAPI presentation
      -> application use cases / unit of work
          -> EOD data validation and manifests
          -> indicator/factor calculation
          -> Composite Quant Score
          -> Target Portfolio / Rebalance Suggestions
          -> Daily Portfolio Decision Summary
          -> accounting / performance / backtest
              -> SQLite

Optional read-only paths:
  EOD data provider or file import -> immutable observations
  Broker read-only connector       -> BrokerObservation -> reconciliation

External manual action:
  Decision Summary -> user -> broker official client
  completed trade  -> ManualRealTradeRecord/import/observation -> reconciliation -> accounting
```

The platform has no path from a Recommendation or RebalanceSuggestion to a broker command.

## 6. Module boundaries

| Module | Owns | Must not own or call |
|---|---|---|
| Strategy | Daily indicators, factor components, Composite Quant Score, advisory classifications, target weights, explanations | Broker SDKs, broker commands, accounting mutation, ORM/API objects |
| Portfolio | Current/Target Portfolio, weights, deviations, concentration, Rebalance Suggestions | Ledger posting, broker commands, provider-native models |
| Accounting | Append-only ledger, cash, positions, cost basis, fees/taxes, units, NAV | Strategy scoring, broker commands |
| Risk | EOD portfolio/assumption checks and explainable warnings | Broker SDKs or order submission |
| Performance | TWR, NAV, drawdown, attribution, benchmark analytics | External calls during calculation or portfolio mutation |
| Backtest | Historical daily clock, point-in-time cursor, EOD execution assumptions, reports | Intraday simulation, production portfolio mutation |
| Paper | PaperOrder/PaperFill simulation and paper-only state | Broker identifiers, broker commands, real-trade records |
| Import/reconciliation | ManualRealTradeRecord, BrokerObservation, CSV import, discrepancies | Initiating or representing a pending broker order |
| EOD providers | Completed daily observations and provenance | Broker execution, streaming subscriptions |

Only the composition root selects concrete read-only providers/connectors. Core packages do not
read environment variables, import provider SDKs, or branch on provider names.

## 7. Canonical domain concepts

### 7.1 Security

Security identity is vendor-neutral: internal UUID plus canonical `(market, symbol)`. Provider
symbols are mappings. User-created identities remain `USER_SUPPLIED_UNVERIFIED` until required
metadata and provenance are verified.

### 7.2 PaperOrder and PaperFill

PaperOrder and PaperFill are internal simulations only. They are marked simulated, never sent to a
broker, and use completed EOD price data or an explicit manual paper price with a versioned
execution assumption. Paper submission/fill terminology must never imply an external broker action.

### 7.3 Recommendation and RebalanceSuggestion

These are advisory. They may carry side, target weight, suggested amount, estimated quantity,
explanation, expiration, and assumptions. Acceptance/rejection records a user decision only.

### 7.4 ManualRealTradeRecord

This records a real trade already completed outside the platform. Required facts include security,
account/portfolio, side, quantity, price, currency, actual execution time, fees, taxes, source,
import identity, and provenance. It cannot represent a pending order.

### 7.5 BrokerObservation

This is an immutable read-only observation of account metadata, cash, positions, completed orders,
completed trades/fills, fees, taxes, or settlements. It is not authoritative until reconciled and
is never a command.

## 8. Data boundary and provenance

Approved granularity is completed daily:

- raw and adjusted daily OHLCV;
- completed session date, calendar, and market timezone;
- EOD FX;
- daily fundamental/valuation snapshots when legitimate;
- daily event/corporate-action observations.

Each observation stores source, source record/version, observed/session time, `available_at`,
`retrieved_at`, quality status, and a payload/content hash where appropriate. Restatements append
and supersede; they do not change historical runs.

Cross-market reports carry a session manifest. If HK and US inputs come from different latest
completed sessions, the report says so. Incomplete same-day bars cannot be mixed into an official
daily report.

No availability is claimed until a legitimate source, entitlement, and provenance path is verified.
Manual import remains a first-class source when labelled and auditable.

## 9. Accounting, cash, and portfolio state

Use an append-only double-entry ledger and rebuildable projections. Corrections use reversals or
superseding facts.

Required accounting capabilities, phased after Phase 1, include:

- deposits/withdrawals and unitized NAV;
- cash by currency and explicit FX;
- positions and weighted-average cost;
- realized/unrealized P&L;
- fees and taxes;
- corporate actions;
- portfolio snapshots and performance series;
- manual cash flows and completed real-trade records;
- reconciliation discrepancies and approved adjustments.

Deposits and withdrawals are external flows, not investment return. With positions, a flow requires
a complete point-in-time `FLOW_PRE` valuation or fails atomically with
`PORTFOLIO_VALUATION_UNAVAILABLE`.

Paper positions update only from PaperFill. Real positions update only after a ManualRealTradeRecord
or BrokerObservation is reconciled and approved as an accounting fact.

## 10. Composite Quant Score and portfolio summary

The Phase 3 security-level contract is one Composite Quant Score per tracked security/completed
session. It includes:

- Decimal score 0–100;
- component breakdown and coverage;
- data-quality/missing status;
- concise explanation and advisory classification;
- target weight and risk flags;
- session date, data-as-of, generated-at, expiration;
- optional amount and estimated quantity;
- price, FX, lot-size, minimum-notional, fee/tax, liquidity, rounding, and stale-data assumptions.

The Phase 3 portfolio-level contract is one Daily Portfolio Decision Summary containing:

- portfolio value/cash/positions and current weights;
- Target Portfolio;
- Current versus Target deviations;
- concentration, exposure, and aggregate risk;
- positions requiring review;
- Rebalance Suggestions;
- estimated cash impact and all relevant warnings;
- completed-session manifest and expiration.

Formulae, weights, thresholds, and factor definitions are not approved by this master revision.
They require separate approval of the Phase 3 Strategy Specification. No score is a promise of
profit.

## 11. Strategy governance

`docs/STRATEGY_SPEC.md` remains `PROPOSED / RESEARCH_UNVALIDATED`. Its existing formula proposal
is not approved by Phase 1 acceptance or this Roadmap refactor. Before implementation, it must be
reviewed for:

- completed-daily-data inputs only;
- point-in-time correctness;
- interpretable components;
- advisory classification and expiration;
- Current/Target portfolio behavior;
- estimated-quantity assumptions;
- no broker call or real-order object;
- deterministic golden cases.

The separate exact strategy-approval gate remains `APPROVE STRATEGY SPEC V1` unless a later user
instruction explicitly replaces it.

## 12. Daily-bar backtesting

Backtests use the same strategy object and canonical daily observations. They must defend against
look-ahead, future data, survivorship errors, bad corporate-action handling, impossible same-bar
assumptions, omitted costs/FX, and calendar/timezone errors.

Baseline execution assumptions are versioned EOD/daily-bar research assumptions, not a broker
execution claim. Reports include before/after-cost return, turnover, trades, exposure, cash,
drawdown, benchmark comparison, and assumptions.

Intraday backtesting and market-microstructure simulation are outside scope.

## 13. Broker/read-only integration

The platform works without a broker connection. Manual entry and CSV/file import are first-class.

An optional connector, including Futu, may read:

- account identity/metadata;
- cash balances and positions;
- completed orders and completed trades/fills;
- fees, taxes, and settlements;
- capability and connection status.

It may create BrokerObservation and reconciliation/discrepancy records. It may not place, cancel,
replace, modify, unlock, reserve, retry, recover, or execute anything. Write-capable credentials
must not enter normal application code. If least-privilege read-only access cannot be isolated, the
connector is rejected pending a separate security decision.

## 14. API boundary

Future APIs may expose:

- EOD data, indicators, Composite Quant Scores, and Daily Portfolio Decision Summaries;
- Current/Target portfolios and Rebalance Suggestions;
- paper-only mutations and paper facts;
- accounting cash flows and snapshots;
- backtest requests/results;
- manual completed-trade recording and CSV import;
- read-only broker synchronization/observations and reconciliation;
- Recommendation acknowledgement/rejection with no external effect.

No endpoint may transmit or prepare a real broker command.

## 15. Frontend boundary

The local dashboard should show:

- EOD session/provenance/quality status;
- portfolio value, cash, NAV, return, drawdown, and exposure;
- one Composite Quant Score and component explanation per tracked security;
- Current versus Target Portfolio;
- Rebalance Suggestions and estimated amounts/quantities;
- assumptions, expiration, and risk warnings;
- clear separation between paper simulation and recorded completed real trades.

It has no real-order submission control. It tells the user to act, if desired, in the broker's
official client.

## 16. Infrastructure and secrets

The sufficient topology is:

```text
Browser -> local FastAPI -> SQLite
                         -> optional local EOD batch
                         -> optional read-only providers/connectors
```

PostgreSQL compatibility may remain for portability but deployment is not required. Do not plan
distributed workers, queues, high availability, horizontal scaling, or execution infrastructure.

Never commit credentials, account IDs, passwords, tokens, private keys, databases, logs, or broker
exports. Read-only connector secrets remain environment/external-secret inputs and are redacted.

## 17. Authoritative phases

The authoritative phase model is exactly:

- Phase 0 — Product Definition, Architecture and Contracts (historically completed; future scope
  superseded by `EOD-001`);
- Phase 1 — Foundation and Contracts (accepted historical implementation);
- Phase 2 — Portfolio Accounting and Lightweight Paper Portfolio;
- Phase 3 — EOD Market Data, Indicators and Composite Score;
- Phase 4 — Daily-bar Backtesting and Analytics — Core MVP;
- Phase 5 — Real Portfolio Tracking and Decision Support.

Detailed scope and stop conditions are in `docs/ROADMAP.md`. No phase exists after Phase 5.

## 18. Quality and change control

For every approved implementation phase:

1. read `AGENTS.md`, Roadmap, master, architecture, database/API contracts, strategy spec, and the
   current phase plan;
2. verify Git status and preserve unrelated changes;
3. state the exact file set;
4. implement only the approved phase;
5. run migrations/application paths relevant to that phase;
6. run pytest, Ruff, and mypy as applicable;
7. verify provenance, missing-data, Decimal, UTC, and scope boundaries;
8. update documentation and matrix with actual evidence;
9. report exact results and stop.

Never claim a phase complete without evidence. Never start the next phase without explicit user
approval.

## 19. Accepted Phase 1 boundary

Phase 1 remains the reviewed foundation:

- packaging/configuration/logging;
- deterministic Alembic revision 0001 and exact cross-dialect Decimal design;
- UTC and signed-zero invariants;
- canonical Security identity and user-supplied unverified securities;
- watchlist administration;
- opening HKD 20,000, 200 units, NAV 100 accounting facts;
- read-only portfolio/performance/status APIs and dashboard;
- inert broker/provider capability descriptors;
- no PaperBroker behavior, strategy calculation, external provider call, or later-phase mutation.

This master revision neither implements Phase 2 nor changes that acceptance status.
