# PAQS-Q R03 — confirmation and rolling stability: proposed mathematical contract

**PROPOSED_SEMANTICS. Research only; pending independent review and explicit adoption.**
Neither baseline nor H1 is changed. [Frozen plan](../evidence/TASK_006B_Q/research-03/PLAN.md),
[executable evidence and report](../evidence/TASK_006B_Q/research-03/REPORT.md).

## 1. Objects, information and clocks

An observation has a security/timeframe/interval key, exact OHLCV, completion flag/time,
coverage, adjustment/session, availability time and transport provenance. Let I_t be
the reviewed `prepare(raw,t)` selection: completed by t, legitimately available by t,
latest version per interval, with conflicts rejected. A future version never replaces
the old version at an old cutoff. An unknown historical availability is not known As-Of.
Keep the F01 vocabulary COMPLETE/PARTIAL/UNKNOWN and aggregate certainty relation, and
F02's raw version retention and all-input time audits. Malformed selected quality fails;
excluded future price payload is not interpreted. These are hard input boundaries.
Claims below assume well-formed temporal envelopes even for excluded records.

Index selected observations in time order. B_t=last_N(I_t), locally 0..N-1 when sufficient;
warm indices 0..W-1, active A_t=W..N-1, N=W+A. Ordered adjacency matters: equal endpoint
refs without equal intervening observations does not imply equal evidence. F_theta(B_t)
is a current calculation, not a historical fact remembered across invocations. The
cutoff, input eligibility metadata and theta belong to its domain. Extra old data may
affect transport/source hashes, not a calculation on identical B_t.

For an event e distinguish five clocks:

1. Extreme observation interval/end x(e); an OHLC bar does not reveal its intrabar high/low order.
2. Reversal completion c(e): the completed later bar closing the reversal predicate.
3. Evidence availability a(e): maximum availability over **all** causal support versions.
4. Recognition r(e): first actual supplied evaluation that emits that witness identity.
5. Calculation cutoff t: time of this invocation. Require x<c<=t and a<=r<=t for a recorded fact.

An isolated current evaluator cannot know first recognition across prior invocations.
It exposes x,c,a and its cutoff, not a fabricated historical r. A newly recognized event
with c<=previous cutoff is an old event rediscovered, not a new reversal. The record model
adds actual r from its explicit supplied schedule. Never backdate r to x or c. Delayed
evidence can make a>c. A saved result means “this calculation emitted e using I_t,” not
“e will always appear in later calculations” or “the latest revision still supports e.”

The inherited bar ref hashes its canonical observation (including price/completion/
coverage) but not availability/retrieval/source strings. R03 additionally uses version
ref hash(bar.ref,available_at). Retries/transports are outside identity. M1 event identity
hashes rule, kind, exact price, ordered four observation refs and version refs. Its support
is explicit, including negative-veto evidence. Snapshot identity also includes N=8, W,
cutoff/status/selected refs. No local array index is a cross-window event identity.
The **original metric** still keys on (kind,price,extreme_ref,confirmation_ref), without
algorithm IDs or added support hashes; changed witness identity is a separate count.

These distinctions would need separate wire fields for event, current support, recognition
and supersession in any future proposal. Here they are frozen dataclasses in pure research;
there is no wire/API/schema migration or persistence design authorization.

## 2. Existing baseline/H1 dependencies and scoped failures

Both use exactly N=W+A: W1 26+104, D1 60+252, M30 40+160. ATR starts with TR_0=H_0-L_0,
then max(H-L,abs(H-prevClose),abs(L-prevClose)), mean14 at index13 and EMA alpha=2/15
afterwards. Each step is quantized to 1e-18 in Decimal Context(50, HALF_EVEN). Without
rounding, two shared recurrences differ by (13/15)^k times initial difference; with
rounding, each step adds a rounding difference of magnitude at most 1e-18. Thus a bound
is (13/15)^k|delta_0| + 1e-18 sum_{i=0}^{k-1}(13/15)^i. Exact convergence at a finite k is
not guaranteed; rounding may also erase a difference. This is an ATR bound, not a bound
on discontinuous threshold decisions or range selection.

ATR at confirmation j depends on the prefix 0..j, including bar0's special TR seed.
Candidate state, previous confirmations and admissibility also depend on earlier
positive-ATR bars and transitions in that prefix. Conservative complete computational
support is therefore 0..j plus configuration and information eligibility; maximum N
observations. The endpoint-only Pivot evidence record is not that complete support.
Dropping bar0 can alter shared state even if x and c are far inside both active domains.
Future bars do not rewrite the already emitted list *within one invocation*, but a new
invocation starts again with a new seed. Origin invariance at fixed B_t is compatible
with failure when B_t itself changes.

The four-bar R02 unit oracle (ATR=1 supplied diagnostically, not normal EMA) confirms
HIGH110 at x0/c1. Baseline keeps LOW90 at1 forever despite failing separation>=2; H1
omits it and confirms LOW95 at2/c3. Price mirror gives LOW90 then HIGH105. Omitting the
physically more extreme intervening price is an explicit admissibility amendment, not
an improvement in observed truth. H1 preserves dual UNSEEDED XOR: both predicates true
must not force an unknowable OHLC path.

The independently reproduced exact 201-bar M30 `path_lock` witness has wide bar13 at the
first positive-ATR seed. OLD has no active Pivot, BOTH has 13, all completed before OLD
cutoff. The preserved diagnostic's seed intervention restores them; all endpoint
eligibility measures and times remain visible. This is COUNTEREXAMPLE_FOUND for H1's
unqualified rolling confirmation consistency. It is not a theorem about every bounded
algorithm. If “unchanged evidence” for H1 includes its full seed prefix, no such witness
qualifies after deleting that prefix: conditioning this way has effectively zero rolling
coverage, and cannot retroactively pass the original criterion.

Hand ATR series TR=(30,2,...,2): old ATR13=4, old ATR14=3.733333333333333333; after dropping
the first bar, ATR13=2. Distance4 with lambda1.8 crosses only the new threshold. No
geometric tolerance makes those predicates equal. Separately the committed six AVGO H1
LEFT_ONLY geometry cases retain exact material flags despite maximum bound drift around
2.13e-16 ATR. The original >0.5 ATR flag and exact range inequality are preserved. These
are cited committed summaries, **not a new raw-market rerun**.

## 3. M1 — finite local confirmation certificate

Version `PROPOSED_SEMANTICS:R03-LOCAL-1`. This tests one locality tradeoff, not a proposed
full swing engine. Normal model wrapper selects N=8. Two frozen views W=0 and W=2 isolate
the cost/benefit of support padding; no parameter search or AVGO optimization. All selected
bars must be COMPLETE AS_OF, contiguous with equal-duration intervals and consistent
validated identity/adjustment. Insufficient N, legitimate partial/unknown, observational
or gapped input returns UNCERTAIN without events; invalid input returns INVALID. VALID
means only the local model can run; it is not a Regime, trend or market completeness result.
This strict synthetic restriction excludes real overnight/session gaps until a separately
reviewed calendar semantics exists. A price gap alone does not imply intrabar ordering.

For 1<=j<=N-2 define v_j=H_(j-1)-L_(j-1). Define raw predicates:

    D_j = v_j>0 AND H_j>max(H_(j-1),H_(j+1)) AND H_j-C_(j+1)>=v_j
    U_j = v_j>0 AND L_j<min(L_(j-1),L_(j+1)) AND C_(j+1)-L_j>=v_j
    R_j = D_j OR U_j
    E_j = (D_j XOR U_j) AND NOT R_(j-1), for 2<=j<=N-2

On E_j emit HIGH at H_j if D_j, otherwise LOW at L_j; x=j,c=j+1. Process j in increasing
order; no global state or initialization candidate exists. Admissible center domain is
2..N-2 intersect active; raw predicate at j-1 is a veto regardless of whether that prior
raw event was itself emitted, vetoed or ambiguous. Both raw directions mean ambiguity:
emit neither, but preserve the veto for the following center. Zero scale and equal
neighbor extreme do not establish a raw event; reversal **distance equality** passes.
No same-bar confirmation, no tie breaking into an invented path, no compulsory alternating
swing sequence. Local strict uniqueness replaces earliest-running-extreme ties.

The full support D(e) is exactly ordered observations j-2..j+1 with versions. It contains
four observations: the two local predicates, their two scales, the unique-center tests
and negative-veto evidence. No recursive state, EMA or outside previous close is involved.
The rule emits only when full support is reconstructible. New legitimate observations
outside that support cannot alter those predicates if global wrapper preconditions remain
valid. A new bad-quality observation can invalidate the whole calculation; the theorem
does not label that a lost confirmed fact. The original lost metric is still reported.

Financial operations are additions/subtractions/comparisons on inherited finite 38,18
inputs in an independent 50-digit context; no binary float or division is used. Coefficient
1 means one preceding range, chosen for transparent unit witnesses. Kernel O(N) time and
O(N) event output, each event O(4) support; prepare up to M=100000 raw records costs
O(M log M) sorting and O(M) memory. N=8 bounds at most three accepted centers (2..6 with
separation>=2). Low-level kernels require validated inputs; public evaluate supplies them.

Hand HIGH: flat H101/L99/C100 neighbors with center2 H110/L108/C109 gives v2=2, distance10,
D2=true,U2=false,R1=false, hence HIGH110 confirmed at3. Mirror gives LOW90. Center2
H110/L90/C100 yields dual raw predicates and no event. Constant or monotone prices have
no strict internal extremum; equality of neighbor high prevents HIGH. These useful and
uncertain cases demonstrate nontriviality without manufacturing two-sided Regime.

Semantic cost: consecutive raw turns can veto one another even when not emitted; local
events may repeat the same kind and omit globally more extreme prices. W=0 can lose a
still-active event when its negative witness leaves the window. These counterexamples
are preserved, not repaired by changing the definition after observing them.

## 4. M2 — immutable first-recognition record comparator

Version `PROPOSED_SEMANTICS:R03-RECORD-1`. This adds no third event detector: input is a
validated M1 Snapshot and explicitly supplied in-memory History. H_0 has empty records,
no last cutoff and hash(RECORD,"EMPTY"). Require strictly increasing cutoff; initial
state/lineage and observation schedule are extra input. At step k, traverse M1 events in
order, append unseen witness IDs with recognition=t_k and prior lineage, then advance
lineage=hash(RECORD,prior lineage,snapshot), even for an uncertain snapshot. Uncertain/
invalid snapshots append no event. Do not mutate earlier tuples or dates. Identity
includes support/version, so a later revised certificate is a different recognized fact.

The event admissibility, ties, separation, ambiguity and scales are exactly M1 within
each valid snapshot. **The union of historical records is not a current separated swing
sequence**: versions/schedules can create conflicting historical events. Current supported
records are distinguished from unsupported records and endpoint-expired-or-revised
records. This last label is deliberately a coarse projection, not causal attribution;
the separate version/information-change audit distinguishes revisions from expiry.
A historical record says it was emitted then; it does not certify latest truth. No retry,
reconstruction from unavailable history, persisted ledger, state service or product code.

With K retained events, advance O(K+N), memory O(K+N); immutable tuple copies cost O(K).
K is unbounded over an unbounded schedule, unlike the current eight-bar detector. The
lineage hash is constant size but is not a substitute for the supplied schedule when
auditing history. All past observations/snapshots influencing accumulated records are
conceptual dependencies. Arbitrary prefixes cannot be erased while retaining their
records and honestly claiming stateless origin invariance.

Same hand example is recognized at supplied cutoff7, not historical confirmation3.
After a W=0 left shift loses its support, H retains the record; an empty H initialized
only at cutoff8 has none. Identical current B and different H yield different histories.
Flat/dual input appends nothing. A repeated unchanged event appends nothing and preserves
first recognition. Later revisions do not delete old facts; independent current results
can differ. This is not a solution to current-window repaint by renaming the old records.

## 5. Quantified property and proof register

Quantifiers range over valid exact inputs/configurations and explicit schedules, not
just sampled prices. “Unchanged full support” means equal ordered consecutive refs and
version identities, no inserted/removed interior observation, same rule and valid global
preconditions in both evaluations. Proofs are elementary mathematical arguments, not
formal-machine verification. Executable finite checks are separately classified.

| ID / property | Premises and statement | Argument, status and limit |
|---|---|---|
| P1 fixed-cutoff causality | For every raw set R and well-timed additional versions V unavailable at t, F(R,t)=F(R∪V,t). M2 additionally fixes prior state and each schedule cutoff before V availability. | `prepare` excludes V before price validation; identical selected B implies same operations. Induct M2 over identical snapshots. PROVED_UNDER_ASSUMPTIONS; no claim when old versions are removed or temporal envelopes malformed. |
| P2 origin invariance | For all valid prefixes with identical last N and eligibility metadata, M1 current events/status at same cutoff/config are equal. | Wrapper/kernels read only B; pure arithmetic/canonical refs deterministic. PROVED_UNDER_ASSUMPTIONS. H1 also has this property yet fails P7. M2 with different H fails; the hand boundary witness is COUNTEREXAMPLE_FOUND. |
| P3 confirmation consistency | For every center e in two windows, full unchanged D(e), valid wrapper and active endpoints imply the same E_j, kind,price,identity in both. No absent old certificate becomes present from only an outer-prefix deletion under these conditions. | Both raw predicates and negative veto are functions only of that quartet, so truth values equal under shifted indices. PROVED_UNDER_ASSUMPTIONS. W=0 endpoint-only property is false, with retained hand counterexample. Recognition clocks are excluded from event equality and separately honest. |
| P4 separation/nontriviality | For all accepted centers j<k, k-j>=2; ties/dual do not force a pivot. At least one valid input emits. | E_j implies R_j; E_(j+1) requires NOT R_j, contradiction. Explicit HIGH110/LOW90 witnesses establish existence; flat/monotone/dual tests establish uncertainty examples. PROVED_UNDER_ASSUMPTIONS, not alternation or directional sufficiency. |
| P5 active expiry/padding | For a one-observation left shift without revisions/insertions, W>=2 and endpoints active both times imply full support survives. | In OLD global coordinates, j>=W+1>=3; support left j-2>=1 is inside NEW, and j+1<=OLD right. Apply P3. PROVED_UNDER_ASSUMPTIONS. W=0 loses center2 while endpoints stay active. Saved records may outlive active support, without staying eligible for current use. |
| P6 saved-result immutability | For every valid M2 step, old record sequence is a prefix of new; old bytes and recognition times are unchanged. | Transition concatenates unseen IDs to immutable tuple; induction on steps. PROVED_UNDER_ASSUMPTIONS. Not latest-truth consistency; revisions/history conflict can remain. Does not repair M1 loss, nor promise bounded historical state. |
| P7 H1 rolling claim | Claim: every old endpoint-eligible event remains, and every old completed still-active event newly appearing is absent unless legitimately new evidence changes it. | Exact retained 201-bar example has zero OLD/13 rediscovered BOTH, same completed evidence endpoints. COUNTEREXAMPLE_FOUND for unqualified rolling claim; seed changes its wider support. No universal bounded-memory impossibility inference. |
| P8 seed/geometry | Common EMA recurrence with unequal initial state need not have equal later ATR; exact event/geometry equality does not follow from small normalized differences. | Recurrence/rounding bound above and 15-bar oracle. COUNTEREXAMPLE_FOUND to guaranteed equal ATR; bound PROVED_UNDER_ASSUMPTIONS for identical later TR sequences only. Discrete selection can amplify changes; six old geometry diagnostics unchanged. |
| P9 version sensitivity | Available revision inside a witness may change its identity/event; cannot affect earlier I_t when originals retained. | Version selection plus explicit support identity; tests revise negative-veto support and delay a missing original. PROVED_UNDER_ASSUMPTIONS for isolation, not that every price revision changes an event. Information-change audit must precede seed attribution. |
| P10 finite-domain validation | All 3^9=19683 declared close words, two adjacent eight-bar windows, W=0 and2. | Independent integer oracle vs Decimal kernel, separation, full-support equality and metrics checked. FINITE_DOMAIN_CHECKED only; not all OHLC, calendars, revisions or markets. |
| P11 adoption feasibility | Can local non-alternating certificates support meaningful reviewed Swing/Regime semantics on session-aware complete markets? | UNRESOLVED. No labels/zones/regime or market acquisition in scope. No success inference from reduced uncertainty or preserved records. |

A scoped incompatibility follows for M2: demanding output include every historical recognized
record and also demanding it be a function only of current B (no declared H) is inconsistent
when two permitted histories end at identical B but only one contains the hand event. Equal
function input would force equal outputs, contradicting record inclusion. This quantifies
over that history-preserving output requirement; it does not rule out bounded local certificates
or policies that explicitly discard old records. Another valid tradeoff is M1 W=2, not a
universal impossibility assertion.

## 6. Original and proposed coverage, not renamed instability

Original opportunity O={OLD events with x and c refs active in NEW}. Lost=O\NEW by original
endpoint key; rediscovered=NEW\OLD with x,c in both active sets and c<=OLD cutoff. Expired
is an OLD event failing endpoint eligibility; new confirmation has c>OLD cutoff. Full-support
opportunity S is the subset of O with identical ordered D(e) available in NEW. Report |O|,
losses, rediscoveries, |S|, support losses and |O\S|; support changes are not natural expiry.
Versions must be audited separately; equality of endpoint metric with a changed support hash
does not establish identical confirmation evidence.

For arbitrary N in the formula, reconstructible centers are 2..N-2 (N-3 possible), while
endpoint-only centers are 0..N-2 (N-1 possible). W=0 omits two left endpoint positions.
For one shift, center2 is the one potentially accepted old center still active but clipped;
each transition can lose at most one such local certificate. W=2 removes those two positions
from active *by an explicit view amendment*, leaving A=N-2. It sacrifices 2/N active bars
(25% for miniature8) but all possible active centers have sufficient left padding. It does
not change any original market W/A/N profile, nor claim a 25% market event cost.

Actual finite-domain comparison (development synthetic words, not independent market trials):

| Model view | Original opportunities | Lost | Rediscovered | Expired | Full-support opportunities | Full-support lost | Coverage excluded |
|---|---:|---:|---:|---:|---:|---:|---:|
| M1 W0 | 17010 | 3402 | 0 | 0 | 13608 | 0 | 3402 (20% of opportunities) |
| M1 W2 | 13608 | 0 | 0 | 3402 | 13608 | 0 | 0 |

The same 3402 events become actual active expiry only under the separately declared W2 view;
they remain **lost still-active events** under W0. M2 preserves past records for both but
inherits the underlying current metrics; reporting zero historical deletions must not replace
those metrics. H1's 13 rediscoveries remain a separate unchanged counterexample. Counts of
model events cannot be interpreted as comparable strategy quality across different semantics.

## 7. Exact amendment/cost comparison and recommendation

| Dimension | Original / H1 frozen | M1 proposed | M2 additional cost |
|---|---|---|---|
| Extreme domain | Running candidate; H1 only eligible i-s>=2 after confirmation | Strict three-neighbor center plus prior raw-turn veto | Same detector per snapshot, historical union not a swing chain |
| ATR/threshold | EMA_TR14 with bounded seed; lambda1.8/1 | No ATR: preceding range with coefficient1 | Same local scale, records preserve historical value/refs |
| W/A/N | W1 26/104/130; D1 60/252/312; M30 40/160/200 | Synthetic8; W0/A8 and support-padding W2/A6 only | Current view same; historical memory unbounded |
| Separation | Two between alternating confirmed extreme candidates | Two via nonrecursive prior-raw veto; no alternation promise | No global separation guarantee across archived versions |
| Ties/same bar | Earliest equal running extreme; x<c | Strict neighbor inequality, no unique event on equal extreme; x=j,c=j+1 | Same predicates; actual r never backdated |
| Dual ambiguity | UNSEEDED waits indefinitely | Ambiguous center abstains and locally vetoes next center | No history fabricated from abstention |
| Active gate | x and c active; older state/ATR implicitly influential | x,c active plus explicit support, report coverage loss | Historical existence separate from current eligibility |
| Information | Accepted F01/F02 permits declared observational/partial outputs | Retain validation, additionally abstain unless complete As-Of contiguous intervals | Same gate; old facts not upgraded by latest revision |
| Downstream | Swing/Regime/.25ATR labels, zones/ranges/material flags | None implemented; local repeated-kind events may invalidate current assumptions | No labels/regime inferred from archive union |

**One recommended next direction:** after independent review and explicit semantic approval,
investigate *local finite-support confirmation certificates with sufficient left padding*,
while keeping recognition/history as a distinct audit concept. Do not carry forward H1 as
a stable replacement or turn M2 into an undisclosed stateful engine. The decision to review
is whether PAQS-Q may replace alternating running-extreme “confirmed Pivot” with a local
certificate, with the disclosed veto/scale/coverage costs. M1 is feasibility evidence, not
the next production algorithm or authorization to implement it.

A separately authorized next experiment should first freeze calendar/quality support and
candidate-domain semantics; retain original metrics, count every excluded support opportunity,
prove common-support consistency, independently test accepted reversal and dual/tie/gap/revision
oracles, and reject any unexplained still-active event changes under its declared padding or
any first-recognition backdating. Also reject a proposal whose only virtue is no events or
lower UNCERTAIN. Market out-of-sample completeness and downstream meaning remain separate
gates. No parameter proposal should be chosen from AVGO direction/P&L or Q/E agreement.

Research deliverables can be correct while mathematical guarantees remain conditional,
real-market completeness **INCOMPLETE**, and product adoption **NOT AUTHORIZED**.
