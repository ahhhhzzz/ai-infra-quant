# TASK-007C2 implementation report

Status: **IMPLEMENTED — awaiting independent review. C2 is not merged.**
Execution date: 2026-09-08. Repository: `ahhhhzzz/ai-infra-quant`.

## Exact authority and integration evidence

GitHub was the authoritative source. Work was performed in a clean independent linked worktree,
starting on `task/007c2-workbench-ui-cleanup` at the exact contract commit. The user's other
worktrees and untracked `phase1_remediation_commit.txt` were not cleaned, stashed or overwritten.

| Reference | Exact SHA / result |
|---|---|
| Authoritative branch before authorized prerequisite integration | `roadmap/no-live-trading` at `0c1713d4409c69a45f8ce5e37951bba72d73d819` |
| Authoritative branch after ordinary fast-forward and GitHub readback | `2cc4eeea3cc31d4fd1f1a4e9c1fbec237f82a2c4` |
| C1 reviewed implementation and unchanged task branch | `3e98d8c5f9948dcaefe59eb3b7b847bd99ba8908` |
| R06 review branch | `review/007c1-remediation-06-independent` at `2240024cb361d79f57fc2eb0d65c2e5aa8697e33` |
| Prepared integration branch | `integration/007c1-user-accepted` at `2cc4eeea3cc31d4fd1f1a4e9c1fbec237f82a2c4` |
| Integration candidate tree | `52554f97d401c81d1f110f76dd6623d464b26820` |
| Ordered integration parents | `0c1713d4409c69a45f8ce5e37951bba72d73d819`, `2240024cb361d79f57fc2eb0d65c2e5aa8697e33` |
| Contract / expected starting C2 HEAD | `c5bd152210ee8b4d071a138867f72d7f8fbd9387` |
| Contract single parent / task merge base with authoritative branch | `2cc4eeea3cc31d4fd1f1a4e9c1fbec237f82a2c4` |
| Contract tree | `00e9b1db26b13ae275c160ee5c642ce53324aa56` |
| Implementation commit | The commit containing this report, single child of the contract SHA above; the final handoff supplies its literal SHA and SHA-pinned report link |

Direct GitHub branch/commit/compare reads verified the exact references, ancestry and file deltas.
The review is a direct child of the C1 implementation and adds only its review document.
The closeout is a direct child of `80f089bc2d285cca492c41aaeaf047e177bc2812` and adds only
`docs/decisions/TASK_007C1_CLOSEOUT_2026_09_08.md`. The integration candidate differs from the
reviewed application by exactly that closeout and `docs/reviews/TASK_007C1_REMEDIATION_06_INDEPENDENT_REVIEW.md`.
All application/resources/tests/dependencies/migrations in the candidate match the reviewed code.
Local `git merge-tree --write-tree` over the two exact GitHub parents independently produced the
candidate tree without conflicts. The candidate was 16 commits ahead / 0 behind the old authority;
the contract was one commit ahead / 0 behind the candidate and added only the C2 contract.

The authoritative HEAD was read again immediately before the authorized update. The prepared
candidate was applied with `force:false` and read back from GitHub. No replacement merge, squash,
rebase or forced update was created. Subsequent publication is restricted to the C2 task branch.
A report cannot embed its own containing commit hash; the literal final SHA is reported externally
and `git log -1 --format=%H -- docs/reports/TASK_007C2_IMPLEMENTATION_REPORT.md` resolves it.

C1 acceptance attribution is unchanged: the [R06 review](../reviews/TASK_007C1_REMEDIATION_06_INDEPENDENT_REVIEW.md)
and [user closeout](../decisions/TASK_007C1_CLOSEOUT_2026_09_08.md) distinguish code review, historical
execution evidence and the user's Research-ON acceptance. C2 did not repeat paid acceptance,
recompute private local Run hashes, or reopen the accepted C1 functionality.

## Implementation

The credential form now owns a single `minmax(0, 1fr)` column, independent of the global six/three
column rules. Title, service, storage explanation, password and status appear vertically above a
dedicated single-column action group. Save/Update has the theme accent; Delete and Close are
secondary. Width is capped at 36rem and the viewport minus 32px; height is capped at the viewport
minus 32px with internal vertical scrolling and wrapping. Font-relative spacing supports text
enlargement. The dialog has an accessible title/description, password autofocus, and an explicit
close-event focus return. Secret clearing and all credential HTTP behavior remain unchanged.

The obsolete local administration container, initial equity/cash/NAV/units/invested/return cards,
duplicate watchlist and mixed provider list are removed. Their rendering functions and initialization
call are retired. All retained `app.js` logic is unchanged; its diff consists only of deletions.
Normal load/refresh no longer reads these endpoints:

- `/api/v1/portfolio`
- `/api/v1/performance`
- `/api/v1/brokers`
- `/api/v1/fundamental-data/providers`
- `/api/v1/event-data/providers`
- `/api/v1/market-data/providers` (its only consumer was the removed mixed list)

Main watchlist GET/add/DELETE, canonical Security selection, market state/Daily/minute reads,
provider identity/quality/timestamps, current refresh, registered model/strategy controls, Narrative
and Legacy histories, known Run lookup and frozen evidence charts remain. No replacement admin
page was added. The current specifications now state A/B/C integration, C1 user acceptance and
actual integration, C2 pending review, and Narrative-first exact-text persistence without machine
semantic/RR certification. Paper/PaperFill, performance, 006B1, PAQS-Q successors, 007D and Phase
3/4 remain inactive; no broker/account/trading capability was introduced.

## Changed files and obsolete assertion replacements

Production (4):
- `src/ai_infra_quant/frontend/templates/index.html`: dialog semantics/action group; remove old administration.
- `src/ai_infra_quant/frontend/static/app.css`: scoped dialog layout/actions; remove retired CSS.
- `src/ai_infra_quant/frontend/static/app.js`: delete only old administration renderer/loader/call.
- `src/ai_infra_quant/frontend/static/paqs-e.js`: credential close-event focus restoration only.

Current documentation (8): `README.md`, `docs/ROADMAP.md`, `docs/MASTER_SPEC.md`,
`docs/STRATEGY_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/REQUIREMENTS_MATRIX.md`,
`docs/PAQS_E_WORKBENCH.md`, `docs/PAQS_E_MODELS.md`.

Tests (3):
- New `tests/browser/test_paqs_e_ui_cleanup.py`: 11 actual Chromium business cases.
- `tests/integration/test_market_dashboard.py`: the old ordering assertion required the market
  dashboard to precede the now-retired portfolio section. It now asserts that the section/old IDs
  are absent and that primary remove/history controls remain; all existing market-first checks remain.
- `tests/integration/test_offline_startup.py`: old `PAPER BROKER: NOT IMPLEMENTED` and
  `LIVE ROUTES: ABSENT` descriptor strings belonged to the removed mixed list. Replacements require
  the normal read-only badge, main Security selector, history and old-container absence. Existing
  startup health and BUY/SELL absence assertions remain.

New report: `docs/reports/TASK_007C2_IMPLEMENTATION_REPORT.md`.
New visual evidence: `docs/evidence/TASK_007C2/README.md` and these 12 synthetic PNG files:
`modal-1440x900-dark.png`, `modal-1440x900-light.png`, `modal-900x900-dark.png`,
`modal-900x900-light.png`, `modal-390x844-dark.png`, `modal-390x844-light.png`,
`modal-390x844-dark-actions.png`, `modal-390x844-light-actions.png`,
`modal-1440x900-text-200-percent.png`, `workbench-1440-dark.png`,
`workbench-900-light.png`, `workbench-390-dark.png`.
Total: 29 changed/added files. No historical contract, implementation report, review or closeout is edited.

## Real browser acceptance

The actual repository Uvicorn entrypoint serves production HTML/CSS/JavaScript and local chart/
Markdown assets. The fixture creates its own migrated SQLite database, removes OpenAI environment
credentials and uses provider `none`; business payloads and credential operations are intercepted.
No real key or provider response is used. The [scenario index](../evidence/TASK_007C2/README.md)
contains all image links and reproduction details.

| Acceptance | Execution evidence |
|---|---|
| 1440x900, 900x900, 390x844, each dark/light | Six open-dialog cases, long unbroken service text and repeated Chinese errors; measured viewport bounds/centering, single column, vertical order, full-width input and non-overlap |
| Reachable actions and narrow scrolling | Measured button bounds/order, distinct primary style, real scroll height; narrow action-area captures |
| Equivalent 200% text | Desktop root font changed from 16px to 32px; computed modal text doubles. This is explicitly text enlargement, not browser page/pinch zoom |
| Credential workflow | Synthetic save, update, delete, failed confirmation, Close/Escape, initial password focus, Tab/Enter, restored focus and secret clearing |
| Main UI | Three viewport cases add/delete/select including empty-list recovery; current refresh/provenance; Narrative/Legacy history; known Run; unchanged frozen evidence |
| Side effects and errors | Every C2 case asserts no retired endpoint requests, no external request, no Analyze POST, no page error and no console error |

The failure scenario is a malformed JSON confirmation GET after an intercepted credential mutation,
exercising the existing safe catch path without a real credential mutation or expected HTTP-resource
console noise. Existing C1 browser tests continue to cover shared-slot status and browser-secret
storage absence. Screenshots contain empty password fields and synthetic fixtures only. Full-page
capture heights are not the browser viewport height; narrow dialogs scroll internally. The complete
workbench captures contain an inherited inert hostile-text fixture, demonstrating retained safe
rendering rather than a real model result.

## Validation environment and results

Actual Windows 11 (`Windows-11-10.0.26200-SP0`), AMD64; CPython 3.12.14 (MSC v.1944),
pytest 8.4.1, Playwright 1.55.0, Chromium 140.0.7339.16, Ruff 0.12.9, mypy 1.17.1.
Already-declared dev dependencies and installed Playwright Chromium were reused. Dependencies and
configuration were not changed. `PYTHONPATH` explicitly selected the C2 `src` and repository root;
`ai_infra_quant.__file__` was verified inside `task007c2-worktree/src`, not the older editable checkout.
`TASK007C_BROWSER_CHANNEL=chromium` and the installed browser cache were selected explicitly.

| Exact command | Result |
|---|---|
| `python -m pytest -ra` | 1351 collected; **1350 passed, 1 skipped, 1 warning in 409.01s (0:06:49)**; exit 0 |
| `python -m ruff check .` | All checks passed |
| `python -m ruff format --check .` | 201 files already formatted |
| `python -m mypy src tests` | Success: no issues found in 197 source files; actual Windows execution |

The initial focused C2 browser run returned `11 passed, 1 warning in 37.37s`. Initial full validation
found one obsolete offline-startup descriptor assertion (`1349 passed, 1 failed, 1 skipped`);
that assertion was replaced as documented above, then the complete suite was rerun. Initial mypy
also required narrowing an intercepted JSON payload to `dict`; that test typing correction is included.
The final results above supersede those development failures. All 110 browser cases (including
the 11 C2 cases) executed and passed within the final full suite.

The only permitted environment skip is the pre-existing PostgreSQL migration smoke,
`tests/integration/test_postgresql_migrations.py:67`: `PHASE1_POSTGRESQL_TEST_URL is not configured`.
It is not a passed PostgreSQL execution. The sole warning is Starlette's deprecated
`anyio.abc.BlockingPortal` alias. No browser tests are skipped/xfail/deselected. Windows PowerShell
checks execute on Windows; no Linux `--platform win32` substitute is claimed.

An independent owned Uvicorn smoke used a fresh temporary SQLite file, upgraded through 0003,
and checked Alembic `current`/`heads`. HTTP 200 responses were verified for `/health`, `/`,
`/openapi.json`, `/api/v1/paqs-e/configuration`, `/static/app.css`, `/static/app.js`,
`/static/paqs-e.js`, `/static/narrative-markdown.js` and the vendored chart script. Configuration
contained exactly 11 models with default `deepseek-v4-flash`. The existing production PowerShell
health handshake returned 0 for matching source SHA and 2 for stale SHA. Only the owned process
was stopped; unrelated user processes/databases were untouched. Development smoke correctly
reported the contract HEAD with tested local changes; the published tree is matched to those bytes.

## Protection audit and handoff boundary

All 302 pre-existing tracked files outside the modified-file allowlist retain their Git blob IDs.
The audit compared Git-cleaned working bytes against the exact contract tree, accounting for normal
Windows CRLF checkout conversion. This includes every backend/application/core/database/integrations
file, registry, strategy/Doctrine/prompt, NarrativeGateway/research flow/parser/credentials, launcher,
source identity, seed/dependency/vendor/Markdown renderer and all historical evidence/contracts.
Migration blob IDs remain:

- 0001: `add8f78b786482f1598824bde9df6df695a87a3f`
- 0002: `ce61b7a8789385cf4df9d0550d196e27fa969e7b`
- 0003: `78890f99a6365fcc82142f1fddc5781f5ff74397`

`paqs-e.js` is byte-identical after excluding the one credential close handler. Research default
OFF/reset, explicit Analyze, one-request/long-running guards, late-response identity, exact text/hash
and frozen evidence semantics therefore remain unchanged. `app.js` has only deleted retired code.
No database, migration, schema, credential architecture, model, provider, retry/fallback, strategy,
trading or runtime-prompt change exists. No raw responses, real secrets, logs or databases are committed.
All browser/provider evidence in this change is synthetic; there were no paid provider calls.

The final publication is a single implementation child of the exact contract, using only
`task/007c2-workbench-ui-cleanup`. The authoritative branch stays at the separately authorized C1
integration SHA. GitHub tree/commit/ref readback and local tree equality are required before the final
handoff. No C2 merge, next-task start or independent PASS is claimed. Stop for independent review.
