# AI Infra Quant Platform — Master Specification v3.2

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

Status: **AUTHORITATIVE — PAQS-E Snapshot-on-Demand MVP; TASK-007A/B/C integrated; TASK-007C1 user-accepted/integrated; TASK-007C2 pending review**

Superseding future-scope decisions:

- `MTF-001` in `docs/ROADMAP.md`, approved 2026-09-01;
- `PAQS-MVP-001` in `docs/ROADMAP.md`, approved 2026-09-02;
- `PAQS-DUAL-001` in `docs/ROADMAP.md`, approved 2026-09-03;
- R20 product adoption: `docs/decisions/R20_PRODUCT_ADOPTION_2026_09_07.md`.

Decision record: `docs/decisions/PAQS_MVP_SCOPE_REDUCTION.md`

## 0. Authority, precedence, and history

Instruction precedence is:

1. current explicit user instruction;
2. root `AGENTS.md`;
3. `docs/ROADMAP.md`;
4. this specification;
5. the current explicitly approved Task Contract;
6. other documentation.

Phase 0 remains historically completed. Phase 1 remains accepted at reviewed commit `f6decf2fbe171c1b9eb46340a9174bc21f293ede`; its PASS status, plan, implementation, tests and two review files remain unchanged.

Completed Phase 2 increments include TASK-003, TASK-004, TASK-005, TASK-005A and TASK-005B. `PAQS-MVP-001` changes only future committed scope and does not rewrite those accepted increments.

## 1. Product objective and boundary

Build a local-first, single-user personal quantitative research and decision-support terminal.

The committed MVP should let the user:

- maintain supported US/HK securities in a local watchlist;
- inspect truthful latest/Daily/recent-minute market data;
- explicitly request current PAQS-E expert analysis over one immutable market snapshot;
- read model-generated Narrative analysis and separately retained legacy structured context/levels/RR;
- retain the historical deterministic PAQS structure implementation as PAQS-Q reference work;
- receive conditional Entry and Holder advisory;
- review immutable analysis evidence and Decision revisions;
- add later product capabilities only through the R20 adoption record and bounded contracts.

All real trading is performed manually in the broker's official client.

The product never accesses a brokerage account, real cash, real positions, completed broker orders or real trades. It does not import or match real-account state and does not need to know whether the user acted on an advisory output.

> 用户在券商官方客户端手工完成所有真实交易。

The original PoC tracked set begins with:

- `US.AVGO`
- `US.VRT`
- `HK.09698`

TASK-006A implemented dynamic supported US/HK security management; these three symbols are initial PoC/seed inputs, not a permanent restriction.

## 2. Operating model

During an active visible Dashboard session, market-data display may refresh approximately every
60 seconds or on manual request, preserving the accepted hidden-page pause, no-overlap and
Security-generation guards. This refresh obtains bounded quotes/completed Daily/minute data,
validates provenance/session/quality, and redraws charts; it never triggers PAQS-E reasoning.

Only an explicit Analyze action freezes one current TASK-006B2 snapshot, optionally obtains bounded
research, invokes tool-free Narrative reasoning and persists a terminal Narrative Run and, on success,
an exact-text Narrative Result. The accepted TASK-007A/B structured runtime/ledger is historical.
Changing Security/model/strategy, loading a page, reading history or receiving a new quote does not
implicitly Analyze. A prior Decision keeps its original snapshot/as-of identity and is never updated
by chart refresh. No hidden Decision memory or background strategy execution is introduced.

Ordinary HTTP/REST remains sufficient for the local MVP; no streaming execution infrastructure is required.

## 3. Scope and non-goals

### Current committed MVP scope

- local single-process modular monolith;
- SQLite runtime and FastAPI/local frontend;
- independent read-only market-data provider path;
- bounded Daily history and recent completed 1-minute OHLCV;
- latest price and market status;
- separate Daily/minute charts and volume;
- dynamic supported US/HK watchlist implemented under TASK-006A;
- PAQS input/session/calendar foundation implemented under TASK-006A;
- accepted TASK-006B2 factual snapshots and TASK-007A structured PAQS-E runtime;
- accepted/integrated TASK-007B immutable structured evidence and TASK-007C workbench;
- accepted/integrated TASK-007C1 Narrative-first analysis, secure models and optional research;
- implemented TASK-007C2 credential layout and administration cleanup, pending independent review;
- conditional Entry/Holder advisory;
- lightweight explanation/reason codes;
- immutable Decision history; optional Quality/Ranking only under a separate approved contract;
- user/engineering documentation for PAQS.

### Optional future extensions, not committed MVP work

These may be reactivated only through later explicit Phase 3/4 approval:

- simulated Paper Portfolio / PaperFill bookkeeping;
- paper NAV/performance;
- position sizing;
- portfolio exposure/correlation controls;
- broader research-factor expansion;
- full deterministic backtesting platform;
- transaction-cost/benchmark engines;
- attribution/exposure/turnover analytics;
- portfolio optimization;
- large parameter-analysis/reporting suites.

No placeholder implementation is required merely to anticipate them.

### Permanently outside product scope

- any brokerage-account connection or observation;
- real cash/positions/trades/import/synchronization/account matching;
- application-submitted real orders or real-order UI/API;
- broker-write adapters or `place_order`, `cancel_order`, `modify_order`;
- trading-password unlock, buying-power reservation, execution workers/retries/recovery/kill switches;
- live OMS/EMS or autonomous/unattended trading;
- microservices, Kafka/queues, distributed workers, Kubernetes, multi-tenancy, cloud HA or 24/7 execution infrastructure;
- tick/order-book persistence as an MVP requirement;
- any authoritative Phase after Phase 4.

Read-only market analysis and conditional advisory are research capabilities, not execution.

## 4. Engineering principles

1. PAQS/Strategy and other core research logic remain provider-agnostic.
2. Provider-specific adapters live under `integrations/` and expose read-only capabilities only.
3. Financial values use Python `Decimal`, never binary float.
4. SQLite persists exact financial values under the accepted Decimal design when persistence is required.
5. Missing, delayed, stale, unavailable, unsupported and erroneous data are explicit and never fabricated.
6. Instants are aware UTC; market sessions retain local date, IANA timezone and calendar semantics.
7. Point-in-time research requires data legitimately available at the calculation cutoff.
8. PAQS must never use unfinished bars as completed facts.
9. Advisory output has no external effect and creates no real-position fact.
10. Every implementation task is separately approved, tested, reviewed and stopped.
11. Product-scope reduction must not justify coupling PAQS to one provider or hard-coded symbol set.

## 5. Target architecture

```text
Browser
  -> local FastAPI presentation
      -> application use cases
          -> market-data queries
          -> supported-security/watchlist administration
          -> PAQS input/session/calendar preparation
          -> explicit PAQS-E Analyze -> optional research -> tool-free Narrative provider
          -> immutable Narrative Run / exact-text Result and user-requested history
          -> legacy structured Run / Decision reads with unchanged historical validator
          -> separately scoped PAQS-Q reference work
              -> SQLite only where approved persistence exists

Independent read-only Market Data Provider
  -> provider adapter under integrations/
      -> canonical quotes, Daily bars, completed minute bars,
         market status and approved calendar/security metadata

Human boundary
  advisory display -> user -> broker official client
```

There is no brokerage-account path and no path from an advisory result to an external command.

## 6. Module boundaries

| Module/port | Owns | Must not own or call |
|---|---|---|
| Dashboard | Market views, watchlist UI, polling, later PAQS presentation | Provider SDK objects, real account/execution concepts |
| Market-data port | Canonical quote, Daily/minute bars, market status and approved calendar/security metadata | Brokerage account access or execution |
| PAQS input foundation | W1/D1/30m derivation, session/calendar/coverage/adjustment metadata | Provider SDK models, broker/account state |
| PAQS-E Strategy | Snapshot-bound expert reasoning through accepted runtime/port plus deterministic guardrails | Provider SDKs in core, hidden history, automatic reruns, broker/accounting mutation |
| PAQS-Q | Separate deterministic/reference work under its own bounded contracts | Redefining PAQS-E semantics or blocking the current PAQS-E MVP |
| Decision Ledger | Immutable runtime artifacts, terminal Analysis Runs and validated Decision revisions | Strategy editing, hidden model memory, market-data store or execution facts |
| Quality/Ranking | Optional derived prioritization of already-defined PAQS state | Creating setups, bypassing PAQS hard gates |
| Portfolio/Accounting | Accepted Phase 1 historical foundation; optional later paper work only if reactivated | Real-account state, PAQS score mutation |
| Performance/Backtest | Dormant optional future extensions only if reactivated | Production mutation, fabricated historical data |

Only the composition root selects a provider. Core modules do not read environment variables, import provider SDKs or branch on provider names.

## 7. Market-data, time and PAQS input contract

The existing provider boundary supports equivalents of `get_latest_quote()`, `get_daily_bars()`, `get_minute_bars()` and `get_market_status()` through TASK-004/TASK-005B.

TASK-006A extends the provider-neutral boundary for supported dynamic US/HK equities and
trading-calendar/session metadata. Provider quote validation occurs before atomic local
Security/Watchlist mutation and never verifies brokerage tradability. This does not authorize
account access.

Current Dashboard behavior retains:

- up to 1500 requested completed Daily sessions, with 1300 used by full load;
- recent 30 market-local calendar days of completed minute data;
- Futu `Session.ALL` for US minute retrieval;
- normal HK provider sessions;
- separate Daily and 1-minute charts;
- market-local labels using IANA timezones.

Initial PAQS timeframe direction:

```text
HTF = completed W1
STF = completed D1
TTF = completed 30m REGULAR-session bars
```

W1 is derived from completed D1. 30m is derived from completed 1-minute bars with market-aware US/HK session rules. H1/H4 are not current MVP requirements.

Canonical state must preserve truthful timestamps and coverage. A latest/intraday price is never a final Daily close. Provider latency and page polling cadence remain distinct facts.

Provider current-QFQ data must not automatically be described as strict point-in-time-safe historical replay data. Strict historical real-market PAQS backtesting is not part of the current MVP.

## 8. PAQS-E / PAQS-Q / Score governance

PAQS-E is the current prioritized expert-reasoning branch. Its accepted runtime loads the registered
`docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md` and versioned prompt; immutable current
snapshot facts enter the Narrative provider-neutral port. New final text is preserved without a
structured semantic validator gate. Legacy post-validation remains unchanged for historical
structured evidence; neither text persistence nor formatting certifies strategy/RR correctness.

PAQS-Q is a separate deterministic/reference branch. Historical v0.3.x research and 006B structure
rules must not silently become required PAQS-E thresholds or a prerequisite to the 007C workbench.

Historical `Composite Quant Score = Daily Base Score + Intraday Minute Adjustment` is a derived
reference concept only. No score may create events/setups, bypass structural invalidation/RR,
replace missing evidence with zero, merge Q/E disagreement into a synthetic decision, or claim
calibrated probability without separate evidence and approval.

## 9. Dashboard product contract

The Dashboard retains accepted market-data, watchlist, chart and refresh behavior. TASK-007C is
accepted and integrated. TASK-007C1 adds the accepted registered-model/secure-credential/research
workflow and exact-text Narrative results, with safe local Markdown and raw views. TASK-007C2
repairs the credential dialog and retires old initial-account cards/duplicate administration.
The normal view preserves Narrative/Legacy history, known Runs, identity and frozen evidence.

Chart refresh must not relabel an old Decision as current. Entry and conditional Holder advisory
remain separate; invalidation, targets, RR, uncertainty and alternative evidence remain visible.
There is no real-order control and no claim the user executed an advisory.

The adopted longer-term product scope is `docs/decisions/R20_PRODUCT_ADOPTION_2026_09_07.md`. Prompt/model workspaces, council critique,
reviewable evolution proposals, news, simulated bookkeeping and operations are staged in later
bounded contracts, not hidden additions to TASK-007C. `docs/research/R20_ADOPTION_PLAN_AND_CODEX_PROMPT_ZH.md` is historical planning context.

## 10. Validation and backtesting boundary

Current PAQS work prioritizes deterministic semantics, synthetic golden fixtures, no-lookahead tests and current read-only smoke evidence.

A broad real-market historical backtesting platform is not a current committed MVP requirement.

If Phase 4 is explicitly reactivated later, it must use legitimate point-in-time data and separately approved assumptions. Current recent-minute display does not imply historical minute replay/tick simulation.

## 11. Infrastructure and secrets

Sufficient topology remains:

```text
Browser -> 127.0.0.1 FastAPI -> SQLite
                            -> independent read-only Market Data Provider
```

PostgreSQL compatibility remains portability, not a deployment requirement.

Never commit credentials, external/private account IDs, passwords, tokens, databases, logs or private broker exports.

## 12. Authoritative phases and bounded workstreams

The authoritative phases remain 0 through 4: historical definition, accepted foundation, active
Phase 2 decision terminal, and optional Phase 3/4 extensions as assigned by the Roadmap/adoption record.
Phase 4 is the final possible phase; no execution phase exists.

Current sequence: TASK-006B2 -> TASK-007A/B/C accepted and integrated -> TASK-007C1
user-accepted and integrated at `2cc4eeea3cc31d4fd1f1a4e9c1fbec237f82a2c4` -> TASK-007C2
implemented, awaiting independent review. The evidence attribution and preserved historical
records are linked in the current delivery status above. No next task is authorized.

TASK-006A is integrated at `7909f1c04f7049cf1ccec78a3d5023ae801b7177`. TASK-006B deterministic
implementation is integrated at `96747041ef0ff8c00937c5dd5e80cb4c5c28c17c`; its real-market
semantic checkpoint remains `STRUCTURE_CONCERNS_FOUND`. Earlier 006C/006D/006E single-engine plans
are superseded by separately planned 006B-Q/006C-Q/006D-Q/006E-Q work and the 007A/B/C/D workstream.
TASK-006B1 historical storage/replay and TASK-007D Q/E comparison are later bounded work, not
prerequisites for the current usable 007C interface. `TASK-006` and `TASK-007` remain umbrellas only.

## 13. Quality and change control

For each approved implementation task: read governing docs; preserve unrelated changes; state the exact file set; implement only approved scope; run proportional validation; verify provenance/freshness/Decimal/UTC/no-lookahead/safety boundaries; update required documentation; report exact evidence; and stop.

Codex must never be instructed to implement umbrella TASK-006 or TASK-007 in one pass.

Documentation requirements become part of PAQS Definition of Done. TASK-006A establishes user and engineering guide foundations, and later PAQS tasks must update them when behavior changes.

## 14. Accepted Phase 1 boundary

Phase 1 remains the reviewed foundation: packaging/configuration/logging; deterministic migration 0001; exact Decimal and UTC invariants; canonical Security identity; Watchlist; opening HKD 20,000, 200 units and NAV 100 facts; accepted read APIs/frontend; inert capability descriptors; tests and reviews.

`PAQS-MVP-001` changes none of that implementation or evidence.
