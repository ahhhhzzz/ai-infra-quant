# Database Schema Specification

Status: Phase 0 design freeze candidate

Initial database: SQLite through SQLAlchemy and Alembic

Migration target: PostgreSQL without changing domain semantics

## 1. Conventions and invariants

### 1.1 Keys and names

- Table names and columns use `snake_case`; table names are plural.
- Platform primary keys are UUIDs. SQLite stores canonical UUID text; PostgreSQL may use native UUID without changing API/domain values.
- External/provider identifiers are never primary keys. They are scoped by provider/profile and protected from normal API responses.
- Every foreign key is indexed when it participates in a lookup. Delete behavior defaults to `RESTRICT`. Domain records are disabled or superseded, not cascade-deleted.
- Mutable projections carry `version INTEGER NOT NULL DEFAULT 1` for optimistic concurrency and `updated_at`.

### 1.2 Time

- `created_at`, `updated_at`, `observed_at`, `available_at`, `data_as_of`, and similar instants are timezone-aware UTC.
- Market sessions use an ISO date plus the security's IANA timezone and trading-calendar identifier.
- Point-in-time queries require `available_at <= :data_as_of`. `period_end` or `effective_at` alone never proves that information was knowable.

### 1.3 Decimal storage

Binary floating point is forbidden for financial values in domain code, persistence bindings, fixtures, and API requests.

The logical exact type for v1 is precision 38, scale 18. It covers amounts, prices, quantities, FX/adjustment rates, ratios/returns, NAV, and raw/gate scores. Currency-specific or UI scales are presentation rules only; gate/accounting values are not rounded to four or eight places before persistence.

The semantic aliases `DECIMAL_AMOUNT`, `DECIMAL_PRICE`, `DECIMAL_QUANTITY`, `DECIMAL_RATE`, `DECIMAL_RATIO`, and `DECIMAL_SCORE` all use this exact logical type in v1. Their names communicate domain meaning, not different SQLite affinities or lossy scales.

| Dialect | Physical type | Binding/result behavior |
|---|---|---|
| SQLite | `TEXT` with TEXT affinity, never `NUMERIC` affinity | Custom SQLAlchemy `ExactDecimal(38,18)` `TypeDecorator` writes a validated fixed-scale canonical string and parses it directly to `Decimal`; it must never pass through float, SQLite numeric coercion, `CAST(... AS NUMERIC)`, or driver-side float conversion. |
| PostgreSQL | `NUMERIC(38,18)` | The same TypeDecorator selects native `Numeric(38,18, asdecimal=True)` and returns `Decimal`. |

SQLite canonical storage format is an optional leading `-`, exactly 20 integer digits, a decimal point, and exactly 18 fractional digits, for example `00000000000000000100.000000000000000001`. Positive values have no `+`; negative values have exactly one leading `-`. The application/API canonical decimal string may omit storage-only leading zero padding.

`ExactDecimal` accepts only `Decimal` or canonical decimal input strings. It rejects floats, booleans, NaN/infinity, exponent notation at the persistence boundary, more than 18 fractional digits, and values outside `-99999999999999999999.999999999999999999` through `99999999999999999999.999999999999999999`. It does not silently quantize an over-scale value. Values with fewer fractional digits are padded exactly on storage.

SQLite lexical ordering is not treated as signed numeric ordering. Repositories first restrict by indexed non-decimal keys/time and then compare/order exact values as Python `Decimal` inside the Unit of Work. SQL `SUM`, `AVG`, arithmetic, numeric `CAST`, and decimal `ORDER BY`/range predicates over these TEXT columns are prohibited unless a later separately specified exact sortable representation is added. PostgreSQL may use native exact numeric operations.

The required SQLite round-trip vectors are:

- `100.000000000000000001`
- `12345678901234567890.123456789012345678`
- `0.123456789012345678`

Tests must prove identical `Decimal.as_tuple()` values after round trip, correct Python-Decimal ordering (including negative/zero/positive and large values), range/scale rejection, `typeof(column)='text'`, and absence of a float anywhere in binding/results.

### 1.4 Currency and rate direction

- Currency columns are uppercase ISO-4217 `CHAR(3)` values.
- An FX pair `(base_currency, quote_currency)` and `rate` means one base unit equals `rate` quote units.
- Every conversion stores the exact applied rate, source, observation/availability times, spread, fee, and reporting-base rate. No conversion uses a later “current” rate when reproducing history.

### 1.5 Enumerations and missing data

Stable domain enums are string values protected with portable `CHECK` constraints where practical. Unknown vendor values are retained in adapter raw/provenance data and mapped to `UNKNOWN`; they do not cause a guessed platform state.

Data-status values are `AVAILABLE`, `MISSING`, `UNAVAILABLE`, `NOT_SUPPORTED`, and `INVALID`. Capability status is `SUPPORTED`, `NOT_SUPPORTED`, `NOT_IMPLEMENTED`, `UNAVAILABLE`, or `UNKNOWN`.

### 1.6 Immutability

These tables are append-only after insert: `ledger_transactions`, `ledger_entries`, `unit_transactions`, `cash_flows` after posting, `fx_transactions` after posting, `order_events`, `fills`, posted `settlements`, `market_prices`, `fx_rates`, `fundamental_records`, `valuation_snapshots`, `corporate_events`, `strategy_runs`, `signals`, `recommendations`, `portfolio_snapshots`, and published `performance_series` points.

Correction means an explicit reversal/superseding row linked to the original. Database repository methods expose no update/delete operation for immutable rows. SQLite triggers added with the relevant migration reject `UPDATE` and `DELETE` on posted ledger entries/transactions, fills, posted cash flows/FX, and unit transactions. PostgreSQL migrations preserve the same rule.

SQLite append-only triggers protect immutability only. They do not use TEXT arithmetic to assert a balanced ledger. The Unit of Work constructs all ledger entries, sums debit/credit base amounts with Python `Decimal`, validates exact equality and domain constraints, and commits the transaction atomically only if balanced. Direct database writes outside repositories are unsupported.

`cash_balances`, `positions`, and current order/reservation state are mutable projections. They are rebuildable from immutable facts and store the last applied ledger/event sequence.

## 2. Relationship overview

```text
securities --< provider_symbol_mappings
          \--< watchlist_items >-- watchlists -- portfolios
          \--< strategy_assignments >-- strategy_definitions
          \--< market_prices / fundamental_records / valuation_snapshots
          \--< positions / orders / fills / corporate_events / risk_flags

broker_profiles --< broker_accounts --< portfolio_accounts >-- portfolios
broker_accounts --< cash_balances / cash_reservations / orders / positions

portfolios --< cash_flows / unit_transactions / portfolio_snapshots
           \--< strategy_runs --< signals --< recommendations --< orders
           \--< ledger_accounts --< ledger_entries >-- ledger_transactions

orders --< order_events
orders --< fills --< settlements
fills/cash_flows/fx_transactions/corporate actions -> ledger_transactions
ledger facts -> cash_balances / positions / snapshots -> performance_series
```

A portfolio may contain many broker accounts. In v1 an active broker account belongs to at most one portfolio, preventing double-counting. A future partitioned-account design requires an explicit allocation ledger and is not implied by the many-to-many join table.

## 3. Security, watchlist, and provider identity

### 3.1 `securities`

| Column | Type/constraint |
|---|---|
| `id` | UUID PK |
| `market`, `symbol` | text, both non-empty; unique together |
| `exchange` | text, nullable only when truthfully unknown |
| `currency` | `CHAR(3)` |
| `display_name` | text |
| `instrument_type` | enum (`EQUITY`, `ETF`, `UNKNOWN`) |
| `enabled` | boolean default true |
| `lot_size`, `min_order_quantity`, `quantity_step`, `fractional_quantity_step` | `DECIMAL_QUANTITY`, positive when present |
| `tick_size`, `min_notional` | `DECIMAL_PRICE` / `DECIMAL_AMOUNT`, positive when present |
| `fractional_supported` | boolean; false does not imply odd lots are supported |
| `market_timezone` | IANA timezone text |
| `trading_calendar` | versioned calendar identifier |
| `metadata_status` | data-status enum |
| `record_source` | `SYSTEM_SEED` or `USER_SUPPLIED` |
| `verification_status` | `VERIFIED`, `SYSTEM_SEED_UNVERIFIED`, or `USER_SUPPLIED_UNVERIFIED` |
| `tradability_status` | `VERIFIED`, `UNVERIFIED`, `NOT_SUPPORTED`, or `DISABLED` |
| `created_at`, `updated_at`, `version` | audit/concurrency |

Initial rows are configurable seed data for `(US, AVGO)`, `(US, VRT)`, and `(HK, 09698)`. Lot/tick/minimum metadata remains null/`UNAVAILABLE` until verified; it is never guessed from the example symbol.

User-created rows normalize `market` and `symbol` to uppercase trimmed canonical values before the unique `(market, symbol)` check. `currency` is exactly three uppercase ASCII letters and `instrument_type` is restricted to the public creation enum. A new user row is always `record_source=USER_SUPPLIED`, `verification_status=USER_SUPPLIED_UNVERIFIED`, and `tradability_status=UNVERIFIED`; the request cannot override those values. Provider mappings, exchange/calendar/timezone, lot/tick/minimum/fractional rules remain null/unavailable. Watchlist membership is allowed, but strategy runs and orders fail closed until required verification/provenance gates pass.

### 3.2 `provider_symbol_mappings`

- `id` UUID PK
- `security_id` FK `securities`
- `provider_type` enum (`BROKER`, `MARKET_DATA`, `FUNDAMENTAL`, `EVENT`)
- `provider_name`, `provider_symbol`
- `valid_from`, `valid_to` nullable UTC instants
- `mapping_status`, `source`, `retrieved_at`
- unique active mapping on `(security_id, provider_type, provider_name)`
- unique active reverse mapping on `(provider_type, provider_name, provider_symbol)`

### 3.3 `watchlists` and `watchlist_items`

`watchlists`: `id`, nullable `portfolio_id`, `name`, `is_default`, audit columns; unique `(portfolio_id, name)` and at most one default per portfolio.

`watchlist_items`: `id`, `watchlist_id`, `security_id`, `added_at`, nullable `removed_at`, `display_order`, optional non-secret `note`; only one active item per `(watchlist_id, security_id)`. Removal is a tombstone so historical membership is reproducible.

## 4. Strategy definitions and outputs

### 4.1 `strategy_definitions`

- `id` UUID PK
- `name`, `version`; unique together
- `implementation_key` (registry key, not import path supplied by a user)
- `parameter_schema_json`, `default_parameters_json`
- `definition_hash`
- `enabled`, `created_at`

Published definitions are immutable; a behavior change creates a new version.

### 4.2 `strategy_assignments`

- `id` UUID PK
- `security_id`, `strategy_definition_id`, optional `portfolio_id`
- `parameters_json`, `parameters_hash`
- `effective_from`, nullable `effective_to`
- `created_at`
- no overlapping active assignment for the same `(portfolio_id, security_id)`

Parameters are validated against the strategy's schema before insert. Decimal parameters are canonical strings in JSON and are converted to `Decimal` at the boundary.

### 4.3 `strategy_runs`

- `id` UUID PK
- `portfolio_id`, `strategy_definition_id`
- `run_mode` (`ANALYSIS`, `PAPER`, `BACKTEST`, `LIVE_RECOMMENDATION`)
- `started_at`, `completed_at`, `data_as_of`
- `provider_manifest_json`, `dataset_hash`, `parameters_hash`
- `strategy_name`, `strategy_version`, `execution_assumption_id`
- `status` (`RUNNING`, `COMPLETED`, `FAILED`, `INVALID_DATA`)
- nullable `error_code`; never store secrets/raw credentials in error text

### 4.4 `signals`

- `id` UUID PK
- `strategy_run_id`, `security_id`, `signal_at`, `data_as_of`
- nullable raw `score`, `score_lower_bound`, `score_upper_bound` (`ExactDecimal(38,18)` / PostgreSQL `NUMERIC(38,18)`)
- `score_status`, `data_coverage` (`DECIMAL_RATIO`)
- `missing_components_json`, `component_scores_json`
- `signal` enum, `confidence` (`DECIMAL_RATIO`), `target_weight` (`DECIMAL_RATIO`)
- `reason_json`, `risk_flags_json`, `strategy_state`, `confirmation_status`
- unique `(strategy_run_id, security_id)`

### 4.5 `recommendations`

- `id` UUID PK
- `signal_id`, `portfolio_id`, `security_id`
- `action`, `state_before`, `state_after_recommended`
- nullable `target_weight`, `suggested_base_amount`, `estimated_quantity`, `limit_price`
- `tranche_number`, `requires_manual_review`, `expires_at`
- `status` (`OPEN`, `ACCEPTED`, `REJECTED`, `EXPIRED`, `SUPERSEDED`)
- audit timestamps and optional user decision reason

A recommendation is not an order. Acceptance may create an order draft in a later phase through a separate use case.

## 5. Broker, account, and portfolio identity

### 5.1 `broker_profiles`

- `id` UUID PK
- unique `name`
- `adapter_key` (`paper`, `futu`, `eastmoney`, etc.)
- `environment` (`PAPER`, `SIMULATED`, `LIVE`, `READ_ONLY`)
- `implementation_status`, `enabled`
- `configuration_json` containing only non-secret settings
- `created_at`, `updated_at`, `version`

Credentials, unlock passwords, tokens, and private keys never enter this table.

### 5.2 `broker_accounts`

- `id` UUID PK (the canonical `account_id`)
- `broker_profile_id`
- nullable `external_account_id` and `external_account_id_hash`
- `display_label`, `account_type`, nullable `base_currency`
- `status`, `is_read_only`
- `last_reconciled_at`, audit/version columns
- unique `(broker_profile_id, external_account_id_hash)` where present

The plaintext external identifier is treated as private and excluded from normal API serialization/logging. An encryption-at-rest choice may be made with the live integration; Phase 1's paper account has no private external ID.

### 5.3 `portfolios`

- `id` UUID PK
- unique `name`
- `base_currency`
- `inception_date` (portfolio-local date), `valuation_timezone`, nullable `daily_cutoff_policy`
- `initial_nav` `DECIMAL_PRICE`
- `status`, audit/version columns

### 5.4 `portfolio_accounts`

- `id` UUID PK
- `portfolio_id`, `broker_account_id`
- `effective_from`, nullable `effective_to`
- `is_primary`
- unique active `broker_account_id` in v1

## 6. Accounting and cash

### 6.1 `ledger_accounts`

- `id` UUID PK
- `portfolio_id`, nullable `broker_account_id`, nullable `security_id`
- `account_code` and `account_type`
- nullable `currency`
- `normal_balance` (`DEBIT`, `CREDIT`)
- `active`, audit columns
- unique active logical key `(portfolio_id, broker_account_id, security_id, account_code, currency)`

Baseline account types include `CASH_ASSET`, `CASH_CLEARING`, `POSITION_COST_ASSET`, `DIVIDEND_RECEIVABLE`, `SETTLEMENT_RECEIVABLE`, `SETTLEMENT_PAYABLE`, `CONTRIBUTED_CAPITAL`, `REALIZED_PNL`, `UNREALIZED_PNL`, `DIVIDEND_INCOME`, `FX_PNL`, `FEE_EXPENSE`, `TAX_EXPENSE`, and `ROUNDING_ADJUSTMENT`.

### 6.2 `ledger_transactions`

- `id` UUID PK
- monotonic `sequence_no` unique
- `portfolio_id`
- `transaction_type` (`INITIAL_CONTRIBUTION`, `DEPOSIT`, `WITHDRAWAL`, `BUY_FILL`, `SELL_FILL`, `FX`, `FEE`, `TAX`, `DIVIDEND`, `CORPORATE_ACTION`, `SETTLEMENT`, `REVERSAL`, `ADJUSTMENT`)
- `effective_at`, `recorded_at`
- `source_type`, `source_id`, `idempotency_key`
- nullable `reverses_transaction_id`
- `description`, `created_by`
- unique `(portfolio_id, idempotency_key)`

Transactions cannot be edited. Reversal links cannot form a cycle, and the original may be reversed only once unless an explicitly versioned correction policy permits otherwise.

### 6.3 `ledger_entries`

- `id` UUID PK
- `ledger_transaction_id`, `ledger_account_id`
- `entry_no` unique within transaction
- `direction` (`DEBIT`, `CREDIT`)
- `amount` `DECIMAL_AMOUNT` greater than zero
- `currency`
- `base_currency`, `base_fx_rate` `DECIMAL_RATE`, `base_amount` `DECIMAL_AMOUNT`
- nullable `quantity` `DECIMAL_QUANTITY`, `unit_price` `DECIMAL_PRICE`, `security_id`
- `effective_at`, `created_at`

For every posted transaction, total debit `base_amount` equals total credit `base_amount`. Currency-specific clearing legs make each currency sub-ledger explainable. A declared rounding entry is the only allowed non-economic balancing adjustment and must be below the configured tolerance.

### 6.4 `cash_flows`

- `id` UUID PK
- `portfolio_id`, `broker_account_id`, `currency`
- `flow_type` (`INITIAL_CONTRIBUTION`, `DEPOSIT`, `WITHDRAWAL`)
- `amount` positive `DECIMAL_AMOUNT`; direction comes from type
- `effective_at`, `requested_at`, `posted_at`
- `idempotency_key`, `status`
- `base_fx_rate`, `base_amount`
- `pre_flow_nav`, `units_issued`, `units_redeemed`
- nullable `pre_flow_snapshot_id` FK `portfolio_snapshots`
- `ledger_transaction_id`, nullable `reverses_cash_flow_id`
- unique `(portfolio_id, idempotency_key)`

Posted rows are immutable. Withdrawals must not exceed available cash or redeem more than outstanding units.
After the initial issue, any external flow also requires positive pre-flow NAV and positive outstanding units. Same-instant flows are ordered by UTC effective time and immutable ledger sequence and each creates its own unit/TWR boundary.

When any position exists, `pre_flow_snapshot_id` is mandatory and must reference an official `FLOW_PRE` snapshot at the flow boundary with `quality_status=COMPLETE`, a valid mark for every position, and a valid FX observation for every required conversion. Missing/stale/incomplete valuation rejects the command atomically with `PORTFOLIO_VALUATION_UNAVAILABLE`; no cash-flow, ledger, or unit row is inserted.

### 6.5 `unit_transactions`

- `id` UUID PK
- `portfolio_id`, `cash_flow_id`
- `unit_event_type` (`INITIAL_ISSUE`, `ISSUE`, `REDEEM`, `REVERSAL`)
- `effective_at`
- `nav_per_unit` `DECIMAL_PRICE`
- `unit_quantity` positive `DECIMAL_QUANTITY`
- `base_amount` `DECIMAL_AMOUNT`
- nullable `reverses_unit_transaction_id`

`unit_quantity = base_amount / nav_per_unit` before declared quantization. Deposits issue and withdrawals redeem at the immediately pre-flow NAV. External flows therefore do not create investment return.

### 6.6 `fx_transactions`

- `id` UUID PK
- `portfolio_id`, `broker_account_id`, `mode` (`EXPLICIT_FX`, `AUTO_FX`)
- `sold_currency`, `sold_amount`; `bought_currency`, `bought_amount`
- `market_rate`, `applied_rate`, `spread_rate`, `fee_amount`, `fee_currency`
- `rate_source`, `rate_observed_at`, `rate_available_at`
- `trade_at`, `settlement_at`, `idempotency_key`, `status`
- `ledger_transaction_id`, optional `order_id`

`AUTO_FX` is present in the record, order/recommendation explanation, and API response. It may not be inferred silently from a cash deficit.

### 6.7 `cash_reservations`

- `id` UUID PK
- `broker_account_id`, `portfolio_id`, `order_id`, `currency`
- `amount` `DECIMAL_AMOUNT`
- `status` (`ACTIVE`, `PARTIALLY_RELEASED`, `RELEASED`, `CONSUMED`, `EXPIRED`)
- `reserved_at`, `expires_at`, `released_at`
- `version`, `last_event_sequence`
- at most one active reservation per order/currency

Reservation changes have an append-only accounting/order event source. The projection cannot make available cash negative.

### 6.8 `cash_balances`

- composite unique key `(broker_account_id, currency)` plus UUID PK
- `settled_amount`, `unsettled_receivable`, `unsettled_payable`, `reserved_amount` as `DECIMAL_AMOUNT`
- nullable `reported_buying_power` and `reported_at` for an external broker observation
- `as_of_ledger_sequence`, `updated_at`, `version`

Application-derived available cash is `settled_amount - reserved_amount`; projected total cash is settled plus receivables minus payables. Broker-reported buying power is labelled external and is not substituted for ledger cash.

### 6.9 `settlements`

- `id` UUID PK
- `portfolio_id`, `broker_account_id`
- `source_type`, `source_id` (fill, FX transaction, dividend, fee, etc.)
- `currency`, `amount`, `direction`
- `trade_at`, `due_at`, nullable `settled_at`
- `policy_id`, `status`, `ledger_transaction_id`
- unique `(source_type, source_id, currency, direction)` where one settlement is expected

Policy identifiers are versioned; market settlement rules are never inferred from symbol text.

## 7. Orders, fills, and position projections

### 7.1 `orders`

- `id` UUID PK (`internal_order_id`)
- unique `client_order_id`
- `idempotency_key`, unique within `broker_profile_id`
- `portfolio_id`, `account_id`, `broker_profile_id`, `security_id`
- `side` (`BUY`, `SELL`), `order_type` (`MARKET`, `LIMIT`)
- `quantity`, nullable `limit_price`, `currency`, `time_in_force`
- `created_at`, nullable `expires_at`
- nullable `strategy_run_id`, `recommendation_id`
- `current_state`, `filled_quantity`, `average_fill_price`
- nullable `external_order_id`, `last_event_sequence`
- `version`

The current-state fields are projections of `order_events` and fills. Sell quantity cannot exceed available long quantity; short/margin semantics have no enum path in v1.

### 7.2 `order_events`

- `id` UUID PK
- `order_id`, monotonic `sequence_no` per order
- `event_type`, `state_from`, `state_to`
- `occurred_at`, `recorded_at`
- `source` (`APPLICATION`, `BROKER`, `RECONCILIATION`, `USER`)
- nullable `external_event_id`, `reason_code`, redacted `details_json`
- unique `(order_id, sequence_no)` and provider-scoped external event uniqueness where present

Allowed states are those in `MASTER_SPEC.md`. Transition validation is owned by Execution; unknown broker status cannot skip to `FILLED` without a confirmed fill.

### 7.3 `fills`

- `id` UUID PK
- `order_id`, `broker_profile_id`, `account_id`, `portfolio_id`, `security_id`
- nullable `external_fill_id`
- `side`, `quantity`, `price`, `currency`
- `gross_amount`, `fee_amount`, `tax_amount`, `net_amount`
- `executed_at`, `received_at`, optional `settlement_due_at`
- `liquidity_flag`, `is_simulated`
- `price_source_type` (`MANUAL_SIMULATION_PRICE`, `MARKET_OBSERVATION`, `BROKER_CONFIRMED`)
- `price_source`, nullable `price_source_record_id`, `price_observed_at`, `price_available_at`, nullable `actor_id`
- `raw_payload_hash`, `ledger_transaction_id`
- unique provider-scoped external fill ID; otherwise unique deterministic fill fingerprint

Fills are immutable. One order may have many fills; the Python-Decimal Unit of Work must prove `sum(fill.quantity)` does not exceed order quantity before commit. In Phase 2, non-test fills must use `MANUAL_SIMULATION_PRICE`, include actor/source/price/currency/observed/available provenance, and cannot pretend to be market-matched. `MARKET_OBSERVATION` automatic matching begins no earlier than Phase 3. Synthetic deterministic fills are test-only and never enter a user production database as real data.

### 7.4 `positions`

- `id` UUID PK
- `portfolio_id`, `account_id`, `security_id`; unique together
- `quantity`, `settled_quantity`, `reserved_sell_quantity`
- `average_cost_local`, `cost_basis_local`, `currency`
- `cost_basis_base`, `realized_pnl_local`, `realized_pnl_base`
- `as_of_ledger_sequence`, `updated_at`, `version`

This weighted-average-cost projection is updated only from confirmed fills and approved corporate actions. Unrealized P&L is computed against an explicitly identified price/FX observation and stored in snapshots, not treated as a permanent position fact.

## 8. Market, FX, fundamental, valuation, and event provenance

### 8.1 `market_prices`

- `id` UUID PK
- `security_id`, `provider_name`, `provider_symbol`
- `interval`, `session_date`, `observed_at`, `available_at`, `retrieved_at`
- raw OHLC, volume; split-adjusted OHLC; total-return-adjusted close using Decimal columns
- `currency`, `market_timezone`, `calendar_id`
- nullable `split_factor`, `total_return_factor`
- `source_record_id`, `source_version`, `raw_payload_hash`, `quality_status`
- unique `(security_id, provider_name, interval, observed_at, source_version)`

Revisions append a new source version. Strategy dataset manifests pin selected row IDs.

### 8.2 `fx_rates`

- `id` UUID PK
- `base_currency`, `quote_currency`, `rate`
- `rate_type` (`SPOT`, `CLOSE`, `TRANSACTION`, `MANUAL`)
- `observed_at`, `available_at`, `retrieved_at`
- `provider_name`, `source_record_id`, `source_version`, `quality_status`
- unique provider observation/version key

Inversion is calculated with Decimal and retains the original row ID; an inverse is not stored as an independent sourced fact unless the provider supplied it.

### 8.3 `fundamental_records`

- `id` UUID PK
- `security_id`, `provider_name`, `source`, `source_record_id`
- `record_type`, `metric_name`
- one of `value_decimal`, `value_text`, `value_boolean`; `unit`, `currency`
- `fiscal_period`, `period_end`
- `published_at`, `available_at`, `effective_at`, `retrieved_at`
- `is_restated`, nullable `supersedes_id`
- `source_version`, `raw_payload_hash`, `quality_status`
- unique `(provider_name, source_record_id, metric_name, source_version)`

The one-value check prevents contradictory representations. Restatements append and link; a point-in-time query returns the latest version available at the requested cutoff, not the latest known today.

### 8.4 `valuation_snapshots`

- `id` UUID PK
- `security_id`, `provider_name`, `source_record_id`
- `data_as_of`, `available_at`, `retrieved_at`
- nullable Decimal metrics: `forward_pe`, `ev_to_ebitda`, `fcf_yield`, `eps_growth_forward`, `roic`, `net_debt_to_ebitda`, `interest_coverage`
- `currency`, `estimate_horizon`, `methodology_version`
- `source_version`, `raw_payload_hash`, `quality_status`
- nullable `supersedes_id`

Null means missing and is accompanied by provenance/quality metadata; it is never zero. Derived valuation scores store source row IDs in the strategy-run manifest.

### 8.5 `corporate_events`

- `id` UUID PK
- `security_id`, `provider_name`, `source_record_id`
- `event_type` (earnings, dividend, split, reverse split, symbol change, delisting, regulatory, other)
- `announced_at`, `available_at`, `effective_at`, `retrieved_at`
- Decimal event terms in typed columns where applicable; descriptive metadata in `details_json`
- `currency`, `source_version`, `raw_payload_hash`, `quality_status`
- unique provider record/version key

An observation has no accounting effect until linked to an approved idempotent ledger transaction.

### 8.6 `risk_flags`

- `id` UUID PK
- optional `portfolio_id`, `security_id`, `strategy_run_id`, `corporate_event_id`
- `flag_type`, `severity`, `status`, `blocks_new_buys`
- `source_type`, `source`, `source_record_id`, `available_at`
- `reason`, `created_at`, optional `resolved_at`, `supersedes_id`

Manual flags record actor and provenance. Resolution appends/supersedes rather than erasing the original fact.

## 9. NAV, snapshots, and performance

### 9.1 `portfolio_snapshots`

- `id` UUID PK
- `portfolio_id`, `valuation_at`, `valuation_kind` (`INCEPTION`, `FLOW_PRE`, `FLOW_POST`, `MARKET_CLOSE`, `LATEST`)
- `base_currency`
- `cash_value`, `market_value`, `receivables`, `payables`, `total_equity`
- `units_outstanding`, `nav_per_unit`
- `cost_basis`, `realized_pnl`, `unrealized_pnl`, `fees`, `taxes`, `equity_pnl`, `fx_pnl`
- `cash_ratio`, `invested_ratio`
- `price_manifest_hash`, `fx_manifest_hash`, `ledger_sequence`
- `is_official`, `quality_status`, `missing_data_json`
- unique official snapshot per `(portfolio_id, valuation_at, valuation_kind)`

Invariant: `nav_per_unit = total_equity / units_outstanding` when units are positive. A snapshot with stale/missing marks is labelled and cannot be silently promoted to official.

An official `FLOW_PRE` snapshot with positions is complete only when every position mark and required FX observation is available, point-in-time valid, and included in the manifests. An incomplete snapshot cannot be used for unit issuance/redemption.

### 9.2 `performance_series`

- `id` UUID PK
- `portfolio_id`, `period_start`, `period_end`, `frequency`
- `start_snapshot_id`, `end_snapshot_id`
- `opening_nav`, `closing_nav`, `twr_return`
- `external_flow_base`, `investment_pnl_base`
- `max_drawdown`, `turnover`, `average_exposure`, `cash_ratio`
- nullable `benchmark_security_id`, `benchmark_return`
- `methodology_version`, `quality_status`, `created_at`
- unique series point key including methodology/benchmark

Daily TWR chains subperiod returns at external flows; weekly/monthly/since-inception values geometrically link daily/subperiod factors. XIRR is not a v1 field.

## 10. Configuration and audit support

### 10.1 `settings`

- `id` UUID PK
- unique `(scope_type, scope_id, key)`
- `value_json`, `value_type`, `schema_version`
- `is_secret` constrained false
- `updated_at`, `version`

Permitted keys are registered in code. Unknown arbitrary keys are rejected. Environment secrets are never copied into settings.

### 10.2 `reconciliation_runs` and `reconciliation_discrepancies`

Although implementation begins in Phase 5, the normalized design is frozen now.

`reconciliation_runs`: profile/account, start/end, external as-of, status, source manifest/hash.

`reconciliation_discrepancies`: run, category (cash/position/order/fill), canonical entity key, internal value JSON, redacted external value JSON, severity, resolution status, optional adjustment transaction. Observations append; resolving a discrepancy does not rewrite the observation.

## 11. Database-level checks and indexes

Minimum constraints include:

- amounts/quantities that are semantically positive are `> 0`; signed direction is an enum/type, not a negative amount accident;
- `filled_quantity <= order.quantity`, `reserved_sell_quantity <= position.quantity`, and units outstanding cannot be negative;
- order `LIMIT` requires `limit_price`; `MARKET` has no limit price;
- currency pairs cannot have equal base/quote for an FX transaction/rate;
- `available_at >= published_at` when both exist unless an explicit source correction flag explains otherwise;
- restatement/supersession links point to the same security/metric/source family;
- one default watchlist per portfolio and one active assignment/mapping/membership per logical key;
- unique idempotency and external-event/fill identifiers as described above.
- user-supplied securities cannot be inserted as verified/tradable and cannot carry provider mappings or trading rules without a separate verified update workflow;
- SQLite exact decimal columns have TEXT affinity and canonical-format/type checks (`typeof(...)='text'` plus length/sign/decimal-point validation) where portable, while precision/scale/range and numeric ordering are enforced by `ExactDecimal`/repository logic.

High-use indexes cover:

- market prices `(security_id, interval, observed_at, available_at)`;
- point-in-time fundamentals/valuations `(security_id, metric_name/data_as_of, available_at)`;
- ledger `(portfolio_id, sequence_no)` and entries by account/security/effective time;
- orders/fills by account, portfolio, state, external ID, and time;
- snapshots/performance by portfolio and valuation/period end;
- active flags, mappings, assignments, and watchlist memberships using partial indexes where supported and portable application checks otherwise.

## 12. Initial data and migrations

Alembic is the only schema-change path. Application startup checks the migration revision and refuses ad hoc `create_all` in normal operation. Migration rendering is dialect-aware: SQLite DDL emits canonical fixed-scale `TEXT` for `ExactDecimal`; PostgreSQL DDL emits `NUMERIC(38,18)`. A migration test inspects the actual SQLite declared type and `typeof()` results so an accidental return to NUMERIC affinity fails.

The Phase 1 bootstrap is idempotent and identified by stable seed keys. It creates:

1. the three configurable security rows and default watchlist memberships;
2. an internal `AI Infra` portfolio with HKD base currency, local inception date `2026-08-31`, and `Asia/Hong_Kong` valuation timezone;
3. a non-operational paper broker profile/account marked `NOT_IMPLEMENTED`;
4. an initial contribution of HKD 20,000 with a balanced opening ledger transaction;
5. 200 portfolio units issued at NAV 100.00;
6. an inception snapshot at local midnight (`2026-08-30T16:00:00Z`) with HKD 20,000 cash, zero invested value, and NAV 100.00.

This is a bootstrap fact set, not a deposit/order API. Re-running seed logic must create no duplicates. Phase 2 accounting code must rebuild identical projections from these facts before it can add later transactions.

Future migrations are phased: execution/accounting behavior in Phase 2, external data/strategy records in Phase 3, backtest metadata in Phase 4, reconciliation/Futu records in Phase 5, and live audit/security data in Phase 7. Schema elements may be created earlier when necessary for referential integrity, but no earlier phase exposes future behavior.

## 13. Acceptance properties

- Two independent rebuilds from immutable facts produce byte-for-byte canonical Decimal cash/position/NAV outputs.
- Initial contribution yields equity `20000.000000000000000000`, units `200.000000000000000000`, and NAV `100.000000000000000000` with no investment return.
- SQLite round-trips the three required Decimal vectors with identical tuples, stores them as `text`, orders/compares them correctly in Python Decimal, and rejects overflow/over-scale/float input.
- A deposit/withdrawal property test proves NAV/TWR continuity at the flow boundary.
- With positions, an incomplete/missing mark or FX observation rejects deposit/withdrawal with `PORTFOLIO_VALUATION_UNAVAILABLE` and writes no unit/ledger rows.
- Ledger transactions balance exactly in base currency; deliberately unbalanced writes fail atomically.
- SQLite ledger balance is validated with Python `Decimal` inside the Unit of Work; tests prove no SQL `SUM`/numeric `CAST` over decimal text is used or claimed exact.
- Updating/deleting a posted ledger/fill/cash-flow/unit row fails.
- Reusing an idempotency key with different canonical content fails.
- Point-in-time queries never return a record with `available_at` after the cutoff and preserve pre-restatement results.
- Append-only SQLite triggers reject update/delete of posted facts independently of the Python balance validation.
