# AI Infra Quant Platform — Master Specification v3.1

Status: **AUTHORITATIVE — read-only PAQS decision-terminal direction**

Superseding future-scope decisions:

- `MTF-001` in `docs/ROADMAP.md`, approved 2026-09-01;
- `PAQS-MVP-001` in `docs/ROADMAP.md`, approved 2026-09-02.

Decision record: `docs/decisions/PAQS_MVP_SCOPE_REDUCTION.md`

## 0. Authority, precedence, and history

Instruction precedence is:

1. current explicit user instruction;
2. root `AGENTS.md`;
3. `docs/ROADMAP.md`;
4. this specification;
5. the current explicitly approved Task Contract;
6. other documentation.

Phase 0 remains historically completed. Phase 1 remains accepted at reviewed commit `f6decf2fbe171c1b9eb46340a9174bc21f293ede`; its PASS status, plan, implementation, tests and two review files remain unchanged.

Completed Phase 2 increments include TASK-003, TASK-004, TASK-005, TASK-005A and TASK-005B. `PAQS-MVP-001` changes only future committed scope and does not rewrite those accepted increments.

## 1. Product objective and boundary

Build a local-first, single-user personal quantitative research and decision-support terminal.

The committed MVP should let the user:

- maintain supported US/HK securities in a local watchlist;
- inspect truthful latest/Daily/recent-minute market data;
- receive deterministic PAQS market-structure interpretation;
- receive PAQS event/setup/risk-reward interpretation;
- receive conditional Entry and Holder advisory;
- compare supported opportunities using lightweight explainable Quality/Ranking if separately approved.

All real trading is performed manually in the broker's official client.

The product never accesses a brokerage account, real cash, real positions, completed broker orders or real trades. It does not import or match real-account state and does not need to know whether the user acted on an advisory output.

> 用户在券商官方客户端手工完成所有真实交易。

The original PoC tracked set begins with:

- `US.AVGO`
- `US.VRT`
- `HK.09698`

The committed MVP now plans dynamic supported US/HK security management under TASK-006A rather than permanently restricting market data/PAQS to those three symbols.

## 2. Operating model

During an active visible Dashboard session the application may:

1. obtain/refresh current market state from the independent read-only Market Data Provider;
2. obtain bounded completed Daily and recent completed 1-minute history;
3. validate provenance, timestamps, completeness, session/calendar semantics and data quality;
4. derive current PAQS input timeframes when implemented;
5. calculate the approved PAQS subset for the current task;
6. render market data and later PAQS interpretation/advisory;
7. repeat appropriate current calculations approximately every 60 seconds or on manual refresh;
8. stop automatic page activity when hidden/closed according to the existing Dashboard contract.

Ordinary HTTP/REST polling remains sufficient for the local MVP. WebSocket/streaming infrastructure is not required.

## 3. Scope and non-goals

### Current committed MVP scope

- local single-process modular monolith;
- SQLite runtime and FastAPI/local frontend;
- independent read-only market-data provider path;
- bounded Daily history and recent completed 1-minute OHLCV;
- latest price and market status;
- separate Daily/minute charts and volume;
- dynamic supported US/HK watchlist planned under TASK-006A;
- PAQS input/session/calendar foundation;
- PAQS structure, events, setups, invalidation, targets and RR through bounded TASK-006 work;
- conditional Entry/Holder advisory;
- lightweight explanation/reason codes;
- optional lightweight Quality/Ranking and signal/advisory history when explicitly approved;
- user/engineering documentation for PAQS.

### Optional future extensions, not committed MVP work

These may be reactivated only through later explicit Phase 3/4 approval:

- simulated Paper Portfolio / PaperFill bookkeeping;
- paper NAV/performance;
- position sizing;
- portfolio exposure/correlation controls;
- broader research-factor expansion;
- full deterministic backtesting platform;
- transaction-cost/benchmark engines;
- attribution/exposure/turnover analytics;
- portfolio optimization;
- large parameter-analysis/reporting suites.

No placeholder implementation is required merely to anticipate them.

### Permanently outside product scope

- any brokerage-account connection or observation;
- real cash/positions/trades/import/synchronization/account matching;
- application-submitted real orders or real-order UI/API;
- broker-write adapters or `place_order`, `cancel_order`, `modify_order`;
- trading-password unlock, buying-power reservation, execution workers/retries/recovery/kill switches;
- live OMS/EMS or autonomous/unattended trading;
- microservices, Kafka/queues, distributed workers, Kubernetes, multi-tenancy, cloud HA or 24/7 execution infrastructure;
- tick/order-book persistence as an MVP requirement;
- any authoritative Phase after Phase 4.

Read-only market analysis and conditional advisory are research capabilities, not execution.

## 4. Engineering principles

1. PAQS/Strategy and other core research logic remain provider-agnostic.
2. Provider-specific adapters live under `integrations/` and expose read-only capabilities only.
3. Financial values use Python `Decimal`, never binary float.
4. SQLite persists exact financial values under the accepted Decimal design when persistence is required.
5. Missing, delayed, stale, unavailable, unsupported and erroneous data are explicit and never fabricated.
6. Instants are aware UTC; market sessions retain local date, IANA timezone and calendar semantics.
7. Point-in-time research requires data legitimately available at the calculation cutoff.
8. PAQS must never use unfinished bars as completed facts.
9. Advisory output has no external effect and creates no real-position fact.
10. Every implementation task is separately approved, tested, reviewed and stopped.
11. Product-scope reduction must not justify coupling PAQS to one provider or hard-coded symbol set.

## 5. Target architecture

```text
Browser
  -> local FastAPI presentation
      -> application use cases
          -> market-data queries
          -> supported-security/watchlist administration
          -> PAQS input/session/calendar preparation
          -> PAQS structure/events/setups/risk/advisory
          -> optional lightweight quality/ranking/history
              -> SQLite only where approved persistence exists

Independent read-only Market Data Provider
  -> provider adapter under integrations/
      -> canonical quotes, Daily bars, completed minute bars,
         market status and approved calendar/security metadata

Human boundary
  advisory display -> user -> broker official client
```

There is no brokerage-account path and no path from an advisory result to an external command.

## 6. Module boundaries

| Module/port | Owns | Must not own or call |
|---|---|---|
| Dashboard | Market views, watchlist UI, polling, later PAQS presentation | Provider SDK objects, real account/execution concepts |
| Market-data port | Canonical quote, Daily/minute bars, market status and approved calendar/security metadata | Brokerage account access or execution |
| PAQS input foundation | W1/D1/30m derivation, session/calendar/coverage/adjustment metadata | Provider SDK models, broker/account state |
| PAQS Strategy | Structure, events, setups, invalidation/target/RR, advisory as approved by bounded tasks | Provider SDKs, broker commands, accounting mutation |
| Quality/Ranking | Optional derived prioritization of already-defined PAQS state | Creating setups, bypassing PAQS hard gates |
| Portfolio/Accounting | Accepted Phase 1 historical foundation; optional later paper work only if reactivated | Real-account state, PAQS score mutation |
| Performance/Backtest | Dormant optional future extensions only if reactivated | Production mutation, fabricated historical data |

Only the composition root selects a provider. Core modules do not read environment variables, import provider SDKs or branch on provider names.

## 7. Market-data, time and PAQS input contract

The existing provider boundary supports equivalents of `get_latest_quote()`, `get_daily_bars()`, `get_minute_bars()` and `get_market_status()` through TASK-004/TASK-005B.

TASK-006A is planned to extend the provider-neutral boundary only as needed for supported dynamic US/HK securities and trading-calendar/session metadata. This does not authorize account access.

Current Dashboard behavior retains:

- up to 1500 requested completed Daily sessions, with 1300 used by full load;
- recent 30 market-local calendar days of completed minute data;
- Futu `Session.ALL` for US minute retrieval;
- normal HK provider sessions;
- separate Daily and 1-minute charts;
- market-local labels using IANA timezones.

Initial PAQS timeframe direction:

```text
HTF = completed W1
STF = completed D1
TTF = completed 30m REGULAR-session bars
```

W1 is derived from completed D1. 30m is derived from completed 1-minute bars with market-aware US/HK session rules. H1/H4 are not current MVP requirements.

Canonical state must preserve truthful timestamps and coverage. A latest/intraday price is never a final Daily close. Provider latency and page polling cadence remain distinct facts.

Provider current-QFQ data must not automatically be described as strict point-in-time-safe historical replay data. Strict historical real-market PAQS backtesting is not part of the current MVP.

## 8. PAQS / Score governance

The earlier approved score-level decomposition remains:

```text
Composite Quant Score = Daily Base Score + Intraday Minute Adjustment
```

`PAQS-MVP-001` clarifies the causal relationship:

```text
completed canonical inputs
        ↓
PAQS state machine / hard gates
        ↓
Entry / Holder advisory
        ↓
optional derived Quality / Composite Score + Ranking
```

The numerical layer may summarize or rank PAQS results but may not:

- fabricate Events/Setups;
- override structural invalidation;
- bypass RR;
- substitute missing components with zero;
- turn `NO_TRADE` into `LONG_READY`;
- represent probability without a separately approved calibrated model.

Exact numerical formulae, weights, scale, bands and ranking behavior remain unapproved until a specific Task Contract authorizes them.

## 9. Dashboard product contract

The current Dashboard retains its completed market-data functionality. Future TASK-006E may add:

- PAQS context/structure/setup presentation;
- Entry Advisory;
- conditional Holder Advisory;
- structural invalidation/target/RR;
- reason codes/explanations;
- lightweight Quality/Ranking if approved;
- lightweight advisory history if approved.

The Dashboard contains no real-order control and never claims that the user executed an advisory.

## 10. Validation and backtesting boundary

Current PAQS work prioritizes deterministic semantics, synthetic golden fixtures, no-lookahead tests and current read-only smoke evidence.

A broad real-market historical backtesting platform is not a current committed MVP requirement.

If Phase 4 is explicitly reactivated later, it must use legitimate point-in-time data and separately approved assumptions. Current recent-minute display does not imply historical minute replay/tick simulation.

## 11. Infrastructure and secrets

Sufficient topology remains:

```text
Browser -> 127.0.0.1 FastAPI -> SQLite
                            -> independent read-only Market Data Provider
```

PostgreSQL compatibility remains portability, not a deployment requirement.

Never commit credentials, external/private account IDs, passwords, tokens, databases, logs or private broker exports.

## 12. Authoritative phases and TASK-006 map

The authoritative sequence remains exactly Phase 0 through Phase 4:

- Phase 0 — Product Definition & Architecture (historically completed);
- Phase 1 — Foundation (accepted historical implementation);
- Phase 2 — Market Data, Dashboard & PAQS Decision Terminal MVP (active committed phase);
- Phase 3 — dormant optional research/paper extensions;
- Phase 4 — dormant optional validation/backtest/analytics extensions; final possible phase.

Current Phase 2 completed increments:

```text
TASK-003
TASK-004
TASK-005
TASK-005A
TASK-005B
```

`TASK-006` is an umbrella workstream, not an implementation task.

Planned bounded task identifiers:

```text
TASK-006A — Dynamic US/HK Securities & PAQS Input Foundation
TASK-006B — PAQS Structure Engine
TASK-006C — PAQS Event Engine
TASK-006D — PAQS Setup & Risk Engine
TASK-006E — PAQS Advisory & Decision Dashboard
```

Each requires its own explicit user-approved Task Contract. The current product may be considered functionally complete when TASK-006E passes independent review/integration. Phase 3/4 remain dormant until explicitly reactivated.

## 13. Quality and change control

For each approved implementation task: read governing docs; preserve unrelated changes; state the exact file set; implement only approved scope; run proportional validation; verify provenance/freshness/Decimal/UTC/no-lookahead/safety boundaries; update required documentation; report exact evidence; and stop.

Codex must never be instructed to implement umbrella TASK-006 in one pass.

Documentation requirements become part of PAQS Definition of Done. TASK-006A establishes user and engineering guide foundations, and later PAQS tasks must update them when behavior changes.

## 14. Accepted Phase 1 boundary

Phase 1 remains the reviewed foundation: packaging/configuration/logging; deterministic migration 0001; exact Decimal and UTC invariants; canonical Security identity; Watchlist; opening HKD 20,000, 200 units and NAV 100 facts; accepted read APIs/frontend; inert capability descriptors; tests and reviews.

`PAQS-MVP-001` changes none of that implementation or evidence.
