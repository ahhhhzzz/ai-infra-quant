# Phase 1 Plan — Foundation and Contracts

Status: Phase 1 remediation implemented locally on 2026-08-31; awaiting independent re-review

Phase boundary: foundation, contracts, migrations, initial read-only state, unverified canonical-security creation, and watchlist CRUD only

## 1. Objective

Create a runnable local FastAPI/SQLite modular-monolith foundation that proves domain/adapter separation, dialect-exact Decimal persistence, and truthful missing-data behavior. Initialize the configurable AI Infra portfolio/watchlist with HKD 20,000, 200 units, NAV 100, and no positions. Allow creation of user-supplied canonical securities that remain explicitly unverified/non-tradable until later verification. Do not implement paper execution, strategy calculations, backtesting, any external provider, Futu/OpenD, or live trading.

`APPROVE PHASE 1` authorizes this foundation scope only. It does not approve `STRATEGY_SPEC.md`, select a sizing formula, or satisfy the later exact strategy gate `APPROVE STRATEGY SPEC V1`.

## 2. Preconditions and change control

Before any Phase 1 edit:

1. read `AGENTS.md`, `docs/MASTER_SPEC.md`, all Phase 0 design documents, and this plan in full;
2. run `git status --short --branch`, record all pre-existing changes, and avoid/reconcile overlap before editing;
3. verify the exact instruction `APPROVE PHASE 1` is present;
4. state the planned files and any deviation from the exact list below;
5. do not create a checkpoint if it would include unrelated changes; never push or modify remotes/global Git configuration.

Any design-affecting deviation first updates architecture/contracts/matrix and is reported. It does not authorize future-phase behavior.

## 3. Exact file set

All paths are relative to repository root. Phase 1 creates the following files unless already present from an approved user change; in that case it makes the smallest compatible change and reports it.

### 3.1 Project/configuration

```text
.env.example
.gitignore
README.md
pyproject.toml
alembic.ini
```

`pyproject.toml` targets CPython 3.12 and declares only foundation runtime dependencies: FastAPI,
Uvicorn, SQLAlchemy 2.x, Alembic, Pydantic/Pydantic Settings, Jinja2, and the IANA `tzdata`
database required by `zoneinfo` on Windows. Development extras: pytest, pytest-cov, HTTPX, Ruff,
and mypy plus necessary type stubs. Exact compatible versions must be resolved/recorded during
Phase 1; no broker/provider SDK belongs in dependencies.

`.env.example` contains safe placeholders/defaults only:

```dotenv
APP_ENV=development
DATABASE_URL=sqlite:///./data/ai_infra_quant.db
HOST=127.0.0.1
PORT=8000
TRADING_MODE=PAPER
AUTO_EXECUTION=false
ACTIVE_BROKER=paper
MARKET_DATA_PROVIDER=none
FUNDAMENTAL_DATA_PROVIDER=none
EVENT_DATA_PROVIDER=none
API_BASE_URL=http://127.0.0.1:8000
```

No `FUTU_*` variable is required in Phase 1 because no Futu code exists. Adding future placeholders is allowed only if clearly unused and non-secret.

### 3.2 Package root and configuration

```text
src/ai_infra_quant/__init__.py
src/ai_infra_quant/config.py
src/ai_infra_quant/logging_config.py
```

Configuration validates loopback-only Phase 1 hosting, `AUTO_EXECUTION=false`, and supported enum values. Logging is structured/redacted and never logs settings that may later contain secrets.

### 3.3 Core domain and ports

```text
src/ai_infra_quant/core/__init__.py
src/ai_infra_quant/core/domain/__init__.py
src/ai_infra_quant/core/domain/common.py
src/ai_infra_quant/core/domain/enums.py
src/ai_infra_quant/core/domain/money.py
src/ai_infra_quant/core/domain/security.py
src/ai_infra_quant/core/domain/portfolio.py
src/ai_infra_quant/core/domain/strategy.py
src/ai_infra_quant/core/domain/execution.py
src/ai_infra_quant/core/domain/providers.py
src/ai_infra_quant/core/ports/__init__.py
src/ai_infra_quant/core/ports/broker.py
src/ai_infra_quant/core/ports/market_data.py
src/ai_infra_quant/core/ports/fundamental_data.py
src/ai_infra_quant/core/ports/event_data.py
src/ai_infra_quant/core/ports/repositories.py
src/ai_infra_quant/core/strategy/__init__.py
src/ai_infra_quant/core/strategy/registry.py
src/ai_infra_quant/core/portfolio/__init__.py
src/ai_infra_quant/core/accounting/__init__.py
src/ai_infra_quant/core/execution/__init__.py
src/ai_infra_quant/core/risk/__init__.py
src/ai_infra_quant/core/performance/__init__.py
src/ai_infra_quant/core/backtest/__init__.py
```

The six later behavior packages contain only boundary documentation/types needed by current contracts; no calculation/order simulator is implemented. Broker/provider ports expose the full canonical method signatures/capability models from the master spec, but no concrete adapter is invoked.

### 3.4 Application use cases

```text
src/ai_infra_quant/application/__init__.py
src/ai_infra_quant/application/unit_of_work.py
src/ai_infra_quant/application/bootstrap.py
src/ai_infra_quant/application/portfolio_queries.py
src/ai_infra_quant/application/security_service.py
src/ai_infra_quant/application/watchlist_service.py
src/ai_infra_quant/application/status_queries.py
```

Only read queries, idempotent initial bootstrap, validated unverified-security creation, and
default-watchlist add/remove are allowed. Security creation uses fail-closed US/HK canonicalizers
and forces `USER_SUPPLIED_UNVERIFIED`/`UNVERIFIED` with unavailable metadata; it performs no
provider call or tradability inference. Bootstrap uses a stable singleton identity, local-midnight
UTC conversion, and a canonical configuration fingerprint that rejects drift atomically. No
generic command bus, background worker, strategy run, order, fill, deposit, withdrawal, or FX use
case is created.

### 3.5 Integration descriptors/registries

```text
src/ai_infra_quant/integrations/__init__.py
src/ai_infra_quant/integrations/registry.py
src/ai_infra_quant/integrations/descriptors.py
```

These contain adapter descriptors and independent broker/market/fundamental/event registries. `paper`, `futu`, and `eastmoney` may be described as planned/`NOT_IMPLEMENTED`; `none` is the active unavailable data-provider descriptor. Do not create `integrations/futu`, import `futu`, install an SDK, open a socket, or implement PaperBroker.

### 3.6 Database and migrations

```text
src/ai_infra_quant/database/__init__.py
src/ai_infra_quant/database/base.py
src/ai_infra_quant/database/session.py
src/ai_infra_quant/database/types.py
src/ai_infra_quant/database/models/__init__.py
src/ai_infra_quant/database/models/security.py
src/ai_infra_quant/database/models/strategy.py
src/ai_infra_quant/database/models/portfolio.py
src/ai_infra_quant/database/models/accounting.py
src/ai_infra_quant/database/models/settings.py
src/ai_infra_quant/database/repositories/__init__.py
src/ai_infra_quant/database/repositories/unit_of_work.py
src/ai_infra_quant/database/repositories/security.py
src/ai_infra_quant/database/repositories/portfolio.py
src/ai_infra_quant/database/repositories/watchlist.py
src/ai_infra_quant/database/seed.py
src/ai_infra_quant/database/migrations/README.md
src/ai_infra_quant/database/migrations/env.py
src/ai_infra_quant/database/migrations/script.py.mako
src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py
```

Migration 0001 creates only Phase 1 tables needed for canonical identity, configuration, traceability, and opening accounting facts:

- securities, provider symbol mappings, watchlists/items;
- strategy definitions/assignments (AIInfra definition remains disabled, `PROPOSED / RESEARCH_UNVALIDATED`, and not implemented);
- broker profiles/accounts, portfolios, portfolio-account links;
- ledger accounts/transactions/entries, cash flows, unit transactions, cash-balance projection, portfolio snapshots;
- settings.

Orders/fills/settlements/positions and external-data/strategy-run/performance-series tables are
introduced in their behavior phases unless an FK required now is proven necessary. Revision 0001
uses explicit Alembic operations and is isolated from later ORM metadata. It includes the nullable
restricting cash-flow snapshot FK, corrected logical partial indexes, status checks, and SQLite
append-only/fail-closed guards. Normal startup checks the Alembic revision and never creates schema
from ORM metadata. Databases made by the earlier metadata-driven local draft must be recreated
manually; no arbitrary database is deleted.

Every Phase 1 financial column is declared through dialect-aware `ExactDecimal(38,18)`: SQLite migration DDL must emit fixed-scale canonical `TEXT` with no numeric affinity; PostgreSQL compilation must emit `NUMERIC(38,18)`. The SQLite TypeDecorator validates precision/scale/range, rejects floats, binds canonical padded text, and parses directly to `Decimal`. Ledger balance is checked with Python `Decimal` inside the Unit of Work before atomic commit. No SQLite `SUM`, numeric `CAST`, or decimal TEXT ordering/range query is used or described as exact. Append-only triggers remain database-enforced.

### 3.7 Backend/API and schemas

```text
src/ai_infra_quant/backend/__init__.py
src/ai_infra_quant/backend/main.py
src/ai_infra_quant/backend/dependencies.py
src/ai_infra_quant/backend/api/__init__.py
src/ai_infra_quant/backend/api/router.py
src/ai_infra_quant/backend/api/errors.py
src/ai_infra_quant/backend/api/v1/__init__.py
src/ai_infra_quant/backend/api/v1/portfolio.py
src/ai_infra_quant/backend/api/v1/positions.py
src/ai_infra_quant/backend/api/v1/performance.py
src/ai_infra_quant/backend/api/v1/watchlist.py
src/ai_infra_quant/backend/api/v1/securities.py
src/ai_infra_quant/backend/api/v1/strategies.py
src/ai_infra_quant/backend/api/v1/brokers.py
src/ai_infra_quant/backend/api/v1/providers.py
src/ai_infra_quant/backend/schemas/__init__.py
src/ai_infra_quant/backend/schemas/common.py
src/ai_infra_quant/backend/schemas/portfolio.py
src/ai_infra_quant/backend/schemas/security.py
src/ai_infra_quant/backend/schemas/watchlist.py
src/ai_infra_quant/backend/schemas/status.py
```

`main.py` also owns the unversioned `/health` and read-only HTML root. Router registration is an allowlist matching `API_CONTRACTS.md` Phase 1. There is no `orders.py`, `paper.py`, `live.py`, `accounts.py`, `signals.py`, `indicators.py`, `strategy_run.py`, or backtest route.

`POST /api/v1/securities` is part of the allowlist. It accepts only market, symbol, currency, instrument type, and optional display name; it cannot create verified tradability, mappings, calendars, or trading rules.

### 3.8 Minimal frontend

```text
src/ai_infra_quant/frontend/templates/index.html
src/ai_infra_quant/frontend/static/app.css
src/ai_infra_quant/frontend/static/app.js
```

The page is a dark, desktop-oriented dashboard with read-only financial panels for opening portfolio/NAV/cash and the empty-position/performance inception point, plus identity/watchlist administration and unmistakable provider statuses. It has no paper/live order controls, fake charts/prices/scores, external CDN requirement, or frontend-to-OpenD path.

### 3.9 Tests

```text
tests/conftest.py
tests/unit/test_config.py
tests/unit/test_decimal_contract.py
tests/unit/test_capabilities.py
tests/unit/test_registries.py
tests/unit/test_domain_models.py
tests/architecture/test_import_boundaries.py
tests/integration/test_migrations.py
tests/integration/test_bootstrap.py
tests/integration/test_seed_idempotency.py
tests/integration/test_portfolio_api.py
tests/integration/test_security_api.py
tests/integration/test_watchlist_api.py
tests/integration/test_status_api.py
tests/integration/test_api_surface.py
tests/integration/test_offline_startup.py
tests/integration/test_sqlite_decimal_roundtrip.py
```

Tests create isolated temporary SQLite databases and never use the configured production/local database. Test seed fixtures are labelled synthetic/internal and cannot call a provider.

### 3.10 Phase completion documentation changes

```text
docs/ARCHITECTURE.md
docs/DATABASE_SCHEMA.md
docs/API_CONTRACTS.md
docs/REQUIREMENTS_MATRIX.md
docs/phases/PHASE_1_PLAN.md
```

Only update these if implementation reveals an approved design correction or to record actual Phase 1 evidence/status. Do not change `MASTER_SPEC.md` silently. `STRATEGY_SPEC.md` is not changed unless the user separately approves a Phase 0 correction; no strategy implementation occurs.

## 4. Implementation order

1. **Reconfirm scope and clean baseline.** Record Git status, Python availability, and all user changes. Do not touch remotes/global config.
2. **Packaging/tooling.** Add `pyproject.toml`, safe environment example, ignore rules, package root, config/logging. Install only declared foundation/dev dependencies after normal approval rules.
3. **Canonical domain contracts.** Implement Decimal validators/value objects, verified/unverified identity/status enums, security/portfolio/strategy/execution/provider models and four independent provider/broker ports.
4. **Boundary/registry proof.** Implement typed independent registries/descriptors, then import-boundary and registry tests. No concrete adapter.
5. **Persistence foundation.** Add dialect-aware `ExactDecimal` binding/validation, SQLAlchemy models and Alembic environment/revision. Inspect SQLite DDL/`typeof()` to prove TEXT affinity, compile PostgreSQL type to NUMERIC, and verify Python-Decimal UoW balance plus append-only triggers.
6. **Bootstrap facts.** Implement stable-key/idempotent seed for securities, default watchlist, portfolio/paper descriptor-account, balanced opening contribution, 200 units, HKD cash projection, NAV 100 inception snapshot. Prove rebuild/balance values without adding mutation APIs.
7. **Repositories/application.** Add UoW, read queries, unverified-security service, watchlist service, status queries; test rollback/idempotency/normalization.
8. **Versioned API.** Add problem errors and only the Phase 1 route allowlist. Prove route denylist before frontend work.
9. **Frontend.** Render real internal/bootstrap responses and unavailable statuses. Never insert placeholder market values/scores.
10. **Full validation and evidence.** Run migrations/startup/tests/Ruff/mypy, inspect OpenAPI/dependencies/secrets/Git diff, update requirements evidence, and stop.

## 5. Acceptance criteria

Phase 1 is complete only when all are true:

1. A clean CPython 3.12 environment installs the project without any broker SDK.
2. Alembic upgrades an empty temporary SQLite database to head; normal startup refuses a missing/outdated revision rather than silently using `create_all`.
3. Seed runs twice with identical row counts and stable economics: HKD equity/cash `20000`, units `200`, NAV `100`, no positions, zero investment return.
4. Opening ledger facts balance exactly in Python `Decimal` inside one UoW and every persisted financial value returns as `Decimal`, never float. SQLite storage is TEXT; PostgreSQL type compiles to NUMERIC. The exact tuples for `100.000000000000000001`, `12345678901234567890.123456789012345678`, and `0.123456789012345678` round-trip unchanged, and over-scale/out-of-range/float input is rejected.
5. Initial watchlist contains vendor-neutral securities for AVGO, VRT, and HK.09698; unverified metadata is null/unavailable.
6. `POST /api/v1/securities` normalizes and creates a unique `USER_SUPPLIED_UNVERIFIED`/`UNVERIFIED` record with no mapping/calendar/trading rules; it can be added to the watchlist but cannot enter strategy/order flows. Default watchlist add/remove remains idempotent and preserves security history.
7. `GET /health` and the Phase 1 `/api/v1` routes match `API_CONTRACTS.md`; error responses use the stable Problem model.
8. Portfolio/positions/performance show opening/empty truth: zero positions means unrealized P&L exactly zero; with only one NAV point daily/weekly/monthly returns are unavailable while since-inception return/drawdown are zero. Provider capability remains separately unavailable and no values are synthetic.
9. Broker/provider registries are independently selectable and descriptor reads make no connection attempt.
10. OpenAPI contains no path segment or operation for live orders, live kill switch, paper orders/deposit/withdraw/FX, fills, strategy run/signals/scores/indicators, broker accounts, or backtests.
11. Core import-boundary tests prove it does not import database, backend, integrations, FastAPI, SQLAlchemy, or any broker SDK.
12. The application starts and renders the minimal local read-only dashboard while every external provider is offline/unconfigured.
13. pytest, Ruff check/format check, and mypy all pass with the exact results recorded.
14. `.env`, databases, logs, caches, secrets, account IDs/exports and credentials are ignored/not tracked; a tracked-file scan finds no obvious secret or broker SDK.
15. Git diff contains only Phase 1 planned files and approved documentation updates; unrelated changes are intact.
16. Snapshot quality, score coverage, data availability, and capability statuses use separate
    taxonomies; the inception snapshot/API point is `COMPLETE`.
17. UTC-aware offset round trips preserve the instant, naive persistence is rejected, and all
    signed-zero forms become positive zero.
18. Frontend rendering uses DOM nodes and `textContent`, never user-controlled HTML sinks.

## 6. Test plan

### 6.1 Unit

- configuration rejects `AUTO_EXECUTION=true`, non-loopback bind, invalid currency/mode/provider key;
- Decimal constructors reject floats, NaN/infinity, excessive scale/range and JSON numeric financial input;
- `ExactDecimal` canonical SQLite strings and PostgreSQL NUMERIC compilation satisfy the dialect contract;
- domain IDs/enums/canonical models reject vendor/ORM leakage and invalid order combinations;
- capability statuses distinguish unsupported/not implemented/unavailable;
- four registries have independent namespaces, reject duplicate keys, and return truthful unknown/unimplemented descriptors;
- no descriptor resolution instantiates/connects an adapter.

### 6.2 Architecture

- AST/import scan forbids core dependencies on backend/database/integrations/vendor/FastAPI/SQLAlchemy;
- no `futu`, OpenD, socket/client, order submission, background/distributed-infrastructure import appears;
- presentation schemas map from canonical values and do not import ORM objects into API output.

### 6.3 Migration/database integration

- empty upgrade to head, current revision, downgrade/upgrade on temporary DB where safe;
- required Phase 1 tables, FKs, uniques, checks, indexes, append-only guards;
- exact SQLite TEXT round trips for `100.000000000000000001`, `12345678901234567890.123456789012345678`, and `0.123456789012345678`, including identical Decimal tuples and `typeof=text`;
- negative/zero/positive/large Decimal ordering in Python, plus scale/range/float rejection; tests must demonstrate lexical TEXT order is not used as numeric order;
- balanced opening ledger via Python Decimal UoW, atomic rejection of imbalance, no TEXT `SUM`/numeric `CAST`, and update/delete rejection for posted facts;
- seed twice creates no duplicates and never resets user-created watchlist membership.
- later ORM tables cannot change revision 0001; every nullable logical uniqueness rule and the
  cash-flow snapshot FK are tested adversarially;
- seed name/capital/currency/date/timezone drift fails atomically, and offset-aware timestamps
  round-trip as UTC;
- invalid ledger directions/IDs/numbers/amounts/FX/currency/account scope fail before any write.

### 6.4 API/application integration

- exact portfolio/inception/performance/empty-position models and decimal strings;
- security create normalization, duplicate conflict, forced unverified/tradability status, unavailable provider/trading metadata, and fail-closed strategy/order prerequisites;
- add same watchlist item gets 201 then 200; delete twice gets 204; invalid/disabled/unknown cases;
- missing fields are null plus status, never zero/fake;
- known economic zero remains zero (zero-position unrealized P&L), while capability availability is a separate field;
- problem/error content type, code, field errors and request ID;
- OpenAPI allowlist/denylist, including no `/live` and no financial mutation routes;
- normalized security/watchlist integrity races return stable 409/idempotent responses;
- frontend source scanning rejects user-controlled `innerHTML`, `outerHTML`, and adjacent-HTML
  sinks.
- status endpoints return unavailable descriptors without connection calls;
- UoW rollback leaves no partial writes.

### 6.5 Startup/UI smoke

- startup with no `.env`, no OpenD, no SDK, and no network;
- health/read-only dashboard load using a migrated temp DB;
- UI text clearly labels PaperBroker/Futu/data/fundamental/event as unavailable/not implemented and contains no buy/sell/live controls.

## 7. Exact validation commands

Run from repository root in PowerShell. Use the virtual-environment Python explicitly after creation.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m pytest -ra
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src tests
git status --short --branch
git diff --check
git diff --stat
```

Startup validation (bounded/manual separate terminal, never left running silently):

```powershell
.\.venv\Scripts\python.exe -m uvicorn ai_infra_quant.backend.main:app --host 127.0.0.1 --port 8000
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-WebRequest http://127.0.0.1:8000/openapi.json
```

The report records exit code/pass count/tool version and any external blocker. Do not claim a check was run if it was not. Dependency installation/network approval follows the environment's normal permission process; failure is reported rather than bypassed.

## 8. Explicitly out of scope

- AIInfraStrategy calculations, indicators, score, coverage, confirmation, veto, state transitions, sizing, or recommendations;
- approval/freeze of the proposed strategy or selection of OD-006 sizing; `APPROVE STRATEGY SPEC V1` remains separately required;
- PaperBroker behavior; deposit, withdrawal, FX, reservation, settlement, order, fill, position, P&L mutation, or paper trading UI;
- any automatic/manual paper fill or paper market/limit matching;
- any market, benchmark, fundamental, valuation, event, news, corporate-action, or FX data import/fetch;
- any Futu SDK/dependency/import, OpenD connection, socket probe, account discovery, credentials, reconciliation, or adapter implementation;
- EastMoney adapter or undocumented endpoint/UI automation;
- Backtest engine, simulator, fees/slippage execution, benchmarks, or historical run;
- functional or disabled live routes/handlers, order approval, broker submission, kill switch, authentication/authorization/CSRF, live mode, or autonomous execution;
- microservices, Kafka, Redis, Celery, Kubernetes, task queue, distributed cache/event bus, multi-tenant support;
- broker SDK installation, paper/live orders, GitHub push, remote changes, global Git configuration, deployment, cloud/public hosting;
- modification of `AGENTS.md` or `docs/MASTER_SPEC.md` without a separate explicit requirement decision.

## 9. Phase completion report and stop condition

Report:

- before/after repository status and unrelated changes preserved;
- exact files created/changed and deviations from this list;
- requirements completed and matrix rows updated with actual evidence;
- migration/startup/API/test/Ruff/mypy commands with exact outcomes;
- provider/broker availability (expected unavailable/not implemented) and any external blockers;
- known limitations and decisions still due for later phases;
- confirmation that no broker SDK, OpenD connection, paper/live order, live route, push/remote/global-config change occurred.

Then stop. Do not begin Phase 2. Wait for the exact instruction `APPROVE PHASE 2`.

## 10. Implementation evidence

The exact `APPROVE PHASE 1` instruction was received. The implementation stayed within this
plan and produced the planned package, migration, API/dashboard, and test files. Local evidence:

- remediation began from the reported uncommitted Phase 1 working tree; unrelated prior changes
  were preserved;
- CPython 3.12.13 virtual environment with only the pinned foundation/development dependencies;
- fresh SQLite upgrade/current: `0001_phase1_foundation (head)`;
- actual loopback Uvicorn startup; `/health`, `/openapi.json`, and `/` returned 200;
- full remediation pytest result: `111 passed`;
- Ruff check/format and mypy: passed;
- exact SQLite Decimal tuple round trips with physical `text` storage and PostgreSQL
  `NUMERIC(38,18)` compilation;
- migration isolation, partial uniqueness/FK/check/append-only triggers, Python-Decimal UoW,
  idempotent and drift-safe seed, UTC/signed-zero, security/race fail-closed behavior, frontend
  injection safety, API allowlist/denylist, offline startup, no-connection descriptor, and
  architecture-boundary tests: passed.

No strategy formula, position sizing, PaperBroker execution, order/fill, external provider call,
Futu/OpenD integration, live route, commit, push, remote change, or global Git change occurred.
