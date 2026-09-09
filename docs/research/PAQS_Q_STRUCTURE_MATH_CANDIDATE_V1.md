# PAQS-Q Structure — Mathematical Candidate v1

Executable clarification version: **QSTR-CANDIDATE-1.1**. Sections 1–12 retain the issued
candidate; section 13 freezes serialization, observation policy and diagnostic ablations before
execution. This is still a research candidate, not semantic adoption.

Status: **RESEARCH CANDIDATE FOR TASK-006B-Q; not production strategy authority.**

Task: [006B-Q contract](../../prompts/tasks/TASK-006B-Q_STRUCTURE_FORMALIZATION_AND_STABILITY.md).

Base: `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`. Historical [Lite input](https://github.com/ahhhhzzz/ai-infra-quant/blob/01000900861d4506fb35fbf423901a5b9a306499/docs/research/PAQS_V0.4_LITE_STRUCTURE_QUANT_AMENDMENT.md).

This defines a concrete starting experiment. The implementer must resolve any remaining serialization/normalization ambiguity explicitly, add hand-computed examples, and version every semantic change. A parameter is not validated merely because it is written mathematically. Passing determinism tests establishes reproducibility, not predictive value.

## 1. Pure function and evidence

For timeframe f and analysis cutoff tau:

`S_f(tau) = F_v(B_f(tau), theta_f, calendar_metadata, quality_metadata)`.

`B_f(tau)` contains legitimate completed canonical bars available under the declared observation model by tau. Keep source interval, completion/availability reference, retrieval time, market timezone, session and adjustment basis distinct. Current-QFQ historical observations permit computational cutoff tests but not a claim of genuine historical information-set reconstruction.

Output at minimum: security/timeframe/cutoff; rule version and config hash; input observation hash and bounded evaluation hash; window boundaries; input status; structure sufficiency; ATR; active pivots/labels; D1 zones/range; Regime; warnings/reason codes; structured evidence references; deterministic semantic hash. Store decimal quantities as canonical strings, aware instants in UTC, dates separately. No latest quote, wall clock, LLM, environment or account state participates in F.

Every conclusion provides the evaluated rule identifier, operand values, comparator, threshold and source references. A reason string alone is insufficient. Confirmed evidence is immutable within an evaluation; later evaluations are new outputs, not edits of earlier ones.

## 2. Candidate parameter profile

| Parameter | W1 | D1 | M30 | Origin |
|---|---:|---:|---:|---|
| Warm bars W | 26 | 60 | 40 | Lite research candidate |
| Active bars A | 104 | 252 | 160 | Lite research candidate |
| Total N=W+A | 130 | 312 | 200 | Derived |
| Pivot lambda | 1.8 | 1.8 | 1.0 | Lite research candidate |
| Pivot recency warning age | 52 | 126 | 80 | A/2; diagnostic only |

Shared inherited candidates: ATR n=14; EMA smoothing; extreme separation=2 bars; swing equality tolerance=0.25 ATR. D1 zone epsilon=0.50, independent touch separation=5, half-width clamp=0.15–0.75 ATR, merge IoU=0.50, expiry age=126, decision cap=2 supports+2 resistances. D1 range L=40, inside ratio>=0.70, center width=2–12 median ATR.

No per-symbol fitted settings. Freeze the complete profile before diagnostics. Small perturbations: W1/D1 lambda 1.7/1.8/1.9; M30 0.9/1.0/1.1; zone epsilon 0.45/0.50/0.55; age 100/126/160; range L 30/40/60. Vary one coordinate at a time against the same default observations/cutoffs. EMA/ROC/extension factors belong downstream and are excluded here.

## 3. Numerical and window semantics

Use Decimal local context precision=50, ROUND_HALF_EVEN; arithmetic source values must be finite and valid. Adopt the existing 006B financial quantum `1e-18` for derived values, with rounding sites explicitly frozen: TR, each ATR step, distance ratios, equality tolerance, zone clamp bounds/endpoints and exported derived ratios. Comparisons use the declared rounded operands except Pivot reversal threshold, which uses the exact Decimal product lambda*ATR as the existing implementation does. Include that exact comparator threshold in evidence; do not display a rounded threshold as if it were the actual gate. No binary-float financial computation.

At terminal bar t, choose exactly the last N eligible bars, index them locally `0..N-1`, and use indices `W..N-1` as active. Insufficient N gives `INSUFFICIENT_FOR_Q_HORIZON`, no decision-active structure and Regime `UNCERTAIN`. Do not backfill expected missing sessions with fabricated bars. Distinguish a calendar-confirmed absence from unknown coverage and report the approved input-quality assessment rather than setting all valid inputs to VERIFIED.

Bars outside the window cannot seed ATR or Pivot. Thus the first TR cannot use a preceding close from outside the window. Bar reference identity uses canonical security/timeframe/source time/content, not absolute provider-array position. Positions local to the evaluation are explanatory metadata, not stable evidence identity.

Candidate active-Pivot rule is deliberately explicit: **both extreme and confirmation references must be in the active segment**. Warm pivots and candidates whose extremes remain in warm-up may seed the state machine but cannot become active observations. This is a conservative clarification of the historical Lite text and must be sensitivity-reviewed for suppressed early active evidence. Keep at most one previous same-type warm pivot internally to label the first active pivot; a label using a warm comparator is diagnostic and cannot establish Regime.

## 4. ATR definition

For window-local index i:

`TR_0 = H_0 - L_0`

`TR_i = max(H_i-L_i, abs(H_i-C_(i-1)), abs(L_i-C_(i-1)))`, i>0.

`ATR_i = unavailable`, i<n-1.

`ATR_(n-1) = mean(TR_0,...,TR_(n-1))`.

`ATR_i = alpha*TR_i + (1-alpha)*ATR_(i-1)`, i>=n, `alpha=2/(n+1)`.

Apply section 3 rounding. Call this `EMA_TR_14`, not Wilder ATR. The accepted baseline uses this EMA recurrence; switching to `alpha=1/n` is a separate semantic change, not a correction hidden behind the ATR name. If ATR<=0, do not divide or confirm a Pivot; expose insufficiency at a terminal nonpositive ATR. ATR uses only the declared window.

## 5. Close-confirmed directional-change state machine

Exactly one engine per timeframe, states `UNSEEDED`, `SEEK_HIGH`, `SEEK_LOW`. Process legitimate completed bars in chronological order. Skip Pivot updates until ATR>0. Update candidate extremes before evaluating confirmation. Equal extreme prices retain the earliest reference.

Candidate high `(h,e_h)` and low `(l,e_l)` hold source High/Low, not Close. At current index i:

`down = (e_h < i) and (h-C_i >= lambda*ATR_i)`.

`up = (e_l < i) and (C_i-l >= lambda*ATR_i)`.

| State | Update and condition | Output / next state |
|---|---|---|
| UNSEEDED | Update high=max and low=min; down XOR up | down: emit HIGH then SEEK_LOW; up: emit LOW then SEEK_HIGH |
| UNSEEDED | Both predicates true or both false | Emit nothing, remain UNSEEDED; expose ambiguity if both true |
| SEEK_HIGH | Update candidate high; down and `e_h - previous_extreme_index >= 2` | Emit HIGH; SEEK_LOW |
| SEEK_LOW | Update candidate low; up and `e_l - previous_extreme_index >= 2` | Emit LOW; SEEK_HIGH |

On HIGH confirmation initialize low candidate from the current bar Low; on LOW confirmation initialize high candidate from its High. Only one confirmation per bar. The first seed has no prior-pivot separation gate. Separation=2 measures extreme-to-extreme distance, not confirmation delay. Same-bar extreme/confirmation is prohibited; a bar creating a new extreme cannot also confirm that new extreme. No inference of intrabar High/Low order, retroactive promotion or forced pivot when ambiguous.

Each Pivot carries type, price, extreme and confirmation references, ATR at confirmation, lambda, threshold operands, rule version and content identity. Confirmed pivots alternate types; active filtering does not re-run the state machine or manufacture a replacement.

## 6. Swing labels and directional eligibility

Compare each pivot p with previous same-type confirmed pivot q. Let `delta=round(0.25*ATR_at_confirmation(p))`.

- HIGH: HH if `p.price>q.price+delta`; LH if `<q.price-delta`; EH otherwise.
- LOW: HL if `p.price>q.price+delta`; LL if `<q.price-delta`; EL otherwise.

An equality boundary is EH/EL. Label references include both pivots. Directional evidence requires both p and q active for the latest eligible HIGH and LOW comparisons, hence at least two active highs and two active lows. Do not search backwards for an older favorable label when the latest comparison is ineligible or conflicting. If the latest active pivot's extreme age exceeds A/2, issue a staleness warning; no synthetic reversal or automatic debounce follows.

## 7. D1 zones

Only active D1 pivots form observations, LOW->support, HIGH->resistance. Warm references never count. A touch is a **confirmed pivot reaction**, not every candle intersecting a zone. It is known only at confirmation, while touch separation and age measure extreme-bar indices.

Retain the baseline deterministic clustering algorithm from `build_zones`, `_pair_distance`, `_center_distance`, `_independent_pivots`, `build_zone_geometry` and `_merge_confirmed_zones` in [base source](../../src/ai_infra_quant/core/strategy/paqs_structure.py), replacing only the Major input selector with the candidate active single-pivot set. The prototype/spec must spell out these inherited rules rather than rely on an unspecified clustering library:

1. Separate support/resistance. Sort by price, extreme key, confirmation key, pivot ID. Candidate observation joins a cluster only if its distance to **every** member is <=epsilon, where `d(p,q)=round(abs(p.price-q.price)/median(p.ATR,q.ATR))`.
2. Among eligible clusters choose minimum normalized center distance then deterministic member-based cluster identity, as in the base. No eligible cluster creates a new one.
3. Within each cluster sort by extreme time then confirmation/ID and greedily accept touches with extreme separation>=5 from the last accepted touch. Deduplicate source observations; one pivot is not multiple reactions.
4. `center=median(prices)`, `a=median(confirmation_ATRs)`, `MAD=median(abs(price-center))`, `halfwidth=clamp(MAD,round(0.15*a),round(0.75*a))`. Bounds are rounded center±halfwidth. Even-sized medians are the mean of the two central values.
5. One independent touch is CANDIDATE; >=2 is CONFIRMED. Same-role confirmed zones merge at IoU>=0.50, selecting highest IoU then lower lower-bound and sorted zone IDs. Deduplicate union, reapply independence and rebuild geometry until no merge qualifies. Use interval intersection divided by bounding union, rounded as in base; zero union yields zero.

After reconstruction apply age `t - latest_accepted_touch.extreme_index <=126`. An expired zone cannot enter current decision or range output, even if its delayed confirmation is recent. Future valid independent reactions can refresh age only when legitimately confirmed. Candidate and expired zones may be diagnostic, separate from decision zones.

Keep only confirmed, unexpired supports with `lower<=C_t` and resistances with `upper>=C_t`. A zone containing price is allowed. Do not relabel a crossed zone's role. Define distance from price to interval as `max(lower-C_t, C_t-upper, 0)`; select nearest two per role by distance, newest touch, lower bound then content ID. This is the decision cap; clustering membership is separately available for diagnostics.

This nearest-zone selection/tie policy is an explicit research clarification, not an already validated fact. Test that capped geometry does not hide a qualified nearby box disproportionately.

## 8. Recent D1 range

Use only the capped active support/resistance set. For each pair require `support.upper < resistance.lower`. Let recent window be `[t-L+1,t]`. Select each zone's accepted touches whose **extreme and confirmation** lie in that window. Require >=2 support and >=2 resistance reactions. Sort by extreme time, reject opposite-side ambiguity at the same extreme index, compress consecutive same-side entries; require >=4 alternating entries.

`inside_count = sum(1[support.lower<=C_i<=resistance.upper])` over exactly L recent legitimate bars.

`inside_ratio = round(inside_count/L) >=0.70`.

`range_ATR = median(ATR_i over same L bars)>0`.

`width_ATR = round((resistance.center-support.center)/range_ATR)` must lie in `[2,12]`.

Latest Close must lie inclusively inside the outer bounds. All required ATRs must be available; no fabricated denominator or abbreviated lookback. Pair ranking: more qualifying **recent** independent touches, greater inside ratio, narrower normalized width, deterministic pair ID. Output at most one selected range; expose other qualifying pairs diagnostically. Old touches may describe a zone but cannot prove a current range.

Range IDs track exact evidence versions. Report uninterrupted `RANGE` state run lengths separately from exact-ID run lengths. For geometry comparison report normalized changes in both bounds and interval IoU; a changed hash alone is not a changed market regime.

## 9. Regime function

Evaluate per timeframe, no cross-timeframe vote or score:

1. Invalid/insufficient input, missing horizon or nonpositive terminal ATR -> UNCERTAIN with typed cause.
2. D1 qualifying current range -> RANGE.
3. Latest active HIGH comparison=HH and LOW comparison=HL, all four evidence pivots active, and `C_t>=latest_HL.price` -> BULL_TREND.
4. Latest active HIGH comparison=LH and LOW comparison=LL, all four evidence pivots active, and `C_t<=latest_LH.price` -> BEAR_TREND.
5. Otherwise UNCERTAIN with the exact conflicting/missing/breached condition.

No W1/M30 range. An UNCERTAIN structure can have available market data; separate quality from insufficiency from mixed evidence. Breaching the current trend reference may remove a trend label but does not emit BREAKOUT, RETEST, Setup or advisory.

## 10. Identity, reproducibility and temporal tests

Define a canonical decision projection containing rule/config version, bounded canonical observations, cutoff, active evidence, statuses and deterministic reasons. Its hash excludes wall-clock compute time, transport request IDs, original excluded leading-history length and incidental process metadata. Preserve a separate source-snapshot/capture binding so equivalent decisions do not erase original provenance. The implementer must freeze field order/UTF-8/decimal-string/UTC/null/array ordering and domain-separated hash construction before golden tests.

Origin test: `F(full_history<=t)=F(last_N_bars<=t)` for the decision projection. Repeat with arbitrary leading extremes. All derived bars must be formed under the same cutoff/calendar before comparing; do not change terminal bar identity.

Future-isolation test at a **fixed cutoff t**: later bars or later-available revisions must not influence F(t). For input carrying explicit observation versions, choose only available versions. If historical availability is unknown, mark it unknown instead of inventing it.

Rolling recomputation is not append-only event history. At t+1 the left boundary and ATR seed move; even still-eligible pivots may recompute differently. Do not falsely require equality of F(t) and a truncated F(t+1), and do not claim historical pivot permanence from fixed-cutoff isolation. This is a known research risk to measure before adoption.

## 11. Stability measurements and gates

For K consecutive eligible cutoffs and regime sequence R:

`churn_per_100 = 100 * sum(1[R_i != R_(i-1)]) / (K-1)` for K>=2.

Count actual adjacent transitions; a missing/invalid cutoff breaks a segment, not a bridge between two distant eligible cutoffs. Report data-status transitions separately. Report regime fractions, UNCERTAIN fractions, active pivot count/age, expired/active zones, range fraction/run length, geometry deltas and parameter disagreement `different_comparable_states / comparable_pairs` with explicit denominators.

Per-parameter diagnostic comparisons use structural geometry, role and bar references, not config-hash-driven ID differences. D1 churn>20/100 triggers review, not automatic parameter tuning. Report normalized zone/range-bound changes exceeding 0.5 terminal ATR as a declared research materiality flag, plus all direct BULL<->BEAR flips and latest-pivot reference replacements regardless of magnitude. This flag is a review convention, not an economic significance claim.

Boundary attribution uses diagnostic ablations, **never product outputs**. In addition to normal N-bar evaluations at t and t+1, record (a) a common fixed-left seed evaluation with the new right bar appended and (b) a shifted-left evaluation at the same terminal cutoff. Hold declared active eligibility explicit, record the modified diagnostic horizon and compare decision components. The specification/harness must describe exact ablation intervals before running; effects can interact nonlinearly, so mark non-attributable cases `COMBINED_OR_UNRESOLVED` rather than asserting causality from coincidence.

Zero unexplained future references, origin violations, expired decision zones, hidden warm directional anchors or nondeterministic results are hard correctness gates. Boundary instability, high UNCERTAIN share, excessive churn, zone-cap suppression and parameter disagreements require named case review; no universal PASS follows from low churn or aesthetically plausible charts. Do not silently add smoothing/hysteresis to conceal these failures.

## 12. What is still to be established

The candidate is mathematically explicit but unvalidated. The prototype/report must evaluate: initial dual-reversal ambiguity; warm-extreme exclusion; rolling ATR/pivot seed sensitivity; sufficiency of two active high/low comparisons; zone recency and cap; range sensitivity; missing-session/partial-input handling; observational adjustment limitations; useful coverage for newly listed equities. Any material rule revision gets a new candidate version with before/after same-input diagnostics.

The final research recommendation must separate **engineering correctness**, **structural robustness**, and **not evaluated: predictive/trading performance**. Do not claim semantic adoption, production integration or PAQS-Q completion from this task alone.

## 13. Executable clarification 1.1 — frozen before diagnostics

Rationale: version 1 left wire identity, missing historical availability and exact boundary
ablation intervals unresolved. This clarification fixes those contracts without changing the
candidate numerical profile. See [profile](../evidence/TASK_006B_Q/profile.json) and
[fixed universe](../evidence/TASK_006B_Q/universe.json). No outcome-based parameter choice is allowed.

### 13.1 Canonical schema and identity

The offline observation envelope is `qstr-observations-v1`: security (`US.<symbol>` or canonical
five-digit `HK.<symbol>`), timeframe, market timezone, quality (`COMPLETE`, `PARTIAL`, `UNKNOWN`,
`INVALID`), observation mode (`AS_OF` or `OBSERVATIONAL`), source/provenance text and bars.
Each bar retains start/end, completed_at, available_at (nullable), retrieved_at, source reference,
OHLCV, completed flag, coverage, adjustment basis and session classification. Decimal input must
be exact numeric text; JSON binary floats are rejected. Financial magnitudes are bounded to the
project 38,18 range. Metadata does not become verified because input can be computed.

Canonical encoding recursively maps Decimal to plain canonical strings (no exponent/trailing
fractional zeros; signed zero becomes `0`), aware datetime to UTC with six fractional digits and
`Z`, tuples to arrays; dictionary keys are sorted, separators comma/colon, UTF-8, no NaN.
Hashes are SHA256 of `domain + NUL + canonical_bytes`. Bar identity includes security/timeframe,
source time/content and adjustment basis; local ordinal, retrieval time and incidental provenance
are excluded. Pivot/zone/range evidence IDs include rule/config and stable source IDs, not absolute
provider indices. Raw source-envelope hash and provenance remain separate from decision identity.

The semantic projection contains bounded canonical observations, cutoff, rule/config, window,
input/structure statuses, ATR, active pivots/labels, decision zones/range, deterministic reasons and
operand/comparator evidence. Excluded leading/future observations, source-envelope hash, execution
clock/platform/performance and acquisition provenance are outside that projection. Diagnostics
retain all bounded warm/active pivots, candidate/expired zones and competing ranges separately.
All returned domain objects are frozen; serialized output is immutable text/bytes.

### 13.2 Observation versions and legitimate bars

At fixed cutoff, exclude records completed after cutoff, unfinished records and versions whose
explicit available_at exceeds cutoff before considering OHLC. For a source time key, select the
latest available version; identical duplicates deduplicate, conflicting versions at the same
availability timestamp fail closed. No revision overwrites an earlier evaluation.

`AS_OF` excludes unknown availability. `OBSERVATIONAL` permits null available_at for retrospective
calculation but emits `HISTORICAL_AVAILABILITY_UNKNOWN`; it never invents a publication timestamp.
Retrieval can be later than historical cutoff in this mode and is retained as provenance. The local
AVGO archive is such an observation, with current QFQ and unknown adjustment epoch. Computational
cutoff isolation is not point-in-time information-set validation.

Only completed D1 and explicitly COMPLETE W1/M30 are eligible. M30 must be REGULAR and a complete
30-minute bucket; archive normalization uses the unchanged 006A derivation with supplied market
sessions (including breaks/half-days), not vendor M30 substitution. W1 completion uses source
calendar closing evidence; the nominal week end may follow a Friday completion. Calendar source
coverage is not upgraded. Mixed adjustment bases, invalid OHLC, conflicting keys/overlapping
intervals, identity/timezone conflicts and invalid numeric inputs produce typed INVALID/UNCERTAIN.
Insufficient legitimate N bars produces INSUFFICIENT_FOR_Q_HORIZON, no active structure.

Within an evaluation, the exact N-bar window exclusively seeds ATR/Pivot. Partial aggregate
coverage remains PARTIAL even when enough legitimate complete bars permit calculation. Unknown
aggregate coverage remains UNKNOWN. These are separate from structural sufficiency and Regime.

### 13.3 Numerical and evidence clarifications

Use a fresh explicit Decimal Context(50, ROUND_HALF_EVEN), including normalization, not the
caller's precision or traps. Inherited median helpers round their result to 1e-18; TR, ATR
recurrences, ratios, label tolerance, zone clamps/endpoints and exported ratios round there too.
Pivot distance and lambda*rounded_ATR comparison retain the context-50 product without quantum
rounding; evidence records that exact threshold. One engine is implemented independently; the
old engine is only an optional comparison inside the diagnostics harness.

Example with ATR=2, lambda=1.8: a prior high 110 confirms on close 106.4 (distance=3.6),
not 106.400000000000000001; a current-bar high cannot confirm immediately. Equal highs retain
the earlier extreme. Two support pivots at 100/100.2, ATR=2, at indices 10/15 have center=100.1,
MAD=0.1, clamped halfwidth=0.3, bounds=99.8/100.4. At t=141 the latest-touch age is 126 and
eligible; at t=142 it is expired. These examples are synthetic hand oracles, not market samples.

### 13.4 Exact ablation and diagnostic projection

For consecutive eligible terminals t,t+1, define:

| Arm | Calculation interval | Active interval |
|---|---|---|
| OLD | [t-N+1,t] | [t-A+1,t] |
| RIGHT | [t-N+1,t+1] | [t-A+1,t+1] |
| LEFT | [t-N+2,t] | [t-A+2,t] |
| BOTH (normal next decision) | [t-N+2,t+1] | [t-A+2,t+1] |

RIGHT and LEFT use explicitly modified N+1/N-1 diagnostic horizons. They never replace normal
decisions. Compare Regime, pivot type/price/stable extreme+confirmation refs, role/geometry/touch
refs and range geometry, excluding config-hash-driven IDs and advancing cutoff. If BOTH differs
from OLD, only RIGHT differs and matches BOTH, classify RIGHT_ONLY; analogous LEFT_ONLY;
otherwise COMBINED_OR_UNRESOLVED. All-equal is UNCHANGED. This is operational attribution,
not proof of economic causality; every direct directional flip and material left-only case is
retained for inspection. No automatic smoothing is applied.

### 13.5 Data freeze and verdicts

The 40-member universe (24 US/16 HK), sector sampling labels, cutoff ceiling and last-100
sequential-terminal schedule are frozen before diagnostics. Sector labels are sampling rationale,
not a newly verified live listing census. Missing symbols stay in the denominator. No network
acquisition is part of this run; use the user-authorized existing AVGO archive read-only. It is
one real observation dataset, not a substitute for the other 39 members. W1 needs 229 eligible
weekly bars, D1 411 and M30 299 to supply 100 eligible terminal evaluations.

The report separates engineering execution, real-market gate and semantic adoption. Incomplete
real-universe coverage or unexplained material boundary effects prohibit semantic PASS even if
every synthetic correctness invariant passes. Predictive/trading performance is not evaluated.
