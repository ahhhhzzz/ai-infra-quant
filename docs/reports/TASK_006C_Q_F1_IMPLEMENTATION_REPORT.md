# TASK-006C-Q-F1 implementation report — 2026-09-21

Status: **IMPLEMENTED / VALIDATION INCOMPLETE / AWAITING INDEPENDENT REVIEW**.
This delivers the versioned framework foundation. It does **not** deliver a formal Event strategy,
claim all acceptance gates PASS, or authorize integration or successor work.

## Exact provenance and scope

| Identity | Value |
|---|---|
| Repository | `ahhhhzzz/ai-infra-quant` |
| Task branch | `task/006c-q-f1-versioned-quant-event-framework` |
| Exact development baseline | `857823a0dc39b4c10a1986c575bcbcd9dda11c85` |
| Source branch verified after fetch | `integration/006b-q-closeout-006c-q-f1-handoff` |
| Frozen F1 contract Git blob | `c2c5448c1eb72fd0ece1572c31ba30246a761b51` |
| Pre-port golden checkpoint | `6a1eb14b4201a9e1ddad8162a30ac6e24a79c72c` (direct child of the exact baseline) |
| Implemented code / final focused-test and vector checkpoint | `cc77ee8278ddb7db1dcacdce6c364a89cbf3b51a` |
| Product authority, untouched | `roadmap/no-live-trading` at `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f` |

The [frozen contract](../../prompts/tasks/TASK-006C-Q-F1_VERSIONED_QUANT_EVENT_FRAMEWORK_FOUNDATION.md),
[R05 PASS review](../reviews/TASK_006B_Q_R05_INDEPENDENT_REVIEW.md) and
[closeout decision](../decisions/TASK_006B_Q_CLOSEOUT_AND_006C_Q_HANDOFF_2026_09_21.md)
were checked before implementation. AGENTS and the specified current documents were read.
Neither local nor remote task branch existed; an isolated worktree was created from the exact
baseline. Other worktrees and untracked files were preserved. R05 was not independently reviewed
again, and no R06, new equity data, provider call or user database access occurred.

The present user instruction authorizes implementation and normal push only to this task branch.
It also explicitly permits F1-02 PENDING when no second platform is available. The frozen contract
and historical evidence are unchanged. Final delivery SHA is supplied by post-push GitHub readback;
the report does not invent a self-referential commit hash.

## Implemented behavior

The new isolated modules provide recursively immutable canonical inputs, Structure/Event results
and evidence; explicit pure stage protocols; an immutable allowlist registry; schema/version/
capability checks; canonical JSON and all specified SHA-256 domains; content-verified implementation
artifacts; and the minimal B0/A1 structure port. The [developer guide](../engineering/PAQS_Q_FRAMEWORK.md)
documents schemas, usage, artifact closure, time/status semantics and later plugin addition.

B0 `paqs-q-structure-b0/1.0.0` is the only default selectable reference. A1
`paqs-q-structure-a1/0.1.0` remains experimental: explicit inventory inclusion, exact ID/version
selection and `allow_experimental=True` are all required. Failed selection occurs before invocation.
Enabling A1 does not modify B0, the registry or old results. No event-count-driven promotion exists.

No production Event plugin is registered. Requesting that stage returns
`UNAVAILABLE / EVENT_PLUGIN_NOT_CONFIGURED`, with the upstream binding retained and no success
payload. Two test-only fixture plugins prove swapping and upstream integrity; they are excluded
from the default production registry. Breakout/Failed Break/Retest/Transition/Trigger/Follow-through
remain unimplemented and require later approved contracts.

The price/calendar algorithm is a minimal port, with no `tools/research` import. B0 and A1 share
the four-observation domain; the sole arm condition is prior-raw veto. Legacy endpoint/support/event
identities remain lineage, separate from new framework record/result hashes. Frozen per-window
costs are diagnostics, not returns or a trading strategy. Unknown strict availability, missing
horizon and absent calendar support are explicit insufficiency; an eligible zero-event window
remains distinct. Known future evidence is rejected before result evidence can include it.

## Golden parity

Golden expectations were frozen and committed before production port code existed. The extractor
uses committed R05 full-frame/census/calendar/event/cost catalogs and verifies all 14 case crops.
Price values come from existing offline exports checked against their committed source SHA-256
manifest; no database was opened and no data was fetched. The committed fixture is self-contained.

Twelve frozen inputs cover W1/D1/M30, both qualification modes and the retained insufficient M30
case. Both arms match complete golden semantic projections: status/reason, events, census and
rejections, prices/endpoints, support/calendar identities, window hashes and declared costs.
Hand-calculated synthetic M30 flat/three-center cases additionally establish the sole veto change.

Golden fixture SHA-256:
`a441b129f6ea4c3cb9397e1093eda81f768cce08cf866978b95d022ab4dbc6ba`.
See [freeze provenance](../../tests/paqs_q/golden/README.md) and
[fixture](../../tests/paqs_q/golden/r05.json). No expected semantic output was derived from the new port.

## Acceptance gates

| Gate | Status | Actual evidence / limitation |
|---|---|---|
| F1-01 | PASS | Independent fixed canonical preimages/digests; repeat/ordering/hash-seed/Decimal-context equality; immutable output and IDs. |
| F1-02 | PENDING | Windows canonical vectors executed; WSL reports not installed and Docker is absent. No actual Linux run, VM, container deployment or external CI provisioning. |
| F1-03 | PASS | All 12 frozen inputs / 14 case crops match B0/A1 semantic projections; labelled synthetic parity and failure states pass. |
| F1-04 | PASS | Default registry selects only B0; no selectable A1 or production Event fixture. |
| F1-05 | PASS | Missing either exact ID/version or experimental permission fails closed before invocation. |
| F1-06 | PASS | Explicit A1 produces its own binding; B0 bytes and immutable input/registry remain unchanged. |
| F1-07 | PASS | Unknown/duplicate/disabled/content-conflicting/schema-incompatible bindings and capability incompatibility are rejected. |
| F1-08 | PASS | Config/version/artifact changes alter corresponding hashes; content/inventory tampering, CRLF and packaged-layout verification tested; absent old implementation is UNAVAILABLE. |
| F1-09 | PASS | Completed-bar/future price/calendar checks, prefix injection, unknown availability, HK lunch/overnight/early-close/DST and W1 factual-versus-nominal time boundaries tested. |
| F1-10 | PASS | Explicit INSUFFICIENT/UNAVAILABLE/INVALID reasons and no failure success-payload; valid zero-event distinction. |
| F1-11 | PASS | AST closure/import checks and executable no-file/no-network checks; no provider/DB/environment/clock/RNG use in pure evaluation. |
| F1-12 | FAIL | Product protection passes; retained regression run has 1095 passed and one unchanged historical global assertion forbidding any `*paqs_q*` source path. Browser regression has 65 passed. The failing test was not changed, skipped or renamed around. |

### F1-12 exact retained failure

`tests/architecture/test_task007b_boundaries.py::test_no_later_strategy_execution_or_broker_state_is_added_to_the_ledger`
fails at line 176:

```python
assert not list(SOURCE_ROOT.rglob("*paqs_q*"))
```

This older whole-source-tree absence assertion conflicts with the newly authorized F1 package
names even though the ledger, PAQS-E and every pre-existing product implementation remain
unchanged. Its preceding checks of ledger source still pass. The test is retained verbatim;
there is no test exclusion, allowlist exception or path renaming to hide the new framework.
Consequently F1-12 is FAIL, not a waived PASS. Resolving the historical assertion belongs to
explicit review/governance; this run does not silently loosen a gate or rewrite protected tests.

## Actual execution

Host: Windows; Python 3.12.14; pytest 8.4.1; Ruff 0.12.9; mypy 1.17.1; tzdata 2025.2.
The existing Python environment was reused; no dependencies were installed or changed.
`PYTHONUTF8=1`; `PYTHONPATH` includes `src`, repository root and `tests` for retained suites;
`MYPYPATH` includes `src` and repository root. All database tests use fresh temporary resources
and synthetic fixtures; browser tests run their own temporary Uvicorn/server processes and
headless Chrome. They do not touch the user's database, browser session or processes.

| Executed validation | Result |
|---|---|
| `python -m pytest tests/paqs_q -ra --tb=short` on final code checkpoint | 55 passed, 1 unchanged Starlette deprecation warning, 54.51s |
| `python -m pytest tests/research/paqs_q tests/unit/test_paqs_input.py -ra` | Original 268 passed, 1 unchanged warning, 162.53s |
| Retained product suite listed below | 1095 passed, 1 failed, 1 unchanged warning, 426.33s |
| `python -m pytest tests/browser/test_paqs_e_ui_cleanup.py tests/browser/test_market_archive_browser.py tests/browser/test_paqs_e_workbench.py -ra` | 65 passed, 1 unchanged warning, 134.22s; actual isolated Uvicorn/Chrome |
| Ruff check on the 20 added Python files | PASS |
| Ruff format --check on the same files | PASS; 20 already formatted |
| Native strict mypy --explicit-package-bases on the same files | PASS; 20 files |
| Same strict mypy plus --platform win32 | PASS; 20 files; still a Windows-host run |
| Windows canonical vector command | PASS; 28 outputs, exact input/result/byte/record identities in receipt |
| Portable source ZIP pack/unpack, LF/CRLF and explicit file inventory | PASS; included in focused tests; no built wheel claim |
| Baseline protection, diff and Markdown relative-link checks | PASS; receipt linked below |

Retained product selection (shell wildcards were explicitly expanded into file arguments):

```text
python -m pytest tests/architecture
  tests/unit/test_paqs_structure.py tests/unit/test_paqs_market_snapshot.py
  tests/unit/test_market_data_archive.py tests/unit/test_paqs_e_*.py
  tests/integration/test_database_invariants.py tests/integration/test_migrations.py
  tests/integration/test_migration_configuration.py tests/integration/test_sqlite_decimal_roundtrip.py
  tests/integration/test_market_dashboard.py tests/integration/test_offline_startup.py
  tests/integration/test_paqs_e_*.py tests/integration/test_market_archive*.py
  tests/integration/test_market_data_archive_api.py -ra
```

This is a selected regression suite, not a claimed full-product or PostgreSQL-server run. Retained
regressions ran during implementation; all pre-existing source/test identities they exercised are
identical at final delivery. Final focused checks/vectors ran against `cc77ee8`; later commits only
record documentation/evidence. No code changed to satisfy the historical assertion.

Earlier development checks exposed an incomplete artifact import inventory and normal typing/
formatting errors. These were corrected before the final checkpoint. The final acceptance statuses
above retain the unresolved actual failure and platform omission. Checks were not repeated to
increase test counts; passing retained suites were not rerun after documentation-only edits.

## Cross-platform evidence and reproduction

[Windows vector receipt](../evidence/TASK_006C_Q_F1/windows-vectors.json) contains 28 outputs.
Aggregate canonical vector digest:
`e83520c390d1e6ee034ba393add83f3296aa67d3ec8e589cccb9edf82b8710f8`.

| Plugin | Verified implementation artifact hash |
|---|---|
| B0 | `0953a2df9c4826223345517f4b08d45fe62b45398038e8b7a63954e668aea2e5` |
| A1 | `531d779123324e1596281b314f70dda2c6a03c043c5416fea1e0a6258bc21f80` |

No usable Linux environment was present. `wsl --list --quiet` reported WSL not installed;
`docker` was not found. No installation, external deployment, paid runner or new remote environment
was attempted. F1-02 remains PENDING under the user's explicit platform exception.

On a later available Linux environment with Python 3.12 and the repository's pinned dependencies,
check out the exact final task SHA, then run from its root:

```bash
export PYTHONPATH="$PWD/src:$PWD"
export PYTHONUTF8=1
python -m pytest tests/paqs_q -ra
python tools/validation/paqs_q_f1.py --vectors /tmp/paqs-q-f1-linux-vectors.json
python - <<'PY'
import json
from pathlib import Path
w = json.loads(Path('docs/evidence/TASK_006C_Q_F1/windows-vectors.json').read_text())
l = json.loads(Path('/tmp/paqs-q-f1-linux-vectors.json').read_text())
assert l['platform'] == 'Linux'
for key in ('vectors', 'code_hashes', 'vector_digest'):
    assert w[key] == l[key], key
print('Actual Windows/Linux canonical comparison PASS')
PY
```

The command is reproducible guidance, not a claim that it ran. OS metadata is outside canonical
hash inputs. The checked-in standalone canonical preimage vectors, LF/CRLF checks and win32 mypy
cannot substitute for actual second-platform execution.

## Product protection, files and limits

The [protection receipt](../evidence/TASK_006C_Q_F1/protection.json) compares exact baseline
Git blob/mode identities and working-tree content. All 690 pre-existing objects outside the six
permitted current documentation files remain unchanged, including the contract, R05 review/decision,
historical research sources/tests/evidence, PAQS-E, Analyze, old structure engine, Dashboard/API,
database/migrations, dependencies and existing resources. The new resources are isolated under
`resources/paqs_q`. No Mermaid block was added or changed. New code is not wired into the product.

Machine-readable [validation summary](../evidence/TASK_006C_Q_F1/validation.json) retains commands,
counts, statuses and omissions. Actual changed-file list follows; no unrelated files are included.

```text
docs/ARCHITECTURE.md
docs/MASTER_SPEC.md
docs/REQUIREMENTS_MATRIX.md
docs/ROADMAP.md
docs/STRATEGY_SPEC.md
docs/engineering/PAQS_ENGINEERING_GUIDE.md
docs/engineering/PAQS_Q_FRAMEWORK.md
docs/evidence/TASK_006C_Q_F1/protection.json
docs/evidence/TASK_006C_Q_F1/validation.json
docs/evidence/TASK_006C_Q_F1/windows-vectors.json
docs/reports/TASK_006C_Q_F1_IMPLEMENTATION_REPORT.md
src/ai_infra_quant/application/paqs_q_artifacts.py
src/ai_infra_quant/core/domain/paqs_q/__init__.py
src/ai_infra_quant/core/domain/paqs_q/canonical.py
src/ai_infra_quant/core/domain/paqs_q/inputs.py
src/ai_infra_quant/core/domain/paqs_q/results.py
src/ai_infra_quant/core/ports/paqs_q.py
src/ai_infra_quant/core/strategy/paqs_q/__init__.py
src/ai_infra_quant/core/strategy/paqs_q/calendar.py
src/ai_infra_quant/core/strategy/paqs_q/local.py
src/ai_infra_quant/core/strategy/paqs_q/plugins.py
src/ai_infra_quant/core/strategy/paqs_q/qualification.py
src/ai_infra_quant/core/strategy/paqs_q/registry.py
src/ai_infra_quant/resources/paqs_q/a1.json
src/ai_infra_quant/resources/paqs_q/b0.json
tests/paqs_q/__init__.py
tests/paqs_q/freeze_golden.py
tests/paqs_q/golden/README.md
tests/paqs_q/golden/canonical.json
tests/paqs_q/golden/r05.json
tests/paqs_q/golden/synthetic.json
tests/paqs_q/support.py
tests/paqs_q/test_boundaries.py
tests/paqs_q/test_canonical.py
tests/paqs_q/test_parity.py
tests/paqs_q/test_registry.py
tools/validation/paqs_q_f1.py
```

The bounded research limits remain: AVGO development data only, current-QFQ/PARTIAL and unknown
historical availability; strict historical confirmation and broad market applicability INCOMPLETE.
Neither B0 nor A1 is final Swing/Pivot truth, profitable strategy or trading advice.
`RECOMMEND_CROSS_SAMPLE_ONLY` remains optional future research guidance, not permission for R06.

Normal push is limited to the named task branch. No authority merge/update, force-push, formal
Event strategy, Setup/Risk/Advisory, return backtest, UI/API integration or successor task occurred.
Implementation work stops at this delivery and awaits independent review.
