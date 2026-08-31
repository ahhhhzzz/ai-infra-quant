# Architecture Specification

Status: Phase 0 design freeze candidate

Authority: subordinate to `AGENTS.md` and `docs/MASTER_SPEC.md`

Scope: single-user, local-first, single-process modular monolith

## 1. Architectural outcome

The platform is one deployable Python process with a FastAPI presentation layer, application use cases, broker-agnostic domain modules, SQLAlchemy persistence, and replaceable adapters. Module boundaries are enforced through Python imports, platform-owned canonical models, repository/port interfaces, and tests. They are not process or network boundaries.

No microservices, Kafka, Redis, Celery, Kubernetes, distributed event store, or autonomous trading is part of v1. In-process domain events may be used to coordinate projections, but the database transaction remains the durability boundary.

```text
Browser (HTML/CSS/JS)
        |
FastAPI routes and versioned schemas
        |
Application use cases / transaction boundary
        |
        +--> Strategy -------> canonical Signal/Recommendation
        +--> Portfolio ------> allocation/holding views
        +--> Accounting -----> ledger, cash, positions, NAV units
        +--> Execution ------> canonical order state machine
        +--> Risk -----------> policy decisions
        +--> Performance ----> reproducible return series
        +--> Backtest -------> historical orchestration/simulation
        |
Core ports (BrokerAdapter, MarketDataProvider,
            FundamentalDataProvider, EventDataProvider, repositories)
        |
Integrations and database adapters
```

Only the composition root may select concrete adapters. Core modules receive interfaces and canonical values; they do not read environment variables, import vendor SDKs, or branch on provider names.

## 2. Dependency rule

The permitted compile-time direction is:

```text
backend -> application -> core
database -----------------> core ports/domain
integrations -------------> core ports/domain
composition root -> backend + application + database + integrations
```

`core` imports neither `backend`, `database`, nor `integrations`. `database` and `integrations` implement ports owned by the core. One adapter may use adapter-private helper code, but no adapter may import another adapter. The frontend calls only the REST API and never a broker, OpenD, or the database.

Phase 1 will add an import-boundary test that fails when a core package imports `futu`, `integrations`, `database`, `fastapi`, or another external adapter namespace.

## 3. Required module separation

| Module/port | Owns | May consume | Must not own or call |
|---|---|---|---|
| Strategy | Indicator calculation, score, data-quality gates, state transition recommendations, explanations | Canonical point-in-time market/fundamental/event inputs; portfolio constraints supplied in `StrategyContext` | Broker SDKs, order submission, cash/position mutation, API/ORM objects |
| Portfolio | Internal portfolios, account membership, target/current weights, allocation constraints, aggregate holding views | Accounting projections, canonical prices/FX, strategy recommendations | Ledger posting, fill simulation, broker SDKs, return calculation |
| Accounting | Append-only economic ledger, cash/settlement projections, weighted-average cost, position projections, unit issuance/redemption, NAV snapshots | Confirmed fills, explicit cash/FX/corporate-action events, canonical valuation inputs | Order submission, strategy scoring, provider-specific models |
| Execution | Canonical order lifecycle, idempotency, cash reservation coordination, adapter dispatch, reconciliation workflow | Risk decisions, `BrokerAdapter`, accounting commands after confirmed fills | Strategy formulas, direct position mutation, vendor types outside an adapter |
| Risk | Pre-trade and portfolio policy evaluation with explainable decisions | Canonical orders, portfolio/accounting views, capabilities, market status/age supplied as values | Broker SDKs, submitting orders, posting ledger entries |
| Performance | TWR, unitized NAV series, drawdown, benchmark and P&L attribution reports | Immutable ledger/snapshots and point-in-time prices/FX | Execution, order creation, strategy decisions, external provider calls during calculation |
| Backtest | Historical clock, point-in-time data cursor, next-bar execution simulator, fee/slippage models, result reporting | The same Strategy interface and canonical signal/order models; provider ports restricted by simulated clock | Live adapters, same-bar fills, future observations, production-account mutation |
| BrokerAdapter | Canonical broker account/order/fill/capability contract | Adapter-private SDK/API models inside `integrations/<broker>` | Strategy/accounting policy, market-data-provider selection, direct database projections |
| MarketDataProvider | Quotes, snapshots, bars, order books, subscriptions and price-data capability declaration | Provider-specific source inside its adapter | Fundamentals/events, broker execution, strategy decisions |
| FundamentalDataProvider | Point-in-time financials, estimates, valuation metrics and balance-sheet metrics with provenance | A verified source or explicit manual records | Prices masquerading as fundamentals, unsupported estimates, broker submission |
| EventDataProvider | Earnings/corporate/regulatory events and manual risk flags with provenance | A verified source or explicit manual records | Price bars, strategy state mutation, unverified scraped claims presented as facts |

This separation is mandatory even where one vendor can supply more than one capability. For example, Futu market data and Futu execution are two adapter classes behind different ports; configuring one does not configure the other.

## 4. Package ownership

The frozen logical packages are:

```text
src/ai_infra_quant/
  backend/                 # HTTP, HTML, request/response mapping
  application/             # use-case orchestration and unit of work
  core/
    domain/                # canonical immutable value/entity models
    strategy/
    portfolio/
    accounting/
    execution/
    risk/
    performance/
    backtest/
    ports/                 # provider, broker, repository contracts
  database/                # SQLAlchemy models, migrations, repositories
  integrations/            # paper/futu/eastmoney/manual/import adapters
  frontend/                # packaged templates and static assets
```

Physical creation is phased. Empty future adapter packages are not required in Phase 1. A registry may describe a planned adapter as `NOT_IMPLEMENTED` without importing or instantiating it.

## 5. Canonical model boundary

- Domain identifiers are UUIDs represented at the API as lowercase canonical strings. Vendor account/order/symbol identifiers are separate fields and are never used as primary keys.
- All instants are timezone-aware UTC. Market-local dates also carry an IANA timezone/calendar identifier.
- Currency is an uppercase ISO-4217 code. Unsupported or non-fiat units require a later schema decision.
- Money, prices, quantities, fees, tax, rates, ratios, and returns are `Decimal`; API representations are decimal strings.
- Persistence is dialect-aware: SQLite uses validated fixed-scale canonical decimal `TEXT` with no numeric affinity; PostgreSQL uses `NUMERIC(p,s)`. SQLite decimal arithmetic/balancing occurs in Python `Decimal` inside the Unit of Work, never by claiming `TEXT` `SUM`/`CAST` is exact.
- Domain and port models are independent of Pydantic, SQLAlchemy, Futu, or any other provider model.
- Capability outcomes use explicit states: `SUPPORTED`, `NOT_SUPPORTED`, `NOT_IMPLEMENTED`, `UNAVAILABLE`, and `UNKNOWN`. Missing data uses `MISSING`, `UNAVAILABLE`, or `NOT_SUPPORTED` and is never replaced by fabricated values.

## 6. Authoritative state and write flows

### 6.1 Orders and fills

```text
Recommendation (optional)
  -> StandardOrder draft
  -> RiskDecision
  -> PENDING_APPROVAL (live only)
  -> ExecutionEngine/idempotency check
  -> BrokerAdapter submission
  -> append OrderEvent
  -> confirmed FillResult
  -> append fill + accounting transaction
  -> rebuild/update cash and position projections
```

An acknowledgement (`SUBMITTED`) is not a fill. Holdings and cash change only after a confirmed fill or another explicit accounting event. The execution engine owns the internal state transition; an adapter reports facts and cannot update projections directly.

### 6.2 Accounting

The append-only double-entry ledger is the economic source of truth. `cash_balances`, `positions`, `portfolio_snapshots`, and `performance_series` are reproducible projections. Corrections use reversing and replacement transactions; rows are not overwritten or deleted. Order status history and reconciliation observations are append-only facts even though a current-state order projection is maintained for efficient reads.

For SQLite, the Unit of Work loads canonical decimal text as `Decimal`, validates transaction balance in Python, and writes all entries atomically. Database triggers protect append-only facts but do not perform or claim exact decimal aggregation over text. PostgreSQL may additionally enforce exact `NUMERIC` balance checks.

### 6.3 External data

Provider observations are immutable by provenance/version. A strategy run selects only records whose `available_at <= data_as_of`. A later restatement creates a new record linked to the superseded record and cannot change a historical run.

### 6.4 Reconciliation

The internal ledger remains authoritative for internal performance. Broker snapshots are external observations. Reconciliation records discrepancies and requires an explicit adjustment/reversal workflow; it never silently replaces internal orders, fills, positions, or cash.

## 7. Transactions, concurrency, and idempotency

- One application command runs in one SQLAlchemy unit of work and database transaction.
- SQLite runs as one application process. Financial mutation use cases serialize writes and use optimistic `version` fields on projections where stale updates matter.
- Every order, cash flow, FX conversion, and future live mutation requires a unique idempotency key. Reusing a key with the identical canonical request returns the original result; reusing it with a different request returns `IDEMPOTENCY_CONFLICT`.
- Provider calls never occur while a database write transaction is held open. The command records intent, performs external I/O, then records the observed result through an explicit state transition.
- There is no background distributed worker. Later scheduled activity, if approved, runs in process and is restart-safe through persisted jobs/events.

## 8. Runtime and safety topology

Phase 1 binds to loopback by default:

```text
Browser -> 127.0.0.1 FastAPI -> local SQLite
```

Phase 1 has no operational broker, no OpenD connection, no paper order submission, and no live routes. Missing provider data appears as unavailable. Futu SDK installation and Futu/OpenD connectivity begin no earlier than Phase 5. Live order routing begins only in Phase 7 after authentication, authorization, CSRF controls where applicable, persistent kill switch, limits, freshness/cash/market checks, reconciliation, and manual confirmation exist. Completing Phase 7 still does not authorize enabling live mode.

## 9. Phase allocation

| Phase | Architectural increment |
|---|---|
| 0 | Freeze boundaries, contracts, schema, strategy proposal, traceability, and Phase 1 plan |
| 1 | Packaging, configuration, dialect-exact persistence, canonical models/ports/registries, user-created unverified securities, minimal portfolio records, truthful portfolio/provider reads, and identity/watchlist administration only |
| 2 | PaperBroker lifecycle, explicit manual simulation fills with provenance, execution/risk baseline, append-only accounting, cash/FX/settlement, positions, NAV/TWR; no automatic price matching |
| 3 | A legitimate historical-data path, separately approved strategy, manual/provenance-aware fundamentals/events, recommendations/sizing, and provenance-backed automatic paper matching |
| 4 | Backtest clock/simulator/costs/FX/calendars/corporate actions and anti-leakage evidence |
| 5 | Futu SDK and read-only Futu market/account adapters; offline-safe startup and reconciliation observations |
| 6 | Canonical-to-Futu trading conversion with all server routes still absent/disabled |
| 7 | Live safety, authenticated manual approval, audit, and separately authorized enablement |
| 8 | EastMoney decision; implement only against a verified legitimate stable interface |

## 10. Master-spec review register

The following register records every contradiction, ambiguity, or missing design decision identified during the full review. `RESOLVED` means this Phase 0 revision makes an explicit choice and mirrors that choice into `MASTER_SPEC.md` where the master requirement itself needed clarification. `OPEN` means the issue is listed without silently selecting an option.

| ID | Master-spec issue | Resolution/status |
|---|---|---|
| DR-001 | The suggested API includes a live-order route, while live ordering is forbidden before the safety phase. | **RESOLVED:** no live-order or kill-switch route is registered in Phases 1-6. Phase 7 may register guarded routes. |
| DR-002 | Paper mutation routes are listed without phase availability. | **RESOLVED:** contracts are documented now; routes first exist in Phase 2. Phase 1 returns normal 404 because they are not registered. |
| DR-003 | Phase 1 must show HKD 20,000/NAV 100, while full accounting starts in Phase 2. | **RESOLVED:** Phase 1 seeds an idempotent opening portfolio/account, balanced opening ledger transaction, cash projection, 200 units, and inception snapshot through a migration/bootstrap service. It does not support later mutations. Phase 2 introduces the general accounting posting/rebuild behavior and must reproduce the opening economics exactly. |
| DR-004 | `ACTIVE_BROKER=paper` is shown before PaperBroker implementation. | **RESOLVED:** configuration may name `paper`, but Phase 1 exposes it as `NOT_IMPLEMENTED`; it cannot place an order. |
| DR-005 | `MARKET_DATA_PROVIDER=futu` is an example before the Futu phase. | **RESOLVED:** Phase 1 default is `none`; status is `UNAVAILABLE`. No Futu module or SDK is loaded. |
| DR-006 | Phase 3 requires historical data, but the first named real provider is Futu in Phase 5. | **OPEN (OD-001):** a legitimate Phase 3 data path must be approved; no source is assumed. |
| DR-007 | The master uses `account_id` without separating internal and vendor account identifiers. | **RESOLVED:** `account_id` is the internal UUID; `external_account_id` is adapter-owned data protected from API exposure by default. |
| DR-008 | Decimal precision/scales and JSON representation are unspecified. | **RESOLVED:** schema precision is defined in `DATABASE_SCHEMA.md`; Python uses `Decimal`; APIs use strings; float inputs are rejected for financial commands. |
| DR-009 | Append-only requirements coexist with current orders, cash balances, and positions. | **RESOLVED:** ledger entries, fills, cash flows, unit transactions, order events, and source observations are immutable; current-state tables are rebuildable projections with versions. |
| DR-010 | Settlement conventions and fee/tax schedules vary by market and date. | **OPEN (OD-003):** use explicit versioned policy configuration; no current market rule is claimed. |
| DR-011 | FX-rate direction, timestamp, and valuation source are unspecified. | **RESOLVED:** `base/quote` means quote units per one base unit; each conversion/snapshot stores rate, source, observed/available timestamps, and base-reporting conversion rate. |
| DR-012 | The exact unitized-NAV cash-flow ordering is underspecified. | **RESOLVED:** value portfolio immediately before the flow; issue/redeem `flow_base / pre_flow_nav`; post the cash and units atomically; compute post-flow NAV from equity/units, which must equal pre-flow NAV subject only to declared quantization. |
| DR-013 | A daily valuation boundary across HK and US markets is not selected. | **OPEN (OD-002):** portfolio timezone/cutoff requires approval before Phase 2 performance implementation. |
| DR-014 | FX P&L decomposition is required but no attribution convention is named. | **RESOLVED:** total base-currency P&L is invariant; Phase 2 uses transaction-date historical-cost FX for realized trade P&L and period-start/transaction/end rates for a documented residual FX attribution. Exact examples are an acceptance test. |
| DR-015 | Weighted-average cost does not say how fees/taxes are treated. | **RESOLVED:** buy-side acquisition fees/taxes increase cost; sell-side fees/taxes reduce proceeds; income/withholding are separate ledger accounts. |
| DR-016 | Corporate actions come from EventDataProvider but also mutate accounting. | **RESOLVED:** provider records are observations; only an approved, idempotent accounting command posts their economic effect. |
| DR-017 | Vendor-neutral security ID format is unspecified. | **RESOLVED:** internal UUID plus unique `(market, symbol)`; vendor symbols live only in mappings. |
| DR-018 | Raw versus adjusted prices are preserved, but indicator usage is unspecified. | **RESOLVED:** total-return-adjusted close is used for M3/M6; split-adjusted, dividend-unadjusted OHLC is used for MA/ATR/drawdown/confirmation; raw OHLC and adjustment provenance are retained. |
| DR-019 | Strategy formulas, normalization, thresholds at decimal boundaries, and sell rules are conceptual. | **RESOLVED as a proposal:** rules and golden cases are in `STRATEGY_SPEC.md`, but remain `PROPOSED / RESEARCH_UNVALIDATED`. `APPROVE PHASE 1` does not approve them; Phase 3 strategy implementation requires the separate exact instruction `APPROVE STRATEGY SPEC V1`. |
| DR-020 | `65-79` and `80-100` leave decimal-boundary wording ambiguous. | **RESOLVED:** comparisons are `>=80`, `>=65`, `>=50`, otherwise below 50. Scores are rounded only for display; gates use unrounded Decimal values. |
| DR-021 | Missing valuation can still yield the suggested 85% `COMPLETE` coverage, yet it must require manual review. | **RESOLVED:** coverage remains 85% when all price components exist, but a missing valuation/fundamental review applies a hard `REVIEW_REQUIRED` override and caps the action at WATCH. |
| DR-022 | Dual momentum says “materially negative” and “cash opportunity cost” without thresholds/source. | **RESOLVED as a proposal:** exact configurable hurdle and block rule are in `STRATEGY_SPEC.md`; no external cash series is claimed. |
| DR-023 | Strategy `confidence` has no meaning. | **RESOLVED as a proposal:** it is a deterministic data/confirmation confidence indicator, explicitly not a probability, as defined in `STRATEGY_SPEC.md`. |
| DR-024 | Strategy state changes could be confused with order or holding changes. | **RESOLVED:** recommendation state changes only from canonical context; tranche/position states advance only after confirmed fills. |
| DR-025 | Cross-sectional comparison of only three securities could dominate absolute scoring. | **RESOLVED:** it changes priority ordering only and never changes the 0-100 absolute score or turns a blocked name into an entry. |
| DR-026 | Paper partial fills are conditional on simulator support, and Phase 2 precedes any approved market-data matching path. | **RESOLVED:** Phase 2 schema/lifecycle supports multiple/partial fills but production-like fills are explicitly user-supplied manual simulation facts with `MANUAL_SIMULATION_PRICE` provenance. Automatic market/limit matching is deferred to Phase 3. Synthetic full/partial fills remain test-only. |
| DR-027 | Backtest fill timing permits an alternative next-bar model without naming controls. | **RESOLVED:** default is T-close signal/T+1-open fill; alternatives require an explicit versioned execution-assumption ID and cannot be the default. |
| DR-028 | Watchlist schema is plural while baseline API is singular. | **RESOLVED:** the database supports multiple lists; v1 API operates on the portfolio's immutable default watchlist. |
| DR-029 | Registry examples appear to register future adapters immediately. | **RESOLVED:** registries distinguish descriptors from instantiated implementations. Future adapters report `NOT_IMPLEMENTED`; no placeholder claims connectivity. |
| DR-030 | Broker reconciliation could overwrite internal accounting. | **RESOLVED:** observations and discrepancy records are append-only; adjustments require explicit reviewed transactions. |
| DR-031 | Phase 1 authentication is not specified. | **RESOLVED:** Phase 1 is loopback-only and has no financial mutation. Its only user writes are canonical-security identity creation and watchlist administration. Authentication design is deferred to the live-safety phase. Non-loopback deployment is unsupported in Phase 1. |
| DR-032 | CSRF semantics depend on the future authentication method. | **OPEN (OD-004):** select session/CSRF versus token model before Phase 7. |
| DR-033 | Settings could become a secret store. | **RESOLVED:** settings are typed, non-secret application values; secrets remain environment/external secret storage and are never returned by the API. |
| DR-034 | SQLite `NUMERIC` affinity can coerce decimal text to integer or binary `REAL`; `Numeric(asdecimal=True)` cannot guarantee exact round trips. | **RESOLVED:** SQLite uses a custom dialect-aware TypeDecorator backed by no-numeric-affinity fixed-scale canonical `TEXT`; PostgreSQL uses `NUMERIC(p,s)`. Floats are rejected. SQLite ordering/range and ledger balance use validated Python `Decimal` in one Unit of Work; no exact SQL text arithmetic is claimed. Required extreme values have exact round-trip tests. |
| DR-035 | Benchmark, broker, price, valuation, and event availability is not established. | **OPEN (OD-001/OD-005):** UI/API must say unavailable until a legitimate source and entitlement are verified. |
| DR-036 | EastMoney is required architecturally but no legitimate interface is selected. | **OPEN (OD-005):** retain only contract/capability design until Phase 8 approval. |
| DR-037 | Order cancellation/modification methods exist but route timing is unspecified. | **RESOLVED:** paper variants may start in Phase 2; Futu mapping no earlier than Phase 6; live access no earlier than Phase 7. None exists in Phase 1. |
| DR-038 | Time-in-force, fractional/odd-lot, and market rule defaults are not universal. | **RESOLVED:** canonical enums exist; capability and security metadata gate use; unsupported combinations return `CAPABILITY_NOT_SUPPORTED` rather than being guessed. |
| DR-039 | Python/tooling versions are not selected. | **RESOLVED:** Phase 1 targets CPython 3.12, Alembic, pytest, Ruff, and mypy through `pyproject.toml`; no broker SDK is a dependency. |
| DR-040 | Strategy runs require data version but providers may not supply one. | **RESOLVED:** platform computes a deterministic dataset manifest/hash over selected immutable observation IDs and provenance even when a vendor version is absent. |
| DR-041 | Allocation references give both percentages and HKD amounts, which diverge after equity changes. | **RESOLVED:** percentage is the continuing cap; HKD 8,000/7,000/5,000 is the illustration at initial HKD 20,000 only. Current cap amount is recomputed from current equity. |
| DR-042 | Inception is specified as a date but no instant/timezone is defined. | **RESOLVED:** store portfolio-local `inception_date=2026-08-31` with `valuation_timezone=Asia/Hong_Kong`; the opening instant is local midnight (`2026-08-30T16:00:00Z`). The daily performance cutoff remains OD-002. |
| DR-043 | Unit issuance/redemption is undefined if units or pre-flow NAV are non-positive. | **RESOLVED:** after initial issuance, external flows require positive outstanding units and positive pre-flow NAV. Otherwise reject the flow and require an explicit reviewed capital-recovery accounting procedure; never divide by zero or invent units. |
| DR-044 | Multiple external flows at the same instant could make TWR/unit ordering ambiguous. | **RESOLVED:** order by effective UTC instant then immutable transaction sequence; value and issue/redeem units immediately before each flow, creating a separate subperiod boundary for each. |
| DR-045 | `APPROVE PHASE 1` could be read as implicit approval of proposed strategy formulas. | **RESOLVED:** it authorizes foundation work only. Strategy implementation requires the later separate exact instruction `APPROVE STRATEGY SPEC V1`. |
| DR-046 | The 1% risk-budget/8% distance sizing formula caps exposure far below the stated allocation/tranche examples and implies a stop that is not enforced. | **OPEN (OD-006):** choose hard-stop risk-budget sizing with an enforced stop, or target-allocation sizing with ATR/historical-volatility scaling. Recommendation is target-allocation sizing; no final formula is selected. |
| DR-047 | Independently flooring 30/30/40 tranche quantities makes one- or two-unit targets unusable. | **RESOLVED:** compute cumulative legal targets and subtract confirmed cumulative fills. Small targets may use fewer executable tranches with explicit adjustment statuses and may never exceed target/cash/cap/risk constraints. |
| DR-048 | A 50% reduce of one share/lot produces a zero quantity. | **RESOLVED:** return `REDUCE_NOT_EXECUTABLE_DUE_TO_LOT_SIZE`; do not create an order. `HOLD_REVIEW` versus full `EXIT` is a separately approved user decision. |
| DR-049 | Phase 2 paper fills have no market-price source because market data starts in Phase 3/5. | **RESOLVED:** Phase 2 accepts only explicit manual simulation fills with actor/source/price/currency/observed/available provenance. Automatic matching waits for Phase 3; synthetic fills are test-only. |
| DR-050 | External cash-flow unitization can use an incomplete NAV once positions exist. | **RESOLVED:** require a complete official `FLOW_PRE` snapshot with every position mark and FX conversion. Otherwise reject with `PORTFOLIO_VALUATION_UNAVAILABLE`. |
| DR-051 | Watchlist CRUD accepts only an existing security ID, so arbitrary user symbols cannot be added. | **RESOLVED:** Phase 1 adds `POST /api/v1/securities` for canonical user-supplied unverified records. Watchlist membership is allowed, but strategy/orders remain blocked until all required metadata/provenance is verified. |
| DR-052 | A provisional/incomplete score could trigger score-based REDUCE. | **RESOLVED:** score-based reduction requires `COMPLETE`, no `REVIEW_REQUIRED`, and current approved inputs. Missing/stale valuation/fundamentals yields `HOLD_REVIEW`; independent severe trend, valid high/critical flags, approved non-tradability, and hard cap breaches retain precedence. |
| DR-053 | Inception-only return/unrealized-P&L semantics and score persistence precision were underspecified. | **RESOLVED:** inception-only daily return is null/`UNAVAILABLE`; since-inception return/drawdown may be exact zero; zero positions imply exact zero unrealized P&L independently of market-data capability; raw/gate scores retain sufficient precision and only display values are rounded. |
| DR-054 | M6 normalization history length and hurdle compounding label were unclear. | **RESOLVED:** minimum M6 normalization requires approximately 379 contiguous closes and a full 756-reference window approximately 883; the compounded hurdle input is an annual effective rate. |
| DR-055 | Formula documentation could be mistaken for validated predictive performance. | **RESOLVED:** strategy status remains `PROPOSED / RESEARCH_UNVALIDATED` until separate approval, Phase 4 backtesting, and later forward observation; no profitability/predictive claim is made. |

## 11. Open decisions requiring approval

These decisions do not block Phase 1 unless stated. `APPROVE PHASE 1` authorizes foundation work only and does not approve strategy formulas, provider choices, sizing, or later safety decisions.

### OD-001 — Legitimate Phase 3 market-data path

- Options: (A) audited import of user-supplied licensed CSV/Parquet data; (B) move verified Futu read-only market data earlier; (C) select another documented/licensed provider.
- Recommendation: **A** for Phase 3 and retain Futu integration in Phase 5.
- Trade-offs: A preserves phase separation and is reproducible but requires the user to supply lawful data; B reduces duplication but changes the approved phase order and requires OpenD/SDK earlier; C adds vendor cost, entitlement, and integration scope.
- User approval required: **Yes, before Phase 3; no impact on Phase 1.**

### OD-002 — Portfolio daily valuation cutoff

- Options: (A) one global snapshot after the latest tracked market closes; (B) 16:30 Asia/Hong_Kong with latest-known US marks; (C) per-market close series plus a separate global series.
- Recommendation: **C**, with the global official daily snapshot after the latest tracked close and clearly labelled intraday/latest views.
- Trade-offs: C is most truthful across time zones but creates more series; A is simpler but delays the daily point; B is timely in HK but mixes stale and fresh closes.
- User approval required: **Yes, before Phase 2 performance acceptance.**

### OD-003 — Paper settlement and fee/tax policy set

- Options: (A) deliberately simplified, labelled simulation policy; (B) versioned market-specific policies populated only from verified rules; (C) user-configured schedules.
- Recommendation: **B plus C overrides**, with no claim that defaults reproduce a current broker statement until verified.
- Trade-offs: verified policies improve realism but need maintenance and sources; simplified policies are stable for tests but not realistic; overrides are flexible but reduce comparability.
- User approval required: **Yes, before Phase 2 uses non-zero production-like schedules; schema work may proceed.**

### OD-004 — Phase 7 local authentication model

- Options: (A) local password plus secure server session and CSRF token; (B) short-lived bearer tokens; (C) external identity provider.
- Recommendation: **A** for local single-user v1.
- Trade-offs: A is simplest for browser safety but needs secret/session management; B complicates safe browser storage; C is excessive for local v1.
- User approval required: **Yes, before Phase 7.**

### OD-005 — Fundamental/valuation/event and EastMoney sources

- Options: (A) provenance-rich manual entry/import only; (B) a licensed documented provider; (C) leave capability unavailable.
- Recommendation: **A or C until a legitimate source and entitlement are verified.** EastMoney remains `NOT_IMPLEMENTED` unless an official stable interface is approved in Phase 8.
- Trade-offs: manual data is auditable but laborious and can become stale; licensed data may be costly/restricted; unavailable data prevents BUY/ACCUMULATE recommendations but is truthful.
- User approval required: **Yes before selecting any external source or implementing EastMoney; no impact on Phase 1.**

### OD-006 — Primary position-sizing model

- Options: (A) hard-stop risk-budget sizing, which requires an approved stop policy that is actually enforced; (B) target-allocation sizing with ATR/historical-volatility scaling under the 40%/35%/25% maximum allocations.
- Recommendation: **B** for this long-only staged investment strategy. A stress-loss/risk-budget calculation may be a secondary cap, but is not a guaranteed maximum loss without an enforced stop.
- Trade-offs: A gives explicit per-trade loss budgeting only if stops are executable/enforced and can cause very small positions/gap risk; B better matches staged allocation intent and small capital but has no predetermined maximum loss and needs stress testing.
- User approval required: **Yes as part of `APPROVE STRATEGY SPEC V1`, before Phase 3 sizing implementation; no impact on Phase 1.**

## 12. External availability statement

Phase 0 performed no network, broker, OpenD, market-data, benchmark, fundamental, valuation, event, or entitlement verification. Therefore this design claims no such data is available. Phase 1 must expose these capabilities as `UNAVAILABLE` or `NOT_IMPLEMENTED` until a legitimate source is separately verified.
