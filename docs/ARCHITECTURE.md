# Architecture Specification

Status: **AUTHORITATIVE — EOD/no-live architecture**

Authority: subordinate to `AGENTS.md`, `docs/ROADMAP.md`, and `docs/MASTER_SPEC.md`

Decision: `EOD-001`

## 1. Architectural outcome

The platform is a local, single-user, single-process modular monolith. FastAPI presents local APIs
and HTML; application use cases coordinate broker-agnostic core modules; SQLAlchemy/Alembic own
persistence; optional adapters read completed EOD or broker-observation data.

```text
Local browser
    |
FastAPI presentation
    |
Application use cases / Unit of Work
    |
    +-- EOD ingestion and session manifest
    +-- Strategy: indicators, factors, Composite Quant Score
    +-- Portfolio: Current/Target, deviations, Rebalance Suggestions
    +-- Accounting: ledger, cash, positions, NAV
    +-- Performance: TWR, drawdown, attribution
    +-- Backtest: deterministic daily-bar simulation
    |
SQLite (default)

Optional read-only boundaries:
    completed EOD provider/import -> immutable observations
    broker connector              -> BrokerObservation -> reconciliation

Human boundary:
    Daily Decision Summary -> user -> broker official client
    completed real trade   -> manual/file/read-only observation -> reconciliation
```

There is no application path from advisory output to a real broker command.

## 2. Dependency rule

Permitted compile-time direction:

```text
backend -> application -> core
database -----------------> core ports/domain
integrations -------------> core read-only ports/domain
composition root -> backend + application + database + integrations
```

`core` imports neither `backend`, `database`, nor `integrations`. Domain models are independent of
Pydantic, SQLAlchemy, and provider SDKs. Only the composition root selects a concrete adapter.

Adapters do not import each other. The frontend calls only local REST endpoints. A read-only broker
connector produces BrokerObservation; it does not receive a command port.

## 3. Required module separation

| Module/port | Owns | May consume | Must not own or call |
|---|---|---|---|
| Strategy | Completed-session indicators, factors, Composite Quant Score, advisory classification, explanation | Canonical EOD inputs, portfolio constraints | Broker SDKs, broker commands, accounting mutation, API/ORM objects |
| Portfolio | Current/Target Portfolio, weights, deviations, concentration, Rebalance Suggestions | Accounting views, EOD prices/FX, strategy output | Ledger posting, broker commands, provider-native models |
| Accounting | Append-only ledger, cash, positions, cost basis, units, NAV, fees/taxes | PaperFill, reconciled ManualRealTradeRecord, approved cash/FX/corporate-action facts | Strategy scoring, broker commands |
| Risk | EOD data/portfolio/assumption checks and warnings | Canonical portfolio/score/capability values | Broker SDKs or order submission |
| Performance | TWR, NAV, drawdown, benchmark and P&L attribution | Immutable facts and official EOD snapshots | External calls during calculation |
| Backtest | Historical daily clock, point-in-time cursor, EOD execution assumptions, reproducible reports | Same Strategy interface and canonical daily data | Intraday simulation, production mutation |
| Paper | PaperOrder/PaperFill lifecycle and paper-only state | EOD/manual paper price assumptions | External account/order identifiers or broker commands |
| EOD data port | Completed daily OHLCV/FX/fundamental/event observations and provenance | Provider/import source | Streaming subscriptions, execution |
| Broker observation port | Read-only account/cash/position/completed-order/completed-trade facts | Least-privilege connector | Place/cancel/modify/unlock/reserve/retry/recover |
| Reconciliation | Comparison, discrepancy, approved adjustment workflow | ManualRealTradeRecord, BrokerObservation, internal projections | Initiating a broker operation |

## 4. Package ownership

```text
src/ai_infra_quant/
  backend/                 # local HTTP, HTML, request/response mapping
  application/             # use cases and transaction boundary
  core/
    domain/
    strategy/
    portfolio/
    accounting/
    risk/
    performance/
    backtest/
    paper/
    ports/                 # EOD data, observation, repository contracts
  database/                # models, migrations, repositories
  integrations/            # read-only providers/connectors and imports
  frontend/
```

Physical creation remains phased. Existing Phase 1 packages and abstract ports are historical
artifacts; this documentation-only decision does not change code.

## 5. Canonical boundaries

- Internal IDs are canonical UUIDs; external IDs are private provenance, never primary keys.
- Instants are aware UTC. A market observation also carries completed session date, IANA timezone,
  and calendar version.
- Financial values are Decimal. SQLite uses validated fixed-scale canonical TEXT with no numeric
  affinity; PostgreSQL portability uses NUMERIC.
- Point-in-time selection requires `available_at <= data_as_of`.
- Missing facts use explicit availability/quality statuses.
- Raw observations and accounting facts are append-only; corrections supersede or reverse.

Four concepts are never conflated:

1. PaperOrder/PaperFill — internal simulated lifecycle only.
2. Recommendation/RebalanceSuggestion — advisory output only.
3. ManualRealTradeRecord — already completed external trade.
4. BrokerObservation — immutable read-only external observation pending reconciliation.

## 6. Authoritative flows

### 6.1 Daily EOD analysis

```text
completed market session
  -> read/import completed daily observations
  -> validate session/calendar/provenance/availability
  -> persist immutable observations and dataset manifest
  -> calculate indicators and factor components
  -> Composite Quant Score per security/session
  -> Target Portfolio
  -> Rebalance Suggestions
  -> Daily Portfolio Decision Summary
  -> report ready
  -> stop
```

Each report identifies cross-market session differences and rejects incomplete same-day inputs from
official status.

### 6.2 Human decision and completed real trade

```text
Decision Summary
  -> user reviews
  -> optional manual action in broker official client
  -> completed trade fact enters by manual entry/file/read-only observation
  -> validate provenance and deduplicate
  -> reconcile against internal state
  -> approve accounting fact or record discrepancy
  -> append ledger transaction
  -> rebuild projections/snapshot
```

Recommendation acknowledgement is not in this flow as an execution action; it records only the
user's review decision.

### 6.3 Paper simulation

```text
PaperOrder
  -> paper-only validation
  -> explicit EOD/manual simulation-price assumption
  -> PaperFill
  -> paper ledger transaction
  -> paper cash/position projection
```

Paper records are always labelled simulated and cannot carry a broker-write handle.

### 6.4 Accounting

The append-only ledger is the economic source of truth. Cash, positions, portfolio snapshots, and
performance are rebuildable projections. External flows are separated from return. Corrections use
reversals; reconciliation never silently overwrites internal facts.

## 7. Transactions, idempotency, and provenance

- One mutation command runs in one SQLAlchemy Unit of Work.
- Financial mutations use an idempotency key or deterministic import identity.
- Identical replay returns the existing semantic result; different content conflicts.
- Provider/connector I/O occurs outside a database write transaction.
- Observation imports store source/version/hash and are immutable.
- ManualRealTradeRecord uniqueness covers source/import ID when present and a deterministic fact
  fingerprint otherwise.
- BrokerObservation is never authoritative until reconciliation records its disposition.
- A Recommendation decision cannot create PaperOrder or ManualRealTradeRecord implicitly.

## 8. Broker and provider boundary

The platform must work offline and without a broker.

An EOD provider may expose completed daily bars, adjusted prices, EOD FX, daily fundamentals,
valuations, events, and corporate actions. It has no subscription/order-book surface.

An optional broker connector may read account metadata, cash, positions, completed orders,
completed trades/fills, fees, taxes, and settlements. It may report connection/capability status.
It may not place, cancel, replace, modify, unlock, select for execution, reserve buying power,
retry/recover a write, or run an execution worker.

If an SDK cannot enforce least-privilege read-only authority, the connector is not approved until a
separate security decision supplies an acceptable isolation boundary.

## 9. Runtime and infrastructure

```text
Browser -> 127.0.0.1 FastAPI -> SQLite
                            -> optional local EOD batch
                            -> optional read-only source/connector
```

Manual EOD execution is sufficient. A scheduler may only fetch, calculate, generate, and notify.
No microservices, queues, distributed workers, Kubernetes, multi-tenancy, high availability,
low-latency infrastructure, or 24/7 execution service is planned.

PostgreSQL compatibility remains engineering portability, not a deployment requirement.

## 10. Phase allocation

The authoritative phase set is exactly:

| Phase | Architectural increment |
|---:|---|
| 0 | Product definition, contracts, provenance/accounting boundaries, plus `EOD-001` supersession |
| 1 | Accepted foundation, exact persistence, identity/watchlist, opening facts, read APIs, inert descriptors |
| 2 | Portfolio accounting and lightweight EOD PaperOrder/PaperFill bookkeeping |
| 3 | Completed EOD data, indicators, Composite Quant Score, Target Portfolio, Rebalance Suggestions, Daily Decision Summary |
| 4 | Daily-bar backtest and analytics; completes Core MVP |
| 5 | ManualRealTradeRecord, file import, optional BrokerObservation, reconciliation, real-portfolio decision support |

No later phase exists.

## 11. Supersession register

| ID | Decision | Disposition |
|---|---|---|
| EOD-A001 | Older designs contemplated broker-write execution | Permanently removed from future scope by `EOD-001`; historical Phase 0/1 evidence remains |
| EOD-A002 | BrokerAdapter contained write signatures | Historical Phase 1 contract artifact; never approved for implementation |
| EOD-A003 | MarketDataProvider described quotes/subscriptions/order books | Replaced by completed-daily read/import contract |
| EOD-A004 | Generic Order/Fill could conflate paper and real execution | Replaced by PaperOrder/PaperFill, ManualRealTradeRecord, and BrokerObservation |
| EOD-A005 | Recommendation acceptance could create an order draft | Replaced by non-executing acknowledgement/rejection |
| EOD-A006 | Later broker phases extended beyond the Core Roadmap | Removed; Roadmap ends at Phase 5 |
| EOD-A007 | Cross-market daily cutoff was undecided | Each market uses its latest completed session; report manifest discloses differing dates |
| EOD-A008 | Always-on execution infrastructure was contemplated | Replaced by manual or simple local report-only EOD batch |

## 12. Open decisions

These do not authorize implementation:

### OD-EOD-001 — Legitimate completed-daily data source

Choose lawful file import, a documented/licensed provider, or verified read-only Futu market data.
Manual/import provenance is preferred for a reproducible first implementation.

### OD-EOD-002 — Official multi-market report policy

Define when a portfolio summary becomes official if tracked markets have different latest completed
sessions. The report must always expose the session manifest.

### OD-EOD-003 — Paper fee/tax/FX and EOD fill assumptions

Approve versioned, labelled assumptions before Phase 2 production-like simulation.

### OD-EOD-004 — Strategy formulas and target construction

Approve the Phase 3 Strategy Specification separately. This Roadmap does not approve formulae,
weights, thresholds, sizing, or profitability claims.

### OD-EOD-005 — Read-only broker least privilege

Before any Phase 5 connector, prove that permissions and code paths cannot write. Otherwise use
manual entry/import only.

## 13. Historical evidence boundary

The original Phase 0 documents and accepted Phase 1 plan/reviews necessarily contain historical
terminology from the earlier direction. Remaining sensitive terms in the immutable review files and
the accepted Phase 1 plan are historical evidence or explicit Phase 1 prohibitions. They do not
govern future scope; this architecture and `docs/ROADMAP.md` do.
