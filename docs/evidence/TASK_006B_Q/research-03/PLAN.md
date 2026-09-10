# R03 frozen study definition

Status: PROPOSED_SEMANTICS; synthetic mathematical study, not adoption.
Base ddb61c15f1aea026b26c116f35fa1e2b0b0d055a; issued contract
8338144f0185f1b5b416daf08d5bcbff074bb345. Commit this file before executing new
comparisons or enumeration. Preserve this blob; corrections require separate addenda.

## Questions and two models

Distinguish a current reconstructible witness from an immutable record of what was
actually recognized at a cutoff. Neither endpoint references nor saved bytes alone
prove rolling consistency. Baseline/H1 remain unchanged controls.

**M1, PROPOSED_SEMANTICS:R03-LOCAL-1**: minimal finite local witness, not a swing engine.
For eligible observations numbered from zero, define raw predicates at center j>=1,
with successor j+1: v_j=H_(j-1)-L_(j-1)>0; HIGH requires H_j strictly greater than
both neighboring highs and H_j-C_(j+1)>=v_j; LOW symmetrically requires L_j strictly
less than both neighboring lows and C_(j+1)-L_j>=v_j. Ties do not establish a unique
extreme. Two true predicates are ambiguous, not an ordered high/low path.
An event at j>=2 is emitted iff exactly one raw predicate at j is true AND neither
raw predicate at j-1 is true. The preceding raw predicate is a veto even if ambiguous
or itself vetoed. Thus accepted centers are separated by >=2 without recursive state.
Support is exactly the four consecutive observations j-2 through j+1 (including the
negative veto evidence). Reversal completion is j+1; actual recognition is the first
evaluation containing that full witness. No retrospective knowledge claim.

Use exact Decimal Context(50, HALF_EVEN), inherited 38,18 input bounds, stable
observation refs plus version availability identities. No EMA; v is a proposed
local scale, coefficient 1, chosen as a transparent unit-range oracle, not optimized.
Keep inherited prepare/validate/availability boundaries. Additional strict model
precondition: COMPLETE AS_OF observations and consecutive equal-duration intervals;
otherwise INVALID or UNCERTAIN, never fill gaps or upgrade quality. This restriction
deliberately excludes session gaps and observational market adoption.

Miniature N=8. W=0/A=8 exposes support loss; W=2/A=6 is the mathematical minimum
left padding that protects a still-active four-observation witness. These are two
views of the same model, not market parameter candidates. No labels/regime/zones.
Maximum raw input remains inherited 100000; no network/DB. Model outputs immutable
tuples. Revisions produce different witness identities and a separately measured
information-change classification, never a seed-only explanation.

**M2, PROPOSED_SEMANTICS:R03-RECORD-1**: in-memory immutable tuple of first-recognition
records fed validated M1 snapshots in strictly increasing cutoff order. Initial state
is explicitly empty with a lineage hash. For each snapshot, append previously unseen
witness IDs with actual recognition cutoff and predecessor lineage; never rewrite old
records. Active-current IDs, expired endpoints and unsupported/revised old witnesses
are separate projections. Revisited old IDs are not newly confirmed. No persistence,
no historical initialization inference, no claim bounded-state origin invariance.
Invalid/uncertain snapshots do not establish events. State includes the entire supplied
snapshot sequence and grows O(total recognized events + steps); it is extra input.

## Predeclared propositions and falsifiers

P1 fixed-cutoff causality for both models under identical starting state/schedule and
unchanged eligible information; unavailable future payloads cannot affect output.
P2 M1 origin invariance for identical bounded observations, metadata and configuration.
P3 M1 rolling equality only for identical ordered full support/version identities and
unchanged valid global preconditions; no inserted observation inside that support.
P4 accepted M1 centers are >=2 apart; strict local uniqueness, XOR and positive scale
do not force a pivot in flat, monotone or dual-ambiguous data.
P5 W>=2 removes support clipping for events whose endpoints remain active; W=0 does
not. Report original endpoint opportunities/losses/rediscoveries alongside full-support
opportunities and their coverage cost, including a synthetic boundary-loss witness.
P6 M2 stored-record immutability by append-only induction; origin invariance fails if
state differs. It does not repair current M1 stability or guarantee revision truth.
P7 baseline/H1 fixed-cutoff origin invariance does not imply rolling consistency;
reproduce the retained 201-bar/13-event counterexample exactly.
P8 bounded EMA seed can affect shared confirmation/geometry; exact recurrence equality
and inherited .5 ATR/material flags are different assertions.
No universal impossibility theorem. Claims not proved remain UNRESOLVED.

## Frozen hand examples and domain

M1/M2 accepted HIGH: eight consecutive synthetic bars, all O=C=100,H=101,L=99 except
center2 O=C=109,H=110,L=108. Center2 confirms at3 (distance10>=2), prior raw veto false.
Mirror about 200 accepts LOW90. Repeat with center4 for an event surviving one shift.
Dual rejection: center2 H110,L90,C100; both predicates true. Equal high at successor
rejects unique HIGH. Flat and monotone have no strict internal extremum.
Retain R02 four-bar constant-ATR unit trap and mirror (omitted LOW90 vs accepted LOW95),
ATR 30,2,...,2 hand series, and exact H1 rejection fixture without modifications.

Exhaustive domain: all 3^9=19683 nine-bar close words over {99,100,101}, O=C,
H=C+1,L=C-1, consecutive synthetic M30 intervals, no random seed. Compare first8 and
last8 for W=0 and W=2; independently check formulas, separation, support stability,
old endpoint metrics and support coverage. Budget 120 seconds; if exceeded stop and
record incomplete count without extrapolation. This finite domain is not a theorem
about general OHLC or markets. Hand fixtures cover wider/non-symmetric OHLC and ambiguity.
Test available/future revisions, delayed evidence, unavailable malformed payload,
invalid/contradictory quality, legitimate partial/unknown, incomplete and missing bars.
Check prefixes, fresh processes and hostile Decimal contexts. Evidence uses fresh
paths with exclusive creation. Do not run existing raw-market acquisition/studies.

## Validation and stop

Run all retained 132 research tests plus new R03 tests, Ruff/format, native and win32
strict mypy over added Python, links/diff/allowlist and all465 base plus issued-contract
mode/type/blob checks. Do not rerun unrelated product/browser/database suites.
One final recommendation must name a semantic tradeoff, acceptance/rejection oracles
and unproven scope; no trend-rate goal, market PASS, product adoption or 006C-Q.
