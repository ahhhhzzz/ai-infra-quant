# Read-Only PAQS Decision-Terminal Product Roadmap

Status: **AUTHORITATIVE — local read-only PAQS MVP and optional extension scope**

Decisions:

- `MTF-001`, approved 2026-09-01 — daily + completed 1-minute read-only market-data direction;
- `PAQS-MVP-001`, approved 2026-09-02 — focused PAQS decision-terminal MVP, TASK-006 workstream split, optional Phase 3/4 extensions.

Decision record: `docs/decisions/PAQS_MVP_SCOPE_REDUCTION.md`

Product: **Personal Quantitative Research and Decision-Support Tool**

## 1. Authority, supersession, and history

This Roadmap governs future product scope after the accepted Phase 1 baseline.

`MTF-001` superseded the earlier completed-daily-only future direction without rewriting history. `PAQS-MVP-001` now supersedes the earlier assumption that the current product must continue through a broad paper-tracking and full-backtesting platform before it can be considered complete.

Historical facts remain unchanged:

- Phase 0 was completed historically;
- Phase 1 was implemented and independently accepted;
- the reviewed Phase 1 commit is `f6decf2fbe171c1b9eb46340a9174bc21f293ede`;
- Phase 1 status remains PASS;
- both Phase 1 review files remain immutable evidence;
- TASK-003 completed the bounded Phase 2 Futu quote-only market-data PoC;
- TASK-004 implemented the provider-neutral read-through market-data backend;
- TASK-005 implemented the market-data Dashboard;
- TASK-005A implemented the Windows one-click launcher;
- TASK-005B implemented bounded long Daily history, recent minute history, US `Session.ALL`, incremental browser refresh, and chart-time semantics.

Earlier Phase 1 broker/provider abstractions are historical artifacts, not authority to implement brokerage-account or broker-write behavior.

## 2. Current product objective

The committed MVP is a local-first, single-user, read-only personal investment decision terminal.

The product should let the user:

```text
add supported US/HK securities
        ↓
view truthful read-only market data
        ↓
understand PAQS market structure
        ↓
see PAQS events/setups
        ↓
see structural invalidation/target/RR
        ↓
receive conditional Entry / Holder advisory
        ↓
compare opportunities with lightweight Quality/Ranking
```

All real trading is performed manually by the user in the broker's official client.

The application never needs to know whether a recommendation was acted upon and never connects to a brokerage account.

## 3. Market-data and supported-security direction

Market-data access and brokerage-account access remain separate concepts.

The approved provider path is independent read-only market data. Current implementation uses Futu OpenD quote-only APIs behind a provider-neutral application/core boundary.

Existing Phase 2 capabilities include:

- latest quote and market state;
- completed Daily OHLCV;
- recent completed 1-minute OHLCV;
- approximately 1300 Daily sessions for Dashboard full load;
- recent 30 market-local calendar days of minute history;
- Futu `Session.ALL` for US minute history;
- normal HK provider sessions;
- explicit missing/unavailable/error semantics;
- no production market-data persistence.

The initial PoC symbols were:

```text
US.AVGO
US.VRT
HK.09698
```

`PAQS-MVP-001` requires the current MVP to progress from this hard-coded PoC set to a user-manageable supported US/HK watchlist under TASK-006A. Dynamic security support does not authorize arbitrary global markets.

Provider-specific code remains under `integrations/`; PAQS/Strategy, Dashboard, Risk, optional future Performance/Backtest, and core domain logic consume provider-agnostic canonical data.

## 4. Dashboard and refresh contract

The existing market Dashboard remains retained:

- security selector;
- latest price and market status;
- separate Daily and 1-minute charts;
- volume;
- market-data timestamps and status;
- manual refresh;
- approximately 60-second visible-page refresh;
- automatic-refresh countdown;
- no overlapping requests;
- pause while hidden and immediate refresh on visibility return;
- pannable long Daily/minute chart history;
- local vendored chart dependency;
- Windows one-click launch path.

Future PAQS Dashboard work is additive. It must not reintroduce trading controls or imply a real brokerage position.

Closing the page requires no background processing.

## 5. Time, data-quality, and PAQS input direction

Quotes, bars and later PAQS outputs distinguish their own timestamps. At minimum existing market data already distinguishes:

```text
latest_quote_at
latest_completed_minute_bar_at
latest_completed_daily_session
```

Future PAQS outputs require `as_of_timestamp`, component confirmation timestamps, coverage and calculation time.

Rules remain fixed:

- unfinished minute bars are never treated as completed;
- latest/intraday price is never called a final daily close;
- polling cadence and provider latency are separate facts;
- no market value is fabricated;
- financial values use Decimal;
- aware UTC is used for instants and IANA market timezones for session/calendar semantics.

The initial PAQS multi-timeframe research direction is:

```text
HTF = completed W1
STF = completed D1
TTF = completed 30m REGULAR-session bars
```

W1 is derived from completed D1; 30m is derived from completed 1-minute data with market-aware US/HK session rules. H1/H4 are not current MVP requirements.

Strict historical real-market PAQS backtesting is not part of the current MVP. Point-in-time corporate-action safety must not be falsely claimed from provider QFQ data alone.

## 6. PAQS and numerical Score relationship

The approved high-level score decomposition from `MTF-001` remains historical/current score-level governance:

```text
Composite Quant Score
=
Daily Base Score
+
Intraday Minute Adjustment
```

`PAQS-MVP-001` clarifies that this numerical score is **not** the causal strategy engine.

The primary decision path is:

```text
canonical completed market data
        ↓
PAQS structure / events / setups
        ↓
structural hard gates + risk/reward
        ↓
Entry / Holder advisory
        ↓
optional derived Quality / Composite Score and ranking
```

A future numerical score may summarize or rank already-defined structural states. It may never:

- fabricate an Event or Setup;
- bypass structural invalidation;
- bypass RR;
- convert missing data into zero;
- convert `NO_TRADE` into `LONG_READY`;
- claim probability without a separately validated/calibrated model.

Exact Quality/Composite formulae remain separately unapproved.

## 7. Authoritative phase model and current product-completion line

The authoritative phase sequence remains exactly Phase 0 through Phase 4. No Phase 5 exists.

### Phase 0 — Product Definition & Architecture

Historically completed. Later scope decisions do not rewrite historical evidence.

### Phase 1 — Foundation

Completed and independently accepted. Preserve accepted FastAPI/SQLite/SQLAlchemy/Alembic foundation, deterministic migration 0001, Decimal/UTC invariants, Security identity, Watchlist, opening accounting facts, accepted APIs/frontend, tests and review evidence.

### Phase 2 — Market Data, Dashboard & PAQS Decision Terminal MVP

Phase 2 is the active and committed product phase.

Completed increments:

```text
TASK-003   Futu quote-only Market Data PoC
TASK-004   Provider-neutral Market Data Backend
TASK-005   Market Data Dashboard
TASK-005A  Windows one-click launcher
TASK-005B  Expanded history + US 24H minute semantics
TASK-006A  Dynamic US/HK Securities & PAQS Input Foundation
```

TASK-006A passed focused remediation and was integrated at
`7909f1c04f7049cf1ccec78a3d5023ae801b7177`. TASK-006B is the current bounded implementation
task; its result remains subject to independent review and the mandatory real-structure checkpoint.

Planned PAQS umbrella workstream:

```text
TASK-006   PAQS Decision-Terminal Workstream (umbrella only; not an implementation task)
```

Planned bounded tasks, each requiring its own explicit Task Contract and approval:

#### TASK-006A — Dynamic US/HK Securities & PAQS Input Foundation (completed/integrated)

Planned scope:

- dynamic supported US/HK security/watchlist workflow replacing the three-symbol PoC restriction;
- provider support validation without account access;
- provider-agnostic trading-calendar/session contract;
- completed W1 derivation from D1;
- regular-session completed 30m derivation from 1m;
- coverage/data-quality/adjustment-basis metadata;
- PAQS user/engineering documentation foundations.

Explicitly excludes PAQS ATR/Pivot/Zone/Range/Regime logic.

#### TASK-006B — PAQS Structure Engine (current bounded task)

Planned scope:

- ATR;
- Micro/Major confirmed directional-change Pivot;
- Swing labels;
- Key Level geometry;
- Pivot Zones;
- Range detection;
- Base Regime;
- deterministic/no-lookahead structure fixtures and debug output.

Mandatory stop/checkpoint: review real read-only structures before TASK-006C approval.

#### TASK-006C — PAQS Event Engine

Planned scope:

- Break Attempt / Breakout / Breakdown;
- Failed Breakout / Failed Breakdown;
- Retest lifecycle;
- Key Level role flip;
- Regime Transition;
- Trigger;
- Follow-through.

No user Entry/Hold/Exit advisory is authorized by this task.

#### TASK-006D — PAQS Setup & Risk Engine

Planned scope:

- core setup families;
- Setup expiry;
- setup-specific structural invalidation;
- structural Target T1/T2 selection;
- no-target-shopping invariant;
- RR hard gate;
- next-open entry revalidation;
- explicitly approved Entry Advisory states.

#### TASK-006E — PAQS Advisory & Decision Dashboard

Planned scope:

- conditional Holder Advisory;
- explanations/reason codes;
- PAQS Dashboard integration;
- lightweight Quality/Ranking after hard gates if separately approved;
- lightweight immutable signal/advisory history if separately approved;
- complete user-facing decision-terminal workflow.

The current committed product may be considered functionally complete after TASK-006E passes independent review and integration.

### Phase 3 — Dormant Optional Research / Paper Extensions

Phase 3 remains a valid extension slot but is **not part of the current committed MVP sequence**.

Possible future work may be reactivated only by explicit user approval, such as:

- richer research extensions;
- simulated Paper Portfolio;
- PaperFill bookkeeping;
- paper NAV/performance;
- position sizing;
- portfolio exposure/correlation controls.

No placeholder Phase 3 implementation is required now.

### Phase 4 — Dormant Optional Validation / Backtest / Analytics Extensions

Phase 4 remains the final possible product phase but is **not required for current product completion**.

Possible future work may be reactivated only by explicit user approval, such as:

- deterministic point-in-time backtesting using legitimate data;
- transaction-cost assumptions;
- benchmark comparison;
- drawdown/volatility/turnover;
- attribution/exposure;
- strategy comparison/parameter analysis;
- reproducible research reports.

Current recent-minute capability does not imply historical minute replay, tick simulation, or market-microstructure storage.

## 8. Current MVP scope disposition

### KEEP

```text
local single-user app
read-only market data
Dashboard
Windows launcher
dynamic supported US/HK watchlist
PAQS structure/events/setups/risk-reward/advisory
lightweight explanations
lightweight Quality/Ranking if approved
lightweight signal/advisory history if approved
user + engineering documentation
```

### SIMPLIFY

```text
Composite Score -> derived quality/ranking layer, not causal strategy
ranking -> lightweight decision prioritization, not portfolio optimizer
validation -> proportional PAQS/golden-fixture validation, not institutional platform
```

### OPTIONAL FUTURE EXTENSIONS

```text
Paper Portfolio
Paper Accounting / PaperFill bookkeeping
Position sizing
Portfolio optimization
Full backtesting platform
Performance attribution/exposure analytics
Large research-report / parameter-analysis suite
```

These are not current committed work but may be attached later through Phase 3/4 without rewriting PAQS core boundaries.

## 9. Permanently removed / forbidden product scope

The following remain permanently outside the product rather than merely deferred:

```text
real completed-trade entry/import
real external account observation
broker account synchronization
brokerage cash/positions/orders/trades
real-account matching/discrepancy handling
real portfolio tracking
trade sizing from real brokerage holdings
real broker fees/taxes/settlement synchronization
broker-write adapters
place_order / cancel_order / modify_order
real-order API/UI
Live OMS/EMS
trade-password unlock
execution workers/retries/recovery/kill switches
autonomous/unattended trading
```

Unnecessary infrastructure remains excluded: microservices, Kafka, distributed workers, Kubernetes, multi-tenancy, 24/7 execution infrastructure, tick persistence, institutional OMS, and large generic provider frameworks.

## 10. Governance and stop conditions

- Phase 1 remains accepted and immutable as historical evidence.
- `TASK-006` is an umbrella identifier only; Codex must never be told to “implement TASK-006” as one task.
- TASK-006A through TASK-006E are planned identifiers, not implementation authority.
- Each implementation task requires an explicit user-approved Task Contract stored on its own task branch.
- Codex receives only a short prompt pointing to repository, task branch and Task Contract path.
- Codex stops after its approved task and pushes only that task branch.
- Independent GitHub review is required before remediation/integration.
- One task passing does not approve the next task.
- Documentation and requirements must preserve data freshness, no-lookahead, non-fabrication and read-only safety rules.
- Optional Phase 3/4 work stays dormant until explicitly reactivated.
