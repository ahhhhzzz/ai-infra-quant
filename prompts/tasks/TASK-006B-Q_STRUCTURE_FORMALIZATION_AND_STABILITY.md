# TASK-006B-Q — Structure Formalization and Stability

Status: **AUTHORIZED TASK START — mathematical specification, isolated research prototype and structural validation only; production adoption pending review.**

Repository: `ahhhhzzz/ai-infra-quant`

Task branch: `task/006b-q-structure-formalization`

Authoritative branch: `roadmap/no-live-trading`

Exact base: `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`

Owner instruction, 2026-09-09: “PAQS-Q 这个需要尽可能工程化和数学化，你看看怎么弄，先进行006B-Q吧”. This starts the bounded definition/validation work proposed immediately before that instruction. It does not assert that untested numeric candidates are production-approved.

## 1. Objective and authority

Deliver an executable, deterministic mathematical candidate for PAQS-Q structure and evidence of its stability. A prose-only report does not complete this task. Product integration is a subsequent adoption step after independent review and owner semantic acceptance; do not turn the research prototype into a hidden production path.

Read in full before changes:

1. `AGENTS.md`, `docs/ROADMAP.md`, `docs/MASTER_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/STRATEGY_SPEC.md`, `docs/REQUIREMENTS_MATRIX.md` and the applicable phase plan if one exists.
2. [Dual-branch decision](../../docs/decisions/PAQS_DUAL_BRANCH_ARCHITECTURE.md).
3. [006B1 closeout](../../docs/decisions/TASK_006B1_CLOSEOUT_2026_09_09.md).
4. [Original structure contract](TASK-006B_PAQS_STRUCTURE_ENGINE.md), [remediation](TASK-006B_REMEDIATION_01.md), and `src/ai_infra_quant/core/strategy/paqs_structure.py` at the exact base.
5. Historical [stability review](https://github.com/ahhhhzzz/ai-infra-quant/blob/01000900861d4506fb35fbf423901a5b9a306499/docs/research/TASK_006B_STRUCTURE_STABILITY_REVIEW.md) and [Lite amendment](https://github.com/ahhhhzzz/ai-infra-quant/blob/01000900861d4506fb35fbf423901a5b9a306499/docs/research/PAQS_V0.4_LITE_STRUCTURE_QUANT_AMENDMENT.md), both at that exact research commit.
6. [Candidate mathematical specification](../../docs/research/PAQS_Q_STRUCTURE_MATH_CANDIDATE_V1.md) and this contract.

The old research sequencing that held 006B1 is superseded by its accepted closeout. The old research values remain candidate values. The current task permits their isolated research implementation without declaring the old amendment production-approved. PAQS-E's registered strategy, prompts, Narrative and Legacy paths retain their existing authority.

Run `git status`, inspect worktrees, and state exact planned files. Use an isolated worktree if necessary. Preserve `phase1_remediation_commit.txt` and all unrelated changes. Do not reset, stash, clean or terminate another worktree's processes.

## 2. Scope and deliverables

Implement a standalone, provider-neutral pure calculation under `tools/research/paqs_q/`, with dedicated tests under `tests/research/paqs_q/`. Product modules must not import the prototype. It may read/import existing immutable domain types and accepted input normalization without changing them.

Required deliverables:

- Reviewable mathematical specification: formulas, numerical policy, full state transitions, boundary cases, parameter origins and limitations. Refine the candidate document with explicit change rationale and version increments rather than silently changing rules.
- Typed input/output and parameter schemas; immutable output; deterministic canonical serialization and hashes; executable local CLI accepting documented fixture/research inputs without OpenD or LLM access.
- One Pivot engine per W1/D1/M30, bounded warm/active history, active-only evidence, D1 zones/range and conservative per-timeframe Regime.
- A machine-readable rule-to-function-to-test matrix, including every acceptance item in section 5.
- Synthetic golden/adversarial cases plus reproducible structural diagnostics on real observations where available.
- `docs/reports/TASK_006B_Q_IMPLEMENTATION_REPORT.md`: exact SHA/base, full changed paths, commands/results, skipped/blocked evidence, open semantic questions and adoption recommendation. Engineering execution and real-market semantic acceptance must have separate verdicts.
- `docs/evidence/TASK_006B_Q/README.md` and compact JSON/CSV diagnostics/manifests. Report a runnable offline command and representative cases for human inspection.

Allowed changes are limited to those two new tool/test directories, this task's research document, report and evidence directory. The issued contract is immutable after handoff; material scope changes require a separate addendum. If an indispensable change falls outside this list, report the concrete dependency; do not expand production scope.

All existing files outside the allowlist must retain base Git mode/type/blob identity, including all `src/`, existing tests, project dependency/lock/config files, migrations 0001–0004, accepted research strategy bytes and historical evidence. New tool/test files must be discoverable via explicit commands without modifying pytest configuration. Use installed dependencies or the standard library; isolate optional research acquisition dependencies outside the production environment.

## 3. Implementation sequence

1. Record baseline/protected-file manifest and inherited defects. Freeze the candidate version, parameter profile, canonical schema, fixed validation universe and cutoffs before real-market diagnostics.
2. Implement the pure prototype and synthetic oracles. Do not call the old engine and merely repackage Micro/Major results as a new engine. Reuse only explicitly compatible pure helpers; document source attribution and semantic differences.
3. Run same-input reproducibility, cutoff isolation, origin invariance and boundary-exit experiments. Compare against the historical engine on the same normalized observations to determine whether the original path-lock and stale-zone cases were addressed.
4. Run fixed-universe and small one-parameter-at-a-time sensitivity diagnostics. Preserve unsuccessful cases and unavailable symbols. Do not optimize by return, drawdown, hit rate or agreement with PAQS-E.
5. Produce a concise Chinese explanation of what the machine can determine, evidence it requires, and when it reports `UNCERTAIN`. Finish the report and stop for independent review; no merge, production wiring or 006C-Q.

## 4. Research data contract

Default execution must be fully local using synthetic fixtures or explicit user-supplied files. No automatic networking on import/test/startup. A separate opt-in research acquisition command may use publicly accessible or already authorized historical data after checking current provider documentation/terms and recording the actual provenance. Provider adapters stay in `tools/research/paqs_q/integrations/`. No bypass of access restrictions, paid signup or use of user credentials without authorization.

OpenD historical research quota budget is **zero**. Never acquire a broad sample through the user's OpenD. Existing archives can be supplied read-only as observations; do not add a database export route or chart/Analyze integration. Archive reads do not make current-QFQ data point-in-time corporate-action-safe.

Before fetching/computing diagnostics, commit/freeze a universe of at least 40 equities (at least 24 US and 16 HK), including AVGO, VRT, NVDA, 09698 and 00700 where supported, with declared sector diversity and cutoff schedule. Include an exchange-symbol mapping, sampling rationale and exclusion policy. Do not substitute survivors after seeing results; report valid/insufficient/unavailable counts by timeframe with explicit denominators.

Target at least 100 sequential fully eligible terminal cutoffs per symbol/timeframe. W1 therefore needs at least 229 completed weekly bars for a 130-bar evaluation window; two years alone cannot satisfy it. Obtain sufficient daily/calendar history for proper weekly derivation, or report the W1 shortfall. M30 must be regular-session, exchange-calendar-aware; direct vendor M30 bars cannot silently substitute if bucket alignment, breaks, completion or partial sessions differ from canonical 006A semantics.

Record source URL/provider/version, retrieval time, symbol mapping, requested/actual coverage, session/calendar origin, adjustment mode, missingness and content hashes. Parse prices from exact source numeric text into Decimal; if a source library already emitted binary floats, disclose lost source precision and classify it as approximate research input, not an exact-decimal validation oracle. No invented calendar, gap fills, synthetic substitution labelled real, or fabricated historical publication/availability timestamps.

Commit only permitted compact evidence and reproducibility metadata, not bulk licensed market data, databases, secrets or logs. A hash alone is not reproducibility: provide acquisition/normalization commands and describe whether the original exact observations can be retained/reobtained. Source revisions can prevent byte-identical refetches; state that limit.

If real data cannot meet scope, still complete the pure implementation, synthetic validation and runnable harness. Mark real-market gate `INCOMPLETE` with exact shortfalls; do not assert overall semantic PASS. This is a truthful deliverable, not authority to weaken the gate.

## 5. Acceptance matrix

| ID | Required evidence / acceptance |
|---|---|
| QSTR-001 | Same canonical bounded input + cutoff + rule version + parameters produces identical decision bytes/hash across processes, repeated runs and surrounding Decimal contexts. |
| QSTR-002 | Completed-only/cutoff tests: injecting, changing or removing records available only after cutoff cannot affect facts at that cutoff; zero future-evidence references. Missing availability metadata stays explicit. |
| QSTR-003 | Full history vs exact required trailing window gives identical active structure; at least three extra leading-history lengths and adversarial leading extremes. Excluded raw-history diagnostics may differ, decision identity must not. |
| QSTR-004 | Warm-up facts cannot create active zones/ranges or supply directional evidence through hidden anchors. Insufficient window, nonpositive ATR and invalid data produce typed conservative results. |
| QSTR-005 | Pivot state transition/threshold/tie/same-bar/gap tests with hand-computed expected references. `extreme_at < confirmed_at <= cutoff`; initial UNSEEDED ambiguity never forces a pivot. |
| QSTR-006 | Expired evidence excluded; touch independence/age exact at age limit and limit+1; active D1 confirmed zones <=4; zero W1/M30 decision zones/ranges; no role flip. |
| QSTR-007 | Range reactions and closes share one recent window; historical touches cannot qualify it; semantic persistence reported separately from content/version identity. |
| QSTR-008 | Honest separate input, structure-sufficiency and Regime statuses. Active HH/HL or LH/LL evidence required; latest close can invalidate direction without inventing an event. |
| QSTR-009 | Rolling boundary ablation distinguishes new-right information, left expiry and combined/non-attributable cases. Inspect all material left-boundary-only directional flips; unexplained cases prevent semantic adoption. |
| QSTR-010 | Fixed universe and cutoff manifest precedes diagnostics. Coverage and missingness denominators; same-input old/new comparisons; parameter sensitivity and all outliers retained. |
| QSTR-011 | Rule/parameter/input/output hashes and bar evidence trace; financial JSON fields are decimal strings; clock/runtime/version/provenance envelopes are separate from semantic equality projection. |
| QSTR-012 | All protected files identical to base; no product import of prototype, network in ordinary runs, broker/LLM/database mutation, API/UI, scanner or successor implementation. |

Required tests are substantive invariants/adversarial examples, not assertions that mirror implementation. Include equal highs/lows, flat ATR, invalid OHLC, duplicate/conflicting time keys, US/HK completion/session cases, split-basis mismatch, partial history, chronological ties and rolling-window transitions. Use explicit synthetic labelling; market-data quality flags must not be relabelled to make tests pass.

Run dedicated tests, Ruff and format on added Python paths, explicit mypy (including Windows target where applicable), `git diff --check`, link verification and protected-blob comparison. Run existing relevant structure/input/boundary regression tests. Full unrelated browser/business suites and Uvicorn startup are not required for an isolated research-only change; do not claim they ran. Any runtime change would violate this contract rather than justify expanding testing.

Performance is measured on declared hardware, at max evaluation windows and fixed candidate counts: wall time p50/p95, memory, comparison counts, complexity and repeats. Avoid an invented universal latency promise. Extra leading history may cost input parsing but must not expand the calculation window. No service/cache/background worker is needed.

## 6. Stop boundary and handoff

No Event, Setup, RR, trade stop/target, advisory states, EMA/ROC confirmation, probability, composite score, P&L optimization, scanner, Paper accounting or broker access. No PAQS-E semantic changes. No chart/archive Analyze wiring or new migration.

Task output is **a candidate structural engine with validation**, not a released Q trading strategy. Independent review and explicit semantic adoption precede production integration; this task does not merge itself or activate 006C-Q.

Make local commits and preserve worktrees. Push only this task branch when authorized by the owner's handoff, read back the exact GitHub SHA/report and report them. Never force-push or change the authoritative branch. Report any actual approval/access rejection faithfully.
