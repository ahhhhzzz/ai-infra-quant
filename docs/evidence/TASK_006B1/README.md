# TASK-006B1 browser / execution evidence

These are synthetic acceptance artifacts, not real Futu/OpenD market observations or paid-model
results. Temporary SQLite databases were used; no user database or account was opened.

Python 3.12.14, Playwright 1.55.0, Chromium 140.0.7339.16 (build 1187), Windows. The declared
browser binary was installed in an external workspace cache after its initial absence. Chromium
then launched normally; no skipped, rewritten or weakened browser tests.

`tests/browser/test_market_archive_browser.py` runs the real application factory under Uvicorn,
with a test-only injected provider returning 1 completed D1 and 601 completed M1 bars, calendar and
exact 38,18-boundary values. Test fixture control routes exist only in that test module; normal
application routes do not include them. Each successful save invokes exactly one D1, M1 and
calendar capability within one context. Offline mode makes provider construction fail; list,
detail and 500+101-row paging still succeed and issue zero provider calls / Analyze POSTs.

The final full suite also launches normal `ai_infra_quant.backend.main:app` against a fresh
migrated temporary database and verifies health/home/static/OpenAPI. The new browser acceptance
verifies 0004 head, actual archive POST/GET routes, guard/error recovery, stale selection/removal,
keyboard operation, no document overflow, and no unexpected console/page errors on successful paths.

| Width | Dark | Light |
|---|---|---|
| 390 px | [dark](archive-390-dark.png) | [light](archive-390-light.png) |
| 900 px | [dark](archive-900-dark.png) | [light](archive-900-light.png) |
| 1440 px | [dark](archive-1440-dark.png) | [light](archive-1440-light.png) |

Images capture the folded-section content after explicit save, offline reload, M1 selection and
second-page read. UUIDs, prices and dates are test-only data; list entries accumulate in the temporary
fixture database across viewport cases. Large exact prices intentionally exercise horizontal
scrolling rather than financial-value rounding. The table supports keyboard horizontal scrolling.

Final test totals, static results, source protection and environment limitations are recorded in
[the implementation report](../../reports/TASK_006B1_IMPLEMENTATION_REPORT.md). This is implementation
evidence, not independent acceptance or permission to merge.

Additional real-process probe: late US→HK watchlist selection response suppression passed;
restarting normal Uvicorn on the same temporary SQLite database preserved the exact capture.
With watchlist initialization intentionally returning 503, known-ID lookup and M1 500/101 paging
still passed at 390 px with zero POSTs / unexpected page errors. Probe exit 0 after resolving
Windows test-process teardown permissions; only its own temporary process trees were stopped.
