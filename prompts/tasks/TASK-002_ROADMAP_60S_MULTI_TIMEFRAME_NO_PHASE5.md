# TASK-002_ROADMAP_60S_MULTI_TIMEFRAME_NO_PHASE5

**Task ID:** TASK-002_ROADMAP_60S_MULTI_TIMEFRAME_NO_PHASE5  
**Status:** APPROVED_FOR_IMPLEMENTATION  
**Baseline commit:** `1f724ebe6cf5e5ffe7562cb578ae464ff44f613c`  
**Target base branch:** `roadmap/no-live-trading`  
**Task branch:** `task/TASK-002_ROADMAP_60S_MULTI_TIMEFRAME_NO_PHASE5`

## 1. Goal

Supersede the current EOD-only future Roadmap with the final product direction:

- local-first;
- single-user;
- read-only quantitative decision-support tool;
- daily + 1-minute dual-timeframe market data;
- 60-second refresh/recalculation;
- independent read-only Market Data Provider;
- all real trading performed manually outside the application;
- final Roadmap contains Phase 0 through Phase 4 only;
- Phase 5 and all real-portfolio/broker-account integration are permanently removed.

This task is documentation-only.

It must not modify runtime code, migrations, tests, or immutable Phase 1 review evidence.

## 2. Historical boundary

Preserve without reinterpretation:

- Phase 0 historical completion;
- Phase 1 accepted implementation;
- reviewed Phase 1 commit: `f6decf2fbe171c1b9eb46340a9174bc21f293ede`;
- Phase 1 PASS status;
- both Phase 1 Review files.

The previous EOD-only Roadmap commit:

`1f724ebe6cf5e5ffe7562cb578ae464ff44f613c`

must not be reverted.

This task creates a new traceable superseding product decision.

Phase 2 has not begun.

## 3. Final product boundary

The application is a personal quantitative research and decision-support system.

It may:

- obtain market data from an independent read-only Market Data Provider;
- display quotes and charts;
- calculate indicators;
- calculate Composite Quant Scores;
- rank tracked securities;
- produce risk/reference states;
- maintain lightweight simulated/paper research state in later approved tasks;
- run backtests.

The application must not:

- connect to a brokerage account;
- read brokerage cash;
- read real brokerage positions;
- read or import real trades;
- synchronize completed broker orders;
- reconcile against a real brokerage account;
- place, cancel, replace, or modify a real order.

Global real-trading boundary:

> 用户在券商官方客户端手工完成所有真实交易。

The application does not need to know whether the user actually executed a recommendation.

## 4. Market Data Provider boundary

Broker connection and market-data connection are distinct concepts.

The product may connect to an **independent read-only Market Data Provider**.

The Market Data Provider supplies market information only and must not require the application to access the user's brokerage account.

Future provider-facing capabilities may include equivalent operations such as:

```text
get_latest_quote()
get_daily_bars()
get_minute_bars()
get_market_status()
```

Exact Python interfaces and provider implementation are not approved by this task.

This task does **not** select a concrete provider.

Provider selection, API credentials, entitlement validation, pricing, and a real-data proof of concept belong to a later Market Data implementation task.

The architecture must remain provider-agnostic so a provider can be replaced without rewriting Strategy, Dashboard, Portfolio, or Backtest logic.

## 5. Initial tracked securities

Initial product targets remain:

```text
US.AVGO
US.VRT
HK.09698
```

The system must support both US and Hong Kong market-data requirements for these initial instruments.

## 6. Dashboard and chart requirements

The first usable product must prioritize a broker-style read-only dashboard.

Required views:

- security selector;
- latest price;
- market status;
- daily candlestick chart;
- current trading day's 1-minute candlestick chart;
- volume;
- Composite Quant Score;
- security ranking;
- reference/risk state;
- market-data timestamps;
- explicit missing/delayed/stale/error state.

Daily candles and 1-minute candles must be displayed as separate timeframes.

They must not be overlaid in the same coordinate system.

The user may switch between them using a timeframe tab/button.

For the first minute-bar implementation, only the **current trading day's completed 1-minute bars** are required.

Full historical minute replay, tick history, order book history, and market-microstructure storage are not MVP requirements.

Exact minute-data retention policy is deferred to the Phase 2 implementation plan.

## 7. 60-second refresh contract

During an active visible dashboard session, the following are refreshed or recalculated approximately every 60 seconds:

- page market state;
- latest price;
- incremental 1-minute bars;
- Composite Quant Score;
- tracked-security ranking;
- reference/risk state.

MVP transport should use ordinary HTTP/REST polling.

WebSocket or streaming infrastructure is not required.

The frontend must eventually support these behavioral requirements:

- no overlapping polling requests;
- pause automatic polling while the page is hidden;
- refresh immediately when the page becomes visible again;
- manual `刷新最新行情` control;
- automatic-refresh countdown.

Closing the page does not require background processing.

## 8. Market-data time semantics

Quotes, bars, and scores must distinguish at minimum:

```text
latest_quote_at
latest_completed_minute_bar_at
latest_completed_daily_session
score_calculated_at
```

The product must never:

- present an unfinished 1-minute bar as a completed minute bar;
- describe an intraday/latest price as the final daily close;
- confuse polling frequency with source latency.

For example:

```text
polling frequency = 60 seconds
provider data delay = 15 minutes
```

must be represented as different facts.

Missing, delayed, stale, unavailable, or erroneous data must be explicit.

No market value may be fabricated.

## 9. Composite Quant Score architecture

The approved high-level architecture becomes:

```text
Composite Quant Score
    =
Daily Base Score
    +
Intraday Minute Adjustment
```

Daily Base Score represents medium-term structure and may eventually include factors such as:

- trend;
- absolute momentum;
- relative momentum;
- volatility;
- drawdown;
- medium-term risk.

Intraday Minute Adjustment represents current-session strength/risk and may eventually use:

- 5-minute momentum;
- 15-minute momentum;
- 30-minute momentum;
- price versus session open;
- price versus previous close;
- short-term moving averages;
- VWAP;
- minute volume;
- intraday volatility/risk adjustment.

This task approves only the architecture.

It does **not** approve:

- exact formula;
- weights;
- thresholds;
- score bands;
- normalization method;
- sizing formula;
- profitability claims.

`docs/STRATEGY_SPEC.md` must remain `PROPOSED / RESEARCH_UNVALIDATED`.

Its existing EOD-only formula proposal must no longer be treated as the authoritative implementation formula for the new Composite Quant Score.

A later explicit strategy task must approve the concrete model.

## 10. Final authoritative phase model

The final Roadmap contains exactly:

### Phase 0 — Product Definition & Architecture

Historical completion preserved.

Future product-scope decisions may supersede earlier Phase 0 planning without rewriting historical evidence.

### Phase 1 — Foundation

Completed and independently accepted.

Preserve:

- FastAPI;
- SQLite;
- SQLAlchemy;
- Alembic;
- deterministic migrations;
- Decimal/UTC invariants;
- Security identity;
- Watchlist;
- Portfolio;
- opening accounting foundation;
- accepted Phase 1 APIs/frontend;
- Phase 1 tests and reviews.

### Phase 2 — Market Data, Dashboard & First Composite Score MVP

Highest priority is a visible, usable product.

Planned scope includes:

- independent Market Data Provider integration;
- AVGO / VRT / HK.09698;
- latest price;
- market status;
- daily OHLCV;
- current-session completed 1-minute OHLCV;
- daily/1-minute chart switching;
- 60-second polling;
- manual refresh;
- data freshness/error handling;
- first approved dual-timeframe Composite Score implementation;
- score display;
- ranking/reference state.

The exact Composite Score formula requires a separate Task Contract and explicit approval before implementation.

Complex accounting must not block these visible Phase 2 deliverables.

### Phase 3 — Quant Research Expansion & Lightweight Paper Tracking

Planned scope may include:

- richer factor research;
- strategy explanation;
- additional ranking/risk analytics;
- signal history;
- lightweight simulated/paper portfolio;
- PaperFill-based research bookkeeping;
- paper performance analysis.

Paper state remains simulated only.

No real account, real position, real trade, or broker synchronization is permitted.

### Phase 4 — Backtesting & Analytics

Final product phase.

Planned scope includes:

- deterministic backtesting;
- point-in-time controls;
- transaction-cost assumptions;
- benchmark comparison;
- drawdown;
- volatility;
- turnover;
- attribution;
- exposure;
- diagnostics;
- strategy comparison;
- parameter analysis;
- reproducible research reports.

Daily-bar backtesting is the baseline requirement.

The existence of live/current 1-minute dashboard data does not automatically require full historical minute replay or tick-level simulation.

No Phase 5 exists.

## 11. Permanently removed Phase 5 scope

Delete from future product authority:

```text
ManualRealTradeRecord
real completed-trade entry
real trade CSV/file import
BrokerObservation
broker account synchronization
Futu or other broker-account integration
Broker Adapter for account observations
real brokerage cash
real brokerage positions
real portfolio tracking
real trade reconciliation
reconciliation discrepancy handling
real Current vs Target portfolio
trade sizing based on real brokerage holdings
real broker fees/taxes/settlement synchronization
```

These capabilities must not be moved into Phase 2, Phase 3, or Phase 4.

They are removed, not deferred.

## 12. Permanent trading exclusions

Continue to permanently forbid:

```text
place_order
cancel_order
modify_order
broker write
real-order API
real-order UI
Live OMS
Live EMS
trading-password unlock
broker buying-power reservation
execution retry/recovery
execution workers
execution kill switch
autonomous trading
unattended trading
```

Also continue to exclude unnecessary infrastructure:

```text
microservices
Kafka
distributed workers
Kubernetes
multi-tenant architecture
24/7 execution infrastructure
tick persistence
institutional OMS
large generic provider plugin frameworks
```

Read-only 1-minute market data and intraday score calculation are **not** execution capabilities and must no longer be prohibited merely because they are intraday.

## 13. Allowed documentation changes

Expected documentation scope:

```text
README.md
AGENTS.md
docs/ROADMAP.md
docs/MASTER_SPEC.md
docs/ARCHITECTURE.md
docs/DATABASE_SCHEMA.md
docs/API_CONTRACTS.md
docs/STRATEGY_SPEC.md
docs/REQUIREMENTS_MATRIX.md
```

Changes must be limited to future product scope and consistency.

## 14. Forbidden changes

Do not modify:

```text
src/**
tests/**
docs/reviews/PHASE_1_INDEPENDENT_REVIEW.md
docs/reviews/PHASE_1_POST_REMEDIATION_REVIEW.md
docs/phases/PHASE_1_PLAN.md
```

Do not modify, delete, stage, or commit any local untracked:

```text
phase1_remediation_commit.txt
```

Do not create or modify migrations.

Do not implement market data.

Do not implement Composite Score.

Do not start Phase 2.

## 15. Documentation acceptance criteria

The task passes only if all authoritative future-scope documents consistently satisfy the following:

1. Final phase model is exactly Phase 0–4.
2. No authoritative Phase 5 remains.
3. Phase 1 PASS status and historical evidence remain unchanged.
4. Product is no longer described as EOD-only.
5. Daily bars remain supported.
6. Completed current-session 1-minute bars are explicitly supported.
7. Daily and 1-minute charts are explicitly separate.
8. 60-second refresh/recalculation behavior is documented.
9. Manual refresh is documented.
10. Hidden-page polling pause and visible-page refresh behavior are documented.
11. The four time semantics are documented.
12. Source latency is distinguished from polling cadence.
13. Composite Score architecture is Daily Base + Intraday Minute Adjustment.
14. Formula/weight/threshold decisions remain unapproved.
15. Independent read-only Market Data Provider is explicitly allowed.
16. No concrete Market Data Provider is selected by this task.
17. No broker-account connection remains in future scope.
18. ManualRealTradeRecord is removed from future scope.
19. BrokerObservation is removed from future scope.
20. Real-account reconciliation is removed from future scope.
21. No broker-write or autonomous-trading capability exists.
22. No Phase 2 functionality is implemented by this documentation task.

## 16. Validation

Because this is documentation-only, validation should remain proportional.

Required:

```text
git diff --check
git diff --stat
```

Perform targeted repository scans confirming:

```text
Phase 5
ManualRealTradeRecord
BrokerObservation
broker sync
reconciliation
EOD-only
minute bars prohibited
intraday prohibited
```

Any remaining occurrence must be classified as either:

- immutable/historical evidence; or
- a defect that must be removed from authoritative future-scope documentation.

Verify that no files under:

```text
src/
tests/
docs/reviews/
```

were changed.

Full Phase 1 runtime regression testing is not required for this documentation-only task.

## 17. Commit and push rules

Work only on the approved task branch.

Do not modify `master`.

Do not force-push.

Do not amend historical commits.

Create one documentation commit after validation.

Do not automatically merge into `roadmap/no-live-trading`.

Do not start another task.

Report the resulting:

- branch;
- commit SHA;
- parent SHA;
- changed files;
- validation results.

Then stop for independent ChatGPT review.

## 18. Stop condition

After the documentation commit is pushed to the task branch:

**STOP.**

Do not implement Market Data Provider integration.

Do not select a concrete data vendor.

Do not implement the Dashboard.

Do not implement Composite Quant Score.

Do not begin Phase 2.

Wait for independent review and explicit user approval.
