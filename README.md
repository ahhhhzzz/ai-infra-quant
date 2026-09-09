# AI Infra Quant

AI Infra Quant is a local-first, single-user research and decision-support workbench. It provides
read-only current US/HK market data, active watchlist management and explicit Snapshot-on-Demand
PAQS-E Narrative analysis using one registered model. Optional web research defaults OFF; final
reasoning is tool-free. Exact text and frozen evidence are retained in the Narrative Ledger, with
Legacy structured history kept separately. The app never observes/imports brokerage accounts,
positions or trades, or sends orders. Real trading is manual in the broker's official client.

C1 and C2 are accepted and integrated; current runtime code is
`d2d25efc79d2560a7ed09895c7dd7a2c1724aee9`. ADC-001 documentation consolidation is reviewed and integrated.
006B1 may start under its original bounded scope and the new post-ADC exact-baseline handoff.
See [current architecture](docs/ARCHITECTURE.md), [roadmap/status](docs/ROADMAP.md),
[workbench guide](docs/PAQS_E_WORKBENCH.md) and [model/credential guide](docs/PAQS_E_MODELS.md).

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
application runtime remains SQLite-only. Current migration head is
`0003_task007c1_narrative_ledger`; this is not a local market archive or strict historical replay.

## Validation

```powershell
.\.venv\Scripts\python.exe -m pytest -ra
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src tests
```

These commands are the runtime validation workflow, not ADC execution evidence. Historical test
runs and screenshots remain in their original reports; ADC performs docs-only scope/link checks.
See [requirements traceability](docs/REQUIREMENTS_MATRIX.md) and
[architecture history](docs/ARCHITECTURE.md#9-historical-evolution-and-evidence).

## Models, credentials and analysis history

Select a model and open **配置此模型 API Key**. The local password form submits its key to Windows
Credential Manager; status reads never return it. UI-managed keys require no `.env` write.
Stored service slots are shared by models using that service; OpenAI alone has an optional existing
read-only environment fallback. Presence is not connectivity, balance or permission verification.

Research must be explicitly enabled and resets OFF on model changes. Successful Narrative text
has safe formatted and exact raw views; text/hash/lineage do not machine-certify strategy or RR.
C2 repairs the dialog and removes old opening-capital/NAV cards and duplicate administration from
the normal UI. Historical data, seed, compatibility APIs and migrations 0001/0002/0003 remain.
No Paper/PnL, backtest, PAQS-Q successor, broker or automatic analysis is activated.

C1 user acceptance and C2 review/closeout attribution are linked from [ROADMAP](docs/ROADMAP.md).
The C2 user's screenshot showed C1 branch without SHA; it is not independent exact-C2 runtime proof.
