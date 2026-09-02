# PAQS v0.3.1 — Completeness Lock
## Price Action Quant Strategy
### Structure → Context → Event → Setup → Entry / Hold / Exit Advisory

**Status:** RESEARCH DEFINITION LOCK FOR DESIGN; **not an implementation contract**  
**Scope:** closes the eight P0 completeness gaps identified during review of the user-provided PAQS v0.3 Structural Completeness Specification.  
**Relationship to existing authority:** this research document does **not** supersede `docs/ROADMAP.md`, `docs/MASTER_SPEC.md`, or an explicitly approved Task Contract. Implementation remains prohibited until a later Task Contract explicitly adopts the relevant rules.  
**Historical relationship:** `PAQS_V0.2_CORE_DEFINITION_LOCK.md` remains research history. v0.3.1 preserves the v0.3 Price Action direction and locks the additional semantics below.

---

# 1. Preserved PAQS architecture

PAQS remains a deterministic, explainable Price Action decision-support model. It does not predict the next bar directly and does not generate broker commands.

The strategy pipeline remains:

```text
Completed Price Data
        ↓
ATR / Volatility Scale
        ↓
Pivot / Swing
        ↓
Key Level / Zone / Range
        ↓
Base Regime
        ↓
Price Action Events
        ↓
Regime Transition
        ↓
Trigger
        ↓
Follow-through
        ↓
Setup Qualification
        ↓
Structural Invalidation
        ↓
Structural Target
        ↓
RR / Entry Revalidation
        ↓
Advisory State
        ↓
Optional Quality / Composite Score
```

The following remain FIXED research semantics:

- only confirmed pivots are usable;
- event extreme time and confirmation time are distinct;
- `feature[t] = f(data <= t)`;
- Zone is an area, not an arbitrary one-price line;
- Range suppresses internal micro-trend until structural breakout;
- `Event != Setup != Signal`;
- Break Attempt is not Breakout;
- Failed Breakout requires excursion + reclaim;
- Retest occurs only after confirmed Breakout;
- Follow-through occurs only after Trigger and begins in `PENDING` state;
- HTF / STF / TTF are hierarchical roles, not votes to average;
- Invalidation and Target must have structural provenance;
- RR is a hard gate for a declared entry variant;
- historical events/signals are immutable snapshots;
- Quality Score is not probability;
- the product remains read-only decision support and never represents a real brokerage position or order.

---

# 2. P0-1 — Entry / RR Temporal Contract

## 2.1 Problem closed

v0.3 defined:

```text
DECISION_TIME(t) = bar t close
ENTRY_TIME        = next tradable bar open
```

while RR requires an Entry price. The next tradable open is not known at decision time. Therefore a setup cannot become final `LONG_READY` at bar `t` by pretending the next open equals the current close.

## 2.2 FIXED two-stage decision

### Stage A — Setup decision at completed bar close

At `DECISION_TIME(t)` the engine may know:

```text
setup
invalidation snapshot
target snapshot
reference price = close_t
```

It may calculate an **indicative** RR using `close_t`, but this value is not an executable-entry RR.

Outputs allowed:

```text
WATCH_LONG
ENTRY_PENDING_REVALIDATION
NO_TRADE
SETUP_EXPIRED
```

The engine must persist:

```text
setup_decision_at
reference_entry_price
indicative_rr_t1
indicative_rr_t2
```

### Stage B — Entry revalidation

When the next tradable bar open becomes legitimately known:

```text
entry_reference_price = open_(t+1)
```

recompute:

```text
RR_T1
RR_T2
setup validity
context validity
entry degradation
```

Only then may the advisory become:

```text
LONG_READY
```

If the structure remains valid but price has moved too far and T1 RR fails:

```text
VALID_SETUP_BUT_POOR_ENTRY
WAIT_RETEST
```

If the setup or context has invalidated:

```text
NO_TRADE
```

## 2.3 No synthetic fill semantics

`entry_reference_price` is a research/advisory reference. It is not a real fill and does not imply the user traded.

The strategy never imports a real fill to decide whether the setup was correct.

## 2.4 Backtest rule

A backtest may use the next tradable open only when that bar is reached by the historical clock. It may not use `open_(t+1)` while evaluating state at `t`.

---

# 3. P0-2 — Entry / Holder / Exit Advisory State Machines

PAQS must distinguish a new-entry question from the conditional question "if already held, is the thesis still valid?". The product still has no real-position state.

## 3.1 Entry Advisory

Fixed enum:

```text
NO_SETUP
WATCH_LONG
ENTRY_PENDING_REVALIDATION
LONG_READY
VALID_SETUP_BUT_POOR_ENTRY
WAIT_RETEST
NO_TRADE
SETUP_EXPIRED
```

Meaning:

- `NO_SETUP`: no qualifying setup exists;
- `WATCH_LONG`: structure/location is interesting but required trigger/confirmation is incomplete;
- `ENTRY_PENDING_REVALIDATION`: setup qualified at a completed decision bar but next-open RR is not yet known;
- `LONG_READY`: declared entry variant, structural validity and entry-time T1 RR all pass;
- `VALID_SETUP_BUT_POOR_ENTRY`: thesis remains valid but current entry geometry is unattractive;
- `WAIT_RETEST`: do not chase; a later retest may create a new entry candidate;
- `NO_TRADE`: a hard gate failed;
- `SETUP_EXPIRED`: the setup lifecycle ended before valid entry.

## 3.2 Holder Advisory

Fixed conditional enum:

```text
THESIS_VALID
HOLD_WITH_WARNING
TARGET_REACHED_REVIEW
EXIT_IF_HELD
```

The phrase `IF_HELD` is mandatory where needed because PAQS does not know real brokerage holdings.

### THESIS_VALID

Use when:

```text
no hard invalidation
AND
no stronger holder state applies
```

### HOLD_WITH_WARNING

Use when the broad thesis remains structurally valid but a soft deterioration exists, such as:

```text
micro structure weakens
follow-through deteriorates
price re-enters a weaker location
```

A soft warning must not silently move the hard invalidation boundary.

### TARGET_REACHED_REVIEW

Use when a snapshotted structural target is reached while the thesis has not hard-invalidated.

This state is a **profit-taking decision point**, not an automatic full sell. v0.3.1 intentionally does not invent one universal take-profit policy for trend, range and breakout setups.

### EXIT_IF_HELD

Use when the snapshotted hard structural invalidation is confirmed.

This is the minimum locked sell/exit semantic in v0.3.1: the original thesis is no longer valid.

## 3.3 Holder-state precedence

At a completed decision point:

```text
HARD INVALIDATION
    > TARGET REACHED
    > SOFT WARNING
    > THESIS VALID
```

If a bar both touches a target and closes through hard invalidation, record both facts, but the current holder advisory is:

```text
EXIT_IF_HELD
```

For historical P&L, if OHLC does not reveal which intrabar event occurred first, record:

```text
AMBIGUOUS_INTRABAR_SEQUENCE
```

and do not fabricate an execution order. Higher-resolution legitimate data is required to resolve it.

## 3.4 Exit variants still separate

The following remain VARIANT rather than hidden defaults:

```text
T1 full exit
T1 partial exit
no target exit / structural invalidation only
trailing stop after T1
runner to T2
```

They must be declared before backtesting and may not be selected trade-by-trade from hindsight.

---

# 4. P0-3 — Setup-Specific Invalidation Contract

## 4.1 General rule

Every Setup must snapshot:

```text
thesis_anchor_level_id
setup_invalidation_source
setup_invalidation_level
trade_invalidation_source
trade_invalidation_level
invalidation_buffer_atr
invalidation_timeframe
```

The invalidation source is selected by setup semantics, not by whichever stop produces the best historical RR.

After `LONG_READY`, the hard invalidation may not be widened. A future trailing-stop variant may tighten it but is outside v0.3.1.

## 4.2 Trend Pullback Long

Setup thesis:

```text
HTF bull context
+
STF correction into pre-existing structural support
+
TTF reversal trigger
```

Fixed source rules:

```text
setup anchor:
    the STF structural support Key Level snapshotted when the setup is created

setup invalidation:
    decisive STF close below anchor lower boundary - buffer

context invalidation metadata:
    HTF major HL / major support invalidation
```

The HTF boundary is context metadata and cannot be used after entry to retroactively widen a tighter snapshotted setup invalidation.

## 4.3 Range Failed Breakdown Long

Fixed source:

```text
FAILED_BREAK_EXTREME
```

Hard invalidation:

```text
decisive close below failed_break_extreme - failed_break_stop_buffer
```

The system may not replace the failed-break extreme with a farther support level merely to improve survival statistics.

## 4.4 Right-Side Breakout Long — Follow-through variant

Fixed source:

```text
BREAKOUT_SOURCE_LEVEL snapshot
```

Hard invalidation:

```text
decisive STF close below old resistance lower boundary - buffer
```

## 4.5 Right-Side Breakout Long — Retest variant

Fixed source:

```text
RETEST_FAILURE_BOUNDARY derived from the immutable breakout-source snapshot
```

Hard invalidation follows the declared Retest Failure semantics. A micro low may be recorded as quality information but is not silently substituted as the hard stop.

## 4.6 Soft vs hard

A TTF micro break against a long position is normally:

```text
HOLD_WITH_WARNING
```

unless it independently satisfies the snapshotted hard invalidation rule.

---

# 5. P0-4 — Structural Target Candidate Selection

## 5.1 Candidate generation

For a Long setup, collect only decision-time-known confirmed candidates above the entry reference from the v0.3 approved source families:

```text
OPPOSITE_RANGE_BOUNDARY
PREVIOUS_MAJOR_SWING_HIGH
CONFIRMED_MAJOR_RESISTANCE
GAP_EDGE
```

Future measured-move/channel projections remain excluded.

## 5.2 Normalize geometry

A Key Level is treated as an interval:

```text
lower_bound
upper_bound
```

A single-price level uses:

```text
lower_bound == upper_bound
```

For a Long target, the effective first obstacle is the nearest lower boundary of a resistance interval.

## 5.3 Merge confluence before choosing

Candidates within:

```text
key_level_merge_tolerance_atr
```

may be treated as one obstacle cluster while preserving all `confluence_sources`.

Source priority is used only for provenance/tie interpretation inside the same obstacle cluster. It may not be used to skip a nearer valid obstacle.

## 5.4 T1 and T2

After filtering invalid/expired/behind-entry candidates and merging confluence:

```text
T1 = nearest materially relevant structural obstacle
T2 = next distinct structural obstacle, if present
```

The target snapshot records:

```text
target_source
target_source_object_id
target_lower_bound
target_upper_bound
target_effective_price
target_created_at
```

## 5.5 Entry gate uses T1 by default

The default v0.3.1 entry gate is:

```text
RR_T1 >= minimum_rr
```

If T1 fails, the engine may not ignore it and use a distant T2 merely to pass RR.

Allowed result:

```text
VALID_SETUP_BUT_POOR_ENTRY
WAIT_RETEST
or
NO_TRADE
```

depending on setup lifecycle.

A future runner variant may use T2 only if that variant is declared before evaluation.

---

# 6. P0-5 — Initial US/HK Multi-Timeframe Aggregation Contract

## 6.1 Initial PAQS mapping

For the initial tracked equities:

```text
US.AVGO
US.VRT
HK.09698
```

v0.3.1 locks the first research mapping to:

```text
HTF = W1 completed bars
STF = D1 completed bars
TTF = 30m completed REGULAR-session bars
```

This mapping is selected because it is deterministic from the currently approved Daily + completed 1-minute market-data boundary for both US and HK markets.

`H1` and `H4` are **not** part of the v0.3.1 initial core. Their session anchoring requires a separate future contract.

## 6.2 W1 construction

W1 is derived only from completed D1 bars in market-local calendar time.

The current partially formed week is not usable as a completed W1 bar. A W1 bar becomes eligible only when the week is known complete under the historical/as-of clock.

No future daily bar may be used to complete a historical week before it becomes available.

## 6.3 D1 construction

Use canonical completed provider-neutral daily bars only.

The current intraday/latest price is never substituted for the final daily close.

## 6.4 US 30m regular-session bars

Timezone:

```text
America/New_York
```

Structural PAQS TTF uses regular session only:

```text
09:30–16:00 local exchange time
```

Aggregate consecutive 30-minute intervals anchored at 09:30:

```text
09:30–10:00
10:00–10:30
...
15:30–16:00
```

US overnight, pre-market and after-hours `Session.ALL` data remain legitimate market-data observations but are excluded from the v0.3.1 structural TTF engine by default. They may be retained as explicit context metadata for later research.

DST must use the IANA timezone and may not use a fixed UTC offset.

## 6.5 HK 30m regular-session bars

Timezone:

```text
Asia/Hong_Kong
```

Use:

```text
09:30–12:00
13:00–16:00
```

with independent 30-minute buckets anchored at each session segment start. The lunch break is never bridged into one synthetic candle.

## 6.6 Derived-bar completeness

Only completed source 1-minute bars may enter a derived 30m bar.

Missing minute observations are not fabricated or forward-filled. The aggregate uses the legitimately observed source bars and records source coverage metadata. An interval with no legitimate source bars is unavailable, not a zero-volume fabricated candle.

Each derived bar preserves at minimum:

```text
market_timezone
session_type = REGULAR
interval_start
interval_end
source_first_bar_at
source_last_bar_at
source_bar_count
completed = true
```

## 6.7 Timeframe conflict semantics

The v0.3 hierarchy remains:

```text
W1 = Context
D1 = Setup
30m = Trigger
```

30m strength cannot overwrite a W1 Range/Bear context. It may only qualify or weaken the lower-timeframe setup according to the declared setup family.

---

# 7. P0-6 — Gap Session Semantics

## 7.1 Gap type locked for v0.3.1

The first supported Gap Key Level source is:

```text
REGULAR_SESSION_OPEN_GAP
```

It is explicitly a regular-session concept, not a claim that no trading occurred overnight.

## 7.2 Gap creation

For a new regular session:

```text
previous_regular_close
current_regular_open
```

become legitimately known under completed-bar semantics.

Gap size:

```text
abs(current_regular_open - previous_regular_close)
```

normalized using the last completed D1 ATR available before the new session open.

Research parameter:

```text
gap_min_size_atr
```

must enter the Parameter Registry before optimization. Candidate research default:

```text
default = 0.25
range   = [0.10, 1.00]
```

Gap interval:

```text
gap_low  = min(previous_regular_close, current_regular_open)
gap_high = max(previous_regular_close, current_regular_open)
```

The Gap becomes usable only after the current regular-session open is legitimately established by completed source data.

## 7.3 US overnight treatment

Overnight/premarket trading through the regular-session gap interval does not erase the semantic fact that a regular-session opening gap occurred.

Record research metadata such as:

```text
overnight_traded_through_gap
premarket_traded_through_gap
```

but do not silently redefine the Gap based on hindsight.

## 7.4 HK lunch break

The 13:00 afternoon reopen is not treated as a new daily `REGULAR_SESSION_OPEN_GAP` in v0.3.1.

## 7.5 Gap lifecycle

Use explicit status:

```text
OPEN
PARTIALLY_FILLED
FILLED
EXPIRED
```

Role (`SUPPORT`, `RESISTANCE`, `TARGET`, `REFERENCE`) remains separate from source (`GAP_EDGE`).

---

# 8. P0-7 — Corporate-Action / Adjustment Basis

## 8.1 Problem closed

Splits, consolidations, dividends and other mechanical corporate actions must not appear to PAQS as fake breakouts, gaps, pivots or regime changes.

At the same time, a historical backtest must not use adjustment information from a corporate action that was not yet effective at the historical as-of time.

## 8.2 FIXED canonical requirement

PAQS structural calculations require a price series with explicit:

```text
adjustment_basis
adjustment_as_of
corporate_action_cutoff_at
```

The required research basis is:

```text
POINT_IN_TIME_ADJUSTED
```

Meaning:

> prices used at as-of time `t` may incorporate only corporate actions whose effective information is legitimately applicable at or before `t`.

Actions effective after `t` must not alter the historical state visible to the strategy at `t`.

## 8.3 Live and backtest parity

Live research:

```text
adjustment_as_of = current calculation cutoff
```

Historical replay:

```text
adjustment_as_of = historical data_as_of
```

Daily and minute-derived data participating in the same PAQS calculation must use the same canonical adjustment basis.

## 8.4 Unsupported data behavior

If the provider/application layer cannot establish a consistent point-in-time adjustment basis for an affected span, PAQS must return an explicit unsupported/unavailable data-quality state.

Forbidden:

```text
silently mix raw Daily with adjusted minute
silently treat a split discontinuity as a breakdown
use today's future-adjusted series as proof of a historical signal without point-in-time controls
fabricate missing corporate-action factors
```

Exact provider-specific acquisition of adjustment factors remains an implementation/data-contract task, not a Strategy dependency.

---

# 9. P0-8 — PAQS and Composite Quant Score Relationship

## 9.1 Primary decision engine

v0.3.1 locks the research direction:

```text
PAQS structural/event/setup state machine
        ↓
Advisory State
```

is primary.

A numerical Score must not create a Breakout, invent a Setup, bypass RR, cancel hard invalidation, or turn `NO_TRADE` into `LONG_READY`.

## 9.2 Compatibility with current approved high-level score architecture

The current authoritative documentation still contains:

```text
Composite Quant Score
=
Daily Base Score
+
Intraday Minute Adjustment
```

v0.3.1 does not silently supersede that governance decision.

If a future Task Contract retains Composite Score, the PAQS-compatible interpretation is:

```text
Daily Base Score
    = derived summary of completed W1/D1 structural context and setup quality

Intraday Minute Adjustment
    = bounded derived summary of completed 30m trigger/follow-through/risk information
```

The Composite Score is therefore a **derived presentation / quality / ranking layer**, not the causal strategy engine.

## 9.3 Hard gates dominate score

Examples:

```text
HARD_INVALIDATION
→ EXIT_IF_HELD
regardless of score

RR_T1 < minimum_rr
→ no LONG_READY
regardless of score

HTF = UNCERTAIN and setup variant disallows it
→ NO_TRADE
regardless of score
```

## 9.4 Missing intraday data

Missing intraday data is not equivalent to zero adjustment.

Allowed representation:

```text
Daily component = available
Intraday component = NOT_APPLIED / UNAVAILABLE
coverage = partial
```

Forbidden:

```text
missing intraday -> adjustment = 0
```

unless the data is complete and the true calculated adjustment is exactly zero.

## 9.5 Score formula remains separately unapproved

v0.3.1 does not lock:

```text
score scale
weights
normalization
bands
ranking formula
quality-score formula
```

Those require a later explicitly approved scoring contract after PAQS structural semantics are implemented and validated.

---

# 10. Unified advisory snapshot

A future PAQS advisory object should be able to explain the entire decision without brokerage state.

Minimum logical fields:

```text
strategy_version
config_hash
symbol
market
as_of_timestamp
calculated_at

HTF_context
STF_setup
TTF_trigger

base_regime
transition_state

key_levels_snapshot
events_snapshot
followthrough_state

entry_advisory
holder_advisory

reference_entry_price
entry_reference_price

setup_invalidation_source
setup_invalidation_level
trade_invalidation_source
trade_invalidation_level

target_t1_source
target_t1_level
target_t2_source
target_t2_level

indicative_rr_t1
rr_t1
rr_t2

hard_gate_results
soft_warnings
reason_codes

quality_score = null until separately defined
probability   = null until calibrated

data_quality
coverage
```

The object is immutable for its `as_of_timestamp`. A later recalculation produces a new revision rather than rewriting history.

---

# 11. Additional v0.3.1 reason codes

Add research reason codes:

```text
ENTRY_PENDING_REVALIDATION
ENTRY_GAP_DEGRADED_RR
VALID_SETUP_POOR_ENTRY
WAIT_RETEST

THESIS_VALID
HOLD_WITH_WARNING
TARGET_REACHED_REVIEW
EXIT_IF_HELD
AMBIGUOUS_INTRABAR_SEQUENCE

INVALIDATION_SETUP_ANCHOR
INVALIDATION_FAILED_BREAK_EXTREME
INVALIDATION_BREAKOUT_SOURCE
INVALIDATION_RETEST_FAILURE

TARGET_T1_NEAREST_OBSTACLE
TARGET_T2_SECOND_OBSTACLE
TARGET_SHOPPING_FORBIDDEN

MTF_W1_D1_30M
TTF_REGULAR_SESSION_ONLY
US_EXTENDED_SESSION_CONTEXT_ONLY

REGULAR_SESSION_OPEN_GAP
GAP_OVERNIGHT_TRADED_THROUGH

POINT_IN_TIME_ADJUSTED
UNSUPPORTED_CORPORATE_ACTION_BASIS

SCORE_DERIVED_NOT_DECISION_ENGINE
INTRADAY_SCORE_NOT_APPLIED
```

---

# 12. v0.3.1 Acceptance / Golden Tests

These are research-definition tests to be translated into implementation fixtures only after an approved Task Contract.

## C01 — Next-open RR not known early

At D1 close:

```text
setup qualified
indicative RR = 3.0
```

Expected:

```text
ENTRY_PENDING_REVALIDATION
not LONG_READY
```

Next session opens with RR = 0.8.

Expected:

```text
VALID_SETUP_BUT_POOR_ENTRY
WAIT_RETEST
```

## C02 — Conditional holder advisory without brokerage state

Structure remains valid.

Expected:

```text
holder_advisory = THESIS_VALID
```

No real-position object is required or created.

## C03 — Soft warning is not exit

TTF micro break against Long while hard invalidation remains intact.

Expected:

```text
HOLD_WITH_WARNING
not EXIT_IF_HELD
```

## C04 — Hard invalidation

Snapshotted failed-break extreme is decisively broken.

Expected:

```text
EXIT_IF_HELD
```

## C05 — Target reached is not universal full sell

T1 is reached with no hard invalidation and no declared full-exit variant.

Expected:

```text
TARGET_REACHED_REVIEW
```

## C06 — Ambiguous target and invalidation same OHLC bar

A bar high crosses T1 and close confirms hard invalidation, but lower-resolution OHLC cannot establish event order.

Expected:

```text
target_reached = true
hard_invalidation = true
holder_advisory = EXIT_IF_HELD
backtest_event_order = AMBIGUOUS_INTRABAR_SEQUENCE
```

No fabricated fill ordering.

## C07 — Invalidation cannot widen after entry

A Trend Pullback Long snapshots STF support invalidation. A farther HTF support later looks more convenient.

Expected:

```text
original hard invalidation unchanged
```

## C08 — Nearest target blocks target shopping

T1 resistance gives RR 1.2; farther T2 gives RR 3.5; minimum RR is 2.0.

Expected:

```text
NO_TRADE or WAIT_RETEST
```

T2 cannot rescue the entry.

## C09 — US TTF excludes extended session

US `Session.ALL` contains overnight/premarket/regular/after-hours bars.

Expected:

```text
PAQS 30m TTF uses only 09:30–16:00 America/New_York
```

## C10 — HK lunch not bridged

Expected:

```text
11:30–12:00 bar
13:00–13:30 bar
```

No synthetic `12:00–13:00` or cross-lunch candle.

## C11 — Current W1 incomplete

During the middle of a market week:

Expected:

```text
current partial W1 excluded
last completed W1 used
```

## C12 — Regular-session gap semantics

US previous regular close 100, overnight trades through 101–103, next regular open 104.

Expected:

```text
REGULAR_SESSION_OPEN_GAP exists
```

with extended-session overlap metadata recorded separately.

## C13 — Future corporate action injection resistance

A historical `as_of=t` is evaluated before a later split/dividend effective date.

Expected:

```text
future action does not alter PAQS state at t
```

## C14 — Unsupported adjustment basis

Daily and minute histories have inconsistent/unknown corporate-action adjustment basis.

Expected:

```text
PAQS unavailable / unsupported
```

not a fabricated structure.

## C15 — Score cannot override hard gate

PAQS returns `NO_TRADE` because T1 RR fails while a hypothetical quality score is high.

Expected:

```text
entry_advisory remains NO_TRADE
```

---

# 13. Locked vs still open after v0.3.1

## 13.1 Research semantics now locked

The following are no longer open design gaps inside the PAQS v0.3.1 research model:

1. two-stage Entry / RR timing;
2. conditional Entry vs Holder advisory states;
3. hard invalidation is setup-specific and snapshotted;
4. T1 is the nearest relevant structural obstacle and cannot be skipped for RR shopping;
5. initial equity MTF mapping is `W1 → D1 → 30m regular-session`;
6. initial Gap semantic is `REGULAR_SESSION_OPEN_GAP`;
7. PAQS requires explicit point-in-time corporate-action adjustment semantics;
8. PAQS state machine is primary; Composite/Quality Score is derived and cannot override structural hard gates.

## 13.2 Still VARIANT / future research

The following remain intentionally unapproved:

```text
T1 full vs partial take-profit
structural trailing stop
runner to T2
position sizing
portfolio exposure / correlation risk
countertrend setups under HTF UNCERTAIN
H1 / H4 aggregation
extended-session structural triggers
trendline/channel/measured-move engines
probability calibration
exact Quality / Composite Score formula
```

These are not allowed to leak into an initial implementation as silent defaults.

---

# 14. Engineering implication and staging

v0.3.1 confirms that PAQS is larger than a score calculator. The safest future engineering sequence remains incremental.

A candidate decomposition for later user approval is:

```text
TASK-006A — PAQS Structure Foundation
ATR
Pivot / Swing
Key Level geometry
Zone
Range
W1/D1/30m timeframe primitives
Base Regime
no-lookahead / adjustment metadata

TASK-006B — PAQS Event Engine
Breakout / Failed Breakout
Retest
Role Flip
Transition
Trigger
Follow-through

TASK-006C — PAQS Setup & Risk Geometry
Setup families
Setup expiry
Invalidation snapshots
Target selection
RR
Entry revalidation

TASK-006D — PAQS Advisory / Presentation Layer
Entry advisory
Holder advisory
Reason codes
immutable signal/advisory ledger
optional later Quality / Composite Score mapping
Dashboard integration
```

This is **research staging only**, not approved Task scope. No implementation branch or Codex work is authorized by this document.

---

# 15. Final completeness statement

After v0.3.1, PAQS can distinguish three different questions:

```text
NEW ENTRY:
Is there a valid setup, trigger, structural stop, structural target and acceptable entry-time RR?

IF ALREADY HELD:
Is the original thesis structurally valid, merely weakened, at a target decision point, or invalidated?

SCORE / RANKING:
How strong or high-quality is an already-defined structural state relative to other research candidates?
```

The model therefore no longer treats one numerical score as the strategy itself.

The minimum closed advisory lifecycle is:

```text
NO_SETUP
→ WATCH_LONG
→ ENTRY_PENDING_REVALIDATION
→ LONG_READY / WAIT_RETEST / NO_TRADE

if conceptually held:
THESIS_VALID
→ HOLD_WITH_WARNING
→ TARGET_REACHED_REVIEW
or
→ EXIT_IF_HELD on hard structural invalidation
```

Profit-taking execution variants and position sizing remain separate future research by design.

> **Price Action semantics, information timing, structural provenance and historical state may not drift merely to improve backtest results.**

---

**End — PAQS v0.3.1 Completeness Lock**
