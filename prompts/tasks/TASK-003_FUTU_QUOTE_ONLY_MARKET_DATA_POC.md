# TASK-003_FUTU_QUOTE_ONLY_MARKET_DATA_POC

**Task ID:** TASK-003_FUTU_QUOTE_ONLY_MARKET_DATA_POC  
**Status:** APPROVED_FOR_IMPLEMENTATION  
**Baseline commit:** `c0df2fedc1679541e0ccdd408a259b8dabc64f0a`  
**Target base branch:** `roadmap/no-live-trading`  
**Task branch:** `task/TASK-003_FUTU_QUOTE_ONLY_MARKET_DATA_POC`

## 1. Goal

Implement the first concrete Phase 2 market-data proof of concept using **Futu OpenAPI/OpenD in quote-only mode**.

The task must prove, truthfully and with explicit capability/error reporting, whether the configured local Futu OpenD environment can provide the required market data for:

```text
US.AVGO
US.VRT
HK.09698
```

Required data capabilities:

- latest price / quote state;
- market status;
- daily OHLCV;
- current trading day's completed 1-minute OHLCV;
- source/retrieval timestamps;
- entitlement/permission, delay/staleness, unavailable, and provider-error states.

This task is a **market-data integration PoC**, not a Dashboard task and not a Composite Score task.

## 2. Authoritative product boundary

Decision `MTF-001` remains authoritative.

Futu is used only as a market-data provider. The application must not access any brokerage-account state.

Allowed Futu capability:

```text
OpenQuoteContext / quote-market-data APIs only
```

Permanently forbidden in this task and future product scope:

```text
OpenSecTradeContext
OpenFutureTradeContext
trade unlock
account discovery for trading
broker cash
broker positions
broker orders
broker fills/trades
place_order
cancel_order
modify_order
broker reconciliation
real-trade import/sync
```

Do not weaken this boundary because Futu also operates a brokerage business.

No code path in the PoC may instantiate or call a Futu trade context.

## 3. Historical boundary

Preserve without reinterpretation:

- Phase 0 historical completion;
- Phase 1 implementation and PASS status;
- both immutable Phase 1 review files;
- TASK-002 / `MTF-001` documentation baseline.

Do not rewrite Phase 1 history or begin unrelated Phase 2 features.

## 4. Scope

### 4.1 Futu quote-only adapter

Add a small provider-specific adapter under the existing `integrations/` boundary.

The adapter must remain isolated from Strategy, Portfolio, Accounting, Risk, Performance, and Backtest.

Use the official Futu Python OpenAPI package and **quote context only**.

The adapter should expose a minimal provider-facing capability sufficient for this PoC, equivalent to:

```text
latest quote / snapshot
market status
completed daily bars
completed current-session 1-minute bars
provider/capability status
```

Do not build a large generic plugin framework.

Do not design abstractions beyond what is needed to keep Futu-specific SDK objects out of core/application-facing canonical data.

### 4.2 Configuration

OpenD connection settings must be configuration-driven and non-secret, for example host/port with safe local defaults where appropriate.

No Futu account password, trade password, token, account ID, private export, or other credential may be committed.

If authentication/login must be completed in OpenD itself, the application must treat OpenD as an external local prerequisite rather than embedding user credentials.

Update `.env.example` only if needed for safe non-secret OpenD connection settings.

### 4.3 Initial securities

PoC coverage is exactly:

```text
US.AVGO
US.VRT
HK.09698
```

Use canonical platform Security identity. Provider symbol mapping must remain explicit and provider-specific.

Do not hard-code these symbols deep inside reusable provider logic; they may be defaults/fixtures for the PoC runner.

### 4.4 Latest quote

For each initial security, attempt to obtain a latest quote/snapshot using the quote-only API.

Canonical PoC output must distinguish at minimum:

```text
security
price
currency when legitimately available
latest_quote_at
retrieved_at
provider
availability/status
provider delay/latency when it can be determined truthfully
reason/error when unavailable
```

Do not label an intraday/latest price as a final daily close.

### 4.5 Market status

Obtain the market/session status through a quote-only Futu capability when available.

Return provider-neutral status plus the original/provider status or explanatory detail where useful.

Do not infer `OPEN` solely from wall-clock time when the provider supplies an authoritative state.

If exact canonical market-state mapping remains ambiguous, preserve the raw provider state safely and report the canonical result as `UNKNOWN` rather than fabricating certainty.

### 4.6 Daily OHLCV

For each initial security, request daily K-line/OHLCV data sufficient to prove daily-bar access.

The PoC does not need to ingest full long-term history into production persistence.

Daily-bar output must preserve:

- Security;
- completed session date/time;
- Decimal OHLCV where applicable;
- source/provider;
- retrieval time;
- availability/quality status.

Do not claim an incomplete current daily bar is a completed daily session.

### 4.7 Current-session completed 1-minute OHLCV

For each initial security, request 1-minute K-line data for the current trading session/day where available.

Only **completed** 1-minute bars may be exposed as completed PoC output.

The adapter must conservatively exclude an unfinished current minute.

Canonical minute-bar output must preserve at minimum:

```text
security
interval_start
interval_end
open
high
low
close
volume
is_completed
source/provider
retrieved_at
```

Do not implement tick storage, order-book storage, streaming, WebSocket handling, or full historical minute replay.

### 4.8 Decimal and time semantics

Financial market values entering canonical application data use `Decimal`, not binary float.

Provider-native numeric representations may be parsed at the integration boundary but must not leak as financial floats into canonical domain/application data.

All instants exposed to application-facing code are timezone-aware. Preserve market-local session semantics and convert instants to canonical UTC where appropriate.

The PoC must not conflate:

```text
latest_quote_at
latest_completed_minute_bar_at
latest_completed_daily_session
retrieved_at
provider delay
```

### 4.9 Provider status and truthful failure

Futu/OpenD availability and market-data entitlements are environmental facts.

The implementation must handle at least:

- OpenD unavailable / connection refused;
- provider/API failure;
- missing quote entitlement or unsupported data right;
- empty provider result;
- malformed/invalid provider response;
- one security failing while others succeed.

Do not fabricate data to make the PoC pass.

The process should return a structured result per security/capability instead of collapsing every partial failure into an unhandled exception.

## 5. PoC runner / smoke path

Provide a simple local executable smoke path, script, or module entry point that a developer can run against a locally running OpenD.

It must attempt the required capabilities for all three initial securities and print or write a concise machine-readable or clearly structured report.

The report should make it easy to determine:

```text
AVGO      latest / daily / 1m / market-status
VRT       latest / daily / 1m / market-status
HK.09698  latest / daily / 1m / market-status
```

For each capability report one of the truthful outcomes such as:

```text
AVAILABLE
DELAYED
STALE
UNAVAILABLE
NOT_ENTITLED
PROVIDER_ERROR
INVALID
```

Exact enum naming may follow existing project conventions where appropriate; do not create unnecessary parallel taxonomies.

The smoke path must close the quote context cleanly.

## 6. Dependency and packaging rules

Add the official Futu Python API dependency in the least invasive way appropriate to the current packaging structure.

Prefer keeping provider-specific dependency optional if the existing project structure supports a clean optional extra without overengineering.

Do not add unrelated market-data libraries or a second provider.

Do not add a trading SDK abstraction.

## 7. Tests

Add focused tests for the new integration boundary without requiring live OpenD for the normal test suite.

At minimum test:

1. provider SDK objects do not escape canonical outputs;
2. financial values are converted to Decimal correctly;
3. canonical US/HK symbol mapping for AVGO, VRT, HK.09698;
4. unfinished 1-minute bar is excluded from completed output;
5. latest price is not represented as final daily close;
6. provider partial/empty/error responses become explicit status/reason;
7. quote context is closed on success and failure;
8. no trade context or trade-operation symbol is imported/called by the new Futu provider code;
9. existing Phase 1 behavior remains intact.

Use mocks/fakes at the Futu SDK boundary for deterministic automated tests.

Do not require network access or a live OpenD instance for the ordinary automated test suite.

## 8. Live PoC attempt

After implementation and automated tests, attempt the real smoke path **only if a local OpenD is reachable and usable in the execution environment**.

If live OpenD is available, report real observed results for the three initial securities, including which capabilities succeeded and any entitlement/delay limitations.

If OpenD is not running, login/authorization is incomplete, or required quote rights are unavailable:

- do not fabricate success;
- do not request or embed user credentials;
- do not broaden scope into installing/configuring a brokerage account;
- report the precise blocking condition as `LIVE_POC_BLOCKED` or an equivalent explicit result;
- the code/tests may still be committed if all offline acceptance criteria pass.

A blocked live check is not evidence that the provider works for the user's entitlements; it remains a follow-up verification item before relying on the provider operationally.

## 9. Explicit non-goals

Do not implement:

- Dashboard UI or chart rendering;
- 60-second frontend polling;
- Composite Quant Score;
- ranking/risk model;
- persistent production market-data ingestion pipeline beyond what the PoC genuinely needs;
- PaperOrder/PaperFill behavior;
- portfolio accounting expansion;
- backtesting;
- WebSocket/streaming;
- tick/order-book data;
- historical minute replay;
- broker account access;
- any live trading functionality;
- another market-data provider.

Do not start TASK-004.

## 10. Allowed change scope

Expected changes may include only what is necessary for this PoC, such as:

```text
pyproject.toml
.env.example                         # only safe OpenD host/port settings if needed
src/ai_infra_quant/integrations/**
src/ai_infra_quant/core/**           # only minimal provider-neutral market-data value/port types if genuinely required
src/ai_infra_quant/application/**    # only minimal PoC orchestration if genuinely required
tests/**                             # focused tests for this task
docs/**                              # only small documentation/evidence updates required by actual behavior
```

Prefer the smallest file set.

Do not modify Phase 1 migrations or immutable reviews.

## 11. Forbidden files / historical evidence

Do not modify:

```text
docs/reviews/PHASE_1_INDEPENDENT_REVIEW.md
docs/reviews/PHASE_1_POST_REMEDIATION_REVIEW.md
docs/phases/PHASE_1_PLAN.md
src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py
```

Do not modify, delete, stage, or commit local untracked:

```text
phase1_remediation_commit.txt
```

## 12. Acceptance criteria

The task passes implementation review only if:

1. Futu integration uses quote-only APIs and never instantiates a trade context.
2. No brokerage-account cash, positions, orders, fills, trades, or account synchronization is implemented.
3. AVGO, VRT, and HK.09698 are the explicit PoC set.
4. Latest quote capability is implemented with truthful status/error handling.
5. Market-status capability is implemented with truthful status/error handling.
6. Daily OHLCV capability is implemented.
7. Current-session completed 1-minute OHLCV capability is implemented.
8. Unfinished minute bars are excluded from completed results.
9. Canonical financial values use Decimal.
10. Canonical times are timezone-aware and required market-time distinctions are preserved.
11. Polling cadence is not invented by the provider PoC and provider delay is not mislabelled.
12. Normal automated tests do not require live Futu/OpenD.
13. Focused Futu adapter tests pass.
14. Existing relevant project tests pass.
15. Ruff and mypy pass for the affected project scope / full project as required by existing project practice.
16. The PoC smoke path exists and closes the quote context cleanly.
17. A live OpenD check is attempted only when reachable; its result is reported truthfully.
18. No Dashboard, Composite Score, paper trading, backtest, or TASK-004 behavior is implemented.
19. Phase 1 reviews, plan, migration 0001, and `phase1_remediation_commit.txt` remain untouched.
20. No secret or private brokerage data is committed.

## 13. Validation

Run at minimum:

```text
pytest -ra
ruff check .
ruff format --check .
mypy src tests
git diff --check
git diff --stat
```

Also perform a targeted source scan proving the new Futu integration contains no trade-context or broker-write capability. The scan should include at least these forbidden concepts:

```text
OpenSecTradeContext
OpenFutureTradeContext
place_order
cancel_order
modify_order
unlock_trade
```

If a forbidden string exists only in a test asserting its absence or in this immutable Task Contract, classify it explicitly rather than treating the scan mechanically.

## 14. Git rules

Work only on:

```text
task/TASK-003_FUTU_QUOTE_ONLY_MARKET_DATA_POC
```

Do not modify `master`.

Do not force-push.

Do not amend historical commits.

After implementation and validation, create one implementation commit and push only the task branch.

Do not merge into `roadmap/no-live-trading`.

Do not start another task.

## 15. Final report

After push, report:

- branch;
- implementation commit SHA;
- parent SHA;
- tree SHA if available;
- exact changed files;
- dependency changes;
- automated validation results;
- Futu quote-only architecture summary;
- live PoC result for AVGO, VRT, HK.09698 if OpenD was reachable;
- exact live blocker if not reachable/entitled;
- confirmation that no Futu trade context/account/trading capability was added;
- confirmation that Phase 1 reviews/plan/migration were untouched;
- confirmation that `phase1_remediation_commit.txt`, if present, remained untouched and untracked;
- confirmation that no force-push occurred and no base branch was modified.

Then STOP.

Do not begin TASK-004 without explicit approval.