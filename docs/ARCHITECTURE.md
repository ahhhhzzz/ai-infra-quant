# Architecture Specification

Status: **AUTHORITATIVE — TASK-007A integrated; TASK-007B independently reviewed; TASK-007C authorized next**

Authority: subordinate to `AGENTS.md`, `docs/ROADMAP.md`, and `docs/MASTER_SPEC.md`

Decisions: `MTF-001`, `PAQS-MVP-001`, `PAQS-DUAL-001`; R20 adoption record: `docs/decisions/R20_PRODUCT_ADOPTION_2026_09_07.md`

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
    +-- explicit PAQS-E runtime / validation / immutable Decision evidence
    +-- separate PAQS-Q deterministic/reference work when approved
    |
SQLite where approved persistence exists

Independent read-only boundary:
    Market Data Provider
      -> canonical quote/Daily/minute/status/calendar/security metadata

Internal PAQS-E reasoning boundary (no public route in TASK-007A):
    application runtime -> provider-neutral reasoning port -> OpenAI Responses adapter

TASK-007B explicit analysis boundary (independent review PASS; verify integration):
    Analyze API -> application service -> current snapshot + TASK-007A runtime
                                      -> core Decision Ledger port -> SQLAlchemy transaction

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
| PAQS-Q / historical structure | Deterministic structure and separately contracted future event/setup/risk/advisory | PAQS input foundation | Replacing PAQS-E semantics, provider SDKs, broker commands, accounting mutation |
| PAQS-E reasoning runtime | Versioned snapshot-bound request/result, registered Markdown strategy/prompt packages, deterministic contract validation | Immutable factual snapshot and explicit auxiliary context | API/UI exposure, persistence, provider SDK imports outside integrations, hidden conversation state, broker behavior |
| PAQS-E Analyze service | One explicit current request, one snapshot/runtime attempt, terminal outcome persistence and safe read queries | TASK-006B2 snapshot query, TASK-007A runtime, core Decision Ledger port | Provider SDK/SQLAlchemy imports, open database transaction across provider call, hidden prior Decision/context, automatic analysis |
| PAQS-E Decision Ledger adapter | Immutable runtime artifacts, terminal runs, validated Decision revisions and atomic commit | Core/domain evidence and SQLAlchemy session factory | Strategy/prompt loading authority, strategy inference, market-data cache/replay, broker execution facts |
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

TASK-007C adds the explicitly authorized PAQS-E workbench under `prompts/tasks/TASK-007C_PAQS_E_USER_DASHBOARD.md`.
It retains JavaScript/CSS and vendored Lightweight Charts. Market-data refresh, page load,
Security/model/strategy selection and history reads never trigger Analyze. Only the explicit Analyze
action sends a new POST; existing Decisions retain their original snapshot/as-of metadata.
No TASK-007C implementation or acceptance is claimed by this architecture update.

## 7. PAQS causal architecture

The current PAQS-E path is explicit Analyze -> immutable TASK-006B2 factual snapshot -> registered
strategy/prompt and TASK-007A provider-neutral reasoning -> deterministic contract validation ->
TASK-007B immutable evidence/Decision -> TASK-007C presentation. Storage is evidence, not strategy
or prompt authority, and prior Decisions are not implicit model context.

PAQS-Q retains separately governed deterministic Structure/Event/Setup/Risk/Advisory research.
Its exact thresholds do not silently bind PAQS-E. Optional Quality/Ranking may summarize approved
outputs but cannot create setups, bypass risk gates or conceal Q/E disagreement.

## 8. Historical TASK-006 architecture and separate PAQS-Q direction

`TASK-006` is an umbrella only. The accepted 006A/006B implementation remains preserved.
The following old 006C/006D/006E descriptions record historical decomposition; their future
authority is superseded by 006C-Q/006D-Q/006E-Q in the Roadmap. They do not gate the 007C workbench.

### TASK-006A — Dynamic US/HK Securities & PAQS Input Foundation

Implemented supported-security/watchlist flow and provider-agnostic W1/D1/30m input preparation.
It implements no ATR/Pivot/Zone/Range/Regime behavior.

### TASK-006B — PAQS Structure Engine

Owns ATR, Micro/Major Pivot, Swing, Key Level geometry, Pivot Zones, Range and Base Regime. Must expose deterministic/no-lookahead structure debug evidence. Its deterministic implementation passed; the recorded real-market checkpoint is `STRUCTURE_CONCERNS_FOUND`, motivating separately governed PAQS-Q stabilization.

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

Any Q-side successor requires its own approved contract; it must not silently expand or block the prioritized PAQS-E workstream.

## 9. Paper, backtest and human boundaries

### TASK-007A — internal PAQS-E runtime and OpenAI strategy port

TASK-007A introduces an internal-only PAQS-E reasoning boundary. A frozen versioned request binds
the exact TASK-006B2 snapshot identity and factual payload, fixed v1 runtime permissions, selected
model ID, selected registered strategy ID/content hash, runtime prompt version/hash, and an ordered
list of explicit auxiliary-context items. The accepted Master Spec remains a tracked Markdown
resource loaded through the registry; neither its body nor model choice is hard-coded in the
provider adapter.

Core and application code depend only on the provider-neutral reasoning port. The first concrete
adapter lives under `integrations/openai_reasoning/`, uses the OpenAI Responses API strict Pydantic
output path, sends a fresh request with `store=false`, and supplies no tools, background mode,
conversation, previous-response state, or fallback model. A deterministic Decimal validator may
reject identity, factual, permission, state-matrix, structural-reference, target-order, and RR
contract violations; it never upgrades or downgrades a valid PAQS-E judgment.

`OPENAI_API_KEY` is an optional server environment secret and is never part of the request/result
domain, logs, APIs, persistence, strategy resources, or prompt resources. TASK-007A registers no
Analyze endpoint and adds no Decision Ledger, Dashboard workflow, historical replay, PAQS-Q, or
broker capability.

### TASK-007B — explicit Analyze and immutable analysis evidence

TASK-007B independent review PASS covers `7785cdeeacb14f0762f6104ed99f01b5e76d1dd3`;
evidence is `docs/reviews/TASK_007B_INDEPENDENT_REVIEW.md`. Verify authoritative integration separately. The synchronous application service
accepts only a supported Security UUID, explicit model ID and registered strategy ID. It obtains
one fresh snapshot through `PaqsMarketSnapshotQueries`, loads the accepted registered strategy and
versioned prompt, builds the complete TASK-007A request with server runtime configuration and
`auxiliary_context=()`, and canonicalizes/hashes the exact request before one runtime attempt.
It neither calls the snapshot HTTP endpoint nor fetches prior Decisions as reasoning context.

Persistence follows the core-facing Decision Ledger port. The SQLAlchemy adapter opens its
transaction only after the runtime returns. Runtime artifacts plus a terminal Analysis Run commit
together; success also requires exactly one Decision in that same transaction. Provider and
validation failures commit truthful failed runs with no Decision. Success is returned only after
commit, and any failed success transaction rolls back the whole pair.

Migration revision `0002_task007b_paqs_e_ledger` follows `0001_phase1_foundation` and adds only
`paqs_e_runtime_artifacts`, `paqs_e_analysis_runs`, and `paqs_e_decisions` with their indexes,
constraints and immutable triggers. SQLite rejects UPDATE and DELETE on all three tables.
Canonical request/result JSON is stored as exact TEXT with SHA-256; artifacts preserve exact
runtime-loaded UTF-8 text and deduplicate by kind, logical key and content hash. Readback verifies
stored hashes and the Decision's direct result-summary copies. Exact Decimal/UTC persistence
uses the existing dialect-aware types; SQLite remains the configured runtime, while SQLAlchemy
and core ports preserve future PostgreSQL replaceability without a deployment change.

Decision series are `(security_id, strategy_id)`, independent of model/content version. Every
successful explicit Analyze appends the next positive revision and references its immediate
predecessor, including repeated identical snapshots. Uniqueness and transaction logic protect
revision allocation; old rows remain immutable. The request capsule stores bounded factual
evidence for a formed reasoning request, not a market-data persistence/replay service.

Read-only run, Decision and bounded Security-history APIs prepare TASK-007C without adding its
frontend. No hidden Decision memory, background analysis, PAQS-Q, paper portfolio, position state,
broker access, or execution behavior is introduced. The API key stays outside all ledger evidence.

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
| 2 | Active Market Data/Snapshot + PAQS-E TASK-007A/B/C usability work; separate PAQS-Q reference branch |
| 3 | Dormant optional research/paper extensions; explicit reactivation required |
| 4 | Dormant optional validation/backtest/analytics extensions; final possible phase |

The current-analysis usability milestone is Phase 2 after TASK-007C passes review and integration. Further adopted product capabilities are staged by bounded contracts. No later phase exists after Phase 4.

## 12. Supersession register

| ID | Earlier future direction | Current disposition |
|---|---|---|
| MTF-A001 | Product restricted to completed daily data | Superseded: Daily plus completed minute analysis allowed |
| MTF-A002 | Minute/intraday analysis prohibited with execution | Superseded: read-only minute analysis allowed; execution remains forbidden |
| MTF-A003 | Real-account observation/import/matching planned | Permanently removed |
| MTF-A004 | Market data could be coupled to broker connector | Replaced by independent provider-agnostic read-only port |
| MTF-A005 | Future phases extended beyond analytics | Removed; final possible phase is Phase 4 |
| PAQS-A001 | Broad Paper/Backtest platform required before product completion | Superseded: product completion line is Phase 2 PAQS Decision Terminal MVP |
| PAQS-A002 | Composite Score is the primary causal strategy | Superseded: PAQS-E and PAQS-Q have separate strategy authority; score is derived/reference only |
| PAQS-A003 | Three PoC symbols are permanent supported set | Superseded for future work by dynamic supported US/HK security direction |

## 13. Open decisions

These remain open and do not authorize implementation:

- TASK-006A is completed/integrated at `7909f1c04f7049cf1ccec78a3d5023ae801b7177`;
- separately scoped PAQS-Q structure/event/setup methods;
- exact Quality/Composite Score formula and ranking behavior;
- later product modules and any bounded Vue migration under the R20 adoption record;
- any optional Phase 3/4 reactivation;
- any historical-minute expansion or strict real-market historical PAQS replay.

## 14. R20 reuse boundary

`docs/decisions/R20_PRODUCT_ADOPTION_2026_09_07.md` governs capability adoption. `docs/research/R20_ADOPTION_PLAN_AND_CODEX_PROMPT_ZH.md` is historical planning context.
007C may adapt isolated CSS/layout assets and reproduce workbench interactions, preserving source
license notices. Existing API/domain contracts govern data binding. R20 Vue/Pinia/router components
are not drop-in code; its current TacticalChart uses KLineChart and crypto contract assumptions.
Do not import R20 execution, unrestricted Python plugins, plaintext secret persistence, automatic
strategy evolution, provider defaults or public-account display behavior.

Later prompt/model/version workspaces, critique/council, reviewed research suggestions, sourced
news context, simulated bookkeeping and operations must fit existing application/core/ports/adapters
and their own contracts. No third-party product document can override the broker/no-live boundary.

## 15. Historical evidence boundary

Accepted Phase 1 plan/review files remain immutable historical evidence and do not govern later PAQS future scope. Future docs/tasks must not rewrite them.
