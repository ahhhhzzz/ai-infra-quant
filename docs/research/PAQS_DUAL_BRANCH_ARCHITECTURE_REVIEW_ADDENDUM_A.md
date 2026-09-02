# PAQS Dual-Branch Product Architecture Review — Addendum A

**Status:** PRODUCT / ARCHITECTURE REVIEW ADDENDUM — RESEARCH ONLY; IMPLEMENTATION NOT AUTHORIZED  
**Repository:** `ahhhhzzz/ai-infra-quant`  
**Research branch:** `research/006b-structure-stability`  
**Authoritative product HEAD at drafting:** `96747041ef0ff8c00937c5dd5e80cb4c5c28c17c`

Parent review:

- `docs/research/PAQS_DUAL_BRANCH_PRODUCT_ARCHITECTURE_REVIEW.md`

New PAQS-E strategy authority candidate:

- `docs/research/PAQS_E_NAKED_PRICE_ACTION_DOCTRINE.md`

This addendum corrects and refines the parent architecture review after adoption of the Naked Price Action Doctrine as the preferred PAQS-E strategy-brain candidate and after the product owner clarified the intended runtime model.

It does not modify authoritative Roadmap/Requirements, authorize Codex, approve an OpenAI integration, or approve any implementation Task Contract.

---

## 1. PAQS-E strategy authority correction

The parent review stated that PAQS v0.3.x should serve as the semantic foundation for PAQS-E. That framing is now too mechanical.

Preferred authority hierarchy for PAQS-E is:

```text
PAQS_E_NAKED_PRICE_ACTION_DOCTRINE.md
    -> primary semantic strategy doctrine candidate

PAQS v0.3.x research/formalization
    -> hard-guardrail / audit / terminology / anti-cheating reference

PAQS-Q v0.4 Lite research
    -> separate deterministic machine branch
```

PAQS-E must not recreate the full v0.3 deterministic Pivot/Zone/Range machinery merely because those semantics were previously formalized for code.

The PAQS-E doctrine preserves semantic reasoning such as:

```text
context
structure
location
event
setup
trigger
follow-through
invalidation
target
RR / entry quality
advisory
```

while retaining v0.3-style discipline such as:

```text
strict As-Of
no lookahead
Event != Setup != Advisory
Break Attempt != automatically Breakout
Trigger != Follow-through
Entry != Holder
no retroactive invalidation widening
no target shopping
NO_TRADE is valid
immutable historical decisions
```

Exact deterministic PAQS-Q thresholds are not automatically binding on PAQS-E.

---

## 2. Runtime model: Snapshot-on-Demand, not real-time signal generation

Both PAQS-E and PAQS-Q are user-triggered decision-support engines for the current MVP.

Canonical runtime:

```text
user selects a Security
        -> user requests Analyze
        -> product freezes one immutable Market Snapshot
        -> PAQS-E and/or PAQS-Q analyze that exact snapshot
        -> results are returned and optionally persisted
        -> run ends
```

The product does not continuously regenerate advisories merely because quotes or bars update.

A later user request creates a new snapshot and a new decision revision.

Therefore:

```text
Decision(snapshot A) remains immutable
Market moves
User requests Analyze again
Decision(snapshot B) is a new decision
```

This operating model applies to both branches and is independent of whether the underlying market-data page continues its existing lightweight refresh behavior.

Market-data display refresh is not strategy re-analysis.

---

## 3. Current-snapshot evidence boundary

PAQS-E and PAQS-Q confirmation semantics must use completed factual evidence only.

Authoritative structural inputs for the initial current analysis are:

```text
completed W1
completed D1
completed M30 REGULAR-session bars
```

An incomplete current M30 bucket must not confirm:

```text
Pivot
Breakout
Trigger
Follow-through
Setup
```

The latest quote may be supplied separately as:

```text
current_price_reference
quote_timestamp
reference_only = true
```

Its permitted purpose is current entry/location context, for example detecting that price has already moved far from a structurally reasonable entry area.

It must never be silently promoted into completed-bar structural evidence.

For the first PAQS-E MVP, an incomplete current candle should preferably be excluded entirely rather than shown ambiguously to the model.

---

## 4. PAQS-E input isolation

The initial PAQS-E runtime should be deliberately narrow and tool-less.

A PAQS-E model call receives only product-controlled inputs associated with one immutable snapshot and the approved runtime doctrine/prompt package.

Initial call must not provide:

```text
web search
browser tools
news retrieval
analyst targets
social-media sentiment
broker account data
real positions/orders/cash
uncontrolled external chart URLs
future bars
prior PAQS-E decisions as hidden context
prior conversational memory
```

The model must not choose its own data source or historical cutoff.

This is required to make PAQS-E a Naked Price Action engine rather than a generic investment chatbot.

---

## 5. Stateless reasoning by default

Every ordinary PAQS-E Analyze action is a fresh reasoning run:

```text
current doctrine version
+ current prompt version
+ current immutable snapshot
+ structured output schema
```

Prior PAQS-E conclusions are not automatically fed back into the next model call.

Reason: hidden prior decisions create anchoring and make historical evaluation harder to interpret.

A future explicit feature such as `Compare with previous decision` may supply a prior decision as a clearly labelled input, but that is not part of the first runtime contract.

---

## 6. PAQS-E priority relative to PAQS-Q

The dual-branch architecture remains accepted for migration planning, but implementation priority changes.

Current product priority:

```text
1. PAQS-E usable on-demand expert analysis
2. shared factual/snapshot discipline
3. PAQS-E immutable auditability and evaluation
4. PAQS-Q engineering/stabilization as scanner/reference branch
```

PAQS-Q remains valuable for:

```text
machine baseline
repeatable reference
future large-universe scanning
robustness comparison
quantitative evidence
```

but PAQS-Q semantic stabilization must not block an otherwise safe PAQS-E MVP.

PAQS-Q may change methods later without redefining PAQS-E doctrine.

---

## 7. OpenAI-first, provider-agnostic architecture

The first implemented PAQS-E provider may be OpenAI only.

This is an implementation-scope simplification, not vendor lock-in.

Core contract remains conceptually:

```text
PaqsEReasoningProvider
    analyze(request) -> PaqsEProviderResult
```

First adapter:

```text
OpenAIReasoningProvider
```

Possible later adapters:

```text
AnthropicReasoningProvider
GoogleReasoningProvider
other providers
```

Provider-specific request/response types must stay inside `integrations/` or an equivalent infrastructure boundary.

PAQS-E core/domain must not import an OpenAI SDK type.

The model identifier is configuration, not strategy semantics.

API credentials must remain server-side/local configuration, never committed to GitHub, persisted in ordinary product data, or exposed to frontend JavaScript.

---

## 8. Doctrine runtime packaging

PAQS-E must not send the entire research history verbatim on every model call.

A versioned runtime package should be derived from the strategy authority and include at minimum:

```text
strategy_doctrine_version
compact core doctrine
canonical reasoning questions
hard guardrails
output-field semantics
forbidden behaviors
```

The runtime prompt must preserve the intent of `PAQS_E_NAKED_PRICE_ACTION_DOCTRINE.md`, especially its canonical compact doctrine and reasoning-question sequence.

The runtime package is an auditable artifact with its own version/hash.

A prompt change creates a new prompt version; it must not silently mutate historical meaning.

---

## 9. PAQS-E Market Snapshot philosophy

The shared snapshot must provide facts, not a pre-decided PAQS answer.

Preferred first PAQS-E snapshot inputs:

```text
snapshot_version
snapshot_hash
security_id
symbol
market
market_timezone
as_of_timestamp
calculated_at

completed W1 bars
completed D1 bars
completed M30 bars

latest quote as optional reference-only fact

session / calendar metadata
coverage / data-quality metadata
adjustment metadata
provider provenance

objective measurements where approved:
ATR14
optional EMA20 / EMA50
optional ROC20 / ROC60
optional volume-derived factual measurements
```

A snapshot must not require PAQS-Q Pivot/Zone/Range/Regime output in order for PAQS-E to reason.

PAQS-Q-derived facts may later be displayed as a separate branch output, not smuggled into PAQS-E as ground truth.

---

## 10. Deterministic chart rendering

A future/early PAQS-E implementation may send deterministic charts alongside structured snapshot facts because the doctrine relies on visual-semantic concepts such as:

```text
impulse vs correction
channel quality
widening structure
three-push / exhaustion
location
trend deterioration
```

Any chart supplied to a model must satisfy:

```text
chart derived only from snapshot data
chart cutoff == snapshot cutoff
chart identifies timeframe
chart rendering version recorded
chart cannot contain future bars
```

Uncontrolled screenshots from a live external charting site are not valid PAQS-E evidence.

If chart rendering is not ready in the first implementation increment, structured OHLC input may be used first; chart support is additive.

---

## 11. Structured output and post-validation boundary

PAQS-E must return schema-constrained structured output plus concise human explanation.

The logical output follows Doctrine Section 26 and includes at minimum:

```text
one_line_thesis
context
current_location
key_levels (small decision-relevant set)
price_action
setup
entry
invalidation
targets
risk_reward
holder_advisory
uncertainty
next_evidence_needed
reason_codes
explanation
```

Deterministic post-validation may:

```text
validate schema
reject non-finite/invalid numeric values
verify references/timeframes belong to the snapshot contract
recalculate RR
verify target/invalidation arithmetic direction
verify As-Of/snapshot identity
flag impossible out-of-contract claims
```

Post-validation must not replace strategy reasoning, for example by selecting a different structural invalidation solely because deterministic code prefers it.

---

## 12. Initial PAQS-E model behavior requirements

The initial model runtime must be explicitly instructed to:

```text
reason only from supplied snapshot facts/charts
follow the Naked Price Action Doctrine
identify only a small number of decision-relevant levels
state alternative interpretation
state conflicting evidence
allow UNCERTAIN / NO_SETUP / WATCH / WAIT_RETEST / NO_TRADE
separate setup validity from current entry quality
separate entry advisory from conditional holder advisory
never claim calibrated probability
never infer user holdings
never fabricate missing bars/facts
never rewrite historical decisions
```

The model should not be asked to predict every next bar.

---

## 13. Revised implementation sequencing

The parent review prioritized Local Market Data Store before strategy integration. For the newly clarified on-demand current-analysis MVP, that dependency is not absolute.

Existing TASK-006A already provides sufficient read-through current factual inputs to construct a bounded current snapshot.

Recommended PAQS-E-first sequence:

```text
Roadmap migration approval
        |
        v
TASK-006B2
Snapshot-on-Demand Current Market Snapshot Contract
        |
        v
TASK-007A
PAQS-E Doctrine Runtime + Structured Output + OpenAI Provider Port
        |
        v
TASK-007B
On-Demand PAQS-E Analysis Service + Immutable Decision Ledger
        |
        v
TASK-007C
PAQS-E User Dashboard / Analyze workflow
        |
        +-----------------------------+
        |                             |
        v                             v
TASK-006B1                       PAQS-Q engineering
Local Market Data Store         006B-Q / C-Q / D-Q / E-Q
+ Replay Foundation
        |
        v
PAQS-E historical As-Of / Gold-Set evaluation expansion
        |
        v
TASK-007D
Dual-Branch comparison/disagreement presentation when PAQS-Q is usable
```

TASK-006B1 remains important and approved only as a planned node, but it no longer blocks current on-demand PAQS-E MVP creation.

Before strict historical replay/evaluation at arbitrary past cutoffs, local or otherwise legitimate point-in-time replay data must exist.

---

## 14. Why Snapshot precedes the OpenAI adapter

The first API integration must not begin from:

```text
ticker -> LLM
```

It must begin from:

```text
ticker
-> product-owned immutable Snapshot
-> snapshot_hash
-> doctrine runtime request
-> OpenAI provider adapter
-> structured output
```

This makes model integration replaceable and protects no-lookahead/audit boundaries from the first real call.

---

## 15. First-provider scope

Initial implementation scope should support one provider and a configurable model identifier.

Required:

```text
provider = OPENAI
model_id = local/server-side configuration
```

Not required initially:

```text
provider UI selector
Anthropic implementation
Gemini implementation
multi-model voting
ensemble logic
automatic model benchmarking
continuous/background PAQS-E calls
```

Provider abstraction is designed now; additional adapters are implemented only when needed.

---

## 16. No background strategy automation

PAQS-E and PAQS-Q strategy runs are explicitly user-triggered in the MVP.

Do not introduce:

```text
per-minute strategy polling
automatic re-analysis on quote refresh
background LLM jobs
unattended advisory updates
```

The existing Dashboard may refresh market-data display independently.

Strategy results change only after a new explicit Analyze action or a future separately approved trigger mode.

---

## 17. Governance consequence

This addendum changes the proposed Roadmap migration plan but does not itself authorize that migration.

Any authoritative Roadmap update must explicitly adopt:

```text
PAQS-E Naked Price Action Doctrine as primary E strategy authority candidate
Snapshot-on-Demand runtime
PAQS-E priority
OpenAI-first/provider-agnostic design
stateless/tool-less first analysis mode
completed-bar structural evidence boundary
```

No implementation task may cite this addendum as sufficient authority without an explicit user-approved Task Contract.

**End — PAQS Dual-Branch Product Architecture Review Addendum A**