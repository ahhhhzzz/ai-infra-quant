# TASK-007C1 REMEDIATION 01 — Live Dogfood Runtime Compatibility

Status: **APPROVED REMEDIATION CONTRACT — user-authorized remediation only**

Issued: 2026-09-07

Repository: `ahhhhzzz/ai-infra-quant`

Authoritative branch: `roadmap/no-live-trading`

Authoritative SHA at remediation issuance: `80f089bc2d285cca492c41aaeaf047e177bc2812`

TASK-007C1 branch: `task/007c1-paqs-e-multi-model-web-research`

Exact remediation base / reviewed implementation SHA: `fc527c61fcdc2b4f54506dc5622f0b1faa6945d5`

Original TASK-007C1 Contract commit: `9f41016b2341e91ad2825b7f731bca4f378b0108`

Original TASK-007C1 Contract:
`prompts/tasks/TASK-007C1_PAQS_E_MULTI_MODEL_SECURE_CREDENTIALS_WEB_RESEARCH.md`

This remediation is driven by real local product dogfooding of the exact implementation SHA above. It is intentionally narrow. It does not reopen PAQS-E strategy semantics, the deterministic validator contract, Decision Ledger schema, model catalog scope, credential architecture, or the permanent no-live-trading boundary.

---

## 1. Remediation purpose

Correct four concrete integration defects exposed only after real local use of TASK-007C1:

1. stale backend reuse by the Windows launcher after branch/code changes;
2. incomplete compatibility with legal DeepSeek native web-search action shapes;
3. a fixed 180-second browser abort that can expire before a legitimate synchronous Analyze finishes;
4. model-authored echoes of deterministic Snapshot facts causing avoidable validator failure.

No other behavior is authorized.

---

## 2. Accepted live evidence

### R1 — stale backend reuse

The user switched to the TASK-007C1 implementation but an already-running older FastAPI process remained on port 8000. `start_dashboard.bat` accepted the process solely because `/health` reported healthy and reused it.

Observed result:

- current files/templates were TASK-007C1;
- the running backend still returned the older configuration schema containing `model_provider: openai` and `api_key_configured` rather than `default_model_key` and `models[]`;
- the TASK-007C1 model and strategy selectors therefore remained empty until the old process was manually stopped and the current code was started.

After restart, `/api/v1/paqs-e/configuration` returned the correct eleven-model TASK-007C1 projection.

### R2 — DeepSeek web research

With `DeepSeek V4 Flash` and web research enabled, the real product returned:

`PAQS_E_RESEARCH_PRECONDITION_FAILED`

and correctly created no Decision.

The implementation currently requires every returned `web_search_call.action.type` to equal `search`. Current official DeepSeek Responses documentation permits server-side web-search actions of `search`, `open_page`, and `find_in_page`. Therefore the normalizer is narrower than the provider's documented legal output shape and must be corrected without weakening evidence provenance.

The raw live provider response was not retained and must not be fabricated. The remediation must fix the documented incompatibility and prove it with safe deterministic fixtures, then require a separate live smoke.

### R3 — browser timeout shorter than real Analyze

Real DeepSeek Run:

- Run ID: `038920ac-8bf6-4d2c-97f5-e78f803f0f2f`
- provider: `deepseek`
- model: `deepseek-v4-flash`
- started: `2026-09-07T15:45:56.215389Z`
- completed: `2026-09-07T15:49:57.172050Z`
- terminal status: `VALIDATION_FAILED`

Elapsed time was about 241 seconds.

The TASK-007C1 browser aborts Analyze after 180 seconds. The browser therefore showed an unknown outcome before the server reached its truthful terminal result.

### R4 — deterministic Snapshot echo mismatch

The same real Run reached provider success, strict structured parsing and domain conversion, then failed only the deterministic validator with:

- code: `CURRENT_PRICE_FRESHNESS_MISMATCH`
- field: `price_references.current_price_reference.freshness_status`

The accepted validator already defines this field as a deterministic projection of Snapshot quote availability:

- `AVAILABLE -> FRESH`
- `STALE -> STALE`
- `DELAYED -> DELAYED`
- otherwise `UNKNOWN`

This is not a strategy judgment. The validator must not be weakened. Instead, deterministic Snapshot-bound echo fields must be projected by application code before validation so model interpretation cannot overwrite immutable facts.

---

## 3. R1 remediation — startup-captured source revision handshake

### 3.1 Requirement

The launcher must never treat any healthy AI Infra Quant process as reusable without proving that the running process was started from the same source revision as the current checkout.

### 3.2 Runtime identity

Expose a bounded non-secret runtime source revision in the existing health surface or an equally small loopback-only runtime identity surface.

Preferred behavior:

- capture the source revision **once at application/process startup**;
- do not recompute it dynamically on every health request;
- represent a real Git SHA as exactly 40 lowercase hexadecimal characters;
- allow a bounded `unknown`/unavailable state only for non-launcher/manual environments where a Git revision cannot be resolved;
- never expose filesystem paths, environment dumps, credentials, branch credentials, or arbitrary process metadata.

It is acceptable for `start_dashboard.bat` to resolve the current checkout SHA using `git rev-parse HEAD` and pass that exact value to the new Uvicorn process through a dedicated process environment variable. The application must freeze that value at startup.

If a fallback startup-time Git lookup is implemented, it must also be frozen once. It must not read current `.git/HEAD` dynamically after startup, because a later branch switch must not make an old process falsely appear current.

### 3.3 Launcher behavior

Before reusing an existing healthy service on port 8000:

1. determine the current checkout HEAD;
2. read the running service's startup-captured source revision;
3. reuse only when the revisions are exactly equal.

If the running service is healthy but has a missing, invalid or different source revision:

- do not open the Dashboard as if it were current;
- do not silently reuse it;
- print a clear stale-backend/version-mismatch message containing only safe revisions/status;
- fail safely and instruct the user to close/restart the existing dashboard process;
- do **not** automatically kill an arbitrary process or force-terminate unrelated work.

If port 8000 belongs to a non-AI-Infra service, retain the existing port-conflict behavior.

### 3.4 Tests

Add launcher/runtime tests proving:

- same SHA healthy backend is reusable;
- old SHA healthy backend is rejected as stale;
- missing/invalid revision is not silently accepted;
- a branch/code change cannot be masked by dynamic revision lookup;
- launcher still does not terminate unrelated processes;
- existing Futu OpenD behavior remains unchanged.

Do not solve R1 with browser cache-busting alone. The observed fault was a stale Python backend process, not static browser cache.

---

## 4. R2 remediation — DeepSeek native web-search action compatibility

### 4.1 Preserve research architecture

Retain the accepted lifecycle:

`Snapshot freeze -> bounded research -> frozen AuxiliaryContext -> tool-free PAQS-E reasoning -> validator -> Ledger`

Do not move web tools into final PAQS-E reasoning.

Do not add automatic retries, provider fallback, model fallback or a second paid research provider.

### 4.2 DeepSeek documented actions

For the DeepSeek Responses research route, safely accept completed native `web_search_call` actions documented by DeepSeek:

- `search`
- `open_page`
- `find_in_page`

Unknown action types still fail closed.

A legal `open_page` or `find_in_page` action must not cause the entire capsule to fail merely because it is not a `search` action.

### 4.3 Evidence provenance must remain strict

Do not turn this compatibility fix into permissive source acceptance.

Requirements:

- at least one actual native `search` action must exist;
- only `search` actions contribute search query strings/counts;
- included evidence URLs must still be grounded in provider-native search sources and/or provider-native URL citations;
- `open_page` / `find_in_page` may enrich or inspect already-native material but may not allow a model-generated arbitrary URL to become trusted evidence;
- generated summary JSON may not invent URLs, publication timestamps or citations;
- future-dated known publications remain excluded;
- unknown publication time remains explicitly unknown with the existing limitation;
- no chain-of-thought/reasoning trace may be persisted.

If the official action objects include a URL/target, use it only according to the documented schema and only if it can be bound to the verified native source/citation set. Otherwise record only bounded safe action provenance or ignore that action for evidence construction.

### 4.4 Bounds

Preserve the original cost-conscious intent while accommodating provider-native page actions:

- maximum 4 reported **search queries**;
- maximum 8 included evidence items;
- maximum 64 verified raw source records;
- existing per-item and total normalized character bounds remain;
- no continuation/retry initiated by this application;
- for DeepSeek only, total completed `web_search_call` action records may be accepted up to the provider's documented server-side auto-continuation cap of 10, provided no more than 4 are actual search queries/actions producing those queries;
- exceeding the accepted action/query bounds fails closed rather than truncating silently.

Do not claim that application acceptance limits guarantee provider-side billing limits. DeepSeek's native server-side search continuation remains a documented cost-control limitation.

Other providers must not be broadened automatically unless their already-approved native response shape requires the same documented action handling.

### 4.5 Tests

Add deterministic fixtures covering:

- `search` only;
- `search -> open_page -> message`;
- `search -> open_page -> find_in_page -> message`;
- multiple legal page/find actions with <=4 search queries;
- >4 search queries rejected;
- >10 DeepSeek web-search action records rejected;
- unknown action type rejected;
- page/find actions cannot smuggle an unverified URL into evidence;
- future and unknown publication timestamp behavior unchanged;
- final PAQS-E reasoning still receives frozen `auxiliary_context[]` and `tools=[]`.

---

## 5. R3 remediation — do not auto-abort a valid long synchronous Analyze

### 5.1 Preserve synchronous Analyze

TASK-007B/TASK-007C1 Analyze remains one explicit synchronous request.

Do not introduce:

- background workers;
- job queues;
- polling APIs;
- websocket analysis;
- automatic resubmission;
- retry-on-timeout.

### 5.2 Browser behavior

Remove the fixed 180-second application-level `AbortController` timeout as a normal terminal mechanism for Analyze, or replace it with a design that demonstrably cannot expire before the server/provider's bounded operation while still satisfying the no-retry contract.

Preferred minimal behavior:

- keep the fetch pending until the server sends its terminal response or a real network/browser failure occurs;
- retain the global one-in-flight Analyze guard;
- after a long threshold such as 180 seconds, update UI text to state that analysis is still running and must not be resubmitted;
- this long-wait notice must **not** abort, retry or release the in-flight guard;
- when the server eventually returns `SUCCEEDED`, `PROVIDER_FAILED` or `VALIDATION_FAILED`, render the truthful terminal result normally;
- if the actual connection fails or the page is closed, preserve the existing unknown-outcome guidance to inspect history/known Run before explicitly trying again.

Do not increase the timeout to another arbitrary value and call the problem solved unless tests prove that the new bound is derived from a real server-side whole-operation bound. A non-aborting long-wait state is preferred.

### 5.3 Tests

Using fake timers/delayed browser fixtures, prove:

- at 180 seconds the request remains in flight;
- no second Analyze POST occurs;
- the button remains guarded;
- a later terminal server response is rendered correctly;
- actual rejected/network-failed fetch still becomes the existing unknown-outcome state without retry.

---

## 6. R4 remediation — deterministic Snapshot fact projection before validator

### 6.1 Principle

Do not ask the LLM to be authoritative for values already fully determined by the immutable request/Snapshot and existing runtime policy.

The provider still returns the strict PAQS-E schema, but application code may project deterministic Snapshot-bound echo fields onto the parsed domain result **after strict provider parsing and before the existing validator**.

This projection must be provider-neutral and apply consistently to all registered models, not only DeepSeek.

### 6.2 Required deterministic current-price projection

At minimum, the effective result passed to the validator must use the bound Snapshot/runtime mapping for:

`price_references.current_price_reference`:

- `price` = Snapshot current/reference quote price;
- `timestamp` = Snapshot latest quote timestamp;
- `freshness_status` = existing validator mapping from Snapshot quote availability;
- `session_type` = existing validator mapping from Snapshot canonical market state.

These are immutable facts/derived enums, not model judgments.

### 6.3 Executable-entry echo fields

Do **not** change whether the model marks `executable_entry_reference.eligible` true or false.

If the model marks it eligible, the exact factual echoes that the existing validator already requires to equal the bound Snapshot/runtime may be projected deterministically, including price/timestamp/freshness/session as appropriate.

The projector must not make an otherwise-ineligible market state eligible. Existing checks such as market-open/session/entry-policy checks remain authoritative and must still be capable of failing the result.

### 6.4 Explicitly forbidden normalization

Do not normalize, overwrite or auto-correct semantic model judgments, including:

- identity/provider/model identity;
- support status/input quality in this remediation;
- context/regime/bias;
- key levels;
- current event;
- trigger/follow-through;
- setup family/direction/stage;
- entry advisory;
- `executable_entry_reference.eligible`;
- invalidation selection;
- target selection;
- holder advisory;
- uncertainty;
- explanation/reason codes.

Do not change model-selected invalidation or target numeric references.

Do not alter RR fields/arithmetic in this remediation. Existing deterministic Decimal validation remains unchanged.

### 6.5 Validator must remain unchanged in authority

Do not weaken or delete validator rules, including:

- `CURRENT_PRICE_FACT_MISMATCH`;
- `CURRENT_PRICE_FRESHNESS_MISMATCH`;
- `CURRENT_PRICE_SESSION_MISMATCH`;
- executable-entry fact/freshness/market/session rules;
- RR arithmetic/guardrail rules;
- trigger/follow-through/setup/short-execution rules.

Direct validator tests with an unprojected invalid result must still demonstrate that the validator rejects the mismatch. The new projector exists before validation in the normal runtime path; it does not redefine what the validator accepts.

Do not modify the PAQS-E strategy Markdown, Doctrine or runtime prompt semantic content to solve this issue.

### 6.6 Required regression evidence

Add a regression matching the real failure class:

- Snapshot quote status = `AVAILABLE`;
- synthetic provider output says current freshness = `STALE`;
- strict provider schema/domain parsing succeeds;
- deterministic projector produces `FRESH` from the bound Snapshot;
- unchanged validator then passes this field;
- the test also proves the same unprojected bad result still yields `CURRENT_PRICE_FRESHNESS_MISMATCH` when calling the validator directly.

Also cover current session and price/timestamp projection without changing semantic decisions.

---

## 7. Protected semantics and files

Do not change or weaken:

- `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md`;
- runtime strategy Markdown;
- `src/ai_infra_quant/resources/paqs_e/runtime_prompt_v1.md` semantic content;
- `src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py`;
- `src/ai_infra_quant/database/migrations/versions/0002_task007b_paqs_e_decision_ledger.py`;
- accepted TASK-007A/007B/007C review evidence;
- Decision revision lineage;
- Snapshot construction semantics;
- no-live-trading/broker boundary.

No database migration is authorized or expected.

No new model is authorized.

No provider/model fallback is authorized.

No arbitrary provider URL is authorized.

No broker/account/execution behavior is authorized.

---

## 8. Required deterministic validation

Run at minimum:

- focused remediation unit tests for runtime source revision, DeepSeek research action normalization, long-running browser Analyze behavior and deterministic Snapshot projection;
- existing TASK-007C1 focused suite;
- full pytest suite;
- full browser suite;
- Windows launcher tests;
- Ruff check;
- Ruff format check;
- mypy;
- fresh SQLite migration/startup through `0002_task007b_paqs_e_ledger`;
- real Uvicorn `/health`, `/openapi.json`, `/`, PAQS-E configuration smoke;
- protected-file diff audit;
- secret scan.

All tests must use synthetic credentials except the separate opt-in live smoke.

---

## 9. Post-remediation live smoke gate

Ordinary Codex implementation must not require or solicit the user's real API key.

After deterministic remediation passes and the exact final SHA is pushed, final product acceptance still requires user-executed live evidence on that exact SHA.

### 9.1 Reasoning smoke

Preferred:

- `DeepSeek V4 Flash`;
- one supported Security;
- web research OFF;
- one explicit Analyze;
- allow the synchronous request to remain pending beyond 180 seconds if necessary;
- terminal `SUCCEEDED` Decision expected unless a genuine semantic validator issue remains.

If a semantic validator failure remains, capture only safe Run ID + validation issue; never relax validator merely to force success.

### 9.2 Research smoke

Then:

- `DeepSeek V4 Flash`;
- web research ON;
- one explicit Analyze;
- successful Decision plus frozen `auxiliary_context[]` with verified native source URLs/provenance expected.

Never expose, commit, log or screenshot the real API key.

No automatic paid retries.

---

## 10. Git preconditions

Before editing, Codex must verify:

```text
repository = ahhhhzzz/ai-infra-quant
branch = task/007c1-paqs-e-multi-model-web-research
HEAD = exact Remediation 01 Contract commit supplied by the handoff
Remediation 01 Contract parent = fc527c61fcdc2b4f54506dc5622f0b1faa6945d5
original implementation parent = 9f41016b2341e91ad2825b7f731bca4f378b0108
origin/roadmap/no-live-trading = 80f089bc2d285cca492c41aaeaf047e177bc2812
merge base with authoritative = 80f089bc2d285cca492c41aaeaf047e177bc2812
```

If any precondition is false, stop without implementation changes and report the mismatch.

Use a clean isolated checkout/worktree if necessary. Do not stash/reset/terminate unrelated work.

Commit and push only the existing TASK-007C1 task branch. No force-push. No merge.

---

## 11. Required final remediation report

The remediation implementation report must include:

1. original authoritative SHA;
2. original TASK-007C1 Contract SHA;
3. original implementation SHA `fc527c61fcdc2b4f54506dc5622f0b1faa6945d5`;
4. Remediation 01 Contract SHA;
5. exact final remediation implementation SHA;
6. parent / merge-base / ahead-behind evidence;
7. exact changed-file list relative to `fc527c61...`;
8. R1 source-revision handshake design and launcher behavior;
9. R2 exact DeepSeek action normalization and bounds;
10. R3 long-running browser behavior and proof that 180 seconds no longer aborts;
11. R4 exact deterministic fields projected and explicit fields not projected;
12. proof that validator rules/semantic strategy content were not weakened;
13. focused/full/browser/launcher/lint/format/mypy/startup results;
14. migration head confirmation;
15. secret/protected-file audit;
16. live-provider smoke evidence only if separately performed, with no credentials;
17. remaining limitations;
18. confirmation authoritative branch was not moved and no merge occurred.

Stop for independent re-review after pushing the remediation implementation.

Do not start another task.

---

## 12. External design reference for R2

Current DeepSeek Responses documentation checked at remediation issuance documents server-side `web_search_call.action` as `search`, `open_page`, or `find_in_page`, and documents server-side web search auto-continuation capped at 10 rounds.

Reference:

- `https://api-docs.deepseek.com/api/create-response/`
- `https://api-docs.deepseek.com/guides/responses_api/`

These are design evidence only and must not become runtime dependencies.