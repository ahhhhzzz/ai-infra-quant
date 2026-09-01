# Architecture Specification

Status: **AUTHORITATIVE — daily + 1-minute read-only architecture**

Authority: subordinate to `AGENTS.md`, `docs/ROADMAP.md`, and `docs/MASTER_SPEC.md`

Decision: `MTF-001`

## 1. Architectural outcome

The platform is a local, single-user, single-process modular monolith. FastAPI presents local REST
APIs and HTML; application use cases coordinate provider-agnostic modules; SQLAlchemy/Alembic own
persistence; an independent Market Data Provider adapter supplies read-only market information.

```text
Local browser
    |
FastAPI presentation
    |
Application use cases / Unit of Work
    |
    +-- dashboard refresh coordinator
    +-- daily and completed-minute data validation
    +-- Strategy: Daily Base + Intraday Minute Adjustment
    +-- ranking / reference-risk state
    +-- later paper research / performance / backtest
    |
SQLite

Independent read-only boundary:
    Market Data Provider -> canonical quote/daily/minute/status observations

Human boundary:
    advisory display -> user -> broker official client
```

There is no brokerage-account integration and no application path to a broker command.

## 2. Dependency rule

```text
backend -> application -> core
database -----------------> core ports/domain
integrations -------------> core market-data ports/domain
composition root -> backend + application + database + integrations
```

`core` imports neither `backend`, `database`, nor `integrations`. Domain models are independent of
Pydantic, SQLAlchemy, and provider SDKs. Only the composition root selects a concrete provider.
Adapters do not import one another. The frontend calls only local REST endpoints.

## 3. Module separation

| Module/port | Owns | May consume | Must not own or call |
|---|---|---|---|
| Dashboard | Selector, chart timeframe, visible-page polling/countdown, freshness/error display | Canonical API responses | Provider SDK models, account or execution concepts |
| Strategy | Indicators, Daily Base Score, Intraday Minute Adjustment, combined score, explanation | Canonical daily/minute inputs | Provider SDKs, broker commands, accounting mutation |
| Portfolio | Tracked-security ranking and later simulated allocations | Strategy/risk outputs | Real-account facts or broker commands |
| Accounting | Accepted opening facts and later approved paper bookkeeping | Confirmed PaperFill | Real-account facts or Strategy scoring |
| Risk | Explainable reference/risk states and data-quality warnings | Canonical market/score values | Provider SDKs or order submission |
| Performance | Paper/research performance | Immutable internal facts | External calls during calculation |
| Backtest | Historical daily clock, point-in-time cursor, reproducible reports | Canonical historical data and approved Strategy | Production mutation or invented minute history |
| Market data port | Quote, daily bars, completed minute bars, market status, timestamps | Independent provider/import source | Brokerage account access or execution |

Provider-specific code belongs under `integrations/`. Core packages do not read environment
variables, import SDKs, or branch on provider names.

## 4. Market Data Provider boundary

Market-data access is independent from brokerage-account access. A future adapter may implement
equivalents of:

```text
get_latest_quote()
get_daily_bars()
get_minute_bars()
get_market_status()
```

TASK-003 separately approved a minimal Futu OpenD quote-only adapter for the provider proof of
concept. TASK-004 composes it behind a provider-neutral application query service and FastAPI
presentation layer. It maps only the three explicit provider symbols to canonical quote,
market-status, completed-daily, and completed-minute results. OpenD availability,
login, entitlements, and observed delay remain external facts and are never fabricated.

TASK-005 consumes those provider-neutral responses directly from the local browser. TASK-005B
extends the existing routes with bounded historical K-line paging, a 1300-session Daily request,
and a rolling 30-calendar-day minute window. US minute requests use Futu `Session.ALL`; HK requests
retain normal HK sessions. The Dashboard uses locally vendored TradingView Lightweight Charts
5.2.1, renders daily and minute OHLCV in separate candle/volume panes, and formats chart timestamps
with the canonical IANA market timezone. It adds no backend route group, provider dependency, or
persistence.

The port is read-only and exposes no account identity, cash, position, order, trade, account matching,
or command surface.

Each backend request opens at most one short-lived quote context for the requested capability (the
state query shares one context across quote and market-status reads) and closes it at request end.
Provider-native SDK objects and tabular values remain inside `integrations/`. Provider mode `none`
returns structured unavailability without attempting an external connection.

## 5. Canonical market-data boundaries

- Internal Security IDs are UUIDs; provider symbols are mappings.
- Instants are aware UTC; sessions also carry local date, timezone, and calendar.
- Financial values are Decimal. SQLite uses canonical fixed-scale TEXT with no numeric affinity;
  PostgreSQL portability uses NUMERIC.
- Point-in-time selection requires `available_at <= data_as_of` where applicable.
- Missing, delayed, stale, unavailable, invalid, and error states are explicit.
- Raw observations are immutable or versioned with provenance.
- No market value is fabricated.

Daily bars remain supported with up to 1500 requested completed sessions. The Dashboard full load
uses 1300 Daily bars and 30 market-local calendar days of completed minute bars. Unfinished minute
bars are not returned as completed. Daily and 1-minute bars are rendered in separate coordinate
systems selected by a timeframe control.

Canonical responses distinguish:

```text
latest_quote_at
latest_completed_minute_bar_at
latest_completed_daily_session
score_calculated_at
```

Provider latency and local polling cadence are separate metadata. A latest/intraday price is never
labelled as a final daily close.

## 6. Dashboard refresh flow

```text
initial load or Security switch
  -> request full bounded Daily/minute history
  -> establish a recent pannable viewport

visible page incremental or manual refresh
  -> if no request is active, request local market state
  -> request five completed daily bars and two calendar days of minute data independently
  -> adapter reads provider state and bars
  -> merge/deduplicate/prune browser caches or return explicit per-capability error state
  -> render selected daily or 1-minute chart
  -> reset approximately 60-second countdown
```

Automatic polling pauses while the page is hidden and refreshes immediately when visible again.
Requests do not overlap, and an abort controller plus request-generation/security checks prevent
an older response from overwriting a newly selected Security. Closing the page requires no
background activity. MVP uses ordinary HTTP/REST polling; streaming infrastructure is not
required. Score/ranking/risk calculation remains future separately approved work.

## 7. Composite Score boundary

```text
Composite Quant Score = Daily Base Score + Intraday Minute Adjustment
```

The daily component represents medium-term structure. The minute adjustment represents
current-session strength/risk. The architecture carries component timestamps, coverage, missing
inputs, and `score_calculated_at`.

Exact formulae, weights, thresholds, bands, normalization, sizing, and profitability claims are
unapproved. The existing completed-daily-only proposal in `docs/STRATEGY_SPEC.md` is research history, not an
implementation contract. A later strategy Task Contract is required before implementation.

## 8. Paper and human boundaries

Later lightweight paper state is simulated only. Paper positions may change only from confirmed
PaperFill facts under a separately approved task. Advisory output does not create a paper fact.

The application maintains no real-account or real-position state. It does not observe, import, or
match real trades. Whether the user acts in the broker's official client is outside the system.

## 9. Runtime and infrastructure

```text
Browser -> 127.0.0.1 FastAPI -> SQLite
                            -> independent read-only Market Data Provider
```

No microservices, queues, distributed workers, Kubernetes, multi-tenancy, high availability,
24/7 execution service, tick store, or institutional provider framework is planned. PostgreSQL
compatibility remains portability, not a deployment requirement.

## 10. Phase allocation

| Phase | Architectural increment |
|---:|---|
| 0 | Historical product definition plus `MTF-001` future-scope supersession |
| 1 | Accepted FastAPI/SQLite foundation, identity/watchlist/opening facts, read APIs, inert descriptors |
| 2 | Independent market data, read-only dashboard, daily/current-minute views, 60-second refresh, first separately approved dual-timeframe score |
| 3 | Richer research/risk analytics, signal history, lightweight simulated paper tracking |
| 4 | Deterministic backtesting and analytics; final phase |

No later phase exists.

## 11. Supersession register

| ID | Earlier future direction | Current disposition |
|---|---|---|
| MTF-A001 | Product restricted to completed daily data | Superseded: daily plus current-session completed 1-minute data |
| MTF-A002 | Minute/intraday analysis prohibited with execution | Superseded: read-only minute analysis allowed; execution remains forbidden |
| MTF-A003 | Real-account observation/import/matching planned | Permanently removed from product scope |
| MTF-A004 | Market data could be coupled to a broker connector | Replaced by an independent provider-agnostic read-only market-data port |
| MTF-A005 | Future phases extended beyond analytics | Removed; final phase is Phase 4 |

## 12. Open decisions

These remain open and do not authorize implementation:

- operational OpenD availability, quote entitlements, pricing, latency, and live US/HK evidence;
- any provider capability beyond the bounded TASK-004 read-through backend;
- minute-data retention policy;
- exact Composite Score formula, weights, thresholds, bands, and normalization;
- later paper research assumptions;
- any historical-minute expansion beyond the daily-bar backtest baseline.

## 13. Historical evidence boundary

The accepted Phase 1 plan and review files contain terminology from earlier directions. They remain
immutable historical evidence and do not govern future scope. TASK-003 and TASK-004 change no
Phase 1 plan, review, or migration.
