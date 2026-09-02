# PAQS Dual-Branch Roadmap Migration Proposal

**Status:** PRODUCT MIGRATION PROPOSAL — USER APPROVAL REQUIRED; AUTHORITATIVE ROADMAP NOT YET CHANGED  
**Repository:** `ahhhhzzz/ai-infra-quant`  
**Research branch:** `research/006b-structure-stability`  
**Authoritative product branch:** `roadmap/no-live-trading`  
**Authoritative product HEAD at drafting:** `96747041ef0ff8c00937c5dd5e80cb4c5c28c17c`

Primary inputs:

- `docs/research/PAQS_DUAL_BRANCH_PRODUCT_ARCHITECTURE_MEMO.md`
- `docs/research/PAQS_DUAL_BRANCH_PRODUCT_ARCHITECTURE_REVIEW.md`
- `docs/research/PAQS_DUAL_BRANCH_ARCHITECTURE_REVIEW_ADDENDUM_A.md`
- `docs/research/PAQS_E_NAKED_PRICE_ACTION_DOCTRINE.md`
- `docs/research/PAQS_V0.4_LITE_STRUCTURE_QUANT_AMENDMENT.md`
- `docs/research/TASK_006B_STRUCTURE_STABILITY_REVIEW.md`

This proposal defines the exact product/task migration recommended for the authoritative Roadmap and Requirements Matrix. It is not itself authoritative and does not authorize Codex or any implementation task.

---

## 1. Proposed decision record

Recommended decision identifier:

```text
PAQS-DUAL-001
```

Proposed decision:

> PAQS becomes a dual-branch read-only investment decision-support architecture. PAQS-E is the prioritized LLM-native Naked Price Action Expert Reasoning branch. PAQS-Q is a separate deterministic machine-quant reference/scanner branch. Both consume product-controlled point-in-time market facts and operate on explicit user-triggered Snapshot-on-Demand analyses. Neither branch connects to brokerage accounts or performs autonomous trading.

This decision supersedes the existing future assumption that TASK-006C/006D/006E form one single PAQS engine path, while preserving all accepted historical implementation/review evidence.

---

## 2. Product operating model after migration

Current MVP decision flow becomes:

```text
User selects supported US/HK Security
        ↓
User explicitly requests Analyze
        ↓
Product creates immutable Snapshot-on-Demand market facts
        ↓
        ├────────────────────────────┐
        ↓                            ↓
PAQS-E Expert Engine             PAQS-Q Quant Engine
prioritized LLM-native           deterministic/reference
        ↓                            ↓
Expert advisory                 Quant advisory/baseline
        └─────────────┬──────────────┘
                      ↓
             Dashboard / comparison
                      ↓
             Human capital decision
```

Market-data display refresh remains separate from strategy analysis.

Neither PAQS-E nor PAQS-Q automatically re-runs on every quote/bar refresh in the current MVP.

---

## 3. Shared runtime invariants

Both branches inherit:

```text
read-only decision support
single-user local-first product
no brokerage-account access
no broker writes
no autonomous trading
strict As-Of boundary
completed-bar structural evidence
no lookahead
Decimal/factual validation where applicable
immutable historical decision revisions where persisted
```

Current structural evidence:

```text
W1 = completed weekly bars
D1 = completed daily bars
M30 = completed regular-session 30-minute bars
```

Latest quote may be exposed separately as reference-only current-price context and must not confirm completed-bar structure.

---

## 4. PAQS-E authoritative strategy positioning

After migration, documentation should classify:

```text
PAQS_E_NAKED_PRICE_ACTION_DOCTRINE.md
    = primary PAQS-E semantic strategy authority candidate

PAQS v0.3.x documents
    = historical formalization / guardrail / audit / terminology reference

PAQS-Q v0.4 Lite research
    = separate deterministic machine-branch research foundation
```

Do not rewrite or delete v0.3.x historical research to create the new classification.

PAQS-E strategy reasoning remains semantic and must not be silently replaced by PAQS-Q thresholds.

---

## 5. PAQS-Q positioning

PAQS-Q remains useful but is no longer the product bottleneck for PAQS-E.

PAQS-Q objectives:

```text
engineering stability
reproducibility
bounded machine structure
large-universe scanning later
quantitative reference
repeatable comparison
robustness diagnostics
```

Its strategy methods may evolve later through separately approved research/Task Contracts.

PAQS-Q does not define PAQS-E semantics.

---

## 6. Historical task disposition

### TASK-003 / 004 / 005 / 005A / 005B

**KEEP unchanged as accepted market-data / Dashboard / launcher baseline.**

### TASK-006A

**KEEP unchanged and classify as SHARED PAQS FOUNDATION.**

It provides:

```text
supported US/HK Security workflow
provider validation
calendar/session semantics
completed W1/D1/M30 inputs
coverage/quality/adjustment metadata
```

### TASK-006B

**KEEP as historical deterministic implementation evidence.**

Record status explicitly:

```text
TASK-006B deterministic implementation: PASS / integrated
TASK-006B real-market semantic checkpoint: STRUCTURE_CONCERNS_FOUND
```

Do not delete its implementation or pretend it achieved final market-semantic acceptance.

It becomes prototype/research evidence feeding PAQS-Q stabilization.

---

## 7. Shared planned task map

### TASK-006B2 — Snapshot-on-Demand Current Market Snapshot Contract

**Recommended next implementation task after Roadmap migration.**

Purpose:

- create one immutable current analysis snapshot from existing accepted current/read-through facts;
- strict `as_of_timestamp` boundary;
- canonical W1/D1/M30 completed-bar payloads;
- latest quote as optional explicitly reference-only field;
- session/calendar/coverage/quality/adjustment/provider provenance;
- objective numerical facts approved for sharing;
- canonical serialization and `snapshot_hash`;
- no PAQS-Q or PAQS-E strategy judgment;
- no LLM call;
- no market-data persistence requirement.

The task should be intentionally sufficient for current on-demand PAQS-E analysis without waiting for historical replay infrastructure.

### TASK-006B1 — Local Market Data Store & Replay Foundation

**KEEP as shared foundation but move behind the initial PAQS-E current-analysis MVP.**

Purpose remains:

```text
canonical completed D1 persistence
canonical completed 1m persistence
provenance / retrieved_at / adjustment / quality
incremental ingest / dedupe
observation/version semantics
local deterministic replay
lower repeated OpenD historical consumption
```

It becomes mandatory before strict arbitrary historical As-Of replay/evaluation is claimed.

It must not implement PAQS-E or PAQS-Q strategy logic.

---

## 8. PAQS-E prioritized workstream

Create umbrella only:

```text
TASK-007 — PAQS-E Expert Reasoning Workstream
```

TASK-007 is never itself an implementation task.

### TASK-007A — PAQS-E Doctrine Runtime, Structured Output & OpenAI Provider Port

Recommended immediately after TASK-006B2.

Bounded scope:

- versioned runtime extraction/package from `PAQS_E_NAKED_PRICE_ACTION_DOCTRINE.md`;
- compact doctrine + canonical reasoning questions + hard guardrails;
- PAQS-E input request domain bound to snapshot identity;
- PAQS-E structured output schema based on Doctrine Section 26;
- provider-neutral `PaqsEReasoningProvider` port;
- first/only implementation adapter: OpenAI;
- configurable server-side model identifier;
- no frontend API key exposure;
- no web/browser/tool calls supplied to the model;
- stateless/fresh analysis request semantics;
- deterministic schema/fact/RR post-validator;
- no continuous/background analysis;
- no broker behavior.

A real provider smoke may be included if credentials/environment are available, but deterministic adapter/schema acceptance must not depend on committing secrets.

### TASK-007B — On-Demand PAQS-E Analysis Service & Immutable Decision Ledger

Scope:

- explicit user-triggered Analyze application service/API;
- one request freezes/uses one immutable snapshot;
- one PAQS-E analysis result per request;
- immutable decision persistence/revision semantics;
- store snapshot identity, doctrine/prompt/provider/model metadata and structured result;
- preserve past decisions; never regenerate/overwrite history;
- allow provider unavailability to fail truthfully;
- no automatic re-analysis on market-data refresh.

### TASK-007C — PAQS-E User Dashboard

Scope:

- user-visible `Analyze with PAQS-E` action;
- show snapshot/as-of metadata;
- one-line thesis;
- HTF/STF/TTF context;
- 1–4 key decision levels;
- location;
- event/setup/stage;
- trigger/follow-through;
- entry advisory;
- holder advisory;
- invalidation;
- T1/T2 and deterministic RR;
- chase/poor-entry warning;
- uncertainty/conflicting evidence;
- alternative interpretation;
- next evidence needed;
- show prior immutable decisions separately when requested;
- no real-order controls.

### PAQS-E historical evaluation expansion

After TASK-006B1/local replay foundation is available, extend PAQS-E evaluation through a separately approved bounded task or extension of TASK-007B/C governance:

```text
strict historical As-Of snapshots
Gold Set
prompt/model stability
key-level/setup/invalidation/target quality
NO_TRADE discipline
anti-hindsight evaluation
```

No P&L-only model selection.

### TASK-007D — Dual-Branch Comparison / Disagreement Dashboard

Defer until PAQS-Q produces a usable advisory/reference output.

Scope:

- same snapshot identity displayed for Q/E comparison;
- separate outputs;
- alignment/disagreement diagnostics;
- no averaging into one synthetic score.

---

## 9. PAQS-Q workstream after migration

Existing future single-engine tasks are not executed as currently worded.

Reclassify/rescope:

```text
TASK-006B-Q — PAQS-Q Structure Stabilization
TASK-006C-Q — PAQS-Q Event Engine
TASK-006D-Q — PAQS-Q Setup, Risk & Setup-Specific Quant Confirmation
TASK-006E-Q — PAQS-Q Advisory / Scanner Presentation
```

PAQS-Q concrete strategy semantics still require explicit approval before implementation.

PAQS-Q work may proceed after PAQS-E MVP milestones without blocking PAQS-E.

Expanded external-data robustness work remains part of PAQS-Q semantic acceptance rather than PAQS-E runtime authority.

---

## 10. Revised implementation order

Recommended committed sequence after migration approval:

```text
PAQS-DUAL-001 docs migration
        ↓
TASK-006B2
Snapshot-on-Demand Current Market Snapshot
        ↓
TASK-007A
Doctrine Runtime + Structured Output + OpenAI Provider Port
        ↓
TASK-007B
On-Demand Analysis + Immutable Decision Ledger
        ↓
TASK-007C
PAQS-E Dashboard / Analyze workflow
        ↓
usable PAQS-E current-analysis MVP
        ↓
TASK-006B1
Local Market Data Store + Replay Foundation
        ↓
PAQS-E historical As-Of / Gold-Set validation expansion

PAQS-Q 006B-Q / 006C-Q / 006D-Q / 006E-Q
may then progress as a separate engineering/reference stream
without redefining PAQS-E.

TASK-007D dual comparison
only after PAQS-Q is usable.
```

This order prioritizes visible PAQS-E product value while preserving strict factual/as-of boundaries.

---

## 11. Snapshot-on-Demand governance

Authoritative docs should explicitly state:

```text
strategy analysis is not real-time background execution
```

One Analyze request:

```text
freezes one snapshot
returns one result
optionally persists one immutable decision
ends
```

A new quote or newly completed bar does not modify that result.

A new explicit Analyze request is required to obtain an updated PAQS-E/PAQS-Q judgment in the MVP.

This does not prohibit ordinary market-data Dashboard refresh.

---

## 12. OpenAI-first boundary

Roadmap should authorize only the architecture direction, not an API call by itself.

When TASK-007A is later explicitly approved, initial provider scope should be:

```text
provider abstraction exists
OpenAI adapter implemented
one configurable OpenAI model id
no other provider adapter required
no multi-model voting
```

The strategy doctrine must remain provider-independent.

API keys/secrets are never committed.

---

## 13. Requirements Matrix changes proposed

Add/update requirements approximately as follows.

### Shared

```text
PAQS-013  Dual PAQS-E / PAQS-Q parallel strategy architecture
PAQS-014  Snapshot-on-Demand user-triggered strategy execution
PAQS-015  Shared immutable Point-in-Time Market Snapshot contract
PAQS-016  Latest quote is reference-only and cannot confirm completed-bar structure
PAQS-017  PAQS branches remain runtime-independent; one may fail without disabling the other
```

### PAQS-E

```text
PAQSE-001 Naked Price Action Doctrine is primary semantic strategy authority candidate
PAQSE-002 v0.3.x is formalization/guardrail/audit reference, not full runtime state machine
PAQSE-003 LLM provider port is provider-agnostic; OpenAI is first adapter only
PAQSE-004 Model receives product-controlled snapshot only; no web/tools in first MVP
PAQSE-005 Ordinary Analyze calls are stateless/fresh by default
PAQSE-006 Structured schema-constrained output
PAQSE-007 Deterministic schema/fact/RR post-validation
PAQSE-008 Immutable decision revisions with snapshot/doctrine/prompt/provider/model metadata
PAQSE-009 Entry advisory and holder advisory remain separate
PAQSE-010 NO_TRADE/WATCH/WAIT_RETEST/UNCERTAIN are valid outputs
```

### PAQS-Q

```text
PAQSQ-001 PAQS-Q is deterministic machine/reference/scanner branch
PAQSQ-002 PAQS-Q strategy thresholds do not silently bind PAQS-E
PAQSQ-003 PAQS-Q methods may evolve under separate research/task governance
```

### Permanent safety

Existing no-broker/no-write/no-autonomy requirements remain unchanged.

---

## 14. Authoritative docs-only migration files

If the user approves this migration proposal, Product Management should prepare a docs-only authoritative migration commit on a dedicated migration branch from exact authoritative HEAD.

Expected changed files:

```text
docs/ROADMAP.md
docs/REQUIREMENTS_MATRIX.md
docs/decisions/PAQS_DUAL_BRANCH_ARCHITECTURE.md
```

Optionally update a high-level architecture/strategy index only if needed to prevent contradictory authority.

Do not modify product code in the migration task.

Do not create TASK-006B2/007A implementation authority in the same commit.

After integration of the docs migration, discuss and create the first bounded implementation Task Contract separately.

---

## 15. Historical preservation

The migration must preserve:

```text
TASK-006A accepted evidence
TASK-006B deterministic implementation PASS
TASK-006B remediation evidence
TASK-006B real-market STRUCTURE_CONCERNS_FOUND checkpoint
v0.3.x research history
v0.4 Lite research history
Phase 1 immutable evidence
```

No historical file needs to be rewritten simply to match the new naming.

---

## 16. Explicit non-goals of the migration

The migration does not itself authorize:

```text
OpenAI API calls
new database migration
Market Data Store implementation
Snapshot implementation
PAQS-E implementation
PAQS-Q remediation
Dashboard changes
historical backtest
model voting/ensemble
broker integration
real trading
autonomous/background strategy execution
```

---

## 17. Approval boundary

If approved, the user is approving only:

```text
PAQS-DUAL-001 product/task migration direction
and the authoritative docs-only Roadmap/Requirements migration
```

The user is **not** simultaneously approving TASK-006B2, TASK-007A or any code implementation.

Each implementation task still requires its own explicit Task Contract approval under existing governance.

**End — PAQS Dual-Branch Roadmap Migration Proposal**