# TASK-006B — Focused Remediation 01

Status: **APPROVED FOCUSED REMEDIATION — TASK-006B ONLY**

Repository: `ahhhhzzz/ai-infra-quant`

Task branch: `task/006b-paqs-structure-engine`

Authoritative base branch: `roadmap/no-live-trading`

Authoritative base SHA: `7909f1c04f7049cf1ccec78a3d5023ae801b7177`

Independently reviewed implementation HEAD: `a9365be8e57a4a92ed1f6142c6a228b47c2a4c82`

Parent Task Contract: `prompts/tasks/TASK-006B_PAQS_STRUCTURE_ENGINE.md`

This remediation is limited to two independently confirmed defects. It does not authorize unrelated refactoring, strategy redesign, parameter changes, persistence changes, or any TASK-006C behavior.

## 1. Confirmed defect A — W1 UNKNOWN coverage enters confirmed structure

### Problem

TASK-006B permits only legitimate completed source coverage to enter confirmed structure calculations.

The reviewed implementation currently normalizes W1 bars when:

```text
is_completed == true
AND
coverage != PARTIAL
```

This also admits:

```text
coverage == UNKNOWN
```

TASK-006A can legitimately expose a finalized W1 with `DerivedCoverage.UNKNOWN` when the calendar/schedule basis is unavailable. Such a bar may remain useful as diagnostic input metadata, but it must not contribute to confirmed TASK-006B structure.

If UNKNOWN W1 bars enter normalized structure, they can affect:

```text
bar_count
ATR
Micro/Major Pivot
Swing labels
Key Levels / Zones
Range
Base Regime
```

This violates the parent Task Contract's legitimate-source-coverage boundary.

### Required remediation

For W1 structure normalization, require explicit:

```text
bar.is_completed
AND
bar.coverage is DerivedCoverage.COMPLETE
```

`UNKNOWN` and `PARTIAL` W1 bars must not enter confirmed structure calculations.

Do not change TASK-006A to fabricate or upgrade calendar coverage. The structure engine must fail closed at its own eligibility boundary.

D1 remains governed by the existing canonical completed-D1 contract. M30 must continue to require explicit COMPLETE derived coverage.

### Required tests

Add deterministic regression coverage proving at minimum:

1. `COMPLETE` W1 is eligible;
2. `PARTIAL` W1 is excluded;
3. `UNKNOWN` W1 is excluded;
4. excluded UNKNOWN/PARTIAL W1 bars do not increase structure `bar_count`;
5. excluded UNKNOWN/PARTIAL W1 bars do not contribute to ATR warm-up/readiness;
6. excluded UNKNOWN/PARTIAL W1 bars cannot create/change Pivot, Zone, Range, or Base Regime results;
7. adding excluded bars to an otherwise identical prefix leaves legitimate structure unchanged.

The existing M30 COMPLETE-coverage behavior must remain unchanged.

## 2. Confirmed defect B — calculated_at can precede input as_of_timestamp

### Problem

The reviewed application currently records `calculated_at` before retrieving/building the PAQS input bundle.

The TASK-006A input bundle subsequently defines:

```text
as_of_timestamp = max(
    local input-query clock,
    provider retrieval timestamps,
    calendar retrieval timestamp
)
```

Therefore a provider retrieval timestamp may be later than the earlier captured structure `calculated_at`, producing impossible provenance such as:

```text
calculated_at < as_of_timestamp
```

A structure snapshot cannot claim to have been calculated before the data cutoff/retrieval facts it used.

### Required remediation

Obtain/build the PAQS input bundle first.

Only then establish the structure calculation timestamp.

The final snapshot must always satisfy:

```text
calculated_at >= as_of_timestamp
```

The smallest acceptable application rule is logically equivalent to:

```text
bundle = input_queries.current_bundle(...)
calculated_at = max(self._now(), bundle.as_of_timestamp)
```

Then build the snapshot from that same bundle and timestamp.

A narrowly scoped domain-level invariant rejecting `calculated_at < as_of_timestamp` is allowed as defense in depth, but is not permission for broader timestamp refactoring.

### Required tests

Add deterministic regression tests proving at minimum:

1. when provider/input `as_of_timestamp` is later than the structure query clock, final `calculated_at == as_of_timestamp` or is later;
2. when query clock is later, final `calculated_at` uses that later legitimate time;
3. final snapshot always satisfies `calculated_at >= as_of_timestamp`;
4. the input bundle is built exactly once for one structure request and the snapshot uses that same bundle;
5. no future market data is fabricated or fetched solely to make timestamps ordered.

## 3. Focused audit conclusions to preserve

Independent follow-up inspection found no additional blocker requiring remediation in this cycle.

In particular:

- top-level `PARTIAL` PAQS input may still contain legitimate COMPLETE bars; TASK-006B may calculate from those legitimate bars while preserving PARTIAL quality/warnings;
- `INVALID` input must continue to suppress structure;
- D1 completed-bar semantics remain unchanged;
- M30 must continue to require `DerivedCoverage.COMPLETE`;
- current provider QFQ replay-unsafety remains visible and is not upgraded;
- no TASK-006C Event/Transition/Trigger/Retest logic is authorized.

Do not reinterpret this focused remediation as a broad redesign of input-quality semantics.

## 4. Scope restrictions

Do not implement or modify behavior for:

```text
Break Attempt
Breakout / Breakdown
Failed Breakout / Failed Breakdown
Retest
Role Flip
Regime Transition
Trigger
Follow-through
Setup
Invalidation / Stop
Target
RR
Entry Advisory
Holder Advisory
Quality / Composite Score
Ranking
Paper Portfolio
Backtesting
brokerage-account access
broker-write capability
```

Do not add a migration.

Do not modify:

- `docs/phases/PHASE_1_PLAN.md`
- `docs/reviews/PHASE_1_INDEPENDENT_REVIEW.md`
- `docs/reviews/PHASE_1_POST_REMEDIATION_REVIEW.md`
- `src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py`

If `phase1_remediation_commit.txt` exists locally, leave it untouched/untracked/uncommitted.

## 5. Validation

Run at minimum:

```text
full pytest
focused TASK-006B tests including the new regressions
ruff check
ruff format --check
mypy
fresh SQLite migration/startup
/health
/openapi.json
```

If OpenD is unavailable, report the live smoke test as blocked/environmental evidence; do not fabricate live structure evidence.

## 6. Final report

Report:

- authoritative base SHA verified;
- reviewed implementation HEAD verified;
- remediation contract present;
- final task-branch HEAD SHA;
- exact remediation changed-file list;
- exact fix for W1 UNKNOWN coverage;
- exact fix for `calculated_at >= as_of_timestamp`;
- full/focused test results;
- Ruff/mypy/startup evidence;
- OpenD evidence separately identified;
- confirmation that no migration, TASK-006C, advisory/score/ranking, brokerage-account, or broker-write behavior was introduced.

Do not merge into `roadmap/no-live-trading`.

Do not start TASK-006C.

Stop after pushing the remediation.