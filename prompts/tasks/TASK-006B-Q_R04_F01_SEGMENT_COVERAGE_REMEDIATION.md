# TASK-006B-Q R04-F01 — Segment Coverage Evidence Remediation

Status: **APPROVED FOCUSED REMEDIATION ONLY**

Owner authorization: user instruction `继续`, received 2026-09-11

Repository: `ahhhhzzz/ai-infra-quant`

Task branch: `task/006b-q-r04-local-certificate-market-applicability`

## 1. Exact authority and starting point

This contract authorizes only the focused remediation of finding `R04-F01`.

Required lineage:

- authoritative product branch: `roadmap/no-live-trading` at
  `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`;
- R04 development base: `cc909077a470f7a6e717787307e8a4a8062ff792`;
- R04 frozen plan: `ce53cc86f358590b1778ebd486f91efcb6adc62a`;
- reviewed R04 implementation: `30fa67bcf4521600030ce76bf953fdff87d2e668`;
- independent review commit: `4906985744512092fc098340f43e8eec1f41c494`;
- independent review file:
  `docs/reviews/TASK_006B_Q_R04_INDEPENDENT_REVIEW.md` at that review commit.

The contract commit must be a direct child of the reviewed R04 implementation. Begin implementation
only after the task branch is fast-forwarded to the exact contract commit supplied in the handoff.
Do not merge, cherry-pick or copy the review commit into the task branch. Read it by exact SHA.

Before editing, read `AGENTS.md`, `docs/ROADMAP.md`, `docs/MASTER_SPEC.md`,
`docs/ARCHITECTURE.md`, `docs/STRATEGY_SPEC.md`, `docs/phases/PHASE_1_PLAN.md`, the original R04
contract, frozen specification/plan, final R04 report, and the exact independent review. Record
`git status`, preserve every unrelated worktree and untracked user file, and use an isolated clean
worktree if needed.

## 2. Finding to close

`tools/research/paqs_q/r04/study.py::costs` currently constructs segment keys using
`str(r["segment"])` but compares the original segment value with the resulting string. For an
unresolved row, `None != "None"`, so every valid W1 observational cutoff in both retained studies
emits this false counter:

```json
"None":{"centers":0,"events":0,"support":0}
```

Decoding the retained `census_ids` proves the correct frozen totals:

| W1 observational segment coverage | Count |
|---|---:|
| Active centers | 10,400 |
| Resolved-segment centers | 8,479 |
| Unresolved-segment centers | 1,921 |

`audit-02.json` already reports `UNRESOLVED_SEGMENT.center_uses = 1921`, so the defect is a
localized contradiction in each cutoff's `costs.segments` map. Existing candidate events,
endpoint/full-support transitions, losses, rediscoveries, veto/omission counts, case selection,
calendar facts and the `INCOMPLETE` market conclusion are not reopened by this contract.

## 3. Authorized objective

Make segment aggregation use one explicit, canonical unresolved sentinel consistently, prove the
per-cutoff denominators from the decoded census, and append corrected immutable machine evidence.

The corrected invariant for every `VALID` result is:

```text
sum(costs.segments[*].centers) == costs.active_centers
sum(costs.segments[*].support) == costs.complete_support_active
sum(costs.segments[*].events) == costs.events
```

The unresolved key must be exactly `UNRESOLVED_SEGMENT`; the corrected output must contain no
string key `"None"`. Normalization must occur before both key enumeration and counter comparison.
Use an explicit `is None` distinction rather than truthiness or an output-only rewrite.

Do not change what makes a row active, accepted, vetoed, supported or calendar-qualified. Do not
change model identity, support hashes, calendar selection, price selection, cutoff mapping,
recognition semantics, R03 controls, frozen parameters or the recommendation.

## 4. Exact permitted file scope

Existing files that may be modified:

```text
tools/research/paqs_q/r04/study.py
tests/research/paqs_q/r04/test_study.py
```

New files may be added only under:

```text
docs/evidence/TASK_006B_Q/research-04/study-03/
docs/evidence/TASK_006B_Q/research-04/remediation-01/
```

The remediation evidence directory must include, at minimum:

```text
REPORT.md
DEPRECATION.md
DELTA.json
audit-03.json
validation.json
protection.json
```

Do not modify or delete any file under `study-01/`, `study-02/`, `charts-01/` or `charts-02/`.
Do not modify the original R04 `REPORT.md`, `README.md`, `CASE_REVIEW.md`, `CORRECTION_01.md`,
`audit-01.json`, `audit-02.json`, `same-input-delta.json`, original contract, frozen PLAN/spec/
freeze manifest, earlier research, reviews or decisions. This remediation contract is immutable
after issuance.

All other task-head files are protected. In particular, no `src/`, product test, dependency,
migration, database, frontend/API, PAQS-E, provider, credential, archive helper or user-data change
is authorized. No repository configuration or authority document update is authorized.

If a necessary fix cannot fit this exact scope, stop and report the blocker rather than expanding
the task.

## 5. Required implementation and tests

Implement the smallest type-safe correction in `costs()`. A helper is permitted only inside the
authorized module. Preserve exact Decimal behavior and canonical serialization.

Add focused regression coverage that would fail on the reviewed R04 head and pass after the fix:

1. a valid W1 result with unresolved calendar/segment rows must expose
   `UNRESOLVED_SEGMENT` with the decoded nonzero center count and no `"None"` key;
2. for every valid tested result, the three segment-sum invariants in section 3 must hold;
3. resolved D1/M30 segment keys and counts must remain unchanged;
4. invalid/insufficient results must not gain fabricated segment coverage;
5. existing event, reason, support and case-selection assertions must remain unchanged.

Do not weaken, rename or remove existing tests. Synthetic fixtures remain explicitly synthetic and
must not be counted as additional real equities.

## 6. Fresh evidence and reconciliation

Use the exact frozen AVGO normalized inputs, calendar export and hashes recorded in
`research-04/PLAN.md` and `freeze.json`. Access to the user-local archive is read-only and optional
only for the already-defined normalizer attestation; OpenD history and price acquisition request
budgets remain zero. Never write, migrate, checkpoint or bootstrap the user database.

Run the corrected frozen study into the fresh exclusive `study-03/` path. Never overwrite prior
study output. Generate a fresh audit as
`research-04/remediation-01/audit-03.json`. Reusing the existing 12 `charts-02` images is preferred:
prove that all `study-03/cases/*.json` are byte-identical to `study-02/cases/*.json` and that the
existing chart hashes remain unchanged. Do not add duplicate charts merely to change a directory
number.

`DELTA.json` must independently compare `study-03` with `study-02` and record:

- the exact 100-cutoff W1 unresolved count series and aggregate 1,921;
- 10,400 active = 8,479 resolved + 1,921 unresolved;
- absence of `"None"` and presence of `UNRESOLVED_SEGMENT` in corrected valid W1 results;
- equality of all event catalogs, endpoint/full-support transitions, status/reason totals,
  veto/omission metrics, baseline/H1 controls and case bytes;
- equality of D1/M30 segment semantics;
- the explicit volatile fields ignored in comparison, limited to actual run/recognition/audit
  timestamps, runtime measurements and derived serialized byte-size changes.

If any other semantic field changes, do not explain it away: stop, preserve the fresh output and
report the discrepancy for review.

`DEPRECATION.md` must state narrowly that only the per-cutoff
`costs.segments["None"].centers` values in retained `study-01` and `study-02` are invalid; it must
not deprecate their event, transition, reason, support, calendar, case or overall market-gate data.
`study-03` becomes the corrected R04 machine-readable evidence candidate only after focused review.

## 7. Validation and preservation gates

Run and record exact commands, versions, exit codes and counts:

```text
python -m pytest tests/research/paqs_q tests/unit/test_paqs_input.py -ra
python -m ruff check tools/research/paqs_q/r04 tests/research/paqs_q/r04
python -m ruff format --check tools/research/paqs_q/r04 tests/research/paqs_q/r04
python -m mypy --strict --explicit-package-bases tools/research/paqs_q/r04 tests/research/paqs_q/r04
python -m mypy --strict --explicit-package-bases --platform win32 tools/research/paqs_q/r04 tests/research/paqs_q/r04
git diff --check
```

The retained suite baseline is 225 passing tests; the final total must be at least 226 with no
skip/xfail introduced. The existing unrelated Starlette deprecation warning may remain if unchanged.

Preservation evidence must verify Git mode/type/blob identity for every one of the 580 files at
`30fa67bcf4521600030ce76bf953fdff87d2e668` except the two explicitly mutable files in section 4,
plus the immutable issued remediation contract. Thus at least **579 objects** are protected. It
must also prove:

- only the two authorized existing paths changed;
- every other delivery path is an allowed new remediation/study path;
- no deletion, rename, symlink or mode change occurred;
- all relative links resolve and `git diff --check` passes;
- task branch history remains a normal fast-forward descendant of reviewed R04 head;
- authority, review and prior branches remain unchanged.

No browser, Uvicorn, PostgreSQL, migration or full product suite is required because this finding
is isolated to offline research evidence aggregation. Do not claim those checks were run if they
were not.

## 8. Delivery and stop condition

`REPORT.md` must be in Chinese and include:

- exact starting R04 SHA, independent review SHA, contract SHA and final implementation SHA;
- exact changed/added paths;
- before/after segment totals and per-cutoff invariant result;
- `study-03` versus `study-02` semantic delta;
- all validation and protection outcomes;
- confirmation that prior evidence, frozen inputs, product code, user database and authority are
  unchanged;
- unchanged limitations: AVGO-only development data, current-QFQ/PARTIAL, unknown historical
  availability, strict history and broad market applicability `INCOMPLETE`;
- explicit statement that no-veto research and 006C-Q were not started.

Commit and normally push only to
`task/006b-q-r04-local-certificate-market-applicability`. Never force-push, merge, update
`roadmap/no-live-trading`, modify the independent review branch, or start a successor. Read back
the final task-branch SHA and remediation report from GitHub, then stop for focused independent
re-review.
