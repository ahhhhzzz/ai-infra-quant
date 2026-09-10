# R04 proof premises and observation boundaries

This elaborates, without replacing, the [frozen specification](../../../research/PAQS_Q_LOCAL_CERTIFICATE_MARKET_APPLICABILITY_R04.md).
It does not adopt a PAQS Pivot or change R03 M2. The
[M2 clarification](../research-03/remediation-01/M2_STATE_CLARIFICATION.md) remains authoritative
for what R03 retained: external replay inputs are still required; no price-snapshot ledger is
introduced by R04's explicit research recognition records.

## Conditional argument

For center j define S_j as ordered price/version observations j−2 through j+1, the ordered
calendar facts for their slots and all intervening dates, and the rule/mode/aggregate qualification.
Each selected observation retains coverage, adjustment, completion and availability. Let A_j be
the calendar/quality eligibility of that complete support. A rejected or unknown prior raw
predicate is not false. The output is A_j AND (D_j XOR U_j) AND NOT(D_(j−1) OR U_(j−1)).

If two valid evaluations have identical ordered S_j and active extreme/confirmation endpoints,
each arithmetic operand and each positive/negative slot fact is identical. Thus A_j, D_j, U_j,
D_(j−1), U_(j−1), kind and price are identical. This establishes conditional output consistency.
It establishes neither an alternating Swing sequence nor historical knowability nor completeness
of the supplied market calendar. No set-only or endpoint-only premise can substitute for S_j.

For a one-observation left shift, W>=2 ensures a still-active center retains its two earlier
prices. All fixed horizons satisfy this. Calendar invariance, ordering, no inserted/deleted
evidence and global input validity are additional premises, not consequences of W>=2.
Accordingly the original endpoint metric is retained alongside full-support opportunities,
coverage exclusions, changed witness identities and information-change counters.

## Executable counterexamples and limits

The dedicated [tests](../../../../tests/research/paqs_q/r04/test_calendar_model.py) establish:

- Delete only j−2 while j−1,j,j+1 form a raw HIGH: current raw=True but prior raw=None;
  MISSING_EXPECTED_SESSION prevents acceptance. Restoring that actual expected row enables the
  quartet; the change is support/information change, not magical reseeding.
- Same price endpoints with a later calendar version: OLD remains identical to independent
  OLD at its own cutoff; NEW records one calendar revision, one changed witness and one excluded
  full-support opportunity. Equal endpoints do not imply identical evidence.
- A late calendar fact is absent at OLD. Unknown-version ordering conflicts fail closed.
  Future malformed payloads are isolated before semantic validation. A later price revision
  is selected only at NEW, counted as revised information, and never edits OLD.
- Missing expected OPEN sessions differ from explicitly CLOSED weekends/holidays/exceptional
  closures. US March2026 DST changes UTC09:30-equivalent from14:30 to13:30; HK lunch/overnight
  remains prohibited, and within-segment missing buckets remain missing.
- A synthetic Thursday-completed holiday W1 has a later nominal Monday endpoint. Factual close,
  not nominal interval end, determines eligibility. An absent civil-day fact cannot certify it.
- Ties, dual raw turns and zero preceding range do not force output. Two independent HIGHs
  remain HIGH/HIGH. A current negative-veto rule does not establish alternation.
- Both public and JSON price paths preserve F01 quality relationships. PARTIAL/UNKNOWN is not
  upgraded; invalid or contradictory selected price quality fails. Current-QFQ and unknown
  availability cannot become strict AS_OF merely because observed OHLC is usable.

The unchanged168 research controls retain H1's13 rediscoveries and the original R03 W0 losses /
W2 costs. R04 does not rename these observations or recompute a favorable alternative history.

## Clocks and lineage

OHLC does not tell us the exact intrabar instant of the high/low. The inherited `extreme_time`
field identifies the extreme bar's interval end, **not** the tick occurrence time. In W1 this is
the nominal next-Monday boundary. The original Bar's `completed_at` and event `reversal_time`
carry factual close times; slot qualification checks the final evidenced session. Case JSON
retains each bar's start/end/completed_at so these clocks can be distinguished. Chart labels
use interval starts and the exact calculation cutoff, with no candle completed after cutoff.

`available_at=null` means historical availability is unknown. `recognized_at` is the UTC time
when this research execution actually first encountered the witness; `first_seen_scheduled_cutoff`
is an experiment coordinate. Neither the old cutoff nor reversal time is substituted for actual
recognition. Fresh reproduction intentionally changes run timestamps; semantic numeric metrics
and deterministic case selection should reproduce on the frozen inputs.

Complete computational support is relative to the qualified, supplied derived observations.
The [normalizer attestation](normalizer-attestation.json) verifies immutable archive memberships
and exact original datasets using unchanged006A helpers. COMPLETE W1/M30 constituent coverage
is relative to that captured schedule. R04 separately demands explicit OPEN/CLOSED facts for
the civil dates it crosses; it does not certify that the provider calendar itself was complete,
historically available or independently correct. The real Capture's aggregate PARTIAL/current-QFQ
and calendar coverage_complete=false remain visible. Unknown pre2026 closure dates remain unknown.

An observed local shape is therefore not a historical strict certificate. The real AS_OF gate
and independent-equity market gate remain unresolved even when conditional synthetic tests pass.
