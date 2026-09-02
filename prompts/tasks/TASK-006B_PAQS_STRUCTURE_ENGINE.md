# TASK-006B — PAQS Structure Engine

Status: **APPROVED IMPLEMENTATION CONTRACT — TASK-006B ONLY**

Repository: `ahhhhzzz/ai-infra-quant`

Task branch: `task/006b-paqs-structure-engine`

Authoritative base branch: `roadmap/no-live-trading`

Authoritative base SHA at task creation: `7909f1c04f7049cf1ccec78a3d5023ae801b7177`

Parent Roadmap decision: `PAQS-MVP-001`

Predecessor: TASK-006A — PASS / integrated at authoritative base SHA above.

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
9. `docs/research/PAQS_V0.2_CORE_DEFINITION_LOCK.md` only for the numeric structure-parameter defaults explicitly adopted by this contract
10. `docs/engineering/PAQS_ENGINEERING_GUIDE.md`
11. `docs/user/PAQS_USER_GUIDE.md`
12. this Task Contract

Then run `git status`, preserve unrelated user changes, and state the exact files planned for modification before implementation.

GitHub is the only authoritative source of truth.

Do not modify:

- `docs/phases/PHASE_1_PLAN.md`
- `docs/reviews/PHASE_1_INDEPENDENT_REVIEW.md`
- `docs/reviews/PHASE_1_POST_REMEDIATION_REVIEW.md`
- `src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py`

If local `phase1_remediation_commit.txt` exists, leave it untracked, untouched, unstaged, and uncommitted.

## 1. Objective

TASK-006B is the first PAQS task that interprets market structure.

It must deterministically transform the provider-agnostic TASK-006A input bundle into explainable structure state:

```text
completed W1 / D1 / M30 bars
        ↓
ATR
        ↓
Micro / Major confirmed Pivot
        ↓
Swing labels
        ↓
Major Swing Key Levels
        ↓
Pivot Zones
        ↓
Range
        ↓
Base Regime
        ↓
read-only Structure Snapshot
```

The task answers only:

> What structure is legitimately confirmed from completed data available as of the current calculation cutoff?

It does **not** answer:

> Should the user buy, hold, reduce, sell, or enter now?

## 2. Existing TASK-006A baseline to preserve

The authoritative base already includes:

- dynamic provider-validated US/HK listed-equity Watchlist flow;
- provider-neutral canonical market-data boundary;
- provider-confirmed equity classification for dynamic add;
- completed D1;
- recent completed 1m;
- trading-calendar/session semantics;
- completed W1 derived from D1;
- completed regular-session M30 derived from 1m;
- truthful source coverage / partial-bucket behavior;
- QFQ labelled `PROVIDER_QFQ_CURRENT`;
- `historical_replay_safe = false` for current provider QFQ;
- PAQS input quality/warnings;
- no historical public `as_of` replay route;
- no persistence for PAQS input/derived bars;
- user and engineering PAQS guides.

TASK-006B consumes this foundation. It must not duplicate provider/session/calendar logic inside the Structure Engine.

## 3. Permanent safety boundary

TASK-006B must not introduce:

```text
brokerage-account access
real cash
real positions
real orders
real fills/trades
trade import/reconciliation
broker write
place_order
cancel_order
modify_order
unlock_trade
autonomous trading
OMS/EMS
```

No structure result has external side effects.

## 4. Explicit TASK-006B scope

Allowed implementation scope:

```text
Structure Parameter Registry
ATR
Micro Pivot
Major Pivot
Swing labels
Major Swing Key Levels
Pivot-cluster Zones
Range detection
Base Regime
Structure Snapshot
read-only structure debug/API output
synthetic deterministic fixtures
no-lookahead tests
PAQS user/engineering documentation updates
006A completion-status documentation bookkeeping
```

## 5. Explicitly out of scope

Do not implement any TASK-006C or later behavior:

```text
BREAK_ATTEMPT
BREAKOUT
BREAKDOWN
FAILED_BREAKOUT
FAILED_BREAKDOWN
RETEST
ROLE_FLIP
BULL_TRANSITION
BEAR_TRANSITION
TRIGGER
FOLLOW_THROUGH

Setup families
Setup expiry
trade invalidation
trade stop
Target T1/T2
RR
next-open entry revalidation

NO_SETUP
WATCH_LONG
ENTRY_PENDING_REVALIDATION
LONG_READY
VALID_SETUP_BUT_POOR_ENTRY
WAIT_RETEST
NO_TRADE
SETUP_EXPIRED

THESIS_VALID
HOLD_WITH_WARNING
TARGET_REACHED_REVIEW
EXIT_IF_HELD

Quality Score
Composite Score
Ranking
Probability
Paper Portfolio
PaperFill
Position sizing
Backtest
```

A completed close outside a Range or previous swing may affect current Base Regime truthfulness, but TASK-006B must not label that fact as Breakout/Breakdown/Event/Transition or produce an advisory.

## 6. Input contract

The Structure Engine consumes provider-agnostic PAQS input only.

Logical input remains the TASK-006A `PaqsInputBundle` or an equivalent application-domain view containing:

```text
security identity
market
market timezone
as_of_timestamp
completed_w1_bars
completed_d1_bars
completed_30m_bars
calendar metadata
adjustment metadata
source coverage
data quality / warnings
```

The Structure Engine must not consume or import:

```text
Futu SDK
OpenQuoteContext
Futu DataFrame
provider-native enum
environment variables
latest quote as a completed close
broker/account state
```

Only completed bars whose source coverage is legitimate may enter confirmed structure calculations.

## 7. Timeframe hierarchy

TASK-006B computes structure independently on:

```text
W1  role = CONTEXT
D1  role = SETUP
M30 role = TRIGGER
```

This task does **not** combine the three timeframe states into a final trading decision.

M30 local bullish structure must not rewrite W1 or D1 state. W1 / D1 / M30 outputs remain separately inspectable.

H1 and H4 remain out of scope.

## 8. Structure Parameter Registry

TASK-006B must introduce an explicit immutable/default configuration object and deterministic `config_hash`.

The following parameters are adopted for TASK-006B.

### ATR

```text
atr_period
default = 14
```

### Pivot

```text
micro_pivot_atr_lambda
default = 1.0
allowed research range = [1.0, 2.5]

major_pivot_atr_lambda
default = 1.8
allowed research range = [1.0, 2.5]

pivot_min_bars
default = 2
allowed research range = [1, 5]

structure_equal_tolerance_atr
default = 0.25
allowed research range = [0.10, 0.50]
```

### Zone

```text
zone_cluster_epsilon_atr
default = 0.50
allowed research range = [0.25, 0.90]

zone_min_touch_separation_bars
default = 5
allowed research range = [3, 20]

zone_min_halfwidth_atr
default = 0.15
allowed research range = [0.10, 0.30]

zone_max_halfwidth_atr
default = 0.75
allowed research range = [0.50, 1.00]

zone_merge_iou
default = 0.50
allowed research range = [0.30, 0.70]
```

### Range

```text
range_lookback_bars
default = 40
allowed research range = [20, 80]

range_inside_ratio
default = 0.70
allowed research range = [0.60, 0.85]

min_range_width_atr
default = 2.0
allowed research range = [1.5, 4.0]

max_range_width_atr
default = 12.0
allowed research range = [8.0, 20.0]
```

The task must not optimize these values against returns.

No UI parameter editor is introduced.

`config_hash` must be stable for semantically identical parameter sets, using canonical sorted serialization and a deterministic cryptographic hash such as SHA-256.

Passing tests do not authorize parameter optimization.

## 9. Decimal and deterministic arithmetic contract

All price, ATR, normalized-distance, Zone and Range arithmetic uses `Decimal`.

Binary floating point must not influence any structural boundary or comparison.

Use a local explicit Decimal calculation context sufficient for the accepted project precision and deterministically quantize exposed recursively-used financial results to the existing project financial scale.

Rounding mode:

```text
ROUND_HALF_EVEN
```

Do not mutate Python's process-global Decimal context as an implicit side effect.

Equivalent input bars and config must produce equivalent output and `config_hash` across runs.

## 10. Normalized structure-bar adapter

W1, D1 and M30 have different underlying source domain types. TASK-006B may introduce one internal provider-neutral structure-bar abstraction so algorithms do not branch on provider/source classes.

It must retain at minimum:

```text
security
timeframe
bar key / canonical source reference
interval or session reference
open
high
low
close
volume
is_completed
source coverage
```

For any Pivot output, preserve a deterministic source reference for both:

```text
extreme bar
confirmation bar
```

For D1, session date remains available. For W1/M30, derived interval references remain available.

Do not fabricate an exchange-close timestamp that TASK-006A did not provide.

## 11. ATR Engine

True Range is fixed:

For the first eligible bar:

```text
TR[0] = high - low
```

For subsequent bars:

```text
TR[t] = max(
    high[t] - low[t],
    abs(high[t] - close[t-1]),
    abs(low[t] - close[t-1])
)
```

ATR period:

```text
n = 14
```

Warm-up:

- ATR is unavailable until 14 legitimate TR values exist.
- the first ATR is the arithmetic mean of the first 14 TR values.
- subsequent ATR values use EMA recurrence:

```text
alpha = 2 / (n + 1)
ATR[t] = alpha * TR[t] + (1 - alpha) * ATR[t-1]
```

An unavailable ATR is `None` / explicit not-ready state, never zero.

ATR is a volatility/distance scale only and must not itself determine direction.

## 12. Pivot Engine — fixed directional-change semantics

Each timeframe runs two fully independent Pivot instances:

```text
MICRO
MAJOR
```

A Micro Pivot must never be retrospectively promoted into a Major Pivot.

A future Major confirmation must not rewrite an earlier Micro record.

### 12.1 States

Each engine uses:

```text
UNSEEDED
SEEK_HIGH
SEEK_LOW
```

### 12.2 Candidate extreme

In `SEEK_HIGH`, maintain the greatest legitimate source-bar High and its source reference.

In `SEEK_LOW`, maintain the lowest legitimate source-bar Low and its source reference.

### 12.3 High confirmation

A candidate Pivot High confirms only at a completed bar close when:

```text
candidate_high - current_close
>= lambda_pivot * current_ATR
```

Pivot price = candidate High.

Extreme reference = bar where candidate High occurred.

Confirmation reference = current completed bar.

Then state becomes `SEEK_LOW`.

### 12.4 Low confirmation

A candidate Pivot Low confirms only when:

```text
current_close - candidate_low
>= lambda_pivot * current_ATR
```

Then state becomes `SEEK_HIGH`.

### 12.5 Close-confirmation / same-bar ambiguity rule

Extreme uses actual High/Low. Reversal confirmation uses completed Close.

A candidate extreme formed on the same bar as the putative confirmation must **not** be confirmed on that same bar because OHLC does not reveal intrabar ordering.

Therefore:

```text
candidate_extreme_bar_index < confirmation_bar_index
```

is required.

A large same-bar wick/range alone cannot manufacture a confirmed turning point.

### 12.6 Minimum separation

After at least one Pivot exists, a new Pivot may confirm only if its candidate extreme bar is at least `pivot_min_bars` source bars away from the previous confirmed Pivot's extreme bar.

If the reversal threshold is met before minimum separation, remain in the current seek state and continue updating the candidate extreme; do not fabricate a Pivot.

### 12.7 Deterministic initialization

After ATR first becomes available, `UNSEEDED` maintains running candidate High and Low observations.

For each subsequent completed bar calculate:

```text
down_reversal = seed_high - close >= lambda * ATR
up_reversal   = close - seed_low  >= lambda * ATR
```

The first Pivot may be established only when exactly one direction is legitimately confirmed and the corresponding candidate extreme occurred on an earlier bar.

If both directions satisfy on the same decision bar, initialization is ambiguous from OHLC. Confirm neither and remain `UNSEEDED` until a later bar makes direction deterministic.

No arbitrary initial trend direction is allowed.

## 13. Pivot output

Each confirmed Pivot stores at minimum:

```text
pivot_id
security
timeframe
hierarchy = MICRO | MAJOR
type = HIGH | LOW
price
extreme_source_ref
confirmation_source_ref
atr_at_confirmation
lambda_used
confirmed = true
```

`pivot_id` must be deterministic for the same security/timeframe/config/source references.

Only confirmed pivots may be emitted as usable structure.

## 14. Swing Labels

Swing labels use confirmed pivots of the same hierarchy and same type only.

For two consecutive confirmed highs:

```text
epsilon = structure_equal_tolerance_atr * ATR_at_current_pivot_confirmation
```

Then:

```text
HH if current_high > previous_high + epsilon
LH if current_high < previous_high - epsilon
EH otherwise
```

For lows:

```text
HL if current_low > previous_low + epsilon
LL if current_low < previous_low - epsilon
EL otherwise
```

Each label stores the current Pivot ID, previous comparable Pivot ID, tolerance used and label.

Unconfirmed candidates never receive Swing labels.

## 15. Key Level scope in TASK-006B

Supported sources only:

```text
MAJOR_SWING
PIVOT_CLUSTER
RANGE_BOUNDARY
```

Supported roles only:

```text
SUPPORT
RESISTANCE
REFERENCE
```

No TASK-006C role flip lifecycle exists yet.

### 15.1 Major Swing Key Level

Every confirmed Major Pivot may expose a point Key Level:

```text
Pivot Low  -> SUPPORT
Pivot High -> RESISTANCE
lower_bound = upper_bound = pivot price
source = MAJOR_SWING
```

A confirmed Major Pivot is a confirmed Major Swing observation; this does not mean a one-touch Pivot is a confirmed repeated-reaction Zone.

### 15.2 Range-boundary Key Level

When a Range is valid, its selected support/resistance Zone may additionally be referenced as `RANGE_BOUNDARY` geometry in the snapshot.

Do not mutate the underlying Zone role/source history.

## 16. Pivot Zone Engine

High Major Pivots cluster only with High Major Pivots and produce resistance geometry.

Low Major Pivots cluster only with Low Major Pivots and produce support geometry.

No High/Low cross-role clustering is allowed.

### 16.1 Pair distance

For two Major Pivot observations:

```text
normalized_distance =
abs(price_i - price_j) / median(ATR_i, ATR_j)
```

They are cluster-compatible when:

```text
normalized_distance <= zone_cluster_epsilon_atr
```

### 16.2 Deterministic clustering

Avoid provider/input iteration-order dependence.

For each role independently:

1. sort observations by price, then extreme source key, then confirmation source key, then stable Pivot ID;
2. build clusters using deterministic complete-link compatibility: a new observation may join a cluster only when it is compatible with **every** observation already in that cluster;
3. if more than one cluster is eligible, choose the cluster with the smallest normalized distance to its current simple median center; stable cluster ID is the final tie-break;
4. otherwise create a new cluster.

Equivalent observations in a different input order must yield identical clusters.

### 16.3 Independent touch rule

A cluster observation counts as a valid independent touch only when its extreme source-bar index is at least:

```text
zone_min_touch_separation_bars
```

from the previously accepted touch in chronological order.

Select independent touches chronologically and deterministically.

Repeated adjacent-bar reactions must not inflate touch count.

### 16.4 Candidate vs confirmed Zone

```text
independent_touch_count = 1 -> CANDIDATE
independent_touch_count >= 2 -> CONFIRMED
```

### 16.5 Zone center

v0.3.1 direction supersedes the undefined v0.2 weighted/rejection-strength center.

Use simple median of accepted independent-touch Pivot prices.

Even-count median is the arithmetic mean of the two middle Decimal values.

### 16.6 Zone width

Reference ATR = simple median of accepted touches' `atr_at_confirmation`.

```text
MAD = median(abs(pivot_price - center))

half_width = max(
    MAD,
    zone_min_halfwidth_atr * reference_ATR
)

half_width = min(
    half_width,
    zone_max_halfwidth_atr * reference_ATR
)

lower_bound = center - half_width
upper_bound = center + half_width
```

### 16.7 Confirmed Zone merge

Only same-role confirmed Zones may merge.

Define interval IoU deterministically. If:

```text
IoU >= zone_merge_iou
```

merge them by unioning their underlying accepted touch observations and recomputing independent touches, center, reference ATR and width from source observations.

If more than one merge is possible:

1. choose the pair with highest IoU;
2. then lowest combined lower bound;
3. then stable Zone IDs.

Repeat until no eligible pair remains.

Candidate-only Zones do not force merge of confirmed Zones.

`zone_id` must be deterministic from role/timeframe/config and sorted source Pivot IDs.

### 16.8 Deferred Zone lifecycle

TASK-006B does not implement:

```text
ROLE_FLIP_CANDIDATE
role-flip confirmation
breakout origin
zone event invalidation
persistent zone versions
persistent expiry lifecycle
```

The structure snapshot is recomputed from current legitimate input rather than persisted.

## 17. Range Engine

Range detection uses confirmed support and resistance Zones on the same timeframe.

### 17.1 Preconditions

A candidate support/resistance pair requires:

```text
resistance.lower_bound > support.upper_bound
support independent touches >= 2
resistance independent touches >= 2
```

### 17.2 Alternation

Combine accepted support/resistance touch observations chronologically.

Map to:

```text
L = support touch
H = resistance touch
```

Compress consecutive same-side observations into one chronological reaction group.

A Range requires at least four alternating reaction groups, containing a subsequence equivalent to:

```text
H-L-H-L
or
L-H-L-H
```

and each side must still have at least two valid independent touches.

### 17.3 Lookback and inside ratio

Range evaluation requires at least `range_lookback_bars` legitimate completed bars on that timeframe.

Use the latest 40 bars by default.

Define:

```text
RangeLow  = support.lower_bound
RangeHigh = resistance.upper_bound
```

Then:

```text
InsideRatio =
count(close within [RangeLow, RangeHigh]) / range_lookback_bars
```

Valid Range requires:

```text
InsideRatio >= range_inside_ratio
```

### 17.4 Width

```text
MedianATR = median(ATR values aligned to the Range lookback bars where ATR is ready)

RangeWidthATR =
(resistance.center - support.center) / MedianATR
```

All lookback bars must have ATR ready for the width calculation. Otherwise the Range is not confirmed.

Valid Range requires:

```text
min_range_width_atr <= RangeWidthATR <= max_range_width_atr
```

### 17.5 Active Range

A valid confirmed Range is active only when the latest legitimate completed close remains inside:

```text
[support.lower_bound, resistance.upper_bound]
```

A close outside this geometry means the Range is not currently active in TASK-006B.

Do not label the outside close as Breakout/Breakdown. Event semantics belong to TASK-006C.

### 17.6 Multiple valid Ranges

If multiple valid Ranges contain the latest completed close, choose `ACTIVE_RANGE` deterministically by:

```text
1. highest total independent touch count
2. highest InsideRatio
3. narrower RangeWidthATR
4. stable Range ID
```

Range ID must be deterministic from timeframe/config/support-zone ID/resistance-zone ID.

Expose other valid Ranges for debug if useful, but only one `active_range` may drive Base Regime precedence.

## 18. Base Regime Engine

TASK-006B Base Regime enum is exactly:

```text
BULL_TREND
BEAR_TREND
RANGE
UNCERTAIN
```

Do not introduce `BULL_TRANSITION` or `BEAR_TRANSITION` in this task.

### 18.1 Precedence

```text
1. invalid/insufficient structure input -> UNCERTAIN
2. active confirmed Range -> RANGE
3. confirmed Major trend structure -> BULL_TREND / BEAR_TREND
4. otherwise -> UNCERTAIN
```

### 18.2 Bull

Bull requires the most recent comparable Major Swing labels to include:

```text
latest Major High label = HH
AND
latest Major Low label = HL
```

and the latest completed Close must not be below the price of that latest Major HL Pivot Low.

This Pivot Low is only a Base-Regime structural-coherence boundary in TASK-006B. It is **not** a trade stop or TASK-006D invalidation level.

If the close is below it, return `UNCERTAIN`, not automatic `BEAR_TREND`.

### 18.3 Bear

Bear requires:

```text
latest Major High label = LH
AND
latest Major Low label = LL
```

and latest completed Close must not be above the price of that latest Major LH Pivot High.

If violated, return `UNCERTAIN`, not automatic Bull.

### 18.4 Conflicts / equality

Equal labels (`EH` / `EL`), incomplete Swing history, conflicting conditions or missing ATR/Pivots produce `UNCERTAIN` unless an active Range has precedence.

Micro Pivots never directly set Base Regime in TASK-006B.

## 19. Structure Snapshot

Introduce an immutable provider-neutral logical output such as:

```text
PAQSStructureSnapshot
```

Top-level fields must include at minimum:

```text
strategy_version
structure_version
config_hash
security_id
market
symbol
market_timezone
provider
as_of_timestamp
calculated_at
input_quality
input_warnings
adjustment_metadata
```

Per timeframe:

```text
role = CONTEXT | SETUP | TRIGGER
timeframe = W1 | D1 | M30
latest_completed_bar_ref
bar_count
atr_ready
latest_atr
micro_pivots
major_pivots
micro_swing_labels
major_swing_labels
key_levels
zones
valid_ranges
active_range
base_regime
warnings
```

The snapshot must contain enough provenance to answer:

```text
Why is this Pivot confirmed?
Which source bars formed this Zone?
Why is this Range active?
Why is Base Regime BULL/BEAR/RANGE/UNCERTAIN?
```

No probability or profitability language is allowed.

## 20. Read-only structure endpoint

TASK-006B may add one local read-only endpoint:

```text
GET /api/v1/strategies/paqs/securities/{security_id}/structure
```

It returns the current `PAQSStructureSnapshot` or a truthful structured unavailable/invalid result.

No public historical `as_of` parameter.

No config override/query parameter.

No mutation.

No trade recommendation.

No Dashboard PAQS decision-card integration yet; that belongs to TASK-006E.

A minimal developer-readable JSON structure output is sufficient for the mandatory 006B checkpoint.

## 21. Persistence boundary

TASK-006B must not add persistence for:

```text
ATR
Pivot
Swing label
Key Level
Zone
Range
Base Regime
Structure Snapshot
```

No Alembic migration is expected or authorized.

Do not modify migration `0001`.

Structure is read-through / recomputed in memory from legitimate PAQS inputs.

Persistent immutable advisory/signal history belongs to later work.

## 22. Input-quality behavior

If TASK-006A input is invalid/unavailable, do not fabricate structure.

Examples:

- no completed bars -> explicit unavailable/insufficient state;
- fewer than ATR warm-up bars -> ATR not ready and Base Regime `UNCERTAIN`;
- partial M30 bucket is already excluded by 006A and must not be reconstructed;
- unsupported/unknown calendar schedule must not be guessed;
- adjustment metadata remains visible;
- current provider QFQ replay-unsafety remains a warning/metadata fact, not silently upgraded.

A missing structure component is not numeric zero.

## 23. Required documentation updates

Update:

```text
docs/user/PAQS_USER_GUIDE.md
docs/engineering/PAQS_ENGINEERING_GUIDE.md
docs/REQUIREMENTS_MATRIX.md
docs/STRATEGY_SPEC.md
```

Also correct current Roadmap bookkeeping so TASK-006A is recorded as completed/integrated at base SHA `7909f1c04f7049cf1ccec78a3d5023ae801b7177` and TASK-006B is the current bounded structure task. Do not mark TASK-006B complete until implementation/review evidence exists.

The User Guide must explain in ordinary language:

- ATR is a volatility scale, not a direction signal;
- Pivot extreme time differs from confirmation time;
- Micro vs Major Pivot;
- HH/LH/EH and HL/LL/EL;
- Key Level vs Zone;
- what Range means;
- what BULL_TREND / BEAR_TREND / RANGE / UNCERTAIN mean;
- why `UNCERTAIN` is legitimate;
- structure output is not BUY/HOLD/SELL.

The Engineering Guide must document exact deterministic algorithms, parameters, IDs/hashes, no-lookahead rules and tests.

## 24. Required unit tests — ATR

At minimum prove:

```text
TR first-bar rule
TR gap rule
14-bar warm-up
SMA seed
EMA recurrence
Decimal-only arithmetic
same input => same result
ATR missing != zero
```

## 25. Required unit tests — Pivot

At minimum prove:

```text
close-based reversal confirmation
wick alone does not confirm
extreme ref != confirmation ref when appropriate
same-bar extreme/confirmation is rejected
ambiguous UNSEEDED bar does not fabricate direction
pivot_min_bars is enforced
Micro and Major engines are independent
future bars do not move past confirmation timestamps
prefix invariance / no-lookahead
```

Prefix invariance means: compute structure on bars `[0:t]`, then recompute with additional future bars; already-confirmed Pivot facts with confirmation <= t must remain identical.

## 26. Required unit tests — Swing / Key Level / Zone

At minimum prove:

```text
HH / LH / EH
HL / LL / EL
only confirmed Major Pivots create Major Swing Key Levels
High Pivots do not cluster with Low Pivots
zone_cluster_epsilon behavior
independent-touch separation
1 touch = CANDIDATE
2+ touches = CONFIRMED
simple median center
MAD width
min/max ATR width clamps
same-role IoU merge
deterministic merge tie-break
shuffled input order => identical Zone result
stable IDs
```

## 27. Required unit tests — Range

At minimum prove:

```text
requires confirmed support + resistance
requires >=2 independent touches on each side
requires alternating reaction sequence
inside-ratio threshold
width lower bound
width upper bound
insufficient 40-bar lookback does not confirm
latest close outside geometry => no active Range
multiple-range deterministic selection
Range suppresses internal Micro trend in Base Regime
```

## 28. Required unit tests — Base Regime

At minimum prove:

```text
HH + HL -> BULL_TREND when coherent
LH + LL -> BEAR_TREND when coherent
active Range -> RANGE even if Micro structure trends
broken prior bull coherence -> UNCERTAIN, not automatic BEAR
broken prior bear coherence -> UNCERTAIN, not automatic BULL
equal/conflicting/incomplete structure -> UNCERTAIN
Micro Pivots alone cannot set Base Regime
```

## 29. Golden synthetic fixtures

Create clearly labelled synthetic structure fixtures. Minimum:

```text
S01 clean bull Major structure
S02 clean bear Major structure
S03 confirmed Range with internal Micro trend
S04 insufficient history / UNCERTAIN
S05 delayed Pivot confirmation after earlier extreme
S06 same-bar wick ambiguity does not confirm
S07 Equal High / Equal Low tolerance
S08 one-touch candidate support Zone
S09 confirmed repeated support Zone
S10 deterministic overlapping-Zone merge
S11 invalid Range due poor inside ratio
S12 invalid Range due width
S13 multiple Range deterministic selection
S14 prefix/no-lookahead future-injection resistance
S15 M30 structure consumes only completed 006A M30 input
```

Synthetic fixtures must never be presented as real market evidence or profitability evidence.

## 30. Integration/API/architecture tests

At minimum verify:

- structure endpoint for a valid supported Security;
- truthful unavailable/invalid behavior;
- output carries `config_hash`, `as_of_timestamp`, input quality and adjustment metadata;
- no provider-native type crosses into core Structure domain;
- core does not import Futu;
- Structure Engine reads no environment variables;
- no float financial arithmetic is introduced;
- no persistence/migration is added;
- no TASK-006C Event enums/logic appears;
- no advisory/score/ranking appears;
- no brokerage/write capability appears.

## 31. Validation commands

Run and report at minimum:

```text
pytest
ruff check
ruff format --check
mypy
application startup
GET /health
GET /openapi.json
focused TASK-006B tests
```

If the repository has an existing project-standard equivalent command, use it consistently and report exact command/result.

## 32. Real read-only structure checkpoint

After deterministic tests pass, attempt a current read-only structure smoke for the existing supported initial equities:

```text
US.AVGO
US.VRT
HK.09698
```

If OpenD is available, report for each:

```text
input as_of
W1/D1/M30 bar counts
ATR readiness / latest ATR
Micro Pivot count
Major Pivot count
latest Major Swing labels
confirmed support/resistance Zones
active Range if any
Base Regime per timeframe
warnings / adjustment basis
```

Observed market structure is environmental evidence only and must not be hard-coded into deterministic tests.

If OpenD is unavailable, report the smoke as blocked truthfully. External OpenD availability alone does not fail deterministic implementation acceptance.

However Roadmap requires a **mandatory human checkpoint before TASK-006C approval**. Therefore TASK-006C must not be approved until real read-only structure output has been reviewed by the user/project manager in an environment where sufficient market data is available.

## 33. Human checkpoint intent

The checkpoint is not a profitability test.

The purpose is to inspect whether examples such as:

```text
Pivot locations
Major vs Micro density
support/resistance Zones
Range selection
Base Regime
```

look semantically reasonable on real charts before layering Event semantics on top.

If the structure engine is deterministic but produces obviously unusable real structure, do not tune parameters ad hoc in production. Record the issue and return to research/parameter governance before TASK-006C.

## 34. Scope-control acceptance

TASK-006B is not complete merely because code compiles.

It may pass implementation review only if:

```text
all adopted structure semantics are deterministic
tests pass
no-lookahead/prefix tests pass
input order does not affect structure
config hash is stable
user/engineering docs are updated
006A status bookkeeping is corrected
no migration exists
no TASK-006C behavior exists
no advisory/score behavior exists
no brokerage/write behavior exists
```

Tests prove implementation consistency, not profitability.

## 35. Codex final report requirements

Codex final report must include:

- authoritative base SHA actually verified;
- initial task branch SHA / Task Contract commit;
- final task branch HEAD SHA;
- exact changed-file list;
- summary of ATR/Pivot/Zone/Range/Regime design actually implemented;
- parameter/config hash behavior;
- full pytest result;
- focused test result;
- Ruff result;
- mypy result;
- startup/health/OpenAPI result;
- live OpenD structure smoke separately identified as environmental evidence or blocked;
- confirmation no migration was added;
- confirmation protected Phase 1 files are unchanged;
- confirmation no TASK-006C/advisory/score/broker-write behavior was introduced;
- unresolved issues/blockers.

## 36. Stop condition

After implementation:

1. commit and push only `task/006b-paqs-structure-engine`;
2. do not merge into `roadmap/no-live-trading`;
3. stop for independent review;
4. remediation, if required, must be separately focused;
5. even after TASK-006B PASS/integration, do not start TASK-006C until the mandatory real-structure human checkpoint is satisfied and the user explicitly approves TASK-006C.

**End — TASK-006B Approved Contract**