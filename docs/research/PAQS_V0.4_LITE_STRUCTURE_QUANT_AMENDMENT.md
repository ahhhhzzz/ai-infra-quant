# PAQS v0.4 Lite — Structure Simplification & Quant Confirmation Amendment

Status: **RESEARCH DEFINITION AMENDMENT — USER-APPROVED DIRECTION; IMPLEMENTATION CONTRACT STILL REQUIRED**

Repository: `ahhhhzzz/ai-infra-quant`

Accepted TASK-006B authoritative SHA: `96747041ef0ff8c00937c5dd5e80cb4c5c28c17c`

Parent research review:

- `docs/research/TASK_006B_STRUCTURE_STABILITY_REVIEW.md`

Validation evidence:

- branch `validation/006b-real-market-structure-checkpoint`
- HEAD `b23d1c196eda957ab04dc0f79c477e2ee1a6e471`

This amendment defines the simplified research target that should replace the over-complex current Structure semantics before TASK-006C. It does **not** authorize product-code changes by itself.

---

## 1. Product objective

The MVP does not attempt to encode the complete discretionary reasoning of an expert naked-price-action trader.

The objective is a stable, bounded and explainable decision-support loop:

```text
Market Data
  -> W1 Context
  -> D1 Current Structure
  -> M30 Trigger Structure
  -> Breakout / Failed Breakout / Retest / Follow-through
  -> Setup
  -> Quant Confirmation / Veto
  -> Invalidation
  -> Target
  -> RR
  -> Entry / Holder Advisory
```

The system should prefer `UNCERTAIN`, `WATCH_LONG`, `WAIT_RETEST` or `NO_TRADE` over false precision.

No profitability guarantee, probability estimate, machine-learning model or autonomous trading is introduced.

---

## 2. What remains the PAQS core

The following PAQS concepts remain first-class:

- completed-data-only semantics;
- ATR as volatility/distance scale;
- confirmed directional-change Pivot;
- extreme reference distinct from confirmation reference;
- HH / HL / LH / LL / EH / EL labels;
- support/resistance as areas rather than exact lines;
- D1 Range;
- conservative Regime semantics;
- future TASK-006C Breakout / Failed Breakout / Retest / Follow-through;
- future TASK-006D Setup / Invalidation / Target / RR / next-open revalidation;
- future advisory states including `WATCH_LONG`, `ENTRY_PENDING_REVALIDATION`, `LONG_READY`, `VALID_SETUP_BUT_POOR_ENTRY`, `WAIT_RETEST`, `NO_TRADE` and `SETUP_EXPIRED`;
- deterministic Decimal arithmetic;
- no lookahead;
- explainability.

The amendment removes complexity that did not demonstrate sufficient current-decision value.

---

## 3. Removed / simplified structure concepts

### 3.1 No independent Micro + Major pair on every timeframe

PAQS v0.4 Lite uses **one primary Pivot engine per timeframe**.

The v0.3.1 model of six independent Pivot state machines:

```text
W1 Micro + Major
D1 Micro + Major
M30 Micro + Major
```

is retired for the Lite MVP.

Role-specific Pivot scales preserve the useful intent of the old hierarchy without allowing two independent engines to seed into incompatible phases.

Initial research defaults:

```text
W1 pivot_atr_lambda  = 1.8
D1 pivot_atr_lambda  = 1.8
M30 pivot_atr_lambda = 1.0
```

These values preserve the old coarse-vs-trigger intent. They are research defaults, not return-optimized parameters.

The following accepted mechanics remain unchanged unless a later implementation contract explicitly says otherwise:

```text
ATR period = 14
pivot_min_bars = 2
confirmation uses completed Close
extreme uses source-bar High/Low
same-bar extreme/confirmation ambiguity cannot confirm
UNSEEDED initialization remains deterministic
```

There is no retrospective Pivot promotion.

---

## 4. Timeframe responsibilities

### 4.1 W1 — Context

W1 answers only:

```text
What is the broad structural context?
```

W1 provides:

- ATR;
- one Pivot sequence;
- swing labels;
- broad `BULL_TREND` / `BEAR_TREND` / `UNCERTAIN` context;
- recent structural swing references for explanation.

W1 does **not** need a separate Micro structure for the MVP.

W1 persistent multi-zone clustering is not required for v0.4 Lite.

### 4.2 D1 — Setup Structure

D1 is the main current-structure layer.

D1 provides:

- ATR;
- one Pivot sequence;
- swing labels;
- active support/resistance Zones;
- active Range;
- `BULL_TREND` / `BEAR_TREND` / `RANGE` / `UNCERTAIN`.

D1 is the primary source of decision-relevant Zones for later Event and Setup logic.

### 4.3 M30 — Trigger Structure

M30 answers:

```text
What is the recent local turning structure around the D1 setup/zone?
```

M30 provides:

- ATR;
- one finer Pivot sequence;
- swing labels / local direction;
- trigger references used later by TASK-006C.

M30 does **not** maintain an independent persistent Zone universe in the Lite MVP.

M30 does **not** need a separate coarse Major engine.

---

## 5. Bounded Current Structure Horizon

Provider history availability and current-structure memory are separate concepts.

The provider or future local store may retain much more history than the Structure Engine is allowed to use for the current snapshot.

Initial research windows:

| Timeframe | Warm-start bars | Active structure bars | Total current-evaluation window |
|---|---:|---:|---:|
| W1 | 26 | 104 | 130 |
| D1 | 60 | 252 | 312 |
| M30 | 40 | 160 | 200 |

Interpretation:

```text
older provider/store history
        -> ignored by current Structure snapshot
warm-start segment
        -> ATR initialization + deterministic Pivot seeding only
active segment
        -> current structural facts
```

The full current-evaluation window is always selected relative to the current completed terminal bar.

### 5.1 Origin invariance requirement

Once the required current-evaluation window is available, adding arbitrary older leading history must not change the current active Structure snapshot.

This directly replaces the accidental v0.3.1 semantic:

```text
provider maximum history origin -> Pivot state for today
```

with:

```text
explicit bounded current-evaluation window -> Pivot state for today
```

AVGO-style 2020-to-2026 path-lock is not acceptable under v0.4 Lite.

### 5.2 Warm-start facts

Warm-start bars may establish ATR and Pivot state.

Pivots confirmed before the active segment are not active current Pivots.

At most the minimum deterministic pre-active comparable references required to label the first active High/Low may be retained internally as anchors.

Such anchors:

- may support the first active swing label;
- may not create a current Zone;
- may not count as a current Range touch;
- may not independently determine current Regime.

### 5.3 History sufficiency

The first implementation should require the complete declared evaluation window for a fully valid v0.4 Lite timeframe.

If the required window is unavailable:

```text
structure_history_status = INSUFFICIENT_FOR_LITE_HORIZON
```

and downstream logic must fail conservatively rather than silently reverting to unbounded-provider-origin behavior.

A later amendment may define partial-history support for newly listed equities; it is not required for the first stabilized MVP.

---

## 6. Pivot recency / staleness

v0.4 Lite does not allow a Pivot outside the active structure horizon to define current Regime.

This bounded eligibility is the primary staleness rule.

Additionally expose a diagnostic warning when the latest confirmed active Pivot is older than half of the active horizon:

```text
W1 warning threshold  = 52 active bars
D1 warning threshold  = 126 active bars
M30 warning threshold = 80 active bars
```

The warning does not by itself fabricate a reversal.

A directional Regime still requires sufficient active two-sided swing evidence. A hidden warm-start anchor cannot substitute for missing active current structure.

---

## 7. D1 Zone semantics — current relevance, not historical accumulation

Zones remain important PAQS concepts, but only D1 maintains clustered decision Zones in the Lite MVP.

Unchanged starting semantics:

```text
High Pivot -> resistance observation
Low Pivot  -> support observation
candidate = 1 independent touch
confirmed = >=2 independent touches
zone_min_touch_separation_bars = 5
zone_cluster_epsilon_atr = 0.50
zone_min_halfwidth_atr = 0.15
zone_max_halfwidth_atr = 0.75
zone_merge_iou = 0.50
```

### 7.1 Active-horizon eligibility

Only D1 active-segment Pivots may create current Zone observations.

Warm-start anchors cannot create current Zones.

### 7.2 Zone expiry

A confirmed Zone is decision-active only when its latest accepted independent reaction/touch is no older than:

```text
zone_max_age_bars = 126 D1 sessions
```

This is the initial Lite research default and corresponds to half the D1 active horizon.

Age is measured from the latest accepted independent touch.

A new valid reaction resets the Zone age.

Expired Zones may be reported as diagnostic history during validation but are excluded from:

- current decision-relevant Zone output;
- Range construction;
- TASK-006C Breakout/Retest source eligibility;
- TASK-006D Setup / Target / Invalidation source eligibility.

### 7.3 Maximum current decision Zone set

After recency filtering, expose at most:

```text
2 nearest relevant Support Zones
2 nearest relevant Resistance Zones
```

Maximum D1 decision-zone count:

```text
4
```

A Support Zone whose entire geometry is above current price is not a current Support decision zone before role-flip semantics exist.

A Resistance Zone whose entire geometry is below current price is not a current Resistance decision zone before role-flip semantics exist.

Role flip remains a TASK-006C Event lifecycle concern.

This cap is a product/current-decision boundary, not a statement that older historical levels never existed.

---

## 8. D1 Range semantics — recent box only

Range remains a D1 concept in the Lite MVP.

Initial preserved defaults:

```text
range_lookback_bars = 40
range_inside_ratio = 0.70
min_range_width_atr = 2.0
max_range_width_atr = 12.0
```

A current Range requires:

- one currently active Support Zone;
- one currently active Resistance Zone;
- at least two independent Support reactions;
- at least two independent Resistance reactions;
- alternating side reactions;
- latest Close inside Range geometry;
- inside-ratio and width gates.

### 8.1 Critical recency change

Every reaction/touch used to prove the current Range must occur inside the same last-40-D1-bar Range evaluation window.

Old Zone history may not be combined with recent closes to manufacture a current Range.

### 8.2 Range continuity metric

Validation must distinguish:

1. semantic `RANGE` Regime continuity;
2. exact versioned Range-ID continuity.

A Zone version/touch update changing an ID must not automatically be reported as a new semantic box if the current geometry and `RANGE` state remain materially continuous.

---

## 9. Base Regime

### W1

Allowed current context states:

```text
BULL_TREND
BEAR_TREND
UNCERTAIN
```

### D1

Allowed current setup-structure states:

```text
BULL_TREND
BEAR_TREND
RANGE
UNCERTAIN
```

Active D1 Range retains precedence.

### M30

M30 may expose:

```text
BULL_TREND
BEAR_TREND
UNCERTAIN
```

for local trigger structure; no M30 Range is required in the Lite MVP.

Regime cannot be created from warm-start anchors alone.

No hysteresis/debounce is added yet. Regime churn must be re-measured after the upstream simplification before deciding whether any additional stability rule is necessary.

---

## 10. Quant Confirmation Layer — PAQS remains primary

The Lite MVP adds a small deterministic quantitative evidence layer.

Hard governance rule:

> **PAQS is primary. Quantitative factors may confirm, veto or downgrade an existing PAQS Setup, but may never create a Setup.**

Therefore:

```text
NO_SETUP + strong quant factors != Setup
```

No weighted composite score, probability, ML classifier or return-trained optimizer is introduced.

### 10.1 Trend confirmation

D1 deterministic trend evidence:

```text
EMA20
EMA50
```

For a Long candidate:

```text
CONFIRM  if Close > EMA50 and EMA20 > EMA50
CONFLICT if Close < EMA50 and EMA20 < EMA50
NEUTRAL  otherwise
```

EMA uses completed D1 observations only.

### 10.2 Momentum confirmation

D1 momentum:

```text
ROC20 = Close[t] / Close[t-20] - 1
ROC60 = Close[t] / Close[t-60] - 1
```

For a Long candidate:

```text
CONFIRM  if ROC20 > 0 and ROC60 > 0
CONFLICT if ROC20 < 0 and ROC60 < 0
NEUTRAL  otherwise
```

Momentum is confirmation evidence, not a standalone Buy signal.

### 10.3 Extension / anti-FOMO filter

Define:

```text
extension_atr = (Close - EMA20) / ATR14
```

Initial research threshold for a Long candidate:

```text
max_extension_atr = 2.0
```

If:

```text
extension_atr > 2.0
```

then the candidate is `EXTENDED`.

The intended downstream behavior is a downgrade such as:

```text
VALID_SETUP_BUT_POOR_ENTRY
```

rather than chasing the move.

The threshold is a research default, not a return-optimized value.

### 10.4 Quant interaction with PAQS

Initial deterministic policy:

```text
PAQS Setup absent
    -> quant layer cannot run the decision into LONG_READY

PAQS Setup valid + EXTENDED
    -> cannot be LONG_READY at current price

PAQS Setup valid + Trend CONFLICT + Momentum CONFLICT
    -> quantitative veto -> NO_TRADE / filtered candidate with explanation

PAQS Setup valid + mixed CONFIRM/NEUTRAL evidence
    -> preserve PAQS candidate; continue to Invalidation / Target / RR gates

PAQS Setup valid + Trend CONFIRM + Momentum CONFIRM
    -> positive confirmation only; still cannot bypass PAQS, RR or next-open gates
```

Quant evidence is always exposed in explanations.

---

## 11. External historical validation data — zero OpenD research budget

Large-sample research validation must not consume the user's Futu/OpenD historical quota.

Separate the data roles:

```text
External internet historical provider
    -> research / calibration / robustness validation only

Futu OpenD
    -> production/local product current market-data path
    -> occasional final environment smoke only
```

External validation data must never silently become the authoritative production provider.

### 11.1 Preferred zero-OpenD research path

For the first v0.4 Lite validation harness, `yfinance` / Yahoo Finance may be used as an **ephemeral personal research provider**, subject to its then-current terms and availability.

Design-time observations on 2026-09-02:

- yfinance documents multi-ticker historical downloads;
- daily history supports multi-year periods;
- intraday intervals include 30m;
- yfinance documents that intraday history cannot extend beyond the last 60 days;
- yfinance states that it is an unofficial research/education tool and that Yahoo Finance data is intended for personal use;
- Yahoo exposes Hong Kong symbols such as `0700.HK` with historical daily prices.

References checked at design time:

- https://ranaroussi.github.io/yfinance/
- https://ranaroussi.github.io/yfinance/reference/yfinance.price_history.html
- https://legal.yahoo.com/us/en/yahoo/guidelines/ydn/index.html
- https://finance.yahoo.com/quote/0700.HK/history/

This provider is intentionally **not** a production dependency.

Do not commit bulk raw Yahoo market data into GitHub. Validation should fetch ephemerally and commit only reproducibility metadata, symbol lists, summary diagnostics and bounded human-review samples where permitted.

### 11.2 Fallback research providers

Official API alternatives may be evaluated if stronger availability/contracts are needed.

At design time:

- Alpha Vantage advertises global equity daily/weekly/monthly data with 20+ years of history, but full-length daily access is premium;
- EODHD advertises broad global EOD history, while its free plan is limited to 20 API calls/day and approximately one year of EOD history for arbitrary symbols.

These limitations make them fallback candidates rather than the default zero-cost broad validation path.

No external research provider is frozen forever by this amendment.

---

## 12. Expanded validation universe

The five-security OpenD checkpoint was sufficient to reveal design defects but is not enough for broad structural confidence.

The v0.4 Lite validation must use a fixed, declared sample of at least:

```text
>= 40 liquid equities total
>= 24 US
>= 16 HK
```

The sample should deliberately cover:

- mega-cap technology;
- semiconductors / AI infrastructure;
- high-volatility growth;
- industrials;
- financials;
- consumer;
- healthcare where available;
- energy where available;
- lower-volatility large caps;
- different observed bull, bear and range periods.

The symbol list must be fixed before running diagnostics to reduce cherry-picking.

Current five validation securities should remain included where supported:

```text
US.AVGO
US.VRT
US.NVDA
HK.09698
HK.00700
```

This is a structural robustness sample, not a training set for maximizing P&L.

---

## 13. Validation methodology

### 13.1 Broad D1 / W1

Use external historical daily data to derive D1 and W1 validation inputs.

Target at least two years of D1 history per security when available, while the current Structure snapshot must still obey the explicit bounded v0.4 Lite horizon.

### 13.2 M30

Use external 30m/intraday data where legally and technically available.

For yfinance, treat the documented last-60-day intraday window as the maximum research horizon rather than claiming deeper intraday history.

### 13.3 Required machine diagnostics

At minimum report:

- origin invariance;
- no-lookahead violations;
- current Pivot count and latest Pivot age;
- active Zone count;
- expired Zone count;
- Range fraction;
- semantic Range continuity;
- Regime fractions;
- Regime changes per 100 cutoffs;
- top Regime-churn outliers;
- small parameter perturbation diagnostics;
- external-provider quality/adjustment metadata.

### 13.4 Origin invariance acceptance

For the same terminal bar and same declared v0.4 evaluation window:

```text
full provider history
vs
exact required bounded window
```

must produce the same current active Structure result.

Older unused history may not affect current Pivot, Zone, Range or Regime facts.

### 13.5 No-lookahead acceptance

Required:

```text
0 confirmed-fact future-leak violations
```

under declared rolling-horizon semantics.

Rolling-window expiry itself is not a future rewrite; validation must compare only facts that remain eligible under both evaluated horizons.

### 13.6 Zone acceptance

By construction:

```text
active D1 decision Zones <= 4
```

No expired Zone may participate in current Range/Event/Setup decisions.

### 13.7 Regime churn

Regime churn remains a diagnostic rather than a P&L optimization target.

Any D1 security showing more than 20 Base-Regime state changes per 100 evaluated cutoffs should trigger focused semantic review before acceptance; this threshold is an outlier-review trigger, not an optimization target.

---

## 14. Parameter governance

The first Lite implementation must not grid-search parameters against returns.

Allowed research sensitivity checks are small perturbations around declared defaults, used only to detect pathological structural fragility.

Examples:

```text
W1/D1 pivot lambda: 1.7 / 1.8 / 1.9
M30 pivot lambda: 0.9 / 1.0 / 1.1
D1 zone epsilon: 0.45 / 0.50 / 0.55
zone max age: 100 / 126 / 160
extension ATR: 1.5 / 2.0 / 2.5
```

No variant may be selected because it produced the highest historical return during this stabilization work.

---

## 15. Quant validation is not model training

Terminology is important.

This work is:

```text
rule calibration
robustness validation
structural validation
```

It is not machine-learning training.

External data answers questions such as:

- does the same bounded definition behave reasonably across many securities?;
- is origin sensitivity eliminated?;
- are active Zones bounded and recent?;
- does Regime churn remain pathological?;
- are small parameter perturbations structurally tolerable?;

External data is **not** used to automatically learn a parameter set that maximizes backtested profit.

---

## 16. TASK sequencing impact

The intended sequence becomes:

```text
TASK-006B deterministic implementation
    PASS / integrated at 96747041...

PAQS v0.4 Lite research amendment
    current step

Focused 006B-Lite remediation contract
    NOT YET AUTHORIZED

006B-Lite implementation + independent review

Expanded external-data structure checkpoint

006B-Lite semantic acceptance

TASK-006B1 Local Market Data Store & Replay Foundation

TASK-006C Event Engine

TASK-006D Setup / Risk + minimal Quant Confirmation Layer

TASK-006E Advisory / Dashboard
```

The Quant Confirmation Layer belongs downstream of an existing PAQS Setup and should be implemented with TASK-006D or a bounded split of TASK-006D if implementation size requires it.

It must not be pulled forward into Structure remediation.

---

## 17. Explicit non-goals

This amendment does not authorize:

- machine learning;
- neural networks;
- probability prediction;
- P&L parameter optimization;
- automated security selection;
- live broker account access;
- order placement/modification/cancellation;
- real position import;
- real trade reconciliation;
- autonomous trading;
- replacing Futu as the product's current-market provider;
- implementing TASK-006C before Structure acceptance.

---

## 18. Required approval before implementation

Before any production-code remediation begins, the project owner must explicitly approve this v0.4 Lite amendment or request changes to its concrete semantics.

Only after approval should a focused implementation Task Contract be created from the accepted authoritative base.

**End — PAQS v0.4 Lite Structure Simplification & Quant Confirmation Amendment**