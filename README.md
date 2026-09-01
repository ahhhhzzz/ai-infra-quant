# AI Infra Quant

AI Infra Quant is a local-first, single-user, read-only quantitative research and investment
decision-support tool. Its authoritative future direction is defined in `docs/ROADMAP.md`: daily
plus current-session completed 1-minute market data, a broker-style dashboard, approximately
60-second refresh/recalculation, and a dual-timeframe Composite Quant Score. Daily and 1-minute
charts are separate views.

TASK-003 adds a bounded Futu OpenD proof of concept using quote-market-data APIs only. It does not
register an application route or connect to brokerage-account state. The application never reads
real-account facts, imports or reconciles real trades, or sends a broker command. The user performs
every real trade manually in the broker's official client.

The accepted Phase 1 implementation is the local FastAPI/SQLite foundation. It exposes opening
portfolio facts, identity/watchlist administration, and truthful provider capability descriptors;
it does not fetch external data or implement later-phase portfolio behavior.

## Local setup

CPython 3.12 is required. The pinned `tzdata` package supplies the IANA database on hosts such
as Windows that do not provide it to Python's `zoneinfo` module.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn ai_infra_quant.backend.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. All external providers remain unavailable and the paper broker
is only a non-operational descriptor in Phase 1.

To run the optional quote-only Futu PoC against an already configured local OpenD:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,futu]"
.\.venv\Scripts\python.exe -m ai_infra_quant.integrations.futu_quote.poc
```

`FUTU_OPEND_HOST` and `FUTU_OPEND_PORT` default to `127.0.0.1:11111`. The runner reports
`LIVE_POC_BLOCKED` without attempting an SDK connection when that TCP endpoint is unreachable.
OpenD login and quote entitlements are external prerequisites; no credential belongs in this app.

Alembic selects its database URL in this order: an explicit
`-x database_url=...` override, `DATABASE_URL` from application settings or `.env`, then the
application's default SQLite URL. PostgreSQL overrides are for migration verification only;
Phase 1 application runtime remains SQLite-only.

## Validation

```powershell
.\.venv\Scripts\python.exe -m pytest -ra
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src tests
```

Phase 1 implementation evidence is recorded in `docs/REQUIREMENTS_MATRIX.md` after the final
validation run.

## Phase 1 evidence

Local validation on 2026-08-31 used CPython 3.12.13 and the exact dependencies pinned in
`pyproject.toml`.

- Alembic upgraded a fresh SQLite database and reported `0001_phase1_foundation (head)`.
- Uvicorn started on `127.0.0.1`; `/health`, `/openapi.json`, and `/` returned 200.
- The complete Phase 1 remediation suite passed: `111 passed`.
- `ruff check .`, `ruff format --check .`, and `mypy src tests` passed.
- SQLite returned the three required Decimal vectors with identical tuples and
  `typeof(value) = 'text'`; PostgreSQL compilation returned `NUMERIC(38,18)`.
- Architecture tests prove core/application dependency boundaries and the absence of future
  route modules.
- Migration isolation, security-identity, UTC, signed-zero, seed-drift, database uniqueness,
  trigger, race-conflict, and frontend injection-safety adversarial tests passed.

Revision `0001_phase1_foundation` is an explicit historical schema: it does not consult current
ORM metadata. A local development database created by the earlier metadata-driven draft must be
recreated before running this remediated revision. The application never deletes a database.

Phase 1 remains intentionally limited and has passed independent review. TASK-003 is the first
bounded Phase 2 integration PoC; no PaperBroker, paper fill/order, market-data API/dashboard,
strategy calculation, backtest, or real-order route was added.
