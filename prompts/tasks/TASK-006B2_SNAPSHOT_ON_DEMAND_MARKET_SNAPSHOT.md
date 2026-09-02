# TASK-006B2 — Snapshot-on-Demand Current Market Snapshot Contract

Status: **APPROVED IMPLEMENTATION TASK CONTRACT**

Repository: `ahhhhzzz/ai-infra-quant`

Authoritative base branch: `roadmap/no-live-trading`

Authoritative base SHA: `b35bb9ff62a7a88b8cc08a8af5278ea4ab5aca0c`

Task branch: `task/006b2-snapshot-on-demand-market-snapshot`

Decision authority:

- `docs/decisions/PAQS_DUAL_BRANCH_ARCHITECTURE.md` (`PAQS-DUAL-001`)
- `docs/ROADMAP.md`
- `docs/REQUIREMENTS_MATRIX.md`

Research inputs adopted by this task only where explicitly stated below:

- `docs/research/PAQS_DUAL_BRANCH_ARCHITECTURE_REVIEW_ADDENDUM_A.md`
- `docs/research/PAQS_DUAL_BRANCH_ROADMAP_MIGRATION_PROPOSAL.md`
- `docs/research/PAQS_E_NAKED_PRICE_ACTION_DOCTRINE.md` only for the factual-vs-reasoning separation; this task does not implement PAQS-E reasoning.

This Task Contract is the implementation authority for TASK-006B2. Research documents by themselves are not implementation authority.

---

## 1. Objective

Implement one provider-neutral, immutable, current **Snapshot-on-Demand Market Snapshot** that freezes the factual market inputs used by future PAQS-E and PAQS-Q analyses.

The task answers only:

> **What exact market facts were available to the product for this Security when the user requested an analysis snapshot?**

It does not answer:

> Is this a Buy, Sell, Long, Hold, Range, Breakout, Setup, good RR, or valid trade?

The canonical flow is:

```text
supported Security
    -> existing read-only market-data queries
    -> existing PAQS input derivation
    -> current quote / market-state reference
    -> canonical factual snapshot
    -> canonical serialization
    -> SHA-256 snapshot_hash
```

No LLM call and no strategy interpretation belongs in this task.

---

## 2. Product runtime semantics

TASK-006B2 implements the factual snapshot used by the approved Snapshot-on-Demand runtime.

One request:

```text
user/application requests current snapshot
    -> retrieve current legitimate facts
    -> freeze one immutable snapshot object
    -> return it
    -> request ends
```

A later quote or completed bar must not mutate an already returned in-memory snapshot object.

A later request creates a new snapshot.

This task does not persist snapshots and does not implement the future immutable Decision Ledger.

---

## 3. Shared branch boundary

The snapshot is shared factual infrastructure for both:

```text
PAQS-E — LLM-native Expert Reasoning branch
PAQS-Q — deterministic Quant/reference branch
```

The snapshot must not contain one branch's strategy conclusions as input facts for the other branch.

In particular TASK-006B2 must not expose current TASK-006B Structure Engine outputs inside the shared market snapshot.

Forbidden snapshot facts include:

```text
Micro Pivot
Major Pivot
Swing classification as strategy output
Key Level derived by PAQS Structure
Zone
Range
Base Regime
Breakout
Failed Breakout
Retest
Trigger
Follow-through
Setup
Invalidation decision
Target decision
RR decision
Entry Advisory
Holder Advisory
Quality Score
Composite Score
Ranking
```

Future PAQS-E must be able to reason from market facts without being anchored by PAQS-Q/legacy structure conclusions.

---

## 4. Existing authoritative factual sources

Reuse existing provider-neutral application/domain contracts rather than creating a second market-data stack.

Primary existing sources include:

```text
PaqsInputQueries.current_bundle(security_id)
MarketDataQueries.state(security_id)
```

Existing `PaqsInputBundle` already provides:

```text
security_id
market
symbol
market_timezone
provider
as_of_timestamp
completed_w1_bars
completed_d1_bars
completed_30m_bars
calendar metadata
adjustment metadata
data_quality
warnings
source_coverage
```

Existing market state provides current quote and market-state provider results.

Do not import or expose Futu SDK/native objects into the new core snapshot domain.

---

## 5. Snapshot schema identity

Introduce a provider-neutral immutable domain object conceptually named:

```text
PaqsMarketSnapshot
```

Exact internal class/file naming may follow project conventions, but the semantics are fixed.

Minimum top-level fields:

```text
snapshot_schema_version
snapshot_hash
security
as_of_timestamp
created_at
w1_bars
d1_bars
m30_bars
current_price_reference
market_state_reference
calendar_metadata
adjustment_metadata
data_quality
warnings
source_coverage
provider_metadata
```

The object must be immutable/frozen according to project conventions.

`snapshot_hash` must be self-consistent with the canonical hash payload defined by this contract.

---

## 6. Security identity block

The snapshot must expose enough immutable identity for downstream analysis and audit.

Minimum logical fields:

```text
security_id
market
symbol
display_symbol
display_name
currency
instrument_type
market_timezone
```

Only existing supported/eligible US/HK equities may produce a valid current PAQS snapshot.

Do not infer unsupported metadata.

Do not add brokerage tradability/account semantics.

---

## 7. Timeframe factual bar payloads

The initial snapshot uses exactly these structural-evidence timeframes:

```text
W1 = completed weekly factual bars
D1 = completed daily factual bars
M30 = completed REGULAR-session 30-minute factual bars
```

All price/volume values remain Decimal in the domain object.

The API serialization must preserve exact decimal text semantics; no binary-float financial conversion may be introduced.

Bars must be sorted in deterministic chronological order before inclusion/hashing.

Duplicate canonical bar identities are invalid and must not be silently retained.

### 7.1 W1 cap and eligibility

Maximum current snapshot W1 payload:

```text
156 bars
```

Use the latest 156 eligible W1 bars after canonical ordering.

An authoritative W1 evidence bar must satisfy both:

```text
is_completed == true
coverage == DerivedCoverage.COMPLETE
```

`PARTIAL` and `UNKNOWN` W1 bars must not enter `w1_bars`.

If such bars exist upstream, their exclusion must remain truthful through warnings/coverage/provenance where applicable; do not silently upgrade their quality.

### 7.2 D1 cap and eligibility

Maximum current snapshot D1 payload:

```text
500 bars
```

Use the latest 500 canonical completed D1 bars after canonical ordering.

Canonical `DailyBar` already requires completed data; do not invent an incomplete D1 representation in this task.

### 7.3 M30 cap and eligibility

Maximum current snapshot M30 payload:

```text
200 bars
```

Use the latest 200 eligible M30 bars after canonical ordering.

An authoritative M30 evidence bar must satisfy:

```text
is_completed == true
coverage == DerivedCoverage.COMPLETE
session_type == REGULAR
```

No partial current M30 bucket is included.

### 7.4 Context-cap interpretation

These caps are **snapshot input/context caps**, not universal PAQS strategy semantics.

They must not be documented as proving that older Price Action is irrelevant.

PAQS-Q may later use separate explicitly approved strategy horizons.

PAQS-E may later revise context packaging under its own Task Contract without rewriting historical TASK-006B2 evidence.

---

## 8. Latest quote reference

The current/latest quote is useful for entry-location/chase context, but it is not completed structural evidence.

Expose a nullable/structured `current_price_reference` with minimum logical semantics:

```text
status
provider
retrieved_at
reason
price
currency
latest_quote_at
price_kind
reference_only = true
```

When quote data is unavailable/error:

- retain truthful status/provider/retrieved_at/reason;
- price/timestamp payload may be absent;
- do not fabricate zero or reuse a stale D1/M30 close as the quote.

Hard invariant:

```text
current_price_reference.reference_only == true
```

The quote must not be serialized under a name implying `completed_close`, `bar_close`, `trigger_close`, or similar structural authority.

---

## 9. Market-state reference

Expose current market state only as factual context.

Minimum logical semantics:

```text
status
provider
retrieved_at
reason
canonical_state
provider_state
reference_only = true
```

Market state does not authorize strategy interpretation.

Provider failure is a truthful unavailable/error state, never fabricated `CLOSED` or `UNKNOWN` unless the underlying canonical provider result supports that state.

---

## 10. As-Of semantics

`snapshot.as_of_timestamp` means:

> the latest factual time boundary necessary to describe the information included in this snapshot request.

It must be an aware UTC instant.

It must be **not earlier than** every included factual/provider retrieval instant relevant to the snapshot, including at minimum where present:

```text
PaqsInputBundle.as_of_timestamp
quote ProviderResult.retrieved_at
market-state ProviderResult.retrieved_at
calendar retrieved_at
adjustment_as_of
```

If a successful quote contains `latest_quote_at`, the snapshot `as_of_timestamp` must not precede it.

`created_at` must satisfy:

```text
created_at >= as_of_timestamp
```

A recommended implementation is to retrieve/freeze all component views first, derive the final `as_of_timestamp`, then set:

```text
created_at = max(now(), as_of_timestamp)
```

Do not record `created_at` before component retrieval in a way that can produce inverted provenance.

---

## 11. Data quality and partial snapshots

TASK-006B2 is a factual snapshot builder, not a strategy gate.

A snapshot may truthfully exist with:

```text
data_quality = COMPLETE
or
data_quality = PARTIAL
```

An upstream fully invalid/unavailable factual state must be represented truthfully according to existing application/API conventions; do not fabricate an analyzable complete snapshot.

A PARTIAL snapshot must preserve:

```text
warnings
source_coverage
calendar status/reason
adjustment metadata
provider result statuses/reasons
```

This task must not decide whether a future PAQS-E/PAQS-Q strategy is allowed to form a Setup from PARTIAL data.

That policy belongs downstream.

Missing data is not numeric zero.

---

## 12. Calendar metadata

The snapshot should expose a bounded provider-neutral calendar/session provenance summary sufficient for downstream audit without duplicating arbitrary provider-native objects.

Minimum logical semantics:

```text
status
provider
retrieved_at
reason
market_timezone
```

The full list of historical trading-day objects does not need to be exposed in the public snapshot JSON unless required by implementation consistency.

If included internally for hash/audit, it must remain provider-neutral and canonical.

Do not create new inferred trading sessions.

---

## 13. Adjustment metadata

Preserve existing adjustment truth exactly.

Minimum fields:

```text
basis
adjustment_as_of
historical_replay_safe
```

For current Futu QFQ path, do not change:

```text
basis = PROVIDER_QFQ_CURRENT
historical_replay_safe = false
```

A current snapshot may be useful for current decision support while still truthfully stating that current-QFQ data is not strict point-in-time-safe historical replay.

Do not claim otherwise.

---

## 14. Source coverage

Preserve source-coverage diagnostics from TASK-006A, including conceptually:

```text
d1_source_count
w1_completed_count
w1_partial_count
minute_source_count
m30_completed_count
m30_partial_count
```

If TASK-006B2 excludes completed-but-UNKNOWN W1 from its authoritative W1 payload, add/derive sufficient snapshot-level diagnostic semantics so the API does not misleadingly imply all upstream completed W1 objects were authoritative COMPLETE evidence.

Exact naming may be improved, but the distinction must be testable.

---

## 15. Objective numerical features

Initial TASK-006B2 snapshot contains no strategy-derived quantitative features beyond the factual OHLCV/provider/session/quality metadata already described.

Specifically do **not** add in this task:

```text
EMA20
EMA50
ROC20
ROC60
ATR14 as a new shared precomputed feature
RSI
MACD
volatility score
trend score
momentum score
extension score
PAQS-Q score
```

Future TASK-007A may explicitly approve objective feature packaging for PAQS-E.

Existing ATR/Pivot calculations under legacy TASK-006B are not imported into this shared snapshot.

---

## 16. Canonical serialization

Implement one deterministic canonical serialization used for hashing and reproducibility tests.

Canonical rules:

```text
encoding = UTF-8
object key order = deterministic / canonical
Decimal = canonical decimal string, no float conversion
datetime = aware UTC canonical ISO-8601 representation
date = ISO-8601 date
enum = canonical string value
arrays = deterministic semantic order
bars = chronological order
```

Do not depend on Python object repr, unordered set/dict iteration, memory addresses, locale, or process-global formatting.

Equivalent semantic domain values must serialize identically across repeated runs.

---

## 17. Snapshot hash

Algorithm:

```text
SHA-256(canonical_hash_payload_utf8)
```

Expose lowercase hexadecimal SHA-256 text.

The hash payload must contain every factual field whose value could influence what a downstream strategy/model is told for this snapshot.

The hash payload must exclude self-referential/transient identity fields:

```text
snapshot_hash
created_at
```

`snapshot_schema_version` **must** be included in the hash payload.

`as_of_timestamp` and included provenance/retrieval timestamps **must** be included because they are part of the factual snapshot contract.

Therefore:

```text
identical canonical analysis payload + different created_at
    -> identical snapshot_hash

any changed model-visible fact/provenance/as_of/schema version
    -> changed snapshot_hash
```

Do not use random UUIDs as the snapshot factual identity.

A later Decision Ledger may have its own separate decision ID.

---

## 18. Hash self-validation

The immutable snapshot domain object should reject or prevent an inconsistent state where:

```text
snapshot_hash != SHA256(canonical payload)
```

Implementation may use a factory/builder that computes the hash rather than requiring callers to supply it.

Tests must prove tampering/changing a payload component changes the expected hash.

---

## 19. Public read-only endpoint

Add one current read-only endpoint:

```text
GET /api/v1/paqs/securities/{security_id}/market-snapshot
```

No query parameters.

Specifically forbidden in TASK-006B2:

```text
?as_of=
?history_days=
?w1_limit=
?d1_limit=
?m30_limit=
?provider=
?model=
?include_structure=
```

Historical As-Of replay belongs after TASK-006B1 and later evaluation work.

The endpoint must not mutate database state.

The endpoint must not call any LLM provider.

---

## 20. API response requirements

The public response must expose developer-readable factual fields sufficient for future 007A integration.

At minimum expose:

```text
snapshot_schema_version
snapshot_hash
security
as_of_timestamp
created_at
W1/D1/M30 factual bars
quote reference/status
market-state reference/status
data_quality
warnings
source coverage
adjustment metadata
provider/calendar provenance
```

All times must have explicit timezone/UTC representation in JSON.

All financial Decimal values must serialize in a way that preserves project financial precision and must not silently round through binary float.

No PAQS strategy conclusion fields may appear.

---

## 21. Snapshot schema version

Introduce a fixed explicit initial schema version, for example:

```text
paqs-market-snapshot-v1
```

Exact constant naming may follow repository conventions.

Schema-version changes that alter canonical model-visible semantics must produce a different hash due to the version being included in the hash payload.

Do not silently change v1 semantics in future tasks without version/governance consideration.

---

## 22. No persistence / migration

TASK-006B2 adds no production persistence for market snapshots.

No new database table.

No new Alembic migration.

Do not modify migration `0001_phase1_foundation.py`.

TASK-006B1 remains the future Local Market Data Store task.

TASK-007B remains the future immutable PAQS-E Decision Ledger task.

---

## 23. No PAQS-E/OpenAI implementation

TASK-006B2 must not add:

```text
openai package dependency
OpenAI client
OPENAI_API_KEY
LLM provider interface
prompt templates
Doctrine runtime packaging
structured PAQS-E output schema
PAQS-E Analyze endpoint
model selector
model API call
```

Those belong to TASK-007A/007B.

---

## 24. No PAQS-Q strategy implementation

Do not implement or remediate:

```text
PAQS-Q v0.4 Lite
Pivot stabilization
Zone decay
Range changes
Quant factors
Event engine
Setup engine
Advisory engine
scanner
```

Legacy TASK-006B code remains untouched unless a narrowly necessary compatibility refactor is unavoidable; such a refactor must not change its strategy behavior and must be justified in the final report.

Preferred implementation should not need to modify legacy structure semantics.

---

## 25. No Dashboard feature in this task

Do not add an Analyze button.

Do not add PAQS-E/PAQS-Q cards.

Do not change current Dashboard strategy behavior.

The developer-readable JSON endpoint is sufficient for TASK-006B2 acceptance.

Dashboard integration belongs to TASK-007C and later PAQS-Q presentation.

---

## 26. No brokerage / execution capability

Permanent project boundary remains unchanged.

Do not add or access:

```text
broker account
cash
positions
orders
trades
trade password
place_order
cancel_order
modify_order
unlock_trade
OMS/EMS
live execution
autonomous trading
```

Futu usage remains quote/read-only market data only.

---

## 27. Architecture boundaries

Core snapshot domain:

- provider-neutral;
- no Futu import;
- no FastAPI import;
- no environment-variable reads;
- no OpenAI import;
- no database-session access.

Application layer may orchestrate existing provider-neutral query services.

Backend/API layer may serialize the immutable domain snapshot.

Integrations remain responsible for provider-specific market-data translation.

---

## 28. Required unit tests — canonical snapshot domain

At minimum prove:

```text
snapshot is immutable
schema version is present
all instants are aware UTC
created_at >= as_of_timestamp
finite Decimal validation where relevant
canonical bar ordering
canonical duplicate handling/rejection
W1 authoritative eligibility requires COMPLETE + completed
M30 authoritative eligibility requires COMPLETE + completed + REGULAR
D1 remains completed canonical facts
context caps are exactly W1 156 / D1 500 / M30 200
```

---

## 29. Required unit tests — canonical serialization/hash

At minimum prove:

```text
same semantic payload -> identical canonical bytes/text
same semantic payload -> identical SHA-256
created_at change alone -> same hash
snapshot_hash is not part of hash payload
schema version is part of hash payload
as_of change -> different hash
Decimal change -> different hash
bar change -> different hash
quote fact/status change -> different hash
quality/warning/coverage change -> different hash
adjustment/provenance change -> different hash
input ordering differences normalize to identical semantic hash where order is non-semantic
financial values never pass through float
```

Add a deterministic known/golden hash fixture for at least one fully specified synthetic snapshot.

---

## 30. Required unit tests — quote and state references

At minimum prove:

```text
available quote -> reference_only true
unavailable quote -> no fabricated price
provider error -> truthful status/reason
quote cannot populate structural bar arrays
market-state reference_only true
market-state unavailable does not fabricate CLOSED
snapshot as_of >= quote retrieved_at
snapshot as_of >= successful latest_quote_at
snapshot created_at >= final as_of
```

---

## 31. Required integration/API tests

At minimum verify:

- valid supported US Security snapshot endpoint;
- valid supported HK Security snapshot endpoint;
- zero query parameters in OpenAPI for the snapshot route beyond path parameter;
- response W1 contains only explicit COMPLETE eligible bars;
- response M30 contains only explicit COMPLETE REGULAR bars;
- D1/W1/M30 caps are enforced;
- partial input quality remains partial and warnings remain visible;
- quote unavailable/provider error remains truthful;
- snapshot hash is stable for a frozen deterministic fixture/request dependency set;
- no structure fields are present;
- no strategy/advisory fields are present;
- no mutation/database write occurs merely from snapshot GET;
- no new migration exists.

Tests should use deterministic provider/query fixtures where possible and must not require live OpenD.

---

## 32. Architecture/no-scope tests

At minimum verify/search that:

```text
core snapshot module does not import futu
core snapshot module does not import openai
core snapshot module does not import FastAPI
no OPENAI_API_KEY handling exists in TASK-006B2 changes
no OpenAI dependency was added
no broker account/write API was added
no TASK-007A/B/C behavior was added
no PAQS-Q remediation/event/setup/advisory behavior was added
no migration file was added
protected Phase 1 migration remains unchanged
```

---

## 33. Documentation updates

Update user/engineering documentation only as necessary to explain the factual snapshot concept.

At minimum update the engineering PAQS documentation so future 007A implementers can understand:

```text
Snapshot-on-Demand
snapshot_schema_version
snapshot_hash
completed W1/D1/M30 evidence
quote reference-only semantics
quality/coverage/adjustment provenance
snapshot is factual, not a strategy judgment
```

Do not document PAQS-E as implemented.

Do not mark TASK-007A/B/C complete.

Roadmap/Requirements task status may be updated only to reflect TASK-006B2 implementation evidence after actual implementation/review, not merely by starting the task.

---

## 34. Validation commands

Run and report at minimum project-standard equivalents of:

```text
pytest
ruff check
ruff format --check
mypy
application startup
GET /health
GET /openapi.json
focused TASK-006B2 tests
fresh SQLite migration verification
```

If commands differ from these exact spellings, report the actual project-standard commands and outcomes.

---

## 35. Live OpenD smoke

A live quote-only OpenD smoke is optional environmental evidence, not a deterministic acceptance dependency.

If OpenD is available, attempt current snapshots for the existing familiar equities such as:

```text
US.AVGO
US.VRT
HK.09698
```

Report only factual snapshot evidence:

```text
snapshot_hash
as_of_timestamp
W1/D1/M30 counts
quote reference status/price/timestamp
quality/warnings
adjustment basis
```

Do not claim PAQS-E/PAQS-Q strategy conclusions.

If OpenD is unavailable, report the smoke as blocked truthfully without failing deterministic acceptance solely for that reason.

---

## 36. Protected files / historical evidence

Do not modify accepted immutable Phase 1 review evidence.

Do not modify:

```text
docs/phases/PHASE_1_PLAN.md
src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py
```

If local file exists:

```text
phase1_remediation_commit.txt
```

leave it:

```text
untracked
untouched
unstaged
uncommitted
```

Its presence alone does not block this task.

---

## 37. Expected implementation areas

Exact file choices are delegated to Codex within architecture boundaries, but likely bounded areas include:

```text
src/ai_infra_quant/core/domain/...
src/ai_infra_quant/application/...
src/ai_infra_quant/backend/...
tests/unit/...
tests/integration/...
docs/engineering/...
```

Do not use this list as permission for unrelated refactors.

---

## 38. Acceptance summary

TASK-006B2 is accepted only if all of the following hold:

```text
one provider-neutral immutable current Market Snapshot exists
Snapshot-on-Demand semantics are preserved
W1/D1/M30 factual evidence is bounded and truthful
W1 UNKNOWN/PARTIAL is excluded from authoritative W1 bars
latest quote is explicit reference-only context
final as_of provenance is correctly ordered
canonical serialization is deterministic
SHA-256 snapshot_hash is stable and self-consistent
created_at does not affect the hash
no PAQS strategy conclusion is embedded
no OpenAI/LLM implementation exists
no persistence/migration exists
no Dashboard Analyze workflow exists
no broker capability exists
full/focused validation passes
```

---

## 39. Codex final report requirements

Final report must include:

- authoritative base SHA actually verified;
- Task Contract commit SHA;
- starting task-branch SHA;
- final implementation HEAD SHA;
- exact changed-file list;
- snapshot schema/version summary;
- W1/D1/M30 caps and eligibility actually implemented;
- canonical serialization/hash behavior;
- quote/market-state reference-only behavior;
- as_of/created_at provenance behavior;
- full pytest result;
- focused TASK-006B2 test result;
- Ruff result;
- mypy result;
- startup/health/OpenAPI result;
- migration verification;
- optional live OpenD snapshot smoke separately identified as environmental evidence or blocked;
- confirmation no OpenAI/LLM behavior was added;
- confirmation no PAQS-Q/legacy strategy semantics were changed;
- confirmation no Dashboard Analyze behavior was added;
- confirmation no brokerage/write behavior was added;
- confirmation protected Phase 1 files remained unchanged;
- confirmation `phase1_remediation_commit.txt`, if present, remained untracked/untouched/unstaged/uncommitted;
- unresolved issues/blockers.

---

## 40. Stop condition

After implementation:

1. commit and push only `task/006b2-snapshot-on-demand-market-snapshot`;
2. do not merge into `roadmap/no-live-trading`;
3. stop for independent review;
4. do not start TASK-007A;
5. do not start TASK-006B1;
6. remediation, if required, must be separately focused and approved;
7. one task passing does not approve the next task.

**End — TASK-006B2 Approved Contract**
