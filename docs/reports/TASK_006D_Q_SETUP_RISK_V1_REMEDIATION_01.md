# TASK-006D-Q Setup/Risk 1.0.1 — S01/S02 focused remediation

Status: **REMEDIATED / LOCAL VALIDATION PASS / AWAITING INDEPENDENT FOCUSED REVIEW / NOT INTEGRATED**. This report records corrections on `task/006d-q-setup-risk-v1` after the reviewed Setup/Risk 1.0.0 commit `5aa5868876f85f305f9e59c75e6cbcd449e3a38c`. It does not amend the [original implementation report](TASK_006D_Q_SETUP_RISK_V1_IMPLEMENTATION_REPORT.md) or its historical AVGO result. The product branch is not updated.

## Findings and corrections

- **S01 — Range Breakdown → Breakout Failure parent.** The 1.0.0 Setup discovery compared `anchor_key` values even though Event 1.0.1 assigns a new reclaim anchor to the Failure. The 1.0.1 rule follows the Failure's exact `related_keys` parent event key, and checks that the parent is an earlier confirmed DOWN `BREAKDOWN` from the same frozen Range boundary. An unrelated Breakdown, wrong direction, or changed source cannot qualify. The separate wick `FAILED_BREAK` route remains available. A real OHLC → Context/Event → Setup positive path and wrong-parent/source negatives are added.
- **S02 — late opening evidence and fact identity.** The 1.0.0 replay looked through the final reference collection at the opening clock and emitted a fact at a future `available_at` before replay reached that time. In 1.0.1, unavailable opening evidence closes that opening as `NO_TRADE`; the later receipt appends an explanatory rejection at its actual availability time. It cannot backdate `LONG_READY` or move the candidate to a later opening. Equal-time replay order is explicit, and `fact_key` is derived from immutable fact meaning rather than the length of a global fact list. The prefix regression compares complete historical `SetupFact` values, including key, relations, targets, reasons and timestamps.

`paqs-q-setup-risk-reference@1.0.1` has a new [manifest](../../src/ai_infra_quant/resources/paqs_q/setup-risk-1.0.1.json) and code hash `849d50f23af1ca572adcbc7a972c61eff6bc61c7cefb6c9cb22c298260d2dac1`. Both Setup manifests list 51 paths: exactly three Setup files have changed content hashes (loader, domain schema, and rules), while the other 48 paths, including 47 upstream dependencies and `setup_targets.py`, match. The fixed [1.0.0 manifest](../../src/ai_infra_quant/resources/paqs_q/setup-risk-1.0.0.json), its report, and the F1/B0/A1/Event 1.0.1 identities remain historical and unchanged. Setup parameters are unchanged; this is a causal and lineage correction, not parameter tuning or a new strategy.

## Validation attribution

The **user-provided external Linux review** of 1.0.0 ran 19 Setup non-browser tests and 9 selected compatibility tests successfully; its three new reproduction cases failed, identifying S01/S02. That external review did not run Windows, browser acceptance, or AVGO.

The **local Windows Python 3.12 remediation work** reproduced the S01 positive-path failure and the S02 full-versus-prefix failure before the fixes. After the fixes, the focused S01/S02 slice passed **8 tests**. The final Setup, selected compatibility and offline Chromium slice then exited **0: 40 passed** in 366.72 s, with one unrelated Starlette/AnyIO deprecation warning. A final S02 assertion about explicit missing-open evidence was added during that run and separately passed afterward (**1 passed**). This is local verification, not an independent focused review. The 1.0.1 manifest verification passed; Ruff check/format passed on 13 files, and strict mypy passed on eight source files. The final test command used the explicit Windows Python 3.12 interpreter:

```powershell
$env:PYTHONPATH = 'src;.'
$env:PLAYWRIGHT_BROWSERS_PATH = 'D:/AI_Infra_Quant_Codex_v1/playwright-browsers'
& 'D:/AI_Infra_Quant_Codex_v1/task007c1-env/Scripts/python.exe' -m pytest tests/paqs_q_setup tests/paqs_q_event/test_registry_artifacts.py::test_closed_calendar_fact_late_for_historical_prefix_blocks_registry tests/paqs_q_event/test_end_to_end.py::test_current_close_invalidates_prior_known_major_trend tests/paqs_q_event/test_end_to_end.py::test_real_ohlc_context_all_six_families_and_transition_structure tests/paqs_q/test_registry.py::test_default_and_two_explicit_experimental_gates tests/architecture/test_import_boundaries.py -q
```

The local Windows Python 3.12 synthetic CLI smoke command exited **0** and generated a new offline `index.html` with exact JSON/HTML under `data/setup-risk-remediation-101-20260923/`:

```powershell
$env:PYTHONPATH = 'src;.'
& 'D:/AI_Infra_Quant_Codex_v1/task007c1-env/Scripts/python.exe' -m tools.research.setup_risk --demo all --output data/setup-risk-remediation-101-20260923
```

| Synthetic case | Status | Facts | LONG_READY facts | 1.0.1 result hash |
|---|---|---:|---:|---|
| Range | AVAILABLE | 129 | 24 | `7431a63eb0115f0711fe3ca666ed5321efccf3ef09f433a21f026ed94c7b0840` |
| Right-side breakout | AVAILABLE | 272 | 34 | `f68ff849fae3104f98097da1a0a8583521a962fe7dd0b4f07babff882e454ae0` |
| Trend pullback | AVAILABLE | 7 | 1 | `3a9c87fe4592abd6b10b5a735d798a239a49229698d2d78df76bac8d0e234e34` |

These are synthetic repeated qualification facts, not trades or market outcomes. The separate offline Chromium acceptance test is included in the 40-pass final slice.

The prior AVGO diagnostic remains `INSUFFICIENT` because its W1 calendar lacks required closed-day evidence. It was not rerun for 1.0.1. No real Setup/Entry qualification, strict point-in-time market replay, fill, position, PnL, product integration or trading claim follows from this remediation.
