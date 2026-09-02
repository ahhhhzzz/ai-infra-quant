# Requirements Traceability Matrix

Status: Phase 1 accepted after independent post-remediation review — PASS; reviewed commit: `f6decf2fbe171c1b9eb46340a9174bc21f293ede`; reviewed tree: `f03d23ededaef37096b508a3040c87ae69d89e32`; GitHub Actions run: `33458517601`; job: `99703528272`; artifact: `9782355130`; result: `119 passed`

Future-scope authority: `docs/ROADMAP.md` decisions `MTF-001` and `PAQS-MVP-001`

Decision record: `docs/decisions/PAQS_MVP_SCOPE_REDUCTION.md`

## 1. Disposition and status rules

| Disposition | Meaning |
|---|---|
| `RETAINED` | Requirement remains in the current Phase 0–4 architecture/current MVP |
| `SUPERSEDED_MTF` | Earlier future direction was replaced by `MTF-001` |
| `SUPERSEDED_PAQS_MVP` | Earlier future direction is replaced by `PAQS-MVP-001` |
| `OPTIONAL_FUTURE` | Valid extension capability but not current committed MVP work; explicit reactivation required |
| `REMOVED_MTF-001` | Permanently outside product scope; not deferred |
| `HISTORICAL_PHASE_1` | Accepted Phase 1 implementation/evidence retained without future authority |

| Status | Meaning |
|---|---|
| `IMPLEMENTED` | Accepted implementation evidence exists |
| `PARTIAL` | Part of the requirement is accepted/implemented and future work remains |
| `DOCUMENTED` | Authoritative future contract/direction exists but implementation is not yet approved/completed |
| `PLANNED_TASK` | Identifier/scope direction is recorded, but an explicit Task Contract is still required |
| `DECISION_REQUIRED` | A separate explicit decision/Task Contract must approve the named choice |
| `DORMANT_OPTIONAL` | Not current committed work; may be reactivated later by explicit approval |
| `OUT_OF_SCOPE` | Permanently removed/forbidden |

Only Phase 0 through Phase 4 are valid target phases.

## 2. Governance and historical baseline

| ID | Requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| GOV-001 | Local-first, single-user, modular monolith | RETAINED | 0–4 | DOCUMENTED | Roadmap 2; Master 1–5 |
| GOV-002 | `MTF-001` supersedes the completed-daily-only future direction without rewriting history | SUPERSEDED_MTF | 0 | DOCUMENTED | Roadmap 1 |
| GOV-003 | `PAQS-MVP-001` makes the Phase 2 PAQS Decision Terminal the current product-completion line | SUPERSEDED_PAQS_MVP | 2 | DOCUMENTED | Roadmap 7–8; decision record |
| GOV-004 | Authoritative phase sequence remains exactly Phase 0–4; no Phase 5 | RETAINED | 0–4 | DOCUMENTED | Roadmap 7; Master 12 |
| GOV-005 | Every implementation task requires explicit approval, Task Contract, independent review and stop | RETAINED | 0–4 | DOCUMENTED | Roadmap 10; Master 13 |
| GOV-006 | Phase 0 history and accepted Phase 1 evidence remain unchanged | HISTORICAL_PHASE_1 | 0/1 | IMPLEMENTED | Immutable Phase 1 plan/reviews |
| GOV-007 | Phase 1 PASS status remains unchanged | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Run `33458517601`; `119 passed` |
| GOV-008 | `TASK-006` is umbrella only; TASK-006A–006E are individually approved bounded tasks | RETAINED | 2 | PLANNED_TASK | Roadmap 7; decision record |
| GOV-009 | Phase 3/4 remain dormant optional extension slots until explicitly reactivated | SUPERSEDED_PAQS_MVP | 3–4 | DORMANT_OPTIONAL | Roadmap 7–8 |

## 3. Accepted Phase 1 requirements

| ID | Requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| P1-001 | FastAPI/SQLite/SQLAlchemy/Alembic modular-monolith foundation | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Accepted Phase 1 review |
| P1-002 | Deterministic migration 0001 and exact Decimal persistence | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Independent migration/Decimal evidence |
| P1-003 | Aware UTC and signed-zero invariants | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Independent regression evidence |
| P1-004 | Canonical Security, Watchlist, Portfolio, opening accounting | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Accepted API/database evidence |
| P1-005 | Opening HKD 20,000, 200 units, NAV 100 | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Seed/accounting evidence |
| P1-006 | Accepted Phase 1 APIs/frontend and inert descriptors | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Accepted frontend/API evidence |
| P1-007 | No later-phase behavior retrofitted into Phase 1 historical evidence | HISTORICAL_PHASE_1 | 1 | IMPLEMENTED | Accepted boundary |

## 4. Market data, supported securities and Dashboard requirements

| ID | Requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| MKT-001 | Independent read-only Market Data Provider is allowed | SUPERSEDED_MTF | 2 | IMPLEMENTED | TASK-004 query port; Roadmap 3 |
| MKT-002 | Provider path requires no brokerage-account access | RETAINED | 2 | IMPLEMENTED | TASK-003/004 quote-only boundary |
| MKT-003 | Futu OpenD quote-only APIs are selected for current provider path | RETAINED | 2 | IMPLEMENTED | TASK-003 adapter |
| MKT-004 | Live OpenD availability/login/entitlements/delay/coverage remain truthful environment facts | RETAINED | 2 | DECISION_REQUIRED | TASK-003/005B smoke evidence |
| MKT-005 | AVGO/VRT/HK.09698 are accepted initial PoC symbols | RETAINED | 2 | IMPLEMENTED | TASK-004/005B |
| MKT-006 | User-manageable supported US/HK equities replace the three-symbol PoC restriction | SUPERSEDED_PAQS_MVP | 2 | IMPLEMENTED | TASK-006A supported-security API/UI/tests |
| MKT-007 | Daily OHLCV supports bounded 1300-session Dashboard history | RETAINED | 2 | IMPLEMENTED | TASK-005B |
| MKT-008 | Recent 30-calendar-day completed 1-minute OHLCV is supported | RETAINED | 2 | IMPLEMENTED | TASK-005B |
| MKT-009 | US minute retrieval uses `Session.ALL`; PAQS initial M30 filters regular session | RETAINED | 2 | IMPLEMENTED | TASK-005B; TASK-006A M30 tests |
| MKT-010 | Unfinished minute bars are excluded | RETAINED | 2 | IMPLEMENTED | adapter/API tests |
| MKT-011 | Latest/intraday price is distinct from completed Daily close | RETAINED | 2 | IMPLEMENTED | TASK-004 state/API tests |
| MKT-012 | Missing/delayed/stale/unavailable/error states are explicit; no market value fabricated | RETAINED | all | IMPLEMENTED | provider result/API contracts plus AGENTS |
| MKT-013 | TASK-006A prepares provider-neutral trading calendar/session/coverage/adjustment metadata | RETAINED | 2 | IMPLEMENTED | Calendar port, PAQS bundle/diagnostic tests |
| MKT-014 | Initial PAQS timeframe input is W1/D1/30m regular session; H1/H4 are not MVP requirements | SUPERSEDED_PAQS_MVP | 2 | DOCUMENTED | PAQS v0.3.1; Roadmap 5/7 |

| ID | Dashboard requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| UI-001 | Selector/latest/market status/Daily/1m/volume/timestamps | RETAINED | 2 | IMPLEMENTED | TASK-005/005B |
| UI-002 | Daily and 1-minute candles remain separate chart timeframes | RETAINED | 2 | IMPLEMENTED | TASK-005 |
| UI-003 | Visible-page ~60s refresh, no overlapping requests, hidden pause/resume | RETAINED | 2 | IMPLEMENTED | TASK-005 |
| UI-004 | Manual refresh and countdown | RETAINED | 2 | IMPLEMENTED | TASK-005 |
| UI-005 | Dynamic supported US/HK add/remove flow is user-facing rather than backend-only | SUPERSEDED_PAQS_MVP | 2 | IMPLEMENTED | TASK-006A Dashboard form and integration tests |
| UI-006 | PAQS context/setup/advisory/invalidation/target/RR presentation | RETAINED | 2 | PLANNED_TASK | TASK-006E planned scope |
| UI-007 | No real-order UI/control and no claim user executed advisory | RETAINED | all | DOCUMENTED | Roadmap/Master safety boundary |

## 5. PAQS / Score requirements and task map

| ID | Requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| PAQS-001 | PAQS state/hard-gate engine is primary causal decision system | SUPERSEDED_PAQS_MVP | 2 | DOCUMENTED | Roadmap 6; Strategy |
| PAQS-002 | Numerical Quality/Composite Score is derived only and cannot override PAQS hard gates | SUPERSEDED_PAQS_MVP | 2 | DOCUMENTED | Roadmap 6; PAQS v0.3.1 |
| PAQS-003 | `TASK-006` is umbrella only | RETAINED | 2 | PLANNED_TASK | Roadmap 7 |
| PAQS-004 | TASK-006A — Dynamic US/HK Securities & PAQS Input Foundation | RETAINED | 2 | IMPLEMENTED | Dynamic add, calendar, W1/M30, diagnostics, guides |
| PAQS-005 | TASK-006B — PAQS Structure Engine | RETAINED | 2 | PARTIAL | Task-branch Decimal ATR/Pivot/Swing/Level/Zone/Range/Base-Regime engine, structure API and deterministic tests; independent review and live human checkpoint pending |
| PAQS-006 | TASK-006C — PAQS Event Engine | RETAINED | 2 | PLANNED_TASK | Roadmap 7 |
| PAQS-007 | TASK-006D — PAQS Setup & Risk Engine | RETAINED | 2 | PLANNED_TASK | Roadmap 7 |
| PAQS-008 | TASK-006E — PAQS Advisory & Decision Dashboard | RETAINED | 2 | PLANNED_TASK | Roadmap 7 |
| PAQS-009 | Manual real-market structure checkpoint is required after 006B before 006C authorization | RETAINED | 2 | DOCUMENTED | Roadmap 7; decision record |
| PAQS-010 | Entry/Hold/Exit advisory remains conditional decision support without brokerage position knowledge | RETAINED | 2 | DOCUMENTED | Strategy/PAQS v0.3.1 |
| PAQS-011 | Exact score/quality/ranking formula remains unapproved | RETAINED | 2 | DECISION_REQUIRED | Strategy |
| PAQS-012 | No profitability/Alpha/probability claim from tests or backtests | RETAINED | 2–4 | DOCUMENTED | Strategy/AGENTS |

Earlier score-level governance remains recorded for compatibility:

```text
Composite Quant Score = Daily Base Score + Intraday Minute Adjustment
```

but `PAQS-MVP-001` makes it a derived presentation/ranking concept if retained, not the causal strategy engine.

## 6. Optional future extensions

| ID | Requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| PAP-001 | Simulated Paper Portfolio / PaperFill bookkeeping | OPTIONAL_FUTURE | 3 | DORMANT_OPTIONAL | Roadmap 7–8 |
| PAP-002 | Paper NAV/performance/accounting | OPTIONAL_FUTURE | 3 | DORMANT_OPTIONAL | Roadmap 7–8 |
| PAP-003 | Position sizing / exposure / correlation controls | OPTIONAL_FUTURE | 3 | DORMANT_OPTIONAL | Roadmap 7–8 |
| RES-001 | Broader factor/research expansion | OPTIONAL_FUTURE | 3 | DORMANT_OPTIONAL | Roadmap 7–8 |
| BT-001 | Deterministic point-in-time backtesting platform | OPTIONAL_FUTURE | 4 | DORMANT_OPTIONAL | Roadmap 7–8 |
| BT-002 | Transaction costs / benchmark comparison | OPTIONAL_FUTURE | 4 | DORMANT_OPTIONAL | Roadmap 7–8 |
| BT-003 | Drawdown/volatility/turnover/attribution/exposure analytics | OPTIONAL_FUTURE | 4 | DORMANT_OPTIONAL | Roadmap 7–8 |
| BT-004 | Portfolio optimization / broad parameter-analysis/reporting suite | OPTIONAL_FUTURE | 4 | DORMANT_OPTIONAL | Roadmap 7–8 |
| BT-005 | Phase 4 remains final possible phase; no Phase 5 | RETAINED | 4 | DOCUMENTED | Roadmap 7 |

These optional capabilities are not required to call the current product complete after Phase 2 TASK-006E. They may be reactivated later without changing the permanent read-only/no-broker boundary.

## 7. Permanently removed capabilities

| ID | Removed capability | Disposition | Status |
|---|---|---|---|
| REM-001 | Legacy real completed-trade record and import | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-002 | External real-account observation/synchronization | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-003 | Brokerage cash/positions/orders/trades access | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-004 | Real-account matching/discrepancy handling | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-005 | Real portfolio tracking / Current-vs-Target from broker state | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-006 | Real trade sizing/fees/taxes/settlement synchronization | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-007 | Broker-account integration | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-008 | Broker writes / real-order API/UI / Live OMS/EMS | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-009 | Password unlock / buying-power reservation / execution workers/retries/kill switch | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-010 | Autonomous or unattended trading | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-011 | Microservices/Kafka/distributed workers/Kubernetes/multi-tenancy/24×7 execution | REMOVED_MTF-001 | OUT_OF_SCOPE |
| REM-012 | Any authoritative Phase after Phase 4 | REMOVED_MTF-001 | OUT_OF_SCOPE |

## 8. Current implementation statement

Phase 1 remains accepted with `119 passed` in independent GitHub Actions run `33458517601`.

TASK-003 through TASK-005B implement the accepted provider, market-data, Dashboard, launcher, and
expanded-history baseline. TASK-006A implements provider-validated dynamic US/HK equities,
provider-neutral calendar/session input, completed W1 and regular-session M30 derivation, truthful
adjustment/coverage metadata, and summary diagnostics.

TASK-006A passed focused remediation and is integrated at
`7909f1c04f7049cf1ccec78a3d5023ae801b7177`. TASK-006B now implements the provider-neutral,
read-through structure subset on its task branch: Decimal ATR, independent Micro/Major Pivots,
Swing labels, Major-swing levels, Pivot Zones, Range and four-state Base Regime, plus a read-only
structure endpoint. Independent review and the real-structure human checkpoint remain pending.

No TASK-006C Event behavior, later setup/risk/advisory/Quality/Ranking behavior, paper behavior, or
backtest behavior is implemented by TASK-006B.
