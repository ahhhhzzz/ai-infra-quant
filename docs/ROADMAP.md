# Read-Only PAQS Dual-Branch Decision-Terminal Product Roadmap

## Current delivery status — 2026-09-09

TASK-007A/B/C and user-accepted C1 are integrated. C2 is independently reviewed, user-closed and
integrated; accepted C2 runtime code is `d2d25efc79d2560a7ed09895c7dd7a2c1724aee9`, included in
`f78894bceb2900eff6e134bdf61f673309426355`. The earlier ADC sequencing baseline was
`722936984deac652b443eba132c69650653345e1`; the current handoff follows the ADC closeout below.
See [C2 review](reviews/TASK_007C2_INDEPENDENT_REVIEW.md),
[C2 closeout](decisions/TASK_007C2_CLOSEOUT_AND_006B1_HANDOFF_2026_09_08.md) and
[sequencing decision](decisions/ARCHITECTURE_DOCUMENTATION_CONSOLIDATION_BEFORE_006B1_2026_09_09.md).
The user acceptance screenshot showed a C1 branch without a SHA; it is not independent proof of
exact-C2 runtime identity. Historical execution and user acceptance remain separately attributed.

ADC-001 is **REVIEWED PASS / CLOSED / INTEGRATED** at accepted implementation
`66a3ca7bbff258665b25e5ab17231138bf3cc49f`; its F01 is closed with zero outstanding findings.
See [focused review](reviews/TASK_ADC_001_F01_FOCUSED_RE_REVIEW.md) and
[closeout/resumption decision](decisions/TASK_ADC_001_CLOSEOUT_AND_006B1_RESUMPTION_2026_09_09.md).
Current task: **006B1 — IMPLEMENTED / PENDING INDEPENDENT REVIEW**, not integrated.
The task started at `bed9059fd6ce6c0a7cd750376c972070db0a39dd`, with authoritative baseline
`02326a3bb19c2a89352d765f5331670b5f3f466d`, under the updated handoff. Explicit archive/replay
and additive 0004 are implemented; PAQS-Q successors, Paper/PnL and Phase 3/4 remain dormant.
See [006B1 implementation report](reports/TASK_006B1_IMPLEMENTATION_REPORT.md).
[ARCHITECTURE](ARCHITECTURE.md) is the current component/lifecycle entry point.

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
optional explicit factual research
        ↓
selected-model tool-free PAQS-E Narrative
        ↓
read exact text, immutable evidence and Narrative history
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

Current PAQS-E selects one of eleven registered models through provider-neutral ports and
compatible Responses/Chat adapters. OpenAI was the first historical adapter. Multi-model does
not mean voting, ensemble, fallback or retry. Ordinary Analyze is stateless: registered strategy
and Narrative prompt, frozen Snapshot and optionally accepted research enter tool-free final
reasoning. Research defaults OFF/reset on model change; history and refresh never Analyze.
Final text is preserved exactly without Legacy semantic validation. Integrity/hash checks do
not certify strategy reasoning, target/RR validity or strict historical As-Of safety.
See [ARCHITECTURE](ARCHITECTURE.md) for current research, credential and ledger boundaries.

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

#### TASK-006B1 — Local Market Data Store & Replay Foundation — IMPLEMENTED / PENDING INDEPENDENT REVIEW

Original contract commit: `d2bc397612a32adb2b5f78fec3ec894b3eacdb38`. Its bounded scope remains
valid. The [new closeout/resumption decision](decisions/TASK_ADC_001_CLOSEOUT_AND_006B1_RESUMPTION_2026_09_09.md)
lifts the earlier startup hold after ADC review/integration. Use the task branch addendum
`prompts/tasks/TASK-006B1_POST_ADC_HANDOFF_2026_09_09.md` and its exact baseline; do not reuse
the old start prompt or merge old 006B1 drafts.

Retained shared scope direction:

```text
canonical completed D1 persistence
canonical completed 1m persistence
provenance / retrieved_at / adjustment / quality
incremental ingest / dedupe
observation/version semantics
local deterministic replay
offline stored-capture reads consume no OpenD calls; live refresh behavior remains unchanged
```

TASK-006B1 becomes required before the product claims strict arbitrary historical As-Of replay/evaluation. It must not implement strategy logic.

### PAQS-E prioritized workstream

```text
TASK-007 — PAQS-E Expert Reasoning Workstream
```

`TASK-007` is umbrella only and must never itself become one implementation Task Contract.

#### TASK-007A — PAQS-E Doctrine Runtime, Structured Output & OpenAI Provider Port — COMPLETED / INTEGRATED

Final accepted/integrated SHA: `ca9712649b7ec26a67047e251200a50b353ad5b4`.

Historical contribution: registered strategy/prompt, Snapshot-bound provider-neutral structured
request/result, OpenAI Responses adapter and deterministic validator. This is retained Legacy
behavior; C1 Narrative is now the normal Analyze path. Historical contracts/reviews are linked
from [architecture history](ARCHITECTURE.md#9-historical-evolution-and-evidence).

#### TASK-007B — On-Demand PAQS-E Analysis Service & Immutable Decision Ledger — ACCEPTED / INTEGRATED

Exact reviewed implementation SHA: `7785cdeeacb14f0762f6104ed99f01b5e76d1dd3`. Independent review: `docs/reviews/TASK_007B_INDEPENDENT_REVIEW.md`.
The review verdict is PASS and this implementation is included in the integrated baseline above.
Historical contribution: explicit Snapshot-on-Demand structured Analyze, immutable runtime
artifacts, terminal Analysis Runs and validated Decision revisions. Provider/validation failures
create no Decision. These records and GETs remain retained Legacy evidence; old POST is normally
410 and hidden from OpenAPI. Current Narrative persistence is separate, with head 0003.

#### TASK-007C — PAQS-E User Dashboard — ACCEPTED / INTEGRATED

The accepted workbench delivered explicit Analyze, truthful failure states, immutable history,
known Run reads and frozen evidence charts. The original structured presentation remains Legacy.
C1 adds registered models, secure credentials, optional research and exact-text Narrative with
safe formatted/raw views. C2's credential layout and obsolete administration cleanup are reviewed,
user-closed and integrated. See [workbench guide](PAQS_E_WORKBENCH.md),
[C2 review](reviews/TASK_007C2_INDEPENDENT_REVIEW.md) and the current status above.

The usable current-analysis milestone is accepted. This is not strict historical replay,
backtesting, machine-certified Narrative strategy/RR or PAQS-Q completion.

#### TASK-ADC-001 — Architecture / Documentation Consolidation — REVIEWED PASS / CLOSED / INTEGRATED

Docs-only implementation `66a3ca7bbff258665b25e5ab17231138bf3cc49f`; no runtime change.
[Contract](../prompts/tasks/TASK-ADC-001_ARCHITECTURE_DOCUMENTATION_CONSOLIDATION.md),
[original report](reports/TASK_ADC_001_IMPLEMENTATION_REPORT.md),
[initial review](reviews/TASK_ADC_001_INDEPENDENT_REVIEW.md),
[focused PASS](reviews/TASK_ADC_001_F01_FOCUSED_RE_REVIEW.md) and
[authorized closeout](decisions/TASK_ADC_001_CLOSEOUT_AND_006B1_RESUMPTION_2026_09_09.md).
Historical pending-review statements are superseded by this closeout, not rewritten.

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
006B2 + 007A/B/C accepted and integrated
  → 007C1 user-accepted and integrated
  → 007C2 reviewed, user-closed and integrated
  → ADC-001 docs-only consolidation [reviewed, closed and integrated]
  → 006B1 bounded archive/replay [implemented; pending independent review; not integrated]
  → later approved strict historical As-Of / GoldSet work
```

PAQS-Q successors remain separately governed; 007D follows usable Q-side output.
The old 006B1 functional scope remains valid; its old starting SHA/prompt is not current authority.

### R20 product adoption after the first usable workbench

The user has authorized adopting R20's useful product capabilities, beyond a visual redesign.
The governing adoption record is `docs/decisions/R20_PRODUCT_ADOPTION_2026_09_07.md`; `docs/research/R20_ADOPTION_PLAN_AND_CODEX_PROMPT_ZH.md` is preserved as earlier planning context,
not an executable instruction or a replacement for current contracts.

TASK-007C delivers the bounded current-analysis workbench first. Later task contracts stage
prompt/model configuration, strategy-version inspection, research critique/council, reviewable
improvement proposals, sourced news context, simulated bookkeeping and local operational tooling
as assigned by the adoption record. TASK-007C1 has delivered its separately approved model/credential/research scope; C2 and ADC-001 are integrated; 006B1 is authorized next under its updated handoff;
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
exact final Narrative with strategy questions and uncertainty
immutable Narrative revisions and separate Legacy Decision reads
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
- One task passing does not approve the next task. The user explicitly authorized the ADC integration/006B1 handoff; 006B1 must follow that exact updated baseline and stop for its own review.
- Research memos/doctrines/amendments do not automatically authorize code changes; each Task Contract must state which research semantics it adopts.
- Documentation and requirements must preserve data freshness, strict As-Of/no-lookahead, non-fabrication and read-only safety rules.
- Provider behavior is bounded by accepted C1 contracts; the current model registry, endpoints and research lifecycle are not expanded by ADC.
- Keys are submitted through the local password form to OS-protected storage; status/read APIs never return secrets. OpenAI retains its read-only environment fallback.
- Secrets must never be committed, placed in browser persistence, logged, or stored in application databases/ledgers.
- Optional Phase 3/4 work stays dormant until explicitly reactivated.
