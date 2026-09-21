# PAQS-Q single-pattern research v1 — implementation and validation

Date: 2026-09-21. **IMPLEMENTED / WINDOWS VALIDATED / AWAITING INDEPENDENT REVIEW**.
Task branch: `task/paqs-q-single-pattern-research-v1`; no product merge is authorized.
Base: `4ae42961916955ab281a253f4c4fd9c3679ea58e` (remote authority unchanged at task start).
Implementation commit: `b5eb601cb506672f37e3c901ab8be0e501828d91`
(initial implementation `820898e590b0507a3b4332f7eafea3985e107e73`).
The later delivery commit only adds current documentation and this report; tested code is unchanged.

## Delivered scope

[Rules and Windows commands](../PAQS_Q_SINGLE_PATTERN.md) were recorded before implementation.
One D1 long-only pattern: confirmed local high → buffered close breakout → first retest → later
strong bullish bar → next tradable open. Existing B0 raw inequalities/prior-raw veto and the old
pure EMA14 ATR are reused unchanged. Point substitution, entry cancellation, frozen low-based
intrabar stop, 2R target, holding limit and cost/sizing model are explicit new research assumptions.
This is not B0 certification, complete PAQS-Q, formal Event/Setup/Risk or market validity.

Nine new tool files (eight Python plus HTML), two focused test files and the rules/usage guide.
Six existing current documents receive only status/link updates. No `src/`, dependencies,
historical tests, research sources/evidence, frozen contracts, product API/UI/database changes.
No new plugin framework, brokerage connection, model call, provider acquisition or parameter search.
CLI import/report replaces neither existing Snapshot nor PAQS-E. F1 Event remains unconfigured;
A1 remains opt-in/disabled by default. The accepted Linux exception and original FAIL are retained.

## Actual data and result

Reused existing local `US.AVGO.D1.json` and `capture-calendar.json`, without modifying either.
1,500 real observed daily bars, **2020-09-17 through 2026-09-08**. These are existing OpenD quote
archive exports, not newly downloaded data. No user database was accessed. The calendar lists
1,501 sessions through 2026-09-09; its last session is beyond the completed price sample.
All supplied calendar sessions within the price range have bars; calendar completeness itself
is not certified (`coverage_complete=false`), and source dataset quality remains PARTIAL.

- Price file SHA256: `d060a2abc82dceb957c49e607f8308ef6a57bdf0dd291110c8d29a8256435160`.
- Calendar file SHA256: `46c652b3062e4c6aeb43454dbcff5d8deb5f348639766b9e444b21116ebf6b2d`.
- Both final CLI reports bind normalized code inventory digest
  `a7b80eb41a5831bea55d94b49da1ca1af37ef3b65a37211d6d81d7316f0bdd99`.
- Real run: **12 signals, 12 closed trades, 0 open**. Initial cash 100,000 USD;
  final marked equity **91,869.4809306673337332843103572**; return **−8.130519%**;
  maximum close-equity drawdown **28.547655%**; closed-trade win rate **41.666667%**.
- Same-cost/allocation buy-and-hold: return **1022.873503%**, close drawdown **40.874275%**.
  It starts at the first open; strategy waits for warmup/signals. Both mark remaining shares at
  the last close without final sell costs. It is not a dividend-inclusive total-return benchmark.
- Synthetic demo: 3 signals/entries, 2 closed (one target, one gap stop), 1 open position.
  Synthetic results validate mechanics only; they are not market observations.

All 1,500 real bars have unknown historical availability and current-QFQ adjustment. These results
are **EXPLORATORY_NOT_POINT_IN_TIME**, not certified historical backtests. Prefix causality does
not recover missing vintage prices, corporate-action histories or historical publication times.
Costs/slippage and nominal adjusted-price share quantities are simulated; no volume/limit/suspension
or real settlement model. No tuning was performed after seeing the negative strategy return.

## Executed validation

Actual environment: Windows 11 build 26200, Python **3.12.14**, pytest **8.4.1**, tzdata **2025.2**,
Jinja2 **3.1.6**, Ruff **0.12.9**, mypy **1.17.1**, Playwright **1.55.0**,
Chromium Headless Shell **140.0.7339.16** (existing build 1187).
Initial validation ran on the implementation working tree subsequently committed as `820898e`;
only test-file formatting followed that pytest run. A final import review added explicit rejection
of malformed JSON completion flags (string `"false"` is not boolean true) and missing timestamps.
The 14 non-browser tests and lint/type checks were rerun for that correction, committed as `b5eb601`
after formatting. Final real/synthetic CLI ran at `b5eb601` with documentation-only pending changes.
The HTML/strategy/simulation are unchanged from the inspected `820898e` reports. No historical
result is represented as a fresh execution; repeated tests below are not additional distinct cases.

| Command / check | Actual outcome |
|---|---|
| `python -m pytest tests/research/single_pattern --confcutdir=tests/research/single_pattern -q` | **15 passed**, 25.53s, exit 0; no product conftest |
| `python -m pytest tests/research/single_pattern/test_research.py --confcutdir=tests/research/single_pattern -q` after input guard correction | **14 passed**, 0.63s, exit 0; includes malformed completion flag |
| `python -m pytest tests/architecture/test_import_boundaries.py tests/architecture/test_task007b_boundaries.py -q` | **12 passed**, exit 0 |
| `python -m pytest tests/integration/test_offline_startup.py::test_migrated_app_starts_offline_and_renders_dashboard -q` | **1 passed**, exit 0; temporary test database only |
| `python -m ruff check tools/research/single_pattern tests/research/single_pattern` | PASS, exit 0 |
| `python -m ruff format --check tools/research/single_pattern tests/research/single_pattern` | 10 files already formatted, exit 0 |
| `python -m mypy tools/research/single_pattern` (`MYPYPATH=src`) | PASS, 8 Python files, exit 0 |
| Real and synthetic CLI commands from usage guide | exit 0; HTML/JSON/three CSV exports |
| Actual AVGO HTML inspection at 1440×1100; trade locator | 12 trade rows, no JS errors; screenshots inspected |
| Documentation links / scope protection / `git diff --check` | 243 relative links valid; existing source, contracts, historical tests/evidence unchanged; exit 0 |

Set `PYTHONPATH=src;.` for tests, and `PLAYWRIGHT_BROWSERS_PATH` to the existing browser installation
when it is outside Playwright's default cache. The CLI itself resolves this checkout's `src`.
Existing Starlette/AnyIO deprecated BlockingPortal warning remains in product-conftest tests.
No F1 rerun, historical research suite, full product regression or Linux browser matrix was run.

Assertions cover every synthetic prefix, future extension, confirmation vs extreme time, delayed
retest confirmation, expiry/equality/failure, bad inputs/calendar gaps, current-vintage limitations,
next-open fills, gap stops, same-bar stop/target conflict, cash/fees/PnL/drawdown, time exit,
ignored held-position signals, no forced final liquidation, exact JSON/CSV and inert/offline HTML.

## Delivery and remaining limits

Local ready-to-open outputs (ignored by Git): `data/avgo-research-v1-final/report.html` and
`data/synthetic-research-v1-final/report.html`. Each directory has exact results, trades, signals and
equity exports. CSV `trades` contains closed trades; remaining positions and pending signals are
explicit in HTML/JSON. Raw real data/reports/screenshots are not redistributed in Git.

This research loop is runnable with the existing real sample; no external data condition blocks
this delivery. Another machine must supply its own local observations and expected-session file
or use `--demo`. Strict PIT research would additionally require historical price/adjustment
versions and independently evidenced calendar/availability. Only a single existing symbol was
observed; 12 trades do not establish generality or profitability. Independent review is pending.
Complete Event, Setup/Risk, Q/E comparison and formal UI remain unimplemented and are not started.

## Subsequent closeout — 2026-09-21

The original implementation/execution record above remains unchanged. The owner subsequently
provided an external focused PASS and authorized closeout/fast-forward integration. Current state:
**FOCUSED REVIEW PASS / CLOSED / INTEGRATED**, effective under the
[closeout decision](../decisions/PAQS_Q_SINGLE_PATTERN_V1_CLOSEOUT_2026_09_21.md).
This addition does not represent new Windows/browser/AVGO execution or independent AVGO recomputation.
