# TASK-007B — On-Demand PAQS-E Analysis Service & Immutable Decision Ledger

Status: **APPROVED TASK CONTRACT — implementation authorized only on the dedicated TASK-007B branch after this Contract commit**

Repository: `ahhhhzzz/ai-infra-quant`

Authoritative base branch: `roadmap/no-live-trading`

Exact authoritative base SHA: `ca9712649b7ec26a67047e251200a50b353ad5b4`

Dedicated task branch: `task/007b-paqs-e-analysis-decision-ledger`

Parent workstream: `TASK-007 — PAQS-E Expert Reasoning Workstream` (umbrella only)

Immediate prerequisite accepted/integrated:

- TASK-007A final integrated SHA: `ca9712649b7ec26a67047e251200a50b353ad5b4`
- Parent TASK-007A Contract: `prompts/tasks/TASK-007A_PAQS_E_RUNTIME_STRUCTURED_OUTPUT_OPENAI_STRATEGY_PORT.md`
- TASK-007A Remediation 01: `prompts/tasks/TASK-007A_REMEDIATION_01_RUNTIME_CONTRACT_GUARDRAILS.md`
- TASK-007A Remediation 02: `prompts/tasks/TASK-007A_REMEDIATION_02_PLATFORM_STABLE_STRATEGY_HASH.md`

This task is bounded to one explicit current-analysis service/API, immutable PAQS-E analysis/decision evidence persistence, revision semantics, repository/UoW boundaries, and read APIs needed by the later TASK-007C Dashboard.

It does **not** implement the TASK-007C Dashboard UI, historical replay, local market-data store, PAQS-Q, paper portfolio, real-position state, broker/account/order behavior, background analysis, or automatic re-analysis.

---

## 1. Authoritative product requirements adopted by this task

TASK-007B implements the accepted Roadmap/Requirements direction already present at authoritative base `ca9712649b7ec26a67047e251200a50b353ad5b4`:

```text
explicit user-triggered Analyze
one request -> one immutable current Market Snapshot
one PAQS-E reasoning attempt per Analyze request
validated successful result -> immutable Decision
new Analyze -> new Decision revision; never overwrite old Decision
persist snapshot/strategy/prompt/provider/model/runtime/validator identity
truthful provider failure
no automatic strategy rerun on market-data refresh
```

TASK-007B must consume, not redefine, the accepted TASK-006B2 Market Snapshot and TASK-007A PAQS-E runtime contracts.

The permanent product remains:

- local-first;
- single-user;
- read-only decision support;
- human capital decision outside the application;
- no brokerage-account connection/observation;
- no broker writes or execution path.

---

## 2. Product objective

Implement the first usable server-side PAQS-E Analyze workflow so that an explicit caller can select one supported Security, one explicit OpenAI model identifier and one registered primary strategy, request one analysis, and receive either:

1. one persisted, validated, immutable PAQS-E Decision; or
2. one truthful persisted analysis-run failure where a complete TASK-007A reasoning request existed but provider/validation failed.

Conceptual success flow:

```text
Explicit Analyze request
        ↓
validate supported Security + selected strategy/model
        ↓
TASK-006B2 current snapshot acquisition
        ↓
freeze one immutable PaqsMarketSnapshot
        ↓
load selected registered StrategyPackage
load versioned PromptPackage
server-controlled PaqsERuntimeConfigV1
auxiliary_context = empty for TASK-007B public Analyze v1
        ↓
build one PaqsEReasoningRequestV1
        ↓
canonical serialize + hash exact request evidence
        ↓
TASK-007A PaqsEReasoningRuntime
        ↓
OpenAI provider-neutral port/adapter
        ↓
strict structured result
        ↓
deterministic TASK-007A validation
        ↓
transactionally persist runtime artifacts + Analysis Run + Decision revision
        ↓
commit succeeds
        ↓
return success
```

Provider/validation failure flow:

```text
complete immutable reasoning request exists
        ↓
provider/configuration failure OR deterministic validation failure
        ↓
persist runtime artifacts + immutable failed Analysis Run
        ↓
NO Decision row
        ↓
return truthful failure including safe analysis_run_id
```

A public API success must never be returned before the successful Decision transaction has committed.

---

## 3. Hard scope exclusions

TASK-007B must not add or reactivate:

- TASK-007C HTML/JS/CSS Analyze UI;
- model/strategy selector widgets in the Dashboard;
- automatic/background/continuous PAQS-E analysis;
- periodic strategy polling;
- Celery, Redis, worker queues or unattended jobs;
- TASK-006B1 market-data persistence/replay;
- arbitrary historical As-Of replay;
- PAQS-Q implementation or dual-branch comparison;
- paper portfolio, PaperFill, portfolio P&L or position sizing;
- user's real or simulated current position as implicit analysis state;
- brokerage account connection/observation;
- cash, positions, orders or trades from a real broker;
- `place_order`, `cancel_order`, `modify_order`, `unlock_trade`;
- OMS/EMS or any broker-write capability;
- web/news/social/browser/file-search retrieval;
- OpenAI tools or hidden provider conversation state;
- multi-model voting/ensemble;
- multi-user/authentication/tenant implementation;
- PostgreSQL deployment itself.

TASK-007B may preserve architectural replaceability for future PostgreSQL, but current runtime remains the accepted local SQLite application database.

---

## 4. Public Analyze v1 input contract

Implement one explicit current-analysis endpoint conceptually equivalent to:

```text
POST /api/v1/paqs-e/analyses
```

The request body must expose only the caller-controlled fields needed for the current MVP:

```text
security_id
model_id
strategy_id
```

Requirements:

- `security_id` is the canonical existing Security UUID;
- `model_id` is an explicit non-empty caller-selected model identifier and must be passed unchanged to TASK-007A;
- no silent model fallback;
- `strategy_id` selects only a registered TASK-007A strategy; callers never provide a filesystem path;
- model selection and strategy selection remain independent;
- model provider remains the accepted OpenAI adapter for current v1;
- runtime configuration is server-controlled `PaqsERuntimeConfigV1`, not arbitrary client input;
- runtime prompt/version is server-controlled;
- API key is never accepted in this request;
- arbitrary strategy Markdown is never accepted in this request;
- arbitrary runtime prompt text is never accepted in this request;
- arbitrary `short_execution_allowed`, session policy, RR policy, freshness policy or timeframe mapping is never accepted from the frontend;
- TASK-007B public Analyze v1 supplies `auxiliary_context=()`.

The last point does **not** permanently prohibit auxiliary context. TASK-007A remains extensible. A future separately approved task may expose explicit audited context inputs. TASK-007B v1 deliberately keeps the first Dashboard-facing Analyze surface simple and reproducible.

Every explicit POST is a new reasoning attempt. Do not deduplicate or reuse a prior Decision merely because `snapshot_hash + model_id + strategy_id` happen to match.

This is required for later repeated-run stability research.

---

## 5. Snapshot acquisition and precondition semantics

TASK-007B must obtain the current snapshot through the accepted application/core TASK-006B2 boundary, not by calling its own HTTP endpoint and not by duplicating snapshot-building logic.

The Analyze service must:

1. resolve/validate the canonical Security under existing supported-security semantics;
2. request a fresh current TASK-006B2 snapshot for this Analyze call;
3. use exactly that returned immutable snapshot for the whole reasoning request;
4. never replace it with a newer quote/bar during the same run;
5. never mutate the snapshot;
6. never use Dashboard refresh state as strategy state.

If a valid immutable snapshot/reasoning request cannot be constructed at all (for example Security not found/not supported or snapshot acquisition fails before a request exists), return a truthful existing/project-consistent precondition error and create no fabricated Decision.

The Decision Ledger is evidence for actual formed reasoning requests. TASK-007B does not need a separate click-attempt telemetry table for requests that never reached a valid immutable reasoning request.

---

## 6. Request evidence capsule

For every complete TASK-007A reasoning request that is sent to the provider runtime, create an exact deterministic audit representation before persistence:

```text
request_payload_json = canonical_json(PaqsEReasoningRequestV1)
request_payload_sha256 = SHA-256(UTF-8 bytes of request_payload_json)
```

`request_payload_json` must preserve the complete immutable reasoning request, including at minimum:

- snapshot hash and security identity;
- full bounded W1/D1/M30 snapshot bars contained by TASK-006B2;
- quote and market-state references;
- calendar/session evidence;
- adjustment metadata;
- quality/coverage/timeframe provenance;
- provider-delay/provenance data;
- runtime configuration;
- request/output/prompt/runtime identities;
- selected model identity;
- selected strategy identity/hash;
- explicit auxiliary context list (empty in TASK-007B public Analyze v1).

This is an **Analysis Evidence Capsule**, not a replacement Market Data Store.

It exists to answer:

> What exact factual/request payload did this reasoning attempt see?

It must remain independent of later TASK-006B1 market-data caching/replay. Re-downloading, deleting or changing future market-data caches must not mutate old Analyze evidence.

Persist the canonical JSON text exactly as text. Do not use a database JSON type as the byte-authority for the audit hash.

---

## 7. Runtime strategy/prompt artifacts

Persist the exact StrategyPackage and PromptPackage content actually used by an Analyze request as immutable, deduplicated runtime artifacts.

Implement a table/domain concept equivalent to:

```text
paqs_e_runtime_artifacts
```

Required conceptual fields:

```text
id                         UUID
artifact_kind              STRATEGY | PROMPT
artifact_key               strategy_id OR prompt_version
display_name               nullable where not applicable
source_path
content_sha256              lowercase SHA-256
content_text                exact UTF-8 text loaded at runtime
created_at                  aware UTC
```

Uniqueness must distinguish logical identity and bytes, conceptually:

```text
UNIQUE(artifact_kind, artifact_key, content_sha256)
```

Rules:

- Strategy Markdown continues to be loaded from TASK-007A registry/filesystem; database content is audit evidence, not executable strategy authority;
- Prompt continues to be loaded from the versioned TASK-007A prompt resource;
- the Ledger must not become a strategy editor or prompt registry;
- persist the exact content loaded and supplied to the runtime;
- verify `SHA-256(content_text.encode("utf-8")) == content_sha256` before insert/use;
- if an identical logical artifact/hash already exists, reuse it rather than inserting duplicate content;
- if an existing row claims the same logical artifact/hash but stored content/hash verification fails, fail closed;
- no API key or secret may appear in artifact content/metadata;
- artifact rows are immutable after insert.

The currently accepted default strategy remains:

```text
strategy_id = paqs-e-master
source_path = docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md
Git blob = 5e27d45c38fbd9ad4ab49e05df4a5158b3469b73
canonical LF-byte SHA-256 = 73bed86ffef402d3d1e5eff855aaa2cc4bebf1ca1aafa33500c8839f63c16f82
```

Do not hard-code strategy body into persistence/application code.

---

## 8. Analysis Run ledger

Implement an immutable terminal analysis-attempt record conceptually equivalent to:

```text
paqs_e_analysis_runs
```

An Analysis Run represents one complete immutable reasoning request and its terminal application outcome.

Current v1 terminal statuses:

```text
SUCCEEDED
PROVIDER_FAILED
VALIDATION_FAILED
```

Do not add background/in-progress job semantics merely for this synchronous task.

Recommended/required conceptual fields:

```text
id                              UUID
security_id                     FK -> securities.id
symbol
market
instrument_type
snapshot_hash
snapshot_as_of_timestamp
analysis_mode

request_schema_version
output_schema_version
runtime_config_version
validator_version               nullable only when provider failed before validator result

model_provider
model_id
strategy_id
strategy_content_sha256
strategy_artifact_id            FK -> paqs_e_runtime_artifacts.id
prompt_version
prompt_content_sha256
prompt_artifact_id              FK -> paqs_e_runtime_artifacts.id

request_payload_json
request_payload_sha256

status                          SUCCEEDED | PROVIDER_FAILED | VALIDATION_FAILED
provider_response_id            nullable
failure_kind                    nullable; exact TASK-007A ReasoningFailureKind when applicable
failure_reason                  nullable; safe/redacted reason only
validation_issues_json          canonical JSON array; empty when not applicable

started_at                      aware UTC
completed_at                    aware UTC
created_at                      aware UTC persistence timestamp
```

No binary float fields are allowed for financial data.

The Analysis Run must be append-only/immutable after insert.

### 8.1 Provider/configuration failure

If TASK-007A returns `ReasoningProviderFailure`, persist:

```text
status = PROVIDER_FAILED
failure_kind = exact typed failure kind
failure_reason = safe existing TASK-007A reason
validation_issues_json = []
```

Then return a truthful non-success HTTP response after the failed run record commits.

At minimum preserve exact distinctions:

```text
CONFIGURATION_ERROR
PROVIDER_UNAVAILABLE
PROVIDER_REFUSAL
INVALID_STRUCTURED_OUTPUT
```

Never fabricate a strategy answer or Decision around provider failure.

### 8.2 Validation failure

If TASK-007A returns `PaqsEValidationFailure`, persist:

```text
status = VALIDATION_FAILED
validator_version = failure.validator_version
validation_issues_json = canonical JSON of exact issue list
```

No Decision may be created.

TASK-007B does not need to broaden the accepted TASK-007A provider/runtime return types merely to persist a raw pre-validation model object. Persist the evidence safely exposed by the accepted TASK-007A boundary; do not bypass the runtime or duplicate its validation orchestration.

### 8.3 Successful run

A successful run must correspond to exactly one `ValidatedPaqsEResult` and exactly one Decision row created in the same database transaction.

The run may store safe `provider_response_id` from TASK-007A.

---

## 9. Immutable PAQS-E Decision

Implement a validated Decision record conceptually equivalent to:

```text
paqs_e_decisions
```

A Decision exists **only** after TASK-007A deterministic validation succeeds.

Required conceptual fields:

```text
id                              UUID
analysis_run_id                 UNIQUE FK -> paqs_e_analysis_runs.id
security_id                     FK -> securities.id
symbol
market
instrument_type
snapshot_hash
snapshot_as_of_timestamp
analysis_mode

request_schema_version
output_schema_version
runtime_config_version
validator_version

model_provider
model_id
strategy_id
strategy_content_sha256
strategy_artifact_id            FK -> paqs_e_runtime_artifacts.id
prompt_version
prompt_content_sha256
prompt_artifact_id              FK -> paqs_e_runtime_artifacts.id

revision_no                     positive integer
supersedes_decision_id          nullable self-FK

result_payload_json             canonical PaqsEReasoningResultV1 JSON text
result_payload_sha256           SHA-256 of exact UTF-8 canonical JSON bytes

one_line_thesis                 query-friendly copy
entry_advisory                  exact canonical enum value
holder_advisory_basis           exact canonical enum value
holder_advisory                 exact canonical enum value
market_bias                     exact canonical enum value
setup_family                    exact canonical enum value
setup_direction                 exact canonical enum value
setup_stage                     exact canonical enum value
rr_status                       exact canonical enum value
rr_t1                           exact Decimal nullable
uncertainty_level               exact canonical enum value

created_at                      aware UTC
```

The full structured result remains authoritative inside `result_payload_json`; selected duplicated columns exist only for efficient listing/filtering/presentation and must exactly match the structured result.

Use canonical JSON and exact Decimal semantics. Do not convert `rr_t1` through binary float.

A successful Decision is immutable after insert. No update or delete path is authorized.

---

## 10. Decision revision semantics

A new explicit Analyze always creates a new Analysis Run.

Every successful Analyze creates a new Decision revision even when:

- the same Security is analyzed;
- the same Snapshot hash happens to recur;
- the same model is selected;
- the same strategy hash is selected;
- the resulting advisory is identical.

Revision series identity for TASK-007B v1 is:

```text
security_id + strategy_id
```

Do **not** include `model_id` in the series key.

Rationale:

```text
strategy_id = method/family identity
model_id = reasoning executor metadata
```

Changing model remains visible in each Decision but does not create a disconnected history for the same strategy.

Changing to a different `strategy_id` creates a separate revision series.

For each series:

```text
first Decision:
revision_no = 1
supersedes_decision_id = null

next Decision:
revision_no = previous revision_no + 1
supersedes_decision_id = immediately previous Decision id
```

Requirements:

- `revision_no > 0`;
- unique `(security_id, strategy_id, revision_no)`;
- `analysis_run_id` unique;
- `supersedes_decision_id` may not self-reference;
- when non-null it must reference the immediately previous revision in the same Security/strategy series;
- no gaps may be deliberately created by normal application behavior;
- no old Decision may be overwritten to represent a new opinion.

Concurrent duplicate submissions are not to be automatically deduplicated. Database uniqueness + transaction logic must prevent two rows from claiming the same revision number. The application is single-user, but correctness must not rely solely on the UI disabling double-clicks.

---

## 11. Transaction boundary

Do not hold a SQLite database transaction open across the external OpenAI network call.

Recommended bounded sequence:

```text
1. build immutable snapshot/request/artifact packages in memory
2. canonicalize/hash request evidence
3. call TASK-007A runtime/provider with no database write transaction held
4. obtain terminal outcome
5. open one persistence transaction
6. resolve/insert immutable strategy + prompt artifact rows
7a. provider/validation failure:
      insert one immutable failed Analysis Run
      commit
      return truthful failure
7b. success:
      insert one SUCCEEDED Analysis Run
      compute next revision within transaction
      insert one immutable Decision referencing that run
      commit atomically
      only then return success
```

If the final success transaction fails:

- rollback the transaction;
- return an internal persistence error;
- do not return a successful Decision;
- do not fabricate a Decision ID;
- do not leave a committed successful Analysis Run without its Decision.

A provider/validation failure run must itself be committed before the API returns the corresponding failure with an `analysis_run_id`.

---

## 12. Database migration and physical database choice

Use the existing application database selected by current `DATABASE_URL`.

Current default remains:

```text
sqlite:///./data/ai_infra_quant.db
```

TASK-007B must add a new Alembic migration conceptually named:

```text
0002_task007b_paqs_e_decision_ledger.py
```

Requirements:

- `down_revision = "0001_phase1_foundation"`;
- never edit `0001_phase1_foundation.py`;
- add only TASK-007B tables/indexes/constraints/triggers;
- preserve all Phase 1 schema/history;
- fresh SQLite migration must reach the new head cleanly;
- upgrade from an existing database at 0001 must reach 0002 cleanly;
- downgrade behavior must remove only TASK-007B-owned schema;
- use repository-consistent UUID/string, aware UTC and Decimal type patterns;
- avoid application business logic that depends on SQLite-specific SQL;
- SQLite-specific immutable trigger DDL may be isolated inside the migration, following the accepted Phase 1 pattern;
- do not create a separate market-data database in this task;
- do not implement `market_data.sqlite` / DuckDB / Parquet here.

The domain/application contract must treat SQLite as the current adapter, not as the business interface.

---

## 13. Database immutability

At minimum the following TASK-007B tables are append-only after insert:

```text
paqs_e_runtime_artifacts
paqs_e_analysis_runs
paqs_e_decisions
```

For current SQLite runtime, implement database-level UPDATE/DELETE rejection triggers consistent with the existing Phase 1 immutable-table approach.

Application repositories must expose no ordinary mutation/delete operation for these records.

A new viewpoint is represented by a new Decision revision, never an UPDATE.

Do not add a public DELETE endpoint for Analysis Runs, Decisions or runtime artifacts.

---

## 14. Repository / port architecture and future PostgreSQL replaceability

Persistence must remain behind application/core-facing abstractions.

Conceptually preserve:

```text
Analyze Service
      ↓
Decision Ledger / Unit-of-Work port
      ↓
SQLAlchemy repository/UoW adapter
      ↓
SQLite today
PostgreSQL adapter/deployment later if separately approved
```

Rules:

- core/domain must not import SQLAlchemy;
- application Analyze service must not call `sqlite3`, raw SQLite connection APIs or SQLite file paths;
- database models/repositories remain under `database/`;
- use existing SQLAlchemy session/UoW conventions or a bounded PAQS-E-specific UoW/port if needed for correct atomicity;
- do not introduce a generic enterprise persistence framework;
- no empty `future/postgres` placeholder implementation is required;
- do not encode `user_id`/tenant behavior that does not yet exist;
- schema/table design should avoid unnecessary SQLite-only semantics so a future PostgreSQL adapter/migration remains tractable.

TASK-007B does not remove the current `Settings.database_url` SQLite-only runtime guardrail. A future web-deployment task may separately change runtime database support.

---

## 15. Canonical JSON and hash integrity

Use the accepted canonical serialization discipline already present in the repository.

For persisted request/result audit payloads:

```text
payload_text = canonical_json(domain_object)
payload_sha256 = SHA-256(payload_text.encode("utf-8"))
```

Rules:

- persisted JSON text must be canonical, deterministic and UTF-8;
- no pretty-print/whitespace-dependent audit identity;
- Decimal remains exact canonical decimal text;
- aware UTC timestamps remain canonical;
- database-native JSON reserialization must not be the audit authority;
- on repository/domain readback, verify stored payload SHA-256 before presenting it as valid audit evidence;
- for successful Decisions, verify query-friendly denormalized columns agree with parsed structured result;
- hash mismatch/corruption must fail truthfully rather than silently recomputing and accepting altered content.

Do not make the API key, environment values or non-reasoning secrets part of request/result payload hashes.

---

## 16. Decision history is not model memory

Persisted Decisions must **not** become hidden prompt state.

Every ordinary TASK-007B Analyze remains fresh/stateless:

```text
new explicit Analyze
        ↓
new current snapshot
        ↓
new TASK-007A request
        ↓
no previous Decision automatically supplied
```

The Analyze service must not:

- fetch the latest Decision and silently inject it into the prompt;
- infer holder basis from previous Ledger rows;
- use database history as hidden conversation memory;
- use prior model output unless a future caller explicitly supplies it through a separately approved audited auxiliary-context contract.

The Decision Ledger is history/evidence, not implicit LLM memory.

---

## 17. Read APIs required for TASK-007C

TASK-007B must expose bounded read-only APIs sufficient for later Dashboard work, conceptually:

```text
GET /api/v1/paqs-e/analyses/{analysis_run_id}
GET /api/v1/paqs-e/decisions/{decision_id}
GET /api/v1/paqs-e/securities/{security_id}/decisions
```

### 17.1 Analysis Run read

Must expose safe audit/status information, including:

- analysis_run_id;
- status;
- Security/snapshot identity;
- model/strategy/prompt/runtime/validator identities where available;
- request payload/hash or an equivalently complete safe audit representation;
- provider response ID if safely available;
- typed failure kind/reason where applicable;
- validation issues where applicable;
- timestamps.

Never expose API credentials, environment dumps, request headers or raw exception traces.

### 17.2 Decision read

Must expose:

- Decision/revision identity;
- Security/snapshot/as-of identity;
- model/strategy/prompt/runtime/validator metadata;
- full structured PAQS-E result;
- result payload hash;
- revision/supersedes metadata;
- created_at.

### 17.3 Security Decision history list

Return newest first and provide at minimum:

- bounded `limit` with default 20 and maximum 100;
- optional `strategy_id` filter;
- enough summary fields for TASK-007C history presentation without parsing the complete evidence capsule for every row.

No mutation endpoint is authorized.

---

## 18. Analyze HTTP success/failure semantics

### 18.1 Success

Return only after successful transaction commit.

Response must include at minimum:

```text
analysis_run_id
decision_id
revision_no
snapshot_hash
snapshot_as_of_timestamp
model_id
strategy_id
strategy_content_sha256
status = SUCCEEDED
result = full structured PAQS-E result
```

A `201 Created` or repository-consistent successful create status is preferred.

### 18.2 Provider/configuration failure

After failed Analysis Run persistence commits, return a non-2xx project-consistent problem response containing safe machine-readable context including:

```text
analysis_run_id
status = PROVIDER_FAILED
failure_kind
```

Suggested HTTP mapping may follow project conventions, but must preserve semantic distinction. In particular:

- missing OpenAI credential/configuration and provider unavailable must not look like a successful `NO_TRADE`;
- provider refusal must not be converted into `UNCERTAIN`;
- invalid structured output must not become a fabricated Decision.

### 18.3 Validation failure

After failed Analysis Run persistence commits, return a non-2xx truthful response containing safe machine-readable:

```text
analysis_run_id
status = VALIDATION_FAILED
validator_version
validation issues
```

No Decision ID is returned because no Decision exists.

### 18.4 Snapshot/security precondition failure

Reuse truthful existing semantics for Security not found/not supported and snapshot acquisition errors.

Do not create a fake Analysis Run if no complete immutable reasoning request existed.

---

## 19. Secret and sensitive-data handling

`OPENAI_API_KEY` remains server-side only under the accepted TASK-007A contract.

TASK-007B must never persist or expose it in:

- runtime artifacts;
- request payload JSON;
- Analysis Runs;
- Decisions;
- result JSON;
- API responses;
- logs;
- error text;
- validation issues;
- database rows;
- migration defaults;
- test fixtures containing a real secret.

Do not persist raw provider exception text when it may include credentials or transport details. Persist only safe typed failure data already provided by the accepted TASK-007A boundary.

No Dashboard API-key input/storage UI is authorized.

---

## 20. Query-friendly fields are derived copies, not second strategy authority

The `paqs_e_decisions` summary columns such as:

```text
one_line_thesis
entry_advisory
holder_advisory
market_bias
setup_family
setup_stage
rr_status
rr_t1
uncertainty_level
```

must be copied directly from the validated structured result at persistence time.

They must never be recomputed using a second deterministic trading strategy.

They exist only for efficient history/list queries and Dashboard rendering.

If a summary column disagrees with the canonical result payload, treat the persisted row as invalid/corrupt evidence rather than choosing one silently.

---

## 21. Expected bounded implementation areas

Exact names may follow project conventions, but expected areas include:

- `core/domain/` PAQS-E Decision Ledger entities/enums/invariants;
- `core/ports/` persistence/UoW repository interfaces;
- `application/` explicit PAQS-E Analyze orchestration service and read queries;
- `database/models/` TASK-007B SQLAlchemy models;
- `database/repositories/` SQLAlchemy repository/UoW implementation;
- `database/migrations/versions/0002_task007b_paqs_e_decision_ledger.py`;
- `backend/schemas/` Analyze/Analysis Run/Decision API schemas;
- `backend/api/v1/` PAQS-E Analyze/read routes;
- composition/container wiring;
- focused unit/integration/architecture/migration tests;
- minimal authoritative architecture/API/requirements/engineering documentation updates needed to describe TASK-007B pending independent review.

No frontend files should be needed.

---

## 22. Required tests — orchestration

Add deterministic tests proving at least:

- one POST Analyze builds exactly one fresh TASK-006B2 snapshot and uses that exact snapshot for the request;
- the service does not call the public snapshot HTTP endpoint internally;
- explicit model ID reaches TASK-007A unchanged;
- explicit registered strategy ID selects the matching StrategyPackage;
- strategy and model selections are independent;
- public Analyze v1 supplies no hidden prior Decision and no hidden auxiliary context;
- Dashboard/market-data refresh does not trigger PAQS-E Analyze;
- repeated explicit Analyze calls are not deduplicated even if snapshot/model/strategy are identical.

Use injected/fake provider boundaries; normal tests require no live paid OpenAI call.

---

## 23. Required tests — persistence/evidence

Prove at least:

### Runtime artifacts

- strategy/prompt exact content and hashes persist;
- same logical artifact/hash is deduplicated;
- different content hash creates a distinct artifact version;
- stored content hash is verified;
- artifacts cannot be updated/deleted under current SQLite runtime.

### Request evidence

- canonical request JSON contains the exact bound Snapshot payload;
- request SHA-256 equals stored canonical UTF-8 bytes;
- readback verifies hash;
- corrupt/tampered stored request payload fails truthfully;
- no API key appears in stored request evidence.

### Failed Analysis Runs

- provider failure persists one `PROVIDER_FAILED` run and zero Decisions;
- configuration failure remains typed and persists safely;
- provider refusal persists safely and creates zero Decisions;
- invalid structured output persists safely and creates zero Decisions;
- deterministic validation failure persists one `VALIDATION_FAILED` run with issues and zero Decisions;
- failed run records are immutable.

### Successful Decision

- success persists runtime artifacts + SUCCEEDED run + Decision in one transaction;
- API success is not returned before commit;
- Decision `analysis_run_id` is unique;
- canonical result JSON/hash round-trip exactly;
- stored summary fields exactly equal validated result fields;
- Decision rows cannot be updated/deleted.

### Transaction rollback

- forced Decision insert/commit failure returns non-success and leaves no committed successful run/Decision pair;
- no orphan SUCCEEDED Analysis Run exists without its Decision after failed success transaction.

---

## 24. Required tests — revisions

Prove at least:

- first successful `(security_id, strategy_id)` Decision is revision 1 with no supersedes ID;
- second is revision 2 and supersedes revision 1;
- model change does not start a new strategy revision series;
- strategy content/hash change under the same `strategy_id` continues the same series while preserving new hash metadata;
- a different `strategy_id` starts a separate revision series;
- unique `(security_id, strategy_id, revision_no)` is enforced;
- same snapshot analyzed twice may produce two successive revisions;
- historical Decisions remain byte/row immutable after later revisions.

---

## 25. Required tests — API

At minimum verify:

### POST Analyze

- valid request success path;
- Security not found;
- unsupported Security;
- unregistered strategy;
- empty/invalid model identifier;
- missing API credential -> truthful provider/config failure with failed run and no Decision;
- provider unavailable;
- provider refusal;
- invalid structured output;
- deterministic validation failure;
- success returns persisted Decision identity/result.

### GET reads

- get Analysis Run by ID;
- get Decision by ID;
- list newest Security Decisions;
- optional strategy filter;
- bounded list limit 1..100;
- 404 for unknown IDs;
- no secret fields in OpenAPI/response schemas.

OpenAPI must contain the new TASK-007B routes but no Dashboard or broker-write endpoints.

---

## 26. Required tests — migration/database portability boundary

Run migration tests proving:

- fresh empty SQLite database upgrades 0001 -> 0002 successfully;
- existing 0001 database upgrades to 0002 without altering accepted Phase 1 objects/data;
- expected TASK-007B tables/indexes/triggers exist;
- immutable triggers reject UPDATE/DELETE for the three ledger tables;
- downgrade removes only TASK-007B objects and returns to 0001 shape;
- optional PostgreSQL migration smoke may run if the repository's existing configured environment is available, but absence of `PHASE1_POSTGRESQL_TEST_URL` remains an acceptable environmental skip;
- application/core code does not import `sqlite3` or depend on a physical SQLite file path for Decision Ledger behavior.

Do not modify accepted Phase 1 migration evidence to make tests pass.

---

## 27. Architecture boundary tests

Add focused architecture tests proving at minimum:

- core Decision Ledger domain imports neither FastAPI nor SQLAlchemy;
- application Analyze service imports neither OpenAI SDK nor SQLAlchemy/sqlite3;
- provider-specific OpenAI behavior remains under `integrations/openai_reasoning/`;
- database adapter does not become strategy authority;
- TASK-007B adds no frontend Analyze button/UI;
- no market-data persistence table appears;
- no PAQS-Q code appears;
- no broker/account/order/write capability appears;
- no background scheduler/worker dependency appears.

---

## 28. Documentation updates

On the task branch, make only the minimal documentation updates required to describe the implemented TASK-007B contracts and pending-review status.

Expected documents may include:

- `docs/API_CONTRACTS.md`;
- `docs/ARCHITECTURE.md`;
- `docs/REQUIREMENTS_MATRIX.md`;
- `docs/engineering/PAQS_ENGINEERING_GUIDE.md`;
- `docs/ROADMAP.md` only if needed to state TASK-007A integrated and TASK-007B pending independent review without falsely claiming acceptance before review.

Do not mark TASK-007B COMPLETE/INTEGRATED until independent review and authoritative fast-forward actually occur.

Do not rewrite accepted historical phase evidence.

---

## 29. Validation gate

Run at minimum repository-standard equivalents of:

```text
pytest focused TASK-007B tests
pytest full suite
ruff check
ruff format --check
mypy
```

Also verify where feasible:

- fresh SQLite migration to new Alembic head;
- upgrade from an existing 0001 fixture/database shape;
- downgrade 0002 -> 0001;
- application startup;
- `/health`;
- `/openapi.json`;
- new Analyze/read routes appear;
- existing market-data/Dashboard routes still work;
- no live OpenAI paid/network call is required.

A real OpenAI smoke is optional only and must never expose the local secret.

---

## 30. Protected files/history

Do not modify:

- `docs/phases/PHASE_1_PLAN.md`;
- `src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py`;
- accepted immutable Phase 1 review evidence;
- accepted PAQS-E research strategy source merely to accommodate persistence;
- TASK-007A contracts/remediation contracts except for no changes at all unless a separately approved documentation correction is required (none is expected).

Preserve TASK-007A `.gitattributes` LF rules for hashed strategy/prompt resources.

If `phase1_remediation_commit.txt` exists locally, leave it untracked, untouched, unstaged, and uncommitted.

---

## 31. Permanent broker/no-live-trading boundary

TASK-007B must preserve the permanent product boundary:

```text
PAQS-E Decision
      ↓
read-only user display later in TASK-007C
      ↓
human decides manually
      ↓
user acts only in official broker client outside this application
```

No Ledger field or API may imply that an advisory was executed.

Do not add:

```text
order_id
broker_order_id
broker_account_id
position_id
fill_id
executed_quantity
execution_status
```

to the PAQS-E Decision Ledger merely because historical Phase 1 accounting/broker-shaped artifacts exist.

TASK-007B stores analysis facts, not brokerage execution facts.

---

## 32. Git and stop condition

Implementation must occur only on:

```text
task/007b-paqs-e-analysis-decision-ledger
```

Task branch was created from exact authoritative base:

```text
ca9712649b7ec26a67047e251200a50b353ad5b4
```

Before editing, Codex must verify:

- current branch is exactly the TASK-007B branch;
- current HEAD is exactly this Contract commit;
- Contract commit's parent is the authoritative base SHA above;
- `roadmap/no-live-trading` still points to the authoritative base when implementation begins;
- merge base with authoritative is exactly that base.

Use targeted staging.

Commit and push only the TASK-007B branch.

Do not merge.

Do not start TASK-007C.

Stop after implementation for independent review.

---

## 33. Required Codex final implementation report

The final report must include at minimum:

### Git evidence

- authoritative base SHA;
- TASK-007B Contract commit SHA;
- final implementation HEAD;
- direct parent/lineage evidence;
- merge-base/ahead/behind evidence;
- push verification;
- confirmation no merge occurred.

### Exact changed files

List every changed file.

### Implemented contract summary

Report:

- Analyze API path/input;
- Analysis Run statuses;
- Decision revision-series key and semantics;
- exact new database tables;
- exact migration revision/down_revision;
- immutable trigger behavior;
- request/result canonical hash behavior;
- runtime artifact persistence/dedup behavior;
- failure persistence behavior;
- repository/UoW boundary;
- read API paths;
- API-key secrecy confirmation.

### Validation evidence

Report exact results for:

- focused tests;
- full pytest;
- Ruff check;
- Ruff format check;
- mypy;
- migration upgrade/downgrade/fresh DB tests;
- startup/health/OpenAPI regression;
- any environmental skip.

### Scope confirmation

Explicitly confirm no:

- TASK-007C UI;
- market-data persistence/replay;
- PAQS-Q;
- paper portfolio/PnL/position sizing;
- hidden Decision memory;
- background analysis;
- broker/account/order/write capability;
- protected Phase 1 file mutation.

### Unresolved issues

List any unresolved issue truthfully. Do not claim PASS; stop for independent review.

**End — TASK-007B**