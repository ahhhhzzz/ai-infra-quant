# AI Infra Quant Platform — Master Specification v3.0

Status: **AUTHORITATIVE — daily + 1-minute read-only direction**

Superseding decision: `MTF-001` in `docs/ROADMAP.md`, approved 2026-09-01

## 0. Authority, precedence, and history

Instruction precedence is:

1. current explicit user instruction;
2. root `AGENTS.md`;
3. `docs/ROADMAP.md`;
4. this specification;
5. the current explicitly approved phase plan or Task Contract;
6. other documentation.

Decision `MTF-001` supersedes `EOD-001` for future scope without reverting its traceable commit or
rewriting history. Phase 0 remains historically completed. Phase 1 remains accepted at reviewed
commit `f6decf2fbe171c1b9eb46340a9174bc21f293ede`; its PASS status, implementation, plan, tests, and two
review files are unchanged. TASK-003 established the bounded Phase 2 quote-only provider PoC;
TASK-004 adds its provider-neutral read-through backend; TASK-005 adds only the read-only local
Dashboard that consumes it.

## 1. Product objective and boundary

Build a local-first, single-user quantitative research and decision-support tool. The product uses
daily data and a bounded recent window of completed 1-minute bars, presents a visible read-only dashboard, and
refreshes/recalculates approximately every 60 seconds while that dashboard is visible.

Initial tracked securities remain configurable:

- `US.AVGO`
- `US.VRT`
- `HK.09698`

Accepted opening Phase 1 facts remain configurable: HKD base currency, initial capital 20000,
inception date 2026-08-31, initial NAV 100, and 200 units.

The product may read market information from an independent Market Data Provider. It never accesses
a brokerage account, real cash, real positions, completed broker orders, or real trades. It neither
imports real trades nor matches real-account state. It does not need to know whether the user
acted on an advisory output.

> 用户在券商官方客户端手工完成所有真实交易。

## 2. Operating model

During an active visible dashboard session:

1. obtain or refresh latest market state from an independent read-only provider;
2. obtain paged Daily history and incremental completed 1-minute bars;
3. validate provenance, timestamps, latency, completeness, and quality;
4. calculate indicators and the approved Composite Quant Score model when one exists;
5. rank tracked securities and calculate reference/risk state;
6. render separate daily and 1-minute chart views;
7. repeat approximately every 60 seconds, or refresh on manual request;
8. stop automatic activity when the page is hidden or closed.

When a hidden page becomes visible it refreshes immediately. Polling requests never overlap. The
UI provides `刷新最新行情` and an automatic-refresh countdown. Ordinary HTTP/REST polling is the
MVP transport; WebSocket or streaming infrastructure is not required.

## 3. Scope and permanent non-goals

In scope:

- local, single-process modular monolith;
- bounded Daily history and recent 30-calendar-day completed 1-minute OHLCV;
- latest price and market status;
- separate daily/minute candlestick charts and volume;
- indicators, score, ranking, and reference/risk state;
- later-approved lightweight simulated/paper research state;
- deterministic backtesting and analytics;
- SQLite runtime and FastAPI/local frontend.

Permanently outside product scope:

- any brokerage-account connection or observation;
- real cash, positions, trades, imports, synchronization, or account matching;
- application-submitted real orders or real-order UI/API;
- broker-write adapters or `place_order`, `cancel_order`, `modify_order` calls;
- live OMS/EMS, buying-power reservation, password unlock, execution workers, retries, recovery,
  kill switches, or autonomous/unattended trading;
- tick/order-book persistence and full historical minute replay as MVP requirements;
- microservices, Kafka/queues, distributed workers, Kubernetes, multi-tenancy, cloud high
  availability, and 24/7 execution infrastructure.

Read-only minute data and intraday calculation are research capabilities, not execution.

## 4. Engineering principles

1. Strategy, Portfolio, Accounting, Risk, Performance, and Backtest remain provider-agnostic.
2. Provider-specific adapters live under `integrations/` and expose read-only market data only.
3. Financial values use Python `Decimal`, never binary float.
4. SQLite persists exact financial values as fixed-scale canonical `TEXT` with no numeric affinity;
   PostgreSQL portability uses `NUMERIC(p,s)`.
5. External cash flows remain separate from investment return.
6. Missing, delayed, stale, unavailable, and erroneous data are explicit and never fabricated.
7. Instants are aware UTC; market sessions retain local date, timezone, and calendar.
8. Point-in-time research records require `available_at <= data_as_of`.
9. Simulated PaperFill state and advisory output are distinct and have no external effect.
10. Each task and phase is explicitly approved, verified, and stopped independently.

## 5. Target architecture

```text
Browser
  -> local FastAPI presentation
      -> application use cases / unit of work
          -> dashboard market-state query
          -> daily and completed-minute validation
          -> indicators / Composite Quant Score / ranking / risk state
          -> optional later paper research / performance / backtest
              -> SQLite

Independent read-only Market Data Provider
  -> provider adapter under integrations/
      -> canonical quotes, daily bars, completed minute bars, market status

External manual action
  advisory display -> user -> broker official client
```

There is no brokerage-account path and no path from an advisory result to an external command.

## 6. Module boundaries

| Module | Owns | Must not own or call |
|---|---|---|
| Dashboard | Selector, separate timeframes, polling state/countdown, freshness/error display | Provider SDK models, broker/account concepts |
| Strategy | Daily Base Score, Intraday Minute Adjustment, combined score, explanation | Provider SDKs, broker commands, accounting mutation |
| Portfolio | Tracked-security ranking and later simulated research allocations | Real-account state or broker commands |
| Accounting | Accepted Phase 1 opening facts and later approved paper bookkeeping | Strategy scoring or real-account facts |
| Risk | Explainable security/reference states | Broker SDKs or execution |
| Performance | Paper/research analytics | External calls during calculation |
| Backtest | Deterministic historical clock, point-in-time cursor, reports | Production mutation or assumed minute history |
| Market data port | Canonical quote, daily bars, completed minute bars, market status, timestamps | Brokerage account or execution capability |

Only the composition root selects a provider. Core modules do not read environment variables,
import provider SDKs, or branch on provider names.

## 7. Market-data and time contract

The provider boundary offers equivalents of `get_latest_quote()`, `get_daily_bars()`,
`get_minute_bars()`, and `get_market_status()`. TASK-003 approved a minimal Futu OpenD
quote-market-data implementation. TASK-004 exposes it through a provider-neutral application query
layer and three read-through API groups. OpenD availability, login, entitlements, latency, and
US/HK live observations remain environmental facts.

Daily data remains supported with a bounded 1300-session Dashboard request. The minute Dashboard
uses only completed provider bars from a rolling 30 market-local calendar-day window. US history
uses Futu `Session.ALL`; HK keeps normal provider sessions. Daily and 1-minute bars are displayed
in separate coordinate systems selected by a timeframe control.

At minimum, canonical state distinguishes:

```text
latest_quote_at
latest_completed_minute_bar_at
latest_completed_daily_session
score_calculated_at
```

Polling frequency is not provider latency. An unfinished minute bar is excluded from completed-bar
results. A latest/intraday price is never described as a final daily close.

## 8. Composite Quant Score governance

Approved architecture:

```text
Composite Quant Score = Daily Base Score + Intraday Minute Adjustment
```

The daily component may later represent trend, absolute/relative momentum, volatility, drawdown,
and medium-term risk. The minute component may later represent current-session momentum, price
relative to open/previous close, short averages, VWAP, volume, and intraday volatility/risk.

No formula, weight, threshold, band, normalization, sizing rule, or profitability claim is approved
by this master revision. `docs/STRATEGY_SPEC.md` remains `PROPOSED / RESEARCH_UNVALIDATED`; the
earlier completed-daily-only proposal is not authoritative for implementation. A separate strategy Task
Contract and explicit approval are required before score implementation.

## 9. Dashboard contract

The first usable dashboard shows a security selector, latest price, market status, bounded Daily
history, recent completed 1-minute history, volume, Composite Quant Score, security ranking,
reference/risk state, timestamps, and explicit missing/delayed/stale/error status. It contains no
real-order control and makes no claim that the user executed a recommendation.

## 10. Backtesting

Daily-bar backtesting is the baseline. It uses deterministic point-in-time data selection,
versioned transaction-cost assumptions, benchmark comparison, and reproducible reports. Current
minute data does not imply historical minute replay, tick simulation, or market-microstructure
storage. Any expansion beyond daily-bar baseline requires separate approval and legitimate data.

## 11. Infrastructure and secrets

Sufficient topology:

```text
Browser -> local FastAPI -> SQLite
                         -> independent read-only Market Data Provider
```

PostgreSQL compatibility is an engineering portability property, not a deployment requirement.
Never commit credentials, external/private account IDs, passwords, tokens, databases, logs, or
private exports. Provider secrets remain environment/external-secret inputs and are redacted.

## 12. Authoritative phases

The authoritative sequence is exactly:

- Phase 0 — Product Definition & Architecture (historically completed);
- Phase 1 — Foundation (accepted historical implementation);
- Phase 2 — Market Data, Dashboard & First Composite Score MVP;
- Phase 3 — Quant Research Expansion & Lightweight Paper Tracking;
- Phase 4 — Backtesting & Analytics (final product phase).

Detailed scope and stop conditions are in `docs/ROADMAP.md`. No later phase exists.

## 13. Quality and change control

For each approved implementation task: read governing docs; preserve unrelated changes; state the
exact file set; implement only approved scope; run the required proportional validation; verify
provenance, freshness, Decimal, UTC, and exclusions; update documentation/evidence; report exact
results; and stop.

TASK-003 implements the bounded Futu quote-only provider PoC. TASK-004 registers only the market
state, completed daily-bar, and completed minute-bar API groups. TASK-005 adds the market-first
Dashboard. TASK-005B expands only bounded chart history, US `Session.ALL` minute retrieval,
historical paging, incremental refresh, and long-history viewport behavior. It adds no persistence
or route group, selects no score formula, and does not start later Phase 2 features.

## 14. Accepted Phase 1 boundary

Phase 1 remains the reviewed foundation: packaging/configuration/logging; deterministic migration
0001; exact Decimal and UTC invariants; canonical Security identity; Watchlist; opening HKD 20,000,
200 units, and NAV 100 facts; read-only portfolio/performance/status APIs; accepted dashboard; and
inert capability descriptors. This revision changes none of that implementation or evidence.
