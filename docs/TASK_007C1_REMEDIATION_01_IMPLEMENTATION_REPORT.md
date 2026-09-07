# TASK-007C1 Remediation 01 implementation evidence

Status: **IMPLEMENTED — STOP FOR INDEPENDENT RE-REVIEW; LIVE SMOKES STILL REQUIRED**

Only R1–R4 are implemented. This report does not declare product acceptance, integration or a
successful live provider run. The literal final commit SHA accompanies this report in the handoff;
the report is version-bound to its containing remediation implementation commit. Resolve that
commit with `git rev-parse HEAD` on the published task branch, and verify its parent below.

## Git authority and preconditions

GitHub was the sole source for ref/commit/compare verification. Before implementation:

| Evidence | Exact value |
|---|---|
| Repository | `ahhhhzzz/ai-infra-quant` |
| Authoritative branch | `roadmap/no-live-trading` |
| Original authoritative SHA | `80f089bc2d285cca492c41aaeaf047e177bc2812` |
| Original TASK-007C1 Contract SHA | `9f41016b2341e91ad2825b7f731bca4f378b0108` |
| Original implementation SHA | `fc527c61fcdc2b4f54506dc5622f0b1faa6945d5` |
| Remediation 01 Contract / starting HEAD | `b7316e83f7fd377f4c628db90dee8e3d7b4a5335` |
| Contract parent | `fc527c61fcdc2b4f54506dc5622f0b1faa6945d5` |
| Original implementation parent | `9f41016b2341e91ad2825b7f731bca4f378b0108` |
| Merge base with authoritative | `80f089bc2d285cca492c41aaeaf047e177bc2812` |
| Starting task ahead / behind authoritative | `3 / 0` |
| Remediation implementation sole parent | `b7316e83f7fd377f4c628db90dee8e3d7b4a5335` |
| Resulting task ahead / behind authoritative | `4 / 0` |
| Resulting task ahead / behind original implementation | `2 / 0` |

The isolated checkout was clean at the exact contract SHA before edits. Both contracts were read.
The contract commit changes only the remediation contract. Git HTTPS transport was unavailable;
GitHub connector data supplied the exact missing blob/tree/commit, verified by Git object hashes.
Publication uses GitHub Git-data objects and a non-force fast-forward of only
`task/007c1-paqs-e-multi-model-web-research`. The final handoff records the verified resulting SHA.
No merge, authoritative branch update, remote/global Git configuration change, or unrelated
checkout reset/stash/termination is authorized or performed.

## Exact changed files relative to original implementation

The first file below belongs to the pre-existing remediation contract commit. The other eighteen
files comprise this remediation implementation; accepted evidence is not rewritten.

```text
prompts/tasks/TASK-007C1_REMEDIATION_01_LIVE_DOGFOOD_RUNTIME_COMPATIBILITY.md
README.md
docs/API_CONTRACTS.md
docs/ARCHITECTURE.md
docs/PAQS_E_MODELS.md
docs/PAQS_E_WORKBENCH.md
docs/REQUIREMENTS_MATRIX.md
docs/TASK_007C1_REMEDIATION_01_IMPLEMENTATION_REPORT.md
scripts/dashboard_runtime.ps1
src/ai_infra_quant/application/paqs_e_runtime.py
src/ai_infra_quant/backend/main.py
src/ai_infra_quant/backend/runtime_identity.py
src/ai_infra_quant/frontend/static/paqs-e.js
src/ai_infra_quant/integrations/openai_reasoning/gateway.py
start_dashboard.bat
tests/browser/test_paqs_e_long_running.py
tests/browser/test_paqs_e_workbench.py
tests/integration/test_runtime_source_revision.py
tests/unit/test_paqs_e_remediation_01.py
```

## R1: source revision handshake

The launcher resolves current checkout HEAD using Git and accepts only a 40-character lowercase
hexadecimal revision. It passes `AI_INFRA_SOURCE_REVISION` to its own Uvicorn child. Application
creation freezes the validated value in a closure; health never rereads Git or the environment.
Manual startup without a valid value reports only `unknown`. No path or arbitrary environment
content is exposed.

The PowerShell helper returns 0 only for healthy status/database plus an exact valid revision
match. Missing, invalid or different revisions return 2 with safe revision/status text and an
instruction to close/restart the existing dashboard process. The launcher stops before opening
the browser. Unhealthy/non-AI services retain the port-conflict path. Startup waiting uses the
same revision check. The repository helper runs in a dedicated PowerShell child; its execution
policy argument affects only that child and does not change machine/user policy.

No automatic process termination is added. Existing Futu OpenD lookup/start/readiness sections
and the quote-only Uvicorn launch remain unchanged. Tests execute the production helper with
synthetic HTTP responses. A separate real HTTP smoke also proves same-SHA exit 0 and stale-SHA
exit 2 against the actual running Uvicorn service. Environment changes after application creation
cannot relabel the old process.

## R2: DeepSeek action compatibility

Only DeepSeek accepts completed `search`, `open_page` and `find_in_page` native actions, with at
most ten total action records. At least one native search is mandatory. Only search actions
supply queries; each must supply at least one valid bounded query and the total cannot exceed
four. Other providers retain search-only, at most four action records.

Page/find target URLs, contents and source-like fields are ignored for evidence construction.
They cannot promote arbitrary URLs into trusted material. Only native search source records
and native URL citations ground generated summary URLs. Raw source/citation records are counted
before URL deduplication and bounded to 64. Included items remain <=8, summaries <=1600 characters,
normalized item <=4000 characters and total <=24000. Exceeding bounds fails closed.

Known future publications remain excluded; unknown publication time retains its explicit cutoff
limitation. No raw model reasoning trace is persisted. Frozen auxiliary evidence reaches the
final reasoning request with `tools=[]` and `tool_choice=none`. No application continuation,
automatic retry, second provider or model fallback is added.

The documented action incompatibility is confirmed by the official
[DeepSeek response schema](https://api-docs.deepseek.com/api/create-response/).
The [DeepSeek compatibility guide](https://api-docs.deepseek.com/guides/responses_api/) documents
the server-side ten-round continuation cap. Application acceptance limits do not guarantee
provider-side billing limits. Deterministic fixtures are synthetic, not reconstructed live data.

## R3: long synchronous Analyze

The 180-second timer updates the captured attempt's status text without aborting fetch, releasing
the global guard, resubmitting, or retrying. Fetch stays pending until a terminal response or real
connection/browser failure. The timer is cleared on completion. No polling, worker or queue is added.

Three real Chromium fake-clock scenarios keep the request pending through 180 seconds, reject a
second form submission, retain the disabled button through 241 seconds, then render SUCCEEDED,
PROVIDER_FAILED or VALIDATION_FAILED correctly. Advancing the clock after completion cannot
overwrite terminal text. The retained unknown-outcome browser test now waits past 180 seconds
and explicitly injects a connection failure; history/prior Decision retention and no retry remain
asserted. This is the only modified older test: the obsolete automatic-timeout expectation is
replaced by non-aborting wait plus genuine network-failure evidence.

## R4: Snapshot fact projection

After strict provider schema/domain parsing and before the unchanged validator, the runtime
projects `current_price_reference.price`, `.timestamp`, `.freshness_status` and `.session_type`
from the bound Snapshot. Availability mapping is AVAILABLE->FRESH, STALE->STALE, DELAYED->DELAYED,
otherwise UNKNOWN. Market mapping is OPEN->REGULAR, PRE_MARKET->PRE, AFTER_HOURS->POST,
CLOSED->CLOSED_REFERENCE, otherwise UNKNOWN.

For an executable entry already marked eligible by the model, the same four factual echoes are
projected. Eligibility and policy-basis text are never altered. Ineligible entry fields remain
untouched. The projector returns new frozen dataclasses without mutating provider output or Snapshot.

No identity, support/input quality, context/regime/bias, key level, event, trigger/follow-through,
setup, entry/holder advisory, invalidation, target, RR/arithmetic, uncertainty, explanation or
reason-code field is projected. Structural invalidation/target numeric references remain untouched.
Market-open/session/freshness rules can still reject model-eligible entries.

All eleven registered routes pass strict synthetic output with wrong price/time/session and
STALE freshness on an AVAILABLE Snapshot through projection. The same unprojected result still
fails direct validation with CURRENT_PRICE_FACT_MISMATCH, CURRENT_PRICE_FRESHNESS_MISMATCH and
CURRENT_PRICE_SESSION_MISMATCH. Availability/market-state regressions retain the entry restrictions.

The entire `validate_reasoning_result` function source is unchanged from `fc527c61...`:
SHA-256 `1f52c6c6094ce9b25fe0a7a22ddfdea0e52d8484eb5032ab4bac5e8b9ff1d271`.
Strategy/Doctrine/runtime prompt, core domain, Snapshot construction, Decision Ledger and revision
lineage, migration files, model registry and accepted independent reviews remain unchanged.

## Deterministic validation

Environment: Windows; Python 3.12.14; pytest 8.4.1; Playwright 1.55.0;
Chromium 140.0.7339.16; Ruff 0.12.9; mypy 1.17.1. Declared dependencies and Chromium launch normally.
All credential fixtures are synthetic; no paid provider call or real-key solicitation occurred.

Commands use the isolated environment Python from the repository root. Temporary databases,
native logs and generated browser artifacts remain outside the repository.

| Validation | Result |
|---|---|
| Remediation plus existing C1 focused suites (command below) | 255 passed, 1 warning in 40.57s |
| `python -m pytest -ra --basetemp ../task007c1-test-tmp/r01-full` | 752 collected; 751 passed, 1 skipped, 1 warning in 258.31s |
| `python -m pytest tests/browser -ra --basetemp ../task007c1-test-tmp/r01-browser` | 54 passed, 1 warning in 37.44s; no skip/xfail/failure/error |
| Remediation unit/runtime/launcher regression rerun | 106 passed, 1 warning in 3.42s |
| Final remediation unit rerun after fixture-order clarification | 89 passed, 1 warning in 1.02s |
| Existing Windows launcher suite | 3 passed within focused/full/regression runs |
| `python -m ruff check .` | Passed |
| `python -m ruff format --check .` | 174 files already formatted |
| `python -m mypy src tests` | Passed; 171 source files |
| Fresh SQLite `alembic upgrade head`, `current`, `heads` | `0002_task007b_paqs_e_ledger (head)` |
| Real Uvicorn HTTP smoke | Health, OpenAPI, root and configuration 200; eleven models; default DeepSeek V4 Flash |
| Real HTTP revision handshake | Same revision exit 0; stale revision exit 2 |
| Protected-file audit | 48 protected files unchanged; entire validator source unchanged |
| Secret/private-artifact and diff whitespace checks | Passed |

Focused command (plus the isolated `--basetemp` directory):

```text
python -m pytest tests/unit/test_paqs_e_remediation_01.py tests/integration/test_runtime_source_revision.py tests/integration/test_windows_launcher.py tests/browser/test_paqs_e_long_running.py tests/unit/test_paqs_e_model_gateway.py tests/integration/test_paqs_e_multi_model.py tests/browser/test_paqs_e_multi_model.py -ra
```

The sole full-suite skip is the pre-existing optional PostgreSQL migration test because
`PHASE1_POSTGRESQL_TEST_URL` is not configured. The sole warning is Starlette's deprecated
`anyio.abc.BlockingPortal` alias. Initial fixture failures were corrected; all final checks above
pass. No test was weakened, skipped or marked xfail to hide a remediation failure.

## Remaining acceptance and limitations

No post-remediation live provider smoke has been performed. On the exact published SHA, the user
must run one explicit DeepSeek V4 Flash Analyze with web research OFF, then one with research ON,
using credentials only through the secure local UI. Record safe terminal status/Run ID and, for
research success, frozen native-source auxiliary evidence. Never retain a real key or raw reasoning.
Do not automatically retry paid calls. A remaining semantic validator failure must be reported,
not repaired by relaxing strategy validation.

Provider entitlement/network behavior and DeepSeek internal search cost remain external limits.
Manual environments without a valid startup source identity truthfully report unknown and cannot
be silently reused by the launcher. No database migration, new model, provider fallback, arbitrary
provider URL, automatic analysis, PAQS-Q, backtest, portfolio/PnL, broker or trading execution scope
is added. No real API key is committed, logged or stored in browser/application DB.

The authoritative branch remains at its original SHA. No merge occurs. Stop for independent
re-review after the single authorized task-branch fast-forward; do not start another task.
