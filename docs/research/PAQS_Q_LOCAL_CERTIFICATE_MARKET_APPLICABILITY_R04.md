# R04 frozen calendar-aware local certificate specification

PROPOSED_SEMANTICS:R04-CALENDAR-LOCAL-1. One research candidate, not product adoption.
Frozen before candidate comparisons with [PLAN](../evidence/TASK_006B_Q/research-04/PLAN.md).
Retain R03 M1 raw predicates exactly: v_j=H_(j-1)-L_(j-1)>0; D_j requires strict neighboring
HIGH and H_j-C_(j+1)>=v_j; U_j is the LOW mirror. E_j=(D_j XOR U_j) AND NOT(D_(j-1) OR U_(j-1)).
No same-bar confirmation; equality of reversal distance passes, equal extrema do not; dual abstains.
The prior raw veto applies even if that raw center was vetoed. No alternation filter or Regime.
Use exact inherited Decimal Context(50, HALF_EVEN), finite 38,18 prices; coefficient1, no ATR.

## Windows, clocks and qualification

Use reviewed version selection/quality validation, original W/A/N: W1 26/104/130,
D1 60/252/312, M30 40/160/200. Keep raw versions; select at each cutoff independently.
Warm centers can establish a prior raw predicate, but extreme AND confirmation must be active
for current events. Count every center, including missing left/right support, warm and rejected
centers. Insufficient horizon remains in the 100-cutoff denominator. No prices are filled.

AS_OF: completed prices and all calendar facts must be legitimately available by cutoff,
COMPLETE-qualified and adjustment historically safe. Unknown availability, current-QFQ,
PARTIAL/UNKNOWN or uncertified calendar cannot become strict confirmation.
OBSERVATIONAL: retain original aggregate/per-bar quality; allow valid actual completed D1
observations of legal coverage, but derived W1/M30 require COMPLETE constituent coverage as in
the accepted normalizer. Unknown price/calendar availability may describe an observed local
pattern, never historical knowability or certified overall coverage. Known future versions are
excluded in both modes. Invalid/contradictory selected input fails both modes conservatively.

Extreme time, reversal completed_at, evidence available_at and calculation cutoff are distinct.
available_at is null if any support price/calendar availability is unknown. The retrospective
study records actual run-time recognition separately from first_seen_scheduled_cutoff; the latter
is an experiment coordinate, not an assertion it was recognized then. Strict synthetic schedules
are hypothetical input-time tests, not evidence of real historical recognition. No M2 service.

## Calendar facts and expected slots

Calendar facts are independently sourced from prices: market/date/timezone, OPEN/CLOSED/UNKNOWN,
ordered session segments, source/version, retrieval and availability, strict completeness flag.
Select versions per date at each cutoff; conflicts and malformed selected shapes fail closed.
No missing date defaults to CLOSED. No absent bar creates a calendar fact. Unknown or prohibited
edges veto certification, including when only the *prior* raw predicate is unavailable.

For original AVGO, freeze the immutable Capture calendar in a separate external export, verify
its hash and reconstruct original normalized datasets with the accepted normalizer. Captured
positive session rows are observational schedule evidence; calendar coverage_complete=false is
preserved. Weekend closure convention is based on the published weekday regular schedule at
[Nasdaq](https://www.nasdaq.com/market-activity/stock-market-holiday-schedule), checked 2026-09-10.
Its 2026 holiday dates are cross-checked with the
[Nasdaq Trader calendar](https://www.nasdaqtrader.com/trader.aspx?id=calendar).
Only the explicitly frozen 2026 closures supplement the Capture. Other absent weekdays remain
UNKNOWN, including possible exceptional closures; no extrapolated holiday formula or assumed
five-day holiday week. A captured OPEN contradicting a frozen closure is a conflict, not a fix.
The US venue mapping is the archive's vendor-market mapping, not an independently certified MIC;
these retrospective schedule conventions do not authenticate historical calendar availability.
HK real coverage is absent; HK calendar oracles are explicitly synthetic.

- D1 slot: one evidenced OPEN day, start at first segment open, end at last segment close.
  Adjacent D1 bars must have no OPEN or UNKNOWN date between them. CLOSED dates may be crossed,
  including evidenced holiday/weekend closures. Missing expected OPEN day is a break. Segments
  and timezone determine actual DST/early-close times; never use fixed UTC close assumptions.
- W1 slot: accepted Monday-to-next-Monday nominal interval, completed at final evidenced trading
  close, not nominal endpoint. Every civil day of that week must be OPEN or evidenced CLOSED,
  at least one OPEN session, all expected D1 sessions complete in the accepted construction.
  COMPLETE derived coverage plus exact original normalization is retained. Unknown weekday,
  incomplete constituent/week, unknown calendar boundary or a missing weekly slot is a break.
  Consecutive completed calendar weeks may cross known closures. No synthetic fifth session.
- M30 slot: exactly 30 minutes wholly within one evidenced REGULAR segment, aligned from its
  segment start. Require adjacent buckets in that **same date and segment**. Overnight and HK
  lunch are prohibited even when known; distinguish them from a missing within-segment bucket.
  Early-close remainder shorter than30 minutes is not a complete bucket. Extended US sessions
  cannot enter. The cost is that a quartet cannot use the first three bars of a new segment
  as its confirmation without four same-segment bars; report boundary rejection density.

Each certificate's complete support is ordered four price/version refs plus every calendar fact
used by their slots and intervening edges, the rule, qualification mode and support-policy version.
Retain negative evidence for all nontrading dates traversed. Same unordered sets are insufficient:
check ordered quartet, no inserted/deleted observation, exact selected calendar identities,
unchanged qualification and active endpoints. Changed calendar versions or late prices are
information changes, never pure reseeding. Invalid global input status prevents proof application.

R03 P3 extends only with these additional unchanged-calendar premises: raw arithmetic is the same
function of the quartet and the same slot/edge facts imply identical eligibility. For a one-bar
left shift without information/domain change, W>=2 retains quartet price support for endpoint-
eligible centers. It does not prove unchanged calendar facts or complete observations. Count
violations of those assumptions separately and retain original endpoint-based losses regardless.

## Frozen structural measures and decision limits

Original event comparison key=(kind,exact price,extreme_ref,confirmation_ref), excludes rule IDs.
Report opportunities, losses, rediscoveries with reversal<=OLD cutoff, new reversals, genuine
endpoint expiry; separately full ordered-support opportunities/losses and coverage exclusions.
Count same-endpoint changed witness identities, revisions, unknown calendar/missing slots,
prohibited segments and all skipped/insufficient cutoffs. Do not bridge failed cutoff pairs.

All-center census: accepted active/warm, XOR dual, prior-raw veto, no raw reversal/zero scale,
and unavailable support with explicit reasons. Compute candidate event density per active bar,
event age in observed-bar intervals, consecutive same-kind pairs and separation. Pair amplitude
is abs(current.price-previous.price)/current preceding-bar range; zero scale is undefined.
For rejected unambiguous raw centers with an earlier accepted same-kind active event, compare
their prices: record HIGH higher / LOW lower as an omitted-more-extreme case and its reference.
This is a declared limited comparator, not universal ground truth, false negatives or recall.
Do not select alternating subsequences or run inherited Regime logic on local certificates.

Potential recommendation is continuation under a new contract, a specified *unimplemented* rule
amendment, or rejection. Unexplained changed events under claimed identical full support, hidden
dependencies or fabricated calendar continuity prohibit continuation. Zero loss or more output
alone cannot recommend usefulness. AVGO-only cannot establish broad market applicability.
