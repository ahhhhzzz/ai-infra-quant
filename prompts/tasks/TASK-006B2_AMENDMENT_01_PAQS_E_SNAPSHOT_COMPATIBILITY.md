# TASK-006B2 Amendment 01 — PAQS-E Snapshot Compatibility

Status: **APPROVED FOCUSED AMENDMENT TO TASK-006B2**

Repository: `ahhhhzzz/ai-infra-quant`

Authoritative base branch: `roadmap/no-live-trading`

Authoritative base SHA: `b35bb9ff62a7a88b8cc08a8af5278ea4ab5aca0c`

Task branch: `task/006b2-snapshot-on-demand-market-snapshot`

Parent Task Contract:

- `prompts/tasks/TASK-006B2_SNAPSHOT_ON_DEMAND_MARKET_SNAPSHOT.md`
- Parent Contract commit: `5aba70d3737ebfaa868aa90d062e602067c38024`

PAQS-E semantic review evidence informing this amendment:

- `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md`
- remediated research HEAD: `18a69c1988124b2938682a25a2daddc669a1dcd0`
- focused re-review: `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_FOCUSED_RE_REVIEW.md`
- focused re-review commit: `6495e0d7aa4daac69e530eaa5cdce46d5ef52c0f`

Research documents remain non-authoritative for implementation except where this approved amendment explicitly adopts factual compatibility requirements.

This amendment does **not** modify PAQS-E strategy semantics and does **not** authorize TASK-007A/OpenAI work.

---

## 1. Amendment purpose

The approved TASK-006B2 contract is structurally correct and remains in force.

This amendment adds only two factual/provenance requirements needed so future PAQS-E runtime logic can apply its already-approved downstream degradation and entry-reference policies without parsing free-text warnings or losing provider-delay facts.

The two additions are:

1. machine-readable per-timeframe evidence/source quality and coverage provenance;
2. quote `provider_delay_seconds` provenance.

No other TASK-006B2 semantics are changed.

---

## 2. Amendment A — machine-readable per-timeframe evidence provenance

TASK-006B2 must expose a provider-neutral machine-readable factual block describing the source/evidence state of each shared structural timeframe:

```text
W1
D1
M30
```

Exact internal type/field names may follow repository conventions, but the API/domain semantics must be explicit and testable.

A recommended conceptual shape is:

```text
timeframe_evidence_status:
  W1:
    source_status
    authoritative_bar_count
    excluded_partial_count
    excluded_unknown_count
  D1:
    source_status
    authoritative_bar_count
  M30:
    source_status
    authoritative_bar_count
    missing_elapsed_bucket_count
```

This is a factual provenance/coverage block, not a strategy gate.

### 2.1 Source status

`source_status` should reuse an existing provider-neutral availability/status vocabulary where practical, rather than inventing a strategy-specific quality enum.

At minimum it must preserve whether the relevant upstream source is:

- available;
- unavailable;
- provider error / equivalent truthful failure state.

Do not collapse a provider error into `AVAILABLE` merely because some older bars are present.

Do not derive `LONG_READY`, `WATCH`, `UNCERTAIN`, `DATA_UNAVAILABLE` or any PAQS-E advisory in TASK-006B2.

### 2.2 W1 evidence facts

The snapshot already requires authoritative W1 bars to satisfy:

```text
is_completed == true
coverage == DerivedCoverage.COMPLETE
```

Amendment 01 additionally requires machine-readable diagnostics sufficient to distinguish at least:

```text
authoritative COMPLETE W1 bars included
completed/derived W1 bars excluded because coverage == PARTIAL
completed/derived W1 bars excluded because coverage == UNKNOWN
```

The API must not require downstream PAQS-E code to parse warning strings to discover UNKNOWN/PARTIAL W1 evidence.

If upstream implementation structure means some counts must be derived during snapshot building, derive them deterministically and test them.

### 2.3 D1 evidence facts

Expose at minimum:

```text
D1 upstream/source availability status
authoritative D1 bar count included in snapshot
```

Canonical D1 bars remain completed-only under existing domain invariants.

Do not create a new incomplete D1 bar representation.

### 2.4 M30 evidence facts

Expose at minimum:

```text
M30 upstream/source availability status
authoritative COMPLETE REGULAR M30 count included in snapshot
missing elapsed M30 bucket count, where existing source coverage semantics support it
```

This must remain factual.

TASK-006B2 must not decide whether a missing M30 bucket is enough to prohibit a Trigger or Setup; downstream PAQS-E runtime owns that policy.

### 2.5 Hash inclusion

Any machine-readable timeframe-evidence/coverage facts exposed to downstream analysis must be included in the canonical hash payload.

Therefore changing a model-visible/source-visible timeframe evidence fact must change `snapshot_hash`.

`created_at` remains excluded from the hash exactly as in the parent contract.

---

## 3. Amendment B — quote provider-delay provenance

The `current_price_reference` defined by the parent contract must additionally expose provider-reported delay provenance when available:

```text
provider_delay_seconds
```

The field semantics are factual only.

Rules:

- preserve the provider result value exactly when supplied;
- preserve `null`/absence when the provider does not supply a delay value;
- never fabricate zero delay;
- never infer freshness/staleness from the delay inside TASK-006B2;
- never convert the latest quote into an executable entry reference in TASK-006B2.

Future TASK-007A may combine:

```text
latest_quote_at
retrieved_at
provider_delay_seconds
market-state/session facts
runtime quote_freshness_policy
```

when deciding whether a factual `CURRENT_PRICE_REFERENCE` may become an `EXECUTABLE_ENTRY_REFERENCE`.

That downstream decision is explicitly outside TASK-006B2.

### 3.1 Hash inclusion

If `provider_delay_seconds` is exposed in the snapshot/model-visible factual payload, it must be included in canonical serialization/hash.

Different factual provider delay provenance must therefore produce a different `snapshot_hash`.

---

## 4. No new strategy semantics

This amendment must not add any of the following to the shared snapshot:

```text
analysis_mode decision
Runtime Configuration
PAQS-E degradation decision
CURRENT_PRICE_REFERENCE freshness classification
EXECUTABLE_ENTRY_REFERENCE
FRESH / STALE / DELAYED strategy/runtime classification
LONG_READY
WATCH_LONG
ENTRY_PENDING_REVALIDATION
NO_TRADE
UNCERTAIN
Pivot
Zone
Range
Regime
Event
Setup
Trigger
Follow-through
Invalidation decision
Target decision
RR decision
PAQS-Q score or signal
```

The shared snapshot remains a factual contract only.

---

## 5. No scope expansion

All parent TASK-006B2 boundaries remain unchanged.

This amendment still authorizes **none** of the following:

- OpenAI dependency/client/API key;
- PAQS-E provider port;
- PAQS-E prompt/doctrine runtime packaging;
- PAQS-E Structured Output schema;
- PAQS-E Analyze endpoint;
- Decision Ledger persistence;
- Market Data Store / TASK-006B1;
- PAQS-Q stabilization;
- Dashboard Analyze button;
- database migration;
- broker access/write/autonomous trading.

---

## 6. Required tests added by Amendment 01

In addition to every test/acceptance gate in the parent Task Contract, add focused tests proving at minimum:

### 6.1 W1 provenance

- COMPLETE W1 evidence is counted/included correctly;
- PARTIAL W1 is excluded and counted/represented machine-readably;
- UNKNOWN W1 is excluded and counted/represented machine-readably;
- downstream callers do not need to parse warning text to distinguish these states.

### 6.2 D1 provenance

- D1 source availability status is preserved;
- authoritative D1 included count is deterministic and matches payload.

### 6.3 M30 provenance

- M30 source availability status is preserved;
- authoritative COMPLETE REGULAR M30 included count matches payload;
- missing elapsed bucket count is preserved/derived consistently with existing source-coverage semantics.

### 6.4 Quote delay

- provider delay is preserved when provided;
- provider delay remains null/absent when unavailable;
- zero is not fabricated;
- provider delay does not create any executable/freshness strategy classification.

### 6.5 Canonical hash

- changing timeframe evidence provenance changes the canonical hash;
- changing `provider_delay_seconds` changes the canonical hash when that field is present/model-visible;
- changing only `created_at` still does not change the hash.

### 6.6 No leakage

- public snapshot still contains no Pivot/Zone/Range/Regime/Event/Setup/Advisory/RR/PAQS-Q conclusions;
- no OpenAI/LLM dependency or API behavior is introduced.

---

## 7. Acceptance interpretation

After Amendment 01, TASK-006B2 should give future PAQS-E enough factual information to distinguish:

```text
which timeframe source/evidence is trustworthy or degraded
what evidence was excluded from the authoritative bar payload
what provider-reported quote delay existed
```

without TASK-006B2 itself deciding:

```text
whether PAQS-E may form a Setup
whether Trigger/Follow-through is allowed
whether the quote is executable
whether RR is final
what advisory should be emitted
```

Those remain TASK-007A/007B responsibilities under the accepted PAQS-E Master Spec.

---

## 8. Governing relationship

Implementation must read and obey both:

1. `prompts/tasks/TASK-006B2_SNAPSHOT_ON_DEMAND_MARKET_SNAPSHOT.md`
2. `prompts/tasks/TASK-006B2_AMENDMENT_01_PAQS_E_SNAPSHOT_COMPATIBILITY.md`

Where this Amendment adds a requirement, the addition is mandatory.

Where this Amendment is silent, the parent Contract remains unchanged.

If an apparent conflict is found, stop and report it rather than silently broadening scope.

---

## 9. Final-report additions

In addition to the parent Contract final-report requirements, Codex must explicitly report:

- exact Amendment 01 commit SHA used;
- final machine-readable W1/D1/M30 evidence provenance fields implemented;
- exact quote provider-delay field semantics implemented;
- tests proving PARTIAL/UNKNOWN W1 exclusion/provenance;
- tests proving provider delay preservation/null behavior;
- tests proving these model-visible provenance changes affect `snapshot_hash`;
- confirmation that no PAQS-E advisory/executable-entry/freshness policy was implemented.

**End — TASK-006B2 Amendment 01: PAQS-E Snapshot Compatibility**