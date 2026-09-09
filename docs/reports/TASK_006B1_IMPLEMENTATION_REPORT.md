# TASK-006B1 — Implementation Report

Status: **IMPLEMENTED / PENDING INDEPENDENT REVIEW**. Not merged; no subsequent task started.

## 1. Reviewed starting objects and delivery identity

Repository: `ahhhhzzz/ai-infra-quant`.
Only delivery branch: `task/006b1-local-market-data-store-replay`.

| Object | Exact SHA / result |
|---|---|
| Authoritative `roadmap/no-live-trading` | `02326a3bb19c2a89352d765f5331670b5f3f466d` |
| Starting task HEAD / post-ADC handoff commit | `bed9059fd6ce6c0a7cd750376c972070db0a39dd` |
| Handoff parent / prepared merge | `3b1685ac3f5e491114bba5945786d56b291fb422` |
| Prepared merge first parent / retained hold | `9767554a4bca8c4ea29a8af93ec7f4f3e0f08748` |
| Prepared merge second parent | `02326a3bb19c2a89352d765f5331670b5f3f466d` |
| Original contract publication | `d2bc397612a32adb2b5f78fec3ec894b3eacdb38` |
| Task / authority merge base | `02326a3bb19c2a89352d765f5331670b5f3f466d` |
| Normal prepared-merge tree | `51b9517b2f365710a9169aaf47cbc564aa13e683` |

Fetched GitHub references before work and rechecked them before delivery. Starting task HEAD and
authority matched the supplied objects; no intervening task commit was overwritten. The prepared
merge tree matches `git merge-tree --write-tree` for its ordered parents. The starting commit adds
only the handoff; original contract/hold records are unchanged, and authority-to-start differences
are task documents only. Accepted C2 runtime and ADC closure were retained.

Read AGENTS, current authority docs, the complete
[handoff](../../prompts/tasks/TASK-006B1_POST_ADC_HANDOFF_2026_09_09.md) and
[original contract](../../prompts/tasks/TASK-006B1_LOCAL_MARKET_DATA_STORE_REPLAY_FOUNDATION.md).
The updated handoff replaces the old baseline/hold only; the original functional scope and gates
remain binding. Work used a new clean independent worktree on the authorized task branch.

The exact final delivery SHA is the commit containing this report, returned explicitly in the
handoff response and verified by GitHub readback. It cannot be embedded as its own Git hash.
No report-only successor or external uncommitted runtime file is required to reproduce the change.

## 2. Implementation and persisted data design

- Explicit POST resolves an existing enabled verified canonical equity Security and approved
  US/HK market/currency/IANA timezone. No new Security is invented by capture.
- One request-scoped existing quote provider performs one D1 capability (1500 maximum), one M1
  capability (recent 30 market-local calendar days, 50,000 maximum) and one bounded calendar
  capability covering returned dates/minute window (3001 inclusive days/records maximum).
  No retry/fallback, background capture, quote request, model or research is added by the service.
  Capability counts are saved. Existing SDK history pagination and daily-completion checks remain
  inside the unchanged provider adapter; capability count is not a provider-HTTP billing count.
- Every batch validates identity/provider, shape, completion, dates/one-minute UTC interval,
  observation bounds, exact 38,18 Decimal and OHLCV invariants before it can contribute members.
  Conflicting duplicate identity rejects the entire batch with a safe owned code. Identical repeats
  deduplicate deterministically, retaining earliest member retrieval and explicit raw/duplicate counts.
- Calendar freezes market/date/IANA timezone, normalized and raw day type, regular-session segments,
  provider and retrieval; invalid calendar never creates fabricated completed days. US DST/cross-UTC
  dates and HK lunch/half-day segments retain local meaning.
- Three new tables: `market_archive_captures`, `market_archive_bar_versions`,
  `market_archive_memberships`. Calendar and batch quality/provenance are frozen in hashed capture
  JSON. Membership selects exactly ordered versions for each capture/timeframe, with its own
  retrieval time. There is no mutable latest pointer, first/last-seen reconstruction or auto-stitching.
- Canonical schema `market-archive-v1`: sorted compact UTF-8 JSON, stable SHA-256, canonical exact
  Decimal strings and UTC microsecond strings. Identity includes Security/provider/timeframe,
  market/currency/timezone, current QFQ basis/unknown adjustment epoch and D1 session or M1 UTC
  start/end. Version adds OHLCV/completion and original time interpretation. Retrieval is observation
  metadata, excluded from version hash, so repeated content reuses versions without losing new times.
- Existing `ExactDecimal` yields fixed-scale SQLite TEXT without numeric affinity and PostgreSQL
  NUMERIC(38,18). UTC instants remain distinct from market-local dates. No binary float is used for
  financial values in runtime.
- All network work completes before one short transaction. SQLite BEGIN IMMEDIATE or PostgreSQL
  per-Security row locking plus unique constraints prevent concurrent duplicate versions. Versions,
  capture and all memberships commit atomically. Injected membership failure rolls back everything.
- All three tables reject update/delete. Composite FKs prevent cross-Security/timeframe memberships.
  Ordinal bounds against the capture's frozen count plus populated PK/unique keys prevent later
  additions to a committed capture. Reads verify hashes/exact values and detail membership counts.

Successful observations are conservatively **PARTIAL**: provider AVAILABLE does not certify
historical completeness. The provider status is retained independently; actual bounds/counts and
known regular-session missing counts are explicit. Missing-count zero only refers to returned known
calendar sessions, not every possible trading date or extended session. Unknown calendar means
missing-count null. ERROR/UNAVAILABLE batches have no fabricated members. No valid bar batch yields
503/no capture; valid other batches may still be saved as partial. Database failure has a distinct
safe 503 and rollback. Raw SDK exception text and private paths are not exposed or persisted.

`started_at`/`completed_at` surround collection/validation; `recorded_at` is assigned just before
persistence, not a fictional provider time. The request envelope starts at server time; individual
batch retrieval/window end and member retrieval remain separate. Current-provider QFQ and unknown
corporate-action epoch are not strict historical As-Of. Separate D1/M1/calendar reads are not an
atomic provider Snapshot. No W1/M30 archive authority, backtest return or historical Analyze exists.

## 3. API and UI

| Endpoint | Behavior |
|---|---|
| POST `/api/v1/market-data/archive/captures` | Only `security_id`; explicit fixed-range capture; 201 after persistence, PARTIAL disclosure |
| GET `/api/v1/market-data/archive/securities/{security_id}/captures` | Local descending time/UUID keyset list, default 20 / max 50 |
| GET `/api/v1/market-data/archive/captures/{capture_id}` | Local immutable metadata, calendar and quality |
| GET `/api/v1/market-data/archive/captures/{capture_id}/bars` | D1/M1 only, ascending membership ordinal; default 500 / max 1000 |

GETs return `next_cursor` or null where paginated. Bounded canonical cursor scopes prevent reuse
across Security/capture/timeframe; invalid UUID/limits/cursors/unknown objects return explicit 4xx.
POST requires loopback host/peer and same-origin JSON, no query or extra fields, ≤1024-byte body.
No provider factory, Snapshot or model service is invoked by saved-capture reads.

The default-folded **本地行情存档** section owns one explicit **保存当前行情** button, guarded during
an in-flight request. Local list/detail, a known Capture ID field and D1/M1 exact table work offline.
500+101 row pagination is verified with synthetic data. Security selection/removal invalidates late
responses; no prior Security result attaches to a new selection. Keyboard controls, horizontal
table scrolling and both themes remain usable at 390/900/1440 px. Safe DOM text rendering preserves
exact values. The visible limitation reads “本地存档；当前观察到的复权数据；不等于严格历史时点回测”.

The existing `security-selected` event was sufficient: `app.js` was not changed. Current refresh,
charts, Analyze, secure credentials, Narrative Markdown/raw history and research default OFF remain
on their existing paths. A data URI favicon avoids an inherited missing-favicon request during
clean-browser console validation; no remote icon/renderer/dependency was introduced.

## 4. Validation evidence

Environment: Windows, CPython **3.12.14**, pytest **8.4.1**, Playwright **1.55.0**,
Chromium **140.0.7339.16** (build 1187). Commands used the existing declared-dependency Python
environment with `PYTHONPATH` pointing at this independent worktree and `PYTHONUTF8=1`.
Browser selection: `TASK007C_BROWSER_CHANNEL=chromium`, `PLAYWRIGHT_BROWSERS_PATH` set to the
external browser cache; no repository dependency or configuration file was changed.

| Command / gate | Actual result |
|---|---|
| `python -m pytest -ra` | **1388 passed, 1 skipped, 1 warning in 717.89s (0:11:57)**; exit 0; 1389 collected |
| Browser tests within that full run | **118 passed**, including all 8 new archive cases; no browser skip/xfail/deselection |
| `python -m pytest tests/browser/test_market_archive_browser.py tests/integration/test_api_surface.py -ra` | **10 passed, 1 warning in 31.17s**, exit 0; earlier focused rerun |
| `python -m ruff check .` | All checks passed; exit 0 |
| `python -m ruff format --check .` | 216 files already formatted; exit 0 |
| `python -m mypy src tests` | Success: no issues in 211 source files; exit 0 |
| `git diff --check` | Clean; exit 0 |
| PostgreSQL dialect DDL/type/FK checks | Executed and passed in full suite |
| SQLite 0003→0004 existing evidence retention | Executed and passed in full suite |
| Actual normal Uvicorn and synthetic archive service paths | Executed and passed through full browser suite |

The single skip is `tests/integration/test_postgresql_migrations.py:67`:
`PHASE1_POSTGRESQL_TEST_URL is not configured`. No PostgreSQL live server is claimed tested.
The single warning is Starlette's deprecated `anyio.abc.BlockingPortal` alias. There are no final
failures/errors/xfails; no business test was replaced with an environment check.


The initial browser attempt failed because the default Playwright Chromium executable was absent.
Installed the browser version matching declared Playwright 1.55.0 into a separate cache, then ran
Chromium normally. No browser skip/xfail/replacement or weakened assertion was used. The first full
suite exposed old model/API allowlists that did not yet include the authorized additive files/routes;
only those precise allowlists were extended, keeping existing exclusions intact. A new migration
fixture's duplicate synthetic identity and the inherited favicon 404 were corrected before final
validation. These initial failures are not reported as passes.

Representative 0003→0004 evidence includes nonempty Legacy Decision, Narrative Result and watchlist
rows. The temporary SQLite test compares all preexisting table definitions and row values before
and after upgrade and downgrade, and successfully reads both ledgers through their real repositories.
Other archive tests cover restart with a fresh engine, A→B→A, changed rolling D1 window, offline
provider construction failure, row precision, malformed/unfinished facts, partial/total failures,
concurrency, duplicate/conflicting batches, membership sealing and 500+101 pagination without gaps.

Real Uvicorn uses temporary databases only. Normal `ai_infra_quant.backend.main:app` is covered by
the existing browser startup test. New browser tests use that application factory with a test-only
synthetic provider injection; they exercise actual POST/GET/SQLite, health/home/static/OpenAPI and
0004 head. The test-only control routes are absent from production composition. Screenshot evidence
and execution attribution: [docs/evidence/TASK_006B1](../evidence/TASK_006B1/README.md).

An additional real-browser/process probe also passed (exit 0): explicitly saved US.AVGO,
clicked another watchlist Security while capture was pending, and verified the late response did
not populate the other Security's detail. It then stopped the synthetic Uvicorn process, started
normal `ai_infra_quant.backend.main:app` over the same temporary database, verified 0004 and exact
saved capture readback, and read M1 pages 500/101 at 390 px while watchlist initialization returned
an intentional synthetic 503. After restart there were zero POSTs and zero unexpected page errors;
normal OpenAPI contained no test-only routes. The precommit startup identity was supplied from
verified starting HEAD, as the existing launcher does; this does not pretend the dirty worktree
was already an immutable Git object. An initial probe teardown hit Windows log-handle permissions;
rerunning with permission to stop only its own spawned process trees completed and cleaned its
new temporary directory. No app source or acceptance assertion was changed for that issue.

Environment limits: no Futu/OpenD login, real market/manual trading-date completeness claim, paid
model call or broker connection was performed. PostgreSQL live migration remains optional and was
not run without its explicitly configured isolated test URL; dialect DDL checks run independently.
These limitations do not become false real-market, PostgreSQL-live or independent-review acceptance.

## 5. Changed files and protected scope

| Change | File |
|---|---|
| Modified | [README.md](../../README.md) |
| Modified | [README_FIRST.md](../../README_FIRST.md) |
| Modified | [docs/API_CONTRACTS.md](../../docs/API_CONTRACTS.md) |
| Modified | [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) |
| Modified | [docs/DATABASE_SCHEMA.md](../../docs/DATABASE_SCHEMA.md) |
| Modified | [docs/MASTER_SPEC.md](../../docs/MASTER_SPEC.md) |
| Modified | [docs/PAQS_E_WORKBENCH.md](../../docs/PAQS_E_WORKBENCH.md) |
| Modified | [docs/REQUIREMENTS_MATRIX.md](../../docs/REQUIREMENTS_MATRIX.md) |
| Modified | [docs/ROADMAP.md](../../docs/ROADMAP.md) |
| Modified | [docs/STRATEGY_SPEC.md](../../docs/STRATEGY_SPEC.md) |
| Modified | [src/ai_infra_quant/application/bootstrap.py](../../src/ai_infra_quant/application/bootstrap.py) |
| Modified | [src/ai_infra_quant/backend/api/router.py](../../src/ai_infra_quant/backend/api/router.py) |
| Modified | [src/ai_infra_quant/backend/dependencies.py](../../src/ai_infra_quant/backend/dependencies.py) |
| Modified | [src/ai_infra_quant/database/models/__init__.py](../../src/ai_infra_quant/database/models/__init__.py) |
| Modified | [src/ai_infra_quant/frontend/static/app.css](../../src/ai_infra_quant/frontend/static/app.css) |
| Modified | [src/ai_infra_quant/frontend/templates/index.html](../../src/ai_infra_quant/frontend/templates/index.html) |
| Modified | [tests/architecture/test_task006a_boundaries.py](../../tests/architecture/test_task006a_boundaries.py) |
| Modified | [tests/architecture/test_task006b2_boundaries.py](../../tests/architecture/test_task006b2_boundaries.py) |
| Modified | [tests/architecture/test_task006b_boundaries.py](../../tests/architecture/test_task006b_boundaries.py) |
| Modified | [tests/architecture/test_task007a_boundaries.py](../../tests/architecture/test_task007a_boundaries.py) |
| Modified | [tests/architecture/test_task007b_boundaries.py](../../tests/architecture/test_task007b_boundaries.py) |
| Modified | [tests/browser/conftest.py](../../tests/browser/conftest.py) |
| Modified | [tests/integration/test_api_surface.py](../../tests/integration/test_api_surface.py) |
| Modified | [tests/integration/test_paqs_e_ledger_migrations.py](../../tests/integration/test_paqs_e_ledger_migrations.py) |
| Modified | [tests/integration/test_paqs_e_narrative_ledger_api.py](../../tests/integration/test_paqs_e_narrative_ledger_api.py) |
| Modified | [tests/integration/test_paqs_e_partial_actions_api.py](../../tests/integration/test_paqs_e_partial_actions_api.py) |
| Modified | [tests/integration/test_paqs_e_research_continuation_api.py](../../tests/integration/test_paqs_e_research_continuation_api.py) |
| Modified | [tests/integration/test_paqs_e_search_multiplicity_api.py](../../tests/integration/test_paqs_e_search_multiplicity_api.py) |
| Modified | [tests/integration/test_postgresql_migrations.py](../../tests/integration/test_postgresql_migrations.py) |
| Added | [docs/evidence/TASK_006B1/README.md](../../docs/evidence/TASK_006B1/README.md) |
| Added | [docs/evidence/TASK_006B1/archive-1440-dark.png](../../docs/evidence/TASK_006B1/archive-1440-dark.png) |
| Added | [docs/evidence/TASK_006B1/archive-1440-light.png](../../docs/evidence/TASK_006B1/archive-1440-light.png) |
| Added | [docs/evidence/TASK_006B1/archive-390-dark.png](../../docs/evidence/TASK_006B1/archive-390-dark.png) |
| Added | [docs/evidence/TASK_006B1/archive-390-light.png](../../docs/evidence/TASK_006B1/archive-390-light.png) |
| Added | [docs/evidence/TASK_006B1/archive-900-dark.png](../../docs/evidence/TASK_006B1/archive-900-dark.png) |
| Added | [docs/evidence/TASK_006B1/archive-900-light.png](../../docs/evidence/TASK_006B1/archive-900-light.png) |
| Added | [docs/reports/TASK_006B1_IMPLEMENTATION_REPORT.md](../../docs/reports/TASK_006B1_IMPLEMENTATION_REPORT.md) |
| Added | [src/ai_infra_quant/application/market_data_archive.py](../../src/ai_infra_quant/application/market_data_archive.py) |
| Added | [src/ai_infra_quant/backend/api/v1/market_data_archive.py](../../src/ai_infra_quant/backend/api/v1/market_data_archive.py) |
| Added | [src/ai_infra_quant/backend/schemas/market_data_archive.py](../../src/ai_infra_quant/backend/schemas/market_data_archive.py) |
| Added | [src/ai_infra_quant/core/domain/market_data_archive.py](../../src/ai_infra_quant/core/domain/market_data_archive.py) |
| Added | [src/ai_infra_quant/core/ports/market_data_archive.py](../../src/ai_infra_quant/core/ports/market_data_archive.py) |
| Added | [src/ai_infra_quant/database/migrations/versions/0004_task006b1_market_archive.py](../../src/ai_infra_quant/database/migrations/versions/0004_task006b1_market_archive.py) |
| Added | [src/ai_infra_quant/database/models/market_data_archive.py](../../src/ai_infra_quant/database/models/market_data_archive.py) |
| Added | [src/ai_infra_quant/database/repositories/market_data_archive.py](../../src/ai_infra_quant/database/repositories/market_data_archive.py) |
| Added | [src/ai_infra_quant/frontend/static/market-data-archive.js](../../src/ai_infra_quant/frontend/static/market-data-archive.js) |
| Added | [tests/architecture/test_task006b1_boundaries.py](../../tests/architecture/test_task006b1_boundaries.py) |
| Added | [tests/browser/archive_server.py](../../tests/browser/archive_server.py) |
| Added | [tests/browser/archive_support.py](../../tests/browser/archive_support.py) |
| Added | [tests/browser/test_market_archive_browser.py](../../tests/browser/test_market_archive_browser.py) |
| Added | [tests/integration/test_market_archive_migration.py](../../tests/integration/test_market_archive_migration.py) |
| Added | [tests/integration/test_market_data_archive_api.py](../../tests/integration/test_market_data_archive_api.py) |
| Added | [tests/unit/test_market_data_archive.py](../../tests/unit/test_market_data_archive.py) |

Only listed existing files were edited. Legacy test edits are restricted to required migration-head,
new migration/model/table and four API-route allowlists; old business assertions remain. No third-party
package, CI/launcher configuration, provider adapter, domain strategy or accepted evidence changed.
Startup readiness remains enforced by the existing launcher/health chain; only the application's
expected migration revision constant needed to move to 0004. The launcher was not redesigned.

Original migration Git blob identities remain byte-for-byte:

| Migration | Unchanged blob SHA |
|---|---|
| 0001 | `add8f78b786482f1598824bde9df6df695a87a3f` |
| 0002 | `ce61b7a8789385cf4df9d0550d196e27fa969e7b` |
| 0003 | `78890f99a6365fcc82142f1fddc5781f5ff74397` |

The 29 modified and 24 added files above are the complete 53-file change.
All 313 other preexisting tracked files were checked unchanged,
including contracts/handoff/hold, accepted reports/reviews/closeouts, PAQS-E master strategy,
Narrative and legacy prompts/validator, Snapshot serialization/hash, model registry/endpoints,
credentials, Research/Synthesis and source-SHA handshake. No user database was migrated or removed.
Other worktree HEADs remained C1 `3e98d8c5f9948dcaefe59eb3b7b847bd99ba8908`,
C2 `d2d25efc79d2560a7ed09895c7dd7a2c1724aee9`, ADC `66a3ca7bbff258665b25e5ab17231138bf3cc49f`.
Untracked `phase1_remediation_commit.txt` remained present with SHA-256
`C791BA73B41C4E7719957607E025105A8110FA54A2E1A67F3C5B142DA8030440`.

## 6. Delivery boundary

Push only the task branch, read back its GitHub head and this report, and return the exact resulting
SHA. Authority remains `02326a3bb19c2a89352d765f5331670b5f3f466d`; no force, merge, authority update
or follow-on task. This report records implementation validation only. Independent review is pending.
