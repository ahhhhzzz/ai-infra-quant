# TASK-006D-Q Setup/Risk 1.0.0 — implementation and local validation

Status: **IMPLEMENTED / LOCAL VALIDATION PASS / AWAITING INDEPENDENT FOCUSED REVIEW / NOT INTEGRATED**.
Work began at product commit `c35632638f310509babfea903c6d42dbb4092492` in an isolated worktree;
only `task/006d-q-setup-risk-v1` is authorized for ordinary push. No product branch update is part
of this delivery. [Rules and Windows usage](../PAQS_Q_SETUP_RISK_V1.md) fix this profile.

## Delivered behavior and identity

Three long-only families are implemented: `TREND_PULLBACK_LONG` (confirmed support Zone or an
explicit old-resistance Retest HOLD), `RANGE_FAILED_BREAKDOWN_LONG` (same frozen Range lower source
and excursion), and `RIGHT_SIDE_BREAKOUT_LONG` with separately linked `FOLLOW_THROUGH` and
`RETEST` variants. A Setup binds a later M30 bullish Micro/Strong price candidate according to
family, computes its own q+1..q+3 follow-through, freezes thesis anchor B, counts D1 trading days,
and emits append-only lifecycle facts. D1 hard invalidation is a completed close strictly below
`B − k×ATR_current`; equality and wicks alone do not invalidate. Prior frozen B never moves.

T1/T2 use completed, known Range/Major High/resistance Zone/regular-open Gap evidence. Entry
inside resistance is blocked; complete-diameter clusters retain provenance and the closest
effective price, and T2 never rescues a poor T1. Stage A records indicative structural RR from the
M30 confirmation close. Stage B uses an independent `EntryReference` at the **first** subsequent
regular M30 open, rechecks W1/D1/Setup/targets and RR, and can qualify before that M30 candle
completes. Missing or late open evidence never creates a historical `LONG_READY`. Every Setup fact
has an explicit Entry Advisory; `LONG_READY` is qualification, never a fill or position.

New closed Setup schema and pure rules live in `core/domain/paqs_q/setup_reference.py` and
`core/strategy/paqs_q/setup_rules.py`/`setup_targets.py`. The explicit
`application/paqs_q_setup_artifacts.py` loader verifies three separate QInputs, exact Event 1.0.1
result/code/config bindings, calendar/adjustment/price-scale compatibility and a 51-file
dependency manifest. Setup ID/version: `paqs-q-setup-risk-reference@1.0.0`; manifest code hash
`60438dfc601c1410490561f7e8bb4b52ccd004f4f152e2ec229bfb3de4ed1101`; fixed config hash
`04cc46b7edbdf21b5d105d5fcf754165811a2327b3d38cc811310eedf94b8651`. The run also
binds a canonical hash of all independent open references. Original F1, B0/A1 and Event 1.0.0/
1.0.1 code/manifests/defaults are untouched.

## Windows execution and exact results

Execution host: Windows 11 `10.0.26200`, Python 3.12.14, pytest 8.4.1, Pydantic 2.11.7,
tzdata 2025.2, Ruff 0.12.9, mypy 1.17.1, Playwright 1.55.0. Interpreter:
`D:/AI_Infra_Quant_Codex_v1/task007c1-env/Scripts/python.exe`. The final fixed-rule synthetic
command used this interpreter and exited 0:

```powershell
$env:PYTHONPATH = 'src;.'
& 'D:/AI_Infra_Quant_Codex_v1/task007c1-env/Scripts/python.exe' -m tools.research.setup_risk --demo all --output data/setup-risk-demo-win312-20260923
```

Open `data/setup-risk-demo-win312-20260923/index.html` offline. Exact JSON is beside each HTML.
The three **synthetic** OHLC streams went through real Context/Event 1.0.1 and Setup/Risk 1.0.0;
they did not hand-construct results. Their final result hashes and facts are:

| Synthetic scenario | Result hash | Lifecycle facts | LONG_READY facts |
|---|---|---:|---:|
| Right-side Breakout, FT and Retest | `b4239a2b88e3c8bdb4dc4d2647b80b1c11061f5c20d3db21d02d6c6a0cd9887a` | 272 | 34 |
| Range Failed Breakdown | `9aaf19af71399e893ce19b1e4e97a3751f9143d562a401d24d11d700102818c0` | 129 | 24 |
| Trend Pullback | `0134d3878ac4af6c9f019aede7924a2559d0d505e9c0e5900f50a3716f54a0e9` | 7 | 1 |

These are repeated candidate qualifications, **not trades or independent market opportunities**;
the two Breakout variants share the frozen origin and remain separately identified. No returns,
win rate, sizing, fee, slippage, fill or performance number is produced by this module.

The one fixed-configuration AVGO CLI attempt used local W1 (312 bars), D1 (1,500 bars), M30
(273 bars) and capture calendar in explicit `OBSERVATIONAL` mode, without EntryReference. The
raw SHA256 values, respectively, were
`682aaebb059adb3ed8299b8b145b88b6d3d79ad6203c43716540b7035fa599ba`,
`d060a2abc82dceb957c49e607f8308ef6a57bdf0dd291110c8d29a8256435160`,
`87f8d630d2e3a321ee2093bc9ba064c426909609b2dd1607b837de1fe768fb09` and
`46c652b3062e4c6aeb43454dbcff5d8deb5f348639766b9e444b21116ebf6b2d`.
The command exited **2 / INSUFFICIENT** with
`W1_PARTIAL_TAIL_EXCLUDED, W1_CALENDAR_DATE_MISSING`; it wrote a diagnostic HTML/JSON to
`data/setup-risk-avgo-20260923/`. The supplied last W1 is partial and historical CLOSED facts
are missing from the capture calendar, so Event 1.0.1 cannot certify the completed W1 prefix.
This attempt was made during implementation before the final Setup open-only support and output
identity were frozen; it is retained as an input-coverage diagnosis, not represented as a final
code-hash market replay. Current-QFQ adjustment history and open-event timing are also
uncertified. **No real Setup or Entry qualification was established**, and the sample was not
adjusted, widened or rerun to manufacture one.

To inspect that exact local sample with a fresh output directory (expected to remain insufficient
unless genuine missing evidence is supplied):

```powershell
$env:PYTHONPATH = 'src;.'
python -m tools.research.setup_risk --w1 ../task006b-q-data/US.AVGO.W1.json --d1 ../task006b-q-data/US.AVGO.D1.json --m30 ../task006b-q-data/US.AVGO.M30.json --calendar ../task006b-q-r04-source/capture-calendar.json --mode OBSERVATIONAL --output data/setup-risk-avgo-new
```

## Validation performed in this task

An earlier focused Windows command below exited 0: **31 passed**, consisting of 19 new Setup/CLI/
browser tests and 12 selected E01/E02, Event, F1 and architecture compatibility cases. After the
last Setup-only W1-quality and opening-source guard was added, the two directly affected positive/
negative cases exited 0: **5 passed**. The final `tests/paqs_q_setup` suite then exited 0:
**20 passed** in 291.00 s under Windows Python 3.12.14, including offline Chromium. The selected
12 upstream compatibility cases were executed before that final Setup-only edit; no covered
F1/Event source changed afterward. These runs cover
all four positive Setup paths, independent opening evidence before next M30 completion, AS_OF vs
OBSERVATIONAL, incomplete/mismatched inputs, future-append stability, expiry day 15/16, missing
calendar/bar clock, wick/equality/close invalidation, nearest T1/no T2 shopping, Gap evidence,
target overrun, late/missing open references, and offline Chromium chart navigation. It does not
re-run the full historical F1/product/browser matrix.

```powershell
$env:PYTHONPATH = 'src;.'
$env:PLAYWRIGHT_BROWSERS_PATH = 'D:/AI_Infra_Quant_Codex_v1/playwright-browsers'
& 'D:/AI_Infra_Quant_Codex_v1/task007c1-env/Scripts/python.exe' -m pytest tests/paqs_q_setup tests/paqs_q_event/test_registry_artifacts.py::test_closed_calendar_fact_late_for_historical_prefix_blocks_registry tests/paqs_q_event/test_end_to_end.py::test_current_close_invalidates_prior_known_major_trend tests/paqs_q_event/test_end_to_end.py::test_real_ohlc_context_all_six_families_and_transition_structure tests/paqs_q/test_registry.py::test_default_and_two_explicit_experimental_gates tests/architecture/test_import_boundaries.py -q
```

Final Setup suite command: `python -m pytest tests/paqs_q_setup -q` with the same explicitly
identified Python 3.12 interpreter and `PLAYWRIGHT_BROWSERS_PATH` above. Its only warning was
an unrelated Starlette/AnyIO deprecation.

`ruff check` passed on all new Python modules/tests; `ruff format --check` found 11/11 files
formatted; strict `mypy` passed on the eight new non-test modules after the final edit. Manifest verification returned
the code hash above for all 51 listed files; documentation links and `git diff --check` passed.
The staged changed-file protection check is made before commit and ordinary task-branch push.
Existing Event 1.0.1 focused-review PASS and F1 closeout are historical
attributions; this task did not repeat their full review or claim independent approval.

## Boundaries and review state

The offline report displays data mode, period availability, upstream hashes, Setup source,
trigger/FT association, frozen B, current ATR/S/E, T1/T2 source and rejected obstacles, RR and
Entry Advisory, with clickable D1/M30 candles. Missing open evidence leaves qualification pending;
retrospective QFQ files cannot establish strict PIT. A structurally valid Setup can still be
`VALID_SETUP_BUT_POOR_ENTRY` or `NO_TRADE`. No account, order, fill, position, Holder state,
backtest, Q/E comparison, dashboard/API/database, broker connection or product merge is included.
The task stops for independent focused review after ordinary push of its branch.
