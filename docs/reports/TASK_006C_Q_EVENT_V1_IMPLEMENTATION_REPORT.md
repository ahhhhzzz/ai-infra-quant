# TASK-006C-Q Event reference v1 — implementation and validation

2026-09-23. **IMPLEMENTED / VALIDATED ON WINDOWS / AWAITING FOCUSED INDEPENDENT REVIEW**.
No independent review, user acceptance or product integration is claimed by this report.

Baseline: `roadmap/no-live-trading` at `5326ff6cfa3cae19ebb186643bc3a16bed88b518`.
Task branch: `task/006c-q-event-engine-v1`, in a separate worktree.
Runtime implementation and AVGO execution SHA: `037255bc5d935a8ab38866226fd0a3e624c862b1`.
Subsequent delivery changes add this report/current-state documentation and two timeframe protocol
checks; runtime, manifests and the AVGO output remain the same. Original worktrees are preserved.

## Delivered scope

| Family | Implemented behavior / focused evidence |
|---|---|
| Attempt / Breakout / Breakdown | Strict inequalities, one close break per outside cycle, already-outside activation suppression, rearming on the next bar, Range/underlying Zone deduplication. Opened cycles retain their original source even when Range activity changes. |
| Failed Break / Breakout Failure | Symmetric wick reclaim including same-bar and e+3; valid close break reversal only b+1..b+3; no duplicate wick reclassification, accumulated/frozen excursion extreme. |
| Retest | Inclusive touch window, later-bar Micro/Strong Hold, guard/parent failure first, expiry without invented Start, repeated touch/departure numbering and original deadline. |
| Transition | Real OHLC Range and trend-reversal paths both confirm in synthetic E2E, in both directions. Post-break Major structure and two consecutive valid bars remain mandatory; FT alone cannot confirm a trend. Invalidation cancels first; no arbitrary timeout. |
| Trigger price candidate | Micro first effective crossing, exact Strong ratios/CLV, same-anchor reason merging. Unanchored PRICE_PATTERN has no fabricated guard. EVENT_CONFIRMATION is distinct from later Micro/Strong Hold evidence. |
| Follow-through | q+1..q+3 PENDING → CONFIRMED/NONE/FAILED append-only facts; terminal states stay unchanged after later failures. Missing expected bars reject the replay instead of advancing timers. |

[Rules, parameter sources, input format and commands](../PAQS_Q_EVENT_V1.md) record the owner's
adopted v1 profile and engineering conventions. No market research or parameter search was used
to choose these values. There are no unfinished families within this bounded price-event scope.

New explicit plugins: `paqs-q-event-context-reference@1.0.0` and
`paqs-q-event-reference@1.0.0`, capability `PREFIX_EVENT_CONTEXT_V1`.
The additive loader reuses F1 protocols, Registry, QInput/QResult, canonical serialization and
upstream binding. Strict immutable plugin-owned schemas carry context and event evidence;
F1 closed record tops are unchanged. event_key identifies stable prefix lifecycles; record_id
continues to bind the complete F1 input/upstream result. Historical PENDING facts are not rewritten.

Core reuses unchanged pure ATR/Pivot/Swing/Zone/Range functions, without importing research tools.
W1/D1/M30 are independent. Source use begins after confirmation; current-bar ATR is used in the
adopted formulas. AS_OF defaults to strict evidence qualification; OBSERVATIONAL must be explicit.
Missing historical price/calendar/adjustment evidence does not silently become strict confirmation.

## Actual Windows validation

Environment: Windows 11 `10.0.26200`, Python **3.12.14** (AMD64, MSC 1944), pytest **8.4.1**,
tzdata **2025.2**, Pydantic **2.11.7**, Ruff **0.12.9**, mypy **1.17.1**, Playwright **1.55.0**,
Chromium **140.0.7339.16**. Actual interpreter:
`D:/AI_Infra_Quant_Codex_v1/task007c1-env/Scripts/python.exe`.
`PYTHONPATH=src;.`; `MYPYPATH=src`; browser cache is the existing sibling `playwright-browsers`.

| Actual execution | Result / scope |
|---|---|
| `python -m pytest tests/paqs_q_event tests/paqs_q tests/architecture/test_import_boundaries.py tests/architecture/test_task007b_boundaries.py tests/architecture/test_task006b_boundaries.py -q` | **178 passed**: 72 then-current Event tests + 91 F1 compatibility checks + 15 architecture checks. Exit 0. |
| After the source-freezing correction and new offline smoke: `python -m pytest tests/paqs_q_event -q --basetemp=data/event-test-tmp` | **75 passed**, exit 0; final runtime kernel/manifests. Real OHLC E2E, mirrored equations/deadlines, causal append invariance, strict schemas, calendar/timeframe boundaries, CLI and offline browser. |
| At `037255b…`, after capture half-day adapter coverage: `python -m pytest tests/paqs_q_event/test_cli.py -q` | **4 passed**, exit 0: 3 reruns plus 1 new adapter test. Preserves MORNING_ONLY close and unknown historical availability. |
| At the same runtime SHA, with two new tests in the working tree: `python -m pytest tests/paqs_q_event/test_registry_artifacts.py::test_explicit_event_registry_accepts_calendar_qualified_timeframes -q` | **2 passed**, exit 0: W1 factual completion before nominal week end and HK M30 through the actual Registry/Event protocol. |
| Ruff on the 11 new Python implementation/tool files, all new tests and the one changed architecture test | **All checks passed**, exit 0. |
| mypy strict on the 11 new Python implementation/tool files | **Success: no issues found in 11 source files**, exit 0. |
| AVGO CLI and offline existing-output browser smoke | Exit 0; 2,229 rows match JSON; filter Breakout and select bar 51; K-line/evidence render; zero page errors and zero HTTP(S) requests. |

There are **78 distinct new tests**, validated in the batches above; reruns are not added to that
count. The first two pytest batches executed with HEAD at the baseline and the implementation in
the working tree; they are not described as executions after `037255b`. The final runtime contains
the core bytes tested in the 75-test batch. Only the input adapter changed afterward and its CLI tests
were rerun at `037255b`. Final lint/type checks used that commit plus the two new test cases.
An initial W1 fixture left availability inconsistent with its deliberately wrong completion time;
the fixture was corrected to isolate the intended calendar rejection, without weakening checks.
During implementation, the shallow-outside Range source-freezing case was corrected and tested.

Pytest emitted the existing Starlette/AnyIO `BlockingPortal` deprecation warning; no failed check
remains. No new Linux execution, full product regression, historical research rerun or product
browser matrix is claimed. The accepted historical Linux layout exception remains unchanged.

Reproduce focused checks with the commands above. For lint/type, use the new files listed under
`core/domain/paqs_q/event_reference.py`, `core/strategy/paqs_q/event_{calendar,context,rules,plugins}.py`,
`application/paqs_q_event_artifacts.py`, `tools/validation/paqs_q_event.py`, and
`tools/research/event_engine` (relative to `src/ai_infra_quant` for core/application).
The new manifest inventory has **43 files**, including all **41** transitively imported project
Python files/package initializers and the original two B0/A1 manifests; the AST closure check passes.

## One actual AVGO observation run

Executed once at `037255bc5d935a8ab38866226fd0a3e624c862b1` using the unchanged real inputs:

| Input | SHA256 |
|---|---|
| `../task006b-q-data/US.AVGO.D1.json` | `d060a2abc82dceb957c49e607f8308ef6a57bdf0dd291110c8d29a8256435160` |
| `../task006b-q-r04-source/capture-calendar.json` | `46c652b3062e4c6aeb43454dbcff5d8deb5f348639766b9e444b21116ebf6b2d` |

```powershell
$env:PYTHONPATH = "src;."
& ../task007c1-env/Scripts/python.exe -m tools.research.event_engine --input ../task006b-q-data/US.AVGO.D1.json --calendar ../task006b-q-r04-source/capture-calendar.json --mode OBSERVATIONAL --output data/avgo-event-v1
Start-Process data/avgo-event-v1/report.html
```

The output already exists locally; use a **new** output directory for any deliberate reproduction.
Actual output root:
`D:/AI_Infra_Quant_Codex_v1/task006c-q-event-worktree/data/avgo-event-v1`.
The HTML, precise input/structure/events/summary JSON and browser-smoke receipt/screenshot remain
local ignored outputs. No original report or input was overwritten or committed as new market data.

1,500 D1 bars, 2020-09-17 through 2026-09-08; 1,501 supplied open-day calendar rows include
12 MORNING_ONLY sessions. Both plugin statuses are **AVAILABLE**, strict_confirmation is **false**.
The unchanged reference algorithm emits 4 Micro + 4 Major pivots, 4 candidate Zones, **zero confirmed
Zones and zero Ranges** for this fixed-start sample. Final readiness: ATR/Micro/Major true,
Zone/Range false; regime UNCERTAIN. This sparsity and retained history-origin sensitivity are
reported directly, without tuning or claiming they were resolved.

| Actual event facts | Count |
|---|---:|
| Attempt | 1,460 |
| Breakout / Breakdown | 1 / 1 |
| Failed Break / Breakout Failure | 3 / 0 |
| Retest START / HOLD / FAILURE / EXPIRED | 0 / 0 / 1 / 1 |
| Transition | 0 |
| PRICE_PATTERN / PRICE_TRIGGER_CANDIDATE | 159 / 198 |
| FT PENDING / CONFIRMED / NONE / FAILED | 198 / 113 / 83 / 2 |
| Excursion PENDING / CANCELLED; event invalidation | 4 / 1; 4 |
| Total timestamped facts | 2,229 |

PENDING rows are historical facts; all 198 FT lifecycles have a later terminal in this sample.
Real data need not exercise every family. Synthetic E2E demonstrates all six, including both
Transition paths, positive Retest Hold, cancellation and timeout. No new profit/return statistic
was computed, no parameter changed, and existing research results were not reinterpreted.

Identity (canonical result hashes differ from raw file SHA256, which includes the final LF):

| Identity | Value |
|---|---|
| Context code hash | `0835df906256aceb824bde5f59d8b22fbdc1de029823d353f2ea77c3b16bd0e1` |
| Event code hash | `ecc7003fdf24418e9364c6cf08796345e420a81be44845ba8387456e6853954a` |
| Input hash | `f5ecdabbde99d9f849dd713fc1ea06ff57aab2e1940754a61ae528816850d72d` |
| Structure result hash | `a036226d94f328ce6115c3922f98685aeb4eaa965e8e4986e38c7b0d1c1a76c2` |
| Event result hash | `4e23e17d73f5a458f50928fda06a8edb2e7857f9e2402b63675ef7755488ce7e` |
| `events.json` SHA256 | `907fd3fb368a10eb2822f3f3673c7e0d41dc7fccb379b5f753f7f2fafd021a63` |
| `report.html` SHA256 | `ffa1dc361ca015f7fb80b29152de1baa3b09791deabc2521031a6b3ab5b13102` |
| `summary.json` SHA256 | `abb25483931d70b00d012ed8b4730d6d489834d0b129958531c0da337c4f1e6a` |

## Protection and remaining limits

The 34 original F1 manifest-covered files match the baseline, including package initializers.
B0/A1 manifests, pure old structure engine, dependencies, historical contracts/research/evidence,
single-pattern/risk tools, PAQS-E, Analyze, Dashboard/API and database/migrations are unchanged.
The sole pre-existing test edit adds the exact new loader path to the isolation allowlist;
no boundary assertion or historical test is removed/relaxed. Only new core/tool/test files,
new manifests and necessary current documentation are added or updated.
Documentation validation resolved 277 local Markdown links with no missing target;
`git diff --check` passed. Post-AVGO changes contain only documentation and the two new timeframe
protocol tests. No unrelated working tree was changed.

AVGO remains observational, not strict PIT: all 1,500 price availability timestamps and all 1,501
calendar historical availability timestamps are unknown, quality PARTIAL, current QFQ adjustment,
upstream precision and historical versions unproven, and unlisted calendar dates are not a complete
calendar certificate. Prefix causality is computational evidence, not proof of historical public
availability. Strict mode does not silently accept these limitations.

Formal Setup/Risk, LONG_READY, Q/E comparison, product UI/API integration and trading remain
unimplemented. No independent review PASS or market-validity claim is made. Stop after the task
branch delivery and wait for focused independent review; do not merge the product branch.
