# TASK-006B2 Remediation 01 — W1 As-Of Provenance

Status: **APPROVED FOCUSED REMEDIATION CONTRACT**

Repository: `ahhhhzzz/ai-infra-quant`

Authoritative base branch: `roadmap/no-live-trading`

Authoritative base SHA: `b35bb9ff62a7a88b8cc08a8af5278ea4ab5aca0c`

Task branch: `task/006b2-snapshot-on-demand-market-snapshot`

Parent Task Contract:

- `prompts/tasks/TASK-006B2_SNAPSHOT_ON_DEMAND_MARKET_SNAPSHOT.md`
- Parent Contract commit: `5aba70d3737ebfaa868aa90d062e602067c38024`

Mandatory Amendment 01:

- `prompts/tasks/TASK-006B2_AMENDMENT_01_PAQS_E_SNAPSHOT_COMPATIBILITY.md`
- Amendment commit: `99e06a572eb1fbc6358cda443a8d6c6e41be4fb0`

Reviewed implementation SHA:

- `10692de359b5818c28a2e724a893b5b884e4c79e`

Independent review verdict for that exact implementation SHA:

```text
NEEDS REMEDIATION
```

This remediation is intentionally narrow. All TASK-006B2 behavior not explicitly changed below remains governed by the parent Contract + Amendment 01 and must not be broadened.

---

## 1. Confirmed finding

### R-01 — Completed W1 nominal interval end can push snapshot As-Of into the future

**Severity: HIGH**

Current W1 derivation uses a nominal weekly interval:

```text
interval_start = ISO-week Monday 00:00 market-local
interval_end   = next Monday 00:00 market-local
```

A W1 bar may nevertheless become legitimately completed earlier than that nominal `interval_end` when the official/product calendar shows that the final trading session of the week has ended and all required D1 source dates are present.

Therefore, after the final trading session on Friday (or an earlier holiday-shortened final session), it is valid for:

```text
W1.is_completed == true
W1.coverage == COMPLETE
```

while:

```text
W1.interval_end > current factual/request time
```

The reviewed TASK-006B2 implementation currently adds every included W1 `interval_end` into the final snapshot `as_of_timestamp` candidate set.

That can produce:

```text
snapshot.as_of_timestamp = a future Monday boundary
snapshot.created_at       = clamped to that same future time
```

for a snapshot requested immediately after the last actual trading session of the week.

This is incorrect provenance. A nominal aggregation bucket boundary is not evidence that the product observed facts at that future timestamp.

It violates the approved snapshot meaning:

> `snapshot.as_of_timestamp` is the latest factual time boundary necessary to describe the information actually available for the snapshot request.

It also risks contaminating later:

```text
Decision Ledger ordering
model audit records
same-snapshot comparisons
strict As-Of reasoning
snapshot hashes
```

---

## 2. Required semantic correction

TASK-006B2 must distinguish:

```text
bar interval geometry
```

from:

```text
factual observation / retrieval / completion provenance
```

A W1 `interval_end` may remain in the W1 bar payload and hash as part of the bar's canonical interval geometry.

However, a nominal W1 `interval_end` **must not by itself advance `snapshot.as_of_timestamp` beyond the latest factual information time available to the request.**

The implementation must not claim a future timestamp merely because an already-completed week is represented with a next-Monday bucket boundary.

### Minimum invariant

For the current Snapshot-on-Demand runtime:

```text
snapshot.as_of_timestamp <= effective snapshot creation/request factual time
```

except where an upstream factual/provider timestamp itself is legitimately later and the existing contract requires truthful preservation; such an upstream future timestamp should be treated as an explicit provenance anomaly rather than silently justified by nominal bar geometry.

For normal valid inputs, final `as_of_timestamp` must remain grounded in actual factual/provenance timestamps such as:

```text
PaqsInputBundle.as_of_timestamp
quote ProviderResult.retrieved_at
market-state ProviderResult.retrieved_at
calendar retrieved_at
adjustment_as_of
successful latest_quote_at
D1 factual provider/retrieval timestamps where used
```

Do not use a future nominal W1 bucket boundary as evidence time.

M30 interval-end handling may remain only if it is already guaranteed by existing completed-bar invariants to be `<=` the acquisition cutoff. Do not broaden this remediation into unrelated time-model redesign.

---

## 3. Implementation guidance

Preferred minimal correction:

- remove included W1 `interval_end` values from the set used to advance `snapshot.as_of_timestamp`; or
- equivalently ensure nominal W1 interval geometry cannot advance As-Of beyond the actual factual/acquisition boundary.

Do not change:

```text
W1 interval_start / interval_end representation
W1 completed/COMPLETE eligibility
W1 cap 156
D1 cap 500
M30 cap 200
snapshot schema version unless genuinely required
canonical bar serialization
quote reference-only semantics
market-state reference-only semantics
Amendment 01 timeframe provenance
provider_delay_seconds provenance
```

Do not retrofit a new `completion_timestamp` field unless it is strictly necessary. Prefer the smallest correction consistent with the approved factual contract.

---

## 4. Required regression tests

Add a focused regression proving the real boundary case.

### 4.1 Friday/final-session completion case

Construct a deterministic W1 input where:

```text
market week final trading session has ended
W1 coverage == COMPLETE
W1 is_completed == true
W1 nominal interval_end == next Monday
snapshot request / acquisition time is Friday after final session
```

Assert:

```text
W1 is included in snapshot.w1_bars
W1.interval_end remains next Monday nominal geometry
snapshot.as_of_timestamp does NOT advance to next Monday
snapshot.created_at does NOT advance to next Monday
snapshot.as_of_timestamp is grounded in the actual latest factual/provider time
```

### 4.2 Holiday-shortened week variant

If practical without expanding scope, include a shortened-week fixture where the last official session is earlier than Friday and the same invariant holds.

At minimum one deterministic final-session-before-nominal-interval-end regression is mandatory.

### 4.3 Existing hash invariants

After remediation, preserve existing tests proving:

```text
created_at alone does not change snapshot_hash
model-visible factual/provenance changes do change snapshot_hash
W1 interval geometry remains hashed as part of the W1 factual bar
```

If the corrected As-Of value changes relative to the buggy implementation, the resulting snapshot hash is expected to change because As-Of is model-visible factual provenance.

Do not preserve the previous golden hash merely for compatibility if that fixture encoded incorrect As-Of semantics; update a golden fixture only when required and explain why.

---

## 5. Required no-regression boundaries

The remediation must preserve all previously accepted TASK-006B2 boundaries:

```text
no OpenAI/LLM code
no PAQS-E reasoning/advisory
no executable-entry/freshness policy
no PAQS-Q strategy changes
no Pivot/Zone/Range/Regime/Event/Setup/Trigger/Follow-through/Invalidation/Target/RR decision fields
no database snapshot persistence
no Alembic migration
no Dashboard Analyze workflow
no broker account/write behavior
no TASK-006B1
no TASK-007A
```

Legacy TASK-006B Structure semantics must remain unchanged.

Protected Phase 1 files remain unchanged.

`phase1_remediation_commit.txt`, if present locally, remains untracked, untouched, unstaged, and uncommitted.

---

## 6. Documentation status

Do not perform broad documentation rewrites.

If an engineering-guide sentence currently implies that any included W1 interval boundary may define As-Of, correct only that wording as necessary.

Do not change Roadmap scope.

Do not start PAQS-E implementation.

---

## 7. Validation

Run all parent TASK-006B2 + Amendment 01 validation again, including at minimum:

```text
focused remediation regression
full TASK-006B2 focused suite
full pytest
ruff check
ruff format --check
mypy
startup / health / OpenAPI checks
fresh SQLite migration verification
```

Live OpenD smoke remains optional/environmental.

---

## 8. Git / stop condition

Implement remediation on the same branch:

```text
task/006b2-snapshot-on-demand-market-snapshot
```

Before editing, verify the remediation-contract commit is current HEAD or an ancestor of HEAD and that the reviewed implementation SHA `10692de359b5818c28a2e724a893b5b884e4c79e` is an ancestor.

Use targeted staging only.

Commit and push only the same task branch.

Do not merge into `roadmap/no-live-trading`.

Stop for independent re-review after push.

Do not start TASK-007A or TASK-006B1.

---

## 9. Codex final-report requirements

Report:

- authoritative base SHA;
- reviewed implementation SHA;
- remediation-contract commit SHA;
- final remediation HEAD SHA;
- exact changed files;
- exact As-Of bug fix;
- regression fixture demonstrating completed W1 with nominal future interval end;
- resulting `as_of_timestamp` / `created_at` behavior;
- hash/golden-fixture impact, if any;
- focused/full validation results;
- push verification;
- confirmation no scope leakage occurred.

**End — TASK-006B2 Remediation 01: W1 As-Of Provenance**