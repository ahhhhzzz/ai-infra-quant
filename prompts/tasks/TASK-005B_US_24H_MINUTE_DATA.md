# TASK-005B_US_24H_MINUTE_DATA

**Task ID:** TASK-005B_US_24H_MINUTE_DATA  
**Status:** APPROVED_FOR_IMPLEMENTATION  
**Baseline commit:** `1c1c9d7f017139ab6e96f1e42f072d01f6edce0d`  
**Target base branch:** `roadmap/no-live-trading`  
**Task branch:** `task/TASK-005B_US_24H_MINUTE_DATA`

## 1. Goal

Fix the US-equity 1-minute Dashboard behavior so supported U.S. securities can display the provider's available 24-hour minute history across overnight, pre-market, regular trading, and after-hours sessions.

Current observed behavior:

- US latest quote and market status are available during pre-market;
- US current-session 1-minute endpoint can still return `UNAVAILABLE` because the adapter requests historical 1-minute K-lines without the provider's US 24H session selector;
- HK.09698 minute behavior already works and must not regress.

The intended result for the initial US securities is:

```text
US.AVGO
US.VRT

provider-supported overnight
+ pre-market
+ regular trading hours
+ after-hours
-> completed 1-minute bars shown in the existing 1-minute Dashboard view
```

Only provider-returned bars are allowed. No synthetic minute may be invented.

This task is a bounded market-data remediation. It is not a strategy/score task.

## 2. Provider authority

Futu OpenAPI v10.10 documents `Session.ALL` for U.S. 24H Quote API historical K-line retrieval.

For U.S. historical 1-minute K-lines, TASK-005B must use the official quote-only session capability equivalent to:

```python
request_history_kline(..., ktype=KLType.K_1M, session=Session.ALL)
```

Do not use `Session.OVERNIGHT` for historical K-line requests.

Do not substitute a broker/trade session API.

The integration remains quote-only through `OpenQuoteContext`.

## 3. Market-specific behavior

### 3.1 United States

For `market == "US"` current minute data:

- request provider-supported 24H minute K-lines using `Session.ALL`;
- include actual provider bars from the current U.S. 24H market cycle;
- allow overnight, pre-market, RTH, and after-hours bars when the provider returns them;
- do not fabricate missing minutes;
- do not forward-fill zero-volume gaps;
- continue excluding an unfinished current 1-minute bar.

### 3.2 Hong Kong

For `market == "HK"`:

- preserve existing current-market-local-day minute request semantics;
- do not pass a U.S. session selector;
- preserve the verified HK.09698 behavior;
- do not change HK daily completion semantics.

### 3.3 Other markets

Do not generalize this task into a multi-market session framework.

The initial approved set remains:

```text
US.AVGO
US.VRT
HK.09698
```

## 4. US 24H display-cycle boundary

A U.S. 24H display cycle is anchored in `America/New_York` market-local time.

For this task, define the active display-cycle start as:

```text
if local time >= 20:00:
    cycle_start = current local date at 20:00 America/New_York
else:
    cycle_start = previous local date at 20:00 America/New_York
```

The visible/current cycle ends at the current retrieval instant.

This gives the expected progression:

```text
20:00 previous evening
-> overnight
-> pre-market
-> regular session
-> after-hours
-> 20:00 current evening
```

When retrieval occurs at or after 20:00 ET, a new 24H cycle begins.

Use `ZoneInfo("America/New_York")` / the canonical security market timezone. Do not hard-code UTC-4 or UTC-5 offsets.

This wall-clock boundary defines the display cycle only. It must not be reused as evidence that a daily bar is completed.

The TASK-004 authoritative provider-state rule for current daily completion remains unchanged.

## 5. Historical request date window

Because the U.S. 24H display cycle crosses a calendar date boundary, do not request only:

```text
start = market_today
end = market_today
```

For U.S. minute data, request a calendar window sufficient to include the active cycle, at minimum covering:

```text
previous New York calendar date
through
current New York calendar date
```

Then filter provider-returned bars by the actual aware cycle-start/retrieval instants.

Do not assume that the provider's start/end calendar-date parameters themselves represent the canonical trading-day identity.

## 6. Pagination is mandatory

This task must not simply add `Session.ALL` to the existing one-page request.

A 24H 1-minute cycle can exceed the existing `max_count=1000` page size. The current adapter ignores returned pagination keys, which can truncate U.S. minute data.

TASK-005B must support the official `page_req_key` continuation mechanism for the U.S. 24H minute-history request.

Required properties:

- first request uses no page key;
- subsequent requests pass the previous response's non-null `page_req_key`;
- concatenate canonical provider rows from all required pages;
- stop when the provider returns no next key;
- preserve order deterministically after parsing/filtering;
- de-duplicate by canonical interval identity if duplicate rows are encountered;
- use a finite defensive page bound so a malformed provider continuation cannot loop forever;
- if that defensive bound is exceeded, return an explicit truthful provider error rather than silently truncating and claiming `AVAILABLE`.

Do not add pandas as a new application-level dependency. Provider tabular objects must remain inside `integrations/`.

Daily K requests may remain single-page when their approved bounded ranges cannot exceed the current page limit. Do not unnecessarily rewrite the daily path.

## 7. Futu SDK boundary changes

Extend the internal quote-only Futu SDK binding only as necessary to expose the official session enum value needed by this task, for example:

```text
Session.ALL
```

The optional SDK must remain lazily imported.

Provider-native enum objects must not escape `integrations/futu_quote/`.

No Futu trade context or account API may be imported or referenced.

The `FutuQuoteContext` protocol may be extended only for the official optional keyword arguments required for pagination/session selection.

Do not create a generic provider plugin/session framework.

## 8. Completed-bar rule

Every returned minute bar must remain completed.

For each provider row:

```text
interval_start = provider timestamp interpreted in the security market timezone
interval_end = interval_start + 1 minute
```

Exclude bars where:

```text
interval_end > retrieved_at
```

Do not expose an in-progress minute.

Do not use the latest quote to synthesize or update an unfinished candle.

## 9. Missing-minute behavior

24H trading is not a guarantee that every security has a trade every minute.

Therefore:

- if a provider returns no row for a minute, leave a gap;
- do not forward-fill price;
- do not create a zero-volume candle;
- do not interpolate OHLC;
- do not treat sparse overnight liquidity as an error by itself.

If at least one completed provider bar exists inside the active U.S. cycle, the result may be `AVAILABLE` with those real bars.

If no completed provider bar exists inside the active cycle, return the existing truthful `UNAVAILABLE` semantics with a safe reason.

## 10. Response/API compatibility

Do not add a new API route.

Continue using:

```text
GET /api/v1/market-data/securities/{security_id}/minute-bars
```

Preserve the current response model unless a minimal backward-compatible metadata clarification is genuinely required.

`session_date` may remain the retrieval market-local calendar date used by the existing Dashboard cache contract. Do not expand this task into a trading-calendar model.

The existing Dashboard should consume the new US bars without a layout rewrite.

## 11. Dashboard behavior

TASK-005B is primarily a provider/backend fix.

The existing 1-minute chart should begin rendering U.S. bars during provider-supported overnight/pre-market/after-hours periods once the endpoint returns them.

Do not redesign the Dashboard.

Small UI wording/documentation changes are allowed only if needed to avoid falsely calling the US 1-minute view "regular session only" or "current day only".

The existing:

- security switching;
- chart library;
- volume pane;
- 60-second refresh;
- hidden-page pause;
- manual refresh;
- race protection;
- empty-watchlist behavior

must remain unchanged.

## 12. Daily K is explicitly unchanged

Do not apply `Session.ALL` to Daily K.

Daily bars retain the existing regular-session completion semantics and TASK-004 remediation rules.

In particular:

```text
Daily Base / daily chart input
!=
US 24H minute stream
```

No overnight/pre-market/after-hours prices may be silently redefined as the completed regular-session daily OHLC under this task.

## 13. No Composite Score yet

Do not implement:

```text
Composite Quant Score
Daily Base Score
Intraday Minute Adjustment
ranking
risk score
signals
recommendations
MA / RSI / MACD / VWAP / Bollinger Bands
```

TASK-005B only makes the future intraday input available.

A later explicitly approved TASK-006 will define the score model.

## 14. No persistence or route expansion

Do not introduce:

- minute persistence;
- daily persistence;
- database migration;
- browser IndexedDB archive;
- WebSocket;
- subscription background worker;
- server scheduler;
- aggregate dashboard API;
- new market-data route;
- public/cloud deployment.

The existing read-through architecture remains authoritative.

## 15. Safety boundary

The application remains read-only.

Forbidden:

```text
OpenSecTradeContext
OpenFutureTradeContext
place_order
cancel_order
modify_order
unlock_trade
broker account access
real cash/positions/orders/trades
```

No credentials, account IDs, trade passwords, tokens, or broker exports may be added.

`phase1_remediation_commit.txt` must remain untouched and untracked if present.

## 16. Required focused tests

Add or update focused tests proving at minimum:

1. Futu SDK binding loads the official `Session.ALL` quote-session enum.
2. US 1-minute requests pass `session=Session.ALL`.
3. HK 1-minute requests do not receive the US session selector and retain existing behavior.
4. US pre-market retrieval includes provider bars from the prior local date's 20:00+ overnight segment plus current-date pre-market bars.
5. US RTH retrieval keeps overnight + pre-market + RTH provider bars from the same active cycle.
6. US after-hours retrieval keeps earlier cycle bars plus provider after-hours bars.
7. US retrieval after 20:00 ET begins a new active 24H cycle and excludes the prior cycle.
8. DST handling uses the IANA timezone and not a fixed UTC offset.
9. unfinished latest minute remains excluded.
10. provider gaps are not synthesized.
11. pagination follows at least one non-null `page_req_key` and combines pages.
12. pagination duplicate rows do not produce duplicate canonical minute intervals.
13. defensive pagination-limit exhaustion returns explicit failure rather than partial `AVAILABLE` data.
14. provider entitlement/unavailable/error semantics remain explicit.
15. existing Daily K behavior is unchanged.
16. existing HK.09698 current-session tests remain green.
17. existing API and Dashboard tests remain green.

Normal automated tests must not require live OpenD.

## 17. Live OpenD verification

If OpenD is reachable, run a live smoke against:

```text
US.AVGO
US.VRT
HK.09698
```

During U.S. pre-market/after-hours/overnight when provider data exists, confirm US `minute-bars` returns completed bars rather than the previous regular-session-only empty result.

Report:

- raw provider market state;
- API status;
- count of returned completed minute bars;
- earliest returned interval;
- latest completed interval;
- whether any returned bars come from the prior New York calendar date when expected;
- HK regression result.

If the current U.S. session has genuinely no provider-returned completed bars for a security, report that truthfully. Do not fabricate data to pass the smoke.

## 18. Documentation

Update only documentation necessary to clarify the implemented market-data contract:

- U.S. minute view uses provider-supported `Session.ALL` 24H quote data;
- HK behavior remains current market-local day;
- Daily K remains regular-session completed data;
- no missing-minute interpolation;
- no score behavior is introduced.

Likely documents may include:

```text
README.md
docs/API_CONTRACTS.md
docs/ARCHITECTURE.md
docs/MASTER_SPEC.md
docs/REQUIREMENTS_MATRIX.md
docs/ROADMAP.md
```

Keep changes proportional.

Do not rewrite Phase 1 historical evidence.

## 19. Expected implementation scope

Likely implementation files:

```text
src/ai_infra_quant/integrations/futu_quote/adapter.py
tests/unit/test_futu_quote_adapter.py
```

Possibly small provider-neutral/API/frontend wording tests/docs if needed.

No migration file should change.

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

Also verify:

```text
GET /health -> 200
GET / -> 200
GET /openapi.json -> 200
```

Existing approved API surface must remain unchanged.

Perform the quote-only forbidden-symbol scan for at least:

```text
OpenSecTradeContext
OpenFutureTradeContext
place_order
cancel_order
modify_order
unlock_trade
```

## 21. Git rules

Work only on:

```text
task/TASK-005B_US_24H_MINUTE_DATA
```

Create one implementation commit after this Task Contract.

Do not modify `master`.
Do not modify `roadmap/no-live-trading`.
Do not force-push.
Do not merge.
Do not start TASK-006.

## 22. Final report

Report:

```text
branch
implementation commit SHA
parent SHA
tree SHA
changed files

Futu Session.ALL binding behavior
US 24H request/window behavior
pagination behavior
completed-minute filtering
HK regression behavior
Daily K unchanged confirmation

test results
ruff
mypy
diff check
OpenAPI surface
live OpenD result

confirmation:
  no synthetic bars
  no migration/persistence
  no Score/strategy
  no trading/account access
  no new route
  Phase 1 evidence untouched
  phase1_remediation_commit.txt untouched
  roadmap unchanged
  no force-push
```

Then STOP.
