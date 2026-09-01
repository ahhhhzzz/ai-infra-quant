# TASK-004_MARKET_DATA_BACKEND

**Task ID:** TASK-004_MARKET_DATA_BACKEND  
**Status:** APPROVED_FOR_IMPLEMENTATION  
**Baseline commit:** `67adf07b3439ecf92ff5fc503952dcfecd0e6396`  
**Target base branch:** `roadmap/no-live-trading`  
**Task branch:** `task/TASK-004_MARKET_DATA_BACKEND`

## 1. Goal

Turn the accepted TASK-003 Futu quote-only PoC into the first application-facing Phase 2 Market Data Backend.

The local FastAPI application must expose provider-neutral read-only market data for:

```text
US.AVGO
US.VRT
HK.09698
```

Required backend capabilities:

- latest quote;
- market status;
- completed daily OHLCV;
- current-session completed 1-minute OHLCV;
- provider/data status;
- market/source timestamps;
- truthful unavailable/error handling.

TASK-004 is a backend integration task. It is not a Dashboard task and not a Composite Quant Score task.

## 2. Authoritative boundary

Decision `MTF-001` remains authoritative.

Futu OpenD is the approved first Market Data Provider and remains quote-only.

Allowed capability:

```text
OpenQuoteContext
latest quote
market state
daily K-line
1-minute K-line
quote capability/status
```

Permanently forbidden:

```text
OpenSecTradeContext
OpenFutureTradeContext
account access
cash
positions
orders
fills
real trades
unlock_trade
place_order
cancel_order
modify_order
broker synchronization
broker reconciliation
```

No API route introduced by this task may expose brokerage-account concepts.

## 3. Historical boundary

Preserve without reinterpretation:

- Phase 0 historical completion;
- Phase 1 PASS and implementation;
- Phase 1 migrations;
- Phase 1 plan;
- both immutable Phase 1 reviews;
- TASK-002 / `MTF-001`;
- TASK-003 quote-only implementation and remediation.

Do not rewrite historical evidence.

## 4. Provider configuration

Application configuration may officially support:

```text
MARKET_DATA_PROVIDER=none
MARKET_DATA_PROVIDER=futu
```

The default remains safe/offline:

```text
MARKET_DATA_PROVIDER=none
```

When `MARKET_DATA_PROVIDER=futu`, the backend uses the existing Futu quote-only adapter.

OpenD configuration remains:

```text
FUTU_OPEND_HOST=127.0.0.1
FUTU_OPEND_PORT=11111
```

`FUTU_OPEND_HOST` must remain loopback-only.

The application must never contain or require:

```text
Futu username
Futu password
trade password
account ID
broker token
```

OpenD authentication remains external to the application.

The FastAPI process must still start when:

- OpenD is not running;
- the optional Futu dependency is missing;
- `MARKET_DATA_PROVIDER=none`.

Provider failure must not crash application startup.

## 5. Application/service boundary

Introduce a small provider-neutral Market Data application service/query layer.

Conceptually:

```text
FastAPI
  -> MarketDataService / queries
      -> provider-neutral market-data port
          -> FutuQuoteAdapter
              -> local OpenD
```

Futu SDK, pandas/DataFrame values, and provider-native enums must not escape `integrations/`.

Core/application/backend code consumes canonical market-data objects only.

Do not build a generic plugin framework. Only provider modes `none` and `futu` are required.

## 6. Security resolution

Market-data routes operate on existing canonical platform Securities.

Use existing `security_id` as the primary API identity.

Do not create a second Security registry.

The initial Futu mappings remain exactly:

```text
US.AVGO
US.VRT
HK.09698
```

A nonexistent Security returns a stable not-found response.

A valid platform Security that is not supported by the approved Futu mapping must return an explicit unsupported status/error. Do not silently construct a Futu symbol.

## 7. Approved API surface

TASK-004 may register exactly these market-data route groups.

### 7.1 Current market state

```text
GET /api/v1/market-data/securities/{security_id}/state
```

Return provider-neutral state containing at minimum:

```text
security_id
market
symbol
currency
provider
latest_price
latest_quote_at
market_state
provider_market_state
retrieved_at
provider_delay_seconds when truthfully known
quote_status
market_status
reason/error where applicable
```

Never call `latest_price` a closing price.

### 7.2 Completed daily bars

```text
GET /api/v1/market-data/securities/{security_id}/daily-bars
```

Support a `limit` query parameter with:

```text
default = 120
maximum = 260
```

The backend/provider layer may request a sufficient calendar range to return the requested number of completed trading sessions.

Response includes at minimum:

```text
security_id
provider
status
retrieved_at
latest_completed_daily_session
bars[]
```

Each bar contains:

```text
session_date
open
high
low
close
volume
provider/source time
is_completed = true
```

Financial values serialize as Decimal strings.

The TASK-003 remediation rule is mandatory:

> A current market-local daily bar is completed only when provider market state gives sufficient authoritative evidence that the regular session is closed.

Do not regress to UTC-calendar-date completion inference.

### 7.3 Current-session completed 1-minute bars

```text
GET /api/v1/market-data/securities/{security_id}/minute-bars
```

TASK-004 supports only:

```text
interval = 1 minute
current trading session/day
completed bars only
```

Response includes at minimum:

```text
security_id
provider
status
session_date
retrieved_at
latest_completed_minute_bar_at
bars[]
```

Each bar contains:

```text
interval_start
interval_end
open
high
low
close
volume
is_completed = true
```

The unfinished current minute must remain excluded.

Do not add 5m/15m persistence, ticks, order books, historical minute replay, streaming, or WebSockets.

## 8. Provider failure semantics

Expected provider conditions must return structured, truthful status rather than crash the process.

Preserve existing taxonomy where applicable:

```text
AVAILABLE
DELAYED
STALE
MISSING
UNAVAILABLE
NOT_ENTITLED
PROVIDER_ERROR
NOT_SUPPORTED
INVALID
```

Do not fabricate `DELAYED` or `STALE` from arbitrary thresholds.

If actual provider delay cannot be established truthfully, `provider_delay_seconds = null` is correct.

Individual capabilities may fail independently. A partial response such as the following must remain representable:

```text
latest        AVAILABLE
market_state  AVAILABLE
daily         AVAILABLE
1m            UNAVAILABLE
```

## 9. HTTP behavior

Market-data responses use:

```text
Cache-Control: no-store
```

Expected external-data unavailability must not become an unhandled HTTP 500.

Stable HTTP errors remain appropriate for protocol/resource errors such as:

```text
404  Security does not exist
422  unsupported canonical Security / malformed request
```

Provider/OpenD failures expose safe reasons without stack traces, credentials, private account data, or raw provider payloads.

## 10. Persistence decision

TASK-004 creates no market-data migration and no production market-data persistence.

Do not implement persistent:

```text
market_quotes
market_daily_bars
market_minute_bars
```

The backend is a read-through service over Futu OpenD.

Rationale:

- current priority is a usable product;
- TASK-005 needs a stable API, not a historical warehouse;
- latest quotes do not need permanent 60-second storage;
- minute retention policy remains unapproved;
- backtest/research persistence requirements are not yet frozen.

The logical records in `docs/DATABASE_SCHEMA.md` remain future design, not current tables.

Do not add a migration merely because the logical schema describes future records.

## 11. Connection lifecycle

Keep provider connection behavior simple.

Do not add:

```text
background worker
always-on subscription
WebSocket
persistent streaming connection
scheduler
thread-pool architecture
```

A request may establish/use a quote context through the provider boundary and must close it cleanly.

Do not create a 24/7 OpenD polling process.

## 12. No frontend polling yet

TASK-004 prepares endpoints for future 60-second polling.

It does not implement:

```text
setInterval
60-second browser refresh
countdown timer
visibility pause
manual refresh button
candlestick chart
security selector UI
```

These belong to TASK-005.

## 13. Explicit non-goals

Do not implement:

```text
Dashboard UI
candlestick rendering
Composite Quant Score
Daily Base Score
Intraday Minute Adjustment
ranking
risk/reference model
PaperOrder/PaperFill
accounting expansion
backtesting
market-data DB persistence
background polling
WebSocket
streaming
tick storage
order book
full minute history
second market-data provider
broker account integration
real portfolio tracking
live trading
TASK-005
```

## 14. Existing TASK-003 behavior that must remain

Do not regress:

```text
Decimal canonicalization
aware UTC
market-local session semantics
HK daily completion remediation
unfinished 1m exclusion
latest price != daily close
explicit provider statuses
clean quote-context close
loopback-only OpenD
lazy optional Futu SDK loading
quote-only safety boundary
```

## 15. Tests

Automated tests must not require live OpenD. Use fake/mock provider boundaries.

At minimum cover:

1. new API routes exist;
2. existing Phase 1 routes continue working;
3. Security resolution uses existing canonical Security;
4. unsupported Security is explicit;
5. latest values serialize as Decimal strings;
6. timestamps are aware/ISO-8601 UTC;
7. state route distinguishes latest price from daily close;
8. daily bars expose only completed sessions;
9. HK current-session daily completion remediation remains correct;
10. completed 1m bars only;
11. unfinished 1m bar remains excluded;
12. provider unavailable is structured;
13. `NOT_ENTITLED` is structured;
14. partial provider capability failure does not crash unrelated capability;
15. Futu SDK objects do not leak to API responses;
16. FastAPI starts without live OpenD;
17. FastAPI starts with provider `none`;
18. optional Futu dependency is lazy;
19. `Cache-Control: no-store` is present;
20. no Futu Trade Context/write capability appears.

Continue the forbidden-symbol architecture scan for:

```text
OpenSecTradeContext
OpenFutureTradeContext
place_order
cancel_order
modify_order
unlock_trade
```

## 16. Runtime smoke

When OpenD is available locally, run a real smoke against the FastAPI backend for:

```text
US.AVGO
US.VRT
HK.09698
```

Verify, as available by current market state:

```text
state
daily-bars
minute-bars
```

US/HK markets may be closed, pre-market, or between sessions. Empty current-session 1m data must be interpreted truthfully.

Do not fabricate `AVAILABLE`.

If OpenD is unavailable in Codex's execution environment, offline automated acceptance may still pass and live backend verification remains a local follow-up.

## 17. Expected change scope

Likely files include only what is necessary, such as:

```text
.env.example
README.md
src/ai_infra_quant/config.py
src/ai_infra_quant/core/domain/market_data.py
src/ai_infra_quant/application/market_data_queries.py
src/ai_infra_quant/backend/dependencies.py
src/ai_infra_quant/backend/main.py
src/ai_infra_quant/backend/api/v1/**
src/ai_infra_quant/backend/schemas/**
src/ai_infra_quant/integrations/futu_quote/adapter.py
tests/**
docs/API_CONTRACTS.md
docs/ARCHITECTURE.md
docs/MASTER_SPEC.md
docs/REQUIREMENTS_MATRIX.md
docs/ROADMAP.md
```

Modify only what is actually necessary.

## 18. Forbidden changes

Do not modify:

```text
docs/reviews/PHASE_1_INDEPENDENT_REVIEW.md
docs/reviews/PHASE_1_POST_REMEDIATION_REVIEW.md
docs/phases/PHASE_1_PLAN.md
src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py
```

Do not create a new migration in TASK-004.

Do not modify, delete, stage, or commit local untracked:

```text
phase1_remediation_commit.txt
```

## 19. Acceptance criteria

TASK-004 passes only if:

1. Futu quote-only integration is available through FastAPI;
2. all three approved market-data route groups exist;
3. AVGO/VRT/HK.09698 resolve through canonical Security identity;
4. latest quote/status are provider-neutral;
5. completed daily bars are exposed;
6. completed current-session 1m bars are exposed;
7. unfinished 1m bars are excluded;
8. daily completion uses market-local/provider-state semantics;
9. Decimal and UTC invariants remain;
10. provider failure/entitlement states are explicit;
11. no Futu SDK object leaks through API;
12. app startup does not require OpenD;
13. app startup does not require the optional Futu extra unless Futu is invoked;
14. no brokerage-account access exists;
15. no trade context/write capability exists;
16. no market-data persistence or migration is added;
17. no Dashboard is implemented;
18. no Composite Score/ranking/risk model is implemented;
19. Phase 1 evidence remains untouched;
20. required validation passes.

## 20. Validation

Run at minimum:

```text
pytest -ra
ruff check .
ruff format --check .
mypy src tests
git diff --check
git diff --stat
```

Perform the quote-only forbidden-symbol scan.

Run FastAPI smoke:

```text
GET /health
GET /openapi.json
```

Verify the three new market-data route groups appear in OpenAPI.

If OpenD is reachable, attempt live backend requests.

## 21. Git rules

Work only on:

```text
task/TASK-004_MARKET_DATA_BACKEND
```

Do not modify `master`.
Do not force-push.
Do not amend previous commits.

After implementation and validation, create one implementation commit and push only the task branch.

Do not merge automatically.
Do not begin TASK-005.

## 22. Final report

After push, report:

- branch;
- implementation commit SHA;
- parent SHA;
- tree SHA if available;
- exact changed files;
- test/Ruff/mypy/diff-check results;
- new OpenAPI routes;
- Futu provider architecture summary;
- live OpenD backend result if available;
- confirmation of no Trade Context;
- confirmation of no brokerage-account access;
- confirmation of no migration;
- confirmation of no market-data persistence;
- confirmation of no Dashboard;
- confirmation of no Composite Quant Score;
- confirmation Phase 1 evidence is untouched;
- confirmation `phase1_remediation_commit.txt`, if present, remains untouched and untracked;
- confirmation no force-push occurred and the roadmap branch was not modified.

Then STOP.

Do not begin TASK-005 without explicit approval.
