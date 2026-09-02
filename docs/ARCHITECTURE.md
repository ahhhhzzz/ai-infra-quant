# Architecture Specification

Status: **AUTHORITATIVE — read-only PAQS decision-terminal architecture**

Authority: subordinate to `AGENTS.md`, `docs/ROADMAP.md`, and `docs/MASTER_SPEC.md`

Decisions: `MTF-001`, `PAQS-MVP-001`

## 1. Architectural outcome

The platform is a local, single-user, single-process modular monolith. FastAPI presents local REST APIs and HTML; application use cases coordinate provider-agnostic modules; SQLAlchemy/Alembic own approved persistence; an independent read-only Market Data Provider adapter supplies market information.

```text
Local browser
    |
FastAPI presentation
    |
Application use cases
    |
    +-- dashboard refresh coordinator
    +-- dynamic supported US/HK watchlist administration
    +-- market-data / calendar / session validation
    +-- PAQS input timeframe derivation
    +-- PAQS structure/events/setups/risk/advisory
    +-- optional lightweight quality/ranking/history
    |
SQLite where approved persistence exists

Independent read-only boundary:
    Market Data Provider
      -> canonical quote/Daily/minute/status/calendar/security metadata

Human boundary:
    advisory display -> user -> broker official client
```

There is no brokerage-account integration and no application path to a broker command.

## 2. Dependency rule

```text
backend -> application -> core
database -----------------> core ports/domain
integrations -------------> core ports/domain
composition root -> backend + application + database + integrations
```

`core` imports neither `backend`, `database`, nor `integrations`. Domain models are independent of Pydantic, SQLAlchemy and provider SDKs. Only the composition root selects a concrete provider. Adapters do not import one another. Frontend calls only local REST endpoints.

## 3. Module separation

| Module/port | Owns | May consume | Must not own or call |
|---|---|---|---|
| Dashboard | Selector/watchlist UI, chart views, polling/countdown, later PAQS presentation | Canonical local API responses | Provider SDK objects, real account/execution concepts |
| Security/Watchlist | Canonical Security UUID identity and user-selected supported instruments | Provider-neutral security capability validation | Provider SDK objects in core, account state |
| Market-data port | Quote, completed Daily/minute bars, market status, approved calendar/security metadata | Independent provider/import source | Brokerage-account access or execution |
| PAQS input foundation | W1/D1/30m construction, session/calendar/coverage/adjustment metadata | Canonical market data | Provider SDK objects, broker/account state |
| PAQS Strategy | Structure, events, setups, invalidation/target/RR/advisory by bounded task | PAQS input foundation | Provider SDKs, broker commands, accounting mutation |
| Quality/Ranking | Optional derived prioritization/explanation | PAQS states/advisories | Creating setups or bypassing hard gates |
| Accounting/Portfolio | Accepted Phase 1 historical facts; optional future paper work only if reactivated | Explicit approved internal facts | Real-account state, PAQS rule mutation |
| Performance/Backtest | Dormant optional future extensions | Canonical historical data if explicitly reactivated | Production mutation, fabricated history |

Provider-specific code belongs under `integrations/`. Core packages do not read environment variables, import SDKs, or branch on provider names.

## 4. Market Data Provider boundary

Market-data access is independent from brokerage-account access.

Current accepted adapter path supports equivalents of:

```text
get_latest_quote()
get_daily_bars()
get_minute_bars()
get_market_status()
```

TASK-003 approved a minimal Futu OpenD quote-only adapter. TASK-004 composed it behind provider-neutral application/core boundaries. TASK-005/TASK-005B consume those responses through the local Dashboard.

TASK-006A extends the read-only provider-neutral boundary only as necessary for:

- dynamic supported US/HK security validation/mapping;
- trading-calendar/session metadata required for deterministic PAQS input preparation.

This extension must not expose account identity, cash, positions, orders, trades, account matching or command capabilities.

The three-symbol `POC_SECURITIES` tuple remains PoC/seed input only. Market-data query eligibility
and Futu provider-symbol mapping are derived dynamically from a stored enabled US/HK equity and
the canonical market currency/timezone contract.

Provider-native SDK/tabular objects remain inside `integrations/`.

## 5. Canonical market-data and PAQS input boundaries

- Internal Security IDs are UUIDs.
- Provider symbols are mappings, not application identity.
- Initial dynamic market scope remains US and HK only.
- Instants are aware UTC; market sessions carry local date, IANA timezone and calendar semantics.
- Financial values use Decimal.
- Missing/delayed/stale/unavailable/invalid/unsupported/error states are explicit.
- No market value is fabricated.
- Unfinished minute bars are excluded from completed outputs.
- Latest/intraday price is never labelled as a final Daily close.

Current Dashboard full load uses approximately 1300 completed Daily sessions and 30 market-local calendar days of completed minute data. US minute retrieval uses Futu `Session.ALL`; HK keeps normal provider sessions.

Initial PAQS derived timeframe direction:

```text
D1 canonical completed bars
   -> completed W1

completed 1m
   -> market-aware REGULAR-session filtering
   -> completed 30m
```

H1/H4 are not current MVP requirements.

TASK-006A implements this input flow in memory. Futu trading-calendar rows are mapped to canonical
day/session objects inside the integration adapter. W1 finalization follows calendar evidence,
later-week evidence, or elapsed market-local ISO week without future-bar injection. M30 requires
all expected completed minutes in each calendar-provided regular-session bucket. Derived inputs,
calendar rows, and bundles are not persisted.

PAQS input must carry coverage/session/calendar/adjustment metadata. Current provider QFQ behavior must not be silently represented as strict historical point-in-time-safe replay.

## 6. Dashboard refresh flow

Existing market-data flow remains:

```text
initial load or Security switch
  -> request bounded Daily/minute history
  -> establish recent pannable viewport

visible-page incremental/manual refresh
  -> request state/latest incremental Daily/minute data
  -> merge/deduplicate/prune browser caches
  -> render selected market chart
  -> reset approximately 60-second countdown
```

Automatic polling pauses while hidden and refreshes immediately when visible again. Requests do not overlap; abort/generation/security guards prevent stale responses overwriting newly selected securities. Closing the page requires no background activity.

Future TASK-006E may add PAQS advisory presentation without changing the read-only human boundary.

## 7. PAQS causal architecture

The causal strategy architecture is:

```text
Canonical completed market data
        ↓
PAQS Input Foundation
        ↓
Structure
        ↓
Events / Transition / Trigger / Follow-through
        ↓
Setup
        ↓
Structural Invalidation / Target / RR
        ↓
Entry / Holder Advisory
        ↓
Optional derived Quality / Ranking
```

A numerical Quality/Composite Score is a derived presentation/ranking layer if retained. It must not create a setup, bypass RR or override hard structural invalidation.

## 8. TASK-006 architectural decomposition

`TASK-006` is an umbrella workstream only.

### TASK-006A — Dynamic US/HK Securities & PAQS Input Foundation

Implemented supported-security/watchlist flow and provider-agnostic W1/D1/30m input preparation.
It implements no ATR/Pivot/Zone/Range/Regime behavior.

### TASK-006B — PAQS Structure Engine

Owns ATR, Micro/Major Pivot, Swing, Key Level geometry, Pivot Zones, Range and Base Regime. Must expose deterministic/no-lookahead structure debug evidence. Must stop for manual real-market structure review before 006C.

The TASK-006B implementation is an in-memory, provider-neutral pipeline under `core/strategy`.
It normalizes only completed W1/D1/M30 input bars, calculates Decimal ATR, runs independent Micro
and Major close-confirmed directional-change engines, labels comparable swings, constructs stable
Major-swing levels and same-role Pivot Zones, detects eligible Ranges, and assigns only
`BULL_TREND`, `BEAR_TREND`, `RANGE`, or `UNCERTAIN`. Application composition supplies the current
006A bundle and an immutable default parameter registry; the core reads no environment or provider
SDK. `GET /api/v1/strategies/paqs/securities/{security_id}/structure` is read-only and recalculates
the snapshot without persistence.

### TASK-006C — PAQS Event Engine

Owns Break Attempt/Breakout/Breakdown, Failed Breakout/Breakdown, Retest, role flip, Transition, Trigger and Follow-through. No Entry/Hold/Exit advisory.

### TASK-006D — PAQS Setup & Risk Engine

Owns approved setup families, expiry, structural invalidation, T1/T2, no-target-shopping, RR and next-open revalidation; may expose only explicitly approved Entry Advisory states.

### TASK-006E — PAQS Advisory & Decision Dashboard

Owns conditional Holder Advisory, explanations/reason codes, Dashboard integration and optional lightweight Quality/Ranking plus advisory history when approved.

Each task is separately approved/reviewed/integrated. No implementation may skip the dependency order by implementing later semantics inside an earlier task.

## 9. Paper, backtest and human boundaries

The application maintains no real-account or real-position state. Whether the user acts in the broker official client remains outside system state.

Paper Portfolio/PaperFill, position sizing and broad backtesting/analytics are dormant optional Phase 3/4 extensions under `PAQS-MVP-001`. They are not current committed MVP work and require no placeholder implementation.

If later reactivated, they consume stable provider-agnostic PAQS/advisory facts rather than changing PAQS to depend on them.

## 10. Runtime and infrastructure

```text
Browser -> 127.0.0.1 FastAPI -> SQLite
                            -> independent read-only Market Data Provider
```

No microservices, queues, distributed workers, Kubernetes, multi-tenancy, high availability, 24/7 execution service, tick store or institutional provider framework is planned. PostgreSQL compatibility remains portability, not a deployment requirement.

## 11. Phase allocation

| Phase | Architectural increment |
|---:|---|
| 0 | Historical product definition plus future-scope decisions |
| 1 | Accepted FastAPI/SQLite foundation, identity/watchlist/opening facts, read APIs |
| 2 | Active committed Market Data/Dashboard + TASK-006A–006E PAQS Decision Terminal MVP |
| 3 | Dormant optional research/paper extensions; explicit reactivation required |
| 4 | Dormant optional validation/backtest/analytics extensions; final possible phase |

The current product-completion line is Phase 2 after TASK-006E. No later phase exists after Phase 4.

## 12. Supersession register

| ID | Earlier future direction | Current disposition |
|---|---|---|
| MTF-A001 | Product restricted to completed daily data | Superseded: Daily plus completed minute analysis allowed |
| MTF-A002 | Minute/intraday analysis prohibited with execution | Superseded: read-only minute analysis allowed; execution remains forbidden |
| MTF-A003 | Real-account observation/import/matching planned | Permanently removed |
| MTF-A004 | Market data could be coupled to broker connector | Replaced by independent provider-agnostic read-only port |
| MTF-A005 | Future phases extended beyond analytics | Removed; final possible phase is Phase 4 |
| PAQS-A001 | Broad Paper/Backtest platform required before product completion | Superseded: product completion line is Phase 2 PAQS Decision Terminal MVP |
| PAQS-A002 | Composite Score is the primary causal strategy | Superseded: PAQS state/hard-gate engine is primary; score is derived if retained |
| PAQS-A003 | Three PoC symbols are permanent supported set | Superseded for future work by dynamic supported US/HK security direction |

## 13. Open decisions

These remain open and do not authorize implementation:

- TASK-006A is completed/integrated at `7909f1c04f7049cf1ccec78a3d5023ae801b7177`;
- exact PAQS structure/event/setup parameters beyond approved research locks;
- exact Quality/Composite Score formula and ranking behavior;
- whether lightweight advisory history is included in TASK-006E;
- any optional Phase 3/4 reactivation;
- any historical-minute expansion or strict real-market historical PAQS replay.

## 14. Historical evidence boundary

Accepted Phase 1 plan/review files remain immutable historical evidence and do not govern later PAQS future scope. Future docs/tasks must not rewrite them.
