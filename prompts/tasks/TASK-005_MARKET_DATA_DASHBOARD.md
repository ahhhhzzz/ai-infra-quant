# TASK-005_MARKET_DATA_DASHBOARD

**Task ID:** TASK-005_MARKET_DATA_DASHBOARD  
**Status:** APPROVED_FOR_IMPLEMENTATION  
**Baseline commit:** `1a6ae8f3ba42f2b475e51a637577af6721d5b7ca`  
**Target base branch:** `roadmap/no-live-trading`  
**Task branch:** `task/TASK-005_MARKET_DATA_DASHBOARD`

## 1. Goal

Build the first genuinely usable market-data Dashboard for AI Infra Quant.

The local homepage must allow the user to interactively view:

```text
US.AVGO
US.VRT
HK.09698
```

with:

```text
latest price
market status
daily candlestick chart
current-session completed 1-minute chart
volume
market-data timestamps
provider/data status
60-second automatic refresh
manual refresh
refresh countdown
```

This task turns the existing backend into a visible local Quant terminal.

It is not a strategy/score task.

## 2. Product boundary

The Dashboard remains:

```text
READ ONLY
LOCAL FIRST
DECISION SUPPORT
```

It must never contain:

```text
Buy
Sell
Place Order
Position Sync
Broker Account
Cash Balance from broker
Trade confirmation
Execution controls
```

Real trades remain outside this application.

The page should visibly identify itself as read-only.

## 3. Frontend architecture

Retain the existing architecture:

```text
FastAPI
+
Jinja template
+
Vanilla JavaScript
+
CSS
```

Do not introduce:

```text
React
Vue
Angular
Next.js
Vite
Webpack
npm build pipeline
frontend package manager
SPA router
```

TASK-005 is not a frontend-platform rewrite.

The existing frontend continues to use direct `fetch()` against `/api/v1`.

## 4. Chart library

Use:

```text
TradingView Lightweight Charts
version 5.2.1
```

Prefer the official standalone production browser build:

```text
lightweight-charts.standalone.production.js
```

### Runtime rule

The Dashboard must work without internet access once the project is installed.

Therefore:

```text
CDN at runtime: forbidden
local vendored JS: required
```

Suggested location:

```text
src/ai_infra_quant/frontend/static/vendor/
    lightweight-charts.standalone.production.js
```

Preserve required third-party license/NOTICE material and visible attribution required by the library license/documentation.

Do not vendor unrelated libraries.

## 5. Main Dashboard layout

Homepage `/` becomes market-first.

Desktop-first conceptual layout:

```text
┌──────────────────────────────────────────────────────────┐
│ AI INFRA QUANT           READ ONLY     Futu / Refresh   │
├────────────┬─────────────────────────────────────────────┤
│ WATCHLIST  │ AVGO · US · USD                            │
│            │                                             │
│ AVGO       │ 370.34                   PRE-MARKET          │
│ VRT        │                                             │
│ 09698      │ Last quote ...       Retrieved ...         │
│            │                                             │
│            │ [ 日 K ] [ 1分钟 ]                         │
│            │ ┌───────────────────────────────────────┐   │
│            │ │                                       │   │
│            │ │          Candlestick Chart            │   │
│            │ │                                       │   │
│            │ ├───────────────────────────────────────┤   │
│            │ │             Volume                    │   │
│            │ └───────────────────────────────────────┘   │
│            │                                             │
│            │ Market-data status / reason / timestamps    │
└────────────┴─────────────────────────────────────────────┘
```

Exact pixel styling is not contractual, but it should look like a clean modern financial terminal rather than a developer/debug page.

## 6. Security selector

Primary selector uses the existing canonical watchlist / Security identity.

Initial usable set:

```text
AVGO
VRT
09698
```

Show preferably:

```text
AVGO
Broadcom
US · USD
```

where legitimate local metadata exists.

Do not use provider symbols as primary identity.

Requests continue using:

```text
security_id UUID
```

Default selection:

```text
US.AVGO
```

if present.

Changing security must immediately load its market data.

## 7. Security-switch race protection

This is mandatory.

If the user switches:

```text
AVGO
↓
VRT
```

while an AVGO refresh is still running, the old AVGO response must never overwrite the VRT page.

Implementation must use an explicit mechanism such as:

```text
AbortController
and/or
request generation token
```

Security switch may cancel the previous refresh and start the new one immediately.

No stale cross-security render is allowed.

## 8. Current-state header

For selected security display at minimum:

```text
market + symbol
currency
latest price
canonical market state
provider market state where useful
latest_quote_at
retrieved_at
provider
quote status
market status
```

Examples:

```text
AVGO · US
370.34 USD
PRE-MARKET
```

or:

```text
09698 · HK
30.72 HKD
CLOSED
```

Do not call latest price:

```text
Close
Closing price
Today's close
```

unless sourced from a completed daily bar.

## 9. Timeframe tabs

Exactly two chart modes in TASK-005:

```text
日 K
1 分钟
```

Do not add:

```text
5m
15m
30m
1h
weekly
monthly
custom range
```

Daily and minute data must never be overlaid as two timeframe series in the same coordinate system.

A single chart container may be reused, but only the currently selected timeframe's candle/volume series may be rendered.

## 10. Daily candlestick chart

Use:

```text
GET /api/v1/market-data/securities/{security_id}/daily-bars?limit=120
```

Default display approximately the latest 120 completed trading sessions.

Render:

```text
OHLC candlesticks
+
volume histogram
```

Daily bar time is the market-local:

```text
session_date
```

not its UTC provider timestamp.

Current unfinished regular-session daily K must remain absent according to TASK-004 semantics.

## 11. 1-minute chart

Use:

```text
GET /api/v1/market-data/securities/{security_id}/minute-bars
```

Render only:

```text
current market-local session
completed 1-minute candles
volume
```

No unfinished candle.

No synthetic candle.

No missing-minute interpolation.

If the provider gives:

```text
09:32
09:34
```

do not fabricate:

```text
09:33
```

Minute data should merge by interval identity without creating duplicate candles.

When `session_date` changes:

```text
old minute-session cache -> clear
new session -> start fresh
```

## 12. Chart market-time display

The chart must display clock labels in the security's market timezone, not blindly in UTC.

Required semantics:

```text
US -> America/New_York
HK -> Asia/Hong_Kong
```

Prefer a minimal provider-neutral API extension exposing:

```text
market_timezone
```

from the existing canonical market-data metadata.

TASK-005 is authorized to add this field to existing market-data response schemas only if needed.

No new endpoint is authorized for this.

Do not determine US DST with hard-coded fixed UTC offsets.

Use proper IANA timezone formatting / `Intl.DateTimeFormat`.

## 13. Volume pane

Candlestick and volume belong to the same selected timeframe but visually distinct panes.

Recommended:

```text
upper pane: OHLC
lower pane: volume
```

Do not overlay volume directly across candle bodies.

## 14. Refresh model

Automatic refresh interval:

```text
60 seconds
```

Implementation must not use a naive unconstrained `setInterval()` that can overlap requests.

Preferred model:

```text
refresh completes
      ↓
schedule next refresh in ~60 sec
```

Use:

```text
setTimeout
+
in-flight guard
```

or equivalent.

There must never be two automatic refresh cycles simultaneously active for the selected security.

## 15. What auto-refresh updates

Each visible-page refresh must at least update:

```text
latest quote
market status
current completed 1m data
timestamps
data/provider status
```

Daily data may also be refreshed if the implementation remains simple and within provider limits.

No WebSocket is required.

No backend background polling.

## 16. Manual refresh

Provide:

```text
刷新最新行情
```

or concise equivalent.

Manual refresh:

- performs an immediate refresh;
- cannot create an overlapping request;
- visibly shows loading state;
- resets the next automatic refresh countdown after completion.

Disable or otherwise guard the button while an active refresh is already running.

## 17. Countdown

Display something like:

```text
自动刷新：43s
```

After each completed refresh reset toward:

```text
60s
```

The countdown is polling cadence, not provider latency.

Never label it:

```text
data delay
market delay
```

## 18. Page Visibility API

Mandatory behavior.

### Visible

```text
automatic refresh active
countdown active
```

### Hidden/tab backgrounded

```text
automatic polling pauses
countdown pauses/stops
```

### Becomes visible

Immediately:

```text
refresh now
↓
restart 60-second cycle
```

Use:

```javascript
document.visibilityState
visibilitychange
```

No background polling is required.

## 19. Loading and error states

Each capability must fail truthfully and independently.

Possible UI states include:

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

### Example: US pre-market with no current-session 1m

Show something like:

```text
1分钟行情暂不可用
当前市场：PRE-MARKET
```

not a generic fatal error if this is a legitimate no-data state.

### Example: OpenD offline

Display:

```text
Market data unavailable
OpenD/provider unavailable
```

while keeping the page usable.

Never show a JavaScript stack trace.

## 20. Last-good-data behavior

Transient refresh failure must not silently present old values as fresh.

Either:

1. clear the failed capability; or
2. retain last-successful data with an unmistakable warning such as:

```text
当前刷新失败 · 正在显示上次成功数据
Last successful: ...
```

Both are acceptable.

Forbidden:

- silently keeping stale chart/price while showing the page as AVAILABLE.

## 21. Market-data timestamps

Visible page should expose at least:

```text
latest_quote_at
retrieved_at
latest_completed_daily_session
latest_completed_minute_bar_at
```

Not necessarily all in the top header; some may live in a small data-status panel.

Timestamps should be human-readable.

UTC/raw values may be available through title/tooltips if useful.

## 22. Existing Phase 1 UI

TASK-005 may substantially demote the old Phase 1 debug/admin UI, because the visible product should now prioritize market data.

However, do not remove underlying Phase 1 capabilities.

Keep the existing:

```text
Portfolio facts
System/provider boundary information
Watchlist administration / Security creation
```

available below the primary Dashboard or in a secondary clearly separated local-administration section.

Do not make the old administration form the visual focus.

## 23. Responsive behavior

Desktop is primary.

Must remain usable at ordinary laptop widths.

At narrower widths:

```text
watchlist may move above chart
cards may stack
chart width adapts
```

Chart must react to container/window resize.

No dedicated mobile application work.

## 24. Visual direction

Use a restrained broker-terminal style:

```text
dark neutral background
clear price typography
subtle borders
compact status badges
high information density
minimal decorative graphics
```

Candles:

```text
up = positive/green convention
down = negative/red convention
```

Avoid:

```text
gradients everywhere
glowing neon
AI-themed decoration
marketing landing-page styling
large empty hero sections
```

This should look like a tool, not a brochure.

## 25. Provider configuration

Safe default remains:

```text
MARKET_DATA_PROVIDER=none
```

Do not change it to `futu` globally.

When `none`, Dashboard still loads and clearly reports unavailable market data.

When user launches with:

```powershell
$env:MARKET_DATA_PROVIDER = "futu"
```

the same Dashboard automatically uses the TASK-004 backend.

No Futu credential may enter frontend code.

## 26. No new backend route group

Use the existing TASK-004 routes:

```text
/state
/daily-bars
/minute-bars
```

Do not add aggregate routes such as:

```text
/dashboard
/refresh
/terminal
```

in TASK-005.

The only permitted backend contract extension is minimal display metadata such as:

```text
market_timezone
```

if genuinely required.

## 27. No persistence

Do not introduce:

```text
market quote database writes
daily K persistence
minute K persistence
browser IndexedDB market archive
service worker cache
```

TASK-005 remains read-through.

Ordinary in-memory browser state for the active page is fine.

## 28. Explicit non-goals

Do not implement:

```text
Composite Quant Score
Daily Base Score
Intraday Minute Adjustment
ranking
risk score
reference price model
recommendations
technical indicators
MA
RSI
MACD
VWAP
Bollinger Bands
news
fundamentals
Eastmoney/Choice
historical minute replay
tick/order book
portfolio trading
PaperOrder/PaperFill
backtesting
WebSocket
background worker
login
multi-user
public deployment
GitHub Pages
```

Do not start TASK-006.

## 29. Composite Score placeholder

Do not calculate a fake score.

Prefer not to display Score at all.

If layout contains a reserved future area, it may only state:

```text
Composite Score — not implemented
```

No number, band, recommendation, placeholder 0, or synthetic score.

## 30. Testing requirements

Normal automated suite must remain independent of live OpenD.

At minimum cover:

1. `/` renders Dashboard structure;
2. three supported seeded Securities are selectable through canonical identity;
3. vendor chart asset is locally served;
4. no runtime CDN dependency exists;
5. daily and minute tabs are distinct;
6. latest price is not labelled close;
7. volume area exists;
8. manual refresh control exists;
9. 60-second cadence is explicit;
10. overlapping refresh prevention exists;
11. Page Visibility behavior exists;
12. immediate visible-page refresh exists;
13. security-switch race protection exists;
14. unavailable provider state renders without page failure;
15. NOT_ENTITLED/error state can be shown;
16. no fake data is embedded;
17. no Buy/Sell/order controls exist;
18. no Composite Score calculation exists;
19. existing Phase 1 backend routes/tests still pass;
20. no new API route except explicitly approved minimal metadata extension.

Tests should avoid brittle pixel-level assertions.

## 31. Frontend behavior validation

Because this is a UI task, source-only tests are insufficient for final product confidence.

If browser automation is available in the execution environment, perform a browser smoke at approximately desktop viewport and verify:

```text
page loads
AVGO selected
security switching works
daily chart renders
minute tab renders appropriate state
manual refresh works
countdown runs
hidden-page handling does not create overlap
```

Do not add a heavyweight browser-testing dependency solely to satisfy this task.

If browser automation is unavailable:

```text
VISUAL_SMOKE_BLOCKED
```

is acceptable for commit, but a local user visual smoke is required before final integration approval.

## 32. Live Futu smoke

If OpenD is reachable:

Run the Dashboard with:

```text
MARKET_DATA_PROVIDER=futu
```

Verify at least:

```text
AVGO
VRT
HK.09698
```

can be selected.

Market-session-dependent empty data is acceptable when truthful.

Do not fabricate candles to make visual smoke pass.

## 33. Expected change scope

Likely:

```text
src/ai_infra_quant/frontend/templates/index.html
src/ai_infra_quant/frontend/static/app.css
src/ai_infra_quant/frontend/static/app.js
src/ai_infra_quant/frontend/static/vendor/...
possibly backend market-data schema/application view only for market_timezone
tests/
README.md
small docs updates:
API_CONTRACTS
ARCHITECTURE
MASTER_SPEC
REQUIREMENTS_MATRIX
ROADMAP
```

Only modify necessary files.

## 34. Forbidden historical changes

Do not modify:

```text
docs/reviews/PHASE_1_INDEPENDENT_REVIEW.md
docs/reviews/PHASE_1_POST_REMEDIATION_REVIEW.md
docs/phases/PHASE_1_PLAN.md
src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py
```

No migration.

Preserve:

```text
phase1_remediation_commit.txt
```

untracked and untouched if present.

## 35. Acceptance criteria

TASK-005 passes only if:

1. homepage is a usable market-data Dashboard;
2. AVGO/VRT/09698 can be switched;
3. selector uses canonical Security UUID;
4. latest price + market state display;
5. daily candlestick + volume render;
6. current-session 1m candlestick + volume render;
7. daily/1m are separate modes;
8. completed bars only;
9. market-local time display is correct;
10. 60-second refresh works;
11. automatic refresh cannot overlap;
12. manual refresh works;
13. countdown works;
14. hidden page pauses automatic polling;
15. visibility restore refreshes immediately;
16. security switching cannot suffer stale-response race;
17. truthful provider/status/error UI exists;
18. no stale data is silently represented as fresh;
19. chart dependency works locally without CDN;
20. Phase 1 backend functionality is preserved;
21. no persistence/migration is introduced;
22. no Composite Score is implemented;
23. no trading/account functionality exists;
24. tests/ruff/mypy/diff validation pass;
25. live/visual smoke is truthfully reported.

## 36. Validation

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
GET /health
GET /
GET /openapi.json
```

Existing TASK-004 API surface must remain intact.

Perform forbidden scan for:

```text
OpenSecTradeContext
OpenFutureTradeContext
place_order
cancel_order
modify_order
unlock_trade
```

Also perform a frontend scope scan for accidental:

```text
BUY
SELL
order submission
score calculation
```

Classify historical/tests/contracts carefully rather than treating textual mentions mechanically.

## 37. Git rules

Work only on:

```text
task/TASK-005_MARKET_DATA_DASHBOARD
```

Do not modify `master`.

Do not force-push.

Do not amend previous commits.

After implementation and validation, create one implementation commit and push only the task branch.

Do not merge into `roadmap/no-live-trading`.

Do not start TASK-006.

## 38. Final report

After push, report:

```text
branch
commit SHA
parent SHA
tree SHA
changed files
chart library/version
third-party attribution/license handling
test results
ruff
mypy
diff check
Dashboard behavior:
  security switching
  daily K
  1m K
  volume
  manual refresh
  auto refresh
  countdown
  visibility pause/resume
  race protection
live OpenD result
visual/browser smoke result
confirmation:
  no new migration
  no persistence
  no Composite Score
  no trading/account access
  no new unapproved routes
  Phase 1 evidence untouched
  phase1_remediation_commit.txt untouched
  roadmap branch unchanged
  no force-push
```

Then STOP.
