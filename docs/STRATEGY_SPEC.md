# PAQS / Composite Quant Strategy Research Specification

Status: **PROPOSED / RESEARCH_UNVALIDATED**; not approved for implementation

Future authority: `docs/ROADMAP.md` decision `MTF-001`

Current research definition:

```text
docs/research/PAQS_V0.3.1_COMPLETENESS_LOCK.md
```

The PAQS research document is a design lock for research semantics, **not** an implementation contract. A later explicitly approved Task Contract must adopt a bounded subset before code is written.

## 1. Governance and supersession

Instruction precedence remains:

1. current explicit user instruction;
2. root `AGENTS.md`;
3. `docs/ROADMAP.md`;
4. `docs/MASTER_SPEC.md`;
5. the current explicitly approved Task Contract;
6. this research specification and documents under `docs/research/`.

The former completed-daily-only `AIInfraStrategy v1` formula proposal—including its weights, thresholds, bands, gates, state machine, sizing candidates, and golden cases—is withdrawn as implementation authority. It may be recovered from Git history for research context but must not be implemented as the current strategy.

`PAQS_V0.2_CORE_DEFINITION_LOCK.md` remains research history. `PAQS_V0.3.1_COMPLETENESS_LOCK.md` records the current Price Action research direction and closes identified semantic gaps, but it does not by itself authorize implementation.

No rule, fixture, score, or example in these research documents is a profitability or predictive-validity claim.

## 2. Product and safety boundary

The strategy is read-only decision support for the configurable tracked set beginning with:

```text
US.AVGO
US.VRT
HK.09698
```

It consumes provider-agnostic canonical market data and may produce:

- market-structure state;
- Key Levels / Zones / Range;
- Price Action events;
- Setup and advisory states;
- structural invalidation / target / RR;
- explanation and reason codes;
- optional later Quality / Composite Score and tracked-security ranking.

It has no provider SDK object, brokerage-account fact, external order, or execution capability. Whether the user trades in the broker's official client is outside strategy/application state.

The strategy may say conditionally:

```text
EXIT_IF_HELD
```

but this does not mean the application knows a real position exists and does not submit any broker command.

Missing, delayed, stale, unavailable, invalid, unsupported-adjustment, or incomplete inputs remain explicit. No market, valuation, corporate-action, fundamental, risk, position, or execution value is fabricated.

## 3. Approved high-level score architecture and PAQS research relationship

The currently approved high-level architecture remains:

```text
Composite Quant Score
    =
Daily Base Score
    +
Intraday Minute Adjustment
```

Only this decomposition is authoritative at the score level. Exact numerical formulae remain unapproved.

The PAQS v0.3.1 research direction does **not** treat that numerical score as the causal strategy engine. The proposed relationship is:

```text
Completed canonical market data
        ↓
PAQS structural / event / setup state machine
        ↓
Entry / Holder advisory + hard gates
        ↓
Optional derived Quality / Composite Score
```

If Composite Score is retained by a future approved Task Contract, its PAQS-compatible interpretation is:

```text
Daily Base Score
    = derived summary of completed higher/setup-timeframe structural context

Intraday Minute Adjustment
    = bounded derived summary of completed lower-timeframe trigger / follow-through / risk information
```

The score must never:

- fabricate an Event or Setup;
- override structural invalidation;
- bypass RR;
- convert an unsupported/missing state to zero;
- convert `NO_TRADE` into `LONG_READY`;
- represent a probability without a separately calibrated probability model.

## 4. Current PAQS research pipeline

The current design sequence is:

```text
Completed Price Data
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
Advisory State
        ↓
Optional derived Score / Ranking
```

Research semantics are detailed in `docs/research/PAQS_V0.3.1_COMPLETENESS_LOCK.md`.

## 5. Time, market data and point-in-time semantics

Strategy input/output must distinguish appropriate observation and calculation timestamps, including the existing canonical fields:

```text
latest_quote_at
latest_completed_minute_bar_at
latest_completed_daily_session
score_calculated_at
```

PAQS additionally requires event/setup/advisory `as_of_timestamp` and confirmation timestamps.

Only completed source bars may enter PAQS structure calculations. An unfinished minute bar is excluded. A latest/intraday price is never described as a final daily close. Provider latency remains independent from the approximately 60-second Dashboard polling cadence.

All instants are aware UTC; market sessions use their canonical IANA market timezone. Decimal remains required for financial calculations.

Point-in-time research must satisfy:

```text
feature[t] = f(data <= t)
```

and must not inject future corporate-action information into a historical calculation.

The current PAQS research mapping for the initial US/HK equity set is:

```text
HTF = completed W1
STF = completed D1
TTF = completed 30m REGULAR-session bars
```

where 30m bars are derived only from legitimately completed 1-minute market data. US extended-session data remains valid market-data context but is not part of the initial structural TTF engine.

## 6. Missing-data and data-quality behavior

Future implementation must expose component coverage and timestamps and distinguish at minimum:

```text
AVAILABLE
MISSING
DELAYED
STALE
UNAVAILABLE
INVALID
UNSUPPORTED
```

It must never silently:

- substitute zero for a missing strategy component;
- reuse an unfinished minute bar;
- invent a missing Key Level or price;
- mix inconsistent price-adjustment bases;
- treat a corporate-action discontinuity as genuine Price Action;
- infer intrabar event ordering from OHLC when the ordering is unknowable.

During an active visible Dashboard session, a future approved strategy may recalculate on manual refresh and approximately every 60 seconds. This cadence does not authorize background processing after the page closes.

## 7. PAQS v0.3.1 research locks

`PAQS_V0.3.1_COMPLETENESS_LOCK.md` now defines research semantics for the previously open P0 gaps:

1. two-stage Entry / RR timing and next-open revalidation;
2. separate Entry Advisory and conditional Holder Advisory states;
3. setup-specific snapshotted structural invalidation;
4. nearest-obstacle structural T1 selection and target-shopping prohibition;
5. initial US/HK `W1 -> D1 -> 30m regular-session` aggregation contract;
6. `REGULAR_SESSION_OPEN_GAP` semantics;
7. explicit `POINT_IN_TIME_ADJUSTED` corporate-action basis requirement;
8. PAQS state machine as primary decision logic with Score as a derived layer.

These are **research locks**, not permission to implement them. A Task Contract must explicitly select scope, parameters, models, tests and migration/API/UI effects before any code work.

## 8. Decisions still required before implementation

A later approved strategy Task Contract must still define its exact bounded implementation scope, including:

1. which PAQS modules are included in that task;
2. exact Parameter Registry defaults/ranges adopted by the task;
3. Decimal context and rounding where boundary comparisons require it;
4. deterministic initialization/warm-up rules for ATR and Pivot engines;
5. exact Key Level merge/expiry/version behavior included in scope;
6. missing/stale/unsupported thresholds and result states;
7. exact point-in-time corporate-action source/data plumbing;
8. API/domain persistence/explanation contracts if introduced;
9. synthetic golden fixtures and anti-look-ahead tests;
10. any Quality / Composite Score formula, normalization, scale, bands and ranking behavior if score work is included;
11. any exit variant, simulated-paper interpretation, sizing, trailing stop or position-management behavior if included.

No default in an older strategy proposal silently resolves these decisions.

## 9. Validation requirements for future approved PAQS work

At minimum, proportional future tests must prove the rules actually included in an approved task, with particular attention to:

- point-in-time Pivot confirmation and future-record injection resistance;
- deterministic Key Level / Zone / Range geometry;
- Base Regime vs Transition separation;
- completed-bar-only Trigger / Follow-through behavior;
- Event != Setup != Advisory;
- next-open Entry/RR revalidation without lookahead;
- setup-specific invalidation immutability;
- nearest-target / no-target-shopping behavior;
- US/HK session/calendar and 30m aggregation correctness;
- corporate-action adjustment-basis consistency;
- explicit missing/delayed/stale/unsupported states;
- no provider-native, brokerage-account, or execution dependency;
- no profitability claim from passing tests or backtests.

Synthetic fixtures must be clearly labelled and must not be presented as real market data.

## 10. Research staging; not approved tasks

A candidate decomposition for later discussion is:

```text
TASK-006A — PAQS Structure Foundation
TASK-006B — PAQS Event Engine
TASK-006C — PAQS Setup & Risk Geometry
TASK-006D — PAQS Advisory / Presentation Layer
```

This list is research staging only. It creates no branch, Task Contract or implementation authority by itself.

## 11. Current implementation statement

Phase 2 market-data and Dashboard work has already progressed through the approved TASK-003 / TASK-004 / TASK-005 / TASK-005A / TASK-005B increments described by the authoritative Roadmap and related documents.

No PAQS Pivot/Key-Level/Regime/Event/Setup/Invalidation/Target/RR/Advisory engine is implemented by this documentation work. No concrete Composite Quant Score formula, ranking formula, or PAQS Quality Score is approved or implemented here.

The next strategy implementation task remains blocked on an explicit user-approved Task Contract.
