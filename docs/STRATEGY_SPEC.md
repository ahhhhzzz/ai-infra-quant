# PAQS / Composite Quant Strategy Research Specification

Status: **PROPOSED / RESEARCH_UNVALIDATED**; not approved for implementation except through explicit bounded Task Contracts

Future authority: `docs/ROADMAP.md` decisions `MTF-001` and `PAQS-MVP-001`

Current research definition:

```text
docs/research/PAQS_V0.3.1_COMPLETENESS_LOCK.md
docs/research/PAQS_V0.3.1_REVIEW_AMENDMENT_A.md
```

The PAQS research documents lock research semantics but are not implementation contracts. `PAQS_V0.3.1_REVIEW_AMENDMENT_A.md` governs where it is more specific than the base v0.3.1 document. Implementation authority is granted only by a user-approved bounded TASK-006A/006B/006C/006D/006E Task Contract.

## 1. Governance and supersession

Instruction precedence remains:

1. current explicit user instruction;
2. root `AGENTS.md`;
3. `docs/ROADMAP.md`;
4. `docs/MASTER_SPEC.md`;
5. the current explicitly approved Task Contract;
6. this research specification and documents under `docs/research/`.

The former completed-daily-only `AIInfraStrategy v1` formula proposal remains withdrawn as implementation authority.

`PAQS_V0.2_CORE_DEFINITION_LOCK.md` remains research history. The v0.3.1 Completeness Lock plus Review Amendment A record the current Price Action research direction.

`PAQS-MVP-001` additionally makes the PAQS decision-terminal the current product-completion line and defines the authoritative future task decomposition. The earlier four-item research staging list is superseded.

No rule, fixture, score or example in these research documents is a profitability or predictive-validity claim.

## 2. Product and safety boundary

PAQS is read-only decision support.

The initial PoC tracked set remains:

```text
US.AVGO
US.VRT
HK.09698
```

but future Phase 2 scope now plans dynamic supported US/HK securities under TASK-006A. PAQS must not hard-code strategy logic to those three symbols.

PAQS consumes provider-agnostic canonical market data and may eventually produce:

- market-structure state;
- Key Levels / Zones / Range;
- Price Action events;
- Setup and advisory states;
- structural invalidation / target / RR;
- explanation/reason codes;
- optional lightweight Quality/Composite Score and ranking;
- optional lightweight immutable advisory/signal history if explicitly approved.

It has no provider SDK object, brokerage-account fact, external order or execution capability. Whether the user trades in the broker official client is outside PAQS/application state.

Conditional language such as `EXIT_IF_HELD` never means the system knows a real position exists.

Missing/delayed/stale/unavailable/invalid/unsupported/incomplete inputs remain explicit. No market, corporate-action, risk, position or execution value is fabricated.

## 3. PAQS is primary; Score is derived

The historical/current score-level architecture remains recorded as:

```text
Composite Quant Score
    =
Daily Base Score
    +
Intraday Minute Adjustment
```

`PAQS-MVP-001` clarifies that this numerical decomposition is not the causal strategy engine.

The causal relationship is:

```text
Completed canonical market data
        ↓
PAQS input/session/timeframe foundation
        ↓
PAQS structure / event / setup state machine
        ↓
structural invalidation / target / RR hard gates
        ↓
Entry / Holder advisory
        ↓
optional derived Quality / Composite Score + Ranking
```

If a numerical score is retained by a later approved Task Contract:

```text
Daily Base Score
    = derived summary of completed higher/setup-timeframe structural context

Intraday Minute Adjustment
    = bounded derived summary of completed lower-timeframe trigger/follow-through/risk information
```

The score must never:

- fabricate an Event or Setup;
- override hard structural invalidation;
- bypass RR;
- convert unsupported/missing data to zero;
- convert `NO_TRADE` into `LONG_READY`;
- represent probability without a separately validated/calibrated probability model.

Exact numerical formulae remain unapproved.

## 4. Current PAQS research pipeline

```text
Completed Price Data
        ↓
PAQS Input Foundation
        ↓
ATR / Volatility Scale
        ↓
Pivot / Swing
        ↓
Key Level / Zone / Range
        ↓
Base Regime
        ↓
Price Action Events
        ↓
Regime Transition
        ↓
Trigger
        ↓
Follow-through
        ↓
Setup Qualification
        ↓
Structural Invalidation
        ↓
Structural Target
        ↓
RR / Entry Revalidation
        ↓
Entry / Holder Advisory
        ↓
Optional derived Quality / Ranking
```

Research semantics are detailed in the current v0.3.1 documents listed above.

## 5. Time, market-data and PAQS input semantics

Only completed source bars may enter confirmed PAQS calculations. An unfinished minute bar is excluded. A latest/intraday price is never a final Daily close.

All instants are aware UTC; market sessions use canonical IANA timezones. Financial calculations use Decimal.

Point-in-time semantics require:

```text
feature[t] = f(data <= t)
```

and future corporate-action information must not be injected into a historical state.

The current initial equity timeframe direction is:

```text
HTF = completed W1
STF = completed D1
TTF = completed 30m REGULAR-session bars
```

TASK-006A implements only the provider-agnostic input foundation required to construct/validate
those timeframes and supported dynamic US/HK equities. It does not implement ATR/Pivot/structure
semantics.

US extended-session minute data remains valid market data but is not part of the initial structural 30m TTF engine. H1/H4 are not current MVP requirements.

W1 finalization follows PAQS v0.3.1 Review Amendment A.

Current provider QFQ data must not automatically be treated as strict real-market point-in-time-safe historical replay. Broad historical real-market PAQS backtesting is not current MVP work.

## 6. Missing-data and data-quality behavior

Future implementations must expose relevant component coverage/timestamps and distinguish truthful states such as:

```text
AVAILABLE
MISSING
DELAYED
STALE
UNAVAILABLE
INVALID
UNSUPPORTED
```

They must never silently:

- substitute zero for a missing component;
- reuse an unfinished minute bar;
- invent a Key Level or price;
- mix inconsistent adjustment bases;
- treat corporate-action discontinuity as genuine Price Action;
- infer unknowable intrabar event order from OHLC.

Dashboard recalculation cadence does not authorize background processing after page close.

## 7. PAQS v0.3.1 research locks

The v0.3.1 research definition locks, at research level:

1. two-stage Entry/RR timing and next-open revalidation;
2. separate Entry Advisory and conditional Holder Advisory states;
3. setup-specific snapshotted structural invalidation using explicit close/ATR-buffer inequalities;
4. nearest-obstacle T1 and no-target-shopping;
5. initial `W1 -> D1 -> 30m regular-session` hierarchy plus deterministic W1 finalization;
6. `REGULAR_SESSION_OPEN_GAP` semantics;
7. point-in-time corporate-action basis requirement;
8. PAQS state/hard-gate engine as primary with Score as a derived layer.

These research locks do not authorize one large implementation task.

## 8. Authoritative TASK-006 decomposition

`TASK-006` is an umbrella workstream only and must never be given to Codex as one implementation request.

### TASK-006A — Dynamic US/HK Securities & PAQS Input Foundation

Planned boundary:

- dynamic supported US/HK security/watchlist workflow;
- provider support validation without account access;
- provider-neutral calendar/session metadata;
- completed W1 derivation from D1;
- completed regular-session 30m derivation from completed 1m;
- coverage/data-quality/adjustment metadata;
- PAQS user/engineering documentation foundations.

Not allowed in 006A:

```text
ATR
Pivot
Swing
Key Level / Zone / Range
Base Regime
Event
Setup
Advisory
Score
```

### TASK-006B — PAQS Structure Engine

Planned boundary:

- ATR;
- confirmed Micro/Major Pivot;
- Swing labels;
- Key Level geometry;
- Pivot Zones;
- Range detection;
- Base Regime;
- deterministic/no-lookahead fixtures/debug output.

Mandatory real read-only structure-review checkpoint before TASK-006C approval.

### TASK-006C — PAQS Event Engine

Planned boundary:

- Break Attempt / Breakout / Breakdown;
- Failed Breakout / Failed Breakdown;
- Retest lifecycle;
- Key Level role flip;
- Regime Transition;
- Trigger;
- Follow-through.

No Entry/Hold/Exit advisory.

### TASK-006D — PAQS Setup & Risk Engine

Planned boundary:

- approved setup families;
- Setup expiry;
- setup-specific invalidation;
- T1/T2 selection;
- no-target-shopping;
- RR hard gate;
- next-open entry revalidation;
- only explicitly approved Entry Advisory states.

### TASK-006E — PAQS Advisory & Decision Dashboard

Planned boundary:

- conditional Holder Advisory;
- explanations/reason codes;
- Dashboard PAQS integration;
- optional lightweight Quality/Ranking if explicitly approved;
- optional lightweight immutable advisory/signal history if explicitly approved;
- user-facing decision-terminal completion.

Each Task Contract must explicitly state parameters, domain/API/UI/persistence effects, tests, documentation and stop conditions for that task only.

## 9. Decisions still required before individual implementation tasks

A bounded Task Contract must resolve only the decisions needed by its own scope.

Examples include:

- TASK-006A: supported-security validation/user flow, calendar/session contract, coverage, adjustment metadata and documentation contract;
- TASK-006B: Decimal/rounding, ATR warm-up, Pivot initialization, deterministic Key Level/Zone/Range behavior and structure fixtures;
- TASK-006C: exact Event/Transition/Trigger/Follow-through parameters adopted;
- TASK-006D: setup variants, invalidation/target/RR/entry-revalidation parameters and advisory transitions;
- TASK-006E: holder-state presentation, reason codes, Quality/Ranking formula if included, advisory-history persistence if included.

No default in an older proposal silently resolves these task-level choices.

## 10. Validation requirements

Proportional future tests must prove only the behavior authorized by the current task, with emphasis on:

- no-lookahead / future-record injection resistance;
- deterministic Decimal arithmetic where applicable;
- US/HK session/calendar correctness;
- completed-bar-only semantics;
- explicit missing/unsupported states;
- provider-agnostic core boundaries;
- no brokerage-account/execution dependency;
- no profitability claim from passing tests or smoke evidence.

Synthetic golden fixtures must be clearly labelled and not presented as real market observations.

## 11. Optional future research boundary

Paper Portfolio, PaperFill/accounting, position sizing, broad portfolio analytics and full backtesting are no longer current committed PAQS MVP work under `PAQS-MVP-001`.

They remain dormant optional Phase 3/4 extension paths and may be reactivated later without changing the read-only/no-broker boundary or making PAQS depend on them.

## 12. Current implementation statement

Phase 2 market-data/Dashboard work has progressed through TASK-003/TASK-004/TASK-005/TASK-005A/TASK-005B.

TASK-006A implements dynamic market-data Security expansion and PAQS W1/D1/M30 calendar/input
preparation only. No PAQS Structure/Event/Setup/Risk/Advisory engine, numerical Quality/Ranking,
or optional Phase 3/4 capability is implemented. TASK-006B remains separately gated.
