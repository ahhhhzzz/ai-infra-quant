# AI Infra Quant

AI Infra Quant is a local-first, single-user, read-only quantitative research and investment
decision-support tool. Its authoritative future direction is defined in `docs/ROADMAP.md`: daily
plus recent completed 1-minute market data, a market Dashboard, dynamic supported US/HK equities,
and an incremental PAQS decision-terminal workstream. Daily and 1-minute charts remain separate.

TASK-003 established a bounded Futu OpenD proof of concept using quote-market-data APIs only.
TASK-004 exposes that provider through three provider-neutral, read-through FastAPI endpoints for
market state, completed daily bars, and completed 1-minute bars. TASK-005 adds the local,
market-first Dashboard on top of those endpoints. TASK-005B expands its bounded chart history to
approximately five trading years of Daily K and 30 market-local calendar days of minute K. It does
not connect to brokerage-account state. TASK-006A adds provider-validated US/HK equity addition,
trading-calendar mapping, and provider-agnostic completed W1/D1/regular-session M30 input
preparation. It adds no PAQS structure or advisory logic. The application never reads real-account
facts, imports or reconciles real trades, or sends a broker command. The user performs every real
trade manually in the broker's official client.

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

Open `http://127.0.0.1:8000`. With the safe default `MARKET_DATA_PROVIDER=none`, external provider
calls remain disabled; the paper broker is only a non-operational historical descriptor.

The homepage uses the canonical Watchlist to select the original AVGO, VRT, or HK.09698 entries or
another provider-validated US/HK equity. Enter only market and symbol under **Add US/HK stock**;
validation happens before any local mutation. A successful add immediately refreshes and selects
the security. The Dashboard shows latest price,
market state, separate completed daily and recent 1-minute candlestick/volume views, provider
timestamps/status, manual refresh, and a non-overlapping 60-second visible-page refresh cycle. A
full Security load requests up to 1300 completed Daily bars and 30 calendar days of minute bars;
ordinary refreshes request only five Daily bars and two minute-history days, then deduplicate and
prune the browser caches without resetting the user's viewport. US minute history uses Futu
`Session.ALL` (overnight, pre-market, regular, and after-hours provider bars); HK retains normal HK
sessions. TradingView Lightweight Charts 5.2.1 is vendored under the frontend static assets, so no
runtime CDN or frontend build step is required. Its Apache-2.0 license, NOTICE, and visible
TradingView attribution are preserved with the vendored asset.

To run the optional quote-only Futu backend against an already configured local OpenD:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,futu]"
$env:MARKET_DATA_PROVIDER = "futu"
.\.venv\Scripts\python.exe -m uvicorn ai_infra_quant.backend.main:app --host 127.0.0.1 --port 8000
```

`FUTU_OPEND_HOST` and `FUTU_OPEND_PORT` default to `127.0.0.1:11111`. OpenD login and quote
entitlements are external prerequisites; no credential belongs in this app. The safe default
`MARKET_DATA_PROVIDER=none` keeps the endpoints available with structured `UNAVAILABLE` results.

## Windows one-click Dashboard

After completing the local setup, double-click `start_dashboard.bat` in the repository root. It
reuses an already-running OpenD and reuses a healthy FastAPI instance only when its startup-captured
source revision exactly matches the current Git checkout. A stale/missing/invalid backend revision
fails safely and asks you to close/restart the existing dashboard process; it never kills it.
It starts OpenD as needed and waits for `127.0.0.1:11111`. When the application port is free,
it starts FastAPI with the Futu market-data provider in a separate visible
console, waits for `/health`, and then opens `http://127.0.0.1:8000` in the default browser.

The launcher checks common Futu OpenD installation locations. If it cannot find the executable,
configure its path once and launch the batch file again:

```bat
setx FUTU_OPEND_EXE "C:\path\to\Futu_OpenD.exe"
```

OpenD login and quote entitlements remain external and manual; the launcher never handles
credentials. FastAPI logs remain visible in the separate server console. Stop FastAPI with
`Ctrl+C` in that console or by closing the console window. The launcher may leave OpenD running.

The TASK-004 API surface is:

```text
GET /api/v1/market-data/securities/{security_id}/state
GET /api/v1/market-data/securities/{security_id}/daily-bars?limit=1300
GET /api/v1/market-data/securities/{security_id}/minute-bars?lookback_days=30
```

TASK-006A adds:

```text
POST /api/v1/watchlist/supported-securities
GET  /api/v1/strategies/paqs/securities/{security_id}/input-status
```

The second route reports input counts, timestamps, calendar/adjustment metadata, quality, and
warnings only. It contains no structure, setup, advisory, target, risk/reward, or score. See the
[PAQS user guide](docs/user/PAQS_USER_GUIDE.md) and
[PAQS engineering guide](docs/engineering/PAQS_ENGINEERING_GUIDE.md).

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

Phase 1 remains intentionally limited and has passed independent review. TASK-004 adds the first
Phase 2 market-data backend, TASK-005 adds its read-only Dashboard client, TASK-005B adds bounded
paged chart history/incremental refresh, and TASK-006A adds only the dynamic-security and PAQS input
foundation. No derived-input persistence, PAQS structure/advisory, PaperBroker, paper fill/order,
backtest, brokerage-account access, or real-order route was added.


TASK-007C1 adds a flat eleven-model selector and local **配置此模型 API Key** dialog.
Use the existing Windows launcher, open the loopback workbench, select a model, securely save its
key and explicitly Analyze. UI-managed keys need no `.env` edit. See
[model and credential guide](docs/PAQS_E_MODELS.md) for supported routes, research limits and
the user acceptance recorded in [C1 closeout](docs/decisions/TASK_007C1_CLOSEOUT_2026_09_08.md).
TASK-007A/B/C and user-accepted TASK-007C1 are integrated; the authoritative integration is
`2cc4eeea3cc31d4fd1f1a4e9c1fbec237f82a2c4`. TASK-007C2 repairs this dialog and removes obsolete
initial-account administration from the normal UI, preserving data and all accepted analysis behavior.
C2 is implemented pending independent review, with no C2 merge. See the
[implementation report](docs/reports/TASK_007C2_IMPLEMENTATION_REPORT.md).
