# PAQS Dual-Branch Product Architecture Review

**Status:** PRODUCT / ARCHITECTURE REVIEW — DUAL-BRANCH DIRECTION ACCEPTED FOR MIGRATION PLANNING; ROADMAP AND IMPLEMENTATION CHANGES STILL REQUIRE EXPLICIT USER APPROVAL  
**Repository:** `ahhhhzzz/ai-infra-quant`  
**Research branch:** `research/006b-structure-stability`  
**Authoritative product branch at review time:** `roadmap/no-live-trading`  
**Authoritative product HEAD at review time:** `96747041ef0ff8c00937c5dd5e80cb4c5c28c17c`

Source memo:

- `docs/research/PAQS_DUAL_BRANCH_PRODUCT_ARCHITECTURE_MEMO.md`

Related research:

- `docs/research/PAQS_V0.4_LITE_STRUCTURE_QUANT_AMENDMENT.md`
- `docs/research/TASK_006B_STRUCTURE_STABILITY_REVIEW.md`

This document answers the strategy memo's requested Product Manager questions and proposes a bounded migration/implementation sequence. It is not a Task Contract and does not authorize Codex implementation.

---

## 1. Product decision: accept PAQS-E and PAQS-Q as parallel branches

**Decision for migration planning: ACCEPT.**

PAQS is reinterpreted as a family with two parallel strategy engines:

```text
                         PAQS
                          |
              +-----------+-----------+
              |                       |
           PAQS-Q                   PAQS-E
      Quant Decision Engine   Expert Reasoning Engine
      deterministic code           LLM-native
```

The branches share factual market infrastructure but have different strategy semantics and validation standards.

They must not be averaged into one numerical decision score.

They may disagree; disagreement is a first-class diagnostic fact.

The human user remains the final capital decision maker. Both branches remain read-only decision support.

---

## 2. Reclassification of existing PAQS v0.3.x research

Existing v0.3 / v0.3.1 research documents must remain immutable historical research artifacts. Do not rename or rewrite them merely to make the new architecture look clean.

Reclassify them through additive documentation/indexing:

```text
PAQS v0.3.x research
    -> historical semantic foundation for PAQS-E
    -> source of Expert Reasoning vocabulary and reasoning contracts
    -> not automatically executable deterministic-code requirements
```

A future architecture index may label the documents as `PAQS-E FOUNDATION` without changing their original content or approval history.

The accepted TASK-006B implementation remains historical evidence of the attempt to deterministically formalize part of v0.3.x. Its real-market stability findings remain evidence; they are not erased by the branch split.

---

## 3. Reclassification of PAQS v0.4 Lite

The current v0.4 Lite amendment becomes the research foundation for:

```text
PAQS-Q — Quant Decision Engine
```

Its objective is bounded, deterministic, reproducible machine judgment rather than semantic supersession of PAQS-E.

Its current concrete defaults remain research defaults until separately approved as implementation semantics.

Therefore documentation should eventually say:

```text
PAQS-E: rich Expert Price Action reasoning branch
PAQS-Q: stable deterministic Quant/Price-Action subset
```

not:

```text
v0.4 replaces all v0.3 semantics
```

---

## 4. Current Roadmap task migration

### TASK-006A

**KEEP unchanged; classify as SHARED FOUNDATION.**

TASK-006A already provides the canonical US/HK security, calendar/session, W1/D1/M30, coverage, quality and adjustment foundations needed by both engines.

### TASK-006B

**KEEP as historical accepted deterministic implementation evidence; do not delete or pretend it passed semantic market acceptance.**

Status should eventually be represented as:

```text
TASK-006B deterministic implementation: PASS / integrated
TASK-006B real-market semantic checkpoint: STRUCTURE_CONCERNS_FOUND
```

It becomes the predecessor/prototype evidence for PAQS-Q stabilization, not the complete PAQS family implementation.

### TASK-006B1 — Local Market Data Store & Replay Foundation

**KEEP, elevate to SHARED FOUNDATION, and execute before the two strategy branches become dependent on historical reproducibility.**

Its existing planned purpose remains valid:

- canonical completed D1 persistence;
- canonical completed 1m persistence;
- provenance/retrieved-at/adjustment/quality metadata;
- observation/version semantics;
- incremental ingest/dedupe;
- deterministic replay support.

It should not implement strategy logic.

### New TASK-006B2 — Point-in-Time Market Snapshot Contract

**ADD as SHARED FOUNDATION after TASK-006B1.**

Purpose:

- construct immutable PAQS market snapshots from legitimate stored/current facts;
- canonical serialization and `snapshot_hash`;
- strict `as_of_timestamp` boundary;
- W1/D1/M30 completed-bar payloads;
- objective numerical features allowed to be shared by Q/E;
- data-quality, session, coverage and adjustment provenance;
- deterministic replay/fetch by snapshot identity where supported.

No PAQS-Q or PAQS-E strategy judgment belongs in TASK-006B2.

### New TASK-006B-Q — PAQS-Q Structure Stabilization

**ADD after explicit approval of PAQS-Q/v0.4 concrete semantics.**

This is the bounded deterministic structure task that resolves the existing 006B semantic checkpoint through the Lite machine branch rather than continually expanding v0.3 deterministic complexity.

It should include the expanded external-data robustness checkpoint before semantic acceptance.

### Existing TASK-006C / TASK-006D / TASK-006E

**DO NOT execute under their current single-engine wording. Re-scope into PAQS-Q tasks:**

```text
TASK-006C-Q — PAQS-Q Event Engine
TASK-006D-Q — PAQS-Q Setup, Risk & Setup-Specific Quant Confirmation
TASK-006E-Q — PAQS-Q Advisory / Scanner Presentation
```

The useful event/setup/risk/advisory concepts remain; only their ownership becomes explicit.

### New TASK-007 umbrella — PAQS-E Expert Reasoning Workstream

`TASK-007` is umbrella only and must never itself become an implementation Task Contract.

Bounded planned tasks:

```text
TASK-007A — PAQS-E Contracts, Structured Output & Provider Port
TASK-007B — PAQS-E Default Provider Integration & Expert Analysis Service
TASK-007C — PAQS-E Immutable Decision Ledger & As-Of Evaluation Harness
TASK-007D — Dual-Branch Decision Dashboard & Disagreement Presentation
```

TASK-007A/B/C depend on the shared Point-in-Time Market Snapshot Contract. TASK-007D depends on usable outputs from both branches.

---

## 5. Minimum PAQS-E architecture for an LLM-native MVP

Minimum components:

```text
Shared Market Snapshot
        |
        v
PAQS-E Analysis Service
        |
        +--> Versioned Strategy/Prompt Package
        |
        +--> LLM Reasoning Provider Port
        |        |
        |        +--> default provider adapter
        |
        +--> Structured Output Schema
        |
        +--> Deterministic Post-Validator
        |
        +--> Immutable Decision Ledger
```

Minimum behavior:

1. user requests analysis for a supported security;
2. product obtains/builds one immutable point-in-time snapshot;
3. one versioned PAQS-E reasoning package is applied;
4. provider returns structured output;
5. deterministic validation checks schema, references, arithmetic and snapshot identity;
6. result is stored immutably;
7. API/UI returns the stored decision plus explanation.

Not required for first MVP:

- multi-model voting;
- ensemble scoring;
- autonomous prompt optimization;
- arbitrary web browsing by the model;
- news/sentiment reasoning;
- chart-vision input;
- background autonomous analysis;
- broker integration.

---

## 6. Model-provider abstraction location

The provider abstraction belongs at the application/integration boundary, not in the PAQS-E core semantics.

Recommended logical layout:

```text
core / strategy
    PAQS-E provider-neutral domain schemas and invariants

application
    PAQS-E analysis orchestration
    LLMReasoningProvider port

integrations / llm
    provider-specific adapters
    SDK/API translation
```

The core must not import OpenAI, Anthropic, Google or another provider SDK.

Provider credentials/configuration remain adapter/infrastructure concerns.

The current default provider can change without changing PAQS-E strategy semantics or historical ledger schemas.

---

## 7. PAQS-E Market Snapshot Contract — exact logical fields

The first contract should include at minimum:

```text
snapshot_version
snapshot_hash
security_id
market
symbol
market_timezone
as_of_timestamp
snapshot_created_at

market_data_provider
provider_retrieved_at
adjustment_basis
historical_replay_safe
data_quality
warnings[]

session_metadata
coverage_metadata

completed_w1_bars[]
completed_d1_bars[]
completed_m30_bars[]

objective_features:
    atr14_by_timeframe
    optional ema20
    optional ema50
    optional roc20
    optional roc60
```

Every bar supplied to the model must contain a canonical source reference and at least:

```text
interval/session identity
open
high
low
close
volume
completion/coverage status
```

Only legitimately completed/eligible bars enter authoritative reasoning inputs.

For the first PAQS-E MVP, arbitrary live quote data should not silently mix with completed-bar reasoning. If later included, it must be explicitly separated and timestamped as non-completed/current context.

The snapshot hash must be computed from canonical provider-neutral content, not provider-native objects.

---

## 8. Immutable LLM Decision Ledger — exact logical fields

Minimum ledger record:

```text
decision_id
strategy_family = PAQS-E
strategy_version

security_id
market
symbol

snapshot_version
snapshot_hash
as_of_timestamp

prompt_package_version
prompt_hash
output_schema_version

model_provider
model_id
model_version_or_snapshot_if_exposed
reasoning_config_hash
provider_request_metadata_where_safe

structured_output
raw_explanation
raw_provider_response_if_policy_permits

post_validation_status
post_validation_errors[]

created_at
supersedes_decision_id?   # optional explicit revision link
```

Useful operational metadata may include latency, token usage and provider request ID when available, but these are not strategy semantics.

The ledger is append-only from normal application behavior. New analysis creates a new decision record; it never rewrites a historical judgment.

---

## 9. Strategy / prompt / model version tracking

Historical comparability requires separate dimensions:

```text
strategy_version
    = semantic PAQS-E specification version

prompt_package_version + prompt_hash
    = exact model instruction/rendering contract

snapshot_version + snapshot_hash
    = exact factual input contract/content

output_schema_version
    = structured response schema

model_provider + model_id + provider model snapshot/version if exposed
    = reasoning implementation identity

reasoning_config_hash
    = provider-neutral canonical representation of relevant request settings
```

Never collapse these into one generic `version` string.

Comparisons across decisions must surface which dimensions changed.

If a provider does not expose an immutable model snapshot, store the exact model identifier and truthfully mark stronger reproducibility as unavailable.

---

## 10. PAQS-E historical As-Of evaluation without hindsight

Required evaluation flow:

```text
historical cutoff t
    -> reconstruct/fetch only facts legitimately observed <= t
    -> build immutable snapshot(t)
    -> freeze snapshot(t)
    -> run PAQS-E using declared strategy/prompt/model versions
    -> store decision in evaluation ledger
    -> only afterward attach realized future outcome labels for scoring
```

Forbidden:

- current full chart with future bars hidden only in prose;
- provider data that silently uses future corporate-action knowledge while claiming strict point-in-time safety;
- regeneration of historical model decisions after seeing outcomes and replacement of the original result;
- using realized outcome labels inside the reasoning prompt.

This makes TASK-006B1 observation/version semantics and TASK-006B2 snapshot identity prerequisites for scientifically stronger historical PAQS-E evaluation.

Until point-in-time-safe adjustment history exists, evaluation must truthfully label its adjustment limitation.

---

## 11. Dashboard presentation of PAQS-Q and PAQS-E

Use one shared security/as-of header and two separate engine panels.

Recommended structure:

```text
Symbol / As-Of / Data Quality

PAQS-Q                         PAQS-E
Quant Decision Engine          Expert Reasoning Engine
---------------------          -----------------------
Context / Regime               Expert Context
Current Zones                  Key Levels
Range                          Events / Setup
Trend / Momentum               Trigger / Follow-through
Extension                      Invalidation
Machine state                  Targets / RR
Reasons                        Entry / Holder Advisory
                               Explanation

Disagreement / Alignment Panel
```

Rules:

- no average score;
- no hidden override;
- each engine retains its own reason codes and state;
- disagreement is explicitly shown;
- stale/unavailable/error on either engine is shown independently;
- user may run PAQS-E directly for a selected symbol without a PAQS-Q candidate prerequisite.

First alignment metadata should be categorical/descriptive, not a learned numerical ensemble.

---

## 12. Shared versus isolated components

### Shared

```text
Security identity / watchlist
Market data provider boundary
Local Market Data Store
Calendar/session logic
Completed-bar eligibility
W1/D1/M30 aggregation
Adjustment/quality metadata
Point-in-Time Market Snapshot
Snapshot hashing
Objective numerical features
As-Of discipline
API/auth/local application shell
Dashboard shell
Read-only/no-broker safety boundary
```

### PAQS-Q isolated

```text
bounded Pivot semantics
Zone/Range machine rules
Regime machine rules
Event machine rules
Setup-specific Quant rules
Q advisory states/logic
Q robustness metrics
```

### PAQS-E isolated

```text
Expert Reasoning specification
Prompt package
LLM provider port/adapters
E structured reasoning semantics
E post-validation rules specific to model output
E Decision Ledger
E Gold Set / reasoning-quality evaluation
```

Shared vocabulary may exist, but an E judgment must not be silently replaced by Q logic or vice versa.

---

## 13. Additional architectural risks

### Model nondeterminism and drift

Same snapshot may not always produce identical reasoning. Record versions/configuration and measure repeated-run stability rather than falsely claiming deterministic reproducibility.

### Provider model retirement/change

A provider may change or remove model behavior. Historical ledger metadata must preserve what can be known, and evaluations must not pretend a missing immutable model snapshot exists.

### Cost/rate-limit/outage risk

PAQS-E should be on-demand in the first MVP. PAQS-Q handles scalable scanning. A provider outage must degrade PAQS-E independently without breaking PAQS-Q or market-data viewing.

### Hallucinated numerical facts

The model must not invent bars/levels outside the snapshot. Structured references and deterministic post-validation should reject impossible/non-finite/out-of-contract values and verify RR arithmetic.

### Context-size growth

Do not send unbounded raw history to the model. Snapshot contracts need declared bounded windows and/or derived context while preserving sufficient Price Action evidence.

### Prompt/model leakage in evaluation

Gold Set labels and realized outcomes must not appear in model inputs.

### Subjective Gold Set bias

Gold Set records should allow acceptable ranges/interpretations rather than one hindsight-perfect answer. Separate structural quality evaluation from realized P&L.

### Provider data privacy/retention

Before enabling an external LLM provider in production, document what snapshot data is transmitted and configure provider/account settings consistent with the user's privacy requirements.

### Automation bias

UI must retain uncertainty/reason codes and read-only decision-support positioning. PAQS-E confidence must not be presented as guaranteed probability unless separately calibrated.

### Snapshot/chart mismatch

If chart images are added later, they must be deterministically rendered from exactly the same `snapshot_hash` inputs supplied as structured facts.

### Branch coupling risk

PAQS-E and PAQS-Q must not become mutually blocking at runtime. Either engine can be unavailable while the other remains usable.

---

## 14. Governance for future Task Contracts

Research documents remain non-authoritative for code execution unless an explicit user-approved Task Contract says otherwise.

Required sequence remains:

```text
research / architecture
    -> Product Manager bounded task proposal
    -> user explicit approval
    -> Task Contract committed on dedicated task branch
    -> short Codex execution prompt referencing exact branch/contract/base SHA
    -> implementation push
    -> independent review of exact HEAD
    -> focused remediation if needed
    -> non-force integration only after exact reviewed-HEAD verification
```

Every future Task Contract must cite the exact research documents it adopts and explicitly list research ideas it does **not** adopt.

No memo/amendment/review status may be interpreted as implementation authority.

---

# Recommended implementation migration sequence

The highest-leverage sequence is to finish shared factual/replay infrastructure before duplicating strategy-specific plumbing.

```text
MIGRATION DECISION / ROADMAP UPDATE
        |
        v
TASK-006B1
Local Market Data Store & Replay Foundation
        |
        v
TASK-006B2
Point-in-Time Market Snapshot Contract
        |
        +------------------------------+
        |                              |
        v                              v
PAQS-Q branch                       PAQS-E branch
TASK-006B-Q                         TASK-007A
Structure Stabilization             Contracts + Provider Port
        |                              |
external robustness                 TASK-007B
checkpoint                          Default Provider + Analysis
        |                              |
TASK-006C-Q                         TASK-007C
Events                              Decision Ledger + As-Of Eval
        |
TASK-006D-Q
Setup/Risk/Quant
        |
TASK-006E-Q
Q Advisory/Scanner
        |                              |
        +--------------+---------------+
                       v
                    TASK-007D
              Dual-Branch Dashboard
```

Reasons for this order:

1. TASK-006B1 was already identified as necessary before richer replay work and is strategy-neutral.
2. The dual-branch architecture makes immutable point-in-time snapshots a shared contract rather than an E-only concern.
3. PAQS-Q concrete semantics still require explicit approval; shared infrastructure can progress without prematurely freezing them.
4. PAQS-E should not call a model until the product can prove exactly what facts/as-of snapshot were sent.
5. PAQS-Q remains the scalable scanner; PAQS-E remains on-demand/deep reasoning initially.

---

# Recommended first implementation task

**TASK-006B1 — Local Market Data Store & Replay Foundation** should be the next implementation task after Roadmap migration approval.

It is the least strategy-dependent, highest-reuse next step and benefits:

- PAQS-Q replay and robustness validation;
- PAQS-E strict As-Of snapshots/evaluation;
- lower repeated OpenD history consumption;
- future deterministic local reads;
- observation/version provenance;
- later snapshot hashing and Decision Ledger integrity.

The existing staging node `docs/roadmap/TASK-006B1_LOCAL_MARKET_DATA_STORE_REPLAY_FOUNDATION.md` should be rebased/reapplied onto the then-current authoritative Roadmap only after explicit migration approval. Its scope should remain storage/replay focused; Point-in-Time Market Snapshot construction belongs to separate TASK-006B2 to keep both tasks bounded.

---

# Migration approval boundary

This review recommends the dual-branch migration and task sequence. It does not itself move `roadmap/no-live-trading`, rewrite `REQUIREMENTS_MATRIX.md`, create implementation task branches, or authorize Codex.

Before implementation, Product Management should obtain explicit user approval for the Roadmap migration decision. Then authoritative Roadmap/Requirements can be updated in a docs-only migration commit, after which TASK-006B1 can be discussed and drafted as the first implementation Task Contract.

**End — PAQS Dual-Branch Product Architecture Review**
