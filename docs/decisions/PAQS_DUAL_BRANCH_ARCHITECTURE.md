# PAQS-DUAL-001 — Dual-Branch PAQS Architecture

Status: **APPROVED — authoritative product/task migration direction**  
Approved: **2026-09-03**  
Product branch at approval: `roadmap/no-live-trading`  
Authoritative pre-migration HEAD: `96747041ef0ff8c00937c5dd5e80cb4c5c28c17c`

## Decision

PAQS becomes a dual-branch, local-first, single-user, read-only investment decision-support architecture:

```text
                         PAQS
                          |
              +-----------+-----------+
              |                       |
           PAQS-E                   PAQS-Q
   Expert Reasoning Engine    Quant Decision Engine
        LLM-native            deterministic/reference
```

PAQS-E is the prioritized current product branch. PAQS-Q remains a separate deterministic machine-quant reference/scanner branch whose methods may evolve under separate research and Task Contract governance.

Both branches consume product-controlled point-in-time market facts and use explicit user-triggered **Snapshot-on-Demand** analysis. Neither branch performs continuous/background strategy execution in the current MVP.

This decision supersedes the future assumption that `TASK-006C`, `TASK-006D`, and `TASK-006E` form one single PAQS strategy-engine path. Accepted historical implementation and review evidence is preserved.

## Runtime model

One analysis request is:

```text
user selects Security
    -> user explicitly requests Analyze
    -> product freezes one immutable current Market Snapshot
    -> PAQS-E and/or PAQS-Q analyze that exact snapshot
    -> one result is returned
    -> result may be persisted as an immutable decision revision
    -> run ends
```

Market-data Dashboard refresh remains separate from strategy analysis. A new quote or newly completed bar does not mutate a prior PAQS decision. A new explicit Analyze request is required to create a new decision.

Confirmed structural evidence uses completed data only:

```text
W1 = completed weekly bars
D1 = completed daily bars
M30 = completed regular-session 30-minute bars
```

A latest quote may be exposed separately as reference-only current-price context. It may not confirm completed-bar Pivot, Breakout, Trigger, Follow-through, Setup, or other structural facts.

## PAQS-E authority

The preferred PAQS-E strategy authority hierarchy is:

```text
docs/research/PAQS_E_NAKED_PRICE_ACTION_DOCTRINE.md
    -> primary semantic Naked Price Action doctrine

PAQS v0.3.x research/formalization
    -> historical guardrail / audit / terminology / anti-cheating reference

PAQS-Q v0.4 Lite research
    -> separate deterministic machine-branch research foundation
```

PAQS-E must preserve semantic reasoning over context, structure, location, event, setup, trigger, follow-through, invalidation, target, RR/entry quality, and advisory. PAQS-Q mechanical thresholds do not silently bind PAQS-E.

For the initial PAQS-E MVP:

- analysis is stateless/fresh by default;
- model input is limited to product-controlled snapshot facts and approved doctrine/prompt/schema;
- no web/browser/search tools are supplied to the model;
- no hidden prior PAQS-E decision or conversational memory is supplied;
- no broker account, real position/order/cash, or autonomous trading capability is introduced;
- architecture remains model-provider-agnostic;
- OpenAI is the first planned provider adapter only;
- no multi-model voting/ensemble is required initially.

## PAQS-Q authority

PAQS-Q is the deterministic machine/reference/scanner branch. It is optimized for reproducibility, no-lookahead, bounded machine structure, robustness, replayability, auditability, and later large-universe scanning.

The current PAQS v0.4 Lite work is research input for PAQS-Q, not a universal semantic replacement for PAQS-E. PAQS-Q strategy methods may change later through separately approved research and Task Contracts.

## Historical task disposition

Preserve:

- `TASK-003` through `TASK-005B` as accepted market-data/Dashboard/launcher history;
- `TASK-006A` as shared PAQS factual/input foundation;
- `TASK-006B` as accepted deterministic implementation evidence;
- `TASK-006B` real-market checkpoint result `STRUCTURE_CONCERNS_FOUND` as valid research evidence.

`TASK-006B` must not be rewritten as either a failure of deterministic implementation or a final semantic acceptance. Its correct historical status is:

```text
TASK-006B deterministic implementation: PASS / integrated
TASK-006B real-market semantic checkpoint: STRUCTURE_CONCERNS_FOUND
```

## Planned shared tasks

### TASK-006B2 — Snapshot-on-Demand Current Market Snapshot Contract

Planned next implementation task after this migration. Scope direction only; a separate explicit Task Contract is still required.

Purpose:

- immutable current analysis snapshot from accepted read-through facts;
- strict `as_of_timestamp`;
- canonical completed W1/D1/M30 payloads;
- optional latest quote marked reference-only;
- provider/session/calendar/coverage/quality/adjustment provenance;
- approved objective numerical facts;
- canonical serialization and `snapshot_hash`;
- no PAQS-E/PAQS-Q judgment;
- no LLM call;
- no persistence requirement.

### TASK-006B1 — Local Market Data Store & Replay Foundation

Retained as shared foundation, but no longer blocks the first current-analysis PAQS-E MVP. It becomes required before strict arbitrary historical As-Of replay/evaluation is claimed.

## Planned PAQS-E workstream

`TASK-007` is umbrella only and is never itself an implementation task.

Planned bounded tasks:

```text
TASK-007A — PAQS-E Doctrine Runtime, Structured Output & OpenAI Provider Port
TASK-007B — On-Demand PAQS-E Analysis Service & Immutable Decision Ledger
TASK-007C — PAQS-E User Dashboard
TASK-007D — Dual-Branch Comparison / Disagreement Dashboard (after PAQS-Q usable)
```

PAQS-E is prioritized over PAQS-Q stabilization for the current visible MVP.

## Planned PAQS-Q workstream

The previous future single-engine `TASK-006C/006D/006E` wording is superseded for future implementation. Planned machine-branch task names are:

```text
TASK-006B-Q — PAQS-Q Structure Stabilization
TASK-006C-Q — PAQS-Q Event Engine
TASK-006D-Q — PAQS-Q Setup, Risk & Setup-Specific Quant Confirmation
TASK-006E-Q — PAQS-Q Advisory / Scanner Presentation
```

Each still requires separate research approval and Task Contract authority.

## Recommended implementation order

```text
PAQS-DUAL-001 docs migration
    -> TASK-006B2 Snapshot-on-Demand Current Market Snapshot
    -> TASK-007A Doctrine Runtime + Structured Output + OpenAI Provider Port
    -> TASK-007B On-Demand Analysis + Immutable Decision Ledger
    -> TASK-007C PAQS-E Dashboard / Analyze workflow
    -> usable PAQS-E current-analysis MVP
    -> TASK-006B1 Local Market Data Store + Replay Foundation
    -> PAQS-E historical As-Of / Gold-Set evaluation expansion

PAQS-Q tasks proceed as a separate engineering/reference stream and do not redefine PAQS-E.
```

## Permanent boundaries

This decision does not change the permanent product boundary:

- no brokerage-account connection or observation;
- no real cash/positions/orders/trades;
- no broker-write APIs or UI;
- no `place_order`, `cancel_order`, `modify_order`, or trade-password unlock;
- no autonomous/unattended trading;
- all real trading remains manual in the broker's official client.

## Research evidence

The approved migration was developed from research branch `research/006b-structure-stability`, including research HEAD `01000900861d4506fb35fbf423901a5b9a306499` and the following documents:

- `docs/research/PAQS_DUAL_BRANCH_PRODUCT_ARCHITECTURE_MEMO.md`
- `docs/research/PAQS_DUAL_BRANCH_PRODUCT_ARCHITECTURE_REVIEW.md`
- `docs/research/PAQS_DUAL_BRANCH_ARCHITECTURE_REVIEW_ADDENDUM_A.md`
- `docs/research/PAQS_DUAL_BRANCH_ROADMAP_MIGRATION_PROPOSAL.md`
- `docs/research/PAQS_E_NAKED_PRICE_ACTION_DOCTRINE.md`
- `docs/research/PAQS_V0.4_LITE_STRUCTURE_QUANT_AMENDMENT.md`
- `docs/research/TASK_006B_STRUCTURE_STABILITY_REVIEW.md`

Those research documents remain research evidence. This decision record, Roadmap, and Requirements Matrix provide authoritative product/task direction.

## Governance

This decision authorizes only the docs-only Roadmap/Requirements migration. It does **not** itself authorize implementation of `TASK-006B2`, `TASK-007A`, OpenAI API calls, database migrations, Dashboard changes, PAQS-Q remediation, or any other code.

Every implementation task still requires:

```text
bounded task proposal
-> explicit user approval
-> Task Contract on dedicated task branch
-> short Codex prompt referencing exact branch/contract/base SHA
-> implementation push
-> independent review of exact HEAD
-> focused remediation if needed
-> non-force integration after verification
```
