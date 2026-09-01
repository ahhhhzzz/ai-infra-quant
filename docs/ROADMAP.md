# Read-Only Multi-Timeframe Product Roadmap

Status: **AUTHORITATIVE — daily + 1-minute read-only future scope**

Decision: `MTF-001`, approved 2026-09-01

Product: **Personal Quantitative Research and Decision-Support Tool**

## 1. Authority, supersession, and history

This Roadmap governs future product scope after the accepted Phase 1 baseline. Decision `MTF-001`
supersedes the future-scope direction recorded by `EOD-001` at commit
`1f724ebe6cf5e5ffe7562cb578ae464ff44f613c`; that commit remains intact as traceable history and is
not reverted.

Historical facts are unchanged:

- Phase 0 was completed historically;
- Phase 1 was implemented and independently accepted;
- the reviewed Phase 1 commit is `f6decf2fbe171c1b9eb46340a9174bc21f293ede`;
- Phase 1 status remains PASS;
- both Phase 1 review files remain immutable evidence;
- TASK-003 completed the bounded Phase 2 Futu quote-only market-data PoC;
- TASK-004 adds only the provider-neutral read-through market-data backend;
- TASK-005 adds only the market-data Dashboard client.

Earlier Phase 1 broker/provider abstractions are historical artifacts, not authority to implement
broker-account or broker-write behavior.

## 2. Product operating model

The product is local-first, single-user, and read-only with respect to external financial systems.
It supports daily market data and completed 1-minute bars for the current trading session. During
an active visible dashboard session it refreshes or recalculates approximately every 60 seconds.

The application may obtain market information from an independent read-only Market Data Provider,
display quotes and separate daily/minute charts, calculate indicators and Composite Quant Scores,
rank tracked securities, show reference/risk states, maintain later-approved simulated research
state, and run backtests.

It never connects to a brokerage account and never reads broker cash, positions, completed orders,
or trades. It does not import or match real trades and does not need to know whether the user
acted on a recommendation.

> 用户在券商官方客户端手工完成所有真实交易。

## 3. Market Data Provider boundary

Market-data access and brokerage-account access are distinct concepts. A future integration may
use an independent read-only Market Data Provider that supplies market information without access
to the user's brokerage account. Equivalent operations may include:

```text
get_latest_quote()
get_daily_bars()
get_minute_bars()
get_market_status()
```

These names are illustrative only. `MTF-001` did not itself select a provider. The separately
approved TASK-003 selects Futu OpenD quote-market-data APIs for a bounded PoC covering the three
initial securities; OpenD availability, login, quote entitlements, and observed delay remain
environmental live-verification facts.

TASK-004 exposes that accepted quote-only adapter through provider-neutral FastAPI queries for
current market state, completed daily bars, and current-session completed 1-minute bars. TASK-005
adds the local read-only Dashboard over those routes, including page-local guarded polling. The
default provider mode remains offline (`none`); `futu` is explicit configuration. No market-data
persistence, backend background polling, aggregate Dashboard route, or score behavior is
introduced.

Provider-specific code remains under `integrations/`; Strategy, Dashboard, Portfolio, Risk,
Performance, and Backtest consume provider-agnostic canonical data.

Initial tracked securities are:

```text
US.AVGO
US.VRT
HK.09698
```

The data boundary must support both United States and Hong Kong market requirements.

## 4. Dashboard and chart contract

The first usable product prioritizes a broker-style read-only dashboard with:

- security selector;
- latest price and market status;
- daily candlestick chart;
- current trading day's completed 1-minute candlestick chart;
- volume;
- Composite Quant Score;
- tracked-security ranking;
- reference/risk state;
- market-data timestamps;
- explicit missing, delayed, stale, unavailable, and error states.

Daily and 1-minute candles are separate timeframes and must never be overlaid in the same coordinate
system. A timeframe tab or button switches between them.

The first minute-bar implementation requires only the current trading day's completed 1-minute
bars. Full historical minute replay, tick history, order-book history, and market-microstructure
storage are not MVP requirements. Minute-data retention is deferred to the Phase 2 implementation
plan.

## 5. Refresh and time semantics

While the dashboard is visible and active, the page market state, latest price, incremental
completed 1-minute bars, Composite Quant Score, tracked-security ranking, and reference/risk state
refresh or recalculate approximately every 60 seconds.

MVP transport is ordinary HTTP/REST polling. The frontend must:

- avoid overlapping polling requests;
- pause automatic polling while the page is hidden;
- refresh immediately when the page becomes visible again;
- provide a manual `刷新最新行情` control;
- display an automatic-refresh countdown.

Closing the page requires no background processing.

Quotes, bars, and scores distinguish at minimum:

```text
latest_quote_at
latest_completed_minute_bar_at
latest_completed_daily_session
score_calculated_at
```

An unfinished 1-minute bar must never be presented as completed. An intraday/latest price must
never be called the final daily close. Polling cadence and provider latency are separate facts; for
example, a 60-second polling frequency and a 15-minute source delay must be reported independently.
No market value is fabricated.

## 6. Composite Quant Score architecture

The approved high-level architecture is:

```text
Composite Quant Score
    =
Daily Base Score
    +
Intraday Minute Adjustment
```

The Daily Base Score represents medium-term structure and may later include trend, absolute and
relative momentum, volatility, drawdown, and medium-term risk. The Intraday Minute Adjustment
represents current-session strength/risk and may later use 5/15/30-minute momentum, price versus
session open or previous close, short moving averages, VWAP, minute volume, and intraday volatility.

This decision approves architecture only. Exact formulae, weights, thresholds, bands,
normalization, sizing, and profitability claims remain unapproved. `docs/STRATEGY_SPEC.md` remains
`PROPOSED / RESEARCH_UNVALIDATED`; its earlier completed-daily-only formula is not implementation authority. A
later explicit strategy Task Contract must approve a concrete model before implementation.

## 7. Authoritative phase model

The authoritative phase sequence is exactly Phase 0 through Phase 4.

### Phase 0 — Product Definition & Architecture

Historical completion is preserved. Later product-scope decisions may supersede its planning
without rewriting historical evidence.

### Phase 1 — Foundation

Completed and independently accepted. Preserve FastAPI, SQLite, SQLAlchemy, Alembic, deterministic
migrations, Decimal/UTC invariants, Security identity, Watchlist, Portfolio, opening accounting
foundation, accepted APIs/frontend, tests, and reviews.

### Phase 2 — Market Data, Dashboard & First Composite Score MVP

Highest priority is a visible, usable product. Planned scope includes:

- independent Market Data Provider integration;
- AVGO, VRT, and HK.09698;
- latest price and market status;
- daily OHLCV and current-session completed 1-minute OHLCV;
- separate daily/1-minute chart switching;
- approximately 60-second polling and recalculation;
- manual refresh and automatic-refresh countdown;
- hidden-page polling pause and immediate visible-page refresh;
- freshness, latency, missing-data, and error handling;
- the first separately approved dual-timeframe Composite Score implementation;
- score display, ranking, and reference/risk state.

The exact Composite Score formula requires a separate Task Contract and explicit approval. Complex
accounting must not block the visible deliverables. TASK-004 implements the market-data backend;
TASK-005 implements the read-only Dashboard, separate daily/minute candle and volume views, and
visible-page refresh behavior. Composite Score, ranking, and reference/risk calculation remain
unimplemented.

### Phase 3 — Quant Research Expansion & Lightweight Paper Tracking

Planned scope may include richer factor research, strategy explanation, additional ranking/risk
analytics, signal history, a lightweight simulated/paper portfolio, PaperFill-based research
bookkeeping, and paper performance analysis. Paper state is simulated only. No real account,
position, trade, or brokerage synchronization is permitted.

### Phase 4 — Backtesting & Analytics

This is the final product phase. Planned scope includes deterministic backtesting, point-in-time
controls, transaction-cost assumptions, benchmark comparison, drawdown, volatility, turnover,
attribution, exposure, diagnostics, strategy comparison, parameter analysis, and reproducible
research reports.

Daily-bar backtesting is the baseline. Current-session minute data does not automatically require
historical minute replay or tick-level simulation. The Roadmap ends at Phase 4; no later phase
exists.

## 8. Permanently removed product scope

The following capabilities are removed rather than deferred and must not be moved into any phase:

```text
legacy real completed-trade record type
real completed-trade entry or CSV/file import
legacy external account-observation type
broker account synchronization
Futu or other broker-account integration
Broker Adapter for account observations
real brokerage cash or positions
real portfolio tracking
real trade matching or discrepancy handling
real Current versus Target portfolio
trade sizing based on real brokerage holdings
real broker fees, taxes, or settlement synchronization
```

Broker-write and autonomous-execution capabilities remain permanently forbidden, including
`place_order`, `cancel_order`, `modify_order`, broker write, real-order API/UI, Live OMS/EMS,
trading-password unlock, buying-power reservation, execution retry/recovery/workers/kill switches,
and autonomous or unattended trading.

Unnecessary infrastructure remains excluded: microservices, Kafka, distributed workers,
Kubernetes, multi-tenancy, 24/7 execution infrastructure, tick persistence, institutional OMS,
and large generic provider plugin frameworks.

Read-only 1-minute market data and intraday score recalculation are analysis capabilities, not
execution capabilities.

## 9. Governance and stop conditions

- Phase 1 remains accepted and unchanged; TASK-003, TASK-004, and TASK-005 are bounded Phase 2 increments.
- Each implementation phase requires explicit approval and a phase-specific plan or Task Contract.
- No provider, formula, or retention policy is selected unless separately approved; TASK-003
  selected only the Futu quote-only provider, TASK-004 approved only its read-through backend, and
  TASK-005 approved only the Dashboard client.
- Documentation and requirements must preserve explicit data freshness and non-fabrication rules.
- Every task reports evidence and stops before the next task or phase.
