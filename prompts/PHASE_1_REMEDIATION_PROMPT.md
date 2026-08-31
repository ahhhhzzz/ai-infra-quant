# Codex Prompt — Phase 1 Independent Review Remediation

PHASE 1 REVIEW REMEDIATION ONLY

Read the following files in full before editing:

- AGENTS.md
- docs/MASTER_SPEC.md
- docs/ARCHITECTURE.md
- docs/DATABASE_SCHEMA.md
- docs/API_CONTRACTS.md
- docs/STRATEGY_SPEC.md
- docs/REQUIREMENTS_MATRIX.md
- docs/phases/PHASE_1_PLAN.md
- all current Phase 1 source files, migrations, templates, JavaScript, and tests

Phase 1 has been implemented, but independent review found foundation defects not covered by the current test suite.

Do not begin Phase 2.
Do not add PaperBroker execution.
Do not add order/fill/deposit/withdraw/FX routes.
Do not implement AIInfraStrategy.
Do not add Futu, OpenD, EastMoney, or any external provider SDK/call.
Do not add live routes or authentication.
Do not commit or push.
Do not modify Git remotes or global Git configuration.
Preserve unrelated user changes.

Before editing:

1. Run `git status --short --branch --untracked-files=all`.
2. List every file you plan to change.
3. Confirm all changes are limited to Phase 1 remediation, tests, migrations, and evidence documentation.

## 1. Make Alembic revision 0001 explicit and immutable

The current revision calls `Base.metadata.create_all()` and `Base.metadata.drop_all()`. This is prohibited because later ORM models would retroactively alter historical revision 0001.

Because Phase 1 has not been committed or released and no meaningful user trading data exists, rewrite `0001_phase1_foundation.py` rather than adding a future-phase migration merely to preserve the defective revision.

Requirements:

- Use explicit Alembic `op.create_table`, `op.create_index`, constraints, and trigger DDL.
- Use explicit reverse-order downgrade operations.
- Do not import/use `Base.metadata` in the revision.
- Do not call `create_all()` or `drop_all()` in any migration.
- Preserve dialect-aware `ExactDecimal`: SQLite declared type `TEXT`; PostgreSQL `NUMERIC(38,18)`.
- Preserve append-only SQLite triggers and all corrected constraints.
- Add a static test rejecting `Base.metadata`, `create_all`, or `drop_all` references in versioned migration files.
- Add a deterministic schema test that revision 0001 creates exactly its declared Phase 1 tables, independent of later ORM models.
- Document that existing local Phase 1 development databases created by the prior draft must be recreated; do not delete arbitrary databases automatically.

## 2. Implement separate status taxonomies

Create and consistently use distinct enums/types:

DataAvailabilityStatus:
- AVAILABLE
- MISSING
- UNAVAILABLE
- NOT_SUPPORTED
- INVALID

SnapshotQualityStatus:
- COMPLETE
- PARTIAL
- INVALID

ScoreCoverageStatus:
- COMPLETE
- PARTIAL
- INVALID

CapabilityStatus:
- SUPPORTED
- NOT_SUPPORTED
- NOT_IMPLEMENTED
- UNAVAILABLE
- UNKNOWN

Requirements:

- `PortfolioSnapshot.quality_status` uses SnapshotQualityStatus, not DataAvailabilityStatus.
- The inception snapshot is `COMPLETE`.
- External market/FX/fundamental/event capabilities remain `UNAVAILABLE`.
- API portfolio/performance examples and response models return `quality_status=COMPLETE` for the inception point.
- Add DB check constraints and tests for allowed values.
- Update docs and requirements matrix consistently.

## 3. Implement market-specific, fail-closed security canonicalization

Replace generic trim/uppercase identity normalization with a canonicalization registry or equivalent core service.

Phase 1 baseline:

US:
- trim and uppercase;
- accept only a documented ASCII symbol pattern using letters, digits, period, and hyphen;
- reject empty values, whitespace, slash, angle brackets, dollar signs, and other invalid characters.

HK:
- accept exactly one to five ASCII digits after trimming;
- left-pad to five digits;
- `9698 -> 09698`;
- `700 -> 00700`.

Markets without a configured canonicalizer:
- reject with stable error code `INVALID_MARKET`.

Requirements:

- Apply canonicalization consistently at API validation, domain construction, service, repository lookup/create, and seed identity generation.
- Enforce uniqueness after canonicalization.
- Creating `HK/9698` when `HK/09698` exists returns 409 with the existing `security_id`.
- Do not infer exchange, lot size, calendar, provider mapping, or tradability.
- Add tests for lowercase US, BRK.B/hyphen if allowed, HK padding, duplicate HK identity, invalid characters, unsupported market, and normalized conflict.

## 4. Eliminate user-controlled `innerHTML`

`frontend/static/app.js` currently interpolates API/user-controlled values into `innerHTML`.

Requirements:

- Render watchlist and status rows using `document.createElement`, `textContent`, safe attributes, and event listeners.
- Do not interpolate user/API values into `innerHTML`, `outerHTML`, or `insertAdjacentHTML`.
- Add a frontend/static security test or source-level test proving user-controlled rendering does not use unsafe HTML sinks.
- Keep canonical validation as defense in depth; do not rely on validation alone.

## 5. Enforce documented active/logical uniqueness in the database

Normal unique constraints containing nullable columns do not enforce the intended invariants.

Fix at least:

- one active portfolio membership per `broker_account_id` where `effective_to IS NULL`;
- one active provider mapping per `(security_id, provider_type, provider_name)` where `valid_to IS NULL`;
- one active reverse provider mapping per `(provider_type, provider_name, provider_symbol)` where `valid_to IS NULL`;
- one active strategy assignment for its approved logical scope where `effective_to IS NULL`;
- one logical ledger account even when broker/security/currency dimensions are absent;
- one setting per logical scope/key even when `scope_id` is absent.

Use SQLite/PostgreSQL-compatible partial indexes, separate partial indexes, or explicit non-null canonical logical-key columns. Do not rely on NULL equality in a normal unique constraint.

Add adversarial migration tests that a second active/logical duplicate is rejected.

## 6. Add the missing cash-flow snapshot foreign key

`cash_flows.pre_flow_snapshot_id` must be a nullable FK to `portfolio_snapshots.id` with `ON DELETE RESTRICT`.

Phase 2 will add semantic validation for same portfolio, official FLOW_PRE, COMPLETE quality, complete marks, and FX. Phase 1 must establish the actual FK now.

Add FK inspection and rejection tests.

## 7. Close provider-mapping fail-closed bypasses

Requirements:

- SQLite DB protection must reject both INSERT and UPDATE that would attach a provider mapping to a `USER_SUPPLIED` security.
- Extend the user-supplied security DB invariant so `metadata_status` remains `UNAVAILABLE` and all inferred metadata/trading-rule fields remain absent.
- Add tests for INSERT rejection and UPDATE-to-user-security rejection.
- Do not claim PostgreSQL trigger parity unless implemented; document current Phase 1 runtime scope truthfully.

## 8. Make bootstrap singleton configuration safe

The current seed derives `portfolio_id` from mutable portfolio name but uses fixed IDs for related opening entities. Changing seed settings can create inconsistent multiple active portfolios.

Implement a deterministic, atomic bootstrap contract:

- use stable singleton opening identity independent of mutable display name; and/or an equivalent explicit singleton design;
- derive `opening_at` from `inception_date` at local midnight in `valuation_timezone`, converted to UTC via `zoneinfo`;
- store a canonical seed configuration fingerprint covering portfolio name, base currency, initial capital, units, NAV, inception date, and valuation timezone;
- on later startup with a different bootstrap configuration, fail atomically with stable error `SEED_CONFIGURATION_MISMATCH`;
- do not create a second active opening portfolio;
- do not silently ignore changed capital/units/NAV/currency/date/timezone;
- no partial writes on mismatch.

Add tests for idempotent same-config startup and mismatch of name, capital, currency, inception date, and timezone.

## 9. Implement exact UTC datetime persistence

SQLite `DateTime(timezone=True)` does not preserve offsets, and `.replace(tzinfo=UTC)` can change the instant.

Implement a reusable UTC datetime persistence type or strict equivalent:

- reject naive datetimes at the persistence boundary;
- convert aware datetimes to UTC before storage;
- use a canonical SQLite representation that round-trips the instant exactly;
- restore timezone-aware UTC datetimes on read;
- use a suitable PostgreSQL timezone-aware type;
- remove repository-level blind `.replace(tzinfo=UTC)` repair logic.

Add tests showing `2026-08-31T12:00:00+08:00` round-trips as `2026-08-31T04:00:00Z`.

## 10. Normalize signed zero everywhere

Before domain comparison, API serialization, persistence, canonical request hashing, and idempotency comparison:

- `Decimal('-0')`
- `Decimal('-0.00')`
- `Decimal('0.000000000000000000')`

must become one positive-zero canonical value.

Add unit, persistence, API, and canonical-hash tests.

## 11. Establish one source of truth for strategy statuses

Requirements:

- `implementation_status` comes from `StrategyRegistry`/build-time descriptor;
- `research_status` comes from audited persisted lifecycle/version metadata;
- `required_data_status` is derived at runtime from provider capabilities/coverage;
- `enabled` comes from persisted configuration.

Do not persist duplicate authoritative implementation state that can drift from the registry. Phase 1 AIInfraStrategy must report:

- implementation_status = NOT_IMPLEMENTED
- research_status = RESEARCH_UNVALIDATED
- required_data_status = UNAVAILABLE
- enabled = false

Add drift-prevention tests.

## 12. Harden opening ledger invariants

Before adding any transaction/entries, the Unit of Work must validate at least:

- at least two entries;
- every entry belongs to the supplied transaction ID;
- entry IDs and entry numbers are unique within the transaction;
- direction is DEBIT or CREDIT;
- amount and base_amount are strictly positive;
- base_fx_rate is strictly positive;
- entry currency/base currency is canonical and consistent with approved transaction/portfolio context;
- debit and credit totals balance exactly in Python Decimal;
- referenced ledger accounts belong to the same portfolio;
- no entry is silently omitted from balance validation because of an invalid direction.

Add DB CheckConstraints where portable and Unit-of-Work tests for negative values, zero FX, invalid direction, wrong transaction ID, duplicate entry numbers, and cross-portfolio account references.

## 13. Translate expected integrity races into stable API errors

Security create and watchlist add use check-then-insert. Concurrent/double requests can still hit an `IntegrityError`.

Requirements:

- catch and translate expected unique/integrity conflicts at the application boundary;
- return the documented stable 409 problem response rather than a 500;
- rollback cleanly;
- preserve idempotent watchlist behavior;
- add deterministic conflict/race-oriented integration tests where practical.

## Validation

After fixes:

1. Recreate a fresh temporary SQLite database from the rewritten revision 0001.
2. Run Alembic upgrade and current.
3. Start the app on loopback and verify `/health` and `/`.
4. Inspect `/openapi.json`; the Phase 1 route surface must remain unchanged and contain no Phase 2/live routes.
5. Run the complete existing test suite plus all new adversarial tests.
6. Run Ruff check and format check.
7. Run mypy on source and tests.
8. Run `git diff --check`.
9. Run secret and forbidden-import/dependency scans.
10. Confirm no external network/provider/broker call occurred.

Update:

- README.md
- docs/ARCHITECTURE.md
- docs/DATABASE_SCHEMA.md
- docs/API_CONTRACTS.md
- docs/REQUIREMENTS_MATRIX.md
- docs/phases/PHASE_1_PLAN.md

Do not change strategy formulas or approve STRATEGY_SPEC.

At the end report:

- initial/final Git status;
- every modified/created file;
- each finding above as RESOLVED or DEFERRED with justification;
- exact migration design;
- adversarial test evidence;
- total pytest result;
- Ruff/mypy result;
- route list;
- known limitations;
- confirmation that Phase 2 was not started;
- confirmation that no commit, push, remote change, global Git config change, broker SDK, OpenD connection, external provider call, paper order, or live route occurred.

Stop and wait for independent re-review.
