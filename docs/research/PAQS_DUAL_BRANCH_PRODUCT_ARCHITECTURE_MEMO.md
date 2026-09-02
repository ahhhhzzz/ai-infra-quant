# PAQS Dual-Branch Product Architecture Memo
## Strategy Expert → Product Manager

**Status:** RESEARCH / PRODUCT-ARCHITECTURE MEMO ONLY  
**Implementation authority:** NONE  
**Repository:** `ahhhhzzz/ai-infra-quant`  
**Target branch:** `research/006b-structure-stability`  
**Context:** this memo is written to communicate the strategy direction to the Product Manager ChatGPT. It must not be treated as a Task Contract, code authorization, Roadmap supersession, or approval to start Codex implementation.

---

# 1. Core product decision

PAQS v0.3.x and PAQS v0.4 Lite should no longer be interpreted as a single linear version chain where v0.4 automatically supersedes v0.3.

They have become two materially different strategy branches with different execution models, different strengths, and different validation criteria.

Recommended naming:

```text
PAQS-E
Expert Reasoning Engine
LLM-native Naked Price Action branch
based on PAQS v0.3 / v0.3.1 semantics

PAQS-Q
Quant Decision Engine
Deterministic machine-quant branch
based on PAQS v0.4 Lite direction
```

The relationship is parallel:

```text
                       PAQS
                        │
              ┌─────────┴─────────┐
              │                   │
           PAQS-E              PAQS-Q
      Expert Reasoning       Quant Machine
          Engine               Engine
              │                   │
            LLM              deterministic code
```

**Do not document `PAQS-Q / v0.4 Lite` as a full semantic replacement for `PAQS-E / v0.3.x`.**

---

# 2. Why the split is necessary

The v0.3.x research direction preserves the original Price Action objective:

```text
Context
→ Key Level
→ Event
→ Transition
→ Trigger
→ Follow-through
→ Setup
→ Structural Invalidation
→ Structural Target
→ RR
→ Advisory
```

This includes high-context judgments such as:

- which Key Level matters most now;
- why a level is structurally important;
- whether a breakout is meaningful in its current context;
- whether a failed breakout is a genuine reversal setup or random noise;
- whether a pullback is healthy continuation or structural deterioration;
- how W1 / D1 / intraday evidence should be interpreted together;
- whether a Trigger genuinely changes local structure;
- whether Follow-through is convincing enough;
- which structural level truly invalidates the thesis;
- which target is the next meaningful obstacle rather than merely the mathematically nearest point;
- whether a move is valid but too extended to chase.

These are exactly the areas where deterministic encoding can become brittle, excessively complex, or semantically distorted.

The real-market TASK-006B stability work demonstrated the practical cost of trying to make increasingly rich Price Action semantics fully deterministic: path-lock, stale Pivot state, excessive Zone accumulation, Range-recency ambiguity, and sensitivity to historical initialization.

PAQS v0.4 Lite is therefore valuable, but for a different goal: **build a stable machine-executable Price Action subset rather than emulate the entire discretionary reasoning process.**

---

# 3. PAQS-E definition

## 3.1 PAQS-E is LLM-native

PAQS-E should be formally defined as:

> **An LLM-native Expert Reasoning Engine that executes the PAQS v0.3.x Naked Price Action specification over a controlled point-in-time market snapshot.**

Human discretionary chart interpretation is **not** part of PAQS-E runtime.

The human user remains outside the engine as the final capital allocator.

The responsibility split is:

```text
PAQS-Q
= deterministic Quant Decision Engine

PAQS-E
= LLM Expert Reasoning Engine

Human
= final Capital Decision Maker
```

The human does not manually complete missing PAQS-E reasoning steps during normal runtime.

---

## 3.2 PAQS-E is a complete strategy branch, not a review plugin

Do not call PAQS-E merely an `Expert Review Layer`.

That naming incorrectly implies:

```text
PAQS-Q decides first
→ PAQS-E only reviews PAQS-Q
```

Instead, PAQS-E must be capable of independently producing a complete analysis from the standardized market snapshot.

Recommended term:

```text
PAQS-E — Expert Reasoning Engine
```

It may be used in three modes:

```text
A. PAQS-E standalone
   user selects a symbol
   → PAQS-E performs full expert analysis

B. PAQS-Q scanner → PAQS-E
   PAQS-Q scans a large universe
   → candidate pool
   → PAQS-E performs deep analysis

C. Parallel comparison
   same symbol / same as-of snapshot
   → PAQS-Q output
   → PAQS-E output
   → disagreement surfaced to user
```

PAQS-E is therefore not subordinate to PAQS-Q.

---

# 4. PAQS-Q definition

PAQS-Q is the deterministic machine branch represented by the v0.4 Lite direction.

Its success criteria are different from PAQS-E.

PAQS-Q should optimize for:

```text
stability
reproducibility
no-lookahead
bounded current structure
large-universe scanning
replayability
auditability
low origin sensitivity
bounded Zone / Range complexity
robustness under small parameter perturbations
```

It does **not** need to reproduce every high-context judgment available to PAQS-E.

A PAQS-Q rule can be intentionally simpler if it is deterministic and useful.

Examples include the current v0.4 Lite direction:

```text
one Pivot engine per timeframe
bounded W1 / D1 / M30 horizons
recent D1 Zones
recent D1 Range
EMA20 / EMA50 trend evidence
ROC20 / ROC60 momentum evidence
ATR-based anti-FOMO extension filter
```

These remain useful as machine rules, scanner signals, baselines and validation references.

---

# 5. PAQS-E must be model-provider-agnostic

PAQS-E must not be architecturally equivalent to OpenAI.

The correct relationship is:

```text
PAQS-E Strategy Specification
            ↓
Market Snapshot Contract
            ↓
LLM Reasoning Provider Interface
            ↓
┌──────────────┬──────────────┬──────────────┐
│ OpenAI       │ Anthropic    │ Google       │
│ current      │ optional     │ optional     │
│ default      │ provider     │ provider     │
└──────────────┴──────────────┴──────────────┘
```

Current product preference:

```text
OpenAI = default / preferred provider for the present stage
```

However this is a **provider choice**, not part of PAQS-E strategy semantics.

The durable PAQS-E assets are:

```text
Strategy Specification
Market Snapshot Contract
Prompt / Reasoning Contract
Structured Output Schema
Decision Ledger
Evaluation Dataset
Evaluation Metrics
```

A future model-provider switch should not require redesigning PAQS-E itself.

---

# 6. Deterministic code remains essential

LLM-native strategy reasoning does not mean that the LLM should invent or scrape arbitrary market facts.

The deterministic product layer remains responsible for factual correctness and reproducibility.

Code should own:

```text
Market Data Acquisition
Provider normalization
Corporate-action / adjustment semantics
Market calendar
Session semantics
Completed-bar eligibility
W1 / D1 / M30 aggregation
Point-in-time cutoffs
ATR and other objective numerical features
Data-quality state
Snapshot hashing
Deterministic arithmetic / validation
```

The principle is:

> **Code provides facts. PAQS-E reasons over facts.**

Examples:

- the LLM may decide *why* 196 is the correct structural invalidation;
- deterministic code may verify the RR arithmetic once Entry / Invalidation / Target have been chosen;
- the LLM may interpret a failed breakdown in context;
- code must guarantee the model never sees bars beyond the declared `as_of` cutoff.

This preserves the value of the existing quant/data infrastructure even when the final PAQS-E judgment is LLM-native.

---

# 7. PAQS-E Market Snapshot Contract

PAQS-E must not operate as:

```text
ticker
→ model browses arbitrary internet data
→ model decides what chart/history to use
→ BUY / SELL
```

The model must receive a standardized, immutable, point-in-time snapshot generated by the product.

Minimum logical inputs should eventually include:

```text
snapshot_version
snapshot_hash
symbol
market
as_of_timestamp
calculated_at

W1 completed bars / derived context inputs
D1 completed bars / setup inputs
M30 completed regular-session bars / trigger inputs

market_timezone
session metadata
corporate_action / adjustment metadata
data quality / coverage

ATR14
optional objective features such as EMA20 / EMA50 / ROC20 / ROC60
```

The LLM may additionally receive a deterministic chart rendering in a future phase, but the chart must reflect the exact same snapshot and cutoff.

No PAQS-E analysis may silently use data newer than `as_of_timestamp`.

---

# 8. Strict As-Of discipline

Historical PAQS-E validation must be true point-in-time replay.

For an evaluation cutoff `t`:

```text
model input = data legitimately available at or before t
```

Forbidden:

```text
show full future chart
→ ask model what it would have done at t
```

That introduces hindsight bias and makes the evaluation invalid.

PAQS-E must inherit the same core invariant already valued elsewhere in PAQS:

```text
analysis[t] = f(information <= t)
```

This is one of the most important product boundaries.

---

# 9. Structured PAQS-E output

PAQS-E must not return only free-form prose.

The model should ultimately emit a structured decision object whose core fields can be persisted, compared and evaluated.

Candidate logical schema:

```text
strategy_family = PAQS-E
strategy_version
model_provider
model_id
model_snapshot / version if available
prompt_version
snapshot_hash

context
regime

key_levels[]
events[]
transition
trigger
followthrough
setup

entry_advisory
holder_advisory

entry_reference
invalidation_level
invalidation_reason

target_t1
target_t2
rr_t1
rr_t2

uncertainty
reason_codes[]
explanation
```

The natural-language explanation remains important for the user, but the primary decision facts must be machine-readable.

Deterministic post-validation may check arithmetic and schema consistency without replacing PAQS-E's strategy reasoning.

---

# 10. Immutable LLM Decision Ledger

The PAQS-E decision ledger is a core product asset.

Every analysis must be stored as an immutable snapshot.

Example:

```text
2026-09-02
symbol = FANG
advisory = WATCH_LONG
support = 198
invalidation = 196
T1 = 217
```

If price later falls to 190, the historical decision must not be regenerated and silently rewritten as:

```text
"the real support was 189"
```

A later model call creates a **new revision / new as-of decision**, never a replacement for the historical record.

Ledger metadata should include at minimum:

```text
decision_id
symbol
market
as_of_timestamp
market_snapshot_hash
strategy_version
prompt_version
model_provider
model_id
model parameters / deterministic request config where available
structured output
raw explanation / raw model response where policy permits
created_at
```

This is required to make PAQS-E scientifically evaluable rather than merely conversational.

---

# 11. Multi-model capability

PAQS-E should support multiple reasoning providers architecturally, while using a single default provider initially.

Current stage:

```text
OpenAI = preferred/default PAQS-E provider
```

Future research can run the same:

```text
PAQS-E spec
+
same point-in-time snapshot
+
same output schema
```

through multiple models.

Possible comparisons:

```text
Key Level agreement
Setup classification agreement
Invalidation quality
Target quality
NO_TRADE discipline
FOMO / chase rate
reasoning consistency
repeated-run stability
future realized outcome statistics
```

Model disagreement can later become diagnostic metadata.

Example:

```text
OpenAI    → WATCH_LONG
Model B   → NO_TRADE
Model C   → WATCH_LONG
```

Possible future UI:

```text
model_disagreement = MEDIUM
```

**Do not implement voting / ensemble logic in the first PAQS-E phase.**

Provider abstraction is required now; ensemble strategy is not.

---

# 12. PAQS-E and PAQS-Q should not be averaged into one score

If both engines are present, disagreement is information.

Forbidden design direction:

```text
PAQS-Q = 78
PAQS-E = 91
average = 84.5
→ BUY
```

The two engines should preserve separate outputs.

Example Dashboard concept:

```text
PAQS-Q — Quant Engine
---------------------
W1 Context
D1 Regime
Current Zones
Trend evidence
Momentum evidence
Extension / Anti-FOMO
Machine candidate state

PAQS-E — Expert Reasoning Engine
--------------------------------
Expert Context
Key Levels
Price Action interpretation
Setup
Trigger / Follow-through
Invalidation
Target
RR
Entry Advisory
Holder Advisory
Explanation
```

If aligned:

```text
Machine / Expert alignment = HIGH
```

If different:

```text
disagreement surfaced explicitly
```

No composite numerical score may override a structural hard gate or hide disagreement.

---

# 13. Product operating modes

The product can support two valuable user workflows.

## 13.1 User-selected deep analysis

The user chooses one symbol directly:

```text
Selected Symbol
→ shared Market Snapshot
→ PAQS-E
→ expert decision window
```

This is important because the user may already have investment intent and does not need PAQS-Q screening first.

## 13.2 Large-universe scan

For a broad universe:

```text
Universe
→ PAQS-Q deterministic scanner
→ bounded candidate pool
→ PAQS-E deep reasoning on candidates
→ Dashboard
→ Human capital decision
```

This gives the quant code an important role: scale, filtering, reproducibility and efficient candidate generation.

---

# 14. Different validation standards

PAQS-Q and PAQS-E require different evaluation frameworks.

## 14.1 PAQS-Q

Primary concerns:

```text
determinism
no-lookahead
origin invariance
Pivot staleness
Zone count / recency
Range pathology
Regime churn
small-parameter robustness
large-universe behavior
```

## 14.2 PAQS-E

Primary concerns:

```text
As-Of discipline
Key Level quality
Setup classification quality
Invalidation quality
Target quality
Advisory consistency
NO_TRADE discipline
chasing / FOMO behavior
reasoning stability
prompt-version sensitivity
model-version sensitivity
cross-model disagreement
```

PAQS-E should eventually have a hand-labelled Gold Set of historical point-in-time cases.

A candidate Gold Set record can include:

```text
as_of snapshot
acceptable market context range
important Key Levels
acceptable Setup families
invalid / unacceptable interpretations
reasonable invalidation region
reasonable target candidates
expected advisory class / range
```

The Gold Set evaluates reasoning quality; it should not be constructed by looking for the most profitable historical decisions.

---

# 15. PAQS-E can feed future PAQS-Q research

The two branches can evolve together without becoming identical.

A useful long-term loop is:

```text
PAQS-E repeatedly makes a stable high-context judgment
        ↓
collect sufficient As-Of cases
        ↓
identify the invariant part of the reasoning
        ↓
formalize only that stable subset
        ↓
consider adding it to PAQS-Q
```

This is preferable to attempting to encode the entire naked-Price-Action reasoning process before enough evidence exists.

In other words:

> **PAQS-E can be the discovery / reasoning frontier; PAQS-Q can absorb only the parts that later prove reliably formalizable.**

---

# 16. Interpretation of the current v0.4 Lite amendment

The v0.4 Lite research direction remains useful.

However Product Management should reframe it as:

```text
PAQS-Q Machine Branch
```

rather than:

```text
new universal PAQS version that replaces v0.3.x
```

Its simplifications are valuable specifically because machine execution needs stronger boundedness and determinism.

Likewise v0.3.1 remains useful as the research foundation for:

```text
PAQS-E Expert Reasoning Branch
```

This memo is not requesting deletion or rewriting of historical research documents merely to fit the new naming. Product Management should first decide the governance / documentation migration plan.

---

# 17. Important strategy-expert caution on v0.4 Lite Quant veto

The current v0.4 Lite direction allows Trend and Momentum conflict to veto a valid PAQS candidate.

This policy should not automatically be universal across all future Setup families.

Reason:

```text
Trend Pullback Long
```

may legitimately benefit from EMA / ROC confirmation.

But:

```text
Failed Breakdown Reversal
Bottom / Right-Side Reversal
Range reversal
```

may occur while lagging EMA / ROC evidence is still bearish.

A universal rule such as:

```text
Trend CONFLICT + Momentum CONFLICT
→ always NO_TRADE
```

could systematically suppress the exact early structural reversals that Price Action is meant to recognize.

Recommendation for Product Management:

```text
Quant confirmation / veto policy should eventually be Setup-specific.
```

This is a strategy-design concern, not an instruction to change code now.

---

# 18. Product positioning

Recommended product-level description:

> **Human-in-the-loop AI + Quant Investment Decision Support System**

The three roles are:

```text
Deterministic Quant Infrastructure / PAQS-Q
= facts, scale, discipline, repeatability

LLM / PAQS-E
= high-context Price Action reasoning

Human user
= final capital allocation decision
```

A compact product principle:

> **Quant provides facts and scalable machine judgment; the LLM performs expert Price Action reasoning; the human decides whether to commit capital.**

The product remains read-only decision support. No real brokerage execution is implied by either engine.

---

# 19. Requested Product Manager response

Before any new implementation work, please return a product / architecture analysis that explicitly answers:

1. Do you accept PAQS-E and PAQS-Q as **parallel strategy branches**, not a simple version supersession chain?
2. How should the existing `PAQS v0.3.1` research documents be reclassified as the PAQS-E foundation without destroying research history?
3. How should `PAQS v0.4 Lite` be reclassified as the PAQS-Q machine branch?
4. Which current Roadmap tasks remain valid, which should be renamed, split, postponed or re-scoped?
5. What is the minimum PAQS-E architecture needed for an LLM-native MVP?
6. Where should the model-provider abstraction live?
7. What exact fields belong in the PAQS-E Market Snapshot Contract?
8. What exact fields belong in the immutable LLM Decision Ledger?
9. How should prompt versioning, strategy versioning and model versioning be tracked so historical outputs remain comparable?
10. How should PAQS-E historical As-Of evaluation be implemented without hindsight contamination?
11. How should PAQS-Q and PAQS-E appear side by side in the Dashboard without hiding disagreement behind a score?
12. Which components can be shared between PAQS-E and PAQS-Q, and which must remain isolated?
13. What additional architectural risks have not yet been considered?
14. How should future implementation Task Contracts preserve the rule that **research documents do not automatically authorize code changes**?

---

# 20. Governance instruction

This memo communicates the strategy expert's recommendation to Product Management.

It does **not** itself approve:

```text
006B-Lite implementation
TASK-006C
TASK-006D
PAQS-E API integration
OpenAI API integration
multi-model ensemble
Dashboard changes
Roadmap changes
broker integration
live trading
```

No implementation should begin from this memo alone.

The Product Manager should first discuss the architecture with the user, identify contradictions with existing Roadmap / Master Spec authority, and present a bounded migration plan for explicit user approval.

---

**End — PAQS Dual-Branch Product Architecture Memo**
