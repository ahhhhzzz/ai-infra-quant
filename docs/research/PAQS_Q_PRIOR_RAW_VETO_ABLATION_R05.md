# R05 prior-raw veto controlled ablation — frozen mathematics

Proposed research only. B0 is unchanged `PROPOSED_SEMANTICS:R04-CALENDAR-LOCAL-1` at
corrected R04 `c4e21a0204cf6cdd7bb139584b02f01792a49f13`, reference study-03.
A1 is `PROPOSED_SEMANTICS:R05-NO-PRIOR-RAW-VETO-4SUPPORT-1`.
This specification and [PLAN](../evidence/TASK_006B_Q/research-05/PLAN.md) freeze before AVGO A1.

## Domain and sole intervention

Let Q(j) mean the unchanged R04 ordered price/calendar quartet j-2..j+1 is qualified,
the entire selected input is valid, and both extreme and confirmation endpoints are active.
Retain original W/A/N (26/104/130, 60/252/312, 40/160/200), exact Decimal Context(50,
HALF_EVEN), version selection, UTC/timezones, completed bars, adjustment/quality semantics,
and all R04 slot/edge/negative-evidence requirements. Warm accepted centers remain census only.

With v(j) = H(j-1)-L(j-1) > 0:

```text
D(j) = H(j)>H(j-1) AND H(j)>H(j+1) AND H(j)-C(j+1)>=v(j)
U(j) = L(j)<L(j-1) AND L(j)<L(j+1) AND C(j+1)-L(j)>=v(j)
X(j) = D(j) XOR U(j)
B0(j) = Q(j) AND X(j) AND NOT(D(j-1) OR U(j-1))
A1(j) = Q(j) AND X(j)
```

No three-observation event path exists. Keeping j-2 is intentionally nonminimal logical support;
it preserves the matched R04 eligibility domain, including calendar support and availability.
The implementation consumes R04's pure qualified raw/census, then rebuilds A1 events from
`raw XOR` and a non-null quartet support hash, independently of the B0 veto classification.
R04 support hashes continue to identify the identical four-observation eligibility certificate.
A1 event identities use A1 rule plus endpoint key/support hash. B0 identities remain exact R04.

Endpoint comparison key is the unchanged digest of (kind, exact price, extreme bar ref,
confirmation bar ref), independent of algorithm IDs. Endpoint identity is not a timestamp alone.
Selection preserves all original raw versions. R04's support version includes price refs,
availability identities and ordered calendar facts. Transport retrieval labels are not new prices.

## Propositions and counterexample boundaries

P1: B0 subset A1 on each common qualified domain. Removing a Boolean conjunct cannot remove
an accepted endpoint. A1 minus B0 equals exactly Q AND X AND previous raw present. With one
center per endpoint, this is a bijection to B0 active PRIOR_RAW_VETO rows. Current dual,
zero-scale, unavailable quartet and failed global inputs remain outside both event sets.

P2: adjacent same-kind raw centers are impossible. D(j-1) requires H(j-1)>H(j), whereas D(j)
requires H(j)>H(j-1), a contradiction. U is the mirrored strict-low contradiction. Therefore a
previous dual raw also cannot coexist with any current raw. Additions are nevertheless classified
as opposite/same/dual by actual predicates, and zero categories are retained. This local proposition
does NOT establish alternating accepted output: nonadjacent HIGH/HIGH or LOW/LOW remain possible.

P3: A1 is conditionally rolling-origin stable. Under identical ordered quartet price versions,
calendar facts and edges, quality/mode, valid global input and active endpoints, Q and the exact
three-bar arithmetic X are identical, so acceptance, endpoint and full support identity are
identical. The absolute position of the window origin is absent. Warm horizon >=2 retains the
quartet under one-observation left shifts for still-active endpoints. The claim does not cover
insertions/deletions, revised prices/calendar, changed qualification, missing support or expiry.
These remain reported separately using the unchanged R04 rolling comparison, including original
endpoint loss/rediscovery and narrower full-support opportunities/losses; failed pairs are not bridged.

Concrete synthetic counterexamples: equal neighboring highs/lows defeat strictness; a current
outside bar can satisfy both D/U and must abstain; a zero predecessor range cannot establish raw;
unknown or absent j-2 can leave a current triple eligible but forbid both events; restored j-2
can change availability/eligibility; later price/calendar revisions cannot appear at OLD cutoff;
successive HIGH110/LOW80/HIGH140/LOW50 observations over flat100 neighbors expose a four-event
alternating unit-gap chain in A1 while B0 retains only the first. None establishes trading value.

## Dependency audit

TRIPLE_ONLY_ELIGIBLE is every census row with a populated raw tuple (R04 completed the current
triple qualification) but no quartet support hash. This includes current raw false/false and
dual; report current XOR separately. Since the triple passed, the additional failure is confined
to j-2 or its edge, including LEFT_SUPPORT_MISSING at the beginning of the selected window.
Retain center ref, index, active/warm, timeframe, segment and original unavailable-dependency
reason. Null segment uses UNRESOLVED_SEGMENT. This diagnostic is never consumed by A1 acceptance.

## Finite enumeration

Enumerate all four-observation sequences over the ten exact (low, close, high) triples drawn
from {1,2,3} with low<=close<=high; open=close, volume=1. Ten^4 sequences crossed with four
declared calendar states = 40,000 inputs. States: COMPLETE (one regular M30 segment), J2_UNKNOWN
(extra predecessor day's calendar unknown), J2_MISSING (extra predecessor day's calendar absent),
PROHIBITED_SEGMENT (known earlier session, crossing prohibited). The current triple remains in
one qualified segment in the latter three states. Actual R04 calendar support verifies these
states separately; eligibility is price-independent. No incomplete domain emits an event.
Lexicographic alphabet/product/state order is fixed. SHA256 hashes canonical input plus B0/A1/veto
Boolean outputs in that order. Compare literal strict inequalities with the raw implementation,
set inclusion, bijection and adjacent-same-kind contradiction; retain first veto/A1 witness.
Full public-model tests separately exercise W1/D1/M30 and both markets/modes. This finite domain
does not prove arbitrary OHLC behavior or count as any additional real equity.

## Frozen measurement definitions

All occurrence totals are across overlapping cutoff windows; unique counts are sets of endpoint
keys across that timeframe/mode. Neither count is a sample of independent outcomes.

- Event density: active accepted events / active census centers; undefined if denominator zero.
- Same/opposite pairs: consecutive events in the entire ordered active sequence, without filtering.
  Same-kind rate = sum(same pairs) / sum(max(0,event count-1)) across valid cutoffs. Compare rates
  by integer cross multiplication, not rounded displayed decimals. Pair segment is the right endpoint's.
- Separation is difference in observation indices. Separation-one mass is the count of pairs at 1.
  Unit-gap alternating chains are maximal consecutive opposite pairs at separation1, measured in
  event count; singleton is not a chain, zero if none. Kind runs are maximal same-kind subsequences
  of the complete event sequence; retain run-length histograms independently for HIGH and LOW.
- Age is last selected index minus extreme index. Pair amplitude is absolute price difference
  divided by the CURRENT event's preceding-bar high-low, the unchanged R04 reference. Accepted
  raw entails positive scale. Empty distributions have null extrema/median; use lower median.
- Omissions: recompute the R04 comparator in each arm over rejected unambiguous active raw centers,
  referencing the latest earlier accepted same-kind event; HIGH higher / LOW lower is more-extreme.
  Retain exact reference keys and prices. A restored endpoint means an A1-only endpoint which
  was a more-extreme B0 omission at that cutoff. Unique restored set uses any qualifying occurrence.
- Keep all statuses/reasons, quartet coverage, segment center/support/event sums, raw predicates,
  dependency rows, availability and both endpoint/full-support rolling metrics per cutoff.
  No price after cutoff enters any calculation, case ranking or assessment.

No returns, future-direction assessment, optimized parameters, target/RR, probability, PnL or
product strategy adoption. Strict history and broad market applicability remain INCOMPLETE.
