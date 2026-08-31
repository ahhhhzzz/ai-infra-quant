# AI Infra Quant Platform — Master Specification v1.0

## 0. Document status and instruction precedence

This document is the authoritative product and engineering specification for the repository.

Instruction precedence:

1. The current phase prompt explicitly sent by the user.
2. Root `AGENTS.md`.
3. This `docs/MASTER_SPEC.md`.
4. Current phase plan under `docs/phases/`.
5. Other project documentation.

If two requirements conflict, do not silently choose one. Record the conflict, recommend a resolution, and stop if the conflict blocks the current phase.

This is a long-running, phase-gated project. Do not implement future phases early.

---

## 1. Product objective

Build a local-first, extensible personal quantitative investment platform, not a static dashboard and not a tool hard-coded to one broker.

The platform must ultimately support:

- Security/watchlist management.
- Historical and live market data.
- Pluggable quantitative strategies.
- Paper trading and simulated capital flows.
- Portfolio accounting and performance attribution.
- Backtesting using the same strategy logic as paper/live environments.
- Broker-agnostic execution.
- Market-data-provider-agnostic data access.
- Multiple broker accounts and multiple currencies.
- Futu OpenAPI/OpenD integration.
- A replaceable adapter for EastMoney or other brokers when a legitimate, stable interface is available.
- Manual approval for every live order in v1.

Initial tracked securities:

- `US.AVGO`
- `US.VRT`
- `HK.09698`

Initial paper capital:

- Base reporting currency: `HKD`
- Initial capital: `HKD 20,000`
- Strategy/performance inception date: `2026-08-31`
- Initial NAV: `100.00`

These defaults must be configurable and must not be hard-coded into core business logic.

---

## 2. MVP scope and explicit non-goals

### 2.1 v1 operating model

The first production-worthy version is:

- Single-user.
- Local-first.
- Single-process modular monolith.
- Long-only equities/ETFs.
- Cash-account semantics.
- Manual approval before every live order.
- SQLite first, with SQLAlchemy models compatible with a later PostgreSQL migration.
- FastAPI backend.
- HTML/CSS/JavaScript frontend.

### 2.2 v1 non-goals

Do not introduce the following unless a later phase explicitly proves they are necessary:

- Microservices.
- Kafka or another event bus.
- Redis.
- Celery or a distributed worker system.
- Kubernetes.
- Multi-tenant architecture.
- Distributed event sourcing infrastructure.
- Margin trading.
- Short selling.
- Options, futures, or leveraged derivatives.
- Autonomous live execution.
- High-frequency or intraday market-making logic.

Prefer the simplest design that satisfies the concrete extension requirements in this specification.

---

## 3. Highest-priority engineering principles

1. Broker-agnostic core.
2. Market-data-agnostic core.
3. Fundamental/event data separated from price data.
4. Strategy plugin architecture.
5. Backtest, paper, and live environments share the same strategy implementation.
6. Strategy code must never call a broker SDK directly.
7. Portfolio/accounting code must never call a broker SDK directly.
8. Risk code must never call a broker SDK directly.
9. Trading broker and market-data provider must be independently selectable.
10. External capital flows must be separated from investment return.
11. All accounting calculations must be reproducible.
12. Financial amounts, prices, quantities, fees, and FX rates use `Decimal`, not binary floating point. PostgreSQL persists them as `NUMERIC(p,s)`; SQLite persists them through a dialect-aware, no-numeric-affinity canonical fixed-scale `TEXT` representation so SQLite cannot coerce them to binary `REAL`.
13. No fabricated market, valuation, fundamental, or broker data.
14. Missing data must be marked as `MISSING`, `UNAVAILABLE`, or `NOT_SUPPORTED`.
15. Live trading is disabled by default and must be blocked server-side, not merely hidden in the UI.
16. Every phase must be runnable and tested before the next phase starts.
17. Existing unrelated user changes must not be overwritten.
18. No `git push`, remote changes, or global Git configuration changes without explicit user approval.

---

## 4. Target architecture

```text
                              Frontend
                                  |
                               REST API
                                  |
                              Quant Core
                                  |
       ----------------------------------------------------------------
       |                 |                |               |             |
 Strategy Engine   Portfolio Engine   Risk Engine   Performance   Execution
       |                 |                |               |             |
       ----------------------------------------------------------------
                                                                        |
                                                               BrokerAdapter
                                                                        |
                                  ----------------------------------------------
                                  |                    |                       |
                             PaperBroker           FutuBroker          EastMoneyBroker

Market-data path:

MarketDataProvider -> Normalized Market Data -> Indicators -> Strategy Engine

Fundamental/event path:

FundamentalDataProvider / EventDataProvider
        -> point-in-time normalized records
        -> valuation/fundamental risk modules
        -> Strategy Engine / Fundamental Veto
```

The core must not know which broker or data vendor is active.

Examples that must be supported by the architecture:

- Execution: Futu; price data: Futu.
- Execution: EastMoney; price data: Futu.
- Execution: PaperBroker; price data: another provider.
- One internal portfolio containing positions held across multiple broker accounts.

---

## 5. Suggested repository layout

```text
ai-infra-quant/
├── AGENTS.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── README.md
├── backend/
│   ├── main.py
│   ├── api/
│   ├── schemas/
│   └── services/
├── core/
│   ├── domain/
│   ├── strategy/
│   ├── portfolio/
│   ├── accounting/
│   ├── execution/
│   ├── risk/
│   ├── performance/
│   └── securities/
├── strategies/
│   ├── base.py
│   ├── registry.py
│   ├── ai_infra.py
│   └── dual_momentum.py
├── integrations/
│   ├── registry.py
│   ├── paper/
│   │   └── broker.py
│   ├── futu/
│   │   ├── connection.py
│   │   ├── broker.py
│   │   ├── market_data.py
│   │   ├── symbol_mapper.py
│   │   ├── capabilities.py
│   │   └── errors.py
│   ├── eastmoney/
│   │   ├── broker.py
│   │   ├── market_data.py
│   │   ├── symbol_mapper.py
│   │   └── capabilities.py
│   ├── fundamentals/
│   └── events/
├── database/
│   ├── models.py
│   ├── session.py
│   ├── repositories/
│   └── migrations/
├── backtest/
├── frontend/
├── tests/
│   ├── fixtures/
│   ├── unit/
│   ├── integration/
│   └── golden/
├── docs/
│   ├── MASTER_SPEC.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   ├── API_CONTRACTS.md
│   ├── STRATEGY_SPEC.md
│   ├── REQUIREMENTS_MATRIX.md
│   └── phases/
└── logs/
```

The exact layout may be refined in Phase 0, but separation of core, strategy, integrations, persistence, and presentation is mandatory.

---

## 6. Provider and broker abstractions

### 6.1 BrokerAdapter

Define an abstract broker contract whose return types are platform-owned canonical models.

Minimum methods:

```python
class BrokerAdapter(ABC):
    broker_name: str

    def connect(self) -> ConnectionResult: ...
    def disconnect(self) -> None: ...
    def connection_status(self) -> ConnectionStatus: ...
    def capabilities(self) -> BrokerCapabilities: ...
    def get_accounts(self) -> list[BrokerAccount]: ...
    def get_account_info(self, account_id: str) -> AccountInfo: ...
    def get_cash_balances(self, account_id: str) -> list[CashBalance]: ...
    def get_positions(self, account_id: str) -> list[BrokerPosition]: ...
    def get_orders(self, account_id: str, ...) -> list[OrderResult]: ...
    def get_fills(self, account_id: str, ...) -> list[FillResult]: ...
    def get_buying_power(self, account_id: str, currency: str) -> Decimal: ...
    def place_order(self, order: StandardOrder) -> OrderResult: ...
    def cancel_order(self, request: CancelOrderRequest) -> OrderResult: ...
    def modify_order(self, request: ModifyOrderRequest) -> OrderResult: ...
    def get_market_status(self, market: str) -> MarketStatus: ...
```

Implement:

- `PaperBroker`.
- `FutuBroker`.
- `EastMoneyBroker` as a truthful skeleton until a legitimate, stable trading interface is selected.

Do not fabricate an EastMoney live-trading implementation. Mark unsupported operations as `NOT_IMPLEMENTED` or `NOT_SUPPORTED`.

### 6.2 MarketDataProvider

```python
class MarketDataProvider(ABC):
    def connect(self) -> ConnectionResult: ...
    def disconnect(self) -> None: ...
    def capabilities(self) -> MarketDataCapabilities: ...
    def get_quote(self, security_id: str) -> Quote: ...
    def get_snapshot(self, security_ids: list[str]) -> list[Snapshot]: ...
    def get_history(self, request: HistoryRequest) -> PriceSeries: ...
    def subscribe(self, request: SubscriptionRequest) -> SubscriptionResult: ...
    def unsubscribe(self, request: SubscriptionRequest) -> SubscriptionResult: ...
    def get_order_book(self, security_id: str) -> OrderBook: ...
```

### 6.3 FundamentalDataProvider

Price data alone cannot satisfy valuation and fundamental-risk requirements.

```python
class FundamentalDataProvider(ABC):
    def get_financials(self, security_id: str, as_of: datetime) -> list[FinancialRecord]: ...
    def get_estimates(self, security_id: str, as_of: datetime) -> list[EstimateRecord]: ...
    def get_valuation_metrics(self, security_id: str, as_of: datetime) -> ValuationSnapshot: ...
    def get_valuation_history(self, security_id: str, end: datetime, lookback: str) -> ValuationSeries: ...
    def get_balance_sheet_metrics(self, security_id: str, as_of: datetime) -> BalanceSheetMetrics: ...
```

Every fundamental record must preserve provenance and point-in-time availability:

- `source`
- `source_record_id`
- `period_end`
- `published_at`
- `available_at`
- `effective_at`
- `retrieved_at`
- `currency`
- `is_restated`

### 6.4 EventDataProvider

```python
class EventDataProvider(ABC):
    def get_earnings_calendar(self, security_id: str, ...) -> list[CorporateEvent]: ...
    def get_corporate_actions(self, security_id: str, ...) -> list[CorporateAction]: ...
    def get_regulatory_events(self, security_id: str, ...) -> list[RiskEvent]: ...
    def get_manual_risk_flags(self, security_id: str, ...) -> list[ManualRiskFlag]: ...
```

In v1, fundamental veto may be `MANUAL` or `DATA_ASSISTED`. Do not silently scrape unreliable news and label the result as a verified fundamental fact.

### 6.5 Registry and factory

Use registries/factories so core code does not contain scattered provider-specific conditionals.

Examples:

```python
BrokerRegistry.register("paper", PaperBroker)
BrokerRegistry.register("futu", FutuBroker)
BrokerRegistry.register("eastmoney", EastMoneyBroker)

MarketDataRegistry.register("futu", FutuMarketDataProvider)
```

### 6.6 Capability separation

Define separate capability models:

- `BrokerCapabilities`
- `MarketDataCapabilities`
- `FundamentalDataCapabilities`
- `EventDataCapabilities`

Broker capabilities should include, as applicable:

- `LIVE_TRADING`
- `PAPER_TRADING`
- `US_STOCK`
- `HK_STOCK`
- `CN_STOCK`
- `FRACTIONAL_SHARES`
- `ODD_LOT`
- `MARKET_ORDER`
- `LIMIT_ORDER`
- `AFTER_HOURS`

Unsupported features must be displayed as `NOT_SUPPORTED`, not allowed to fail unpredictably.

---

## 7. Canonical security, account, order, and execution models

### 7.1 Security master

Internal security identifiers must be vendor-neutral.

Example:

```text
market=US, symbol=AVGO
market=US, symbol=VRT
market=HK, symbol=09698
```

Minimum metadata:

- `id`
- `symbol`
- `market`
- `exchange`
- `currency`
- `display_name`
- `instrument_type`
- `enabled`
- `lot_size`
- `min_order_quantity`
- `quantity_step`
- `tick_size`
- `min_notional`
- `fractional_supported`
- `fractional_quantity_step`
- `market_timezone`
- `trading_calendar`
- `created_at`
- `updated_at`

Store provider mappings separately:

- `security_id`
- `provider_type`
- `provider_name`
- `provider_symbol`

For example, Futu may map `HK/09698` to `HK.09698`.

Phase 1 must also provide a user-controlled canonical-security creation path. A user may supply market, symbol, currency, instrument type, and optional display name. Such a record is `USER_SUPPLIED_UNVERIFIED`; tradability, provider mappings, calendar, lot/tick/minimum rules, and price/fundamental provenance remain unavailable until separately verified. It may be placed on a watchlist, but strategy execution and all orders are blocked until required metadata and data are valid.

### 7.2 Portfolio versus broker account

A portfolio is an internal investment grouping. A broker account is an execution/custody account. They must not be the same entity.

One portfolio may aggregate positions across multiple broker accounts.

### 7.3 StandardOrder

Minimum fields:

- `internal_order_id`
- `client_order_id`
- `idempotency_key`
- `portfolio_id`
- `account_id`
- `broker_profile_id`
- `security_id`
- `side`
- `order_type`
- `quantity`
- `limit_price`
- `currency`
- `time_in_force`
- `created_at`
- `expires_at`
- `strategy_run_id`
- `recommendation_id`

A broker adapter converts `StandardOrder` into the broker-specific request.

### 7.4 OrderResult and FillResult

`SUBMITTED` is not `FILLED`.

Minimum order states:

- `CREATED`
- `RISK_REJECTED`
- `PENDING_APPROVAL`
- `SUBMITTING`
- `SUBMITTED`
- `PARTIALLY_FILLED`
- `FILLED`
- `CANCEL_PENDING`
- `CANCELLED`
- `REJECTED`
- `EXPIRED`
- `ERROR`

Positions and cash may only be updated from confirmed fills, fees, FX transactions, cash flows, or corporate actions.

The same idempotency key must never create two broker orders.

---

## 8. Accounting, cash, NAV, and performance

### 8.1 Decimal and append-only ledger

Use `Decimal` in Python for money, price, quantity, FX, fees, ratios, and scores. API values are canonical decimal strings.

Physical persistence is dialect-aware:

- SQLite uses a custom SQLAlchemy `TypeDecorator` or equivalently exact design backed by fixed-scale canonical `TEXT` in a column with no numeric affinity.
- PostgreSQL uses `NUMERIC(p,s)`.
- Floats are forbidden at every boundary.
- SQLite ledger arithmetic and balance validation occur with Python `Decimal` inside one Unit of Work; do not claim that `SUM`, `CAST`, or other SQLite arithmetic over decimal text is exact.
- Ordering/range operations on stored SQLite decimals use validated application `Decimal` values or a separately designed exact sortable representation; ordinary lexical ordering is not assumed to be numeric.

The exact values `100.000000000000000001`, `12345678901234567890.123456789012345678`, and `0.123456789012345678` must round-trip without change.

The accounting ledger is append-only. Orders/fills/cash flows must not be silently overwritten or deleted.

### 8.2 Multi-currency cash

Base reporting currency is HKD, but cash must be recorded by account and currency.

Required concepts:

- `cash_balances`
- `cash_reservations`
- `fx_transactions`
- `settlements`
- `settled_cash`
- `unsettled_cash`
- `buying_power`

PaperBroker must support two explicit FX modes:

1. `EXPLICIT_FX`: user converts currency before trading.
2. `AUTO_FX`: an order creates a recorded FX transaction with rate, spread, and fee.

AUTO_FX must never occur silently.

### 8.3 External cash flows versus return

Deposits and withdrawals are not profit or loss.

Implement unitized NAV and Time-Weighted Return.

Initial state:

```text
Portfolio equity = HKD 20,000
Units = 200
NAV = 100.00
```

A deposit issues new units at the NAV immediately before the external cash flow. A withdrawal redeems units at the NAV immediately before the cash flow. External cash flows must not create a NAV jump.

After positions exist, deposit or withdrawal requires a complete official `FLOW_PRE` valuation snapshot. Every position must have a valid point-in-time mark and every required currency conversion must have a valid point-in-time FX rate. If valuation is incomplete, reject the flow with `PORTFOLIO_VALUATION_UNAVAILABLE`; do not issue/redeem units from an incomplete NAV.

At minimum, report:

- Portfolio value.
- Cash by currency and total HKD equivalent.
- Market value.
- Cost basis.
- Realized P&L.
- Unrealized P&L.
- Fees and taxes.
- Equity P&L.
- FX P&L.
- Daily, weekly, monthly, and since-inception return.
- TWR.
- NAV.
- Maximum drawdown.
- Benchmark return.
- Cash ratio and invested ratio.

Money-Weighted Return/XIRR may be added later.

### 8.4 Cost basis

Use weighted-average cost in v1. Do not mix FIFO and weighted average across modules.

### 8.5 Corporate actions

The data model and accounting engine must accommodate:

- Cash dividends.
- Withholding tax.
- Stock splits.
- Reverse splits.
- Symbol changes.
- Delisting events.
- Fees and rebates.

---

## 9. Strategy plugin architecture

### 9.1 Strategy interface

```python
class Strategy(ABC):
    name: str
    version: str

    def required_history(self) -> HistoryRequirement: ...
    def calculate_indicators(self, context: StrategyContext) -> IndicatorSet: ...
    def calculate_score(self, context: StrategyContext) -> ScoreResult: ...
    def generate_signal(self, context: StrategyContext) -> SignalResult: ...
    def explain_signal(self, context: StrategyContext) -> SignalExplanation: ...
```

Strategy output must be canonical and explainable:

- `security_id`
- `timestamp`
- `data_as_of`
- `strategy_name`
- `strategy_version`
- `score`
- `score_status`
- `data_coverage`
- `missing_components`
- `signal`
- `confidence`
- `target_weight`
- `reason`
- `risk_flags`

New strategies must be added through `StrategyRegistry` without changing PortfolioEngine.

### 9.2 Strategy assignment

Each security can use a strategy and parameter set stored in the database.

Example:

```json
{
  "ma_fast": 50,
  "ma_slow": 200,
  "drawdown_window": 60
}
```

---

## 10. AIInfraStrategy v1

### 10.1 Composite model

```text
Score = 0.30 × M6
      + 0.20 × M3
      + 0.20 × Trend
      + 0.15 × Drawdown
      + 0.15 × Valuation
```

Each component is normalized to 0–100.

Interpretation:

- `80–100`: STRONG BUY CANDIDATE.
- `65–79`: ACCUMULATE candidate.
- `50–64`: WATCH.
- `<50`: AVOID / NO BUY.

Score alone must never submit an order.

### 10.2 Strategy formula approval gate

Before implementing `AIInfraStrategy`, Phase 0 must create `docs/STRATEGY_SPEC.md` and define, with formulas and golden examples:

- M3 period definition, recommended baseline: 63 trading days.
- M6 period definition, recommended baseline: 126 trading days.
- Simple versus log-return choice.
- Realized-volatility window and annualization.
- Exact risk-adjusted momentum formula.
- Exact 0–100 normalization method.
- Own-history lookback and minimum sample size.
- Winsorization/clipping.
- Trend scoring function.
- Drawdown scoring function.
- Valuation scoring function.
- Data-coverage logic.
- Entry/add/hold/reduce/exit/cooldown/re-entry rules.
- Golden deterministic test cases.

Do not invent an arbitrary normalization and immediately encode it. The strategy specification must be reviewed and approved first.

`APPROVE PHASE 1` authorizes foundation implementation only and does not approve strategy formulas. Before any Phase 3 strategy implementation, the user must separately send the exact instruction:

`APPROVE STRATEGY SPEC V1`

Until then, `STRATEGY_SPEC.md` remains `PROPOSED / RESEARCH_UNVALIDATED`.

Absolute scores should primarily use each security's own historical distribution. With only three tracked securities, cross-sectional ranking must be used only as a relative-priority overlay, not as the primary score.

### 10.3 M3 and M6

M3 and M6 are risk-adjusted momentum measures. They must expose:

- Raw return.
- Realized volatility.
- Risk-adjusted momentum.
- Normalized score.
- Data coverage.

### 10.4 Trend

Minimum indicators:

- Current price.
- MA20.
- MA50.
- MA200.

Primary entry filter:

```text
Price > MA200
AND
MA50 > MA200
```

Price below MA200 and MA50 below MA200 must materially reduce the score and/or block entry according to the approved strategy specification.

### 10.5 Drawdown

```text
Drawdown = (Current Price - 60-day High) / 60-day High
```

Initial reference pullback zones:

- AVGO: approximately -7% to -15%.
- VRT: approximately -10% to -18%.
- HK.09698: approximately -12% to -25%.

These are parameter defaults, not automatic buy levels. Drawdown must be evaluated with ATR and historical volatility. The desired setup is `uptrend + healthy pullback`, not a falling knife.

### 10.6 Valuation

Valuation may use, when reliable and point-in-time data is available:

- Forward P/E.
- EV/EBITDA.
- FCF yield.
- Growth-adjusted valuation.
- Balance-sheet metrics.
- The company's own historical valuation range.

Conceptual weight inside the Valuation component:

- 40% historical valuation percentile.
- 30% growth-adjusted valuation.
- 20% FCF/capital efficiency.
- 10% balance sheet.

Missing fields must not be fabricated.

"Cheap" must not mean only that price fell or P/E is low. A valuation improvement requires price/valuation compression without proportionate deterioration in earnings, FCF, balance sheet, or competitive position.

### 10.7 Data coverage gate

Every score must expose data quality.

Suggested baseline status:

- `COMPLETE`: coverage >= 80%.
- `PARTIAL`: 60% <= coverage < 80%.
- `INVALID`: coverage < 60%.

Rules:

- Only `COMPLETE` may produce BUY/ACCUMULATE.
- `PARTIAL` may produce at most WATCH.
- `INVALID` must produce NO SIGNAL.
- Missing price, trading calendar, required trend data, or required FX blocks an executable recommendation.
- Missing valuation or fundamental data blocks automatic execution and requires manual review.

The exact coverage calculation must be defined in `STRATEGY_SPEC.md`.

### 10.8 Confirmation layer

After score and data-quality gates pass, require at least one approved confirmation signal, such as:

1. Price reclaims MA20.
2. Two consecutive sessions without a new low, followed by a break above the prior session high.
3. Break above the previous five-session high.

Without confirmation, status is `WAITING_FOR_CONFIRMATION`.

### 10.9 Dual-momentum filter

Compare 3-month and 6-month absolute and relative momentum across AVGO, VRT, and HK.09698.

If absolute momentum is materially negative, underperforms the cash/short-duration opportunity cost, and trend is deteriorating, reduce priority or block entry even after a large drawdown.

Dual momentum is a risk filter and relative-priority overlay, not a mechanical monthly rotation system.

### 10.10 Fundamental veto

Potential veto conditions:

- Material deterioration in AI CapEx or customer demand.
- Significant order/guidance decline.
- Large EPS-consensus downgrade.
- FCF deterioration.
- Material balance-sheet, accounting, regulatory, governance, or competitive-position risk.

In v1, the veto is manual or data-assisted and must include source/provenance. A veto blocks new buys. It must not automatically liquidate a live holding without a separately approved exit decision.

### 10.11 Strategy state machine and sell logic

The strategy must not implement only entry logic.

Define and test a state machine similar to:

```text
WATCH
  -> ENTRY_READY
  -> TRANCHE_1
  -> TRANCHE_2
  -> TRANCHE_3
  -> HOLD
  -> REDUCE
  -> EXIT
  -> COOLDOWN
  -> WATCH
```

`STRATEGY_SPEC.md` must define:

- Entry rule.
- Add rule.
- Stop-adding rule.
- Hold rule.
- Trend-based reduce/exit rule.
- Fundamental-risk response.
- Portfolio-risk response.
- Rebalance rule.
- Cooldown and re-entry rule.

For safety, strategy output is a recommendation. It does not autonomously execute live trades.

### 10.12 Position sizing and legal order quantity

The primary sizing formula is `DECISION_REQUIRED`. At minimum, the approved decision must compare:

1. **Option A — hard-stop risk-budget sizing.** Quantity is derived from risk budget divided by an approved stop distance. This option requires a corresponding stop policy that is actually enforced; otherwise its output must not be described as a guaranteed maximum loss.
2. **Option B — target-allocation sizing with volatility scaling.** The 40%/35%/25% values remain maximum allocations, while ATR14 and/or historical volatility scales a target below the cap. This is the recommended default for the long-only staged investment strategy.

A stress-loss/risk-budget check may remain as a secondary cap under Option B, but it is not a guaranteed loss limit without an enforced stop.

Initial maximum allocation reference:

- AVGO: 40% / HKD 8,000.
- VRT: 35% / HKD 7,000.
- HK.09698: 25% / HKD 5,000.

These are caps, not required target holdings. Cash may remain 100%.

Default tranches within a target allocation:

- Tranche 1: 30%.
- Tranche 2: 30%.
- Tranche 3: 40%.

Discrete quantities use cumulative legal targets rather than independently flooring three order quantities:

- calculate the legal cumulative target after tranche 1;
- calculate the legal cumulative target after tranche 2;
- tranche 3 cumulative target equals the full legal target;
- next order quantity equals the current legal cumulative target minus confirmed cumulative filled quantity.

Small targets may adapt into fewer executable tranches but must never exceed total legal target, settled cash, allocation cap, or approved risk limit. Explain adjustments with `SMALL_TARGET_SINGLE_TRANCHE` or `DISCRETE_TRANCHE_ADJUSTMENT`.

A one-share/one-lot 50% reduction must not create a zero-quantity fictional order. Return `REDUCE_NOT_EXECUTABLE_DUE_TO_LOT_SIZE` and require a separately approved choice between `HOLD_REVIEW` and full `EXIT`.

PositionSizer must convert theoretical capital to a legal order quantity using broker capabilities and security metadata.

It must never round above available cash, allocation cap, or any risk constraint selected by the separately approved sizing policy.

If the intended amount cannot buy the minimum legal unit, return:

`INSUFFICIENT_CAPITAL_FOR_MINIMUM_ORDER`

and keep the capital in cash.

---

## 11. Backtest correctness

Backtests must defend against:

- Look-ahead bias.
- Data leakage.
- Future functions.
- Survivorship bias.
- Incorrect corporate-action handling.
- Impossible same-bar execution.
- Ignoring transaction costs.
- Ignoring FX.
- Ignoring exchange calendars and time zones.

Required baseline:

1. Indicators use only data known at signal time.
2. A signal generated at Day T close cannot assume a fill at the same close.
3. Default model: `signal at T close -> fill at T+1 open`, unless another explicitly documented next-bar model is selected.
4. Include commission, platform fee, stamp duty where applicable, slippage, minimum commission, and FX cost.
5. Distinguish raw and adjusted prices and preserve splits/dividends/corporate actions.
6. Use correct HK and US calendars/time zones.
7. Every strategy run records `data_as_of`, provider, data version, strategy version, parameters, and execution assumption.
8. Historical fundamental/valuation data must be point-in-time and cannot use information published later.
9. Report before-cost and after-cost return, turnover, trades, exposure, cash ratio, drawdown, and benchmark comparison.
10. Unit tests must prove that signal and fill timing do not leak future data.

Backtest, paper, and live environments must invoke the same strategy object and canonical signal model.

---

## 12. Futu integration

Futu is the first real broker/data adapter.

Architecture:

```text
Frontend -> FastAPI -> Quant Core -> Futu adapter -> OpenD -> Futu
```

Default OpenD configuration, read from environment:

```text
FUTU_HOST=127.0.0.1
FUTU_PORT=11111
```

Implement one shared `FutuConnectionManager` for quote/trade context lifecycle, connectivity, timeout, retry policy, logging, and correct close/disconnect behavior.

Implementation order:

1. No Futu SDK dependency in Phase 0/1 unless the phase plan explicitly requires it.
2. Read-only market data.
3. Read-only account, cash, position, order, and fill reconciliation.
4. Disabled live-trading adapter.
5. Live safety controls and manual order approval.

Any `from futu import ...` must remain inside `integrations/futu/`.

If OpenD is unavailable, the application must still start and display `FUTU OFFLINE`.

No password, trade unlock credential, account ID, or token may be hard-coded or committed.

---

## 13. EastMoney and future brokers

The architecture must support a replaceable EastMoney adapter, but implementation must be truthful.

If there is no selected official, legitimate, stable trading interface:

- Create interfaces, symbol mapping, capability declarations, and a skeleton.
- Return `NOT_IMPLEMENTED` for unsupported live functions.
- Do not use brittle undocumented endpoints or UI automation and present them as a production broker adapter.

Market data and broker execution remain separate, so an EastMoney execution account may use another market-data provider.

---

## 14. PaperBroker

PaperBroker must behave like a broker account, not like editable UI state.

Required capabilities:

- Deposit and withdrawal.
- FX transactions.
- Orders and fills.
- Partial fills if the execution simulator supports them.
- Positions and weighted-average cost.
- Realized and unrealized P&L.
- Commissions, taxes, and slippage.
- Cash reservation on open orders.
- Persistence across restart.

Synthetic fixtures are allowed for unit/integration tests only. They must be clearly marked and must never be displayed as real production market data or used to issue a real recommendation.

Phase 2 does not yet have an automatic market-data matching source. It therefore implements accounting, order lifecycle, and explicitly user-supplied/manual simulation fills only. Every manual fill price is labelled `MANUAL_SIMULATION_PRICE` and stores price, currency, `observed_at`, `available_at`, actor, and source. PaperBroker must not invent a price or claim a market/limit fill without an identified observation. Automatic market/limit matching begins no earlier than Phase 3 after an approved historical/manual market-data path exists.

---

## 15. Live-trading safety

v1 live scope:

- Single user.
- Long only.
- Cash account.
- No margin.
- No shorting.
- No options/futures.
- `AUTO_EXECUTION=false`.
- Manual approval for every order.

Required server-side controls:

- Live route disabled or returns 403/404 unless `TRADING_MODE=LIVE` and all safety prerequisites pass.
- Authentication and authorization for any live endpoint.
- CSRF protection where browser session authentication is used.
- Persistent kill switch.
- Position-size limit.
- Daily order-value limit.
- Portfolio exposure limit.
- Duplicate-order/idempotency protection.
- Invalid-price protection.
- Market-status check.
- Available and settled cash check.
- Currency check.
- Stale-market-data check.
- Broker-connectivity check.
- Explicit order confirmation.
- Reconciliation after startup/reconnect:
  - open orders,
  - fills,
  - positions,
  - cash.

A broker submission acknowledgement does not update holdings. Only confirmed fills do.

---

## 16. Database minimum schema

Phase 0 must propose normalized tables and relationships for at least:

- `securities`
- `provider_symbol_mappings`
- `watchlists`
- `strategy_definitions`
- `strategy_assignments`
- `strategy_runs`
- `signals`
- `recommendations`
- `broker_profiles`
- `broker_accounts`
- `portfolios`
- `portfolio_accounts`
- `cash_balances`
- `cash_reservations`
- `cash_flows`
- `fx_transactions`
- `settlements`
- `orders`
- `fills`
- `positions`
- `ledger_entries`
- `portfolio_snapshots`
- `market_prices`
- `fx_rates`
- `fundamental_records`
- `valuation_snapshots`
- `corporate_events`
- `risk_flags`
- `performance_series`
- `settings`

Use migrations. Do not rely on ad hoc table creation once implementation begins.

---

## 17. API surface

Phase 0 must define versioned API contracts. Suggested baseline:

```text
GET    /api/v1/portfolio
GET    /api/v1/positions
GET    /api/v1/performance
GET    /api/v1/watchlist
POST   /api/v1/watchlist
DELETE /api/v1/watchlist/{security_id}
POST   /api/v1/securities
GET    /api/v1/securities/{security_id}
GET    /api/v1/securities/{security_id}/indicators
GET    /api/v1/securities/{security_id}/score
GET    /api/v1/signals
GET    /api/v1/strategies
POST   /api/v1/strategies/run
POST   /api/v1/paper/deposit
POST   /api/v1/paper/withdraw
POST   /api/v1/paper/fx
POST   /api/v1/paper/orders
GET    /api/v1/orders
GET    /api/v1/brokers
GET    /api/v1/brokers/{broker}/status
GET    /api/v1/brokers/{broker}/accounts
GET    /api/v1/market-data/providers
POST   /api/v1/live/orders
POST   /api/v1/live/kill-switch
```

Do not expose a functioning live route before the live-safety phase.

---

## 18. Frontend requirements

Style:

- Professional quant-terminal look.
- Dark mode.
- High information density without visual clutter.
- Responsive enough for a desktop browser.

Dashboard summary:

- Portfolio value.
- Today P&L.
- Total P&L.
- Return since 2026-08-31.
- NAV.
- Maximum drawdown.
- Cash %.
- Invested %.

Charts:

- Portfolio NAV.
- Optional benchmarks: AVGO, VRT, HK.09698 buy-and-hold.
- Ranges: 1D, 1W, 1M, 3M, YTD, since inception.

Security cards:

- Price and daily change.
- Return since inception date.
- Current and maximum weight.
- Score and score status.
- M6, M3, Trend, Drawdown, Valuation components.
- Data coverage/missing components.
- Signal and confirmation status.
- MA20, MA50, MA200, ATR14, 60-day high, drawdown.
- Available valuation fields with provenance.
- Explanation and risk flags.

Recommendation panel:

- Action.
- Suggested HKD capital.
- Portfolio percentage.
- Legal estimated quantity.
- Tranche number.
- Trigger and confirmation.
- Risk flags.
- Post-trade allocation and remaining cash.

Paper and live actions must be visually and functionally separated. Live status must be unmistakable.

---

## 19. Testing and quality gates

Use pytest. Phase 0 must recommend lint/type-check tools; Phase 1 must configure them.

At minimum, test:

- Decimal-safe accounting.
- Exact dialect-aware SQLite decimal round trips for required extreme/fractional values, range validation, numeric ordering behavior, and Python-Decimal ledger balancing without SQLite text arithmetic.
- MA20/MA50/MA200.
- ATR14.
- 60-day drawdown.
- M3/M6 calculations.
- Score normalization and data coverage.
- Missing valuation handling.
- Confirmation logic.
- Fundamental veto.
- Dual momentum.
- Strategy state transitions.
- The separately approved position-sizing formula, including ATR inputs if the approved option uses them.
- Legal order rounding, lot size, and fractional capability.
- Cumulative legal tranche targets for one share, two shares, fractional quantity, HK board lot, and one-share/one-lot reduce.
- Weighted-average cost.
- Realized/unrealized P&L.
- FX conversion and FX P&L.
- Deposit/withdrawal not changing NAV/TWR.
- External flow rejection with `PORTFOLIO_VALUATION_UNAVAILABLE` when any position mark or required FX observation is missing.
- Unit issuance/redemption.
- Corporate actions.
- Broker canonical responses.
- Risk rejection.
- Duplicate-order prevention.
- Order reconciliation.
- No future-data leakage.
- User-supplied unverified security creation, uniqueness, truthful metadata state, and strategy/order blocking.
- Missing/stale valuation or fundamental inputs produce `HOLD_REVIEW`, never a score-based REDUCE.

Synthetic fixtures are allowed under `tests/fixtures/` but must never enter production tables as real data.

A phase is not complete until its application path runs and all phase-relevant tests, lint, and type checks pass or the report clearly documents an external blocker.

---

## 20. Configuration and secrets

Create `.env.example`, for example:

```dotenv
APP_ENV=development
DATABASE_URL=sqlite:///./data/ai_infra_quant.db
TRADING_MODE=PAPER
AUTO_EXECUTION=false
ACTIVE_BROKER=paper
MARKET_DATA_PROVIDER=futu
FUNDAMENTAL_DATA_PROVIDER=manual
EVENT_DATA_PROVIDER=manual
FUTU_HOST=127.0.0.1
FUTU_PORT=11111
API_BASE_URL=http://127.0.0.1:8000
```

Never include real credentials, account IDs, trade unlock passwords, private keys, or tokens.

`.gitignore` must exclude at least:

- `.env`
- local databases
- logs
- caches
- generated secrets
- broker exports containing private account data

---

## 21. Git and change-control rules

Before each implementation phase:

- Run `git status`.
- Identify unrelated existing changes.
- Show the planned files to modify.
- Create a local checkpoint if safe.

Without explicit user approval, do not:

- `git push`.
- Force-push.
- Change remotes.
- Change global Git config.
- Commit `.env`, databases, logs, secrets, credentials, or private account exports.
- Revert unrelated user changes.

If the repository is not initialized or Git identity is unavailable, report it. Do not modify global configuration silently.

---

## 22. GitHub and deployment boundaries

GitHub is used for source control, issues, pull requests, and CI.

GitHub Pages may host only a read-only/static demonstration that contains no credentials, private account data, broker connectivity, backend database, or live order capability.

Local-first v1:

```text
Browser -> local frontend -> FastAPI -> SQLite -> PaperBroker
```

Later Futu path:

```text
Browser -> trusted FastAPI backend -> Futu adapter -> OpenD -> Futu
```

The frontend must never connect directly to OpenD.

Production API base URL is configured, not hard-coded. Production CORS must not be unconditionally open.

Any public frontend may connect only to an authenticated HTTPS backend. Live-control pages should remain private/local by default.

---

## 23. Implementation phases

### Phase 0 — Design review and specification freeze

No business functionality.

Deliver:

- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/DATABASE_SCHEMA.md`
- `docs/API_CONTRACTS.md`
- `docs/STRATEGY_SPEC.md`
- `docs/REQUIREMENTS_MATRIX.md`
- `docs/phases/PHASE_1_PLAN.md`

Resolve/report contradictions and open design decisions. Stop and wait for `APPROVE PHASE 1`.

`APPROVE PHASE 1` authorizes Phase 1 foundation work only. It does not approve `STRATEGY_SPEC.md`; strategy approval uses the separate exact instruction `APPROVE STRATEGY SPEC V1` before Phase 3.

### Phase 1 — Foundation and contracts

Implement:

- Project skeleton and packaging.
- Configuration and logging.
- SQLAlchemy and migrations.
- Canonical domain models.
- Security master and provider mappings.
- Broker/market-data/fundamental/event interfaces.
- Registries/factories.
- Capability models.
- Minimal portfolio/account entities.
- Initial AI Infra portfolio, HKD 20,000 cash, NAV 100.
- Security creation for user-supplied unverified canonical securities.
- Watchlist CRUD for seeded or user-created securities.
- Minimal read-only financial dashboard/API plus canonical-security creation and watchlist administration; no financial mutation route.

Do not implement live integration or full paper execution.

Phase 1 acceptance:

- Application starts.
- Database initializes through migrations.
- Initial portfolio and watchlist exist.
- A new user-supplied security can be created and added to the watchlist while remaining blocked from strategy/orders until verified.
- Watchlist can be added/removed.
- Broker/provider boundaries are demonstrably decoupled.
- Missing data is shown truthfully.
- Tests/lint/type checks pass.

Stop and wait for `APPROVE PHASE 2`.

### Phase 2 — Paper broker and accounting

Implement:

- PaperBroker.
- ExecutionEngine baseline.
- RiskManager baseline.
- Orders, explicitly user-supplied/manual simulation fills with full price provenance, and positions.
- Multi-currency cash and explicit/auto FX.
- Cash reservation and settlement model.
- Deposits/withdrawals.
- Weighted-average cost.
- Unitized NAV and TWR.
- P&L and performance snapshots.
- Paper buy/sell UI.

Automatic market/limit matching is out of Phase 2 scope. Deposits/withdrawals after positions exist require a complete `FLOW_PRE` snapshot or fail with `PORTFOLIO_VALUATION_UNAVAILABLE`.

Stop and wait for `APPROVE PHASE 3`.

### Phase 3 — Market data, indicators, and AIInfraStrategy

Implement only after the exact separate instruction `APPROVE STRATEGY SPEC V1` has approved `STRATEGY_SPEC.md`:

- Historical market-data interface implementation.
- Trading calendars/time zones.
- MA, ATR, drawdown, M3, M6.
- Valuation/manual fundamental data path with provenance.
- AIInfraStrategy score, coverage gate, confirmation, dual momentum, veto, state machine.
- The separately approved sizing formula and legal order-quantity calculation; do not infer approval of either OD-006 option from this phase label.
- Recommendation panel and strategy explanations.
- Automatic paper market/limit matching only against an approved, provenance-bearing market-data path.

Stop and wait for `APPROVE PHASE 4`.

### Phase 4 — Backtest engine

Implement:

- Shared strategy execution path.
- T-close/T+1-open default fill model.
- Fees, slippage, FX, calendars, corporate actions.
- Buy-and-hold benchmarks.
- Before/after-cost statistics.
- Anti-look-ahead tests.

Backtest completion does not establish profitability or predictive validity. `AIInfraStrategy` remains `RESEARCH_UNVALIDATED` through Phase 4 and until adequate subsequent forward observation is reviewed.

Stop and wait for `APPROVE PHASE 5`.

### Phase 5 — Futu read-only integration

Implement:

- `FutuConnectionManager`.
- Futu market-data adapter.
- Read-only account, cash, position, order, and fill access.
- Startup/reconnect reconciliation reports.
- Offline-safe behavior.

No live order submission.

Stop and wait for `APPROVE PHASE 6`.

### Phase 6 — Disabled Futu trading adapter

Implement canonical order conversion and broker response mapping, but keep live trading server-side disabled. Validate against paper/simulation or Futu's supported test environment where available.

Stop and wait for `APPROVE PHASE 7`.

### Phase 7 — Live safety and controlled manual execution

Implement authentication/authorization, kill switch, idempotency, limits, stale-data checks, reconciliation, manual confirmation, and complete audit logging.

Live mode remains disabled until the user separately authorizes enabling it after review.

### Phase 8 — EastMoney adapter decision and implementation

Evaluate legitimate supported interfaces. Implement a real adapter only if a stable, lawful integration path is selected. Otherwise retain a truthful skeleton.

---

## 24. Phase completion protocol

For every phase:

1. Read `AGENTS.md`, this master specification, architecture docs, strategy spec, and current phase plan.
2. Run `git status` and identify unrelated changes.
3. State the planned file changes before editing.
4. Implement current phase only.
5. Run the application or relevant executable path.
6. Run pytest.
7. Run lint.
8. Run type checking.
9. Fix current-phase failures.
10. Update documentation and requirements matrix.
11. Report exact commands and results.
12. Report changed files, completed requirements, known limitations, and external blockers.
13. Create a local Git checkpoint only if safe.
14. Stop. Do not start the next phase without explicit approval.

Never claim completion without actually running the stated validation commands.

---

## 25. Phase 3 MVP acceptance target

After Phase 3, opening the browser should show:

- `AI INFRA QUANT`.
- Portfolio value: HKD 20,000 plus/minus actual paper activity.
- NAV starting from 100.00.
- Return and drawdown.
- Cash and invested percentages.
- AVGO, VRT, and HK.09698 watchlist cards.
- Truthful data/connection status.
- Indicators, score components, data coverage, signal, and explanation where data exists.
- Add/remove security.
- Deposit/withdraw.
- Paper buy/sell.
- Positions, orders, fills, cash flows, NAV, and P&L.
- Strategy recommendation and legal tranche sizing.

---

## 26. Final design philosophy

The system does not exist to predict tomorrow's price or mechanically buy every RSI/drawdown signal.

Desired decision pipeline:

```text
Fundamental quality and data quality
        -> Trend filter
        -> Risk-adjusted momentum
        -> Healthy pullback
        -> Valuation
        -> Confirmation
        -> Fundamental/risk veto
        -> Volatility-adjusted position size
        -> Legal order quantity
        -> Staged entry
        -> Portfolio accounting
        -> Performance evaluation
```

The system should explain whether the current action is:

- BUY
- ACCUMULATE
- HOLD
- WATCH
- REDUCE
- EXIT
- AVOID
- STAY IN CASH

All live execution remains a separate, explicitly approved action.
