# TASK-006B-Q R04 independent review

Reviewed task head: `30fa67bcf4521600030ce76bf953fdff87d2e668`  
Frozen plan: `ce53cc86f358590b1778ebd486f91efcb6adc62a`  
Development base: `cc909077a470f7a6e717787307e8a4a8062ff792`  
Review verdict: **CHANGES REQUIRED — one bounded machine-readable evidence defect**

## Finding

### R04-F01 — unresolved W1 segment centers are emitted as zero

Severity: required, localized evidence-integrity defect. It does not change the candidate events,
loss/rediscovery results, veto counts, visual cases, or the correctly stated market limitation.

In [`costs()`](../../tools/research/paqs_q/r04/study.py), the segment keys are constructed with
`str(r["segment"])`, but the counters compare the original value with that string. For an unresolved
row this compares `None == "None"`, which is always false. Consequently every valid W1 cutoff in
both `study-01` and `study-02` contains:

```json
"None":{"centers":0,"events":0,"support":0}
```

Independent decoding of each row's `census_ids` gives **1,921 unresolved active W1 centers** across
the 100 observational cutoffs. The declared per-cutoff segment-center totals therefore add to
8,479 while `active_centers` adds to 10,400, a shortfall of exactly 1,921. The separate
`audit-02.json` aggregate correctly reports `UNRESOLVED_SEGMENT.center_uses = 1921`, so the submitted
machine-readable artifacts contradict each other.

The aggregate reason census remains correct: W1 `CALENDAR_UNKNOWN = 6021`, and the report's event,
transition, support, veto, omission, and market-gate conclusions do not depend on the defective
`costs.segments["None"].centers` value. However, the R04 contract explicitly requires output and
support coverage by calendar segment and machine-readable full failures. R04 cannot be closed while
the per-cutoff canonical result understates that denominator.

## Required focused remediation

1. Normalize the unresolved segment to one explicit sentinel, preferably `UNRESOLVED_SEGMENT`,
   before both key construction and comparison. Do not coerce only the dictionary key.
2. Add a regression asserting, for every valid result, that the sum of per-segment center counts
   equals `active_centers`; also assert that the unresolved count equals the decoded census count.
   Cover a W1 calendar-unknown case and retain the existing D1/M30 checks.
3. Preserve `study-01`, `study-02`, all frozen files, the contract, and prior evidence. Append a
   fresh corrected study/audit artifact from the frozen inputs, or an equivalently complete
   immutable remediation artifact that contains every corrected cutoff. Explicitly deprecate the
   two erroneous per-cutoff fields rather than silently replacing them.
4. Reconcile the corrected artifact against `study-02`: candidate events, endpoint/full-support
   transitions, reasons, veto/omission counts, cases, and chart hashes must remain unchanged. Report
   the exact expected W1 totals: 10,400 active centers, 1,921 unresolved, and 8,479 resolved.
5. Rerun the retained 225-test suite plus the new regression, Ruff, formatting, strict mypy for
   native and `win32`, link/diff checks, and the 486-object protection check. Do not modify product
   code, dependencies, migrations, the user database, the frozen rule, or the recommendation.

Do not start the proposed no-veto experiment or 006C-Q until a focused review closes R04-F01.

## Independently verified evidence

- Git history is linear from the stated base through the contract and frozen plan. All 98 task
  paths are additions in the allowed research scope. The verifier passed at the final head with
  482 base objects plus the contract and three frozen objects, 486 protected identities total.
- The required suite reproduced as **225 passed, 1 warning**. Ruff and format checks passed; strict
  mypy passed with `--explicit-package-bases` for native and `--platform win32`.
- Apart from R04-F01, independent recomputation matched all submitted status, reason, integer total,
  transition, event-catalog, support-witness, fixed-cutoff, and 480-row coverage records. W1/D1 have
  100 valid observational cutoffs each; M30 has 74 valid and 26 insufficient. All 300 AS_OF cutoffs
  remain insufficient.
- The calendar manifest contains 1,501 OPEN, 632 CLOSED, and 51 UNKNOWN facts; all 2,184 retain
  unknown historical availability and incomplete strict qualification. The frozen 2026 closure and
  early-close dates agree with Nasdaq's current market schedule and Nasdaq Trader calendar.
- All 12 final case JSON files contain at most 40 completed-at-cutoff candles. Their selected centers,
  reasons, four-price windows, and chart manifests agree. All 12 `charts-02` images were visually
  inspected; their bytes match `charts-01` as reported.

## Decision boundaries

The calendar-aware conditional rule and its synthetic counterexamples are acceptable within the
declared research assumptions, subject to correcting R04-F01's segment denominator. The AVGO
observation remains retrospective current-QFQ/PARTIAL development evidence. Broad market
applicability and strict historical confirmation remain **INCOMPLETE**. No product adoption, merge,
formal Swing/Pivot definition, or 006C-Q authorization follows from this review.
