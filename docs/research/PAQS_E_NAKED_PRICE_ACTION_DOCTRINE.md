# PAQS-E — Naked Price Action Strategy Doctrine
## LLM-Native Expert Reasoning Branch

**Status:** RESEARCH / STRATEGY DOCTRINE DRAFT  
**Implementation authority:** NONE  
**Branch role:** PAQS-E strategy authority candidate for Product Manager review  
**Execution model:** LLM-native reasoning, provider-agnostic  
**Current preferred model provider:** OpenAI, as a product/provider choice only  

> This document is intentionally **not** a Python state-machine specification. Its purpose is to preserve the highest-value Price Action reasoning distilled from public trading commentary while remaining structured enough for a future LLM to execute consistently, explainably, and under strict point-in-time constraints.

This document does **not** claim to reproduce any trader's private strategy, parameters, win rate, or proprietary process. It is a public-evidence-derived research doctrine.

---

# 0. Why PAQS-E needs a new doctrine

PAQS v0.1 → v0.2 → v0.3.x increasingly formalized discretionary Price Action concepts so that deterministic code could execute them.

That work produced valuable engineering guardrails, but it also introduced an important distortion risk:

```text
Price Action idea
    ↓
need to code it
    ↓
need one exact definition
    ↓
need thresholds / windows / enums
    ↓
rich contextual judgment becomes rigid machine logic
```

PAQS-E no longer has that constraint.

PAQS-E is executed by an LLM reasoning engine. Therefore its primary strategy authority should preserve **semantic trading doctrine**, not force the model to behave like a Python interpreter.

The intended separation is:

```text
PAQS-E Doctrine
    = what a strong Price Action analyst should reason about

PAQS-E Guardrails
    = what the analyst is never allowed to cheat on

PAQS-Q
    = the separate deterministic machine-quant branch
```

Accordingly:

- PAQS v0.3.x remains valuable as a formalization and guardrail reference;
- PAQS v0.3.x is **not** the complete strategy brain for PAQS-E;
- exact ATR thresholds, clustering distances, fixed lookbacks and deterministic Pivot/Zone state machines are not automatically binding on PAQS-E unless separately adopted as factual preprocessing or explicit hard guardrails;
- PAQS-E should preserve the original Price Action hierarchy: **context → structure → location → setup → confirmation → invalidation → target → RR → advisory**.

---

# 1. Evidence hierarchy

Every PAQS-E principle should be understood through three evidence classes.

## 1.1 E — Explicit public evidence

Ideas repeatedly and directly expressed in public trading commentary.

Examples retained as high-confidence doctrine:

- first classify the market rather than predict every next bar;
- use multiple timeframes;
- distinguish trend, range and reversal/transition structure;
- focus on breakouts, breakdowns, failed breakouts, secondary confirmation and follow-through;
- exit when the structural thesis is invalidated;
- prefer attractive risk/reward and avoid chasing after excessive extension;
- use important support/resistance/decision levels;
- update judgment as new bars arrive rather than make unconditional long-horizon forecasts.

## 1.2 I — Inferred recurring pattern

Ideas consistently inferred from multiple public cases but not treated as exact private rules.

Examples:

- `顺大逆小`: align with the larger structure and use smaller-timeframe correction/reversal for timing;
- structure and location generally matter more than conventional indicator signals;
- failed breakout near a meaningful boundary is more informative than the same pattern at a random location;
- channel quality, trend deterioration, repeated pushes and local momentum loss can modify confidence;
- old breakout levels, gaps and prior swing levels can become decision levels depending on context.

## 1.3 H — Engineering / research hypothesis

Rules invented primarily to make implementation deterministic.

Examples:

- exact `0.15 ATR` breakout buffer;
- exact Pivot lambda;
- exact number of bars in a reclaim window;
- exact Zone merge tolerance;
- exact Range lookback;
- exact minimum RR;
- exact anti-FOMO threshold.

**PAQS-E governance rule:**

> E and I define the strategy doctrine. H may support tooling, testing or deterministic preprocessing, but must not silently replace higher-level Price Action reasoning.

This is deliberately different from PAQS-Q, where H-style exact rules are necessary for deterministic execution.

---

# 2. PAQS-E identity

PAQS-E is:

> **an LLM-native Naked Price Action Expert Reasoning Engine for read-only investment decision support.**

It is not:

- a deterministic rule engine;
- an autonomous trader;
- a broker execution system;
- a machine-learning probability model;
- a weighted technical-indicator score;
- a generic financial chatbot;
- a human discretionary chart-review workflow.

Human chart interpretation is **not** part of PAQS-E runtime.

The human user remains outside the strategy engine and decides whether to allocate capital after seeing PAQS-E and, where available, PAQS-Q output.

---

# 3. The core doctrine in one sentence

> **First understand what kind of market exists and where price sits inside that structure; then wait for recognizable Price Action at an important location, demand confirmation rather than prediction, define where the thesis is wrong and where the next structural objective lies, and only act when the resulting entry is worth the risk.**

Equivalent compact chain:

```text
CONTEXT
→ STRUCTURE
→ LOCATION
→ EVENT
→ SETUP
→ TRIGGER
→ FOLLOW-THROUGH
→ INVALIDATION
→ TARGET
→ RR / ENTRY QUALITY
→ ADVISORY
```

The order is conceptual, not a requirement that every analysis literally instantiate every enum.

---

# 4. Doctrine Rule 1 — Diagnose the market; do not predict every bar

PAQS-E must begin by asking:

> What market am I looking at **now**?

Useful qualitative states include:

```text
BULL_TREND
BEAR_TREND
RANGE
TRANSITION / REVERSAL_CANDIDATE
TREND_DETERIORATING
UNCERTAIN
```

These are reasoning states, not mandatory one-hot machine labels.

The model should prefer `UNCERTAIN` over fabricated precision when the structure is conflicting or incomplete.

Forbidden framing:

```text
"The next bar will rise."
"This must reach X."
"The market will reverse here because the pattern resembles one old case."
```

Preferred framing:

```text
"The larger structure remains bullish, but the current correction has not yet produced a valid reversal trigger."
"The market is still a range until the boundary is meaningfully resolved."
"The bearish thesis weakens if price reclaims this decision level and follows through."
```

---

# 5. Doctrine Rule 2 — Multi-timeframe analysis is hierarchical, not voting

PAQS-E should normally reason with three roles:

```text
HTF = broad context / major structure
STF = setup structure / correction / range / breakout context
TTF = trigger / local timing
```

The roles do not need to be fixed to one universal set of intervals. The Market Snapshot Contract may supply an instrument-appropriate mapping.

Core principle:

```text
HTF bullish
+
STF correcting
+
TTF turns bullish
→ potential trend-pullback long
```

This is often more meaningful than requiring all three timeframes to already be bullish.

Forbidden:

```text
Daily +80
4H -30
1H +60
average = +36.7
therefore BUY
```

The LLM must explain **how the timeframes interact**, especially when they disagree.

Examples:

- HTF bull + STF correction can be constructive;
- HTF bear + STF bull may simply be a countertrend rally;
- HTF range is not automatically overturned by a small TTF bull sequence;
- HTF uncertainty should lower conviction unless a specific strategy doctrine justifies participation.

---

# 6. Doctrine Rule 3 — Structure and location come before conventional indicators

The LLM should first reason from price behavior:

- swings;
- repeated reactions;
- trend/range geometry;
- breakout and reclaim behavior;
- impulse vs correction;
- support/resistance/decision levels;
- gap context;
- channel behavior;
- trendline or structural boundary where visually and contextually meaningful.

Conventional quantitative features such as EMA, ROC or volume may be supplied as context, but they must not create a setup that Price Action does not support.

```text
NO PAQS-E SETUP
+
strong EMA / ROC
≠
LONG_READY
```

Indicators may confirm, conflict with, or contextualize the LLM's reasoning. They do not replace it.

---

# 7. Doctrine Rule 4 — Key Level reasoning is semantic, not an enum lookup

PAQS-E must identify a **small number of decision-relevant levels**, not enumerate every historical pivot.

A Key Level is a price or zone where the answer to one of these questions may change:

- Is the current structure still valid?
- Has a range actually broken?
- Has an old resistance become support?
- Has the market reclaimed a failed breakdown?
- Is the setup now too close to resistance to justify entry?
- Has the next meaningful target been reached?

Potential sources include, but are not limited to:

```text
major swing high / low
range boundary
repeated support / resistance reaction
old breakout / breakdown origin
role-flip area
gap edge
trendline / channel boundary
prior high-volume or visually important decision area
measured-move objective
```

These are **reasoning cues**, not a closed enumeration.

For each important level the LLM should explain:

```text
price / zone
role
why it matters
relevant timeframe
what changes if price accepts above/below it
```

A precise single-number level should only be used when the structure genuinely supports that precision. Otherwise use a zone.

---

# 8. Doctrine Rule 5 — Context > candle

A strong bullish or bearish bar is not a standalone trade.

A bar matters because of:

```text
where it occurs
what preceded it
what structure it attacks or defends
whether it changes local market behavior
whether the next bars confirm it
```

Therefore:

```text
large green candle at random location
≠
valid long setup
```

But:

```text
failed breakdown at major support
+
bullish reclaim
+
strong close
+
subsequent follow-through
```

may be highly meaningful.

---

# 9. Doctrine Rule 6 — Break Attempt ≠ Breakout

PAQS-E must distinguish:

- a wick/excursion through a level;
- a meaningful close/acceptance beyond the level;
- an initially valid breakout that later fails;
- a breakout that receives continuation;
- a breakout that is successfully retested.

The model should not mechanically promote every intrabar cross to a structural breakout.

The key question is:

> Did price merely probe beyond the boundary, or did the market begin accepting price on the other side?

No exact ATR buffer is universally mandatory for PAQS-E unless the product explicitly supplies one as a hard factual rule.

---

# 10. Doctrine Rule 7 — Failed Breakout is a high-priority Price Action event

A failed breakdown / failed breakout is most meaningful when it happens at an important structural location.

Bullish example:

```text
important support / range low
↓
price trades below it
↓
price fails to sustain below
↓
reclaim
↓
local bullish trigger
↓
follow-through
```

The LLM should reason about:

- importance of the violated boundary;
- depth of the excursion;
- speed and quality of the reclaim;
- whether trapped participants are plausible from the price action;
- whether local structure actually turns;
- whether continuation follows.

A failed breakout event is **not automatically a trade**.

```text
EVENT ≠ SETUP ≠ ADVISORY
```

---

# 11. Doctrine Rule 8 — Right-side confirmation is preferred over blind bottom/top guessing

PAQS-E should distinguish:

```text
"This looks like a bottom"
```

from:

```text
"The structure has produced right-side evidence that the bottom thesis is becoming actionable"
```

Typical right-side evidence may include:

- break of a meaningful lower high / upper boundary;
- reclaim of a decision level;
- retest and hold;
- continuation after the break;
- local reversal structure on the trigger timeframe.

This does not mean every trade must wait for the most conservative confirmation variant. It means the model must explicitly state **what has and has not yet been confirmed**.

---

# 12. Doctrine Rule 9 — Trigger is ignition; follow-through proves the move has participation

A trigger says:

> something has changed enough to become actionable.

Follow-through asks:

> did the market continue behaving consistently with that change?

Examples of weak/no follow-through:

- breakout with almost no extension;
- large directional bar followed immediately by opposite engulfing;
- rapid close back into the prior zone;
- repeated inability to continue after the trigger.

The LLM should be able to output:

```text
TRIGGER_NOT_CONFIRMED
TRIGGER_CONFIRMED_FOLLOWTHROUGH_PENDING
FOLLOWTHROUGH_WEAK
FOLLOWTHROUGH_CONFIRMED
```

without inventing exact bar-count rules unless explicitly supplied.

---

# 13. Doctrine Rule 10 — Impulse vs correction matters

PAQS-E should evaluate whether movement is:

```text
impulsive
or
corrective
```

Useful qualitative cues:

### Impulse

- greater directional displacement;
- less overlap;
- persistent closes in the direction of travel;
- relatively efficient movement.

### Correction

- more overlap;
- smaller displacement relative to the prior impulse;
- may last longer without destroying the higher-timeframe structure;
- often terminates near a relevant decision level.

A bullish HTF does not become bearish merely because the STF is correcting.

The LLM should compare the **quality of the impulse and correction**, not only their direction.

---

# 14. Doctrine Rule 11 — Channel quality and trend deterioration are contextual evidence

PAQS-E may reason about:

### Healthy / narrow trend behavior

- repeated higher lows in a bull trend;
- shallow pullbacks;
- persistent closes in the trend direction;
- limited penetration of the opposite structural side.

### Deterioration / widening behavior

- increasingly deep pullbacks;
- widening swing amplitude;
- less orderly highs/lows;
- weaker follow-through;
- increasing two-sided volatility.

Output should distinguish:

```text
TREND_DETERIORATING
```

from:

```text
TREND_REVERSED
```

Deterioration lowers trend confidence and may increase the relevance of countertrend evidence, but does not automatically prove reversal.

Trendline/channel reasoning is allowed in PAQS-E even though it was deferred from strict v0.3 code formalization.

---

# 15. Doctrine Rule 12 — Three-push / wedge / exhaustion patterns are context, not automatic reversal calls

Repeated pushes with deteriorating progress may indicate exhaustion.

Useful cues may include:

- three directional swings;
- decreasing displacement;
- weaker efficiency;
- failed breakout/reclaim on the final push;
- rejection;
- declining follow-through;
- subsequent break of the nearest opposing micro structure.

The model must not say:

```text
third push exists
→ automatic reversal trade
```

Instead:

```text
exhaustion candidate
+
location
+
right-side trigger
+
follow-through
→ actionable reversal candidate
```

---

# 16. Core Setup Family A — Trend Pullback Continuation / “顺大逆小”

This is a core PAQS-E setup.

## 16.1 Thesis

```text
larger timeframe trend remains structurally valid
+
smaller timeframe corrects against that trend
+
correction reaches a meaningful structural location
+
trigger timeframe stops deteriorating and turns back with the larger trend
```

For a Long:

```text
HTF bullish context
↓
STF pullback / correction
↓
important support / old breakout / structural area
↓
TTF bearish micro structure weakens or breaks
↓
bullish trigger
↓
follow-through / retest evidence as applicable
```

## 16.2 High-quality reasoning cues

- HTF trend remains intact;
- correction is smaller/less efficient than prior bullish impulse;
- pullback reaches a meaningful location rather than ending randomly;
- TTF stops making meaningful new lows;
- latest local lower high is broken or equivalent reversal evidence appears;
- follow-through supports the reversal;
- entry is not excessively extended from the structural stop;
- structural target leaves sufficient room.

## 16.3 Invalidation doctrine

The invalidation should answer:

> What price behavior proves that this was not merely a correction inside the larger bullish thesis?

Typical sources:

- loss of the support thesis;
- decisive failure below the pullback structural low;
- invalidation of the relevant HTF/STF swing structure.

Do not widen invalidation after entry simply because a farther support later looks convenient.

## 16.4 Target doctrine

Possible targets include:

- prior HTF swing high;
- next major structural resistance;
- trend continuation / measured-move area when contextually justified;
- channel objective;
- later trailing structural management.

The nearest meaningful obstacle must not be ignored just to manufacture attractive RR.

---

# 17. Core Setup Family B — Range Failed Breakout Reversal

This is a core PAQS-E setup.

## 17.1 Thesis

For a Long:

```text
meaningful range / support context
↓
price breaks below the boundary
↓
market fails to sustain below
↓
reclaim
↓
bullish trigger
↓
follow-through
```

The same visual failure at a random mid-range location should receive less weight than failure at an important boundary.

## 17.2 Invalidation doctrine

The natural question is:

> If price truly breaks below the failed-break extreme / structural support after the reclaim, does the reversal thesis still make sense?

Usually the answer is no.

## 17.3 Target doctrine

Typical structural objectives:

- range midpoint as an intermediate decision point;
- opposite side of the range;
- next structural resistance beyond the range if a genuine transition develops.

If the entry occurs too close to the range midpoint/opposite boundary and the available RR is poor, PAQS-E should output `NO_TRADE` or `VALID_SETUP_BUT_POOR_ENTRY` rather than force the trade.

---

# 18. Core Setup Family C — Right-Side Structural Breakout

This is a core PAQS-E setup.

## 18.1 Thesis

```text
prior bear / range / bottoming context
+
credible bottom or accumulation-like structure candidate
+
meaningful structural resistance / last important LH is broken
+
right-side continuation evidence appears
```

Potential execution interpretations:

```text
breakout confirmation
or
breakout → retest → hold → continuation
```

PAQS-E should state which variant the current evidence supports rather than mixing them retrospectively.

## 18.2 Invalidation doctrine

Potential invalidation evidence:

- sustained rejection back inside the old range;
- failure of the retest structure;
- loss of the breakout-origin thesis;
- loss of the bottoming structure.

## 18.3 Anti-FOMO doctrine

A correct breakout thesis can still be a bad current entry.

PAQS-E must distinguish:

```text
SETUP_VALID
```

from:

```text
ENTRY_QUALITY_GOOD
```

If price has already expanded too far from a rational structural invalidation point, preferred output is:

```text
VALID_SETUP_BUT_POOR_ENTRY
WAIT_RETEST
```

rather than chasing.

---

# 19. Auxiliary Price Action patterns

The following may modify context or produce secondary candidates, but are not automatically standalone trades:

```text
narrow channel
widening / broadening channel
trendline break
three-push / wedge
failed breakout
role flip
gap reaction
measured move
double top / double bottom
impulse/correction deterioration
```

The LLM must always connect the pattern to:

```text
context + location + confirmation + invalidation + target
```

Pattern naming alone is insufficient.

---

# 20. Structural invalidation doctrine

Every actionable PAQS-E thesis must answer:

> **Where and under what condition is this thesis no longer valid?**

The answer should be structural and explanatory, not merely a percentage stop.

Required fields:

```text
invalidation_level_or_zone
invalidation_condition
invalidation_timeframe
invalidation_reason
```

The LLM should distinguish:

### Soft warning

Examples:

- micro structure weakens;
- follow-through deteriorates;
- price re-enters a weaker location;
- a wick probes through a boundary but acceptance is not confirmed.

### Hard invalidation

The structural premise itself is broken.

PAQS-E may use deterministic code-supplied hard-close/buffer rules as a product guardrail, but the **choice of which structural boundary matters** remains a strategy reasoning question.

Hard invalidation may never be moved farther away after the fact to rescue a losing thesis.

---

# 21. Structural target doctrine

Every actionable PAQS-E thesis should identify the next meaningful structural objective.

Possible target sources:

```text
opposite range boundary
previous major swing
major support/resistance
important gap edge
measured-move objective
channel projection
other clearly explained structural decision level
```

Rules:

1. target must be explainable from information available at the decision time;
2. nearest meaningful obstacle must be acknowledged;
3. the LLM may identify T1 / T2, but must not skip T1 because T2 gives prettier RR;
4. a target is a **decision point**, not automatically a universal full-exit instruction;
5. target choice must be preserved in the immutable decision record.

---

# 22. RR and entry-quality doctrine

PAQS-E must care about both:

```text
Is the direction thesis reasonable?
```

and:

```text
Is the current price worth entering?
```

These are separate questions.

The LLM should propose:

```text
entry_reference / entry_zone
structural invalidation
T1 / T2
```

A deterministic calculator should validate arithmetic RR whenever possible.

For Long:

```text
RR_T1 = (T1 - Entry) / (Entry - Invalidation)
```

PAQS-E should not treat one universal RR threshold as sacred unless the product declares one. The strategic doctrine is:

> **risk must be justified by realistic structural reward, and chasing should be rejected when entry geometry deteriorates.**

---

# 23. Bar-by-bar updating doctrine

PAQS-E must reason incrementally.

Preferred mental model:

```text
day by day
bar by bar
```

A new bar can:

- strengthen the existing thesis;
- weaken it;
- confirm a trigger;
- remove a setup;
- create a transition;
- reach a target;
- hard-invalidate the thesis.

The model must not rewrite the past decision after seeing the outcome.

Each new analysis is a **new revision**, not an edit of the old historical call.

---

# 24. No-trade is a first-class decision

PAQS-E is not required to manufacture a trade on every requested symbol.

Valid outputs include:

```text
NO_SETUP
WATCH_LONG
WATCH_SHORT
ENTRY_PENDING_REVALIDATION
LONG_READY
SHORT_BIAS / AVOID_LONG where product permits
VALID_SETUP_BUT_POOR_ENTRY
WAIT_RETEST
NO_TRADE
SETUP_EXPIRED
```

The model should prefer `NO_TRADE`, `WATCH`, or `WAIT_RETEST` when:

- structure is unclear;
- location is poor;
- confirmation is missing;
- RR is unattractive;
- price is excessively extended;
- multiple timeframes conflict without a clear thesis;
- the setup has already passed without entry.

---

# 25. Holder advisory is separate from entry advisory

PAQS-E does not need access to a broker account.

It should answer two separate questions:

## New-entry question

> Is there a good new entry **now**?

## Conditional holder question

> If this thesis were already held, is it still structurally valid?

Holder states:

```text
THESIS_VALID
HOLD_WITH_WARNING
TARGET_REACHED_REVIEW
EXIT_IF_HELD
```

A stock may simultaneously have:

```text
entry_advisory = VALID_SETUP_BUT_POOR_ENTRY
holder_advisory = THESIS_VALID
```

Human meaning:

> existing holder may still have a valid thesis, while a new buyer should not chase.

This distinction is essential.

---

# 26. PAQS-E output contract

PAQS-E should produce **structured output plus a concise human explanation**.

A future provider adapter should enforce a schema equivalent to the following logical object.

```text
strategy_family: PAQS-E
strategy_doctrine_version
model_provider
model_id
prompt_version
market_snapshot_hash
symbol
market
as_of_timestamp

one_line_thesis

context:
  htf_state
  stf_state
  ttf_state
  regime_summary
  trend_quality

current_location:
  description
  location_quality

key_levels[]:
  price_or_zone
  role
  timeframe
  rationale
  what_changes_if_broken_or_reclaimed

price_action:
  current_event
  transition_state
  trigger_status
  followthrough_status
  impulse_correction_read
  channel_or_exhaustion_context

setup:
  family
  direction
  stage
  why_it_qualifies
  missing_confirmation
  alternative_interpretation

entry:
  advisory
  reference_or_zone
  chase_risk
  wait_condition

invalidation:
  level_or_zone
  condition
  timeframe
  reason
  hard_or_soft

targets:
  t1
  t1_reason
  t2_optional
  t2_reason_optional

risk_reward:
  rr_t1
  rr_t2_optional
  rr_quality

holder_advisory

uncertainty:
  level: LOW | MEDIUM | HIGH
  conflicting_evidence[]
  data_limitations[]

next_evidence_needed[]
reason_codes[]
explanation
```

## 26.1 Required user-facing information

The Dashboard should be able to display, at minimum:

1. **现在是什么行情？**
2. **大周期 / 中周期 / 触发周期分别怎么看？**
3. **真正重要的支撑、压力、决策位在哪里？为什么？**
4. **当前价格处在什么位置？**
5. **当前属于什么 Setup？进行到哪一步？**
6. **Trigger 出现了吗？Follow-through 怎么样？**
7. **现在适合新开仓、观察、等回踩，还是不交易？**
8. **如果已经持有，逻辑仍然成立吗？**
9. **哪里证明判断错了？**
10. **T1 / T2 在哪里，为什么？**
11. **当前 RR 是否值得？**
12. **是否已经涨太多、存在 FOMO / poor entry？**
13. **有哪些反对当前 thesis 的证据？**
14. **下一步需要看到什么，观点才会升级或失效？**
15. **一句大白话结论。**

This is the PAQS-E product output target.

---

# 27. LLM execution contract

PAQS-E strategy reasoning belongs to the LLM.

Deterministic code remains responsible for factual infrastructure:

```text
market-data acquisition
point-in-time cutoff
session/calendar semantics
corporate-action handling
bar aggregation / completeness
basic arithmetic
market snapshot hashing
schema validation
ledger persistence
```

The LLM is responsible for:

```text
context interpretation
key-level selection and explanation
multi-timeframe synthesis
setup identification
Price Action event interpretation
trigger / follow-through interpretation
structural invalidation selection
structural target selection
entry-quality reasoning
holder-thesis reasoning
final advisory explanation
```

The code layer must not silently replace PAQS-E reasoning with PAQS-Q mechanical rules.

---

# 28. Provider-agnostic model architecture

PAQS-E is a strategy family, not an OpenAI-specific strategy.

Architecture:

```text
PAQS-E Doctrine
      ↓
Market Snapshot Contract
      ↓
LLM Reasoning Provider Interface
      ↓
OpenAI / Anthropic / Google / future provider
      ↓
PAQS-E Structured Output
```

Current product preference may set:

```text
default_provider = OpenAI
```

But the immutable decision record should always save:

```text
provider
model
model/version identifier where available
prompt version
strategy doctrine version
snapshot hash
```

No multi-model voting is required for the initial implementation.

---

# 29. Strict As-Of / no-lookahead rule

PAQS-E must only see information legitimately available at the requested analysis cutoff.

For historical replay at time `t`:

```text
model_input = data legitimately available <= t
```

Forbidden:

```text
show the full future chart
then ask the LLM what it "would have done" at t
```

The model may receive precomputed facts only if those facts were themselves generated point-in-time safely.

This is a hard guardrail inherited from the v0.3 formalization work.

---

# 30. Immutable Decision Ledger

Every PAQS-E output is a historical claim that must be preserved.

Minimum identity:

```text
decision_id
symbol
as_of_timestamp
market_snapshot_hash
strategy_doctrine_version
prompt_version
model_provider
model_id
raw_structured_output
created_at
```

If the model changes its view later:

```text
new decision revision
```

not:

```text
overwrite old decision
```

This allows the project to answer:

> **What did PAQS-E actually say at the time?**

rather than producing hindsight narratives.

---

# 31. Anti-hindsight and anti-rationalization guardrails

LLMs are unusually good at creating plausible explanations after an outcome is known.

Therefore PAQS-E must enforce:

1. strict As-Of snapshots;
2. immutable decisions;
3. target and invalidation snapshots;
4. no retroactive widening of invalidation;
5. no retroactive target shopping;
6. model/provider/prompt version tracking;
7. an explicit `alternative_interpretation` field;
8. explicit conflicting evidence;
9. explicit `UNCERTAIN` / `NO_TRADE` permission;
10. historical evaluation on unseen future outcomes.

---

# 32. What PAQS-E inherits from v0.3.x as hard guardrails

The following formalization work remains highly valuable and should generally remain hard:

```text
completed / point-in-time information only
no lookahead
Event ≠ Setup ≠ Advisory
Break Attempt ≠ automatically Breakout
Failed Breakout requires genuine failure/reclaim semantics
Retest is post-breakout behavior
Trigger and Follow-through are distinct concepts
entry question ≠ holder question
historical decisions are immutable
invalidation cannot be widened after the fact to rescue a thesis
nearest meaningful obstacle cannot be ignored solely to improve RR
Quality Score ≠ probability
NO_TRADE is valid
product is read-only decision support
```

These are **discipline rules**, not an instruction to recreate every v0.3 deterministic state machine inside the LLM.

---

# 33. What is explicitly NOT binding on PAQS-E merely because v0.2/v0.3 formalized it

Unless separately promoted to a PAQS-E hard rule, the following should be treated as engineering hypotheses or preprocessing choices:

```text
one exact Pivot lambda
one exact micro/major Pivot architecture
one exact Zone clustering distance
fixed Zone touch count as the only way to identify a key level
one exact Zone age
one exact Range lookback
one exact breakout ATR buffer
one exact reclaim bar count
one exact follow-through bar window
one exact retest tolerance
one universal minimum RR
one universal anti-FOMO ATR threshold
closed Key-Level source enum
requirement that every important trendline/channel concept be generated by deterministic geometry
```

The LLM may use code-supplied measurements as evidence, but should retain semantic Price Action judgment.

---

# 34. PAQS-E vs PAQS-Q

The two branches are parallel.

```text
PAQS-E
= LLM-native semantic Price Action reasoning

PAQS-Q
= deterministic machine-quant Price Action subset
```

Neither automatically supersedes the other.

Possible product flow:

```text
Market Data
    ↓
Shared Point-in-Time Data Layer
    ├────────────────────┐
    ↓                    ↓
PAQS-Q                PAQS-E
Machine Quant         LLM Expert
    ↓                    ↓
Quant Advisory        Expert Advisory
    └──────────┬─────────┘
               ↓
        Dashboard Comparison
               ↓
        Human Capital Decision
```

PAQS-Q may act as scanner/baseline.

PAQS-E may analyze:

- manually selected symbols;
- PAQS-Q candidates;
- current holdings entered manually at the product layer;
- watchlist symbols.

The Dashboard should surface disagreement rather than average the two into one synthetic score.

---

# 35. PAQS-E evaluation should test reasoning quality, not only P&L

A future PAQS-E Gold Set should contain point-in-time cases with manually reviewed labels/ranges for:

```text
broad context
important key levels
reasonable setup family
setup stage
acceptable invalidation region
reasonable target candidates
entry-advisory band
holder-advisory band
important conflicting evidence
```

Evaluation dimensions:

```text
As-Of compliance
key-level relevance
setup classification quality
context / MTF reasoning quality
trigger/follow-through interpretation
invalidation quality
target quality
target-shopping violations
FOMO / chase rate
NO_TRADE discipline
reasoning consistency
prompt/model sensitivity
reasoning-to-outcome expectancy as a later research metric
```

Do not reduce PAQS-E evaluation to:

```text
which model generated the highest historical return
```

until the strategy's reasoning validity and reproducibility are established.

---

# 36. Canonical compact doctrine for runtime extraction

The following compact block is intended for later prompt extraction. It summarizes the strategy without the engineering history.

```text
PAQS-E CORE DOCTRINE

1. Diagnose, do not predict every next bar.
2. Read multiple timeframes hierarchically: higher timeframe = context, middle = setup, lower = trigger.
3. Structure and location matter more than conventional indicators.
4. Identify only the decision-relevant key levels and explain why each matters.
5. A candle or pattern without context/location is not a trade.
6. Distinguish probe/break attempt, accepted breakout, failed breakout, retest and continuation.
7. Failed breakout at an important boundary is a high-priority reversal event, but still requires context and confirmation.
8. Prefer right-side evidence over blind top/bottom guessing.
9. Trigger and follow-through are separate; lack of follow-through weakens the thesis.
10. Compare impulse with correction; a correction against an intact higher-timeframe trend is not automatically a reversal.
11. Use channel quality, trend deterioration and repeated-push exhaustion as contextual evidence, not automatic signals.
12. Core setups: trend pullback / 顺大逆小, range failed-break reversal, right-side structural breakout.
13. Every actionable thesis must define structural invalidation: where and how the idea becomes wrong.
14. Every actionable thesis must define the next realistic structural target(s).
15. Do not skip a nearer meaningful obstacle just to improve RR.
16. A valid setup can still be a poor new entry; do not chase excessive extension.
17. Entry advisory and holder advisory are different questions.
18. NO_TRADE / WATCH / WAIT_RETEST are valid and often preferable to weak trades.
19. Update bar by bar; never rewrite an old decision using future information.
20. State conflicting evidence and an alternative interpretation.
21. Use only point-in-time information from the supplied Market Snapshot.
22. Never claim calibrated probability unless a separate validated probability model exists.
23. The final answer must be structured, explainable and auditable.
```

---

# 37. Canonical reasoning questions for the LLM

Every PAQS-E analysis should internally answer these questions in order:

```text
Q1. What is the higher-timeframe market context?
Q2. What is the setup-timeframe structure?
Q3. What is the trigger-timeframe structure?
Q4. Which 1–4 price areas actually matter for the current decision, and why?
Q5. Where is current price relative to those levels?
Q6. What Price Action event is occurring: correction, breakout, failed breakout, retest, deterioration, exhaustion, none?
Q7. Does a recognized setup family exist?
Q8. What stage is the setup in?
Q9. Has a trigger occurred?
Q10. Is there follow-through, weak follow-through, or still pending evidence?
Q11. What is the strongest alternative interpretation?
Q12. What exact structure/behavior would invalidate the thesis?
Q13. What are T1 and optional T2, and why are they legitimate structural objectives?
Q14. Does the current entry geometry still offer acceptable reward relative to structural risk?
Q15. Is the price already too extended to justify a new entry?
Q16. What is the new-entry advisory?
Q17. If already held, what is the holder advisory?
Q18. What evidence should be watched next to upgrade, downgrade or invalidate the thesis?
```

This question set is preferred over forcing the model through dozens of machine-state enums.

---

# 38. Instructions to Product Manager ChatGPT

This file is a strategy-expert memo for product architecture review.

Please treat the following as the intended product correction:

1. PAQS-E's strategy brain should be this **semantic Naked Price Action Doctrine**, not the full deterministic machinery of PAQS v0.3.1.
2. PAQS v0.3.x should be repositioned primarily as **guardrail / formalization / audit reference** for PAQS-E.
3. PAQS-Q remains the deterministic machine branch and may continue developing bounded mechanical definitions separately.
4. Do not make PAQS-Q's mechanical thresholds silently binding on PAQS-E.
5. Build PAQS-E as an LLM-native, model-provider-agnostic engine.
6. Current preferred provider may be OpenAI, but the strategy must not be vendor-locked.
7. Preserve a deterministic Market Snapshot / As-Of / data-quality layer beneath the LLM.
8. Require structured PAQS-E output matching the product information requirements in Section 26.
9. Require an immutable PAQS-E Decision Ledger.
10. Do not implement multi-model voting in the first version.
11. Do not connect broker execution or autonomous trading.
12. Do not convert this doctrine directly into a giant Python state machine; doing so would recreate the design problem this document is intended to fix.

Before implementation, Product Manager should propose:

```text
PAQS-E Market Snapshot Contract
PAQS-E provider abstraction
PAQS-E prompt/spec packaging
PAQS-E structured output schema
PAQS-E decision-ledger schema
PAQS-E historical As-Of evaluation harness
PAQS-E dashboard presentation
```

Each requires explicit user approval through the project's normal Task Contract governance.

---

# 39. Final strategy position

PAQS-E should preserve the advantage of a strong reasoning model:

> **understand context, select what matters, compare alternative interpretations, and reason about structure semantically.**

It should preserve the advantage of the prior PAQS formalization work:

> **no hindsight, no hidden future information, explicit invalidation, honest targets, honest RR, immutable historical decisions, and permission not to trade.**

The intended synthesis is therefore:

```text
Original Price Action essence
        +
LLM semantic reasoning
        +
strict v0.3-style anti-cheating guardrails
        +
point-in-time deterministic market facts
        =
PAQS-E
```

**End — PAQS-E Naked Price Action Strategy Doctrine**
