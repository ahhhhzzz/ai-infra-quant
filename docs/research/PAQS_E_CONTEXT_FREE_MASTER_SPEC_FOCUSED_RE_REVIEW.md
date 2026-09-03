# PAQS-E Context-Free Master Spec — Focused Re-Review

**Status:** FOCUSED STRATEGY RE-REVIEW — PASS  
**Reviewed branch:** `research/paqs-e-context-free-master-spec-zh`  
**Reviewed HEAD:** `18a69c1988124b2938682a25a2daddc669a1dcd0`  
**Reviewed master spec:** `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md`  
**Baseline originally reviewed:** `64f522f041f430470770c7b90dae0a84746fec65`  
**Prior review:** `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_STRATEGY_REVIEW.md` @ `9f644326f643d9497d6cd05c0ba3006fbe5bb125`  
**Remediation summary:** `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_REMEDIATION_SUMMARY.md`  
**Implementation authority:** NONE. This PASS accepts strategy/runtime semantics; it does not authorize TASK-006B2, TASK-007A, OpenAI integration, Codex, Roadmap changes, or product-code changes.

---

## 1. Verdict

**PASS — suitable to serve as the PAQS-E runtime semantic authority candidate.**

The focused re-review independently inspected the remediated Master Spec itself rather than relying on the remediation summary.

All prior blocking findings F-01 through F-07 are materially resolved in the Master Spec, and all non-blocking clarifications R-01 through R-05 were incorporated without weakening the Naked Price Action strategy core or converting PAQS-E into a deterministic PAQS-Q-style state machine.

The accepted strategy chain remains:

```text
CONTEXT
→ STRUCTURE
→ KEY LEVEL
→ LOCATION
→ EVENT
→ TRANSITION
→ SETUP
→ TRIGGER
→ FOLLOW-THROUGH
→ STRUCTURAL INVALIDATION
→ STRUCTURAL TARGET
→ RR / ENTRY QUALITY
→ ENTRY ADVISORY + HOLDER ADVISORY
```

The accepted initial Setup families remain:

```text
A. Trend Pullback Continuation / 顺大逆小
B. Range / key-support Failed-Break Reversal
C. Right-Side Structural Breakout
```

---

## 2. Blocking findings resolution verification

### F-01 — Current vs historical adjustment semantics

**PASS.**

The Master Spec now explicitly requires:

```text
analysis_mode = CURRENT_ANALYSIS | HISTORICAL_ASOF_REPLAY
```

and correctly permits disclosed, internally consistent current-adjusted data for current analysis while failing closed for strict historical replay when point-in-time-safe adjustment semantics cannot be established.

`historical_replay_safe = false` is no longer treated as an automatic current-analysis failure.

### F-02 — Partial-data degradation policy

**PASS.**

The Master Spec contains an explicit degradation matrix for W1, D1, M30, current price/quote, calendar/session metadata, adjustment warnings and cross-timeframe adjustment inconsistency.

It distinguishes:

```text
DATA_UNAVAILABLE
UNCERTAIN
WATCH_LONG / WATCH_SHORT
ENTRY_PENDING_REVALIDATION
NO_TRADE
```

by semantic cause rather than treating all PARTIAL data as one condition.

### F-03 — Current price vs executable entry reference

**PASS.**

The Master Spec now separates:

```text
CURRENT_PRICE_REFERENCE
EXECUTABLE_ENTRY_REFERENCE
```

and requires session/freshness/runtime-policy validity before an entry reference may support final RR and `LONG_READY`.

A structurally valid setup without a legitimate executable reference is correctly degraded to `ENTRY_PENDING_REVALIDATION` / pending RR.

### F-04 — Semantic zone vs numeric calculation reference

**PASS.**

Invalidation and target semantics now preserve both:

```text
semantic level_or_zone
calculation_reference
```

The calculation reference must be related to the semantic geometry, frozen before RR validation, persisted with the decision and not moved to manufacture better RR.

If a defensible numeric reference is unavailable:

```text
rr_status = NOT_COMPUTABLE
```

and actionable ready states are prohibited.

### F-05 — Holder Advisory basis

**PASS.**

Fresh/stateless analysis defaults to:

```text
holder_advisory_basis = CURRENT_ANALYSIS_THESIS
```

and explicitly does not claim knowledge of the user's unknown actual historical thesis.

`PRIOR_DECISION_ID` is reserved for an explicit future mode where an immutable prior decision is supplied.

### F-06 — Strategy portability vs Runtime-approved scope

**PASS.**

The Master Spec explicitly separates strategy portability from runtime authority and requires externally supplied versioned Runtime Configuration for market/instrument scope, timeframe roles, short execution, extended-hours entry references, freshness and optional guardrails.

The model is forbidden from changing timeframe mapping or permissions after inspecting the chart.

### F-07 — Canonical output vocabulary

**PASS at semantic-spec level.**

The Master Spec now separates machine concepts into canonical fields including:

```text
support_status
input_quality
market_bias
avoid_long_flag
entry_advisory
holder_advisory_basis
holder_advisory
rr_status
```

and removes the earlier slash aliases / duplicate advisory names.

Final provider-facing JSON Schema enum details remain a TASK-007A contract concern rather than a reason to reject the strategy semantics.

---

## 3. Non-blocking clarification verification

### R-01 — Location / Target sequencing

**PASS.** Location now evaluates structure/key-level/visible-obstacle position before formal T1 selection; final Entry Quality is allowed to change after Target/RR geometry is known.

### R-02 — Reproducibility wording

**PASS.** The spec now describes PAQS-E as auditable/comparable/version-controlled and suitable for repeated-run stability evaluation rather than implying bit-for-bit deterministic LLM output.

### R-03 — Participant-intent narratives

**PASS.** Hidden participant intent is explicitly framed as uncertain interpretation rather than observable fact, with preference for direct price-action language.

### R-04 — User-provided charts

**PASS.** Standalone/manual reasoning is separated from Product Runtime; authoritative Product Runtime facts must come from the product-controlled immutable Market Snapshot, and any future chart supplied to the model must be generated from the same snapshot/cutoff.

### R-05 — SETUP_EXPIRED

**PASS.** The model is forbidden from inventing a universal hidden N-bar expiry. Expiration is tied to price extension/opportunity missed, geometry replacement, structural invalidation, or explicit versioned runtime configuration.

---

## 4. Two downstream schema notes — not strategy blockers

These items should be resolved in TASK-007A rather than sent back for another strategy rewrite.

### S-01 — Trigger / Follow-through exact enums

The semantic states are clear, but the final OpenAI Structured Output schema should assign one exact canonical enum set to `trigger_status` and `followthrough_status` rather than leaving any placeholder or prose-form alternatives.

This is a serialization/schema concern, not a remaining ambiguity in the trading doctrine.

### S-02 — Short-side advisory permission

The current recommended v1 sets `short_execution_allowed = false`. TASK-007A should decide one exact machine contract for bearish observations:

- either prohibit `WATCH_SHORT` entirely in v1 and express bearish evidence through `market_bias` + `avoid_long_flag`, or
- add an explicit non-execution `short_advisory_allowed` / research permission distinct from execution permission.

The model must not infer this permission itself.

This is a runtime-schema authorization detail, not a reason to reopen the three core Setup semantics.

---

## 5. Authority recommendation

Recommended project interpretation after this PASS:

```text
PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md
    = PAQS-E primary runtime semantic authority candidate

PAQS_E_NAKED_PRICE_ACTION_DOCTRINE.md
    = conceptual/doctrine foundation

PAQS v0.3.x research
    = guardrail / formalization / audit / terminology reference

PAQS-Q research
    = separate deterministic machine/reference branch
```

The Master Spec still does not itself authorize implementation.

Before TASK-007A, Product Management should make the above authority hierarchy explicit in authoritative product documentation and adopt the exact reviewed Master Spec commit/descendant intended for runtime packaging.

---

## 6. TASK-006B2 impact

This PASS does not require abandoning the already approved TASK-006B2 snapshot architecture.

The shared snapshot should continue to provide product-controlled factual inputs and should not inject legacy PAQS-Q Pivot/Zone/Range/Regime conclusions into PAQS-E.

Before starting Codex on TASK-006B2, Product Management should perform a narrow contract compatibility check for these Master-Spec requirements:

```text
analysis/current adjustment provenance
per-timeframe quality/coverage sufficient for degradation policy
quote timestamp / market state / delay/freshness provenance needed later to derive executable-entry eligibility
snapshot identity / As-Of discipline
```

If the existing TASK-006B2 Contract already carries those facts, no amendment is required. If it omits a factual field needed by the Master Spec, amend only that factual contract boundary; do not add PAQS-E strategy logic to TASK-006B2.

---

## 7. Final status

```text
FOCUSED_RE_REVIEW = PASS
RUNTIME_SEMANTIC_AUTHORITY_CANDIDATE = ACCEPTED
IMPLEMENTATION_AUTHORITY = NONE
TASK-006B2 = STILL PAUSED PENDING CONTRACT-COMPATIBILITY CHECK
TASK-007A = NOT AUTHORIZED
```

**End — PAQS-E Context-Free Master Spec Focused Re-Review**