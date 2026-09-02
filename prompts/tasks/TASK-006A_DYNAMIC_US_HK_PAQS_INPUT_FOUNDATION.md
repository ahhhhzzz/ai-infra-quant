# TASK-006A — Dynamic US/HK Securities & PAQS Input Foundation

Status: **APPROVED IMPLEMENTATION CONTRACT — TASK-006A ONLY**

Repository: `ahhhhzzz/ai-infra-quant`

Task branch: `task/006a-dynamic-us-hk-paqs-input-foundation`

Authoritative base branch: `roadmap/no-live-trading`

Authoritative base SHA at task creation: `2702750dddb9c076d0850ff0ed152964dde3d3f2`

Roadmap decision: `PAQS-MVP-001`

## 0. Authority and required reading

Before changing code, read in full:

1. `AGENTS.md`
2. `docs/ROADMAP.md`
3. `docs/MASTER_SPEC.md`
4. `docs/ARCHITECTURE.md`
5. `docs/REQUIREMENTS_MATRIX.md`
6. `docs/STRATEGY_SPEC.md`
7. `docs/research/PAQS_V0.3.1_COMPLETENESS_LOCK.md`
8. `docs/research/PAQS_V0.3.1_REVIEW_AMENDMENT_A.md`
9. this Task Contract

Then run `git status`, preserve unrelated user changes, and state the exact files planned for modification before implementing.

Phase 1 evidence and migration remain immutable.

If a local `phase1_remediation_commit.txt` exists, leave it untracked, untouched, unstaged, and uncommitted.

## 1. Objective

TASK-006A prepares the data and user-security foundation required by later PAQS tasks without implementing PAQS structure or trading/advisory logic.

It delivers two bounded outcomes:

```text
A. User can add/remove supported US/HK equities in the local Dashboard
   and immediately use the existing read-only market-data views.

B. Application can deterministically prepare provider-agnostic
   PAQS input data using completed W1 / D1 / 30m regular-session bars,
   calendar/session semantics, coverage, and adjustment metadata.
```

TASK-006A does **not** decide trend, structure, setup, buy, hold, sell, score, ranking, target or RR.

## 2. Existing baseline that must be preserved

Accepted existing behavior includes:

- canonical Security UUID identity;
- local Security CRUD foundation;
- Watchlist persistence/add/remove;
- Futu OpenD quote-only provider path;
- latest quote and market-state API;
- completed Daily bars;
- recent completed 1-minute bars;
- US minute `Session.ALL` retrieval;
- normal HK provider sessions;
- Dashboard Daily/1-minute charts and volume;
- manual + approximately 60-second refresh;
- hidden-page pause/resume and race protection;
- Windows one-click launcher;
- Decimal/UTC invariants;
- provider mode `none` truthful unavailability.

The original three PoC symbols remain valid initial data but must cease to be the market-data support whitelist.

## 3. Permanent safety boundary

The task must not introduce:

```text
brokerage-account connection
real cash / positions / orders / trades
real trade import / reconciliation
broker-write capability
place_order / cancel_order / modify_order
trade-password unlock
real-order UI/API
autonomous trading
```

All provider calls introduced by this task must remain quote/read-only market-data or trading-calendar capability.

## 4. No database migration

TASK-006A must not create an Alembic migration.

Do not modify:

```text
docs/phases/PHASE_1_PLAN.md
src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py
docs/reviews/PHASE_1_INDEPENDENT_REVIEW.md
docs/reviews/PHASE_1_POST_REMEDIATION_REVIEW.md
```

Use the existing Security and Watchlist schema.

Do not weaken the accepted `USER_SUPPLIED` fail-closed database/domain invariants.

A provider-validated market-data symbol added by the user remains a `USER_SUPPLIED` Security identity under existing Phase 1 semantics; market-data validation is **not** tradability verification and must not set broker/tradability fields to VERIFIED.

## 5. Dynamic supported-equity user flow

### 5.1 Supported initial market scope

New user-facing dynamic-add flow supports only:

```text
US listed EQUITY
HK listed EQUITY
```

No ETF discovery, A-share, crypto, Japan, Europe, futures or options support is introduced by this task.

Existing legacy Security records of other instrument types are not automatically deleted or rewritten.

### 5.2 User input

The normal Dashboard add-security flow requires only:

```text
market: US | HK
symbol
```

Do not require the user to manually type currency, timezone or instrument type for this normal flow.

Canonical identity rules already accepted in `core/domain/security.py` remain authoritative:

- US symbol uses canonical US normalization;
- HK symbol normalizes to five digits.

For the new equity flow infer:

```text
US -> currency USD, timezone America/New_York
HK -> currency HKD, timezone Asia/Hong_Kong
instrument_type -> EQUITY
```

Display name may default to canonical symbol/display symbol. Provider-name enrichment is not required.

### 5.3 Validate before mutation

The normal add flow must perform quote-only provider validation **before** creating a new Security or adding a watchlist membership.

Validation may use the existing latest-quote/snapshot capability against the canonical provider symbol.

Success requires the provider response to include/match the exact requested canonical symbol and a valid quote result.

If provider mode is `none`, provider is unavailable, provider errors, symbol is not supported, or quote entitlement prevents validation:

```text
no new Security row
no new Watchlist membership
```

Return an explicit structured failure.

### 5.4 Atomic local mutation

After provider validation succeeds:

1. reuse an existing canonical Security if one already exists;
2. otherwise create a `USER_SUPPLIED` Security using inferred currency/type and existing fail-closed semantics;
3. add/reactivate it in the default Watchlist;
4. commit the local mutation atomically.

Duplicate add is idempotent and must not create duplicate Security or active Watchlist rows.

Existing Watchlist removal remains the removal mechanism.

### 5.5 Research eligibility is not tradability eligibility

PAQS research/market-data eligibility must be separate from the historical `strategy_and_orders_allowed`/tradability concept.

TASK-006A must not mark user-added Securities as broker-tradable or VERIFIED merely because quote data exists.

Later PAQS research may consume a user-added Security when:

```text
security is enabled
market is supported by current PAQS input contract
currency matches the market contract
required market data is legitimately available
```

It must not require brokerage trading rules or a real-account concept.

## 6. Remove the hard-coded three-symbol market-data whitelist

Current `POC_SECURITIES`/explicit `_FUTU_CODES` behavior is historical PoC scaffolding and must no longer determine whether a canonical US/HK Security can use market data.

For the Futu quote-only adapter in TASK-006A:

```text
provider symbol for supported canonical US/HK equity
=
canonical display symbol
```

Examples:

```text
US.NVDA -> US.NVDA
HK.00700 -> HK.00700
```

Provider mapping must still be validated by actual quote-only provider responses; do not fabricate support.

Market-data application queries must resolve a canonical `MarketDataSecurity` dynamically from the stored Security identity rather than from a fixed tuple.

Expected market metadata:

```text
US -> USD / America/New_York
HK -> HKD / Asia/Hong_Kong
```

If stored currency conflicts with the canonical market contract, fail explicitly rather than silently correcting the persisted Security.

The initial AVGO/VRT/HK.09698 behavior must remain working.

## 7. User-facing Dashboard behavior

Replace/supplement the current normal "Create unverified security" workflow with a clear supported-equity action such as:

```text
Add US/HK stock
```

Required UX:

- Market selection limited to US/HK;
- Symbol field;
- Add action;
- loading/disabled state while validation is in flight;
- explicit success/failure message;
- successful add refreshes the Watchlist/security selector without page reload;
- newly added security can be selected and immediately load existing latest/Daily/minute market data;
- existing remove action continues to work;
- no broker/trading wording.

The underlying legacy `POST /api/v1/securities` API may remain for local identity administration, but the normal Dashboard add flow must use the provider-validated path.

## 8. Supported-security API contract

Add one bounded provider-validated local endpoint for the Dashboard normal add flow.

Recommended route:

```text
POST /api/v1/watchlist/supported-securities
```

Request:

```json
{
  "market": "US",
  "symbol": "NVDA"
}
```

Logical response fields must include enough information to refresh the UI, including:

```text
created_security
created_watchlist_item
security summary / watchlist item
provider validation status
```

HTTP/problem behavior must distinguish at minimum:

- malformed/unsupported market or symbol;
- provider not configured/unavailable/error;
- symbol/provider validation failure;
- not entitled when the provider reports it;
- incompatible existing canonical Security metadata;
- internal persistence conflict/error.

Provider validation failure must never mutate local Security/Watchlist state.

Do not create a generic external-security discovery/search platform in this task.

## 9. Trading-calendar port

Extend the provider-neutral read-only market-data boundary with the minimal trading-calendar capability needed by PAQS input preparation.

Logical operation:

```text
get_trading_days(market, start_date, end_date)
```

Canonical trading-day object must retain at minimum:

```text
market
market_date
market_timezone
session/day type when provider supplies it
retrieved_at/provenance
```

Initial provider implementation uses Futu OpenD quote-only trading-day capability.

Provider-native enums/objects remain inside `integrations/`.

Unexpected/unsupported provider day types are represented truthfully; do not guess session hours from unknown metadata.

Temporary closures/provider anomalies are not fabricated away. Calendar schedule and actual completed-bar availability are separate facts.

## 10. PAQS input timeframe contract

Initial PAQS input hierarchy is fixed by Roadmap/research definition:

```text
HTF = completed W1
STF = completed D1
TTF = completed 30m REGULAR-session bars
```

H1/H4 are explicitly out of scope.

TASK-006A implements timeframe/input preparation only. It does not interpret market structure.

## 11. Completed W1 derivation

W1 is derived only from canonical completed D1 bars using the security's market-local timezone/calendar date.

Aggregation:

```text
open   = first D1 open
high   = max D1 high
low    = min D1 low
close  = last D1 close
volume = sum D1 volume
```

Use market-local ISO week buckets.

A current partial W1 is excluded from `completed_w1_bars`.

Weekly finalization must follow `PAQS_V0.3.1_REVIEW_AMENDMENT_A.md`:

A W1 may become completed only when legitimately known from one of:

1. provider/official trading calendar establishes that the final scheduled trading session of the ISO week has completed;
2. a completed D1 from a later market-local ISO week becomes available;
3. current live market-local time has moved beyond the end of the ISO week.

Do not require a nonexistent Friday on holiday-shortened weeks.

Do not consult future bars while evaluating an earlier historical cutoff.

## 12. Completed 30m regular-session derivation

Source: canonical completed 1-minute bars only.

### US

Timezone:

```text
America/New_York
```

Initial PAQS structural session:

```text
09:30–16:00 local regular session
```

30m buckets are anchored at 09:30:

```text
09:30–10:00
10:00–10:30
...
15:30–16:00
```

US overnight, pre-market and after-hours data remain valid market data but are excluded from `completed_30m_bars` for initial PAQS input.

DST uses IANA timezone semantics, never a fixed UTC offset.

### HK

Timezone:

```text
Asia/Hong_Kong
```

Regular session segments:

```text
09:30–12:00
13:00–16:00
```

Buckets are independently anchored at 09:30 and 13:00. Lunch is never bridged.

### Per-bucket completeness

A normal 30m derived bar requires all 30 expected completed 1-minute source intervals for that bucket.

If any expected source minute is missing:

```text
derived bucket = PARTIAL / unavailable for PAQS completed input
```

Never forward-fill, zero-fill or interpolate missing source minutes.

A fully completed half-day/short session may produce only the valid 30m buckets that actually fit the provider/calendar session; do not fabricate the absent remainder of a normal full day.

## 13. Derived-bar / input domain model

Introduce provider-agnostic derived/input domain types; exact class names may vary but semantics must include:

### Derived bar

```text
security
timeframe: W1 | M30
interval/period start
interval/period end
open
high
low
close
volume
market_timezone
session_type where relevant
source_bar_count
expected_source_bar_count where relevant
coverage/quality
is_completed
```

Financial values remain Decimal.

### Adjustment metadata

Current Futu history uses current provider QFQ behavior. TASK-006A must expose this truthfully in PAQS input metadata, for example:

```text
adjustment_basis = PROVIDER_QFQ_CURRENT
adjustment_as_of = current/retrieved calculation cutoff
historical_replay_safe = false
```

Do not label current provider QFQ as `POINT_IN_TIME_ADJUSTED` historical replay safety.

Strict historical real-market PAQS replay remains unsupported in this task.

### PAQS input bundle

Introduce an internal provider-agnostic logical bundle containing at minimum:

```text
security_id
market
symbol
market_timezone
as_of_timestamp
completed_w1_bars
completed_d1_bars
completed_30m_bars
calendar metadata
adjustment metadata
data quality / warnings
source coverage
```

No Futu DataFrame, Futu enum, OpenQuoteContext object or provider-native object may enter this bundle.

## 14. PAQS input diagnostics

Provide a bounded read-only diagnostic endpoint so engineering review can verify the foundation without exposing strategy output.

Recommended route:

```text
GET /api/v1/strategies/paqs/securities/{security_id}/input-status
```

It must not expose BUY/HOLD/SELL/Score/Regime.

Return summary metadata only, such as:

```text
security identity
as_of_timestamp
market timezone
provider
data quality
adjustment basis
historical_replay_safe
D1 source count
completed W1 count
1m source count
completed M30 count
latest completed W1/D1/M30 timestamps
warnings/reasons
```

Do not add a public historical arbitrary-`as_of` endpoint in TASK-006A.

## 15. No PAQS structure/decision logic

TASK-006A must not implement or expose:

```text
ATR
Pivot
Swing labels
Key Level
Zone
Range
Base Regime
Transition
Breakout / Failed Breakout
Retest
Trigger
Follow-through
Setup
Invalidation
Target
RR
Entry Advisory
Holder Advisory
Quality Score
Composite Score
Ranking
Probability
```

If any such behavior appears in the diff, stop and remove it unless a direct technical stub is strictly necessary and inert.

## 16. No persistence for derived PAQS input

Do not persist:

```text
trading calendar cache
W1 bars
M30 bars
PAQS input bundles
```

in TASK-006A.

All are bounded read-through/in-memory calculations from current provider/canonical data.

No background polling/service/workers.

## 17. Documentation contract

Create:

```text
docs/user/PAQS_USER_GUIDE.md
docs/engineering/PAQS_ENGINEERING_GUIDE.md
```

### User guide — TASK-006A minimum content

Explain in plain language:

- what PAQS will become and that TASK-006A is only data preparation;
- how to add/remove a supported US/HK stock;
- why provider validation can fail;
- why user-added Security remains a local/unverified identity rather than a broker-tradability claim;
- W1 = context input, D1 = setup input, 30m = trigger input;
- why H1/H4 are not required now;
- why completed bars only are used;
- why US extended-session data is excluded from initial PAQS M30 input;
- why current QFQ data is not a claim of strict historical backtest safety;
- explicitly state that BUY/HOLD/EXIT are not implemented in TASK-006A.

### Engineering guide — TASK-006A minimum content

Explain:

- authority hierarchy and TASK-006A boundary;
- provider -> canonical market data -> PAQS input flow;
- dynamic security mapping and market-data validation vs tradability verification;
- US/HK currency/timezone/session mapping;
- trading-calendar port;
- W1 finalization;
- M30 regular-session aggregation and completeness;
- adjustment metadata;
- no-lookahead and non-fabrication rules;
- data-quality/error semantics;
- future extension points for TASK-006B–006E;
- common misinterpretations table.

Common misinterpretations must include at least:

```text
provider quote validation != brokerage tradability verification
user-added Security != real broker instrument/account state
latest quote != final D1 close
30m != provider-native 30m requirement
US Session.ALL != PAQS M30 structural session
QFQ != automatically point-in-time-safe historical replay
PAQS input endpoint != trading recommendation
```

Update existing authoritative/API/requirements docs when implementation behavior requires it.

## 18. Required tests

Add proportional unit/integration/architecture tests.

### Dynamic security/watchlist

- US symbol normalization;
- HK zero-padding normalization;
- unsupported market rejected;
- provider validation occurs before DB mutation;
- provider unavailable/error -> no Security/watchlist mutation;
- invalid/omitted provider symbol -> no mutation;
- not-entitled status remains explicit when observable;
- successful add creates/reuses one canonical Security and one active watchlist membership;
- duplicate add idempotency;
- currency mismatch on existing Security fails explicitly;
- original AVGO/VRT/HK.09698 remain functional;
- dynamically added supported symbol can immediately use state/Daily/minute market-data queries;
- Futu provider mapping is no longer restricted to `_FUTU_CODES` PoC tuple;
- PAQS research eligibility does not require broker tradability verification.

### Trading calendar

- US/HK provider-native calendar rows are mapped inside integration only;
- unknown day types do not get guessed;
- provider unavailable/error returns explicit status;
- calendar data has correct market timezone/date semantics.

### W1

- normal completed week aggregation;
- current partial week excluded;
- next-week D1 finalizes prior week only after next-week data is available;
- holiday-shortened week finalizes using calendar evidence;
- no future-bar injection.

### M30

- US regular-session bucket boundaries;
- US premarket/after-hours excluded;
- US DST test using `America/New_York`;
- HK morning/afternoon anchors;
- HK lunch not bridged;
- source OHLCV aggregation correctness;
- missing source minute -> partial/unavailable bucket;
- unfinished current bucket excluded;
- no forward/zero fill.

### Adjustment/input status

- `PROVIDER_QFQ_CURRENT` (or equivalent truthful enum/name) is exposed;
- `historical_replay_safe = false` for current provider path;
- diagnostics contain counts/timestamps/status but no PAQS structure/advisory/score;
- provider-native types do not leak into core/application API models.

### Architecture/safety

- core does not import Futu SDK;
- no broker/account/write capability is introduced;
- no financial binary float arithmetic in derived OHLCV;
- no migration/Phase 1 evidence modification.

## 19. Live/read-only smoke evidence

After deterministic tests pass, perform a bounded current-environment smoke check when OpenD is available.

Required original symbols:

```text
US.AVGO
US.VRT
HK.09698
```

Also attempt at least one supported US equity and one supported HK equity outside the original three, preferably using an isolated temporary local database for any watchlist mutation.

Suggested examples only, not test constants:

```text
US.NVDA
HK.00700
```

Record actual symbols used and environment results.

Smoke evidence should include:

- provider validation result;
- market-data state/Daily/minute availability;
- D1 count;
- completed W1 count;
- 1m source count;
- completed M30 count;
- latest completed W1/D1/M30;
- market timezone;
- adjustment basis;
- `historical_replay_safe` value;
- warnings/data-quality status.

Observed counts are environmental evidence only and must never become fixed golden values.

Live provider unavailability/entitlement limits must be reported truthfully and are not permission to fabricate PASS evidence.

## 20. Required validation commands

At minimum run and report exact results for:

```text
pytest
ruff check
ruff format --check
mypy
application startup / health check
```

Run any additional focused tests added by the task.

If CI is configured/triggered, report its result separately from local validation.

## 21. Expected documentation/evidence updates

At implementation completion, update as required:

```text
docs/API_CONTRACTS.md
docs/ARCHITECTURE.md
docs/MASTER_SPEC.md
docs/REQUIREMENTS_MATRIX.md
docs/STRATEGY_SPEC.md
README.md if user start/use behavior changes
```

Do not rewrite `docs/ROADMAP.md` scope during implementation unless the Task Contract itself is found inconsistent and work stops for user decision.

## 22. Completion report

Codex completion report must include:

1. task branch and final HEAD SHA;
2. base SHA used;
3. exact changed-file list;
4. concise architecture summary;
5. dynamic US/HK add-flow behavior;
6. W1/M30/calendar/adjustment behavior;
7. exact tests/lint/type/startup results;
8. live smoke evidence or explicit environmental blocker;
9. known limitations/unresolved issues;
10. explicit statement that no PAQS structure/event/setup/advisory/score behavior was implemented;
11. explicit statement that no broker-account/write capability was introduced.

Do not claim the task PASS. Codex reports implementation evidence only; independent review determines PASS.

## 23. Stop condition

After implementation and validation:

- commit and push only `task/006a-dynamic-us-hk-paqs-input-foundation`;
- do not merge into `roadmap/no-live-trading`;
- do not create or begin TASK-006B;
- do not modify unrelated branches;
- stop and wait for independent review/user approval.

**End — TASK-006A**
