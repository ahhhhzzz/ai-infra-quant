# AIInfraStrategy v1 Specification

Status: **PROPOSED / RESEARCH_UNVALIDATED**; not approved and not implemented. Future scope is EOD-only under `docs/ROADMAP.md` decision `EOD-001`.

Proposed strategy identity: `AIInfraStrategy` / `1.0.0`

Approval gate: `APPROVE PHASE 1` does not approve this document. Strategy implementation is forbidden until the user separately sends the exact instruction `APPROVE STRATEGY SPEC V1` and Phase 3 is authorized.

## 1. Purpose and safety boundary

The strategy runs only on completed daily market sessions, ranks a long-only, cash-account AI-infrastructure watchlist, and emits one explainable Composite Quant Score per tracked security plus advisory recommendations. It does not submit, approve, modify, cancel, or fill a real order. The user alone decides whether to trade and executes any real trade manually in the broker's official client.

The formulae, weights, thresholds, sizing options, and golden cases below remain an unapproved research proposal. This Roadmap refactor changes only the EOD/manual-execution boundary and does not approve or freeze the proposal.

The formulas are research hypotheses. This document makes no claim of profitability, predictive validity, or future performance. Status remains `RESEARCH_UNVALIDATED` through Phase 4 backtesting and until adequate subsequent forward observation is reviewed.

All calculations are deterministic and point-in-time. Inputs must have `available_at <= data_as_of`; provider records selected by a run are pinned in a dataset manifest/hash. No missing value is fabricated, forward-filled across a missing trading session, replaced with zero, or filled with information published later.

The initial symbols, caps, pullback zones, capital, and inception date are parameters attached to database assignments, not constants inside strategy code.

## 2. Numeric and time conventions

- Calculations use `Decimal` with at least 38 significant digits. Raw/gate values persist with at least 18 fractional digits; stored/display rounding never feeds a gate, and UI rounding occurs only after all decisions.
- Natural log, square root, and exponentiation use Decimal operations at the same declared context; binary float is forbidden.
- A trading day is a completed session in the security's versioned exchange calendar. Session `t` is the session containing `data_as_of`, and only a final bar available by the cutoff may be used.
- Comparisons are strict unless stated. Equality with a moving average does not satisfy `>`.
- Price bars must be unique and contiguous for all required scheduled sessions. A missing/duplicate/invalid bar makes the affected leaf unavailable.
- M3/M6 use total-return-adjusted close (`TRC`). MA/ATR/drawdown/confirmation use split-adjusted, dividend-unadjusted OHLC (`SAO`, `SAH`, `SAL`, `SAC`). Raw OHLC and adjustment provenance remain stored.
- Returns and ratios are fractions: `0.10` is 10%.

## 3. Required input context

For each security/run, `StrategyContext` supplies:

- security ID, session/calendar/timezone, `data_as_of`, immutable price-row IDs and adjustment versions;
- at least 220 split-adjusted sessions plus the histories required for momentum normalization (Section 5); minimum normalized M6 requires approximately 379 contiguous closes, while a full 756-observation M6 reference window requires approximately 883 contiguous closes;
- point-in-time valuation/fundamental inputs and provenance;
- active manual/data-assisted risk flags as known at the cutoff;
- current strategy state, confirmed PaperFills or reconciled ManualRealTradeRecords, current position, allocation cap, portfolio equity/cash, FX observation, and legal-quantity metadata/capabilities;
- parameter-set ID/hash and strategy version;
- no broker SDK or provider-native object.

Required price validation: OHLC values are positive, `SAH >= max(SAO, SAC, SAL)`, `SAL <= min(SAO, SAC, SAH)`, volumes are non-negative when present, and adjustment factors are positive. Invalid data is not repaired inside the strategy.

## 4. Base indicators

### 4.1 Simple moving averages

For `n` completed sessions:

```text
MA_n(t) = (1 / n) * sum(SAC_i, i=t-n+1..t)
```

Required: `MA20`, `MA50`, and `MA200`. The current session is included.

MA200 slope over 20 sessions:

```text
MA200_SLOPE20(t) = MA200(t) / MA200(t-20) - 1
```

This needs 220 contiguous split-adjusted closes.

### 4.2 True range and ATR14

For session `i > first`:

```text
TR_i = max(
  SAH_i - SAL_i,
  abs(SAH_i - SAC_(i-1)),
  abs(SAL_i - SAC_(i-1))
)
```

Wilder initialization and recursion:

```text
ATR14_14 = mean(TR_1 .. TR_14)
ATR14_i  = (13 * ATR14_(i-1) + TR_i) / 14, for i > 14
```

The dataset manifest pins the starting bar. Production calculation warms up with all contiguous bars provided, at least 220, so ATR does not change merely because a caller shortened the request window.

### 4.3 60-session high and drawdown

```text
HIGH60(t) = max(SAH_i, i=t-59..t)
DD60(t)   = SAC_t / HIGH60(t) - 1
```

`DD60 <= 0`. It uses highs, not closes.

## 5. Momentum components

### 5.1 Horizon returns

M3 is 63 trading sessions and M6 is 126 trading sessions. Horizon return is simple total return:

```text
R_N(t) = TRC_t / TRC_(t-N) - 1
```

Thus M3 needs 64 closes and M6 needs 127 closes. Simple return is chosen because the result is directly interpretable; log returns are used only to estimate volatility.

### 5.2 Realized volatility

For the same horizon `N`, define daily log total returns:

```text
r_i = ln(TRC_i / TRC_(i-1))
mean_r = sum(r_i) / N
s_N = sqrt(sum((r_i - mean_r)^2) / (N - 1))
RV_N = s_N * sqrt(252)
```

Use `N=63` for M3 and `N=126` for M6. This is sample standard deviation (`N-1`) and 252-session annualization.

### 5.3 Risk-adjusted momentum

```text
VOL_FLOOR = 0.01
RAM_N(t) = R_N(t) / max(RV_N(t), VOL_FLOOR)
```

The 1% annualized floor prevents division by zero and unstable explosion for near-constant test/data series. A non-positive price or invalid return makes the component unavailable. The raw return, realized volatility, floor-applied flag, RAM, normalized score, and source coverage are all output.

### 5.4 Own-history normalization

Each RAM component is normalized against only that security's prior point-in-time RAM observations calculated with the same strategy/data methodology.

1. Select the most recent at most 756 eligible observations strictly before `t`.
2. Require at least 252 eligible observations. Otherwise the normalized component is unavailable.
3. Compute the 5th and 95th percentiles of the reference values using the Type-7 rule. For sorted values `x[0..n-1]`, `h=(n-1)p`, `j=floor(h)`, `g=h-j`, and `Q_p=(1-g)x[j]+g*x[j+1]` (last index handled naturally).
4. Winsorize every reference and the candidate to `[Q_0.05, Q_0.95]`.
5. If all winsorized references are equal, score is `50`.
6. Otherwise use the empirical midrank percentile:

```text
L = count(reference < candidate)
E = count(reference = candidate)
MomentumScore = 100 * (L + 0.5 * E) / n
```

A candidate below/above every reference scores 0/100 before the winsor clipping effect. No cross-sectional values enter this absolute normalization.

Outputs:

```text
M3 = Normalize(RAM_63)
M6 = Normalize(RAM_126)
```

Because each prior M6 RAM observation itself requires 127 closes, the minimum 252 prior observations plus the current candidate require approximately 379 contiguous closes (`126 + 252 + 1`). A full 756-observation prior reference window requires approximately 883 closes (`126 + 756 + 1`). Missing scheduled sessions increase the required raw span and cannot be forward-filled.

## 6. Trend component

Trend is the weighted sum of binary leaves:

| Condition at `t` | Points |
|---|---:|
| `SAC > MA20` | 10 |
| `SAC > MA50` | 15 |
| `SAC > MA200` | 25 |
| `MA20 > MA50` | 10 |
| `MA50 > MA200` | 25 |
| `MA200_SLOPE20 > 0` | 15 |

With complete inputs, `TrendScore` is 0-100. For coverage reporting, an unavailable leaf contributes neither points nor coverage; the partial score is the available-point result divided by available possible points and multiplied by 100.

The hard primary entry filter is independent of the score:

```text
SAC_t > MA200(t) AND MA50(t) > MA200(t)
```

Missing `SAC`, `MA50`, `MA200`, calendar, or adjustment provenance blocks entry. `SAC < MA200` and `MA50 < MA200` together are a severe trend failure used by exit rules.

## 7. Drawdown component

The reference pullback magnitudes are parameters `L0` (shallow edge) and `U0` (deep edge), both positive fractions with `0 < L0 < U0`:

| Initial assignment | `L0` | `U0` |
|---|---:|---:|
| AVGO | 0.07 | 0.15 |
| VRT | 0.10 | 0.18 |
| HK.09698 | 0.12 | 0.25 |

They are defaults for these assignments only, not claims about current prices or automatic buy levels.

Historical-volatility scaling uses the median of the security's prior 252 available `RV63` observations:

```text
v = clip(RV63_t / median(previous_252_RV63), 0.75, 1.50)
L = L0 * v
U = U0 * v
a = ATR14_t / SAC_t
D = min(0.60, U + max(0.05, 2*a))
p = -DD60_t
```

All inputs, including 252 prior RV observations, are required. If `D <= U` after invalid inputs, the component is invalid. Score is the following continuous piecewise function:

```text
p <= 0:           20
0 < p < L:        20 + 80 * p / L
L <= p <= U:      100
U < p < D:        100 * (D - p) / (D - U)
p >= D:           0
```

This rewards a volatility-scaled pullback inside an established trend, not the largest fall. `p >= D` is a falling-knife entry block regardless of composite score. Drawdown cannot authorize entry unless the hard trend filter and confirmation also pass.

## 8. Valuation component

Valuation uses only point-in-time observations with source/provenance. Every metric uses its own prior history as available at each historical cutoff. Percentile normalization uses Section 5.4's Type-7 winsor/midrank method with up to 20 quarterly observations and a minimum of 12. For a lower-is-better multiple, `CheapPercentile(x)=100-Percentile(x)`; for a higher-is-better yield/quality metric, use `Percentile(x)`.

### 8.1 Historical valuation (`H`, 40%)

Leaves:

- forward P/E: lower is better; requires positive value;
- EV/EBITDA: lower is better; requires positive value;
- FCF yield: higher is better.

`H` is the equal-weight mean of available leaf scores and requires at least two leaves to be scored. When that minimum is met, its scored subcoverage is available leaf count divided by 3. With fewer than two leaves, raw availability is reported separately but scored subcoverage is 0 and it has no score contribution.

### 8.2 Growth-adjusted valuation (`G`, 30%)

Using point-in-time forward EPS growth `g` as a fraction:

```text
PEG = forward_PE / (100 * g)
```

It is valid only when forward P/E and `g` are positive and their estimate horizon/methodology match. Lower PEG is better through own-history percentile. `G` coverage is 1 only when scored, otherwise 0.

### 8.3 FCF/capital efficiency (`F`, 20%)

Leaves are FCF yield and ROIC, both higher is better. `F` is the equal-weight mean of scored leaves and requires at least one. Scored subcoverage is scored leaf count divided by 2, or 0 when neither is scored.

### 8.4 Balance sheet (`B`, 10%)

Leaves are net-debt/EBITDA (lower is better, negative net cash allowed) and interest coverage (higher is better, positive). `B` is the equal-weight mean of scored leaves and requires at least one. Scored subcoverage is scored leaf count divided by 2, or 0 when neither is scored.

### 8.5 Valuation aggregation

For subcomponent weights `u={H:.40,G:.30,F:.20,B:.10}`, scored subcoverage `c_j`, and score `s_j`:

```text
C_V = sum(u_j * c_j)
ValuationScore = sum(u_j * c_j * s_j) / C_V, if C_V > 0
```

The missing share is not assigned a neutral or zero score. `C_V` is passed to composite coverage. Any `C_V < 1`, stale review, or unapproved fundamental review sets `requires_manual_review=true` and caps action at WATCH. Thus data cannot appear attractive merely because an unfavorable metric is absent.

Fundamental review is `APPROVED` only when a manual or data-assisted record has provenance, no active veto, and `reviewed_at` is no more than the configurable 30 calendar days before `data_as_of`. This age is a proposed default, not a claim about provider freshness.

## 9. Composite score and coverage

Top-level weights are fixed for v1:

```text
w_M6 = 0.30
w_M3 = 0.20
w_Trend = 0.20
w_Drawdown = 0.15
w_Valuation = 0.15
```

Component scored coverages:

- `C_M6=1` only when return, RV, and 252-observation normalization are valid; else 0.
- `C_M3=1` under the analogous requirements; else 0.
- `C_Trend` is the sum of available Trend leaf point weights divided by 100.
- `C_Drawdown=1` only when all Section 7 inputs are valid; else 0.
- `C_Valuation=C_V` from Section 8.

Let `A` be leaf-weighted component contributions that have a score:

```text
Coverage C = sum(w_i * C_i)
ObservedNumerator A = sum(w_i * C_i * Score_i)
ScoreEstimate = A / C, if C > 0, else null
ScoreLowerBound = A
ScoreUpperBound = A + 100 * (1 - C)
```

This does not silently impute missing data. The estimate is explicitly provisional whenever `C<1` and is accompanied by bounds.

Coverage status:

```text
COMPLETE: C >= 0.80
PARTIAL:  0.60 <= C < 0.80
INVALID:  C < 0.60
```

Hard gates override the numeric status:

- BUY/ACCUMULATE requires `C_M6=C_M3=C_Trend=C_Drawdown=C_Valuation=1`, valid current price/calendar/FX/legal-quantity metadata, and an approved current fundamental review.
- Missing price, calendar, required trend data, adjustment provenance, or FX makes any executable-sized recommendation invalid.
- Missing/partial valuation or fundamental review may leave coverage `COMPLETE`, but action is at most WATCH with `REVIEW_REQUIRED`.
- `PARTIAL` is at most WATCH. `INVALID` is `NO_SIGNAL` and `STAY_IN_CASH` for a non-holder.

Score band uses the unrounded estimate only after gates:

```text
>= 80: STRONG_BUY_CANDIDATE
>= 65: ACCUMULATE_CANDIDATE
>= 50: WATCH
<  50: AVOID
```

## 10. Confirmation layer

At least one confirmation must be true at `t`; all use split-adjusted bars available at the signal close.

1. **MA20 reclaim:** `SAC_(t-1) <= MA20_(t-1)` and `SAC_t > MA20_t`.
2. **Two sessions without a new low, then break:** for sessions `t-2` and `t-1`, each session low is greater than or equal to the minimum low of its preceding 20 sessions; and `SAC_t > SAH_(t-1)`.
3. **Previous five-session high break:** `SAC_t > max(SAH_(t-5)..SAH_(t-1))`.

The current bar cannot be used inside its own lookback comparison except as the breakout close. Equality is not a break. Without confirmation, an otherwise eligible candidate is `WAITING_FOR_CONFIRMATION` and action is WATCH/HOLD, never BUY/ACCUMULATE.

A confirmation is “fresh” for an entry/add through the next three completed sessions. An add requires a confirmation after the preceding tranche's last confirmed PaperFill or reconciled ManualRealTradeRecord.

## 11. Dual-momentum filter and relative priority

The opportunity-cost hurdle is a configured **annual effective hurdle rate** `h` with `h > -1`; default is `0.00` until a legitimate series or user value is configured. It is not silently fetched. Horizon hurdle:

```text
H_N = exp((N / 252) * ln(1 + h)) - 1
```

Entry is blocked for materially negative dual momentum only when all are true:

```text
R_63  < H_63  - 0.05
R_126 < H_126 - 0.05
TrendScore < 50
```

Across currently eligible watchlist securities, compute midrank percentile ranks of `RAM63` and `RAM126`; `RelativePriority=(rank63+rank126)/2`. Require at least two eligible securities. It sorts otherwise valid recommendations only. It never changes the absolute composite score, data status, target weight, or a block/veto. With fewer than two eligible names, priority is `UNAVAILABLE`.

## 12. Fundamental veto

An active, point-in-time flag with `blocks_new_buys=true` blocks ENTRY and ADD regardless of score. Flags require source, source record/manual actor, `available_at`, severity, reason, and review status. Unverified scraped news is not accepted as a verified flag.

For an existing holding:

- `MEDIUM`: HOLD, stop adding, and require review.
- `HIGH`: recommend REDUCE by 50% and require separate human approval.
- `CRITICAL`: recommend EXIT and require separate human approval.

These are recommendations only. A flag never sends or approves a real trade. If provenance is invalid/stale, the result is `REVIEW_REQUIRED`, not a fabricated no-risk outcome.

## 13. State machine and action precedence

Persistent strategy/holding states:

```text
WATCH -> ENTRY_READY -> TRANCHE_1 -> TRANCHE_2 -> TRANCHE_3 -> HOLD
HOLD/TRANCHE_* -> REDUCE -> HOLD or EXIT -> COOLDOWN -> WATCH
```

`ENTRY_READY`, `REDUCE`, and `EXIT` are advisory states. Tranche advancement and full exit occur only after a confirmed PaperFill or a reconciled ManualRealTradeRecord supplied in a later context. A Recommendation acknowledgement never advances state and never invokes a broker.

Evaluate one action per security/session in this precedence order:

1. invalid/missing hard price data -> `NO_SIGNAL`; holder action `HOLD_REVIEW`, non-holder `STAY_IN_CASH`;
2. critical/high fundamental response -> EXIT/REDUCE as Section 12;
3. severe trend EXIT rule;
4. portfolio/allocation risk REDUCE rule;
5. complete/current trend-and-score REDUCE rule;
6. active cooldown -> HOLD if residual position, otherwise STAY_IN_CASH;
7. eligible next tranche -> BUY for first tranche or ACCUMULATE for later tranche;
8. position exists -> HOLD;
9. complete score below 50 -> AVOID/STAY_IN_CASH;
10. otherwise WATCH.

### 13.1 Entry

For zero position, transition `WATCH -> ENTRY_READY` and emit BUY for tranche 1 only when all are true:

- full hard-gate coverage in Section 9 and `ScoreEstimate >= 65`;
- hard primary trend filter passes;
- `DrawdownScore >= 60` and `p < D`;
- at least one fresh confirmation;
- dual-momentum block is false;
- no buy-blocking risk/fundamental flag and current fundamental review is approved;
- cooldown is inactive;
- target legal quantity and tranche 1 legal quantity are positive and do not exceed settled available cash, allocation cap, or any risk constraint selected by the separately approved sizing policy.
- the primary position-sizing decision in Section 14 has been separately approved.

Score `>=80` changes the classification to strong candidate, not tranche count or automatic execution.

### 13.2 Add

An ADD to tranche 2 or 3 requires all entry conditions plus:

- the prior tranche is complete from confirmed cumulative paper/manual quantity;
- at least five completed sessions elapsed since its last confirmed paper/manual fact;
- a fresh confirmation occurred after that fact;
- current price is no more than one `ATR14` above the prior tranche's volume-weighted average confirmed paper/manual price;
- current holding and proposed tranche remain below target/cap/risk/cash limits.

A tranche is complete when confirmed cumulative paper/manual quantity reaches the current cumulative legal target in Section 14. A partial PaperFill below that cumulative target retains the current tranche state. Cancelling an internal PaperOrder remainder requires a new sizing decision; it does not pretend completion.

Stop adding when any add condition fails, score falls below 65, price/fundamental data becomes incomplete/stale, the primary trend filter fails, `p>=D`, a veto appears, cash/FX/fee policy is unavailable, or a portfolio risk limit binds. Stop-adding produces HOLD or WATCH, not an automatic sale.

### 13.3 Hold

With a positive position and no higher-precedence reduce/exit or eligible add, action is HOLD. Falling below an entry threshold alone does not force a sale.

### 13.4 Reduce

The following score-based triggers are eligible to recommend reducing 50% only when `score_status=COMPLETE`, `requires_manual_review=false`, and every input required by the approved score rule is current:

- `SAC < MA50` for two consecutive completed sessions and `ScoreEstimate < 50`; or
- score remains below 50 for five consecutive completed sessions.

Missing/stale/partial valuation or fundamental data, any `REVIEW_REQUIRED`, or an incomplete score produces `HOLD_REVIEW`, not a score-based sale.

Independent higher-precedence responses remain valid without the composite-score gate when their own evidence is current and valid:

- a HIGH provenance-valid fundamental flag may recommend REDUCE under Section 12;
- a hard portfolio-cap breach above 0.02 absolute may recommend a reduction to the cap;
- severe trend EXIT, a CRITICAL flag, or an approved non-tradability event follows Section 13.5.

For a cap breach, size is the reduction needed to return to the cap; a 50% target applies only when another eligible reduce trigger also applies. It never rounds above the position. After a confirmed reducing PaperFill or reconciled ManualRealTradeRecord, state returns to HOLD and another score/trend-based reduce cannot occur for ten sessions unless an EXIT condition or renewed portfolio limit breach occurs.

Reduce quantity is floored to a legal increment. If a one-share/one-lot or other discrete position yields zero legal reduce quantity, no paper-transaction/recommendation quantity is fabricated: status is `REDUCE_NOT_EXECUTABLE_DUE_TO_LOT_SIZE`. The strategy emits `HOLD_REVIEW` pending the user's choice to continue holding or manually exit outside the platform.

### 13.5 Exit

Recommend full legal EXIT when:

- `SAC < MA200` for two consecutive completed sessions and `MA50 < MA200` at `t`; or
- a CRITICAL, provenance-valid fundamental flag applies; or
- an approved delisting/non-tradability event requires closure.

Exit remains a separately reviewed user decision for manual action outside the platform. If the instrument cannot legally trade, action is `EXIT_REVIEW_REQUIRED` with no estimated quantity rather than a fictitious PaperFill.

### 13.6 Portfolio-risk response and rebalance

Strategy consumes risk-limit results but does not treat broker-observed buying power as execution authority or mutate allocations. A hard portfolio-risk block prevents entry/add. A cap breach may create the Section 13.4 reduce recommendation. There is no calendar rebalance and being underweight never causes a buy suggestion without the full entry/add signal.

### 13.7 Cooldown and re-entry

A confirmed full exit starts a 20-completed-session cooldown beginning after the exit session. During cooldown the action is STAY_IN_CASH for that security. After 20 sessions, state returns to WATCH; re-entry requires the complete current entry rule and a confirmation occurring after cooldown ends. No old confirmation is reused.

## 14. Position sizing and legal quantity — DECISION_REQUIRED

Initial assignment caps:

```text
AVGO 0.40, VRT 0.35, HK.09698 0.25
```

These are maxima, not target requirements. Cash may remain 100%. The primary sizing formula is deliberately not frozen by this proposal.

### 14.1 Option A — hard-stop risk-budget sizing

This option derives quantity from a risk budget divided by a stop distance, for example the previously proposed `risk_fraction=0.01` and `max(2*ATR, 0.08*price)`. It is valid only with a separately approved stop policy that is actually enforced and tested. Even then, gaps/slippage must be disclosed. Without an enforced stop, `stop_distance` and `risk budget` cannot be described as a guaranteed maximum loss.

The prior example demonstrates the conflict: a 1% equity risk fraction and minimum 8% distance cap notional exposure at `0.01/0.08=12.5%` of equity; a 30% first tranche is at most 3.75%, or HKD 750 for HKD 20,000—materially below the approximately HKD 2,400 illustration for 30% of a 40% cap.

### 14.2 Option B — target allocation with volatility scaling (recommended)

This option begins from a target allocation below the 40%/35%/25% maximum and scales it downward as ATR/historical volatility rises. Exact reference volatility, scaler/clamps, base target, and any secondary stress-loss cap remain parameters requiring approval. This better matches a staged long-only investment strategy and small portfolio, but it does not define a guaranteed maximum loss.

Recommendation: **Option B**, with a stress-loss/risk-budget calculation as a secondary cap if approved. Final selection and formula require `APPROVE STRATEGY SPEC V1`; this document does not silently select them.

### 14.3 Legal target and cumulative tranche algorithm

After the approved primary sizing model produces `Q_raw`, legal target quantity is:

```text
increment = smallest executable quantity increment under verified fractional/lot/odd-lot capabilities
Q_target = floor(Q_raw / increment) * increment
N = Q_target / increment  # non-negative integer legal units
raw cumulative units = [floor(0.30*N), floor(0.60*N), N]
cumulative targets = strictly increasing positive values from raw cumulative units
next suggested quantity = next cumulative target*increment - confirmed cumulative paper/manual quantity
```

Zero or duplicate cumulative targets are skipped. This adapts small targets into fewer executable tranches. `Q_target=1*increment` becomes one tranche (`SMALL_TARGET_SINGLE_TRANCHE`); `Q_target=2*increment` becomes cumulative targets `[1,2]` (`DISCRETE_TRANCHE_ADJUSTMENT`). The standard 30/30/40 shape is exact only when discrete units permit it.

Before every suggested paper transaction or manual-trade amount, recalculate/validate target, settled cash, allocation cap, approved risk/stress cap, fees/taxes/slippage buffer, currency/FX mode, minimum quantity/notional, tick, and capabilities. Estimated quantity is floored to the legal increment and may never make confirmed paper/manual holdings exceed `Q_target`. If no positive legal quantity exists, return `INSUFFICIENT_CAPITAL_FOR_MINIMUM_ORDER` and retain cash.

For reductions:

```text
desired_reduce = 0.50 * current_quantity
legal_reduce = floor(desired_reduce / increment) * increment
```

If `legal_reduce=0`, return `REDUCE_NOT_EXECUTABLE_DUE_TO_LOT_SIZE`; emit `HOLD_REVIEW` and require separate approval before converting the action to full EXIT.

## 15. Signal output

Every result contains:

- security ID, timestamp, `data_as_of`, strategy name/version, parameter hash, dataset hash;
- raw/adjusted indicator values and source row IDs;
- M6/M3 raw return, RV, RAM, normalized score;
- Trend/Drawdown/Valuation leaves, score and coverage;
- composite estimate, bounds, coverage and coverage status;
- candidate band, action, persistent state/current recommended state, confirmation(s);
- relative priority if available, target weight/quantity if legal;
- sizing decision/status and any `SMALL_TARGET_SINGLE_TRANCHE`, `DISCRETE_TRANCHE_ADJUSTMENT`, or `REDUCE_NOT_EXECUTABLE_DUE_TO_LOT_SIZE` reason;
- missing components, reason codes, active risk flags and `requires_manual_review`.

`confidence` is not a win probability. It is:

```text
confirmation_factor = 1 if confirmed, 0.5 if waiting, 0 if invalid
review_factor = 1 if approved/not required, 0.5 if review required, 0 if blocked/vetoed
confidence = Coverage * confirmation_factor * review_factor
```

It is used only to communicate evidence completeness, never to bypass a gate or scale a real-trade suggestion automatically.

## 16. Deterministic golden cases

Golden fixtures are independent declarative inputs. Implementations must match the unrounded expected Decimal result; displayed values below show sufficient precision. Tests must also perturb future records and prove earlier results do not change.

### G-01 — Momentum raw calculation

Given `TRC_(t-63)=100`, `TRC_t=110`, and the independently calculated 63-session annualized sample RV `0.20`:

```text
R63 = 110/100 - 1 = 0.10
RAM63 = 0.10 / 0.20 = 0.50
```

Expected floor-applied flag: false.

### G-02 — Volatility floor

Given `R63=0.02`, `RV63=0.005`:

```text
RAM63 = 0.02 / 0.01 = 2
```

Expected floor-applied flag: true.

### G-03 — Own-history percentile

Reference has exactly 252 values `x_i=i/100` for integers `i=-126..125`; Type-7 bounds are `Q05=-1.1345`, `Q95=1.1245`.

- candidate `0`: `L=126`, `E=1`, expected score `100*126.5/252 = 50.198412698412698...`;
- candidate `0.50`: `L=176`, `E=1`, expected score `70.039682539682539...`;
- all-equal reference: expected score exactly `50`.

### G-04 — Trend complete and failed gate

Case A: `SAC=110`, `MA20=105`, `MA50=100`, `MA200=90`, `MA200(t-20)=88`. All leaves true: score `100`; primary gate passes.

Case B: `SAC=95`, `MA20=100`, `MA50=98`, `MA200=96`, `MA200(t-20)=95`. Only `MA20>MA50`, `MA50>MA200`, and positive slope are true: score `10+25+15=50`; primary gate fails because `SAC<=MA200`.

### G-05 — Drawdown piecewise

Use AVGO `L0=.07`, `U0=.15`, `RV63/median=1`, `ATR/SAC=.025`; therefore `L=.07`, `U=.15`, and `D=.20`.

- `DD60=0`: score `20`;
- `DD60=-.035`: score `20+80*(.035/.07)=60`;
- `DD60=-.11`: score `100`;
- `DD60=-.175`: score `100*(.20-.175)/(.20-.15)=50`;
- `DD60=-.20`: score `0` and falling-knife entry block.

### G-06 — Valuation aggregation

With complete subcomponent scores `H=80`, `G=60`, `F=70`, `B=50`:

```text
ValuationScore = .4*80 + .3*60 + .2*70 + .1*50 = 69
C_V = 1
```

If B is entirely missing and all other subcomponents remain complete:

```text
C_V = .90
ValuationScore = (32+18+14)/.90 = 71.111111111111...
requires_manual_review = true
```

### G-07 — Complete composite

Scores: `M6=90`, `M3=70`, `Trend=80`, `Drawdown=60`, `Valuation=50`; all coverages 1.

```text
Score = .30*90 + .20*70 + .20*80 + .15*60 + .15*50 = 73.5
Coverage = 1
bounds = [73.5, 73.5]
band = ACCUMULATE_CANDIDATE
```

With all entry gates true and confirmation fresh: zero-position action BUY. Without confirmation: WATCH/`WAITING_FOR_CONFIRMATION`.

### G-08 — Missing valuation is not neutral

Use G-07's first four components and no valuation:

```text
A = 27+14+16+9 = 66
C = .85
Estimate = 66/.85 = 77.647058823529...
Lower = 66
Upper = 81
coverage status = COMPLETE
```

Despite `COMPLETE`, expected action is WATCH with `REVIEW_REQUIRED`; BUY/ACCUMULATE is blocked. With fresh confirmation, `confidence=.85*1*.5=.425`.

### G-09 — Coverage status boundaries

- `C=.800000000000` -> COMPLETE.
- `C=.799999999999` -> PARTIAL.
- `C=.600000000000` -> PARTIAL.
- `C=.599999999999` -> INVALID/NO_SIGNAL.

### G-10 — Confirmation lookback

- Previous close `99`, previous MA20 `100`, current close `101`, current MA20 `100.5`: MA20 reclaim true.
- Current close equal to current MA20: false.
- Prior five highs `[100,102,101,103,104]`, current close `104.01`: five-session break true; current close `104`: false.

### G-11 — Dual-momentum block

With configured `h=0`, `R63=-.06`, `R126=-.08`, and Trend `40`, all three block conditions are true: entry blocked. If Trend is `50` exactly, the strict `Trend<50` condition is false and this filter alone does not block.

### G-12 — State advances only on fills

Start WATCH, all entry rules true -> recommendation state ENTRY_READY/action BUY. A simulated PaperOrder event `SUBMITTED_SIMULATED` leaves persistent tranche state unchanged. A confirmed full tranche-1 PaperFill changes state to TRANCHE_1. A 40% partial PaperFill keeps the tranche incomplete and no tranche-2 recommendation is allowed.

### G-13 — Add timing

Last confirmed tranche fact is session 10. At session 14 only four completed sessions have elapsed: HOLD. At session 15, with a new post-fact confirmation and every other add condition true: ACCUMULATE next tranche. A confirmation from session 9 is not fresh and cannot authorize the add.

### G-14 — Complete score reduce and exit

- Two consecutive closes below MA50 plus a complete/current score `49.9999` and no review flag: REDUCE 50%, subject to legal quantity.
- Score exactly `50`: that reduce rule is false.
- Two consecutive closes below MA200 and `MA50<MA200`: EXIT recommendation regardless of entry score; manual execution approval still required.

### G-15 — Cooldown

Full exit confirmed on session 100. Sessions 101-120 are cooldown (20 sessions) and cannot enter. State returns to WATCH after session 120; the first eligible signal is session 121 and requires a confirmation from session 121 or the permitted fresh window beginning after cooldown, never a pre-exit confirmation.

### G-16 — Position-sizing conflict remains a decision

Given `E=20000 HKD`, `risk_fraction=.01`, `P=100 USD`, `ATR=5 USD`, `f=7.8 HKD/USD`, allocation cap `.40`, available cash `20000 HKD`, and zero fee buffer solely for this arithmetic fixture:

```text
stop_distance=max(10,8)=10 USD
risk_budget=200 HKD
unit_risk=78 HKD
Q_risk=2.564102564102...
Q_cap=8000/780=10.256410256410...
Q_cash=20000/780=25.641025641025...
```

For whole-share step 1, Option A would produce `Q_target=2`. The arithmetic proves why the old formula conflicts with the allocation example; it is not an approved sizing output. The cumulative algorithm would adapt a separately approved two-share target under G-19.

### G-17 — No look-ahead/restatement

A valuation record has `period_end=2026-06-30`, `published_at=2026-09-10`, `available_at=2026-09-10`. A run at `2026-08-31` must not select it. A restatement available `2026-10-01` must not change either the August run or its dataset hash.

### G-18 — One-share target

`Q_target=1`, `increment=1`, raw cumulative units `[0,0,1]`. Positive distinct cumulative targets are `[1]`; next suggested quantity is one share minus confirmed cumulative paper/manual quantity. Expected status: `SMALL_TARGET_SINGLE_TRANCHE`. It never returns zero or exceeds one share.

### G-19 — Two-share target

`Q_target=2`, `increment=1`, raw cumulative units `[0,1,2]`. Positive distinct cumulative targets are `[1,2]`; suggestions are one share then `2-confirmed_cumulative_quantity`. Expected status: `DISCRETE_TRANCHE_ADJUSTMENT` and no suggestion above two cumulative shares.

### G-20 — Fractional target

`Q_target=0.003`, verified fractional `increment=0.001`, so `N=3`; raw cumulative units `[0,1,3]`. Cumulative targets are `[0.001,0.003]`. With `0.001` confirmed, next quantity is `0.002`. Expected status: `DISCRETE_TRANCHE_ADJUSTMENT`.

### G-21 — HK board-lot target

With verified `increment=100` shares and `Q_target=200`, `N=2`; cumulative targets are `[100,200]`. After 100 confirmed shares, next quantity is 100. No 30-, 40-, or 60-share invalid board-lot order is produced.

### G-22 — One-share/one-lot reduce

For current quantity equal to one legal increment, desired 50% reduction is `0.5*increment` and legal floor is zero. Expected: no suggested quantity, `REDUCE_NOT_EXECUTABLE_DUE_TO_LOT_SIZE`, action `HOLD_REVIEW`. Full EXIT requires a separate user decision outside the platform.

### G-23 — Incomplete score cannot sell

Existing holding; provisional score estimate `40`; `score_status=COMPLETE` by numeric coverage but `requires_manual_review=true` because valuation/fundamental data is stale or missing. No valid HIGH/CRITICAL flag, severe trend exit, non-tradability event, or hard cap breach exists. Expected action: `HOLD_REVIEW`, never score-based REDUCE. If the same inputs become fully current/approved and the complete-score reduce trigger persists for its required duration, REDUCE may then be recommended.

## 17. Required Phase 3 strategy tests

In addition to the golden cases:

- MA20/50/200, Wilder ATR14, 60-session high/drawdown, price-adjustment selection;
- simple horizon return, Decimal log RV/sample annualization, floor, Type-7 percentile/ties/winsorization/minimum history;
- valuation leaf direction, partial coverage, stale review, missing data and PIT provenance;
- confirmation exclusion of current bar from lookback; calendar gaps and duplicate bars;
- every state/action precedence path, partial fills, cooldown, fresh confirmation, veto severity, and incomplete-score `HOLD_REVIEW`;
- relative priority cannot alter absolute score/action block;
- both sizing options as research candidates; no sizing implementation before OD-EOD-004 approval;
- cumulative target quantities across one/two units, fractional steps, HK board lots, tick/minimum notional, cash/FX/fee unavailable, reductions, and never-exceed-target properties;
- deterministic replay and a future-record injection test proving no output changes;
- the same strategy object/signals in EOD analysis, paper, and daily-bar backtest contexts.

Synthetic data is allowed only in clearly labelled test fixtures. No golden input or expected result may be shown as real market, valuation, broker, or issuer data.

Passing these tests or a Phase 4 backtest does not establish profitability or predictive validity. Research status changes only after separately approved evaluation criteria and adequate forward observation.
