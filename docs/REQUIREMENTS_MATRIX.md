# Requirements Traceability Matrix

Status: Phase 1 accepted after independent post-remediation review — PASS; reviewed commit: `f6decf2fbe171c1b9eb46340a9174bc21f293ede`; reviewed tree: `f03d23ededaef37096b508a3040c87ae69d89e32`; GitHub Actions run: `33458517601`; job: `99703528272`; artifact: `9782355130`; result: `119 passed`

Future-scope authority: `docs/ROADMAP.md` decision `EOD-001`

## 1. Disposition and status rules

| Disposition | Meaning |
|---|---|
| `RETAINED` | Requirement remains and is assigned to authoritative Phase 0–5 |
| `REPLACED_EOD` | Older future requirement is replaced by the named EOD/no-live equivalent |
| `REMOVED_EOD-001` | Permanently outside product scope; never deferred |
| `HISTORICAL_PHASE_1` | Accepted Phase 1 implementation/evidence retained without future authority |

| Status | Meaning |
|---|---|
| `IMPLEMENTED` | Accepted implementation evidence exists for the complete listed scope |
| `DOCUMENTED` | Authoritative future contract exists but is not implemented |
| `DECISION_REQUIRED` | A named choice must be approved before its target phase |
| `OUT_OF_SCOPE` | Permanently removed by `EOD-001` |

Only Phase 0 through Phase 5 are valid target phases.

## 2. Governance and historical baseline

| ID | Requirement | Disposition | Phase | Status | Evidence/acceptance |
|---|---|---|---:|---|---|
| GOV-001 | Local-first, single-user, single-process modular monolith | RETAINED | 0–5 | DOCUMENTED | Roadmap sections 2,8; Architecture sections 1,9 |
| GOV-002 | EOD/no-live decision governs every future phase | REPLACED_EOD | 0 | DOCUMENTED | `EOD-001` and supersession language in all authoritative specs |
| GOV-003 | Authoritative Roadmap contains exactly Phase 0–5 | REPLACED_EOD | 0 | DOCUMENTED | Roadmap section 9 |
| GOV-004 | Future phase requires explicit approval and plan; stop after each phase | RETAINED | 0–5 | DOCUMENTED | Roadmap section 10; Master section 18 |
| GOV-005 | Phase 0 design and accepted Phase 1 evidence remain historical facts | HISTORICAL_PHASE_1 | 0/1 | IMPLEMENTED | Immutable review files and accepted commit/tree |
| GOV-006 | Phase 1 acceptance status remains PASS | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Independent run 33458517601; 119 passed |
| GOV-007 | Abstract Phase 1 broker-write signatures are artifacts, not implementation authority | REPLACED_EOD | 1 | DOCUMENTED | Roadmap section 1; Architecture section 4 |
| GOV-008 | Preserve unrelated work and require explicit push authority | RETAINED | all | DOCUMENTED | `AGENTS.md` and Git evidence |

## 3. Accepted Phase 1 requirements

| ID | Requirement | Disposition | Phase | Status | Evidence/acceptance |
|---|---|---|---:|---|---|
| P1-001 | CPython/FastAPI/SQLite modular-monolith foundation | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Accepted Phase 1 review |
| P1-002 | Explicit deterministic Alembic revision and pristine configuration behavior | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | H1/H2 independent evidence |
| P1-003 | Exact Decimal: SQLite canonical TEXT, PostgreSQL NUMERIC portability | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Required vectors and PostgreSQL migration evidence |
| P1-004 | Aware UTC persistence and positive signed zero | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Independent regression evidence |
| P1-005 | Vendor-neutral canonical Security and fail-closed user identities | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Security/API/database tests |
| P1-006 | Opening HKD 20,000, 200 units, NAV 100 and balanced ledger | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Seed/accounting evidence |
| P1-007 | Security/watchlist administration and read-only portfolio/status APIs | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Accepted OpenAPI/test evidence |
| P1-008 | Inert broker/provider descriptors with no connection side effect | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Architecture/status tests |
| P1-009 | No Phase 2 behavior retrofitted into Phase 1 | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Accepted phase boundary |

## 4. EOD operating and data requirements

| ID | Requirement | Disposition | Phase | Status | Evidence/acceptance |
|---|---|---|---:|---|---|
| EOD-001 | Completed daily OHLCV only | REPLACED_EOD | 3 | DOCUMENTED | Roadmap section 3; Database section 5.1 |
| EOD-002 | Adjusted daily prices with adjustment provenance | RETAINED | 3 | DOCUMENTED | Master section 8; Database section 5.1 |
| EOD-003 | Completed session date, calendar, and market timezone | REPLACED_EOD | 3 | DOCUMENTED | Architecture section 6.1; API section 2.2 |
| EOD-004 | EOD FX with source/version/availability | REPLACED_EOD | 3 | DOCUMENTED | Database section 5.2 |
| EOD-005 | Optional daily fundamental/valuation snapshots | REPLACED_EOD | 3 | DECISION_REQUIRED | OD-EOD-001 source approval |
| EOD-006 | Daily event/corporate-action observations | REPLACED_EOD | 3 | DOCUMENTED | Database section 5.3 |
| EOD-007 | Point-in-time `available_at <= data_as_of` | RETAINED | 3/4/5 | DOCUMENTED | Master section 8 |
| EOD-008 | Cross-market report exposes differing completed-session dates | REPLACED_EOD | 3 | DOCUMENTED | Roadmap section 3; API section 6 |
| EOD-009 | Incomplete same-day data cannot become official | REPLACED_EOD | 3 | DOCUMENTED | Database section 1.2; API contract tests |
| EOD-010 | Manual MVP analysis trigger after close | REPLACED_EOD | 3 | DOCUMENTED | Roadmap section 2 |
| EOD-011 | Optional scheduler may only fetch, calculate, report, and notify | REPLACED_EOD | 3 | DOCUMENTED | Roadmap section 2; Architecture section 9 |
| EOD-012 | Missing/stale data is explicit and never fabricated | RETAINED | all | DOCUMENTED | Master sections 4,8 |
| EOD-013 | Legitimate data source/entitlement required | RETAINED | 3 | DECISION_REQUIRED | OD-EOD-001 |

## 5. Composite score and decision-support requirements

| ID | Requirement | Disposition | Phase | Status | Evidence/acceptance |
|---|---|---|---:|---|---|
| QNT-001 | One Composite Quant Score per tracked security/completed session | REPLACED_EOD | 3 | DOCUMENTED | Roadmap section 4.1; Database section 5.5 |
| QNT-002 | Score scale 0–100 with interpretable component breakdown | RETAINED | 3 | DOCUMENTED | API section 6.4 |
| QNT-003 | Coverage/quality, missing inputs, explanation, risk flags | RETAINED | 3 | DOCUMENTED | Roadmap section 4.1 |
| QNT-004 | Interpretable advisory classification vocabulary | REPLACED_EOD | 3 | DECISION_REQUIRED | Roadmap section 4.1; final labels require Strategy Spec approval |
| QNT-005 | Target weight plus optional suggested amount/estimated quantity | REPLACED_EOD | 3 | DOCUMENTED | API sections 6.4–6.6 |
| QNT-006 | Suggested quantity exposes price/FX/lot/minimum/cost/liquidity assumptions | REPLACED_EOD | 3/5 | DOCUMENTED | API section 2.3 |
| QNT-007 | Session, generated/data-as-of, provenance, and expiration | REPLACED_EOD | 3 | DOCUMENTED | Database section 5.5 |
| QNT-008 | Formulae/weights/thresholds require separate Strategy Spec approval | RETAINED | 3 | DECISION_REQUIRED | OD-EOD-004; Strategy status |
| QNT-009 | Strategy uses completed daily data only | REPLACED_EOD | 3 | DOCUMENTED | Strategy section 1 |
| QNT-010 | Advisory output never automatically becomes an order or accounting fact | REPLACED_EOD | 3/5 | DOCUMENTED | Roadmap sections 4.2,5; API section 6.8 |
| QNT-011 | No profitability or predictive-validity claim | RETAINED | 3/4 | DOCUMENTED | Strategy sections 1,17 |

## 6. Portfolio summary and recommendation requirements

| ID | Requirement | Disposition | Phase | Status | Evidence/acceptance |
|---|---|---|---:|---|---|
| DEC-001 | One Daily Portfolio Decision Summary per portfolio/report run | REPLACED_EOD | 3 | DOCUMENTED | Roadmap section 4.2; Database section 5.8 |
| DEC-002 | Current Portfolio and current weights | RETAINED | 3/5 | DOCUMENTED | API section 6.7 |
| DEC-003 | Target Portfolio and target weights | REPLACED_EOD | 3 | DOCUMENTED | Database sections 5.6,5.8 |
| DEC-004 | Current versus Target deviations | REPLACED_EOD | 3/5 | DOCUMENTED | Roadmap section 4.2 |
| DEC-005 | Rebalance Suggestions | REPLACED_EOD | 3/5 | DOCUMENTED | Database section 5.7; API section 6.6 |
| DEC-006 | Suggested buy/sell amount and estimated quantity | REPLACED_EOD | 3/5 | DOCUMENTED | API section 6.6 |
| DEC-007 | Estimated cash impact, concentration, exposure, and aggregate risk | RETAINED | 3/5 | DOCUMENTED | Roadmap section 4.2 |
| DEC-008 | Price/FX/lot/fee/tax/liquidity/stale-data warnings | REPLACED_EOD | 3/5 | DOCUMENTED | API section 6.7 |
| DEC-009 | Recommendation acknowledgement/rejection is metadata only | REPLACED_EOD | 3 | DOCUMENTED | API section 6.8 |
| DEC-010 | User executes every real trade in broker official client | REPLACED_EOD | 3/5 | DOCUMENTED | Roadmap sections 2,9 |

## 7. Portfolio accounting and paper-only requirements

| ID | Requirement | Disposition | Phase | Status | Evidence/acceptance |
|---|---|---|---:|---|---|
| ACC-001 | Append-only balanced ledger and explicit reversals | RETAINED | 2 | DOCUMENTED | Database sections 4,8 |
| ACC-002 | Deposits/withdrawals separate from return with unitized NAV/TWR | RETAINED | 2 | DOCUMENTED | Master section 9 |
| ACC-003 | Cash by currency and explicit FX | RETAINED | 2 | DOCUMENTED | Roadmap Phase 2 |
| ACC-004 | Fees, taxes, settlements, cost basis, realized/unrealized P&L | RETAINED | 2 | DOCUMENTED | Database section 4.1 |
| ACC-005 | Complete `FLOW_PRE` valuation required with positions | RETAINED | 2 | DOCUMENTED | Master section 9 |
| ACC-006 | Deterministic snapshots and performance | RETAINED | 2/4 | DOCUMENTED | Database sections 4,6 |
| PAP-001 | PaperOrder/PaperFill are simulated only and never sent to broker | REPLACED_EOD | 2 | DOCUMENTED | Roadmap section 5.1; Database sections 4.2–4.3 |
| PAP-002 | PaperFill uses explicit EOD/manual price source and assumptions | REPLACED_EOD | 2 | DECISION_REQUIRED | OD-EOD-003 |
| PAP-003 | Lightweight paper bookkeeping; no real-time paper exchange | REPLACED_EOD | 2 | DOCUMENTED | Roadmap Phase 2 |
| PAP-004 | No intraday matching or market-microstructure simulation | REMOVED_EOD-001 | — | OUT_OF_SCOPE | `EOD-001` |
| PAP-005 | Idempotency, reversal, and reconciliation foundations | RETAINED | 2 | DOCUMENTED | Architecture section 7 |
| PAP-006 | Paper and real facts use separate schemas/UI language | REPLACED_EOD | 2/5 | DOCUMENTED | Roadmap section 5 |

## 8. Daily-bar backtesting and analytics

| ID | Requirement | Disposition | Phase | Status | Evidence/acceptance |
|---|---|---|---:|---|---|
| BT-001 | Deterministic daily-bar backtest with PIT controls | REPLACED_EOD | 4 | DOCUMENTED | Master section 12 |
| BT-002 | Versioned EOD execution-price assumptions | REPLACED_EOD | 4 | DOCUMENTED | Database section 6 |
| BT-003 | Fees/taxes/FX/cost assumptions and before/after-cost result | RETAINED | 4 | DOCUMENTED | Roadmap Phase 4 |
| BT-004 | Benchmark, attribution, drawdown, volatility, turnover, exposure | RETAINED | 4 | DOCUMENTED | Roadmap Phase 4 |
| BT-005 | Reproducibility hashes and anti-look-ahead evidence | RETAINED | 4 | DOCUMENTED | API section 7 |
| BT-006 | Scenario/stress analysis where justified | RETAINED | 4 | DOCUMENTED | Roadmap Phase 4 |
| BT-007 | Intraday backtest and microstructure simulation | REMOVED_EOD-001 | — | OUT_OF_SCOPE | `EOD-001` |
| BT-008 | Phase 4 completes Core MVP | REPLACED_EOD | 4 | DOCUMENTED | Roadmap section 9 |

## 9. Completed real-trade tracking and read-only broker requirements

| ID | Requirement | Disposition | Phase | Status | Evidence/acceptance |
|---|---|---|---:|---|---|
| REAL-001 | ManualRealTradeRecord stores an already completed trade | REPLACED_EOD | 5 | DOCUMENTED | Roadmap section 5.3; Database section 7.1 |
| REAL-002 | Actual execution time/price/quantity/currency/fees/tax/provenance | REPLACED_EOD | 5 | DOCUMENTED | API section 8.1 |
| REAL-003 | Manual entry and CSV/file import are first-class | REPLACED_EOD | 5 | DOCUMENTED | Roadmap section 6 |
| REAL-004 | Manual cash-flow records | RETAINED | 5 | DOCUMENTED | Roadmap Phase 5 |
| BR-001 | BrokerObservation is immutable and read-only | REPLACED_EOD | 5 | DOCUMENTED | Roadmap section 5.4; Database section 7.2 |
| BR-002 | Optional connector may read account/cash/positions/completed orders/trades/fees/taxes/settlements | REPLACED_EOD | 5 | DOCUMENTED | Master section 13 |
| BR-003 | Reconciliation/discrepancy handling never silently overwrites | RETAINED | 5 | DOCUMENTED | Database section 7.3 |
| BR-004 | Product remains usable without broker connection | REPLACED_EOD | 5 | DOCUMENTED | Roadmap section 6 |
| BR-005 | Connector must prove least-privilege read-only authority | REPLACED_EOD | 5 | DECISION_REQUIRED | OD-EOD-005 |
| BR-006 | External IDs exist only for observed/imported completed facts | REPLACED_EOD | 5 | DOCUMENTED | Database sections 7.1–7.2 |
| BR-007 | No write-capable credentials in normal application code | REPLACED_EOD | 5 | DOCUMENTED | Roadmap section 6; Master section 16 |

## 10. API, UI, quality, and infrastructure

| ID | Requirement | Disposition | Phase | Status | Evidence/acceptance |
|---|---|---|---:|---|---|
| API-001 | Stable versioned schemas, Problem errors, Decimal strings, UTC | RETAINED | 1–5 | DOCUMENTED | API sections 1–2 |
| API-002 | Accepted Phase 1 allowlist remains unchanged | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Independent OpenAPI evidence |
| API-003 | Future EOD/score/target/summary reads | REPLACED_EOD | 3 | DOCUMENTED | API section 6 |
| API-004 | Paper/accounting mutations remain internal | REPLACED_EOD | 2 | DOCUMENTED | API section 5 |
| API-005 | Completed real-trade import/read-only sync/reconciliation | REPLACED_EOD | 5 | DOCUMENTED | API section 8 |
| UI-001 | EOD terminal shows score components, summary, Current/Target, suggestions | REPLACED_EOD | 3/5 | DOCUMENTED | Master section 15 |
| UI-002 | Paper simulation and completed real trades are visually distinct | REPLACED_EOD | 2/5 | DOCUMENTED | Roadmap section 5 |
| UI-003 | No real-order submission control | REMOVED_EOD-001 | — | OUT_OF_SCOPE | `EOD-001` |
| INF-001 | Local FastAPI + SQLite + manual/simple EOD batch is sufficient | REPLACED_EOD | 0–5 | DOCUMENTED | Roadmap section 8 |
| INF-002 | PostgreSQL compatibility is portability, not deployment requirement | REPLACED_EOD | 0–5 | DOCUMENTED | Master section 16 |
| QLT-001 | pytest/Ruff/mypy and relevant executable path per phase | RETAINED | 1–5 | DOCUMENTED | `AGENTS.md`; Master section 18 |
| QLT-002 | Requirements/docs updated with actual evidence | RETAINED | all | DOCUMENTED | This matrix |
| QLT-003 | No secrets/private exports committed | RETAINED | all | DOCUMENTED | `AGENTS.md` |
| QLT-004 | Scope scan rejects invalid future residual requirements | REPLACED_EOD | all | DOCUMENTED | Roadmap governance |

## 11. Permanently removed capabilities

| ID | Removed requirement/capability | Disposition | Decision |
|---|---|---|---|
| REM-001 | Real-time quotes, tick data, order books, streaming/WebSocket, minute bars | REMOVED_EOD-001 | `EOD-001` |
| REM-002 | Intraday calculations, rebalancing, or continuous execution monitoring | REMOVED_EOD-001 | `EOD-001` |
| REM-003 | Application-submitted real orders or real-order UI/API | REMOVED_EOD-001 | `EOD-001` |
| REM-004 | Real `place_order`, `cancel_order`, `modify_order` or broker-write adapter | REMOVED_EOD-001 | `EOD-001` |
| REM-005 | Live OMS/EMS and broker-side order state machine | REMOVED_EOD-001 | `EOD-001` |
| REM-006 | Broker-side cash reservation or account selection for execution | REMOVED_EOD-001 | `EOD-001` |
| REM-007 | Real-order approval, submission, retry, recovery, failover, worker | REMOVED_EOD-001 | `EOD-001` |
| REM-008 | Execution kill switch and trade-password unlock | REMOVED_EOD-001 | `EOD-001` |
| REM-009 | Unattended/autonomous trading or agents | REMOVED_EOD-001 | `EOD-001` |
| REM-010 | EastMoney trading integration | REMOVED_EOD-001 | `EOD-001` |
| REM-011 | Microservices, queues, Kubernetes, cloud HA, multi-tenancy, distributed execution | REMOVED_EOD-001 | `EOD-001` |
| REM-012 | Any authoritative phase after Phase 5 | REMOVED_EOD-001 | `EOD-001` |

## 12. Current implementation statement

Phase 1 is accepted. Independent evidence for the reviewed implementation commit records
`119 passed` on GitHub Actions run `33458517601`.

Phase 2 has not begun. No PaperOrder/PaperFill behavior, EOD data ingestion, Composite Quant Score,
Target Portfolio, Daily Portfolio Decision Summary, backtest, ManualRealTradeRecord, broker
connector, or reconciliation behavior is implemented or claimed by this documentation refactor.
