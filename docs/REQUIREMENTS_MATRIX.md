# Requirements Traceability Matrix

## Current delivery status — 2026-09-09

C1/C2 are accepted and integrated at the current authoritative baseline
`722936984deac652b443eba132c69650653345e1`. ADC-001 is docs-only, **pending independent review**;
006B1 startup is on hold until the new post-review/integration handoff. Exact SHAs, sequence and
separate user/reviewer evidence attribution are in [ROADMAP](ROADMAP.md).
[ARCHITECTURE](ARCHITECTURE.md) is the current component/lifecycle entry point.

Status: Phase 1 accepted after independent post-remediation review — PASS; reviewed commit: `f6decf2fbe171c1b9eb46340a9174bc21f293ede`; reviewed tree: `f03d23ededaef37096b508a3040c87ae69d89e32`; GitHub Actions run: `33458517601`; job: `99703528272`; artifact: `9782355130`; result: `119 passed`

Future-scope authority: `docs/ROADMAP.md` decisions `MTF-001`, `PAQS-MVP-001`, and `PAQS-DUAL-001`

Decision records:

- `docs/decisions/PAQS_MVP_SCOPE_REDUCTION.md`
- `docs/decisions/PAQS_DUAL_BRANCH_ARCHITECTURE.md`

## 1. Disposition and status rules

| Disposition | Meaning |
|---|---|
| `RETAINED` | Requirement remains in the current Phase 0–4 architecture/current MVP |
| `SUPERSEDED_MTF` | Earlier future direction was replaced by `MTF-001` |
| `SUPERSEDED_PAQS_MVP` | Earlier future direction was replaced by `PAQS-MVP-001` |
| `SUPERSEDED_PAQS_DUAL` | Earlier single-engine PAQS future direction was replaced by `PAQS-DUAL-001` without rewriting accepted history |
| `OPTIONAL_FUTURE` | Valid extension capability but not current committed MVP work; explicit reactivation required |
| `REMOVED_MTF-001` | Permanently outside product scope; not deferred |
| `HISTORICAL_PHASE_1` | Accepted Phase 1 implementation/evidence retained without future authority |

| Status | Meaning |
|---|---|
| `IMPLEMENTED` | Accepted implementation evidence exists |
| `PENDING_REVIEW` | Task-branch implementation exists; independent review and integration remain outstanding |
| `REVIEWED_PASS` | Independent review passed for the exact cited implementation SHA; integration is verified separately |
| `APPROVED_TASK` | User authorized a bounded task; implementation follows its committed contract and prerequisites, not yet completed |
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
| GOV-008 | `TASK-006` remains umbrella-only for bounded PAQS-Q/shared-history work; `TASK-007` is umbrella-only for PAQS-E | RETAINED | 2 | DOCUMENTED | Roadmap 7; `PAQS-DUAL-001` |
| GOV-009 | Phase 3/4 remain dormant optional extension slots until explicitly reactivated | SUPERSEDED_PAQS_MVP | 3–4 | DORMANT_OPTIONAL | Roadmap 7–8 |
| GOV-010 | `PAQS-DUAL-001` supersedes the future single-engine TASK-006C/006D/006E assumption while preserving accepted historical evidence | SUPERSEDED_PAQS_DUAL | 2 | DOCUMENTED | Roadmap 1/7; dual-branch decision record |
| GOV-011 | Research doctrines/memos/amendments are not implementation authority; Task Contracts must explicitly adopt bounded semantics | RETAINED | all | DOCUMENTED | Roadmap 10; dual-branch decision record |

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

## 4. Market data, supported securities, Snapshot and Dashboard requirements

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
| MKT-009 | US minute retrieval uses `Session.ALL`; PAQS M30 structural evidence filters regular session | RETAINED | 2 | IMPLEMENTED | TASK-005B; TASK-006A M30 tests |
| MKT-010 | Unfinished minute bars are excluded from completed structural evidence | RETAINED | 2 | IMPLEMENTED | adapter/API/input tests |
| MKT-011 | Latest/intraday price is distinct from completed Daily close | RETAINED | 2 | IMPLEMENTED | TASK-004 state/API tests |
| MKT-012 | Missing/delayed/stale/unavailable/error states are explicit; no market value fabricated | RETAINED | all | IMPLEMENTED | provider result/API contracts plus AGENTS |
| MKT-013 | TASK-006A provides provider-neutral trading calendar/session/coverage/adjustment metadata | RETAINED | 2 | IMPLEMENTED | Calendar port, PAQS bundle/diagnostic tests |
| MKT-014 | Shared initial PAQS structural evidence roles are completed W1 / D1 / 30m regular session; H1/H4 are not MVP requirements | RETAINED | 2 | DOCUMENTED | Roadmap 5; TASK-006A |
| MKT-015 | Latest quote may be included in an analysis snapshot only as explicitly reference-only current-price context | RETAINED | 2 | IMPLEMENTED | TASK-006B2 final SHA `5f996aebb012cc0884d912f6f3eb71c32e9fd627`; `docs/reviews/TASK_006B2_INDEPENDENT_REVIEW.md` |
| MKT-016 | Reference-only quote must not confirm completed-bar structural or strategy facts | RETAINED | 2 | IMPLEMENTED | TASK-006B2 final SHA `5f996aebb012cc0884d912f6f3eb71c32e9fd627`; independent review |
| MKT-017 | Strict arbitrary historical As-Of replay requires later local observation/replay support and must not be falsely claimed from current QFQ read-through data | RETAINED | 2–4 | DOCUMENTED | Roadmap 5/7; TASK-006B1 direction |

| ID | Dashboard requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| UI-001 | Selector/latest/market status/Daily/1m/volume/timestamps | RETAINED | 2 | IMPLEMENTED | TASK-005/005B |
| UI-002 | Daily and 1-minute candles remain separate chart timeframes | RETAINED | 2 | IMPLEMENTED | TASK-005 |
| UI-003 | Visible-page ~60s market-data refresh, no overlapping requests, hidden pause/resume | RETAINED | 2 | IMPLEMENTED | TASK-005 |
| UI-004 | Manual refresh and countdown | RETAINED | 2 | IMPLEMENTED | TASK-005 |
| UI-005 | Dynamic supported US/HK add/remove flow is user-facing rather than backend-only | SUPERSEDED_PAQS_MVP | 2 | IMPLEMENTED | TASK-006A Dashboard form and integration tests |
| UI-006 | Current Dashboard presents exact Narrative text and frozen identity/evidence; structured levels/RR remain Legacy-only | RETAINED | 2 | IMPLEMENTED | `docs/PAQS_E_WORKBENCH.md`; `tests/browser/test_paqs_e_workbench.py`; `docs/evidence/TASK_007C/` |
| UI-007 | No real-order UI/control and no claim user executed advisory | RETAINED | all | DOCUMENTED | Roadmap safety boundary |
| UI-008 | Market-data page refresh does not automatically trigger PAQS-E or PAQS-Q strategy re-analysis | RETAINED | 2 | DOCUMENTED | `PAQS-DUAL-001`; Roadmap 4 |
| UI-009 | Future dual-branch comparison must show PAQS-E and PAQS-Q separately and surface disagreement without averaging into one synthetic decision score | RETAINED | 2 | PLANNED_TASK | TASK-007D scope direction |

## 5. PAQS shared architecture, PAQS-E, PAQS-Q and Score requirements

### 5.1 Historical and shared PAQS requirements

| ID | Requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| PAQS-001 | PAQS remains the causal decision-support family; no numerical score universally overrides branch hard discipline | SUPERSEDED_PAQS_DUAL | 2 | DOCUMENTED | Roadmap 6; `PAQS-DUAL-001` |
| PAQS-002 | Numerical Quality/Composite Score is derived/reference only and cannot fabricate or override structural decisions | RETAINED | 2 | DOCUMENTED | Roadmap 6 |
| PAQS-003 | `TASK-006` is umbrella only; no single umbrella implementation is allowed | RETAINED | 2 | DOCUMENTED | Roadmap 7/10 |
| PAQS-004 | TASK-006A — Dynamic US/HK Securities & PAQS Input Foundation | RETAINED | 2 | IMPLEMENTED | Dynamic add, calendar, W1/M30, diagnostics, guides |
| PAQS-005 | TASK-006B — historical deterministic PAQS Structure Engine implementation | RETAINED | 2 | IMPLEMENTED | Integrated at `96747041ef0ff8c00937c5dd5e80cb4c5c28c17c`; deterministic PASS; real-market semantic checkpoint `STRUCTURE_CONCERNS_FOUND` |
| PAQS-006 | Earlier TASK-006C single-engine Event Engine future wording | SUPERSEDED_PAQS_DUAL | 2 | DOCUMENTED | Replaced by TASK-006C-Q and PAQS-E doctrine/runtime workstreams |
| PAQS-007 | Earlier TASK-006D single-engine Setup & Risk future wording | SUPERSEDED_PAQS_DUAL | 2 | DOCUMENTED | Replaced by TASK-006D-Q and PAQS-E doctrine/runtime workstreams |
| PAQS-008 | Earlier TASK-006E single-engine Advisory & Decision Dashboard future wording | SUPERSEDED_PAQS_DUAL | 2 | DOCUMENTED | Replaced by TASK-006E-Q / TASK-007C / TASK-007D |
| PAQS-009 | TASK-006B real-market checkpoint is preserved as `STRUCTURE_CONCERNS_FOUND` research evidence and blocks pretending old deterministic semantics achieved final market acceptance | RETAINED | 2 | IMPLEMENTED | `docs/reviews/TASK_006B_REAL_MARKET_STRUCTURE_CHECKPOINT.md` evidence branch/history |
| PAQS-010 | Entry and Holder questions remain separate conditional decision-support concepts without brokerage position knowledge | RETAINED | 2 | DOCUMENTED | PAQS-E doctrine; Roadmap 6 |
| PAQS-011 | Exact score/quality/ranking formula remains unapproved | RETAINED | 2 | DECISION_REQUIRED | Roadmap 6 |
| PAQS-012 | No profitability/Alpha/probability claim from implementation tests, structural validation or uncalibrated LLM reasoning | RETAINED | 2–4 | DOCUMENTED | Roadmap/AGENTS/PAQS-E doctrine |
| PAQS-013 | PAQS-E and PAQS-Q are parallel strategy branches, not a simple version supersession chain | RETAINED | 2 | DOCUMENTED | `PAQS-DUAL-001`; Roadmap 2/6 |
| PAQS-014 | Strategy execution is explicit user-triggered Snapshot-on-Demand, not continuous/background strategy analysis | RETAINED | 2 | DOCUMENTED | `PAQS-DUAL-001`; Roadmap 4/7 |
| PAQS-015 | TASK-006B2 defines one shared immutable current Snapshot-on-Demand Market Snapshot with canonical serialization and `snapshot_hash` | RETAINED | 2 | IMPLEMENTED | Final accepted SHA `5f996aebb012cc0884d912f6f3eb71c32e9fd627`; `docs/reviews/TASK_006B2_INDEPENDENT_REVIEW.md` |
| PAQS-016 | Latest quote is reference-only, preserves nullable provider delay, and cannot confirm completed-bar structural evidence | RETAINED | 2 | IMPLEMENTED | TASK-006B2 final independent review at `5f996a...` |
| PAQS-019 | Shared W1/D1/M30 evidence exposes machine-readable source status, authoritative counts, W1 exclusions and M30 missing elapsed-bucket provenance | RETAINED | 2 | IMPLEMENTED | TASK-006B2 Amendment 01; final independent review at `5f996a...` |
| PAQS-017 | PAQS branches remain runtime-independent; one provider/branch may fail without disabling the other or ordinary market-data viewing | RETAINED | 2 | DOCUMENTED | Dual-branch architecture decision/review |
| PAQS-018 | TASK-006B1 Local Market Data Store & Replay Foundation original contract scope retained; startup on hold until ADC review/integration and new handoff | RETAINED | 2 | PLANNED_TASK | Roadmap 7; 2026-09-09 sequencing decision |

### 5.2 PAQS-E requirements

| ID | Requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| PAQSE-001 | `PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md` is the registered primary PAQS-E runtime semantic authority adopted by TASK-007A; `PAQS_E_NAKED_PRICE_ACTION_DOCTRINE.md` remains the conceptual foundation | RETAINED | 2 | IMPLEMENTED | TASK-007A accepted exact strategy hash; Roadmap 6 |
| PAQSE-002 | PAQS v0.3.x is historical formalization/guardrail/audit/terminology reference, not a requirement to recreate its full deterministic state machine inside PAQS-E | RETAINED | 2 | DOCUMENTED | Roadmap 6; Master Spec/Doctrine |
| PAQSE-003 | Provider-neutral Narrative/Legacy ports; one registered model per request, OpenAI was the first historical adapter | RETAINED | 2 | IMPLEMENTED | TASK-007A integrated at `ca9712649b7ec26a67047e251200a50b353ad5b4` |
| PAQSE-004 | Legacy historical: First PAQS-E MVP model call receives only product-controlled snapshot/runtime/prompt/schema inputs and no web/browser/search tools | RETAINED | 2 | IMPLEMENTED | TASK-007A integrated at `ca9712649b7ec26a67047e251200a50b353ad5b4` |
| PAQSE-005 | Ordinary PAQS-E Analyze calls are stateless/fresh by default; prior decisions/conversation are not hidden prompt context | RETAINED | 2 | IMPLEMENTED | TASK-007A integrated runtime; TASK-007B independent review PASS at `7785cdeeacb14f0762f6104ed99f01b5e76d1dd3` |
| PAQSE-006 | Legacy historical: PAQS-E output is schema-constrained structured output plus concise user explanation | RETAINED | 2 | IMPLEMENTED | Master Spec; TASK-007A integrated at `ca9712649b7ec26a67047e251200a50b353ad5b4` |
| PAQSE-007 | Legacy historical: Deterministic post-validation checks schema/factual/arithmetic/RR discipline without replacing LLM strategy reasoning | RETAINED | 2 | IMPLEMENTED | TASK-007A integrated at `ca9712649b7ec26a67047e251200a50b353ad5b4` |
| PAQSE-008 | Legacy historical: PAQS-E decisions are immutable revisions storing snapshot/doctrine/prompt/provider/model metadata and structured result | RETAINED | 2 | REVIEWED_PASS | TASK-007B core ledger, SQLAlchemy adapter, migration 0002 and evidence/revision tests; `docs/reviews/TASK_007B_INDEPENDENT_REVIEW.md` at `7785cdeeacb14f0762f6104ed99f01b5e76d1dd3` |
| PAQSE-009 | PAQS-E Entry Advisory and Holder Advisory remain separate questions | RETAINED | 2 | DOCUMENTED | Master Spec / Doctrine |
| PAQSE-010 | `NO_TRADE`, `WATCH_LONG`, `WAIT_RETEST`, `ENTRY_PENDING_REVALIDATION`, `UNCERTAIN` and poor-entry states are valid first-class outputs | RETAINED | 2 | DOCUMENTED | Master Spec |
| PAQSE-011 | `TASK-007` is umbrella only; planned bounded tasks are TASK-007A/B/C and later TASK-007D | RETAINED | 2 | PLANNED_TASK | Roadmap 7 |
| PAQSE-012 | TASK-007C completion is the current usability milestone for the current Snapshot-on-Demand PAQS-E MVP; historical Gold-Set replay may follow later | RETAINED | 2 | DOCUMENTED | Roadmap 7 |
| PAQSE-013 | Local password submission to registered Windows service slots; safe status-only reads, OpenAI read-only environment fallback, no database/log/browser persistence | RETAINED | 2 | IMPLEMENTED | TASK-007A integrated runtime; TASK-007B ledger/API secrecy independent review PASS; Roadmap 7/10 |
| PAQSE-014 | First PAQS-E implementation does not require multi-model voting/ensemble behavior | RETAINED | 2 | DOCUMENTED | `PAQS-DUAL-001`; Roadmap 6 |
| PAQSE-015 | Legacy historical: Original 007B Analyze accepted Security UUID/model ID/strategy and empty auxiliary context; current four-field Narrative is traced below | RETAINED | 2 | REVIEWED_PASS | TASK-007B application orchestration and API tests; API Contracts 5.10; `docs/reviews/TASK_007B_INDEPENDENT_REVIEW.md` at `7785cdeeacb14f0762f6104ed99f01b5e76d1dd3` |
| PAQSE-016 | Exact canonical request/result UTF-8 text and immutable strategy/prompt content are hashed, persisted and verified on readback | RETAINED | 2 | REVIEWED_PASS | TASK-007B ledger evidence/artifact tests; engineering guide; `docs/reviews/TASK_007B_INDEPENDENT_REVIEW.md` at `7785cdeeacb14f0762f6104ed99f01b5e76d1dd3` |
| PAQSE-017 | Legacy historical: Provider/configuration and validation failures commit typed terminal runs without Decisions; success commits artifacts/run/Decision atomically before returning | RETAINED | 2 | REVIEWED_PASS | TASK-007B failure/rollback/API tests; `docs/reviews/TASK_007B_INDEPENDENT_REVIEW.md` at `7785cdeeacb14f0762f6104ed99f01b5e76d1dd3` |
| PAQSE-018 | Successful revisions append within `(security_id, strategy_id)` across model/content changes and repeated snapshots, preserving immutable prior evidence | RETAINED | 2 | REVIEWED_PASS | TASK-007B revision/uniqueness/immutability tests; `docs/reviews/TASK_007B_INDEPENDENT_REVIEW.md` at `7785cdeeacb14f0762f6104ed99f01b5e76d1dd3` |
| PAQSE-019 | Legacy historical: Original 007B bounded Run/Decision reads supported subsequent 007C; GETs retained without hidden memory or market archive | RETAINED | 2 | REVIEWED_PASS | TASK-007B read/API/architecture tests; API Contracts 5.10; `docs/reviews/TASK_007B_INDEPENDENT_REVIEW.md` at `7785cdeeacb14f0762f6104ed99f01b5e76d1dd3` |

### 5.3 PAQS-Q requirements

| ID | Requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| PAQSQ-001 | PAQS-Q is the deterministic machine/reference/scanner branch | RETAINED | 2 | DOCUMENTED | `PAQS-DUAL-001`; Roadmap 6 |
| PAQSQ-002 | PAQS-Q mechanical thresholds and future methods do not silently bind PAQS-E semantic reasoning | RETAINED | 2 | DOCUMENTED | Roadmap 6; PAQS-E Master Spec/Doctrine |
| PAQSQ-003 | PAQS-Q methods may evolve under separate research/Task Contract governance | RETAINED | 2 | DOCUMENTED | Roadmap 6/7 |
| PAQSQ-004 | TASK-006B-Q — PAQS-Q Structure Stabilization | RETAINED | 2 | PLANNED_TASK | Roadmap 7 |
| PAQSQ-005 | TASK-006C-Q — PAQS-Q Event Engine | RETAINED | 2 | PLANNED_TASK | Roadmap 7 |
| PAQSQ-006 | TASK-006D-Q — PAQS-Q Setup, Risk & Setup-Specific Quant Confirmation | RETAINED | 2 | PLANNED_TASK | Roadmap 7 |
| PAQSQ-007 | TASK-006E-Q — PAQS-Q Advisory / Scanner Presentation | RETAINED | 2 | PLANNED_TASK | Roadmap 7 |
| PAQSQ-008 | PAQS-Q stabilization is not a prerequisite that blocks an otherwise safe PAQS-E current-analysis MVP | RETAINED | 2 | DOCUMENTED | Roadmap 7; `PAQS-DUAL-001` |

Earlier score-level governance remains recorded for compatibility:

```text
Composite Quant Score = Daily Base Score + Intraday Minute Adjustment
```

but it is a derived/reference concept if retained, not a universal causal strategy engine and not a mechanism for averaging PAQS-E with PAQS-Q.

## 6. Optional future extensions

| ID | Requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| PAP-001 | Simulated Paper Portfolio / PaperFill bookkeeping | OPTIONAL_FUTURE | 3 | DORMANT_OPTIONAL | Roadmap 7–8 |
| PAP-002 | Paper NAV/performance/accounting | OPTIONAL_FUTURE | 3 | DORMANT_OPTIONAL | Roadmap 7–8 |
| PAP-003 | Position sizing / exposure / correlation controls | OPTIONAL_FUTURE | 3 | DORMANT_OPTIONAL | Roadmap 7–8 |
| RES-001 | Broader factor/research expansion | OPTIONAL_FUTURE | 3 | DORMANT_OPTIONAL | Roadmap 7–8 |
| RES-002 | Multi-model comparison/voting beyond current single-selection registered gateway | OPTIONAL_FUTURE | 3–4 | DORMANT_OPTIONAL | Roadmap 8 |
| BT-001 | Deterministic point-in-time backtesting platform | OPTIONAL_FUTURE | 4 | DORMANT_OPTIONAL | Roadmap 7–8 |
| BT-002 | Transaction costs / benchmark comparison | OPTIONAL_FUTURE | 4 | DORMANT_OPTIONAL | Roadmap 7–8 |
| BT-003 | Drawdown/volatility/turnover/attribution/exposure analytics | OPTIONAL_FUTURE | 4 | DORMANT_OPTIONAL | Roadmap 7–8 |
| BT-004 | Portfolio optimization / broad parameter-analysis/reporting suite | OPTIONAL_FUTURE | 4 | DORMANT_OPTIONAL | Roadmap 7–8 |
| BT-005 | Phase 4 remains final possible phase; no Phase 5 | RETAINED | 4 | DOCUMENTED | Roadmap 7 |

These optional capabilities are not required for the current Snapshot-on-Demand PAQS-E usability milestone. They may be reactivated later without changing the permanent read-only/no-broker boundary.

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

## 8. Accepted historical implementation checkpoints

Phase 1 remains accepted with `119 passed` in independent GitHub Actions run `33458517601`.

TASK-003 through TASK-005B implement the accepted provider, market-data, Dashboard, launcher, and expanded-history baseline. TASK-006A implements provider-validated dynamic US/HK equities, provider-neutral calendar/session input, completed W1 and regular-session M30 derivation, truthful adjustment/coverage metadata, and summary diagnostics.

TASK-006A passed focused remediation and is integrated at `7909f1c04f7049cf1ccec78a3d5023ae801b7177`.

TASK-006B passed deterministic implementation review/remediation and was integrated at `96747041ef0ff8c00937c5dd5e80cb4c5c28c17c`. Its subsequent real-market structure checkpoint returned `STRUCTURE_CONCERNS_FOUND`, including history-origin/path-lock and structure-stability concerns. This evidence motivates the separate PAQS-Q stabilization branch and does not invalidate the accepted deterministic implementation review.

TASK-006B2 passed final independent post-remediation review and is accepted/integrated at `5f996aebb012cc0884d912f6f3eb71c32e9fd627`. It provides the immutable provider-neutral current Snapshot-on-Demand factual contract, including bounded W1/D1/M30 evidence, quote/market-state reference-only facts, machine-readable coverage/provenance, canonical SHA-256 identity and corrected W1 As-Of semantics. Evidence is preserved in `docs/reviews/TASK_006B2_INDEPENDENT_REVIEW.md`.

TASK-007A is accepted/integrated at `ca9712649b7ec26a67047e251200a50b353ad5b4`. It adds the
internal snapshot-bound PAQS-E request/result contracts,
registered Master Spec/runtime prompt packages, provider-neutral reasoning port, deterministic
validator, and stateless OpenAI Responses adapter.

TASK-007B implements an explicit current Analyze API, immutable runtime artifacts and terminal
Analysis Runs, validated Decision revisions and bounded read APIs on its dedicated task branch.
Its migration 0002 follows the untouched Phase 1 foundation. Exact canonical evidence hashes,
append-only records, atomic success/failure persistence, model-independent strategy revision
series, and safe readback are covered by focused orchestration, evidence, API, migration and
architecture tests. Status is **REVIEWED_PASS** at `7785cdeeacb14f0762f6104ed99f01b5e76d1dd3`;
evidence: `docs/reviews/TASK_007B_INDEPENDENT_REVIEW.md`. The reviewed implementation is integrated in the current authoritative baseline.

No TASK-007C Dashboard Analyze UI, PAQS-Q successor task, market-data persistence/replay, hidden
Decision memory, background analysis, broker behavior, paper behavior, or backtest behavior is
implemented by TASK-007B. Accepted Phase 1 evidence remains unchanged.

## 9. R20 product adoption and immediate workbench task

| ID | Requirement | Disposition | Phase | Status | Evidence |
|---|---|---|---:|---|---|
| R20-001 | Adopt useful R20 workbench/product interactions while preserving PAQS-E and the no-live boundary | RETAINED | 2–4 | DOCUMENTED | `docs/decisions/R20_PRODUCT_ADOPTION_2026_09_07.md`; historical planning: `docs/research/R20_ADOPTION_PLAN_AND_CODEX_PROMPT_ZH.md` |
| R20-002 | 007C retains current JS/CSS and vendored Lightweight Charts; copied substantive code retains origin/license notice | RETAINED | 2 | IMPLEMENTED | `docs/THIRD_PARTY_WORKBENCH.md`; existing vendor hash regression |
| R20-003 | Explicit Analyze, model/registered-strategy selection, truthful failure and immutable Decision history become usable UI flows | RETAINED | 2 | IMPLEMENTED | `tests/browser/test_paqs_e_workbench.py`; `tests/integration/test_paqs_e_configuration.py`; `docs/PAQS_E_WORKBENCH.md` |
| R20-004 | Later prompt/model/version, critique/council, reviewable evolution, news, simulated bookkeeping and operations capabilities follow the adoption record through separate bounded contracts | OPTIONAL_FUTURE | 2–4 | DOCUMENTED | `docs/decisions/R20_PRODUCT_ADOPTION_2026_09_07.md`; no expansion of 007C |
| R20-005 | Do not inherit R20 live execution, unrestricted Python plugins, plaintext secret storage, automatic strategy changes or crypto-specific financial assumptions | RETAINED | all | DOCUMENTED | `docs/decisions/R20_PRODUCT_ADOPTION_2026_09_07.md`; permanent Roadmap boundaries |


## 10. Current Narrative workbench traceability

These rows consolidate the current implementation. Legacy requirement IDs above retain historical
meaning; their original contracts and R01–R06 reports remain untouched and are indexed in
[architecture history](ARCHITECTURE.md#9-historical-evolution-and-evidence). Existing test sources
below are inspected evidence, not ADC execution results. C1 and C2 acceptance are recorded in
[R06 review](reviews/TASK_007C1_REMEDIATION_06_INDEPENDENT_REVIEW.md),
[C1 closeout](decisions/TASK_007C1_CLOSEOUT_2026_09_08.md),
[C2 review](reviews/TASK_007C2_INDEPENDENT_REVIEW.md) and
[C2 closeout](decisions/TASK_007C2_CLOSEOUT_AND_006B1_HANDOFF_2026_09_08.md).

| ID | Current requirement / status | Implementation and existing test evidence |
|---|---|---|
| 007C1-001 | IMPLEMENTED: eleven-model flat catalog, default DeepSeek V4 Flash, fixed routes, one selection | [ModelRegistry](../src/ai_infra_quant/application/paqs_e_models.py); [catalog tests](../tests/unit/test_paqs_e_model_gateway.py) |
| 007C1-002 | IMPLEMENTED: shared secure slots, password submission, safe reads, OpenAI fallback, loopback/Origin boundary | [WindowsCredentialStore](../src/ai_infra_quant/integrations/windows_credentials.py); [credential API tests](../tests/integration/test_paqs_e_multi_model.py) |
| 007C1-003 | IMPLEMENTED: four-field explicit Analyze, current Snapshot and actual model identity | [NarrativeAnalysisService](../src/ai_infra_quant/application/paqs_e_narrative.py); [Narrative API tests](../tests/integration/test_paqs_e_narrative_ledger_api.py) |
| 007C1-004 | IMPLEMENTED: provider-specific optional research, frozen context, truthful cutoff limits | [ModelGateway.research](../src/ai_infra_quant/integrations/openai_reasoning/gateway.py); [native research tests](../tests/unit/test_paqs_e_native_research.py) |
| 007C1-005 | IMPLEMENTED: no retries/fallback or extra search; final tool-free text | [NarrativeGateway](../src/ai_infra_quant/integrations/openai_reasoning/narrative.py); [all-model text tests](../tests/unit/test_paqs_e_narrative_provider.py) |
| 007C1-006 | USER_ACCEPTED: C1 functionally closed | C1 closeout above; not independent verification of user-local hashes or all-model paid acceptance |
| NAR-001 | IMPLEMENTED: no new structured semantic gate; exact prose/hash, independent revisions; only additive 0003 | [Narrative repository](../src/ai_infra_quant/database/repositories/paqs_e_narrative.py); [ledger/API tests](../tests/integration/test_paqs_e_narrative_ledger_api.py) |
| RES-DS-001 | IMPLEMENTED: one SEARCH, direct memo or one tool-free stateless SYNTHESIS; accepted calls as-is | [research_native](../src/ai_infra_quant/integrations/openai_reasoning/deepseek_research_flow.py); [continuation tests](../tests/unit/test_paqs_e_research_continuation.py) |
| RES-DS-002 | IMPLEMENTED: multiplicity safety distinct from bounded ordered capture | [parse_native_search](../src/ai_infra_quant/integrations/openai_reasoning/deepseek_research.py); [multiplicity tests](../tests/unit/test_paqs_e_search_multiplicity.py) |
| RES-DS-003 | IMPLEMENTED: partial statuses coexist; completed-search quorum; completed evidence only | [parser](../src/ai_infra_quant/integrations/openai_reasoning/deepseek_research.py); [16/7/24 fixture tests](../tests/unit/test_paqs_e_partial_actions.py); [lifecycle API](../tests/integration/test_paqs_e_partial_actions_api.py) |
| RES-DIAG-001 | IMPLEMENTED: parser-origin boundary codes, safe bounded counts, no raw/secret/trace persistence | [diagnostic parser](../src/ai_infra_quant/integrations/openai_reasoning/deepseek_research_diagnostics.py); [browser tests](../tests/browser/test_paqs_e_partial_actions.py) |
| UI-NAR-001 | IMPLEMENTED: DOM-only formatted/raw views, research OFF/reset, no automatic Analyze | [paqs-e.js](../src/ai_infra_quant/frontend/static/paqs-e.js); [Markdown/opt-in tests](../tests/browser/test_paqs_e_safe_markdown.py) |
| UI-WAIT-001 | IMPLEMENTED: long-wait guard and unknown outcome, source-SHA handshake | [long-running tests](../tests/browser/test_paqs_e_long_running.py); [runtime revision tests](../tests/integration/test_runtime_source_revision.py) |
| LEG-001 | RETAINED: immutable structured history/validator; default POST 410, internal fixture switch | [paqs_e routes](../src/ai_infra_quant/backend/api/v1/paqs_e.py); [Narrative/Legacy tests](../tests/integration/test_paqs_e_narrative_ledger_api.py) |
| C2-001 | IMPLEMENTED / REVIEWED / INTEGRATED: credential layout, old UI/read cleanup, active watchlist preserved | [template](../src/ai_infra_quant/frontend/templates/index.html); [C2 browser tests](../tests/browser/test_paqs_e_ui_cleanup.py); C2 review/closeout above |
| ADC-001 | PENDING INDEPENDENT REVIEW: docs-only architecture/status/traceability consolidation | [Contract](../prompts/tasks/TASK-ADC-001_ARCHITECTURE_DOCUMENTATION_CONSOLIDATION.md); [report](reports/TASK_ADC_001_IMPLEMENTATION_REPORT.md) |

006B1 archive/replay/0004 is not implemented here. PAQS-Q successors, strict historical As-Of/GoldSet,
007D comparison and Paper/PnL/Phase 3/4 remain deferred. Real-account/trading behavior is forbidden.
