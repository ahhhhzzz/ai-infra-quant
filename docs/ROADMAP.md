# Read-Only PAQS Dual-Branch Decision-Terminal Product Roadmap

## Current delivery status — 2026-09-08

TASK-007A, TASK-007B and TASK-007C are accepted and integrated. TASK-007C1 is
**USER_ACCEPTED / FUNCTIONALLY_CLOSED**, including the user's Research-ON confirmation.
The authorized ordinary fast-forward of `roadmap/no-live-trading` from
`0c1713d4409c69a45f8ce5e37951bba72d73d819` to
`2cc4eeea3cc31d4fd1f1a4e9c1fbec237f82a2c4` has been executed and read back from GitHub.
The integrated application is the reviewed `3e98d8c5f9948dcaefe59eb3b7b847bd99ba8908` tree,
plus the independent review and user closeout documents. See the immutable
[R06 review](reviews/TASK_007C1_REMEDIATION_06_INDEPENDENT_REVIEW.md) and
[user closeout](decisions/TASK_007C1_CLOSEOUT_2026_09_08.md) for evidence attribution.
User acceptance is not a claim that the C2 implementer repeated paid provider tests or
independently recomputed the user's local Run hashes. Historical pending/not-merged statements
in original contracts, reports and reviews describe their original checkpoints and remain unchanged.

TASK-007C2 is **implemented / pending independent review** on its task branch; it is not
independently passed or integrated. Its bounded change repairs the credential dialog and removes
the old opening portfolio cards and duplicate administration UI. The main watchlist, market
quality/provenance, history and frozen evidence remain available. Backend compatibility APIs,
existing databases, opening seed values and migrations 0001/0002/0003 are preserved; head remains
`0003_task007c1_narrative_ledger`. See the [C2 report](reports/TASK_007C2_IMPLEMENTATION_REPORT.md).

The normal explicit Analyze path is Narrative-first: one immutable Snapshot, optional bounded
research, tool-free final reasoning, and exact final text persisted in the Narrative Ledger.
Saving complete prose does not certify strategy semantics, Entry/Holder judgments or RR by machine.
The legacy structured validator is unchanged and historical structured Runs/Decisions remain readable.
Research defaults OFF and resets OFF on model changes. Refresh, credentials and history never Analyze.
The product remains a read-only market and decision-support terminal, without initial asset cards
in its normal UI. Paper/PaperFill, performance statistics, TASK-006B1, PAQS-Q successors, TASK-007D,
and Phase 3/4 are not activated by this work; broker/account/trading capabilities remain forbidden.

Status: **AUTHORITATIVE — local read-only PAQS-E prioritized MVP, parallel PAQS-Q reference branch, and optional Phase 3/4 extensions**

Decisions:

- `MTF-001`, approved 2026-09-01 — daily + completed 1-minute read-only market-data direction;
- `PAQS-MVP-001`, approved 2026-09-02 — focused PAQS decision-terminal MVP, bounded PAQS workstreams, optional Phase 3/4 extensions;
- `PAQS-DUAL-001`, approved 2026-09-03 — dual PAQS-E / PAQS-Q architecture, Snapshot-on-Demand execution, PAQS-E implementation priority.

Decision records:

- `docs/decisions/PAQS_MVP_SCOPE_REDUCTION.md`
- `docs/decisions/PAQS_DUAL_BRANCH_ARCHITECTURE.md`
- `docs/decisions/R20_PRODUCT_ADOPTION_2026_09_07.md` — user-authorized R20 product-capability adoption, staged through bounded tasks

Product: **Personal Quantitative Research and AI-Assisted Decision-Support Tool**

## 1. Authority, supersession, and history

This Roadmap governs future product scope after the accepted Phase 1 baseline.

`MTF-001` superseded the earlier completed-daily-only future direction without rewriting history. `PAQS-MVP-001` superseded the earlier assumption that the current product must continue through a broad paper-tracking and full-backtesting platform before it can be considered complete. `PAQS-DUAL-001` now supersedes the future assumption that one single deterministic PAQS engine must own all Structure/Event/Setup/Advisory behavior.

Historical facts remain unchanged:

- Phase 0 was completed historically;
- Phase 1 was implemented and independently accepted;
- the reviewed Phase 1 commit is `f6decf2fbe171c1b9eb46340a9174bc21f293ede`;
- Phase 1 status remains PASS;
- both Phase 1 review files remain immutable evidence;
- TASK-003 completed the bounded Phase 2 Futu quote-only market-data PoC;
- TASK-004 implemented the provider-neutral read-through market-data backend;
- TASK-005 implemented the market-data Dashboard;
- TASK-005A implemented the Windows one-click launcher;
- TASK-005B implemented bounded long Daily history, recent minute history, US `Session.ALL`, incremental browser refresh, and chart-time semantics;
- TASK-006A implemented the dynamic US/HK PAQS input foundation and passed focused remediation;
- TASK-006B implemented and independently passed its deterministic Structure Engine contract, was integrated at `96747041ef0ff8c00937c5dd5e80cb4c5c28c17c`, and subsequently produced `STRUCTURE_CONCERNS_FOUND` in the mandatory real-market semantic checkpoint;
- TASK-006B2 implemented the immutable Snapshot-on-Demand factual market snapshot, passed remediation and final independent review, and is accepted/integrated at `5f996aebb012cc0884d912f6f3eb71c32e9fd627`.

The correct historical TASK-006B status is therefore:

```text
TASK-006B deterministic implementation: PASS / integrated
TASK-006B real-market semantic checkpoint: STRUCTURE_CONCERNS_FOUND
```

The checkpoint does not erase accepted deterministic implementation evidence and does not constitute semantic acceptance of the old single-engine structure model.

Earlier Phase 1 broker/provider abstractions are historical artifacts, not authority to implement brokerage-account or broker-write behavior.

## 2. Current product objective

The committed product remains a local-first, single-user, read-only personal investment decision terminal.

Under `PAQS-DUAL-001`, PAQS is a family with two parallel strategy branches:

```text
                         PAQS
                          |
              +-----------+-----------+
              |                       |
           PAQS-E                   PAQS-Q
   Expert Reasoning Engine    Quant Decision Engine
        LLM-native            deterministic/reference
```

Current implementation priority is **PAQS-E**. PAQS-Q remains a valuable deterministic reference/scanner branch whose exact methods may evolve later under separate research and Task Contract governance.

The product should let the user:

```text
add supported US/HK securities
        ↓
view truthful read-only market data
        ↓
explicitly request Analyze
        ↓
freeze one immutable current Market Snapshot
        ↓
PAQS-E expert analysis and/or PAQS-Q machine analysis
        ↓
see context / key levels / setup / invalidation / target / RR / advisory
        ↓
compare branches where both are available
        ↓
human makes the capital decision manually outside the app
```

All real trading is performed manually by the user in the broker's official client.

The application never needs brokerage-account knowledge to produce either branch's decision support.

## 3. Market-data and supported-security direction

Market-data access and brokerage-account access remain separate concepts.

The approved provider path is independent read-only market data. Current implementation uses Futu OpenD quote-only APIs behind a provider-neutral application/core boundary.

Existing Phase 2 capabilities include:

- latest quote and market state;
- completed Daily OHLCV;
- recent completed 1-minute OHLCV;
- approximately 1300 Daily sessions for Dashboard full load;
- recent 30 market-local calendar days of minute history;
- Futu `Session.ALL` for US minute history;
- normal HK provider sessions;
- explicit missing/unavailable/error semantics;
- no production market-data persistence.

The initial PoC symbols were:

```text
US.AVGO
US.VRT
HK.09698
```

TASK-006A replaced the hard-coded PoC restriction with a provider-validated user-manageable supported US/HK watchlist. Dynamic security support does not authorize arbitrary global markets.

Provider-specific market-data code remains under `integrations/`; PAQS-E, PAQS-Q, Dashboard, Risk, optional future Performance/Backtest, and core domain logic consume provider-agnostic canonical facts.

## 4. Dashboard and refresh contract

The existing market Dashboard remains retained:

- security selector;
- latest price and market status;
- separate Daily and 1-minute charts;
- volume;
- market-data timestamps and status;
- manual refresh;
- approximately 60-second visible-page refresh;
- automatic-refresh countdown;
- no overlapping requests;
- pause while hidden and immediate refresh on visibility return;
- pannable long Daily/minute chart history;
- local vendored chart dependency;
- Windows one-click launch path.

Market-data display refresh and strategy analysis are separate processes.

The MVP strategy runtime is **Snapshot-on-Demand**, not continuous/background signal generation:

```text
user requests Analyze
    -> freeze one snapshot
    -> return one result
    -> run ends
```

A new quote or newly completed bar does not mutate an existing PAQS-E/PAQS-Q decision. The user must explicitly request Analyze again to obtain a new judgment.

Future PAQS Dashboard work is additive. It must not reintroduce trading controls or imply a real brokerage position.

Closing the page requires no background strategy processing.

## 5. Time, data-quality, Snapshot and PAQS input direction

Quotes, bars, snapshots and later PAQS outputs distinguish their own timestamps. At minimum existing market data already distinguishes:

```text
latest_quote_at
latest_completed_minute_bar_at
latest_completed_daily_session
```

Immutable TASK-006B2 analysis snapshots provide `as_of_timestamp`, provenance, coverage, calculation/creation time and stable `snapshot_hash` identity. Future PAQS decisions bind to that exact snapshot identity.

Rules remain fixed:

- unfinished minute bars are never treated as completed;
- latest/intraday price is never called a final daily close;
- polling cadence and provider latency are separate facts;
- no market value is fabricated;
- financial values use Decimal where deterministic financial arithmetic applies;
- aware UTC is used for instants and IANA market timezones for session/calendar semantics;
- strict no-lookahead / As-Of discipline applies to both PAQS branches.

Current shared structural evidence roles are:

```text
HTF = completed W1
STF = completed D1
TTF = completed 30m REGULAR-session bars
```

W1 is derived from completed D1; 30m is derived from completed 1-minute data with market-aware US/HK session rules. H1/H4 are not current MVP requirements.

TASK-006B2 includes the latest quote only as explicitly reference-only current-price context. It may not confirm completed-bar Pivot, Breakout, Trigger, Follow-through, Setup or other structural evidence. The snapshot also preserves quote provider-delay, market-state, calendar, adjustment, quality and per-timeframe evidence provenance without applying PAQS-E strategy policy.

Strict arbitrary historical point-in-time replay is not yet an implemented current capability. Provider `PROVIDER_QFQ_CURRENT` data must not be falsely described as strict point-in-time corporate-action-safe history.

## 6. PAQS-E, PAQS-Q and numerical Score relationship

### PAQS-E — prioritized Expert Reasoning branch

PAQS-E is the LLM-native Naked Price Action Expert Reasoning Engine.

The semantic hierarchy adopted by TASK-007A and retained by later bounded PAQS-E tasks is:

```text
docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md
    -> primary PAQS-E runtime semantic strategy authority adopted at the TASK-007A registered hash

PAQS_E_NAKED_PRICE_ACTION_DOCTRINE.md
    -> conceptual/doctrine foundation

PAQS v0.3.x research/formalization
    -> historical guardrail / formalization / audit / terminology reference

PAQS-Q research
    -> separate deterministic/reference branch authority only when separately adopted
```

TASK-007A explicitly adopted the registered Master Spec version/hash. The research document itself still does not authorize unrelated implementation or later edits to the strategy; later tasks consume the accepted runtime contract.

PAQS-E should reason semantically over:

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

It must retain hard discipline such as strict As-Of, no hindsight, Event != Setup != Advisory, Trigger != Follow-through, Entry != Holder, no target shopping, no retroactive invalidation widening, and permission to output `NO_TRADE` / `WATCH` / `WAIT_RETEST` / `UNCERTAIN`.

PAQS-Q exact thresholds must not silently become PAQS-E strategy rules.

Initial PAQS-E provider architecture is model-provider-agnostic. OpenAI is the accepted first adapter. The first MVP does not require multi-model voting or ensemble behavior.

Ordinary PAQS-E Analyze calls are stateless/fresh by default. The model receives only product-controlled snapshot facts plus approved doctrine/prompt/output contract. No web/browser/search tools, hidden conversational memory, previous PAQS-E decision, broker data, or future bars are supplied in the initial MVP.

### PAQS-Q — deterministic Quant Decision branch

PAQS-Q is the deterministic machine/reference/scanner branch.

Its priorities include:

```text
engineering stability
reproducibility
no-lookahead
bounded machine structure
replayability
auditability
robustness diagnostics
future large-universe scanning
```

PAQS-Q strategy methods may evolve later without redefining PAQS-E.

### Numerical score

The approved historical score decomposition from `MTF-001` remains recorded for compatibility:

```text
Composite Quant Score
=
Daily Base Score
+
Intraday Minute Adjustment
```

No numerical score is the universal causal authority over both PAQS branches.

A future score/ranking layer may summarize deterministic PAQS-Q states or help prioritize already-defined candidates. It may never:

- fabricate an Event or Setup;
- bypass structural invalidation;
- bypass RR;
- convert missing data into zero;
- convert `NO_TRADE` into `LONG_READY`;
- hide PAQS-E / PAQS-Q disagreement behind an average;
- claim probability without a separately validated/calibrated model.

Exact Quality/Composite formulae remain separately unapproved.

## 7. Authoritative phase model and current Phase 2 workstreams

The authoritative phase sequence remains exactly Phase 0 through Phase 4. No Phase 5 exists.

### Phase 0 — Product Definition & Architecture

Historically completed. Later scope decisions do not rewrite historical evidence.

### Phase 1 — Foundation

Completed and independently accepted. Preserve accepted FastAPI/SQLite/SQLAlchemy/Alembic foundation, deterministic migration 0001, Decimal/UTC invariants, Security identity, Watchlist, opening accounting facts, accepted APIs/frontend, tests and review evidence.

### Phase 2 — Market Data, Dashboard & Dual-Branch PAQS Decision Terminal

Phase 2 remains the active and committed product phase.

Completed increments:

```text
TASK-003   Futu quote-only Market Data PoC
TASK-004   Provider-neutral Market Data Backend
TASK-005   Market Data Dashboard
TASK-005A  Windows one-click launcher
TASK-005B  Expanded history + US 24H minute semantics
TASK-006A  Dynamic US/HK Securities & PAQS Input Foundation
TASK-006B  Historical deterministic PAQS Structure Engine implementation
TASK-006B2 Snapshot-on-Demand Current Market Snapshot
```

Accepted/integrated evidence:

- TASK-006A remediation integrated at `7909f1c04f7049cf1ccec78a3d5023ae801b7177`;
- TASK-006B deterministic implementation integrated at `96747041ef0ff8c00937c5dd5e80cb4c5c28c17c`;
- TASK-006B real-market validation status: `STRUCTURE_CONCERNS_FOUND`;
- TASK-006B2 final independent PASS and integration at `5f996aebb012cc0884d912f6f3eb71c32e9fd627`; evidence: `docs/reviews/TASK_006B2_INDEPENDENT_REVIEW.md`.

### Shared PAQS foundation tasks

#### TASK-006B2 — Snapshot-on-Demand Current Market Snapshot — COMPLETED / INTEGRATED

Accepted scope:

- one immutable current analysis snapshot from existing accepted current/read-through facts;
- strict factual `as_of_timestamp` boundary;
- canonical completed W1/D1/M30 payloads with caps 156/500/200;
- latest quote and market state as explicitly `reference_only` facts;
- session/calendar/coverage/quality/adjustment/provider provenance;
- machine-readable W1/D1/M30 evidence status and quote provider-delay provenance;
- canonical serialization and SHA-256 `snapshot_hash`;
- W1 nominal future interval geometry preserved and hashed without advancing Snapshot As-Of;
- no PAQS-E or PAQS-Q strategy judgment;
- no LLM call;
- no market-data persistence requirement.

Final accepted/integrated SHA: `5f996aebb012cc0884d912f6f3eb71c32e9fd627`.

Independent final review verdict: `PASS`.

#### TASK-006B1 — Local Market Data Store & Replay Foundation — PLANNED / DEFERRED BEHIND INITIAL PAQS-E CURRENT MVP

Retained shared scope direction:

```text
canonical completed D1 persistence
canonical completed 1m persistence
provenance / retrieved_at / adjustment / quality
incremental ingest / dedupe
observation/version semantics
local deterministic replay
lower repeated OpenD historical consumption
```

TASK-006B1 becomes required before the product claims strict arbitrary historical As-Of replay/evaluation. It must not implement strategy logic.

### PAQS-E prioritized workstream

```text
TASK-007 — PAQS-E Expert Reasoning Workstream
```

`TASK-007` is umbrella only and must never itself become one implementation Task Contract.

#### TASK-007A — PAQS-E Doctrine Runtime, Structured Output & OpenAI Provider Port — COMPLETED / INTEGRATED

Final accepted/integrated SHA: `ca9712649b7ec26a67047e251200a50b353ad5b4`.

Accepted scope:

- versioned runtime package explicitly adopting the accepted PAQS-E Context-Free Master Spec;
- compact doctrine/runtime instructions, canonical reasoning questions and hard guardrails;
- PAQS-E request domain bound to exact Snapshot identity;
- strict structured output schema;
- provider-neutral `PaqsEReasoningProvider` port;
- first adapter: OpenAI only;
- configurable server-side model identifier;
- user-supplied OpenAI API credential kept server-side and never committed, persisted in application data, exposed to frontend clients, returned by APIs, or logged;
- no web/browser/tool calls supplied to the model in the first MVP;
- stateless/fresh analysis request semantics;
- deterministic schema/fact/RR post-validation;
- no continuous/background analysis;
- no broker behavior.

#### TASK-007B — On-Demand PAQS-E Analysis Service & Immutable Decision Ledger — ACCEPTED / INTEGRATED

Exact reviewed implementation SHA: `7785cdeeacb14f0762f6104ed99f01b5e76d1dd3`. Independent review: `docs/reviews/TASK_007B_INDEPENDENT_REVIEW.md`.
The review verdict is PASS and this implementation is included in the integrated baseline above.
Implementation follows `prompts/tasks/TASK-007B_ON_DEMAND_PAQS_E_ANALYSIS_DECISION_LEDGER.md`. Reviewed scope:

- explicit user-triggered Analyze service/API;
- one request uses one immutable snapshot;
- one PAQS-E result per request;
- immutable decision persistence/revision semantics;
- snapshot/doctrine/prompt/provider/model metadata;
- truthful provider-unavailable behavior;
- no automatic re-analysis on market-data refresh.

Terminal Analysis Runs and exact request/strategy/prompt evidence are append-only. Successful
Decisions append revisions within `(security_id, strategy_id)`; provider/validation failures
persist a failed run without a Decision. Bounded read APIs support TASK-007C. The independent
review covers this exact implementation SHA; the current integrated status is recorded above.

#### TASK-007C — PAQS-E User Dashboard — ACCEPTED / INTEGRATED

Task Contract: `prompts/tasks/TASK-007C_PAQS_E_USER_DASHBOARD.md`.
The accepted workbench retains JavaScript/CSS and vendored Lightweight Charts, explicit Analyze,
truthful failure states, immutable history, known Run lookup and frozen evidence charts.
TASK-007C1 extends the accepted UI with registered models, secure credentials, optional bounded
research and Narrative-first results; TASK-007C2 cleans up presentation and awaits review.
The original 007C structured presentation remains available for legacy Decision history.
See `docs/PAQS_E_WORKBENCH.md` for the current workflow and limitations.

Authorized scope direction:

- user-visible `Analyze with PAQS-E` action;
- snapshot/as-of metadata;
- one-line thesis;
- HTF/STF/TTF context;
- 1–4 key decision levels;
- location;
- event/setup/stage;
- trigger/follow-through;
- entry advisory and holder advisory;
- invalidation;
- T1/T2 and deterministic RR;
- chase/poor-entry warning;
- uncertainty/conflicting evidence;
- alternative interpretation;
- next evidence needed;
- prior immutable decisions displayed separately when explicitly requested;
- no real-order controls.

TASK-007C has passed independent review and integration, delivering a usable **current Snapshot-on-Demand PAQS-E MVP**. Historical As-Of evaluation remains a later validation capability and does not need to block current-analysis usability.

#### TASK-007D — Dual-Branch Comparison / Disagreement Dashboard

Deferred until PAQS-Q produces usable advisory/reference output.

Planned scope:

- same snapshot identity for Q/E comparison;
- outputs remain separate;
- alignment/disagreement surfaced explicitly;
- no synthetic averaging into one decision score.

### PAQS-Q deterministic/reference workstream

The previously planned future single-engine `TASK-006C`, `TASK-006D`, and `TASK-006E` wording is superseded for future implementation by:

```text
TASK-006B-Q — PAQS-Q Structure Stabilization
TASK-006C-Q — PAQS-Q Event Engine
TASK-006D-Q — PAQS-Q Setup, Risk & Setup-Specific Quant Confirmation
TASK-006E-Q — PAQS-Q Advisory / Scanner Presentation
```

PAQS-Q concrete semantics still require explicit approval before implementation. PAQS-Q work must not block an otherwise safe PAQS-E MVP and must not redefine PAQS-E strategy authority.

### Recommended current implementation order

```text
PAQS-DUAL-001 docs migration                  [DONE]
        ↓
TASK-006B2 Snapshot-on-Demand Market Snapshot [DONE]
        ↓
TASK-007A Doctrine Runtime + Structured Output + OpenAI Provider Port [DONE]
        ↓
TASK-007B On-Demand Analysis + Immutable Decision Ledger [ACCEPTED / INTEGRATED]
        ↓
TASK-007C PAQS-E Dashboard / Analyze workflow [ACCEPTED / INTEGRATED]
        ↓
usable current-analysis PAQS-E MVP
        ↓
TASK-006B1 Local Market Data Store + Replay Foundation
        ↓
PAQS-E strict historical As-Of / Gold-Set evaluation expansion

PAQS-Q tasks proceed separately as reference/scanner engineering.
TASK-007D follows only after PAQS-Q is usable.
```

### R20 product adoption after the first usable workbench

The user has authorized adopting R20's useful product capabilities, beyond a visual redesign.
The governing adoption record is `docs/decisions/R20_PRODUCT_ADOPTION_2026_09_07.md`; `docs/research/R20_ADOPTION_PLAN_AND_CODEX_PROMPT_ZH.md` is preserved as earlier planning context,
not an executable instruction or a replacement for current contracts.

TASK-007C delivers the bounded current-analysis workbench first. Later task contracts stage
prompt/model configuration, strategy-version inspection, research critique/council, reviewable
improvement proposals, sourced news context, simulated bookkeeping and local operational tooling
as assigned by the adoption record. TASK-007C1 has delivered its separately approved model/credential/research scope; only TASK-007C2 UI cleanup is authorized now;
paper/NAV remains dormant Phase 3 work. None authorizes extra Analyze fields beyond the current four-field Narrative request.
PAQS-E doctrine/guardrails, explicit Analyze, immutable evidence, Futu quote-only access and no real
account/execution boundary remain authoritative. No R20 online Python execution, OKX execution,
automatic strategy mutation or secret-storage implementation is adopted wholesale.

A later Vue migration may be considered only in a bounded frontend contract with demonstrated
component-reuse benefit. R20 `.vue` files are not drop-in components for the current frontend.
Copied substantive code must retain its license/attribution and an exact source-commit record.

### Phase 3 — Dormant Optional Research / Paper Extensions

Phase 3 remains a valid extension slot but is **not part of the current committed MVP sequence**.

Possible future work may be reactivated only by explicit user approval, such as:

- richer research extensions;
- simulated Paper Portfolio;
- PaperFill bookkeeping;
- paper NAV/performance;
- position sizing;
- portfolio exposure/correlation controls.

No placeholder Phase 3 implementation is required now.

### Phase 4 — Dormant Optional Validation / Backtest / Analytics Extensions

Phase 4 remains the final possible product phase but is **not required for current product usability**.

Possible future work may be reactivated only by explicit user approval, such as:

- deterministic point-in-time backtesting using legitimate data;
- transaction-cost assumptions;
- benchmark comparison;
- drawdown/volatility/turnover;
- attribution/exposure;
- strategy comparison/parameter analysis;
- reproducible research reports.

Current recent-minute capability does not imply historical minute replay, tick simulation, or market-microstructure storage.

## 8. Current MVP scope disposition

### KEEP / PRIORITIZE

```text
local single-user app
read-only market data
Dashboard
Windows launcher
dynamic supported US/HK watchlist
Snapshot-on-Demand analysis
PAQS-E Naked Price Action expert analysis
structured invalidation / target / RR / advisory
immutable PAQS-E decision revisions
human-readable explanations and uncertainty
```

### KEEP AS PARALLEL REFERENCE WORK

```text
PAQS-Q deterministic structure/events/setups/risk/advisory
future scanner / machine baseline
quantitative evidence
large-universe deterministic screening later
```

### SIMPLIFY

```text
Composite Score -> derived/reference layer, not universal causal strategy
ranking -> lightweight decision prioritization, not portfolio optimizer
validation -> proportional strategy-specific validation rather than one institutional platform
```

### OPTIONAL FUTURE EXTENSIONS

```text
Paper Portfolio
Paper Accounting / PaperFill bookkeeping
Position sizing
Portfolio optimization
Full backtesting platform
Performance attribution/exposure analytics
Large research-report / parameter-analysis suite
multi-model comparison beyond simple provider abstraction
```

These are not current committed work but may be attached later through Phase 3/4 or bounded Phase 2 extensions without changing the permanent read-only/no-broker boundary.

## 9. Permanently removed / forbidden product scope

The following remain permanently outside the product rather than merely deferred:

```text
real completed-trade entry/import
real external account observation
broker account synchronization
brokerage cash/positions/orders/trades
real-account matching/discrepancy handling
real portfolio tracking
trade sizing from real brokerage holdings
real broker fees/taxes/settlement synchronization
broker-write adapters
place_order / cancel_order / modify_order
real-order API/UI
Live OMS/EMS
trade-password unlock
execution workers/retries/recovery/kill switches
autonomous/unattended trading
```

Unnecessary infrastructure remains excluded: microservices, Kafka, distributed workers, Kubernetes, multi-tenancy, 24/7 execution infrastructure, tick persistence, institutional OMS, and large generic provider frameworks.

## 10. Governance and stop conditions

- Phase 1 remains accepted and immutable as historical evidence.
- `PAQS-DUAL-001` changes future product/task direction without rewriting accepted history.
- `TASK-006` remains an umbrella identifier for historical/planned Q-side bounded work; Codex must never be told to implement it as one task.
- `TASK-007` is the PAQS-E umbrella identifier only; Codex must never be told to implement TASK-007 as one task.
- TASK identifiers recorded in this Roadmap are scope direction, not implementation authority.
- Each implementation task requires an explicit user-approved Task Contract stored on its own task branch.
- Codex receives only a short prompt pointing to repository, task branch, exact authoritative base SHA and Task Contract path.
- Codex stops after its approved task and pushes only that task branch.
- Independent GitHub review is required before remediation/integration.
- One task passing does not by itself approve the next task. TASK-007C2 has separate explicit authorization; its committed contract and exact integration prerequisite govern this execution.
- Research memos/doctrines/amendments do not automatically authorize code changes; each Task Contract must state which research semantics it adopts.
- Documentation and requirements must preserve data freshness, strict As-Of/no-lookahead, non-fabrication and read-only safety rules.
- Accepted OpenAI integration remains bounded by TASK-007A; this Roadmap does not authorize additional provider capabilities or calls beyond later approved contracts.
- OpenAI API credentials are user-supplied locally, server-side only, and must never be committed, persisted in application data, exposed to frontend clients, returned by APIs, or logged.
- API keys/secrets must never be committed to GitHub or exposed to the frontend.
- Optional Phase 3/4 work stays dormant until explicitly reactivated.
