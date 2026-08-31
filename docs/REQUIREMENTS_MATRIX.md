# Requirements Traceability Matrix

Status: Phase 0 design freeze candidate

Source baseline: `docs/MASTER_SPEC.md` v1.0 and the Phase 0 user instruction

## 1. Status and evidence rules

| Status | Meaning |
|---|---|
| `DOCUMENTED` | Phase 0 design/contract exists; no business implementation is claimed |
| `NOT_STARTED` | Assigned to a future phase; no implementation/evidence yet |
| `DECISION_REQUIRED` | Design is explicit, but a user/source choice is required before the target phase |
| `IMPLEMENTED` | Reserved for later phases after code and acceptance evidence exist |
| `BLOCKED_EXTERNAL` | Reserved for a verified external blocker; unavailable data alone is not disguised as implementation |

Evidence in this Phase 0 matrix is either a design section or a named future acceptance test. A test name is a plan, not a passing result, until a later phase records its exact command/result or CI artifact. Every future phase must update status and replace planned evidence with actual evidence.

## 2. Architecture and phase control

| ID | Requirement | Target phase | Design document | Status | Test/acceptance evidence |
|---|---|---:|---|---|---|
| ARC-001 | Single-user, local-first, single-process modular monolith | 1 | `ARCHITECTURE.md` §§1,8 | DOCUMENTED | Phase 1 startup/process inspection; no distributed dependencies in lock metadata |
| ARC-002 | No microservices, Kafka, Redis, Celery, Kubernetes, distributed event sourcing, or autonomous trading | all | `ARCHITECTURE.md` §§1,8 | DOCUMENTED | Dependency/config scan each phase |
| ARC-003 | Strategy separated from broker, API, ORM, portfolio mutation, and execution | 1/3 | `ARCHITECTURE.md` §§2-4 | DOCUMENTED | `test_core_import_boundaries`; strategy unit tests use canonical context only |
| ARC-004 | Portfolio separated from Accounting and broker SDKs | 1/2 | `ARCHITECTURE.md` §3 | DOCUMENTED | import-boundary and use-case tests |
| ARC-005 | Accounting owns ledger/cash/position/NAV facts and is separated from execution/strategy | 2 | `ARCHITECTURE.md` §§3,6 | DOCUMENTED | ledger rebuild and forbidden-import tests |
| ARC-006 | Execution owns order lifecycle/idempotency and updates accounting only on confirmed facts | 2 | `ARCHITECTURE.md` §§3,6-7 | DOCUMENTED | order-state/fill integration tests |
| ARC-007 | Risk is broker-agnostic and cannot submit orders | 2 | `ARCHITECTURE.md` §3 | DOCUMENTED | risk decision unit tests and import-boundary test |
| ARC-008 | Performance is read-only/reproducible from accounting facts | 2 | `ARCHITECTURE.md` §§3,6 | DOCUMENTED | deterministic snapshot/TWR rebuild |
| ARC-009 | Backtest reuses Strategy and canonical signals but has isolated clock/simulator | 4 | `ARCHITECTURE.md` §3; `STRATEGY_SPEC.md` §17 | DOCUMENTED | shared-strategy identity and future-data injection tests |
| ARC-010 | BrokerAdapter separated from all data-provider ports | 1 | `ARCHITECTURE.md` §§3-4 | DOCUMENTED | interface signatures and registry independence tests |
| ARC-011 | Market, fundamental, and event providers are three separate ports/capability models | 1 | `ARCHITECTURE.md` §3 | DOCUMENTED | structural protocol/capability tests |
| ARC-012 | Broker and market-data provider independently selectable | 1/5 | `ARCHITECTURE.md` §§1-4 | DOCUMENTED | composition test with independent registry keys; real adapter evidence in Phase 5 |
| ARC-013 | One portfolio may aggregate multiple broker accounts, without conflating entities | 1 | `ARCHITECTURE.md` §5; `DATABASE_SCHEMA.md` §5 | DOCUMENTED | model/repository relationship test |
| ARC-014 | Registries/factories avoid scattered provider-specific conditionals | 1 | `ARCHITECTURE.md` §§1-4 | DOCUMENTED | registry registration/unknown/duplicate tests |
| ARC-015 | Domain/provider responses use platform-owned canonical models | 1 | `ARCHITECTURE.md` §5; `API_CONTRACTS.md` §1 | DOCUMENTED | adapter protocol type and API/ORM isolation tests |
| ARC-016 | In-process transaction/unit-of-work and idempotency rules | 1/2 | `ARCHITECTURE.md` §7 | DOCUMENTED | UoW rollback and idempotency tests |
| ARC-017 | Preserve phase gates; Phase 1 and strategy approval are separate exact instructions | every phase | `ARCHITECTURE.md` §§9-11; Phase plans | DOCUMENTED | `APPROVE PHASE 1` authorizes foundation only; `APPROVE STRATEGY SPEC V1` required before strategy implementation |
| ARC-018 | Preserve unrelated user changes; no unauthorized push/remote/global Git changes | every phase | `AGENTS.md`; `PHASE_1_PLAN.md` | DOCUMENTED | before/after `git status`, remote/config not mutated |

## 3. Canonical security, configuration, and missing data

| ID | Requirement | Target phase | Design document | Status | Test/acceptance evidence |
|---|---|---:|---|---|---|
| DOM-001 | Vendor-neutral security IDs and full security metadata | 1 | `DATABASE_SCHEMA.md` §3.1; `API_CONTRACTS.md` §4.8 | DOCUMENTED | uniqueness, validation, API contract tests |
| DOM-002 | Provider symbol mappings separate from security | 1 | `DATABASE_SCHEMA.md` §3.2 | DOCUMENTED | independent mapping/registry tests |
| DOM-003 | Initial AVGO, VRT, HK.09698 defaults configurable, not core constants | 1 | `DATABASE_SCHEMA.md` §12; `PHASE_1_PLAN.md` | DOCUMENTED | seed override/idempotency test |
| DOM-004 | HKD 20,000, inception 2026-08-31, NAV 100 defaults configurable | 1 | `DATABASE_SCHEMA.md` §12; `API_CONTRACTS.md` §4.2 | DOCUMENTED | bootstrap invariant integration test |
| DOM-005 | Missing facts explicitly MISSING/UNAVAILABLE/NOT_SUPPORTED; never fabricated | 1 | `ARCHITECTURE.md` §5; `API_CONTRACTS.md` §§1-2 | DOCUMENTED | missing-data API/domain tests |
| DOM-006 | Typed capability models for broker/market/fundamental/event | 1 | `ARCHITECTURE.md` §3; `API_CONTRACTS.md` §2.2 | DOCUMENTED | enum and provider descriptor tests |
| DOM-007 | Settings contain no secrets; credentials remain environment/external storage | 1 | `DATABASE_SCHEMA.md` §10.1 | DOCUMENTED | settings allowlist/redaction tests, secret scan |
| DOM-008 | Environment configuration; live disabled and auto execution false | 1 | `ARCHITECTURE.md` §8; `PHASE_1_PLAN.md` | DOCUMENTED | configuration default/validation tests |
| DOM-009 | Decimal domain/API; exact SQLite fixed-scale TEXT and PostgreSQL NUMERIC physical persistence | 1/2 | `DATABASE_SCHEMA.md` §1.3; `API_CONTRACTS.md` §1 | DOCUMENTED | required vector tuple round trips, `typeof=text`, float/scale/range/order tests |
| DOM-010 | All timestamps/calendar/timezones point-in-time explicit | 1/3 | `DATABASE_SCHEMA.md` §1.2; `STRATEGY_SPEC.md` §2 | DOCUMENTED | timezone/calendar validation and PIT tests |
| DOM-011 | User may create canonical unverified security; watchlist allowed but strategy/orders fail closed | 1 | `DATABASE_SCHEMA.md` §3.1; `API_CONTRACTS.md` §4.9 | DOCUMENTED | normalization/uniqueness/forced-status/unavailable-rules/blocking tests |

## 4. Database, accounting, cash, NAV, and performance

| ID | Requirement | Target phase | Design document | Status | Test/acceptance evidence |
|---|---|---:|---|---|---|
| DB-001 | Normalized minimum schema and relationships | 1-3 | `DATABASE_SCHEMA.md` §§2-10 | DOCUMENTED | Alembic schema/FK/index inspection by assigned phase |
| DB-002 | Alembic migrations; no ad hoc normal-startup `create_all` | 1 | `DATABASE_SCHEMA.md` §12 | DOCUMENTED | empty DB upgrade/current/downgrade-upgrade test |
| ACC-001 | Append-only balanced ledger and explicit reversals; SQLite balances in Python Decimal UoW | 1/2 | `DATABASE_SCHEMA.md` §§1.3,1.6,6.1-6.3 | DOCUMENTED | exact UoW balance/rollback, no TEXT SUM/CAST, immutability trigger, reversal tests |
| ACC-002 | Orders/fills/cash flows not silently overwritten/deleted | 2 | `DATABASE_SCHEMA.md` §§1.6,6-7 | DOCUMENTED | update/delete rejection and event-history tests |
| ACC-003 | Multi-currency cash per account/currency; settled/unsettled/reserved/buying power | 2 | `DATABASE_SCHEMA.md` §§6.7-6.9 | DOCUMENTED | cash projection/settlement/reservation tests |
| ACC-004 | Explicit and recorded AUTO_FX/EXPLICIT_FX with rate/spread/fee | 2 | `DATABASE_SCHEMA.md` §6.6; `API_CONTRACTS.md` §6.2 | DOCUMENTED | FX direction, balance, disclosure tests |
| ACC-005 | Deposits/withdrawals separated from return and require complete FLOW_PRE valuation with positions | 2 | `DATABASE_SCHEMA.md` §§6.4-6.5,9; `API_CONTRACTS.md` §6.1 | DOCUMENTED | NAV/TWR continuity and atomic `PORTFOLIO_VALUATION_UNAVAILABLE` tests |
| ACC-006 | Initial equity 20,000, 200 units, NAV 100 | 1 | `DATABASE_SCHEMA.md` §§6.5,12 | DOCUMENTED | exact Decimal bootstrap/rebuild test |
| ACC-007 | Unitized NAV and TWR; daily/weekly/monthly/since inception | 2 | `DATABASE_SCHEMA.md` §9 | DOCUMENTED | unit issue/redeem/geometric-link tests |
| ACC-008 | Weighted-average cost consistently used | 2 | `DATABASE_SCHEMA.md` §7.4; `ARCHITECTURE.md` DR-015 | DOCUMENTED | multi-fill buy/sell/fee realized P&L tests |
| ACC-009 | Cost basis, realized/unrealized, fee/tax, equity/FX P&L reporting | 2 | `DATABASE_SCHEMA.md` §§7.4,9 | DOCUMENTED | accounting equation and attribution fixtures |
| ACC-010 | Corporate actions model: dividends/tax/splits/reverse/symbol/delist/fees/rebates | 2/4 | `DATABASE_SCHEMA.md` §§6,8.5 | DOCUMENTED | idempotent corporate-action ledger tests |
| ACC-011 | Cash/position projections update only from confirmed fills/economic facts | 2 | `ARCHITECTURE.md` §6; `DATABASE_SCHEMA.md` §7 | DOCUMENTED | submitted-versus-filled integration test |
| ACC-012 | Portfolio valuation cutoff across markets | 2 | `ARCHITECTURE.md` OD-002 | DECISION_REQUIRED | user-approved cutoff and close-series acceptance tests |
| ACC-013 | Versioned settlement and fee/tax policy | 2 | `ARCHITECTURE.md` OD-003; `DATABASE_SCHEMA.md` §6.9 | DECISION_REQUIRED | verified/simplified policy fixtures and provenance |
| ACC-014 | Maximum drawdown, benchmark, cash/invested ratios | 2/3 | `DATABASE_SCHEMA.md` §9; `API_CONTRACTS.md` §4.4 | DOCUMENTED | return/drawdown tests; benchmark unavailable until legitimate source |
| ACC-015 | Zero positions imply exact zero unrealized P&L independent of unavailable market-data capability | 1 | `API_CONTRACTS.md` §4.2 | DOCUMENTED | opening portfolio response/capability-separation test |

## 5. Orders, PaperBroker, execution, and risk

| ID | Requirement | Target phase | Design document | Status | Test/acceptance evidence |
|---|---|---:|---|---|---|
| EXE-001 | StandardOrder contains all required canonical identifiers/terms | 1 | `DATABASE_SCHEMA.md` §7.1; `API_CONTRACTS.md` §6.3 | DOCUMENTED | model validation/serialization tests |
| EXE-002 | Required order states and valid state machine | 2 | `DATABASE_SCHEMA.md` §§7.1-7.2 | DOCUMENTED | exhaustive transition-table tests |
| EXE-003 | Submitted is not filled; multiple/partial fills supported | 2 | `ARCHITECTURE.md` §6.1; `DATABASE_SCHEMA.md` §7.3 | DOCUMENTED | acknowledgement/no-position and partial-fill tests |
| EXE-004 | Same idempotency key never creates two broker orders | 2/7 | `ARCHITECTURE.md` §7; `API_CONTRACTS.md` §§1,8 | DOCUMENTED | identical replay/conflicting replay/concurrency tests |
| EXE-005 | PaperBroker behaves as persistent broker account | 2 | `ARCHITECTURE.md` §9; database accounting/order schema | DOCUMENTED | restart persistence and canonical adapter tests |
| EXE-006 | Paper deposits, withdrawals, FX, reservations, settlement, costs, P&L | 2 | `DATABASE_SCHEMA.md` §6; `API_CONTRACTS.md` §6 | DOCUMENTED | Phase 2 end-to-end paper fixtures |
| EXE-007 | Phase 2 permits explicit manual simulation fills with complete price provenance; no automatic matching | 2 | `ARCHITECTURE.md` DR-026/DR-049; `DATABASE_SCHEMA.md` §7.3; `API_CONTRACTS.md` §6.3 | DOCUMENTED | manual full/partial fill, actor/source/time, no-auto-match, synthetic-test isolation |
| EXE-008 | Pre-trade long-only/cash/limits/capability/price/currency checks | 2 | `ARCHITECTURE.md` §3; `STRATEGY_SPEC.md` §14 | DOCUMENTED | risk rejection table tests |
| EXE-009 | Legal cumulative quantity never exceeds target/cash/cap/approved risk; explicit discrete statuses | 3 | `STRATEGY_SPEC.md` §14 | DOCUMENTED | G-18..G-22 and never-exceed property tests |
| EXE-010 | Reconciliation observes discrepancies and never silently overwrites ledger | 5 | `ARCHITECTURE.md` §6.4; `DATABASE_SCHEMA.md` §10.2 | DOCUMENTED | startup/reconnect discrepancy tests |

## 6. Strategy and recommendations

| ID | Requirement | Target phase | Design document | Status | Test/acceptance evidence |
|---|---|---:|---|---|---|
| STR-001 | Strategy interface/registry; same strategy in analysis/paper/backtest/live recommendation | 1/3/4 | `ARCHITECTURE.md` §3; `STRATEGY_SPEC.md` §§1,17 | DOCUMENTED | registry and shared-object execution tests |
| STR-002 | Per-security database assignment and parameter set | 1/3 | `DATABASE_SCHEMA.md` §§4.1-4.2 | DOCUMENTED | assignment overlap/schema/hash tests |
| STR-003 | 30/20/20/15/15 composite and exact decimal score bands | 3 | `STRATEGY_SPEC.md` §9 | DOCUMENTED | G-07/G-08/G-09 |
| STR-004 | M3=63, M6=126 simple return, Decimal log sample RV, annualization/floor | 3 | `STRATEGY_SPEC.md` §5 | DOCUMENTED | G-01/G-02 and formula tests |
| STR-005 | Own-history normalization; 252 prior M6 observations need ~379 closes, full 756 need ~883 | 3 | `STRATEGY_SPEC.md` §5.4 | DOCUMENTED | G-03, exact history-boundary/tie/winsor tests |
| STR-006 | Cross-section is priority overlay only | 3 | `STRATEGY_SPEC.md` §11 | DOCUMENTED | overlay invariance test |
| STR-007 | MA20/50/200 and exact trend entry filter/scoring | 3 | `STRATEGY_SPEC.md` §§4,6 | DOCUMENTED | G-04 and MA fixtures |
| STR-008 | 60-high drawdown, ATR/vol scaling, healthy-pullback/falling-knife function | 3 | `STRATEGY_SPEC.md` §§4.2-4.3,7 | DOCUMENTED | G-05 and boundary/property tests |
| STR-009 | Point-in-time valuation 40/30/20/10 with no fabricated fields | 3 | `STRATEGY_SPEC.md` §8; `DATABASE_SCHEMA.md` §8 | DOCUMENTED | G-06/G-17, missing/stale/provenance tests |
| STR-010 | Exact coverage/bounds and COMPLETE/PARTIAL/INVALID gates | 3 | `STRATEGY_SPEC.md` §9 | DOCUMENTED | G-08/G-09 |
| STR-011 | Missing valuation/fundamental data forces review and no buy/add | 3 | `STRATEGY_SPEC.md` §§8-9 | DOCUMENTED | G-08 and stale-review tests |
| STR-012 | Exact three-signal confirmation; otherwise waiting | 3 | `STRATEGY_SPEC.md` §10 | DOCUMENTED | G-10 and current-bar exclusion tests |
| STR-013 | Exact annual-effective dual-momentum hurdle/block and relative priority | 3 | `STRATEGY_SPEC.md` §11 | DOCUMENTED | G-11 and no-source/unavailable tests |
| STR-014 | Provenance-aware manual/data-assisted fundamental veto | 3 | `STRATEGY_SPEC.md` §12 | DOCUMENTED | severity/staleness/unverified-source tests |
| STR-015 | State machine; score-based REDUCE requires complete/current/no-review inputs | 3 | `STRATEGY_SPEC.md` §13 | DOCUMENTED | G-12..G-15, G-23, and transition matrix |
| STR-016 | Choose hard-stop risk budget versus target-allocation volatility-scaled sizing | 3 | `ARCHITECTURE.md` OD-006; `STRATEGY_SPEC.md` §14 | DECISION_REQUIRED | separate sizing approval; G-16 exposes conflict; no implementation yet |
| STR-017 | Explainable canonical output including coverage/missing/reason/risk | 3 | `STRATEGY_SPEC.md` §15; `API_CONTRACTS.md` §5 | DOCUMENTED | response/golden snapshot tests |
| STR-018 | Strategy remains PROPOSED/RESEARCH_UNVALIDATED and needs separate exact approval | 3 | `STRATEGY_SPEC.md` status | DECISION_REQUIRED | exact `APPROVE STRATEGY SPEC V1`; `APPROVE PHASE 1` is insufficient |
| STR-019 | Legitimate Phase 3 historical market-data path | 3 | `ARCHITECTURE.md` OD-001 | DECISION_REQUIRED | approved provider/import provenance and integration tests |
| STR-020 | Legitimate fundamental/valuation/event source or truthful unavailable status | 3 | `ARCHITECTURE.md` OD-005 | DECISION_REQUIRED | source entitlement/provenance verification or unavailable-gate tests |
| STR-021 | Cumulative legal tranche targets adapt one/two/fractional/board-lot quantities | 3 | `STRATEGY_SPEC.md` §14.3 | DOCUMENTED | G-18..G-21 and confirmed-cumulative-fill tests |
| STR-022 | No profitability/predictive claim; research status persists through backtest and forward review | 3/4+ | `STRATEGY_SPEC.md` §§1,17 | DOCUMENTED | report labels and acceptance review; backtest pass cannot change status automatically |

## 7. Market/fundamental/event data

| ID | Requirement | Target phase | Design document | Status | Test/acceptance evidence |
|---|---|---:|---|---|---|
| DAT-001 | MarketDataProvider quote/snapshot/history/subscription/order-book contract | 1 | `ARCHITECTURE.md` §3; Phase 1 port plan | DOCUMENTED | protocol signatures/canonical return tests |
| DAT-002 | FundamentalDataProvider financial/estimate/valuation/history/balance contract | 1 | `ARCHITECTURE.md` §3; `DATABASE_SCHEMA.md` §8 | DOCUMENTED | protocol and PIT model tests |
| DAT-003 | EventDataProvider earnings/corporate/regulatory/manual flag contract | 1 | `ARCHITECTURE.md` §3; `DATABASE_SCHEMA.md` §§8.5-8.6 | DOCUMENTED | protocol and event provenance tests |
| DAT-004 | Preserve source IDs, period/publish/available/effective/retrieval, currency, restatement | 3 | `DATABASE_SCHEMA.md` §§8.3-8.4 | DOCUMENTED | G-17 and restatement PIT queries |
| DAT-005 | Distinguish raw, split-adjusted, total-return prices/corporate actions | 3/4 | `DATABASE_SCHEMA.md` §8.1; `STRATEGY_SPEC.md` §2 | DOCUMENTED | adjustment-factor and strategy-source tests |
| DAT-006 | Correct US/HK calendars/timezones; no missing-session forward fill | 3/4 | `STRATEGY_SPEC.md` §§2-3 | DOCUMENTED | calendar gap/DST/session tests |
| DAT-007 | Synthetic fixtures isolated from production tables/recommendations | 1 onward | `DATABASE_SCHEMA.md` §12; `STRATEGY_SPEC.md` §17 | DOCUMENTED | fixture provenance and seed-path isolation tests |
| DAT-008 | No external availability claim without legitimate verification | 0 onward | `ARCHITECTURE.md` §12; `API_CONTRACTS.md` §4 | DOCUMENTED | Phase 0 report; provider statuses unavailable |

## 8. Backtest correctness

| ID | Requirement | Target phase | Design document | Status | Test/acceptance evidence |
|---|---|---:|---|---|---|
| BT-001 | Indicators/signals use only data known at signal time | 4 | `ARCHITECTURE.md` §3; `STRATEGY_SPEC.md` §§1-3 | DOCUMENTED | future-record injection and PIT provider tests |
| BT-002 | Default T-close signal to T+1-open fill; no same-bar fill | 4 | `ARCHITECTURE.md` DR-027 | DOCUMENTED | explicit timing golden test |
| BT-003 | Commission/platform fee/tax/slippage/minimum fee/FX cost | 4 | `DATABASE_SCHEMA.md` §§6-7 | DOCUMENTED | before/after-cost deterministic fixture |
| BT-004 | Corporate actions, raw/adjusted prices, survivorship awareness | 4 | `DATABASE_SCHEMA.md` §8; `STRATEGY_SPEC.md` §2 | DOCUMENTED | split/dividend/delist universe tests |
| BT-005 | US/HK calendars/timezones and impossible execution prevention | 4 | `STRATEGY_SPEC.md` §2 | DOCUMENTED | closed-market/DST/next-open tests |
| BT-006 | Run records data/provider/version/strategy/parameters/execution assumption | 3/4 | `DATABASE_SCHEMA.md` §4.3 | DOCUMENTED | manifest/hash reproducibility test |
| BT-007 | PIT historical fundamentals/valuation; no later publications | 4 | `DATABASE_SCHEMA.md` §8; `STRATEGY_SPEC.md` G-17 | DOCUMENTED | later-publication/restatement test |
| BT-008 | Before/after-cost return, turnover, trades, exposure, cash, drawdown, benchmark | 4 | `DATABASE_SCHEMA.md` §9 | DOCUMENTED | report schema/snapshot fixtures |

## 9. Futu, future brokers, and live safety

| ID | Requirement | Target phase | Design document | Status | Test/acceptance evidence |
|---|---|---:|---|---|---|
| INT-001 | No Futu SDK in Phase 0/1; no OpenD connection | 0/1 | `ARCHITECTURE.md` §8; `PHASE_1_PLAN.md` | DOCUMENTED | dependency/import scan; offline startup |
| INT-002 | Shared FutuConnectionManager, SDK imports confined to Futu integration | 5 | `ARCHITECTURE.md` dependency rule | DOCUMENTED | import scan, lifecycle/connect/close tests |
| INT-003 | Futu read-only market/account/cash/position/order/fill and offline-safe startup | 5 | `ARCHITECTURE.md` §9 | DOCUMENTED | mocked protocol plus verified offline status; no availability claimed now |
| INT-004 | Disabled Futu canonical order conversion before live routes | 6 | `ARCHITECTURE.md` §§8-9; `API_CONTRACTS.md` §7 | DOCUMENTED | route absence and mapping simulation tests |
| INT-005 | EastMoney skeleton only until legitimate stable interface selected | 8 | `ARCHITECTURE.md` OD-005 | DECISION_REQUIRED | capability `NOT_IMPLEMENTED`; later source/interface approval |
| LIVE-001 | Long-only cash, no margin/short/options/futures, AUTO_EXECUTION false | 2/7 | `ARCHITECTURE.md` §8; `STRATEGY_SPEC.md` §14 | DOCUMENTED | risk model and configuration tests |
| LIVE-002 | No functional/live route in Phase 1 (indeed Phases 1-6) | 1-6 | `API_CONTRACTS.md` §§3,7 | DOCUMENTED | OpenAPI route denylist test every phase |
| LIVE-003 | Authentication/authorization and CSRF where session auth used | 7 | `ARCHITECTURE.md` OD-004; `API_CONTRACTS.md` §7 | DECISION_REQUIRED | auth/CSRF bypass tests after approval |
| LIVE-004 | Persistent kill switch and position/daily-order/exposure limits | 7 | `API_CONTRACTS.md` §7 | DOCUMENTED | restart persistence and limit rejection tests |
| LIVE-005 | Duplicate, invalid-price, market-status, cash, currency, stale-data, connectivity checks | 7 | `API_CONTRACTS.md` §§7-8 | DOCUMENTED | each server-side rejection and fail-closed tests |
| LIVE-006 | Explicit immutable order confirmation/manual approval every order | 7 | `API_CONTRACTS.md` §7 | DOCUMENTED | challenge mismatch/expiry/replay tests |
| LIVE-007 | Startup/reconnect reconciliation of open orders/fills/positions/cash | 5/7 | `DATABASE_SCHEMA.md` §10.2 | DOCUMENTED | discrepancy and no-silent-overwrite tests |
| LIVE-008 | Completing safety code does not authorize enabling live mode | 7 | `ARCHITECTURE.md` §8 | DOCUMENTED | config default/explicit separate authorization report |

## 10. API and frontend

| ID | Requirement | Target phase | Design document | Status | Test/acceptance evidence |
|---|---|---:|---|---|---|
| API-001 | Versioned request/response models and stable error semantics | 1 | `API_CONTRACTS.md` §§1-2,8 | DOCUMENTED | OpenAPI/problem-schema tests |
| API-002 | Decimal strings, UTC, UUID, explicit missing-data values | 1 | `API_CONTRACTS.md` §§1-2 | DOCUMENTED | schema/serialization tests |
| API-003 | Phase 1 security creation/read, portfolio/positions/performance, and watchlist CRUD | 1 | `API_CONTRACTS.md` §4 | DOCUMENTED | security normalization/status plus endpoint integration tests |
| API-004 | Strategy/indicator/signal endpoints only with Phase 3 behavior | 3 | `API_CONTRACTS.md` §5 | DOCUMENTED | route absence before Phase 3; contract tests in Phase 3 |
| API-005 | Paper financial endpoints only in Phase 2 | 2 | `API_CONTRACTS.md` §6 | DOCUMENTED | Phase 1 route denylist; Phase 2 idempotency tests |
| API-006 | Broker/provider status truthful and no connection side effect | 1 | `API_CONTRACTS.md` §§4.11-4.13 | DOCUMENTED | descriptor/no-instantiation tests |
| API-007 | Local-only CORS/no-store/request IDs/no secret/raw provider exposure | 1/7 | `API_CONTRACTS.md` §9 | DOCUMENTED | header/schema/redaction tests |
| API-008 | Inception-only daily return unavailable; since-inception/drawdown exact zero | 1 | `API_CONTRACTS.md` §4.4 | DOCUMENTED | one-point performance contract test |
| UI-001 | Minimal professional dark read-only dashboard in Phase 1 | 1 | `PHASE_1_PLAN.md`; master §18 | DOCUMENTED | browser smoke and static text/state checks |
| UI-002 | Summary NAV/equity/cash/invested and truthful unavailable status | 1 | `API_CONTRACTS.md` §§4.2-4.4 | DOCUMENTED | browser/API bootstrap test |
| UI-003 | Security cards, indicators, components, explanations, recommendation panel | 3 | `API_CONTRACTS.md` §5; `STRATEGY_SPEC.md` §15 | DOCUMENTED | Phase 3 UI contract/e2e tests |
| UI-004 | Paper and live actions visually/functionally separate; live unmistakable | 2/7 | `API_CONTRACTS.md` §§6-7 | DOCUMENTED | DOM/route/action separation tests |

## 11. Testing, tooling, and delivery

| ID | Requirement | Target phase | Design document | Status | Test/acceptance evidence |
|---|---|---:|---|---|---|
| QLT-001 | pytest configured and phase-relevant unit/integration/golden suites | 1 onward | `PHASE_1_PLAN.md`; `STRATEGY_SPEC.md` §§16-17 | DOCUMENTED | exact `python -m pytest` result each phase |
| QLT-002 | Ruff lint/format and mypy strict-enough project type check | 1 onward | `PHASE_1_PLAN.md` | DOCUMENTED | exact Ruff/mypy results each phase |
| QLT-003 | Application/migrations run before phase completion claim | 1 onward | `PHASE_1_PLAN.md` | DOCUMENTED | exact startup/health/Alembic commands |
| QLT-004 | Requirements matrix/docs updated with behavior/architecture changes | every phase | this document | DOCUMENTED | diff/review checklist |
| QLT-005 | `.gitignore` excludes env, DB, logs, caches, secrets, private exports | 1 | `PHASE_1_PLAN.md` | DOCUMENTED | ignored-file and secret scan tests/checks |
| QLT-006 | No Git push/force-push/remote/global-config mutation without approval | every phase | `AGENTS.md`; `PHASE_1_PLAN.md` | DOCUMENTED | command log and unchanged remote/config review |
| QLT-007 | SQLite exact-decimal persistence never relies on NUMERIC affinity/TEXT arithmetic | 1 onward | `DATABASE_SCHEMA.md` §1.3; `PHASE_1_PLAN.md` | DOCUMENTED | three vectors, typeof/DDL, ordering/range, UoW balance, forbidden SQL scan |

## 12. Phase 0 deliverables

| ID | Requirement | Target phase | Design document | Status | Evidence |
|---|---|---:|---|---|---|
| P0-001 | Architecture and separation verification | 0 | `ARCHITECTURE.md` §§1-9 | DOCUMENTED | file review/diff |
| P0-002 | Contradiction, ambiguity, and missing-decision register | 0 | `ARCHITECTURE.md` §§10-11 | DOCUMENTED | DR-001..DR-055 and OD-001..OD-006 |
| P0-003 | Exact database design | 0 | `DATABASE_SCHEMA.md` | DOCUMENTED | table/invariant review |
| P0-004 | Versioned API and no Phase 1 live route | 0 | `API_CONTRACTS.md` | DOCUMENTED | availability/denylist contract |
| P0-005 | Proposed research strategy formulas/state/golden cases; sizing still decision-required | 0 | `STRATEGY_SPEC.md` | DOCUMENTED | G-01..G-23; no strategy approval implied |
| P0-006 | Requirements traceability | 0 | `REQUIREMENTS_MATRIX.md` | DOCUMENTED | this matrix |
| P0-007 | Exact Phase 1 file/order/acceptance/test/out-of-scope plan | 0 | `phases/PHASE_1_PLAN.md` | DOCUMENTED | plan review |

## 13. Current implementation statement

At the end of Phase 0, only design documents exist. No application, strategy, accounting engine, PaperBroker, provider, Futu/OpenD integration, external-data connection, backtest, paper order, or live order is implemented or claimed. Rows marked `DOCUMENTED` describe frozen proposals/contracts, not runtime completion.
