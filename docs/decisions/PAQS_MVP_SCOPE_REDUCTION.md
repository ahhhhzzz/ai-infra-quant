# PAQS MVP Scope Reduction Decision

Decision: `PAQS-MVP-001`

Status: **AUTHORITATIVE FUTURE-SCOPE DECISION**

Approved: 2026-09-02

Applies to: future work after accepted Phase 1 and the completed Phase 2 market-data/Dashboard increments through TASK-005B.

## 1. Decision summary

The product completion line is reduced to a focused personal investment decision terminal rather than a broad quantitative platform.

The current committed MVP objective is:

```text
Dynamic US/HK watchlist
        ↓
Read-only market data / Dashboard
        ↓
PAQS market structure
        ↓
PAQS price-action events
        ↓
PAQS setups + structural invalidation/target/RR
        ↓
Entry / Holder advisory
        ↓
Lightweight Quality/Ranking + signal/advisory history
```

The main product may be considered functionally complete after the approved Phase 2 PAQS workstream reaches TASK-006E and passes independent review.

This decision does not create implementation authority for any TASK-006 subtask. Each subtask still requires an explicit Task Contract and user approval.

## 2. TASK-006 is an umbrella workstream

`TASK-006` is not itself a Codex implementation task. It is the umbrella for five bounded Phase 2 tasks:

### TASK-006A — Dynamic US/HK Securities & PAQS Input Foundation

Planned responsibility:

- remove the three-symbol market-data PoC limitation for supported US/HK equities;
- allow the local user to add/remove supported US/HK securities from the watchlist through the product UI;
- validate provider support without brokerage-account access;
- preserve canonical Security UUID identity;
- introduce provider-agnostic trading-calendar/session semantics required by PAQS;
- derive completed W1 from D1 and completed regular-session 30m bars from completed 1m;
- expose truthful coverage/data-quality/adjustment-basis metadata;
- create/update PAQS user and engineering documentation foundations.

Explicitly not included: ATR, Pivot, Zone, Range, Regime, Event, Setup, Advisory, Score.

### TASK-006B — PAQS Structure Engine

Planned responsibility:

- ATR;
- confirmed directional-change Micro/Major Pivot;
- Swing labels;
- Key Level geometry;
- Pivot Zones;
- Range detection;
- Base Regime;
- deterministic/no-lookahead structure debug output and fixtures.

Mandatory checkpoint after completion: manually review real read-only AVGO/VRT/HK.09698 plus at least one dynamically added supported security before authorizing TASK-006C.

### TASK-006C — PAQS Event Engine

Planned responsibility:

- Break Attempt / Breakout / Breakdown;
- Failed Breakout / Failed Breakdown;
- Retest lifecycle;
- Key Level role-flip lifecycle;
- Regime Transition;
- Micro Structure Break / Signal-Bar Trigger;
- Follow-through lifecycle.

No Entry/Hold/Exit advisory is produced by this task.

### TASK-006D — PAQS Setup & Risk Engine

Planned responsibility:

- Trend Pullback;
- Range Failed Breakdown;
- Right-Side Breakout setup families;
- Setup expiry;
- setup-specific structural invalidation;
- structural T1/T2 selection;
- no-target-shopping rule;
- RR hard gate;
- next-open entry revalidation;
- `WATCH_LONG`, `LONG_READY`, `WAIT_RETEST`, `NO_TRADE`-class entry advisory states as explicitly approved by its Task Contract.

### TASK-006E — PAQS Advisory & Decision Dashboard

Planned responsibility:

- conditional Holder Advisory such as thesis-valid/warning/target-review/exit-if-held;
- reason codes and explanations;
- Dashboard integration for PAQS context/setup/advisory/invalidation/target/RR;
- lightweight PAQS Quality/Ranking layer only after structural hard gates;
- lightweight immutable signal/advisory history if approved in the Task Contract;
- complete the PAQS user-facing decision-terminal experience.

A Quality/Composite Score may rank or summarize already-defined PAQS states; it may never create a setup, bypass RR, or override hard invalidation.

## 3. Initial PAQS timeframe direction

The initial equity research mapping remains:

```text
HTF = completed W1
STF = completed D1
TTF = completed 30m REGULAR-session bars
```

H1/H4 are not required for the current MVP and must not be introduced unless separately approved.

## 4. Current MVP KEEP / SIMPLIFY / OPTIONAL / REMOVED

### KEEP — committed MVP

- local-first single-user modular monolith;
- existing read-only Futu quote-market-data path;
- existing latest/Daily/1-minute Dashboard;
- Windows one-click launcher;
- dynamic supported US/HK watchlist;
- PAQS structure/events/setups/risk-reward/advisory;
- lightweight explainability;
- lightweight Quality/Ranking if separately approved;
- lightweight signal/advisory history if separately approved;
- user and engineering documentation.

### SIMPLIFY

- `Composite Quant Score` is no longer the causal strategy engine; PAQS is primary and numerical Quality/Composite Score is a derived presentation/ranking layer if retained;
- ranking is lightweight and advisory-oriented rather than a generic portfolio optimizer;
- research validation is proportional to PAQS semantics and synthetic golden fixtures rather than an institutional research platform.

### OPTIONAL FUTURE EXTENSIONS — not committed MVP work

The following are removed from the current committed development sequence but remain architecturally reconnectable under Phase 3 or Phase 4 if the user explicitly reactivates them:

- simulated Paper Portfolio;
- PaperFill bookkeeping/accounting;
- paper NAV/performance;
- position sizing;
- portfolio exposure/correlation controls;
- broad factor-research expansion;
- full deterministic backtesting platform;
- transaction-cost/benchmark engines;
- turnover/attribution/exposure analytics;
- portfolio optimization;
- large parameter-analysis/reporting suites.

No placeholder implementation is required for these optional extensions.

### PERMANENTLY REMOVED / FORBIDDEN

Existing `MTF-001` prohibitions remain unchanged:

- brokerage-account connection/observation;
- real cash/positions/orders/trades/import/matching;
- real-order API/UI or broker-write adapter;
- `place_order`, `cancel_order`, `modify_order`, trade-password unlock;
- live OMS/EMS or autonomous/unattended trading;
- microservices/Kafka/distributed execution infrastructure;
- any authoritative Phase after Phase 4.

## 5. Phase model after this decision

The authoritative phase sequence remains exactly Phase 0 through Phase 4.

- Phase 0 — historical Product Definition & Architecture.
- Phase 1 — accepted Foundation.
- Phase 2 — active Market Data, Dashboard and PAQS Decision Terminal MVP. The current committed product-completion line ends here after TASK-006E passes review.
- Phase 3 — dormant optional research/paper extensions. No Phase 3 implementation begins unless explicitly reactivated by the user.
- Phase 4 — dormant optional validation/backtest/analytics extensions; final possible phase. No Phase 4 implementation begins unless explicitly reactivated by the user.

Thus Phase 3 and Phase 4 remain valid architectural extension slots without being mandatory to call the current product complete.

## 6. Extensibility rule

Scope reduction must not justify coupling PAQS to Futu SDK objects, hard-coding one watchlist, or collapsing module boundaries.

Future optional modules must be able to consume stable provider-agnostic PAQS/advisory facts without rewriting the core strategy. No implementation is required today merely to anticipate every future extension.

## 7. Governance

- `docs/ROADMAP.md` incorporates this decision and is the primary future-scope authority.
- `docs/MASTER_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/REQUIREMENTS_MATRIX.md`, and `docs/STRATEGY_SPEC.md` must remain consistent with this decision.
- TASK-006A through TASK-006E are planned identifiers only until their individual Task Contracts are explicitly approved.
- Every task stops after its own independent review/integration; approval of one does not approve the next.
- Phase 1 plan, migration, and review evidence remain immutable.

**End — PAQS-MVP-001**
