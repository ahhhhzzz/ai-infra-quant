# TASK-007A — PAQS-E Runtime, Structured I/O, OpenAI Provider Port & Primary Strategy Markdown Runtime

Status: **APPROVED TASK CONTRACT — implementation authorized only on the dedicated TASK-007A branch after this Contract commit**

Repository: `ahhhhzzz/ai-infra-quant`

Authoritative base branch: `roadmap/no-live-trading`

Exact authoritative base SHA: `6218c69bfc8202d6649e7ab01a2bd20fd585cdd5`

Dedicated task branch: `task/007a-paqs-e-runtime-openai-strategy-port`

Parent workstream: `TASK-007 — PAQS-E Expert Reasoning Workstream` (umbrella only)

This task is bounded to runtime contracts, primary-strategy Markdown loading, a provider-neutral reasoning port, the first OpenAI adapter, strict structured output, deterministic validation, and server-side API credential/configuration handling.

It does **not** implement the user-triggered Analyze API/service, Decision Ledger persistence, Dashboard Analyze UI, historical replay infrastructure, PAQS-Q, or any broker/account/order behavior.

---

## 1. Authoritative semantic sources adopted by this task

TASK-007A explicitly adopts the following authoritative repository state at exact base SHA `6218c69bfc8202d6649e7ab01a2bd20fd585cdd5`:

Primary PAQS-E runtime semantic strategy authority candidate:

`docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md`

Git blob SHA at the authoritative base:

`5e27d45c38fbd9ad4ab49e05df4a5158b3469b73`

Focused strategy re-review:

`docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_FOCUSED_RE_REVIEW.md`

Git blob SHA at the authoritative base:

`c4f074c863124550b231f55e0d96d221163382e8`

Conceptual/doctrine foundation:

`docs/research/PAQS_E_NAKED_PRICE_ACTION_DOCTRINE.md`

PAQS v0.3.x remains historical guardrail/formalization/audit/terminology reference only.

PAQS-Q research remains a separate deterministic/reference branch and must not silently bind this task.

The Master Spec remains strategy authority through this explicit Task Contract adoption; this task must not silently rewrite its trading semantics.

---

## 2. Product objective

Implement the first bounded PAQS-E reasoning runtime so that one immutable TASK-006B2 Market Snapshot plus an explicitly selected primary strategy Markdown package and explicit runtime context can be sent to a model-provider-neutral reasoning port and returned as one strictly structured, machine-validatable result.

Conceptual flow:

```text
TASK-006B2 immutable Market Snapshot
        +
explicit Runtime Configuration
        +
explicit Model ID
        +
selected Primary Strategy Markdown
        +
optional explicitly supplied Auxiliary Context
        ↓
versioned Reasoning Request
        ↓
PaqsEReasoningProvider
        ↓
OpenAI Responses API adapter (first provider only)
        ↓
strict structured model result
        ↓
deterministic validator
        ↓
validated reasoning result OR truthful provider/validation failure
```

The task must preserve the distinction:

```text
strategy Markdown = strategy semantics
runtime prompt/instructions = how the model should apply the strategy
output schema = serialization / machine contract
```

These layers must not be collapsed into one hard-coded prompt string.

---

## 3. Permanent and task-level boundaries

The product remains local-first, single-user and read-only.

TASK-007A must not add:

- brokerage-account connection or observation;
- real cash/position/order/trade access;
- broker writes;
- `place_order`, `cancel_order`, `modify_order`, `unlock_trade`;
- real-order UI/API;
- live OMS/EMS;
- autonomous/unattended trading;
- Analyze HTTP endpoint or Dashboard Analyze button;
- Decision Ledger database persistence;
- market-data persistence or new database migration;
- TASK-006B1 historical store/replay;
- PAQS-Q implementation;
- multi-model voting/ensemble;
- external web/news/social/file-search retrieval implementation;
- OpenAI tool-calling, web-search tool, browser, file-search tool or connector execution in this task.

The last two bullets are **scope exclusions for TASK-007A implementation only**, not a permanent strategy prohibition. Future tasks may explicitly supply or retrieve auxiliary context under separate governance.

---

## 4. Stable versioned reasoning input contract

Implement a versioned request domain, e.g. `PaqsEReasoningRequestV1` or an equivalent repository-conformant name.

The request must contain these conceptual sections. Exact class/file names may follow existing project conventions, but the semantics are mandatory.

### 4.1 Request identity

Required:

```text
request_schema_version
snapshot_hash
symbol
market
instrument_type
snapshot_as_of_timestamp
analysis_mode
runtime_config_version
prompt_version
output_schema_version
model_provider
model_id
primary_strategy_id
primary_strategy_content_sha256
```

The request must bind to the exact immutable TASK-006B2 snapshot identity.

No request may substitute a different symbol/market/as-of identity from the bound snapshot.

### 4.2 Runtime configuration

At minimum:

```text
supported_market_scope
supported_instrument_scope
htf
stf
ttf
short_advisory_allowed
short_execution_allowed
extended_hours_entry_reference_allowed
entry_reference_policy
quote_freshness_policy
optional versioned RR / ATR guardrails
```

Current v1 defaults/constraints:

```text
supported market scope = US / HK equities already supported by the product
HTF = W1
STF = D1
TTF = M30 REGULAR
short_advisory_allowed = true
short_execution_allowed = false
extended_hours_entry_reference_allowed = false
```

`short_execution_allowed` here means permission to emit an actionable short-entry semantic state such as `SHORT_READY`; it does not imply broker execution.

The model must not infer or silently change runtime permission fields.

### 4.3 Market snapshot facts

The request must carry or deterministically serialize the exact TASK-006B2 snapshot facts needed by the model, including the accepted snapshot identity and factual evidence:

- completed W1 evidence;
- completed D1 evidence;
- completed M30 REGULAR evidence;
- current price reference if present;
- market-state reference if present;
- calendar/session facts;
- adjustment provenance;
- quality/coverage/evidence provenance;
- provider-delay/provenance facts;
- snapshot warnings/reasons where present.

Do not inject legacy PAQS-Q Pivot/Zone/Range/Regime conclusions into the PAQS-E request as authoritative strategy facts.

### 4.4 Explicit extensible auxiliary context

The request architecture must support an optional ordered list of explicitly supplied auxiliary context items.

Each item must be auditable and conceptually contain at least:

```text
context_id
category
source_label
source_timestamp or null
provenance or null
as_of_compatible
content
```

`category` is intentionally extensible rather than a permanently closed enum.

Future callers may use categories such as news, web research, analyst research, social/community commentary, user context, previous PAQS-E result, conversation context, user-supplied position context, financial-report context, or other separately approved inputs.

TASK-007A does **not** implement retrieval for those sources. It only defines the stable explicit input path.

No hidden conversational memory or hidden previous result may be relied upon by the OpenAI adapter. If prior context is used, it must be explicitly represented in the current request or a future auditable extension of this contract.

Future-bar/lookahead information must never be marked `as_of_compatible=true` for a strict As-Of analysis.

### 4.5 Stateless transport semantics

Each provider call is a fresh request.

The OpenAI adapter must not use:

```text
previous_response_id
conversation state
background mode
```

The adapter must explicitly set `store=false` (or the exact SDK-equivalent field) for Responses API calls.

Stateless transport does **not** mean the model can never see prior context. It means all context used by the model must be explicit in the current versioned request rather than hidden provider state.

---

## 5. Primary Strategy Markdown Runtime

Implement a lightweight versioned primary-strategy runtime. Do not build a generic plugin framework.

### 5.1 Strategy registry

Provide a simple tracked, non-secret registry/manifest that maps stable `strategy_id` values to approved repository-relative Markdown files and display metadata.

A JSON or similarly simple project-consistent declarative format is acceptable.

The registry must have one default entry for the accepted PAQS-E Master Spec:

```text
strategy_id = paqs-e-master
strategy source path = docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md
```

The implementation must not hard-code the strategy Markdown body inside Python source or the OpenAI adapter.

### 5.2 Strategy loading

For the selected strategy:

- load UTF-8 Markdown from the registry-declared repository-relative path;
- reject missing/non-UTF-8/non-Markdown/unregistered paths truthfully;
- reject arbitrary absolute paths and path traversal;
- callers select by `strategy_id`, not arbitrary filesystem path;
- calculate SHA-256 over the exact strategy Markdown UTF-8 bytes;
- produce an immutable runtime package containing at least:

```text
strategy_id
display_name
source_path
content_sha256
content
```

A same-named Markdown file whose content changes must naturally produce a new `content_sha256` and therefore a new auditable strategy version identity.

### 5.3 Strategy/model independence

Model selection and primary-strategy selection are independent inputs.

The reasoning provider must conceptually support:

```text
model_id = <selected model>
primary_strategy_id = <selected registered strategy>
```

without embedding one into the other.

The current accepted PAQS-E Master Spec is the default strategy. The architecture may later register other Markdown strategies, but any alternative strategy used with the v1 reasoning result must conform to the same v1 output contract or adopt a separately versioned future schema.

### 5.4 Downstream UI compatibility only

TASK-007A does not implement the Dashboard selector.

However, the backend/application design must make it possible for TASK-007C to present model selection and primary-strategy selection side by side, e.g.:

```text
Model:            <selected model_id>
Primary Strategy: <selected strategy_id>
```

No frontend work is authorized in TASK-007A.

---

## 6. Runtime prompt package

Implement a compact versioned runtime instruction/prompt package separate from the strategy Markdown content.

It must:

- identify the selected strategy package and its hash;
- instruct the model to apply the supplied strategy rather than invent a different strategy;
- preserve strict As-Of/no-lookahead discipline;
- keep Event != Setup != Advisory;
- keep Trigger != Follow-through;
- keep Entry != Holder;
- require structural invalidation and structural targets for actionable states;
- forbid target shopping and retroactive invalidation widening;
- permit `NO_SETUP`, `NO_TRADE`, `WATCH_LONG`, `WAIT_RETEST`, `ENTRY_PENDING_REVALIDATION`, `DATA_UNAVAILABLE`, `UNCERTAIN` and other canonical non-action states;
- require explicit uncertainty and strongest alternative interpretation;
- require output to match the strict schema only.

The prompt package must be version-identifiable and hashable/auditable. A tracked resource file is preferred over a large inline string.

Do not duplicate the entire strategy Markdown into a second independently maintained strategy prompt.

---

## 7. Strict structured reasoning output contract

Implement a versioned strict output model, e.g. `PaqsEReasoningResultV1`.

All top-level required keys must be present. When a field is legitimately unavailable, use explicit null/empty values permitted by the schema rather than dropping required keys or inventing aliases.

The schema should preserve the Master Spec structure at minimum:

```text
identity
support / input quality
one-line thesis
context
key levels
current location
price action
setup
price references
entry advisory
invalidation
targets
risk/reward
holder advisory
uncertainty
next evidence needed
reason codes
concise explanation
```

Key levels must support zero items when the analysis is unavailable/invalid and otherwise at most four current decision-relevant levels.

Semantic zones and numeric calculation references must remain separate fields.

---

## 8. Exact machine enums for v1

Use exact canonical machine values. Do not emit aliases such as `A / B`, `Pending/Confirmed`, mixed-language values, or free-form replacements for enum fields.

### 8.1 Support / quality

```text
SupportStatus:
SUPPORTED
UNSUPPORTED

InputQuality:
COMPLETE
PARTIAL
INVALID
```

### 8.2 Context / bias

```text
ContextState:
BULL_TREND
BEAR_TREND
RANGE
TRANSITION
REVERSAL_CANDIDATE
TREND_DETERIORATING
UNCERTAIN
```

Because the Master Spec allows combined semantic states, each timeframe may expose a bounded list/set of `ContextState` values plus explanation rather than forcing one mutually exclusive one-hot state.

```text
MarketBias:
BULLISH
BEARISH
NEUTRAL
MIXED
UNCERTAIN
```

### 8.3 Location

```text
LocationQuality:
GOOD
MARGINAL
POOR
```

Location quality may be null when support/input quality prevents a reliable location judgment.

### 8.4 Event

```text
EventType:
CORRECTION
BREAK_ATTEMPT
ACCEPTED_BREAKOUT
FAILED_BREAKOUT
RECLAIM
RETEST
ROLE_FLIP
TREND_DETERIORATION
EXHAUSTION_CANDIDATE
NONE
```

### 8.5 Trigger — exact TASK-007A resolution

```text
TriggerStatus:
NOT_CONFIRMED
CONFIRMED
UNAVAILABLE
```

### 8.6 Follow-through — exact TASK-007A resolution

```text
FollowthroughStatus:
NOT_APPLICABLE
PENDING
WEAK
CONFIRMED
UNAVAILABLE
```

Mandatory consistency rules:

```text
trigger = NOT_CONFIRMED
    -> followthrough = NOT_APPLICABLE

trigger = CONFIRMED
    -> followthrough in {PENDING, WEAK, CONFIRMED}

trigger = UNAVAILABLE
    -> followthrough = UNAVAILABLE
```

This resolves focused re-review item S-01 while preserving `Trigger != Follow-through`.

### 8.7 Setup

```text
SetupFamily:
A_TREND_PULLBACK_CONTINUATION
B_FAILED_BREAKOUT_REVERSAL
C_RIGHT_SIDE_STRUCTURAL_BREAKOUT
NONE

SetupDirection:
LONG
SHORT
NEUTRAL

SetupStage:
NONE
CANDIDATE
TRIGGER_PENDING
FOLLOWTHROUGH_PENDING
CONFIRMED
EXPIRED

SetupExpiryReason:
PRICE_EXTENDED_OPPORTUNITY_MISSED
SETUP_GEOMETRY_REPLACED
STRUCTURE_INVALIDATED
RUNTIME_CONFIG_EXPIRY
```

`expiry_reason` must be null unless `SetupStage = EXPIRED`.

Do not invent universal N-bar expiry.

### 8.8 Entry advisory

```text
EntryAdvisory:
NO_SETUP
WATCH_LONG
WATCH_SHORT
ENTRY_PENDING_REVALIDATION
LONG_READY
SHORT_READY
VALID_SETUP_BUT_POOR_ENTRY
WAIT_RETEST
NO_TRADE
SETUP_EXPIRED
DATA_UNAVAILABLE
UNCERTAIN
```

Current v1 authorization rule:

```text
short_advisory_allowed = true
    -> WATCH_SHORT may be used when semantically justified

short_execution_allowed = false
    -> SHORT_READY must be rejected by deterministic validation
```

This resolves focused re-review item S-02 without suppressing bearish research/advisory reasoning.

### 8.9 Holder

```text
HolderAdvisoryBasis:
CURRENT_ANALYSIS_THESIS
PRIOR_DECISION_ID
NOT_AVAILABLE

HolderAdvisory:
NOT_APPLICABLE
THESIS_VALID
HOLD_WITH_WARNING
TARGET_REACHED_REVIEW
EXIT_IF_HELD
UNCERTAIN
DATA_UNAVAILABLE
```

A `PRIOR_DECISION_ID` basis is allowed only when the prior decision is explicitly supplied in the request; hidden conversation/provider state is not sufficient.

### 8.10 RR / risk and other exact enums

```text
RRStatus:
FINAL
PENDING_ENTRY_REFERENCE
NOT_COMPUTABLE

ChaseRisk:
LOW
MEDIUM
HIGH

UncertaintyLevel:
LOW
MEDIUM
HIGH

InvalidationStrength:
HARD
SOFT

PriceSessionType:
REGULAR
PRE
POST
CLOSED_REFERENCE
UNKNOWN

FreshnessStatus:
FRESH
STALE
DELAYED
UNKNOWN
```

---

## 9. Deterministic validator contract

Implement deterministic post-validation that does not replace PAQS-E strategy judgment.

The validator may reject/flag invalid model output for machine-contract violations such as:

- schema invalidity;
- request/snapshot identity mismatch;
- unsupported enum/alias;
- Trigger/Follow-through consistency violation;
- `SHORT_READY` while `short_execution_allowed=false`;
- actionable state without a valid structural invalidation;
- actionable state without a valid nearest structural T1;
- actionable state without numeric invalidation/T1 calculation references;
- actionable state without an eligible executable-entry reference;
- RR arithmetic mismatch;
- non-positive risk;
- target on the wrong side of entry for the declared direction;
- target shopping detectable from internally inconsistent T1/T2 references;
- reference-only quote being represented as completed-bar structural confirmation;
- output identity/hash/version fields not matching the request.

The validator must recompute deterministic financial arithmetic using Decimal, not binary float.

For long:

```text
risk = executable_entry - invalidation_reference
reward_t1 = t1_reference - executable_entry
rr_t1 = reward_t1 / risk
```

For short, only for schema/arithmetic completeness when runtime permission allows it in a future configuration:

```text
risk = invalidation_reference - executable_entry
reward_t1 = executable_entry - t1_reference
rr_t1 = reward_t1 / risk
```

If a valid executable entry or calculation reference is unavailable, RR cannot be `FINAL`.

The validator must never silently transform one valid strategy judgment into another, e.g.:

```text
WATCH_LONG -> LONG_READY
NO_TRADE -> LONG_READY
UNCERTAIN -> WATCH_LONG
```

Validation failure returns a truthful validation/provider failure, not a fabricated replacement strategy answer.

---

## 10. Provider-neutral reasoning port

Implement a provider-neutral port named `PaqsEReasoningProvider` or an equivalent project-consistent interface that preserves this planned architecture.

The core/application layer must not import the OpenAI SDK.

The port must accept the versioned reasoning request plus the resolved strategy/prompt packages as appropriate and return either:

- one structured provider success payload suitable for deterministic validation; or
- one truthful typed provider failure.

At minimum distinguish failures conceptually equivalent to:

```text
CONFIGURATION_ERROR
PROVIDER_UNAVAILABLE
PROVIDER_REFUSAL
INVALID_STRUCTURED_OUTPUT
```

Do not fabricate strategy output when the provider fails.

---

## 11. First provider adapter — OpenAI only

Implement the first provider-specific adapter under `integrations/` or the repository's established provider-specific boundary.

### 11.1 API choice

Use the current OpenAI **Responses API**, not the legacy Assistants API and not a Chat-Completions-only design.

Use the official OpenAI SDK as an explicit project dependency.

### 11.2 Strict Structured Outputs

Use the current Responses API / SDK mechanism for strict JSON-schema/Pydantic structured output.

The provider request must enforce the equivalent of:

```text
JSON Schema structured output
strict = true
```

Do not parse a free-form prose response as if it were authoritative structured output.

### 11.3 Statelessness and storage

Set:

```text
store = false
```

Do not use hidden provider conversation state, `previous_response_id`, or background execution in this task.

### 11.4 Model identifier

The OpenAI model identifier must be an explicit runtime/configuration input and must not be embedded inside the strategy Markdown.

Do not silently switch/fallback to a different model ID when the requested model is unavailable.

### 11.5 No OpenAI tools in TASK-007A

Do not attach web search, file search, browser/computer, code interpreter, MCP or other OpenAI tools in this task.

Again, this is an implementation boundary for TASK-007A, not a permanent ban on future explicitly governed auxiliary-context sources.

---

## 12. OpenAI API credential handling

The real API credential is supplied by the user locally.

Use the server-side environment variable:

```text
OPENAI_API_KEY
```

The real secret must never be:

- committed to GitHub;
- embedded in source code;
- embedded in strategy Markdown;
- embedded in runtime prompt resources;
- persisted in application data/database;
- persisted in a Decision Ledger;
- sent to frontend clients;
- returned by application APIs;
- written to ordinary logs;
- exposed in debug dumps;
- deliberately included in exception text.

The OpenAI SDK may read `OPENAI_API_KEY` from the process environment.

The repository may contain only a safe placeholder/documentation entry such as `OPENAI_API_KEY=` in `.env.example` if needed.

The existing `.gitignore` already excludes `.env` and `.env.*` except `.env.example`; preserve this protection.

Missing API credential must fail truthfully as provider/configuration unavailable. Do not fall back to a fake response.

No Dashboard API-key input/storage UI is part of TASK-007A.

---

## 13. Data retention and audit metadata

TASK-007A does not implement Decision Ledger persistence.

However, the validated runtime result and provider metadata must expose enough non-secret identity for TASK-007B to persist later, including conceptually:

```text
snapshot_hash
request_schema_version
output_schema_version
strategy_id
strategy_content_sha256
prompt_version / prompt hash
runtime_config_version
model_provider
model_id
provider request/result identity if safe and useful
validator version
```

Never include `OPENAI_API_KEY` in audit metadata.

---

## 14. Expected implementation areas

Exact filenames may follow existing repository conventions, but expected bounded areas include:

- core/domain models/enums for reasoning request/result and validation;
- core/application provider-neutral port;
- application/runtime service for strategy/prompt loading and request assembly where appropriate;
- one simple tracked strategy registry/manifest;
- one versioned runtime prompt resource;
- OpenAI integration adapter under provider-specific `integrations/` code;
- safe configuration loading for `OPENAI_API_KEY`;
- `pyproject.toml` dependency update for official OpenAI SDK;
- `.env.example` placeholder/documentation if required;
- focused unit/integration tests;
- minimal architecture/API-contract documentation updates required to explain TASK-007A internal contracts.

No database migration is expected or authorized.

---

## 15. Required tests

Implement focused deterministic tests covering at least:

### Strategy runtime

- default PAQS-E strategy registry entry resolves the authoritative Markdown path;
- exact UTF-8 content is loaded;
- SHA-256 changes when strategy content changes;
- same content produces same SHA-256;
- unregistered strategy ID fails truthfully;
- missing strategy file fails truthfully;
- absolute/path-traversal source is rejected;
- strategy Markdown body is not duplicated/hard-coded in the OpenAI adapter.

### Request binding

- request identity matches exact snapshot identity;
- mismatch in snapshot hash/symbol/market/as-of is rejected;
- auxiliary context is explicit/ordered/auditable;
- no hidden prior result or provider conversation state is required.

### Output schema/enums

- every exact enum round-trips through the schema;
- aliases/free-form enum replacements fail;
- Trigger/Follow-through consistency matrix is enforced;
- setup expiry reason is required only for `EXPIRED` and no hidden N-bar expiry is introduced;
- `SHORT_READY` fails while `short_execution_allowed=false`;
- `WATCH_SHORT` may pass while `short_advisory_allowed=true`.

### Deterministic validator

- Decimal long RR calculation;
- invalid/non-positive risk rejection;
- target-direction rejection;
- missing executable entry prevents `RRStatus=FINAL`;
- actionable advisory without invalidation/T1/numeric references is rejected;
- validator does not upgrade/downgrade valid strategy states on its own.

### OpenAI adapter without live secret/network dependency

Use fakes/mocks/injected client boundaries so normal tests do not require a real API key or paid API call.

Verify the adapter:

- uses Responses API path/SDK surface;
- requests strict structured output;
- sets `store=false`;
- supplies selected strategy Markdown and versioned runtime prompt;
- supplies the explicit model ID;
- does not configure OpenAI tools;
- does not use `previous_response_id`/conversation/background state;
- maps refusal/invalid structured output/provider error to typed truthful failures;
- never exposes API credential through returned domain objects.

### Configuration/security

- missing `OPENAI_API_KEY` -> truthful configuration/provider failure;
- `.env` remains ignored;
- no secret value exists in committed fixtures/tests/docs;
- error/log serialization used by the implementation cannot intentionally include the credential.

### Regression

Run the existing full test suite and preserve all accepted Phase 1 / TASK-003 through TASK-006B2 behavior.

---

## 16. Validation commands / quality gate

At minimum run the repository-standard equivalents of:

```text
pytest focused TASK-007A tests
pytest full suite
ruff check
ruff format --check (or repository-equivalent formatting verification)
mypy
```

Also verify application startup and existing health/OpenAPI behavior remain intact when feasible.

A real OpenAI paid/network smoke call is **not required** for task acceptance and must not be fabricated if unavailable.

If an optional live smoke is attempted, it must use the user's local environment secret only and must never print the secret.

---

## 17. Protected history and no-scope-leak rules

Do not modify accepted Phase 1 immutable evidence or migration history.

In particular do not modify:

- `docs/phases/PHASE_1_PLAN.md`
- `docs/reviews/PHASE_1_INDEPENDENT_REVIEW.md`
- `docs/reviews/PHASE_1_POST_REMEDIATION_REVIEW.md`
- `src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py`

If `phase1_remediation_commit.txt` exists locally, leave it untracked, untouched, unstaged and uncommitted.

Do not alter TASK-006B2 snapshot semantics merely to make the provider implementation easier.

Do not rewrite accepted PAQS-E research source documents during this task.

---

## 18. Acceptance criteria

TASK-007A is acceptable only if all are true:

1. dedicated task branch descends exactly from authoritative base `6218c69...`;
2. accepted Master Spec exact authoritative content is explicitly adopted and usable as the default runtime strategy Markdown;
3. strategy Markdown content is not hard-coded in the OpenAI adapter;
4. a registered strategy can be selected independently from model ID;
5. selected strategy content hash is deterministic and auditable;
6. reasoning input is stable/versioned and supports explicit extensible auxiliary context;
7. output is strict/versioned/machine-readable;
8. Trigger/Follow-through exact enums and consistency rules are implemented exactly;
9. short advisory vs short actionable permission is separated exactly;
10. OpenAI adapter uses Responses API with strict structured output and `store=false`;
11. model ID is explicit and no silent model fallback occurs;
12. API credential remains server-side environment-only and is not committed/persisted/exposed;
13. deterministic validator checks identity/schema/facts/Decimal RR without replacing strategy judgment;
14. provider failure/refusal/invalid output is truthful and no fake strategy answer is produced;
15. no Analyze API, Decision Ledger persistence, Dashboard selector, market-data persistence, replay, PAQS-Q or broker behavior leaks into scope;
16. focused/full tests, Ruff and mypy pass except clearly documented pre-existing/environmental skips;
17. independent GitHub review of the exact final implementation SHA returns PASS before integration.

---

## 19. Stop condition and delivery

Codex may implement only after reading this Contract from the exact task branch.

Codex must:

- implement only TASK-007A on `task/007a-paqs-e-runtime-openai-strategy-port`;
- commit and push only that task branch;
- not merge `roadmap/no-live-trading`;
- not create TASK-007B/007C/006B1 branches;
- stop for independent review.

Final implementation report must include:

- authoritative base SHA;
- Task Contract commit SHA;
- final implementation HEAD;
- exact changed files;
- request/output schema versions;
- exact enum sets implemented;
- strategy registry/default strategy path and content SHA-256;
- runtime prompt version/hash;
- OpenAI SDK/API behavior used;
- confirmation `store=false` and no hidden provider state/tools;
- API credential handling evidence without revealing the secret;
- focused/full test results;
- Ruff/mypy results;
- startup/health/OpenAPI regression results where applicable;
- any environmental/live-API limitation;
- explicit confirmation that no 007B/007C/persistence/broker scope leaked.

**End — TASK-007A**
