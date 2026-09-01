# Requirements Traceability Matrix

Status: Phase 1 accepted after independent post-remediation review — PASS; reviewed commit: `f6decf2fbe171c1b9eb46340a9174bc21f293ede`; reviewed tree: `f03d23ededaef37096b508a3040c87ae69d89e32`; GitHub Actions run: `33458517601`; job: `99703528272`; artifact: `9782355130`; result: `119 passed`

Future-scope authority: `docs/ROADMAP.md` decision `MTF-001`

## 1. Disposition and status rules

| Disposition | Meaning |
|---|---|
| `RETAINED` | Requirement remains in the Phase 0–4 product |
| `SUPERSEDED_MTF` | Earlier future direction is replaced by `MTF-001` |
| `REMOVED_MTF-001` | Permanently outside product scope; not deferred |
| `HISTORICAL_PHASE_1` | Accepted Phase 1 implementation/evidence retained without future authority |

| Status | Meaning |
|---|---|
| `IMPLEMENTED` | Accepted implementation evidence exists |
| `DOCUMENTED` | Authoritative future contract exists but is not implemented |
| `DECISION_REQUIRED` | A separate Task Contract must approve the named choice |
| `OUT_OF_SCOPE` | Permanently removed by `MTF-001` |

Only Phase 0 through Phase 4 are valid target phases.

## 2. Governance and historical baseline

| ID | Requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| GOV-001 | Local-first, single-user, modular monolith | RETAINED | 0–4 | DOCUMENTED | Roadmap 2; Master 3–5 |
| GOV-002 | `MTF-001` supersedes the completed-daily-only future direction without reverting commit `1f724ebe...` | SUPERSEDED_MTF | 0 | DOCUMENTED | Roadmap 1 |
| GOV-003 | Authoritative sequence is exactly Phase 0–4 | SUPERSEDED_MTF | 0 | DOCUMENTED | Roadmap 7; Master 12 |
| GOV-004 | Each implementation task requires explicit approval and stop | RETAINED | 0–4 | DOCUMENTED | Roadmap 9; Master 13 |
| GOV-005 | Phase 0 history and accepted Phase 1 evidence are unchanged | HISTORICAL_PHASE_1 | 0/1 | IMPLEMENTED | Immutable plan/reviews and accepted commit |
| GOV-006 | Phase 1 PASS status remains unchanged | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Run `33458517601`; `119 passed` |
| GOV-007 | Phase 2 work begins only through explicit bounded Task Contracts | RETAINED | 2 | IMPLEMENTED | TASK-003 quote-only PoC; TASK-004 backend; Roadmap 1,7 |

## 3. Accepted Phase 1 requirements

| ID | Requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| P1-001 | FastAPI/SQLite/SQLAlchemy/Alembic modular-monolith foundation | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Accepted Phase 1 review |
| P1-002 | Deterministic migration 0001 and exact Decimal persistence | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Independent migration/Decimal evidence |
| P1-003 | Aware UTC and signed-zero invariants | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Independent regression evidence |
| P1-004 | Canonical Security, Watchlist, Portfolio, opening accounting | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Accepted API/database evidence |
| P1-005 | Opening HKD 20,000, 200 units, NAV 100 | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Seed/accounting evidence |
| P1-006 | Accepted Phase 1 APIs/frontend and inert descriptors | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Accepted OpenAPI/frontend evidence |
| P1-007 | No later-phase behavior retrofitted into Phase 1 | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Accepted boundary and current diff |

## 4. Market data and dashboard requirements

| ID | Requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| MKT-001 | Independent read-only Market Data Provider is allowed | SUPERSEDED_MTF | 2 | IMPLEMENTED | TASK-004 query port; Roadmap 3; Architecture 4 |
| MKT-002 | Provider must not require brokerage-account access | SUPERSEDED_MTF | 2 | IMPLEMENTED | TASK-004 quote-only boundary; Roadmap 2–3; Master 1 |
| MKT-003 | Futu OpenD quote-only APIs are selected for the bounded provider PoC | RETAINED | 2 | IMPLEMENTED | TASK-003 adapter and smoke runner |
| MKT-004 | Live OpenD availability, login, entitlements, pricing, delay, and coverage remain truthful environmental evidence | RETAINED | 2 | DECISION_REQUIRED | TASK-003 live PoC result; Roadmap 3 |
| MKT-005 | Initial tracked set is AVGO, VRT, HK.09698 with US/HK support | RETAINED | 2 | IMPLEMENTED | TASK-004 canonical Security resolution; Roadmap 3 |
| MKT-006 | Daily OHLCV remains supported | RETAINED | 2 | IMPLEMENTED | TASK-004 daily-bars API; Roadmap 7; Database 4.3 |
| MKT-007 | Current-session completed 1-minute OHLCV is supported | SUPERSEDED_MTF | 2 | IMPLEMENTED | TASK-004 minute-bars API; Roadmap 4; Database 4.4 |
| MKT-008 | Unfinished minute bars are excluded | RETAINED | 2 | IMPLEMENTED | TASK-003 adapter tests; TASK-004 API; Roadmap 5 |
| MKT-009 | Latest/intraday price is distinct from final daily close | RETAINED | 2 | IMPLEMENTED | TASK-004 state API/tests; Roadmap 5; Database 1.3 |
| MKT-010 | Missing/delayed/stale/unavailable/error states are explicit | RETAINED | 2 | IMPLEMENTED | TASK-004 provider results/API tests; Roadmap 4–5 |
| MKT-011 | No market value is fabricated | RETAINED | all | DOCUMENTED | `AGENTS.md`; Roadmap 5 |
| MKT-012 | Minute retention policy is deferred to Phase 2 plan | RETAINED | 2 | DECISION_REQUIRED | Roadmap 4 |

| ID | Dashboard requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| UI-001 | Selector, latest price, market status, volume, score, ranking, risk state, timestamps | SUPERSEDED_MTF | 2 | DOCUMENTED | Roadmap 4; Master 9 |
| UI-002 | Daily and 1-minute candles are separate timeframes | SUPERSEDED_MTF | 2 | DOCUMENTED | Roadmap 4; API 5.3–5.4 |
| UI-003 | Timeframe tab/button switches views; no same-coordinate overlay | RETAINED | 2 | DOCUMENTED | Roadmap 4; Architecture 5 |
| UI-004 | Active visible session refreshes/recalculates approximately every 60 seconds | SUPERSEDED_MTF | 2 | DOCUMENTED | Roadmap 5; Architecture 6 |
| UI-005 | Polling requests do not overlap | RETAINED | 2 | DOCUMENTED | Roadmap 5; API 5.5 |
| UI-006 | Hidden page pauses polling; visible page refreshes immediately | RETAINED | 2 | DOCUMENTED | Roadmap 5; API 5.5 |
| UI-007 | Manual `刷新最新行情` is provided | RETAINED | 2 | DOCUMENTED | Roadmap 5; API 5.5 |
| UI-008 | Automatic-refresh countdown is displayed | RETAINED | 2 | DOCUMENTED | Roadmap 5; API 5.5 |
| UI-009 | Closing the page requires no background processing | RETAINED | 2 | DOCUMENTED | Roadmap 5; Architecture 6 |
| UI-010 | Ordinary HTTP/REST polling is MVP transport | RETAINED | 2 | DOCUMENTED | Roadmap 5; API 5.5 |

## 5. Time and Composite Score requirements

| ID | Requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| TIME-001 | `latest_quote_at` is explicit | RETAINED | 2 | IMPLEMENTED | TASK-004 state API; Roadmap 5; API 2 |
| TIME-002 | `latest_completed_minute_bar_at` is explicit | RETAINED | 2 | IMPLEMENTED | TASK-004 minute-bars API; Roadmap 5; API 2 |
| TIME-003 | `latest_completed_daily_session` is explicit | RETAINED | 2 | IMPLEMENTED | TASK-004 daily-bars API; Roadmap 5; API 2 |
| TIME-004 | `score_calculated_at` is explicit | RETAINED | 2 | DOCUMENTED | Roadmap 5; API 2 |
| TIME-005 | Provider latency and polling cadence are different facts | RETAINED | 2 | DOCUMENTED | Roadmap 5; API 2 |
| QNT-001 | Composite architecture is Daily Base + Intraday Minute Adjustment | SUPERSEDED_MTF | 2 | DOCUMENTED | Roadmap 6; Strategy 3 |
| QNT-002 | Daily component may represent medium-term trend/momentum/volatility/drawdown/risk | RETAINED | 2 | DECISION_REQUIRED | Roadmap 6; Strategy 3.1 |
| QNT-003 | Minute component may represent current-session strength/risk | SUPERSEDED_MTF | 2 | DECISION_REQUIRED | Roadmap 6; Strategy 3.2 |
| QNT-004 | Formula, weights, thresholds, bands, normalization, and sizing are unapproved | RETAINED | 2 | DECISION_REQUIRED | Roadmap 6; Strategy 6 |
| QNT-005 | Strategy remains PROPOSED / RESEARCH_UNVALIDATED | RETAINED | 2–4 | DOCUMENTED | Strategy status |
| QNT-006 | Earlier completed-daily-only formula proposal is not implementation authority | SUPERSEDED_MTF | 2 | DOCUMENTED | Strategy 1 |
| QNT-007 | Score/ranking/risk state refresh approximately every 60 seconds while visible | SUPERSEDED_MTF | 2 | DOCUMENTED | Roadmap 5; API 5.5 |
| QNT-008 | No profitability claim | RETAINED | 2–4 | DOCUMENTED | Strategy 1,7 |

## 6. Later research and analytics requirements

| ID | Requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| PAP-001 | Lightweight paper state is simulated only | RETAINED | 3 | DOCUMENTED | Roadmap 7; Database 5 |
| PAP-002 | Paper positions update only from confirmed PaperFill | RETAINED | 3 | DOCUMENTED | `AGENTS.md`; Architecture 8 |
| PAP-003 | Richer factors, explanation, ranking/risk analytics, signal history, paper performance | RETAINED | 3 | DOCUMENTED | Roadmap 7 |
| BT-001 | Deterministic backtesting with point-in-time controls | RETAINED | 4 | DOCUMENTED | Roadmap 7; Database 6 |
| BT-002 | Transaction costs, benchmark, drawdown, volatility, turnover, attribution, exposure | RETAINED | 4 | DOCUMENTED | Roadmap 7 |
| BT-003 | Daily-bar backtesting is baseline | RETAINED | 4 | DOCUMENTED | Roadmap 7; Master 10 |
| BT-004 | Current minute display does not require historical minute/tick simulation | RETAINED | 4 | DOCUMENTED | Roadmap 7; API 7 |
| BT-005 | Phase 4 is the final product phase | SUPERSEDED_MTF | 4 | DOCUMENTED | Roadmap 7 |

## 7. Permanently removed capabilities

| ID | Removed capability | Disposition | Status |
|---|---|---|---|
| REM-001 | Legacy real completed-trade record and entry/import | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-002 | Legacy external account observations and brokerage synchronization | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-003 | Brokerage-account cash/positions/orders/trades access | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-004 | Real-account matching/discrepancy handling | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-005 | Real portfolio tracking and real Current versus Target state | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-006 | Real trade sizing, fees, taxes, or settlement synchronization | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-007 | Futu or other broker-account integration | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-008 | Broker writes, real-order API/UI, Live OMS/EMS | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-009 | Password unlock, buying-power reservation, execution retry/recovery/workers/kill switch | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-010 | Autonomous or unattended trading | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-011 | Microservices, Kafka, distributed workers, Kubernetes, multi-tenancy, 24/7 execution | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-012 | Any authoritative phase after Phase 4 | REMOVED_MTF-001 | OUT_OF_SCOPE |

Read-only current-session minute data and intraday score calculation are expressly not removed;
they are non-executing Phase 2 research capabilities.

## 8. Current implementation statement

Phase 1 remains accepted with `119 passed` in independent GitHub Actions run `33458517601`.

TASK-003 implements the Futu OpenD quote-only provider PoC. TASK-004 adds a provider-neutral
read-through application service and the state, completed daily-bars, and completed current-session
minute-bars APIs, with no production market-data persistence. No daily/minute chart, 60-second
polling, dashboard refresh behavior, Composite Quant Score, ranking/risk calculation, paper
behavior, or backtest behavior is implemented or claimed.
