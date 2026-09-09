# Database Schema

This is the implemented schema at `722936984deac652b443eba132c69650653345e1`.
Runtime is SQLite with SQLAlchemy repositories and explicit Alembic migrations. PostgreSQL
compatibility is a portability/test concern, not a current deployment requirement.
For request orchestration and provenance, see [ARCHITECTURE](ARCHITECTURE.md).

## 1. Migration chain and startup

| Revision | Implemented tables / role |
|---|---|
| `0001_phase1_foundation` | Canonical identity/watchlist, strategy configuration, historical paper descriptors/opening accounting and settings |
| `0002_task007b_paqs_e_ledger` | Immutable runtime artifacts and Legacy structured Analysis Runs/Decisions |
| `0003_task007c1_narrative_ledger` | Additive Narrative Runs and exact-text Results; current head |

Source: [0001](../src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py),
[0002](../src/ai_infra_quant/database/migrations/versions/0002_task007b_paqs_e_decision_ledger.py),
[0003](../src/ai_infra_quant/database/migrations/versions/0003_task007c1_narrative_ledger.py).
The 0002 filename differs from its revision identifier. Normal startup checks the required head
and performs the accepted idempotent foundation bootstrap; it does not create schema from current
ORM metadata or delete databases. All three migration files remain unchanged by ADC.

No 0004 exists. TASK-006B1 archive/replay is on hold pending the ADC review/integration and a new
exact-baseline handoff. Planned archive tables must not be described as current persistence.

## 2. Foundation tables retained from 0001

| Group | Actual table names | Current role |
|---|---|---|
| Identity | `securities`, `provider_symbol_mappings` | Canonical Security and provider-symbol identity, supported-security metadata |
| Watchlist | `watchlists`, `watchlist_items` | Active user-managed membership; removal does not erase Security/analysis history |
| Strategy configuration | `strategy_definitions`, `strategy_assignments` | Foundation configuration; not a UI editor for the registered PAQS-E master/prompt |
| Historical descriptors | `broker_profiles`, `broker_accounts`, `portfolios`, `portfolio_accounts` | Inert/local foundation; names do not authorize real-account connection |
| Opening accounting | `ledger_accounts`, `ledger_transactions`, `ledger_entries`, `cash_flows`, `unit_transactions`, `cash_balances`, `portfolio_snapshots` | Accepted opening facts/projections; no current PaperFill or PnL engine |
| Settings | `settings` | Application settings records; not a secret store |

The accepted seed's HKD 20,000, 200 units and NAV 100 are historical opening facts, not live assets.
C2 retired their cards, duplicate admin UI and dedicated frontend reads. It did not remove these
tables, compatibility APIs or user data. SQL declarations remain in
[database/models](../src/ai_infra_quant/database/models); historical foundation evidence remains
in the unchanged [Phase 1 plan](phases/PHASE_1_PLAN.md).

## 3. Immutable shared artifacts and Legacy evidence

[paqs_e_ledger.py models](../src/ai_infra_quant/database/models/paqs_e_ledger.py) define:

| Table | Evidence |
|---|---|
| `paqs_e_runtime_artifacts` | Artifact kind/key, exact strategy/prompt content and SHA-256; reused by both ledgers |
| `paqs_e_analysis_runs` | Legacy canonical request/hash, Snapshot/runtime/model/strategy identity, terminal provider/validator outcome |
| `paqs_e_decisions` | Legacy structured result/hash, summaries, revision and predecessor identity |

Legacy success has one validated Decision. Provider or semantic validation failure has no Decision.
Historical `VALIDATION_FAILED` and `INVALID_STRUCTURED_OUTPUT` belong to this retained path, not
new final Narrative outcomes. Original structured GETs and validator remain intact; old POST is
normally 410 and hidden from OpenAPI. No conversion backfills Narrative from Legacy or manufactures
structured fields from new prose. Legacy and Narrative revision series are separate.

## 4. Current Narrative Ledger

[paqs_e_narrative.py tables](../src/ai_infra_quant/database/models/paqs_e_narrative.py),
[domain identities](../src/ai_infra_quant/core/domain/paqs_e_narrative.py) and
[SQLAlchemyNarrativeLedger](../src/ai_infra_quant/database/repositories/paqs_e_narrative.py)
are the schema, value and repository authorities.

| Table | Fields and relations |
|---|---|
| `paqs_e_narrative_runs` | `narrative_run_id`; Security FK and frozen symbol/market/type; Snapshot hash/As-Of; analysis/request/output/runtime versions; provider/model; strategy/prompt IDs, hashes and artifact FKs; research boolean; canonical `request_payload_json` and hash; status, safe response ID, typed failure; started/completed/created UTC |
| `paqs_e_narrative_results` | `narrative_result_id`; unique Run FK; matching frozen identity; `revision_no`, predecessor Result FK; exact `response_text`, SHA-256, created UTC |

The request JSON contains the full Snapshot, runtime configuration and accepted auxiliary research.
No credential, raw provider envelope, reasoning transcript or transient native pass-back item is
stored. Research failure diagnostics remain ephemeral API metadata.

`record` begins its write transaction only after provider completion. SQLite `BEGIN IMMEDIATE`
serializes revision allocation; the repository's alternative dialect path locks the Security row.
The transaction reuses immutable artifacts and writes either one successful Run plus one Result,
or a `PROVIDER_FAILED` Run without Result. Failures roll back; no success is returned before commit.
Research and final-provider network calls do not hold a long database write transaction.
Run `started_at`/`completed_at` surround final reasoning; research occurred before `started_at`.

Narrative revision uniqueness is `(security_id, strategy_id, revision_no)`. Revision 1 has no
predecessor; subsequent successes supersede the immediately preceding Result in that series,
including across model or strategy-content-hash changes. Repeated Snapshot requests are not
deduplicated. Failed Runs consume no successful revision.

0003 provides terminal-status/evidence, text-length/hash, positive-revision, predecessor, FK and
uniqueness constraints. SQLite triggers reject Run/Result UPDATE/DELETE and enforce matching
successful parent and lineage at insertion. Repository reads additionally verify canonical request
hash/identity, strategy/prompt artifact hashes, Result text hash, parent identity and predecessor.
These application checks should not be represented as SQL-only semantic certification.

## 5. Exact values, time and storage limits

Financial values use Python `Decimal`. [ExactDecimal](../src/ai_infra_quant/database/types.py)
binds fixed-scale canonical TEXT on SQLite and NUMERIC(38,18) on PostgreSQL. Floats and invalid
scale/range are rejected. Exact arithmetic/balance checks run in Python Decimal; SQLite TEXT
sorting, SUM or numeric CAST are not exact financial operations. Instants are aware UTC;
market-local session dates/timezones retain their independent meaning.

Narrative text is preserved without normalization; UTF-8 text/hash and identity checks prove stored
content, not machine-certified strategy reasoning, profitability, targets or RR. Known future web
publication sources are filtered; missing publication times and provider-native memo statements
retain explicit cutoff limitations. `as_of_compatible` does not prove independent historical safety.

Frozen W1/D1/M30/quote evidence inside a request is not a generic local market archive. Current
QFQ provider reads do not establish strict arbitrary historical As-Of replay, GoldSet or backtesting.
No market archive, PaperOrder/PaperFill, live position/order or new performance table is introduced.

## 6. Verification references

Existing [Narrative ledger/API tests](../tests/integration/test_paqs_e_narrative_ledger_api.py)
cover additive upgrade/Legacy-byte preservation, exact text, revisions, immutability, rollback,
readback corruption and default Legacy POST behavior. Existing
[partial-action API tests](../tests/integration/test_paqs_e_partial_actions_api.py) cover frozen
research before reasoning and no ledger mutation on failed research. These are implementation
source references; ADC performs docs-only audits, not a new database migration/test run.
