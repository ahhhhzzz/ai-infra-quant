# TASK-005B_US_24H_MINUTE_DATA_V2

**Task ID:** TASK-005B_US_24H_MINUTE_DATA  
**Revision:** V2 — supersedes `prompts/tasks/TASK-005B_US_24H_MINUTE_DATA.md` for implementation  
**Status:** APPROVED_FOR_IMPLEMENTATION  
**Baseline commit:** `1c1c9d7f017139ab6e96f1e42f072d01f6edce0d`  
**Target base branch:** `roadmap/no-live-trading`  
**Task branch:** `task/TASK-005B_US_24H_MINUTE_DATA`

## 1. Goal

Fix US pre-market/overnight minute-chart coverage and expand both chart history windows to useful research ranges.

Required Dashboard data windows:

```text
Daily K: approximately 5 trading years
1-minute K: recent 30 market-calendar days
```

For US securities, the 1-minute window must use Futu 24H historical-session semantics so provider-returned overnight, pre-market, regular-session, and after-hours bars may appear.

This remains a bounded chart/data task. It is not strategy, persistence, backtest, or execution work.

## 2. Supersession

This V2 file is the implementation authority for TASK-005B.

The earlier `TASK-005B_US_24H_MINUTE_DATA.md` remains traceable history but is superseded wherever it conflicts with this V2 contract.

The implementation commit must have this V2 contract commit as its direct parent.

## 3. Product and safety boundary

The product remains:

```text
READ ONLY
LOCAL FIRST
DECISION SUPPORT
```

Do not add brokerage-account access, real cash/positions/orders/trades, broker-write APIs, order controls, credentials, or autonomous execution.

Do not implement Composite Quant Score, indicators, ranking, risk score, PaperOrder/PaperFill, backtesting, public deployment, or TASK-006.

## 4. Daily history: approximately five trading years

The Dashboard daily chart must load approximately five trading years of completed daily bars.

Use a count-based bounded contract:

```text
Dashboard full-history request: limit=1300
```

1300 completed sessions is the approved approximation for five trading years.

Expand the existing daily-bars route/adapter validation ceiling only as necessary to support this request. A reasonable API maximum is 1500; do not make it unlimited.

Requirements:

- return at most the requested completed bars;
- preserve market-local `session_date` semantics;
- preserve TASK-004/TASK-005 regular-session completion rules;
- an unfinished current regular-session daily bar remains excluded;
- canonical Daily K remains regular-session daily OHLCV;
- do not mix US overnight/pre-market/after-hours activity into Daily K;
- preserve Decimal-string serialization and provider/source timestamps;
- support securities with less than five years of listing history truthfully by returning all legitimately available completed bars.

## 5. Daily historical paging

Five years may exceed one 1000-bar Futu page.

Historical K-line paging implemented by this task must therefore work for daily history as well as minute history.

Do not silently truncate a five-year request at 1000 bars.

## 6. Minute history: recent 30 market-calendar days

The minute Dashboard must load a bounded rolling window covering:

```text
retrieved_at minus 30 market-local calendar days
through retrieved_at
```

This is a calendar-time window, not a promise of 30 trading sessions.

Weekends, holidays, closed periods, and minutes with no provider bar naturally create gaps.

Do not fabricate bars to fill any gap.

The API may expose a bounded query parameter such as:

```text
lookback_days
```

with:

```text
default = 30
minimum = 1
maximum = 31
```

or an equivalent tightly bounded contract on the existing minute-bars route.

No new route group is approved.

## 7. US 24H minute semantics

For US securities (`US.AVGO`, `US.VRT`), historical 1-minute requests must use the official Futu session mode equivalent to:

```text
Session.ALL
```

This may return provider bars from:

```text
overnight
pre-market
regular trading hours
after-hours
```

Do not request `Session.OVERNIGHT` directly.

Do not synthesize extended-hours candles from latest quotes.

Do not use a fixed UTC offset for New York. Continue using:

```text
America/New_York
```

and timezone-aware/DST-correct conversion.

## 8. US rolling-window boundary

A `start=today, end=today` request is no longer valid for the approved minute window.

For a 30-day request, include enough Futu market-local date coverage to preserve provider bars that fall within the rolling 30-day interval, including prior-evening overnight bars.

It is acceptable to request an extra boundary calendar date and then filter canonically by the final timezone-aware interval.

Final returned minute bars must satisfy:

```text
interval_start >= approved rolling window start
interval_end <= retrieved_at
```

subject to provider-returned data availability.

The unfinished current minute must remain excluded.

## 9. HK minute semantics

For `HK.09698`:

- expand the minute lookback to the same recent 30 market-calendar days;
- retain normal Futu HK historical K-line behavior;
- do not apply US `Session.ALL` to HK;
- return only provider-returned HK bars;
- do not synthesize pre-market, lunch-break, after-hours, overnight, holiday, or missing-minute bars.

## 10. Historical K-line pagination

Current code that ignores Futu `page_req_key` is insufficient for this task.

Implement reusable bounded historical K-line paging inside the Futu quote-only integration layer.

Required behavior:

1. first request uses `page_req_key=None`;
2. subsequent page requests pass the exact key returned by the previous provider call;
3. continue until the returned key is absent/None;
4. combine provider pages in chronological order;
5. deduplicate canonical output identity where necessary (`session_date` for Daily, `interval_start` for minute);
6. propagate provider failures truthfully rather than returning a partial result as fully AVAILABLE;
7. use a defensive finite maximum page count to prevent a malformed provider loop;
8. the ceiling must comfortably cover the expected 30-day 1-minute window;
9. do not use `max_count=None` simply to avoid implementing paging.

A per-page `max_count` of 1000 remains appropriate.

## 11. Futu SDK binding

Extend the lazy quote-only SDK bindings minimally to support the official session constant needed for US historical 24H requests.

Provider SDK objects/constants remain inside `integrations/futu_quote/`.

Do not add any Trade Context or account capability.

The context protocol/history call must support the provider parameters required by paging and US session selection, including `page_req_key` and `session` where applicable.

## 12. Canonical provider/application naming

The existing name `get_current_session_minute_bars()` becomes misleading once multiple dates are returned.

TASK-005B is authorized to perform a minimal provider-neutral rename/refactor such as:

```text
get_recent_minute_bars(security, lookback_days)
```

or equivalent.

Update the application service and tests consistently.

Do not build a generic historical-data framework or plugin system.

## 13. Minute response metadata

Continue using the existing route:

```text
GET /api/v1/market-data/securities/{security_id}/minute-bars
```

No new route is approved.

The response should truthfully describe the multi-day window. Add minimal provider-neutral metadata if useful, preferably:

```text
lookback_calendar_days
window_start
window_end
latest_completed_minute_bar_at
market_timezone
```

If legacy `session_date` is retained for compatibility, document it as the retrieval/current market-local date and do not imply that every returned bar belongs to that single date.

All instants remain aware UTC in the API; chart labels remain market-local via IANA timezone formatting.

## 14. Dashboard full-load versus incremental refresh

Do not re-download five years of Daily K and one month of 1-minute K every 60 seconds.

Implement two bounded modes.

### Full history load

Run on at least:

```text
initial Dashboard load
Security switch
```

Full load requests:

```text
Daily: limit=1300
Minute: lookback_days=30
```

### Incremental refresh

Automatic 60-second refresh, visibility-restored refresh, and ordinary manual refresh must not repeatedly fetch the full month/five-year history.

A recommended bounded design is:

```text
state: normal state request
Daily incremental: latest 5 completed daily bars
Minute incremental: latest 2 calendar days
```

Then merge in browser memory:

```text
Daily dedupe key: session_date
Minute dedupe key: interval_start
```

and prune caches to:

```text
Daily <= 1300 bars
Minute within the latest 30 market-local calendar days
```

Equivalent designs are acceptable if they prove that 60-second polling does not re-fetch the complete five-year/month history.

## 15. Daily merge behavior

The Dashboard should retain the full loaded daily cache in memory and merge small incremental daily responses by `session_date`.

This permits a newly completed regular-session daily bar to appear without a new five-year transfer.

Do not mutate historical OHLCV except by replacing the same provider/session identity with the latest canonical provider result returned by the approved API.

## 16. Minute merge behavior

Maintain an in-memory minute cache for the selected Security.

Merge by canonical interval identity:

```text
interval_start
```

Requirements:

- no duplicate candle after incremental refresh;
- no missing-minute interpolation;
- no synthetic candle;
- sort chronologically before rendering;
- prune bars older than the approved 30-day market-local rolling window;
- switching Security clears/replaces the selected Security's chart cache as appropriate;
- empty/failed incremental data must not silently relabel stale data as fresh.

Retaining last-good history with a clear refresh warning is allowed; clearing failed capability data is also allowed. Preserve TASK-005 truthfulness rules.

## 17. Chart viewport behavior for long history

Loading long history must not make the chart unusable by squeezing every bar into one screen.

Required UX:

- five years of Daily K are loaded and available for horizontal pan/zoom;
- one month of 1-minute bars is loaded and available for horizontal pan/zoom;
- initial visible range should emphasize recent data rather than force-fitting the full history;
- choose a sensible recent default viewport (for example roughly recent 6–12 months of Daily bars and recent active 1m bars);
- subsequent 60-second refresh must not repeatedly reset the user's manual pan/zoom position;
- switching timeframe/Security may establish a new sensible default viewport.

Do not call `fitContent()` unconditionally on every automatic refresh if it destroys user navigation state.

## 18. Performance boundary

A one-month US `Session.ALL` 1-minute window may contain tens of thousands of bars.

The implementation must remain browser-usable and local-machine reasonable.

Do not:

- fetch all tracked Securities' minute histories at once;
- keep unlimited minute history;
- persist the minute window to SQLite;
- introduce a worker/cache server/WebSocket solely for this task.

Only the selected Security requires the full chart-history load.

## 19. Historical quota/rate behavior

Do not add arbitrary sleeps solely for quota management.

Use provider paging correctly and preserve provider errors/status.

Repeated pages belonging to one provider pagination sequence are not to be treated as separate securities or fabricated responses.

Do not expand the tracked universe under this task.

## 20. Expected provider states

If the provider does not offer some extended-hours history, return whatever legitimate bars exist and expose truthful availability/reason semantics.

Do not convert a legitimate sparse extended-hours period into an error merely because every minute is not present.

If no bars exist in the requested window, preserve an explicit `UNAVAILABLE`/appropriate provider status rather than fabricating data.

## 21. Documentation

Update only relevant documentation to reflect:

- Daily Dashboard history approximately five trading years / 1300 bars;
- minute Dashboard history recent 30 calendar days;
- US minute data uses Futu `Session.ALL` 24H semantics;
- HK minute history remains normal HK provider trading sessions;
- historical K-line paging is supported;
- 60-second refresh uses bounded incremental requests rather than re-fetching full history;
- no persistence or strategy behavior was introduced.

## 22. Automated tests

Normal tests must not require live OpenD.

At minimum add/update tests proving:

1. Futu SDK bindings include the required Session.ALL quote-only constant;
2. US 1m history sends Session.ALL;
3. HK 1m history does not receive US Session.ALL behavior;
4. historical paging passes returned `page_req_key` into subsequent provider calls;
5. multi-page rows are combined chronologically;
6. page overlap does not create duplicate canonical bars;
7. provider error on a later page remains explicit and does not silently return partial AVAILABLE history;
8. defensive pagination ceiling prevents infinite looping;
9. US rolling 30-day filtering includes valid overnight/pre-market bars and excludes anything outside the window;
10. unfinished current 1m remains excluded;
11. HK multi-day minute behavior remains valid;
12. daily limit accepts the approved five-year request and does not truncate at 1000;
13. daily current-session completion semantics remain correct;
14. API Decimal/UTC/market-timezone semantics remain correct;
15. Dashboard full-load requests 1300 Daily and 30-day minute history;
16. automatic refresh uses small incremental windows instead of full history;
17. daily/minute frontend caches dedupe and prune correctly;
18. automatic refresh does not force-fit/reset viewport on every cycle;
19. existing TASK-005 polling/visibility/race behavior remains intact;
20. no new API route, migration, persistence, Score, or trading capability appears.

Tests should avoid brittle pixel-level checks.

## 23. Live OpenD validation

If OpenD is reachable, verify:

### US.AVGO and US.VRT

- quote remains AVAILABLE when entitled;
- minute request uses 24H session semantics;
- during pre-market, legitimate provider minute bars are returned when available;
- full 30-day request returns multi-date data;
- pagination completes without truncating at 1000;
- earliest/latest returned timestamps are reported;
- no unfinished current minute is returned.

### HK.09698

- recent 30-day minute history remains available when entitled;
- no artificial extended-hours bars are introduced;
- daily history remains correct.

Also report approximate bar counts and page counts for each live minute-history request when practical.

## 24. Browser smoke

If browser smoke is available, verify:

- Daily tab contains scrollable/pannable history substantially beyond the previous March 2026 boundary where listing history allows;
- 1-minute tab contains recent multi-day history rather than only today's RTH;
- US pre-market/overnight bars are visible when provider data exists;
- user can pan left into older data;
- 60-second refresh adds/updates recent bars without jumping the viewport back to fit-all;
- Security switching still works without stale-response races.

If browser automation is unavailable, report it truthfully.

## 25. Validation

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

API surface must remain the accepted route set; query parameters/schema fields may change only as authorized above.

Perform the existing forbidden trade/account scans.

## 26. Expected change scope

Likely files include:

```text
src/ai_infra_quant/integrations/futu_quote/adapter.py
src/ai_infra_quant/core/ports/market_data.py
src/ai_infra_quant/application/market_data_queries.py
src/ai_infra_quant/backend/api/v1/market_data.py
src/ai_infra_quant/backend/schemas/market_data.py
src/ai_infra_quant/frontend/static/app.js
tests/unit/test_futu_quote_adapter.py
tests/integration/test_market_data_api.py
tests/integration/test_market_dashboard.py
relevant README/docs
```

Do not add a migration.

Do not modify immutable Phase 1 review evidence.

Preserve `phase1_remediation_commit.txt` untouched/untracked if present.

## 27. Git rules

Work only on:

```text
task/TASK-005B_US_24H_MINUTE_DATA
```

Create exactly one implementation commit after this V2 contract commit.

Do not modify `master`.
Do not modify `roadmap/no-live-trading`.
Do not force-push.
Do not merge.
Do not start TASK-006.

## 28. Final report

Report:

```text
branch
commit SHA
parent SHA
tree SHA
changed files
Daily full-history range/count
Minute full-history range
US Session.ALL behavior
HK session behavior
pagination/page-count behavior
incremental refresh behavior
frontend cache/viewport behavior
test/lint/type/diff results
live AVGO/VRT/HK results with bar/page counts when available
browser smoke result
confirmation: no migration, no persistence, no Score, no trading/account access, no new route, roadmap unchanged, no force-push
```

Then STOP.
