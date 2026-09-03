# PAQS-E Context-Free Master Spec — Strategy Review

**Status:** STRATEGY REVIEW — NEEDS REVISION BEFORE RUNTIME AUTHORITY  
**Reviewed branch:** `research/paqs-e-context-free-master-spec-zh`  
**Reviewed file:** `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md`  
**Reviewed commit:** `64f522f041f430470770c7b90dae0a84746fec65`  
**Review scope:** strategy semantics, LLM executability, runtime ambiguity, data/entry/RR boundaries, output consistency.  
**Implementation authority:** NONE. This review does not authorize TASK-006B2, TASK-007A, Codex, OpenAI integration, Roadmap changes or product-code changes.

---

## 1. Verdict

**NEEDS REVISION — the core strategy is accepted; several runtime semantics must be made unambiguous before the file becomes the PAQS-E runtime authority.**

The review does **not** reject the PAQS-E strategy direction.

The following core elements are strong and should remain substantially unchanged:

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

The three core Setup families are also accepted as the initial PAQS-E strategy set:

```text
A. Trend Pullback Continuation / 顺大逆小
B. Failed-Break Reversal at a meaningful range/support boundary
C. Right-Side Structural Breakout
```

The strongest parts of the specification are:

- multi-timeframe hierarchy rather than voting;
- semantic Key-Level selection limited to 1–4 decision-relevant areas;
- Event != Setup != Advisory;
- Break Attempt != accepted Breakout;
- Trigger and Follow-through separation;
- right-side confirmation over blind bottom/top guessing;
- structural invalidation rather than percentage-stop storytelling;
- nearest meaningful T1 / no target shopping;
- actual-entry revalidation and anti-FOMO discipline;
- separate Entry and Holder questions;
- NO_TRADE / WATCH / WAIT_RETEST / UNCERTAIN as legitimate outputs;
- immutable historical decisions and strict As-Of discipline;
- PAQS-E semantic reasoning isolated from PAQS-Q mechanical thresholds.

The remaining findings are mainly contract ambiguities that could cause two otherwise capable LLMs to interpret the same market snapshot differently for avoidable reasons.

---

# 2. Blocking findings — revise before runtime authority

## F-01 — Current analysis and historical replay adjustment semantics are conflated

**Severity:** HIGH  
**Area:** Section 3.4, DATA CHECK, historical evaluation

Current wording requires all timeframes to use a consistent, Point-in-Time-safe adjustment/corporate-action basis and says that if consistency cannot be confirmed the result should be `DATA_UNAVAILABLE` or `UNSUPPORTED`.

That is correct for **strict historical replay**, but it is too strong for the product's initial **current Snapshot-on-Demand analysis**.

The current product can legitimately analyze today's market using a provider's consistently current-adjusted historical bars while still truthfully declaring:

```text
adjustment_basis = PROVIDER_QFQ_CURRENT
historical_replay_safe = false
```

For a current-time analysis, this does not imply that the model has seen future information relative to the current analysis time. It only means the same data cannot later be claimed to reconstruct what was visible at an older historical date.

### Required clarification

The Master Spec should distinguish at least:

```text
CURRENT_ANALYSIS
    current-consistent adjustment basis may be used
    if explicitly disclosed and internally consistent

HISTORICAL_ASOF_REPLAY
    requires point-in-time-safe adjustment/corporate-action semantics
    or the replay claim must fail conservatively
```

Recommended rule:

> Current PAQS-E analysis may use a disclosed current-adjusted basis when all supplied timeframes are internally consistent. `historical_replay_safe=false` is a provenance limitation, not by itself a reason to reject the current analysis. Strict historical As-Of evaluation must not use such data as if it were point-in-time-safe.

Without this distinction, a literal runtime implementation could incorrectly reject the entire first PAQS-E current-analysis MVP.

---

## F-02 — Partial-data degradation policy is underspecified

**Severity:** HIGH  
**Area:** Sections 3, 10, 11, 12

The spec correctly requires a DATA CHECK, but it does not define how different missing/partial inputs affect different layers of the analysis.

`PARTIAL` is not one condition. Examples have materially different consequences:

```text
W1 missing / invalid
D1 missing / invalid
M30 incomplete coverage
latest quote unavailable
calendar metadata partial
adjustment provenance warning
```

A model needs deterministic gating for what it may still conclude.

### Required degradation matrix

At minimum define behavior equivalent to:

```text
W1 not trustworthy
    -> no fully qualified HTF context
    -> actionable LONG_READY prohibited
    -> output DATA_UNAVAILABLE or UNCERTAIN depending on cause

D1 not trustworthy
    -> no valid Setup / Key-Level decision layer
    -> actionable Entry Advisory prohibited

M30 not trustworthy / materially incomplete
    -> HTF/STF context and levels may still be reported
    -> Trigger / Follow-through cannot be confirmed
    -> LONG_READY prohibited
    -> WATCH / UNCERTAIN / DATA_UNAVAILABLE as appropriate

latest quote unavailable or not executable
    -> structural analysis may remain valid
    -> current-entry RR cannot be final
    -> use ENTRY_PENDING_REVALIDATION when Setup is otherwise confirmed
```

The exact product enums may differ, but the semantic gating must be fixed before the model is asked to choose between `DATA_UNAVAILABLE`, `UNCERTAIN`, `WATCH_LONG`, `ENTRY_PENDING_REVALIDATION` and `NO_TRADE`.

Otherwise model behavior will drift mainly because of missing-data interpretation rather than Price Action reasoning.

---

## F-03 — “Executable Entry Reference” is not yet defined tightly enough

**Severity:** HIGH  
**Area:** Section 8.4, advisory states, Snapshot-on-Demand runtime

The spec correctly distinguishes:

```text
Setup Confirmation Price
vs
Executable Entry Reference
```

However, “current latest quote” is not always an executable entry reference.

Examples:

- market is closed;
- quote is stale;
- quote is pre-market or after-hours while the strategy intends regular-session execution;
- provider quote is delayed;
- quote is available but the user has not requested/approved extended-hours interpretation.

### Required semantics

The runtime contract should distinguish, conceptually:

```text
CURRENT_PRICE_REFERENCE
    factual/latest observed price
    may be reference_only

EXECUTABLE_ENTRY_REFERENCE
    a price reference permitted by the declared execution/session policy
    sufficiently fresh for entry-quality/RR revalidation
```

If the Setup is structurally confirmed but an executable entry reference is not legitimately available:

```text
entry_advisory = ENTRY_PENDING_REVALIDATION
```

rather than `LONG_READY`.

`LONG_READY` should require both a valid structural Setup and a valid current entry-reference context under the configured market/session policy.

This clarification is important because the product is explicitly Snapshot-on-Demand rather than continuously executing trades.

---

## F-04 — Structural zones need explicit numeric calculation references for deterministic RR

**Severity:** HIGH  
**Area:** Sections 5, 8, 11

The spec correctly says Key Levels, invalidations and targets may be **zones**, and that false decimal precision should not be invented.

But deterministic RR requires numeric inputs:

```text
Entry
Invalidation
T1
```

A semantic output such as:

```text
invalidation zone = 194–196
target zone = 217–220
```

is not sufficient for a deterministic calculator unless the model or product also provides the exact calculation references.

### Required schema distinction

For actionable analyses, distinguish semantic geometry from calculation references, e.g.:

```text
invalidation:
    level_or_zone
    calculation_reference
    condition
    timeframe
    reason

targets:
    t1_level_or_zone
    t1_calculation_reference
    t1_reason
```

The calculation reference must be:

- inside or explicitly related to the selected semantic zone;
- chosen before RR is validated;
- preserved with the decision;
- not silently moved to improve RR.

If no defensible numeric calculation reference exists, RR should be marked not-final/not-computable and the result should not become `LONG_READY`.

This preserves semantic zones without sacrificing deterministic mathematics.

---

## F-05 — Holder Advisory scope is ambiguous without a prior thesis

**Severity:** HIGH-MEDIUM  
**Area:** Section 9.2, immutable decisions

The specification says PAQS-E can answer:

> If already held, is the Thesis still structurally valid?

But a fresh/stateless PAQS-E call does not know why an actual user entered a position unless a prior decision/thesis is explicitly supplied.

A person may hold the same stock from:

- a Trend Pullback setup weeks earlier;
- a Failed Breakdown reversal;
- a completely unrelated manual thesis;
- a price far below/above the current candidate setup.

Therefore a fresh current snapshot cannot truthfully evaluate the user's **actual historical thesis**.

### Required distinction

For the initial stateless runtime, Holder Advisory should mean:

> **Conditional holder advisory for the current PAQS-E thesis identified in this analysis**, not a claim about the user's unknown real position thesis.

Recommended contract wording:

```text
holder_advisory_basis = CURRENT_ANALYSIS_THESIS
```

A future explicit “manage/review prior PAQS-E decision” mode may instead supply a prior immutable decision and evaluate:

```text
holder_advisory_basis = PRIOR_DECISION_ID
```

Hidden prior conversational memory must not be used.

This distinction prevents the model from giving apparently personalized hold/exit advice based on a thesis it never observed.

---

## F-06 — Runtime configuration authority must be explicit; the model must not self-select scope

**Severity:** HIGH-MEDIUM  
**Area:** Sections 3.1, applicability, short-side mirror logic

The Master Spec is intentionally portable across A/H/US stocks and liquid ETFs and allows a different timeframe mapping when instrument characteristics require it.

That portability is useful at the strategy-spec level, but the **runtime model must not choose these settings after seeing the chart**.

For product v1, configuration should be explicit and external to the model, including at least:

```text
supported_market_scope
supported_instrument_scope
HTF/STF/TTF mapping
short_execution_allowed
extended_hours_entry_reference_allowed
optional versioned RR / ATR guardrails if any
```

For the current product, the first runtime is expected to remain:

```text
US/HK equities
HTF = W1
STF = D1
TTF = M30 REGULAR
short_execution_allowed = false unless separately approved
```

When executable shorting is disabled, the model may still identify bearish context and output an avoid-long warning, but must not emit an actionable short-entry state.

The Master Spec should therefore distinguish:

```text
strategy portability
vs
runtime-approved scope
```

and forbid the LLM from changing timeframe roles or short permissions because the resulting chart is easier to interpret.

---

## F-07 — Output state vocabulary contains aliases/inconsistencies that will break a strict schema

**Severity:** MEDIUM-HIGH  
**Area:** Sections 3.4, 7.2, 9, 11

Several output terms are semantically close but not canonicalized:

Examples:

```text
DATA_UNAVAILABLE
UNSUPPORTED

POOR_ENTRY
VALID_SETUP_BUT_POOR_ENTRY

SHORT_BIAS / AVOID_LONG
WATCH_SHORT

OK / PARTIAL / UNAVAILABLE
vs product-level COMPLETE / PARTIAL / INVALID style quality semantics
```

A human can understand these, but a strict OpenAI Structured Output schema cannot safely treat slash-separated or alias states as one enum.

### Required cleanup

Before TASK-007A, define one canonical enum vocabulary and separate fields where concepts differ.

Example principle:

```text
entry_advisory = one exact state
bearish_context / avoid_long = separate evidence or advisory flag
support_status = supported / unsupported
input_quality = complete / partial / invalid
```

The exact names can be chosen later, but every semantically distinct state should have one canonical machine-readable representation.

This is not a cosmetic issue: exact enums are necessary for ledger comparison, Gold-Set evaluation and cross-model consistency.

---

# 3. Important non-blocking revisions

## R-01 — Location Quality currently depends on T1 before T1 is formally selected

Section 5.3 defines `GOOD` partly by having sufficient room to T1, while the formal algorithm does not select Targets until later.

This creates a small sequencing circularity.

Recommended fix:

```text
LOCATION
    evaluate relation to current structure and nearest visible obstacle

TARGETS / RR
    later formalize T1/T2

ENTRY QUALITY
    final judgment may upgrade/downgrade based on actual target/RR geometry
```

This preserves the conceptual chain without asking the model to know the formal T1 before target selection.

---

## R-02 — “可复现” should not imply deterministic LLM output

The document purpose says a context-free AI should analyze “快速、准确、可复现”.

PAQS-E itself is not deterministic in the PAQS-Q sense.

Recommended wording:

```text
可审计、可比较、受版本控制、可进行重复运行稳定性评估
```

rather than implying identical repeated model outputs.

The reproducible facts should be the Snapshot, doctrine/prompt version, model request configuration, validation and ledger identity.

---

## R-03 — Avoid asserting participant intent from price alone

Phrases such as:

```text
“吸筹式结构”
“是否形成被套盘逻辑”
```

can encourage the LLM to invent hidden participant narratives.

They are acceptable as hypotheses if framed carefully, but should not be treated as observed facts.

Recommended wording:

```text
“筑底/反复承接/压缩式价格结构”
“价格行为是否与失败突破参与者可能受困的情形一致”
```

and require explicit uncertainty if participant intent is not observable from the supplied snapshot.

---

## R-04 — User-supplied charts should not become authoritative product-runtime evidence by default

Section 16 mentions the user providing stocks, charts, OHLCV or Market Snapshots.

That is useful for a context-free standalone instruction document, but the product runtime currently intends a product-controlled immutable Snapshot.

Recommended distinction:

```text
Standalone/manual reasoning use
    may accept user-provided chart/OHLCV with disclosed limitations

Product runtime
    authoritative market facts come only from the product-controlled Snapshot
    any chart shown to the model must be deterministically rendered from the same snapshot/cutoff
```

This prevents unknown chart provenance or hidden future bars from bypassing the As-Of contract.

---

## R-05 — SETUP_EXPIRED should not create an invented hidden time window

`SETUP_EXPIRED` is useful, but the spec deliberately rejects one universal setup-expiry bar count.

Clarify that expiration may be concluded from:

- material price extension / opportunity already passed;
- invalidated setup geometry;
- a versioned configuration explicitly supplied to runtime;
- new structure replacing the old candidate.

The model must not invent an undisclosed “N bars” expiry threshold.

---

# 4. Accepted strategy semantics

The following strategy semantics pass this review and should not be diluted during remediation.

## 4.1 Context and timeframe hierarchy

Retain:

```text
HTF = context
STF = setup structure / location
TTF = trigger / follow-through
```

and preserve the rule that disagreement across timeframes requires interpretation rather than scoring/voting.

## 4.2 Key-Level discipline

Retain 1–4 current decision-relevant areas and require:

```text
price_or_zone
role
timeframe
rationale
what changes if broken/reclaimed
```

Do not return to a machine-generated universe of historical Pivot zones for PAQS-E.

## 4.3 Setup A / B / C

Retain the initial three-family restriction. It is a valuable anti-overfitting / anti-pattern-proliferation constraint for an LLM runtime.

A future new Setup family should require explicit strategy amendment rather than prompt drift.

## 4.4 Trigger / Follow-through separation

Retain. This is one of the strongest protections against the model upgrading an attractive-looking candle directly into an actionable trade.

## 4.5 Structural invalidation and target discipline

Retain:

- semantic selection of the boundary by PAQS-E;
- deterministic arithmetic validation downstream;
- no stop widening to rescue the thesis;
- nearest meaningful T1;
- no target shopping.

## 4.6 Entry revalidation and anti-FOMO

Retain. A correct setup can still produce:

```text
VALID_SETUP_BUT_POOR_ENTRY
WAIT_RETEST
```

when current price destroys entry geometry.

This is essential for Snapshot-on-Demand use.

## 4.7 Uncertainty and alternative interpretation

Retain mandatory conflicting evidence and strongest alternative interpretation. This is particularly important for LLM-native analysis because it counters persuasive single-story rationalization.

---

# 5. Relationship to TASK-006B2

This review does **not** require cancellation of the approved TASK-006B2 concept.

The current Snapshot direction remains compatible with the Master Spec:

```text
completed W1 / D1 / M30 factual bars
market/security identity
strict as_of
calendar/session
adjustment provenance
coverage / data quality
optional current quote marked reference_only
canonical hash
```

The shared Snapshot should continue to exclude strategy conclusions such as:

```text
Pivot
Zone
Range
Regime
Setup
Advisory
PAQS-Q score
```

However, before implementation resumes, Product Management should verify that the TASK-006B2 contract can express the distinctions required by F-01/F-02/F-03, especially:

- adjustment basis vs historical replay safety;
- quality/coverage detail sufficient for downstream degradation gates;
- quote status/market state/timestamps sufficient to distinguish current-price reference from executable-entry reference.

If the existing TASK-006B2 contract already contains these facts, no contract rewrite is needed. If not, a focused contract amendment should be made before Codex implementation starts.

---

# 6. Required remediation outcome

Before `PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md` becomes PAQS-E runtime authority, a revised version should resolve F-01 through F-07 without changing the accepted core Price Action strategy unless the product owner separately requests it.

After revision, perform a focused re-review for:

```text
1. current vs historical adjustment semantics
2. partial-data degradation matrix
3. executable-entry-reference rules
4. zone vs numeric RR references
5. conditional holder-advisory basis
6. runtime scope/config authority
7. canonical output enums
8. no new contradictions introduced
```

A clean re-review may then return:

```text
PASS — suitable as PAQS-E runtime semantic authority
```

Only after that should TASK-007A package the Master Spec into the OpenAI runtime prompt/output contract.

---

# 7. Current project stop state

Until the user resolves the strategy review:

```text
TASK-006B2 Task Contract
    prepared / approved
    implementation paused by user strategy-review request

PAQS-E Master Spec
    core strategy accepted
    runtime authority = NEEDS REVISION

TASK-007A
    not authorized

Codex
    do not start implementation from this review
```

**End — PAQS-E Context-Free Master Spec Strategy Review**