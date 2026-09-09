# R02 frozen experiment plan

Development base: `d50d73eea28005bc96e5ed0721b6a8e385ecedf5`.
Contract: `47e7020609e5655927c6aac11a3b1f35b03c96aa`.
Authority: `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`.

Phase A ran before candidate selection. See [cases](phase-a-cases.json),
[D1 census](phase-a-d1-census.json), [handoff blocks](phase-a-separation.json).
All three original normalized AVGO hashes matched the original manifest before evaluation.
There are 2 common-active-event expiry cases, 8 seed-path cases and 2 interacting/unresolved
cases. D1 has 96 insufficient active-comparison outcomes and 4 directional outcomes. All 100
terminal state machines seek LOW with the low candidate only one extreme index after the prior
HIGH: that candidate can never meet separation=2, even when the reversal distance passes.
This is a candidate initialization trap, not permission to weaken the separation requirement.

## Frozen hypothesis (one candidate total)

**H1 / QSTR-R02-ELIGIBLE-SEED-1**: after a confirmed pivot, initialize/update the opposite
candidate only from bars whose index is at least previous extreme+2. Keep the same close reversal,
ATR, active eligibility and two-high/two-low directional gates. A too-close extreme may not become
an immortal candidate that no later permissible but less extreme observation can replace.
This changes the meaning of a swing extreme to the extremum of the admissible post-pivot domain;
it may omit a physically more extreme intervening price. That semantic cost must be disclosed.
See [complete mathematics](../../../research/PAQS_Q_STRUCTURE_R02_CANDIDATES.md).

No second candidate or parameter search is planned. Persistent UNSEEDED dual ambiguity is retained
and tested; there is no evidence that forcing a seed resolves the AVGO D1 mechanism.

## Frozen data and comparison schedule

- Development: exact original AVGO observations; all original scheduled endpoints, including
  M30 insufficient endpoints. Cutoff list is in [freeze.json](freeze.json).
- Additional validation ceiling: **2026-09-09T14:00:00Z**, locked before any acquisition/comparison.
  Last 100 sequential completed endpoints at/before ceiling per unchanged universe member/frame.
- Original [universe](../universe.json) remains 40 = 24 US + 16 HK, no replacement or expansion.
  Additional equities are held out from candidate selection. Do not revise H1 after comparison.
- Public acquisition: explicitly invoked bounded command only, no OpenD, no credentials/accounts,
  no import/test/analysis networking. Check primary provider terms/documentation, try each plausible
  permitted route once; unavailable paths remain in the denominator. Daily sources do not satisfy
  M30, and missing/unverified calendars cannot create COMPLETE W1.

## Outcomes and rejection criteria fixed before candidate comparisons

Event identity = (kind, exact price, extreme observation ref, confirmation observation ref),
independent of algorithm/config IDs. For adjacent valid normal windows, an opportunity is each
OLD event whose extreme AND confirmation are still in the next active observation set. Losses
are missing such events; expiry counts the excluded OLD events separately. Rediscovery is an
added event whose confirmation was already completed at OLD cutoff; new confirmations are separate.
Record denominators, not only failures. No bridging unavailable endpoints.

Four-arm temporal/version policy is the accepted availability-2 policy. Report revision-confounded
changes separately; inspect all actual inputs including warm-up. For left-only material cases,
run the Phase-A seed/ATR interventions with H1 transitions as well as baseline transitions.
Interventions are diagnostic-only and never enter candidate outputs.

Geometry: pair zones by role/rank as in the retained diagnostic, use max absolute bound change /
new terminal ATR and interval IoU. Record births/deaths separately. Retain the prior material flag
(>0.5 ATR, latest pivot replacement, range change, zone-count change or direct directional flip).
Also count every still-eligible event loss independent of the material flag.

Hard correctness violations must be zero. Repeatable seed-only loss/rediscovery of still-eligible
structure, unexplained material left-only cases or loss of legitimate uncertainty reject robustness
acceptance. Lower UNCERTAIN/churn or more trends alone are not success. The AVGO sample informed H1
and is not out-of-sample validation. Missing real coverage keeps the market gate INCOMPLETE.

Use unchanged OFAT profile: lambda 1.7/1.9 (M30 .9/1.1), D1 epsilon .45/.55, age 100/160, L30/60.
No threshold chosen by labels, returns or Q/E agreement. Performance: 7 repeats per declared
synthetic maximum window, p50/max-as-nearest-rank-p95, tracemalloc peak, same hardware, operation
and geometry comparison counts. No SLA. Both engineering and robustness results remain subject
to independent review; production adoption NOT AUTHORIZED.

## Additive paths and validation

Only `tools/research/paqs_q/r02/`, `tests/research/paqs_q/r02/`, this evidence directory and the
R02 candidate document may be added. All development-base files and issued contract immutable.
Run original 97 research cases, 59 related regressions, new tests, Ruff/format, strict mypy/native
and Windows, diff/link/protected-tree checks. New evidence uses exclusive-create writes, so reruns
must select a fresh output directory. Preserve user DB and `phase1_remediation_commit.txt`.
