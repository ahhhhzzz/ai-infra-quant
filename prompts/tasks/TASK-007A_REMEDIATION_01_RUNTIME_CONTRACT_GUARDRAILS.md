# TASK-007A REMEDIATION 01 — Runtime Contract Guardrails

Status: **APPROVED FOCUSED REMEDIATION CONTRACT**

Repository: `ahhhhzzz/ai-infra-quant`

Task branch: `task/007a-paqs-e-runtime-openai-strategy-port`

Original authoritative base: `6218c69bfc8202d6649e7ab01a2bd20fd585cdd5`

Parent TASK-007A Contract: `prompts/tasks/TASK-007A_PAQS_E_RUNTIME_STRUCTURED_OUTPUT_OPENAI_STRATEGY_PORT.md`

Parent Contract commit: `b74712b8828518d9b507e4bdbf9c43084c8129d3`

Implementation SHA independently reviewed: `5299d199b27b8dc43942a6642274c4b2479554be`

Independent review verdict on that implementation SHA: **NEEDS REMEDIATION**

This remediation is deliberately narrow. It fixes four verified runtime-contract guardrail defects only. It does not authorize TASK-007B, TASK-007C, persistence, Dashboard Analyze, historical replay, PAQS-Q, broker behavior, new strategy semantics, or broader refactoring.

---

## 1. Verified finding R1 — As-Of-incompatible auxiliary context reaches the model

### Evidence

The accepted PAQS-E Master Spec requires strict As-Of discipline:

```text
model_input(t) = all and only data legally available at t
```

The current `AuxiliaryContextItem` carries `as_of_compatible`, but `PaqsEReasoningRequestV1` only prevents a future timestamp from being marked `as_of_compatible=true`.

It still permits `as_of_compatible=false` items, and the OpenAI adapter serializes the entire request with `canonical_json(request)` into the provider-facing model input. Therefore content explicitly declared incompatible with the analysis cutoff can still be visible to the model.

A prompt instruction telling the model not to use future information is not an adequate replacement for input isolation.

### Required remediation

For TASK-007A `CURRENT_ANALYSIS`, **no auxiliary context with `as_of_compatible=false` may reach the reasoning model**.

Use one of these two bounded designs:

1. **Preferred/simple:** reject a reasoning request/runtime call that contains any `as_of_compatible=false` auxiliary item; or
2. preserve such items only in a clearly separate audit-only envelope while deterministically excluding their content from the provider-facing reasoning payload.

Whichever design is chosen, it must be impossible for the OpenAI adapter to transmit the incompatible item content to the model.

Do not globally prohibit future auxiliary context categories. News, web research, analyst research, social/community commentary, prior PAQS-E results, conversation/user context, user-supplied position context, financial reports, and future categories remain architecturally allowed when explicitly supplied and As-Of-compatible under the active analysis contract.

### Required tests

Add deterministic tests proving at least:

- an As-Of-compatible auxiliary item remains available to the provider-facing input;
- an `as_of_compatible=false` item cannot be transmitted to the OpenAI model;
- a source timestamp later than the snapshot cutoff cannot be treated as compatible;
- ordered/auditable compatible auxiliary context behavior remains intact.

---

## 2. Verified finding R2 — zero Key Levels accepted for complete supported analysis

### Evidence

The accepted Master Spec requires each normal analysis to select **1–4** current decision-relevant Key Levels.

The TASK-007A Contract permits zero only when analysis is unavailable/invalid, otherwise at most four.

The implementation currently enforces only `len(key_levels) <= 4`. A `SUPPORTED + COMPLETE` result, including an actionable `LONG_READY`, can therefore validate with `key_levels=()`.

### Required remediation

Preserve `max=4`, and add deterministic minimum-cardinality validation with these bounded v1 semantics:

- `SUPPORTED + COMPLETE` analysis must contain **1–4** Key Levels;
- `LONG_READY` or `SHORT_READY` must always contain **1–4** Key Levels;
- zero Key Levels may remain representable for degraded/unavailable/invalid outputs where a reliable Key-Level decision layer cannot safely be established.

Do not invent mechanical rules for how PAQS-E selects the levels. The validator only enforces cardinality/contract consistency, not strategy selection.

### Required tests

Add tests proving at least:

- `SUPPORTED + COMPLETE` with zero Key Levels fails validation;
- a valid complete result with 1–4 Key Levels passes;
- an actionable READY result with zero Key Levels fails;
- a genuinely unavailable/invalid degraded result can still represent zero Key Levels without fabricating one.

---

## 3. Verified finding R3 — runtime policy labels can disagree with actual validator behavior

### Evidence

`PaqsERuntimeConfigV1` currently exposes:

```text
entry_reference_policy
quote_freshness_policy
```

with defaults:

```text
SNAPSHOT_QUOTE_REGULAR_OPEN_REQUIRED
UPSTREAM_AVAILABLE_REQUIRED
```

but validates only that the strings are non-empty.

The validator nonetheless always applies the single current v1 behavior corresponding to those defaults: available snapshot quote, regular-session/open market, and the current upstream-availability freshness rule.

A caller can therefore supply an arbitrary policy label while runtime behavior remains unchanged, making the versioned configuration/audit identity misleading.

### Required remediation

TASK-007A v1 supports only the semantics already implemented. Make that truthful and machine-enforced.

Require exact v1 policy values, preferably through constants or exact enums:

```text
entry_reference_policy = SNAPSHOT_QUOTE_REGULAR_OPEN_REQUIRED
quote_freshness_policy = UPSTREAM_AVAILABLE_REQUIRED
```

Any other value must fail configuration/request construction truthfully.

Do **not** implement additional entry/freshness policy variants in this remediation. A future alternative policy requires a separately versioned runtime contract or separately approved semantics.

### Required tests

Add tests proving:

- the two exact v1 policy values are accepted;
- arbitrary/non-empty alternative labels are rejected;
- validator behavior remains aligned with those exact policy identities.

---

## 4. Verified finding R4 — minimum RR guardrail invalidates correct non-action judgments

### Evidence

The accepted Master Spec permits `NO_TRADE` when data/analysis are valid but a strategy hard condition fails, and states that any minimum RR threshold must come from explicit Runtime Configuration.

The current validator emits `RR_GUARDRAIL_NOT_MET` whenever `RRStatus=FINAL` and computed T1 RR is below configured `minimum_rr_t1`, regardless of `entry.advisory`.

That means a semantically correct result such as:

```text
entry_advisory = NO_TRADE
rr_status = FINAL
rr_t1 < configured R_min
```

is rejected as an invalid structured result, even though the output may be correctly explaining that the RR hard gate failed.

This oversteps the validator role: the validator may prevent an actionable READY state from violating a configured hard gate, but it must not classify the correct non-action judgment itself as invalid solely because the gate failed.

### Required remediation

Apply `minimum_rr_t1` as an **actionable-state consistency gate**, not as a universal validity gate.

At minimum:

- `LONG_READY` / `SHORT_READY` with final RR below configured `minimum_rr_t1` -> deterministic validation failure `RR_GUARDRAIL_NOT_MET` (or equivalent existing code);
- valid non-action advisories such as `NO_TRADE`, `VALID_SETUP_BUT_POOR_ENTRY`, or `WAIT_RETEST` must not fail validation **solely** because final RR is below `minimum_rr_t1`;
- the validator must not rewrite the advisory in either direction;
- Decimal RR arithmetic validation remains unchanged.

Do not add a universal minimum RR. This applies only when a versioned runtime guardrail explicitly supplies one.

### Required tests

Add tests proving at least:

- `LONG_READY` below configured R_min fails;
- a structurally/mathematically valid `NO_TRADE` with the same below-threshold final RR can pass unchanged;
- validator never converts a non-action advisory into READY or vice versa.

---

## 5. Scope and protected boundaries

This remediation must preserve all accepted TASK-007A behavior that is not implicated by R1–R4, including:

- exact request/output/runtime/prompt/validator versions unless a change is strictly required by these fixes;
- exact machine enum vocabulary;
- Trigger/Follow-through matrix;
- short advisory vs short execution separation;
- Strategy Markdown registry/loader/hash behavior;
- provider-neutral reasoning port;
- OpenAI Responses API adapter;
- strict structured output;
- exact caller model ID with no fallback;
- `store=false`;
- no OpenAI tools/background/conversation/previous-response state;
- server-side-only `OPENAI_API_KEY` secrecy;
- no Analyze endpoint;
- no Decision Ledger/persistence/migration;
- no Dashboard Analyze UI;
- no historical replay implementation;
- no PAQS-Q changes;
- no broker/account/order/write capability.

Do not modify accepted PAQS-E research source files.

Do not modify:

- `docs/phases/PHASE_1_PLAN.md`
- `src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py`
- immutable Phase 1 review evidence.

If `phase1_remediation_commit.txt` exists locally, leave it untracked, untouched, unstaged, and uncommitted.

---

## 6. Expected bounded implementation areas

Prefer changes only where needed, expected primarily in:

- `src/ai_infra_quant/core/domain/paqs_e_reasoning.py`
- `src/ai_infra_quant/application/paqs_e_runtime.py`
- `src/ai_infra_quant/integrations/openai_reasoning/adapter.py` only if R1 filtering is implemented at provider-payload level
- focused TASK-007A unit tests
- minimal TASK-007A documentation if required for exact policy/As-Of semantics

Do not refactor unrelated modules.

---

## 7. Validation gate

Run at minimum:

- focused TASK-007A/config/architecture tests;
- full pytest suite;
- Ruff check;
- Ruff format verification;
- mypy;
- startup/health/OpenAPI/fresh SQLite migration regression where feasible.

No paid/live OpenAI call is required.

Verify specifically that:

- incompatible auxiliary context cannot reach provider-facing model input;
- complete supported output requires 1–4 Key Levels;
- exact v1 policy labels cannot diverge from behavior;
- low configured RR rejects actionable READY but does not invalidate a correct non-action result;
- no TASK-007B/007C/persistence/broker scope appears.

---

## 8. Git and stop condition

Continue on the same task branch:

`task/007a-paqs-e-runtime-openai-strategy-port`

This remediation Contract is based directly on independently reviewed implementation SHA:

`5299d199b27b8dc43942a6642274c4b2479554be`

Use targeted staging only.

Commit and push only the same task branch.

Do not merge `roadmap/no-live-trading`.

Do not create TASK-007B or TASK-007C branches.

Stop after remediation for independent re-review.

Final report must include:

- remediation Contract SHA;
- pre-remediation implementation SHA;
- final remediation HEAD;
- exact changed files;
- exact resolution of R1, R2, R3, R4;
- focused/full validation results;
- confirmation protected files remained unchanged;
- confirmation no scope leakage occurred;
- push verification;
- unresolved issues, if any.

**End — TASK-007A REMEDIATION 01**
