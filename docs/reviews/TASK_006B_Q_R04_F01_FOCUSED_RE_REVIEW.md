# TASK-006B-Q R04-F01 focused independent re-review

Reviewed remediation head: `c4e21a0204cf6cdd7bb139584b02f01792a49f13`  
Code/test implementation: `151f0fb285f35b35ddbc5840f0920e65c5c17bf6`  
Remediation contract: `0215d687b0ece28dee4b7854226b3e8916420518`  
Original R04 review: `4906985744512092fc098340f43e8eec1f41c494`  
Original reviewed R04 head: `30fa67bcf4521600030ce76bf953fdff87d2e668`  
Review date: 2026-09-11  
Review verdict: **PASS — R04-F01 CLOSED**

## Findings

No remaining Critical, Major or Minor finding was identified in the authorized R04-F01 scope.

The focused remediation closes the sole original finding. This PASS does not change R04's market
applicability conclusion, authorize product adoption, merge PAQS-Q research, or start 006C-Q.

## Closure basis

The fix in `tools/research/paqs_q/r04/study.py::costs` uses an explicit `is None` distinction and
normalizes unresolved rows to `UNRESOLVED_SEGMENT` before both segment-key enumeration and all
counter comparisons. It does not rewrite the source census, event set, calendar qualification,
support hashes, acceptance/veto rules or candidate semantics.

Independent decoding and checks at the reviewed remediation head established:

| Check | Independently reproduced result |
|---|---:|
| W1 observational valid cutoffs | 100 |
| D1 observational valid cutoffs | 100 |
| M30 observational valid / insufficient cutoffs | 74 / 26 |
| All AS_OF insufficient cutoffs | 300 |
| Valid cutoffs satisfying all three segment invariants | 274 |
| Non-valid cutoffs retaining empty segment maps | 326 |
| W1 active centers across 100 overlapping cutoffs | 10,400 |
| W1 resolved-segment centers | 8,479 |
| W1 unresolved-segment centers | 1,921 |

For every valid cutoff:

```text
sum(costs.segments[*].centers) == costs.active_centers
sum(costs.segments[*].support) == costs.complete_support_active
sum(costs.segments[*].events) == costs.events
```

Every corrected valid W1 observational result contains `UNRESOLVED_SEGMENT`, contains no `"None"`
key and retains zero support/events in the unresolved bucket. The exact 100-cutoff unresolved
series sums to 1,921 and independently reconciles `10,400 = 8,479 + 1,921`.

The R04-F01 reconciliation was also independently rerun from the committed script. After treating
its three inventory arrays as unordered inventories, the regenerated result equals the committed
`DELTA.json`. All substantive assertions passed: event catalogs, endpoint/full-support
transitions, status/reason totals, veto/omission metrics, baseline/H1 controls and D1/M30 segment
maps are unchanged. The 12 case JSON files are byte-identical to study-02; `audit-03` equals
`audit-02` except for its actual `checked_at` value; protected charts retain their hashes.

## Validation and preservation

Independent Linux reproduction used Python 3.12.14 with the pinned project development versions:

- `python -m pytest tests/research/paqs_q tests/unit/test_paqs_input.py -ra`:
  **234 passed, 1 unchanged Starlette warning**;
- Ruff check and format check over the R04 implementation/tests and remediation verification
  scripts: PASS;
- strict mypy with explicit package bases, both native and `--platform win32`: PASS;
- final-head `protect.py`, link/diff and worktree checks: PASS;
- protected mode/type/blob identities: **579**;
- remote lineage: `30fa67b -> 0215d68 -> 151f0fb -> c4e21a0`, with no merge;
- the task branch alone advanced from the contract to the remediation head; the other 55 recorded
  remote heads, including authority and the original review branch before this closure commit,
  were unchanged.

Only the two authorized existing files changed. All other delivery paths are new files under the
authorized `study-03/` and `remediation-01/` directories. Prior studies, charts, frozen inputs and
plans, product/runtime code, dependencies, migrations and user data remain unchanged.

## Non-blocking reproducibility observation

On Linux, the regenerated `DELTA.json` orders three inventory arrays differently from the Windows
artifact because `Path` ordering is platform-sensitive. Sorting `byte_identical_files`,
`compared_files` and `ignored_exact_volatile_fields` yields complete JSON equality. Their order is
not used by an assertion or research claim, so this is not an R04-F01 finding and does not block
closure. A later new evidence tool may sort stored POSIX path strings if byte-identical
cross-platform manifests become a stated requirement; retained R04 evidence must not be rewritten.

## Decision boundaries

`study-03` is accepted as the corrected R04 machine-readable evidence only for the localized
segment aggregation field described by `DEPRECATION.md`. The retained study-01/study-02 events,
transitions, reasons, support, calendar, cases and market-gate evidence remain valid within their
original stated limits.

R04 remains AVGO-only retrospective development evidence using current-QFQ/PARTIAL observations
with unknown historical availability. Strict historical confirmation and broad market
applicability remain **INCOMPLETE**. The current candidate is not adopted as the formal PAQS
Swing/Pivot definition. Any prior-raw-veto ablation requires a new frozen contract and independent
review before it can inform further research.
