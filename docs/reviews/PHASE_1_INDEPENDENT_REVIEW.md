# AI Infra Quant — Independent Phase 1 Review

## Verdict

**NEEDS REVISION. Do not commit Phase 1 and do not start Phase 2 yet.**

The submitted test suite passes, and the basic package/API boundary is sound, but several foundation defects are not covered by the current 60 tests. The most important are migration immutability, canonical security identity, snapshot status semantics, database uniqueness/FK enforcement, and bootstrap configuration drift.

## Independently validated

- Extracted and reviewed the submitted Phase 1 archive.
- Re-ran the included test suite in the available review runtime: **60 passed**.
- Confirmed no paper/live order route is present.
- Confirmed the custom SQLite decimal storage round-trips the submitted extreme values as TEXT.
- Ran adversarial checks beyond the submitted suite.

## Blocker / High findings

### F1 — Alembic revision is not immutable

`src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py:84` calls `Base.metadata.create_all(...)`; line 98 calls `Base.metadata.drop_all(...)`.

A future model imported into `Base.metadata` becomes part of historical revision 0001. This was reproduced in a temporary copy: adding a hypothetical future model caused `alembic upgrade head` at revision 0001 to create `future_phase_table`.

**Required:** rewrite revision 0001 with explicit `op.create_table`, indexes, constraints, and explicit reverse downgrade operations. Do not use live ORM metadata in a historical revision.

### F2 — Canonical security identity is not implemented

Generic trim/uppercase is used in:

- `core/domain/security.py:17-23`
- `backend/schemas/security.py:50-56`
- `application/security_service.py:34-35`
- `database/repositories/security.py:76-97`

Adversarial API results:

- `HK / 9698` -> **201**, stored as `HK.9698`, despite seeded `HK.09698`.
- `CN / 600519` -> **201**, although Phase 1 has no CN canonicalizer.
- `US / BAD/$` -> **201**.
- HTML-like symbols are accepted.

**Required:** market-specific fail-closed canonicalizer. Phase 1 baseline: US documented ASCII pattern; HK 1-5 digits left-padded to five; unsupported market returns `INVALID_MARKET`; uniqueness after canonicalization.

### F3 — User-controlled HTML is rendered through `innerHTML`

`frontend/static/app.js:13-19` interpolates `security.display_symbol` into `innerHTML`. Because arbitrary symbol markup is currently accepted, this is a stored DOM-injection/XSS surface.

**Required:** construct DOM nodes and assign user-controlled values through `textContent`; never interpolate API/user data into `innerHTML`. Keep strict canonical validation as a separate defense.

### F4 — Snapshot quality and data availability remain conflated

- `core/domain/portfolio.py:44` types snapshot quality as `DataStatus`.
- `database/seed.py:388` stores `AVAILABLE`.
- `backend/api/v1/performance.py:61` hardcodes `AVAILABLE`.

An inception snapshot with known cash, units, NAV, and zero positions should be `SnapshotQualityStatus.COMPLETE`; provider availability remains `UNAVAILABLE`.

**Required:** separate `DataAvailabilityStatus`, `SnapshotQualityStatus`, `ScoreCoverageStatus`, and `CapabilityStatus` across domain, DB checks, schemas, seed, API, and tests.

### F5 — “Unique active” database invariants are not enforced

Nullable columns inside normal unique constraints do not enforce the documented active uniqueness in SQLite/PostgreSQL.

Affected examples:

- `PortfolioAccountModel`: `models/portfolio.py:84-96`
- `ProviderSymbolMappingModel`: `models/security.py:79-105`
- `LedgerAccountModel`: `models/accounting.py:22-52`
- `StrategyAssignmentModel`: no active uniqueness
- `SettingModel`: nullable `scope_id` defeats the intended unique system setting key

Adversarial inserts confirmed the database accepted:

- a second active portfolio-account membership for the same broker account;
- a duplicate active provider mapping;
- a duplicate ledger logical key with nullable dimensions.

**Required:** partial unique indexes or non-null canonical logical keys that work on SQLite and PostgreSQL. Add adversarial migration tests.

### F6 — `pre_flow_snapshot_id` is not a foreign key

`database/models/accounting.py:134` is a plain `String(36)`, while the specification describes a nullable FK to `portfolio_snapshots`.

**Required:** real FK with `RESTRICT`; Phase 2 application validation later adds same-portfolio/FLOW_PRE/COMPLETE rules.

### F7 — Provider-mapping protection is bypassable through UPDATE

Migration trigger `0001_phase1_foundation.py:67-78` protects INSERT only. A mapping created for a seeded security can be updated to reference a user-supplied security; this was reproduced.

The user-supplied DB check also omits `metadata_status='UNAVAILABLE'`.

**Required:** protect INSERT and UPDATE; extend the fail-closed check; add tests.

### F8 — Bootstrap config changes corrupt the singleton opening state

`database/seed.py:103-107` makes `portfolio_id` depend on the configurable name, while account/link/watchlist/ledger/snapshot IDs are fixed. Restarting with a different `INITIAL_PORTFOLIO_NAME` created two active portfolios, only one snapshot/link, and `/api/v1/portfolio` failed with `PORTFOLIO_NOT_FOUND` in the adversarial test.

`OPENING_AT` is also hardcoded rather than derived from inception date/timezone.

**Required:** fixed singleton bootstrap identity plus canonical seed-config fingerprint. On later config mismatch, fail atomically with `SEED_CONFIGURATION_MISMATCH`. Derive opening UTC instant from local inception midnight via `zoneinfo`. Do not silently create a second opening portfolio.

### F9 — SQLite timezone round-trip can change the instant

Repositories repair naive SQLite datetimes using `.replace(tzinfo=UTC)`, for example `database/repositories/security.py:26-32` and `portfolio.py:38-40`.

Adversarial result:

- written: `2026-08-31T12:00:00+08:00`
- read/domain: `2026-08-31T12:00:00+00:00`

The instant moved by eight hours.

**Required:** a dialect-aware UTC datetime type or strict bind/result normalization: convert aware input to UTC before storing, reject naive input, restore UTC on read. Add offset round-trip tests.

## Medium findings to fix in the same Phase 1 remediation

### F10 — Signed zero is not canonical at domain/API boundaries

`core/domain/money.py:38-40` renders `Decimal('-0.00')` as `-0.00`, while DB storage normalizes it to positive zero. This can produce inconsistent canonical request hashes and API values.

**Required:** normalize signed zero in `parse_decimal`/canonical serializer before domain comparison, API serialization, persistence, and idempotency hashing.

### F11 — Strategy implementation status has duplicate sources

`StrategyRegistry` exists, but `/api/v1/strategies` reads `implementation_status` from the database and hardcodes `required_data_status`. This can drift once code implementations appear.

**Required:** implementation status from registry/build descriptor; research status from audited persistence; required-data status from provider capabilities; enabled from persisted configuration.

### F12 — Ledger UoW checks only aggregate debit equals credit

`database/repositories/unit_of_work.py:41-61` does not validate each entry’s positive amount/base amount/FX, transaction ID consistency, unique entry number, account portfolio ownership, or base-currency consistency.

**Required now:** add foundation-level invariants and checks so invalid economic facts cannot be inserted when Phase 2 begins.

### F13 — Concurrency and DB conflicts can become 500s

Security creation and watchlist add use check-then-insert without mapping `IntegrityError` to stable 409 responses. Concurrent local requests can race.

**Required:** catch/translate expected integrity conflicts inside the application boundary and add deterministic double-submit tests.

## Recommended acceptance gate

Phase 1 can be accepted after:

1. Every blocker/high item is fixed.
2. The migration is explicit and deterministic.
3. Adversarial tests are added and pass.
4. Existing 60 tests continue to pass.
5. Ruff and mypy pass in the project’s Python 3.12 environment.
6. OpenAPI remains free of Phase 2/live routes.
7. No external provider or broker dependency is added.
