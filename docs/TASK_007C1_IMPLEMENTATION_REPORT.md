# TASK-007C1 implementation report

Status: implementation submitted for independent review; no merge or integration claim.

## Git identity and scope

- Repository: `ahhhhzzz/ai-infra-quant`.
- Authoritative branch/base: `roadmap/no-live-trading`, `80f089bc2d285cca492c41aaeaf047e177bc2812`.
- Issued Contract/start commit: `9f41016b2341e91ad2825b7f731bca4f378b0108`.
- Task branch: `task/007c1-paqs-e-multi-model-web-research`.
- Contract's sole parent and merge base: `80f089bc2d285cca492c41aaeaf047e177bc2812`.
- Before editing, GitHub compare/ref/commit data independently confirmed both exact branch heads,
  the Contract parent and merge base. The isolated checkout was clean at the exact issued SHA.
- The implementation commit containing this report has the issued Contract commit as its sole
  parent. Thus the task is two commits ahead / zero behind authoritative (Contract + implementation),
  with the same merge base. The exact final commit SHA is supplied in the GitHub-verified handoff;
  a commit cannot embed its own SHA in its tracked contents.
- Git-over-HTTPS failed (connection reset/unreachable). The verified cached parent objects plus
  GitHub Contract content reconstructed the exact starting commit/tree hashes. Publication uses
  GitHub Git-data objects and a non-forced fast-forward of only the authorized task ref, with the
  published tree compared to the locally validated tree. No unrelated checkout or branch is modified.

## Implemented behavior

The flat eleven-model registry and exact provider IDs, fixed endpoints and credential slots are
listed in [the model guide](PAQS_E_MODELS.md). DeepSeek V4 Flash is the default; no model discovery,
arbitrary provider URL, unapproved model, prefix-derived routing or automatic fallback exists.

The provider-neutral gateway uses the existing reasoning port, strict output schema and domain
conversion. Every successful result still passes the unchanged deterministic validator. Qwen uses
its documented Chat JSON Schema path for final reasoning and native Responses search for research,
with the same selected model/key. DeepSeek, Hy4 and OpenAI use Responses JSON Schema; GLM and Kimi
use JSON Object plus mandatory strict local validation. Strategy and prompt content are unchanged.
No required model was found renamed or removed in the official documentation checked during this
implementation. API compatibility details and source links are recorded in the model guide.

Windows Credential Manager implements `CredentialStore` through Win32 APIs, using current-user
local-machine generic credentials in a fixed target namespace. The production backend fails closed
on unsupported platforms or OS failure, with no plaintext fallback. The API uses write-only
`SecretStr`, bounded input, loopback peer/Host checks, same Origin, JSON and Fetch Metadata checks.
No GET writes or paid probes. Shared-slot statuses update across models; the optional OpenAI server
environment fallback is read-only. The password field clears after save/close and is never restored.

Analyze now accepts exactly `{security_id, model_key, strategy_id, web_research}`; the old arbitrary
`model_id` input is rejected. It freezes Snapshot, resolves selected identity, performs requested
research, freezes normalized auxiliary context, then forms the canonical request and performs one
tool-free reasoning attempt. Actual provider/model persist in existing identity fields; revisions
remain Security + strategy across models. Failed research cannot silently proceed or invent a Run ID.

Research bounds: one HTTP attempt, no client continuation/retry, at most four reported queries/four
search-call records, 64 raw source records, eight included items, 1,600 characters per summary,
4,000 per complete item and 24,000 total normalized characters; 2 MB response and 6,000 research
output tokens. OpenAI receives a native four-tool-call cap. DeepSeek ignores that control and Qwen
has no documented equivalent: provider-internal billed searches are not guaranteed to stop at four.
The application enforces the reported-evidence acceptance bound. This limitation is explicitly
retained for independent review, not misrepresented as a provider-side cost guarantee.

Native sources/citations bind URLs and available titles/publication timestamps. Generated summaries
cannot add unverified URLs or dates. Explicit future timestamps exclude a source, including
conflicting citation metadata; unknown publication times carry a visible limitation. Retrieval time
is provenance only. Frozen Snapshot price/bar/session/Decimal facts are never overwritten. No
chain-of-thought is persisted. Current market refresh cannot mutate frozen research or market evidence.

## Bounded supersession of older tests

All existing test names and unrelated assertions remain. The following older expectations changed:

| File / test or fixture | Exact replacement |
|---|---|
| `tests/integration/test_api_surface.py::test_openapi_has_exact_approved_allowlist` | Add only `/paqs-e/credentials/{model_key}` with GET/PUT/DELETE; retain every forbidden scope assertion. |
| `tests/integration/test_paqs_e_analysis_api.py::AnalysisHarness.payload` and `MODEL_ID` | Four-field request with registered `gpt-5.6-luna` and explicit research false; synthetic results still undergo the real validator. |
| `test_repeated_explicit_posts_are_fresh_without_hidden_history_or_deduplication` | Registered Qwen model replaces arbitrary model string; freshness, identity, no-memory and revision assertions retained. |
| `test_strategy_selection_is_independent_and_history_is_bounded_and_filterable` | Registered DeepSeek model replaces arbitrary string; independent strategies/filtering/revisions retained. |
| `test_invalid_model_rejected_before_snapshot_or_provider` | Same invalid cases target `model_key`; no snapshot/provider/ledger side effects retained. |
| `test_openapi_exposes_bounded_read_only_ledger_contract_without_secret_fields` | Exact four Analyze fields plus only credential operations; the sole write-only secret schema has password/writeOnly assertions and read/ledger secret bans remain. |
| `tests/integration/test_paqs_e_configuration.py::test_configuration_is_exact_read_only_and_secret_free` | Exact registry projection, per-slot credential presence and research support replace OpenAI-only presence; zero SQL/provider calls and no secret/body/path leakage retained. |
| `tests/browser/workbench_support.py::respond`, `analyze`, `MODEL` | Project the production registry in synthetic network fixtures; select registered GPT-5.6 Luna instead of filling arbitrary text. All frozen synthetic evidence remains validated. |
| `test_actual_uvicorn_unconfigured_http_and_static_smoke` | Per-model missing credentials and DeepSeek default replace empty model/OpenAI env instructions; real HTTP/static/no-POST checks retained. |
| `test_all_non_explicit_actions_have_zero_analyze_posts` | Select a registered Qwen option and verify it survives navigation instead of arbitrary model text; all other actions and zero-POST checks retained. |
| `test_explicit_capture_double_enter_guard_and_security_switch` | Exact captured four-field POST and human model label; later registered GLM selection cannot alter pending identity; guard/security checks retained. |
| `test_configuration_get_failure_and_invalid_models_never_dispatch` | Inject invalid select options to exercise the existing rejection cases; zero Analyze and invalid-config checks retained. |
| `test_changed_form_does_not_relabel_captured_success` | Change to registered Kimi; original human-readable model identity remains on the successful result. |
| `tests/conftest.py::isolated_os_credentials` (new fixture) | Inject synthetic storage so deterministic tests never read/write user OS secrets. Existing test logic is unchanged. |

New tests cover the exact catalog, all eleven routes and failure cases, stateless transport,
credential CRUD/security/no leakage, registry corruption, research bounds/provenance/As-Of,
cross-model revision continuity, frozen evidence, unsupported/failing research and browser controls.
The accepted chart, Decimal, time zone, XSS, history, race, no-broker and ledger assertions remain.

## Validation evidence

Environment: Windows, Python **3.12.14**, Playwright **1.55.0**, Chromium **140.0.7339.16**.
Declared `.[dev]` dependencies installed in an isolated environment; browser launch used Chromium
normally with no sandbox-disabling flag. Each pytest command used its own temporary DB directory.

| Validation | Exact command (temporary `--basetemp` paths omitted here) | Result |
|---|---|---|
| Focused TASK-007C1 | `python -m pytest tests/unit/test_paqs_e_model_gateway.py tests/integration/test_paqs_e_multi_model.py tests/browser/test_paqs_e_multi_model.py -ra` | **146 passed, 1 warning in 42.54s**, exit 0 |
| Full suite, final tree | `python -m pytest -ra` | **645 passed, 1 skipped, 1 warning in 270.97s (0:04:30)**, 646 collected, exit 0 |
| Standalone browser suite | `python -m pytest tests/browser/test_paqs_e_multi_model.py tests/browser/test_paqs_e_workbench.py -q` | **51 passed, 1 warning in 35.13s**, exit 0; all 51 also passed in the final full suite |
| Lint | `python -m ruff check .` | All checks passed |
| Format | `python -m ruff format --check .` | 170 files already formatted |
| Types | `python -m mypy src tests` | No issues in 167 source files |
| Windows launcher | `tests/integration/test_windows_launcher.py` in full suite | **3 passed** |
| Fresh migration + actual Uvicorn/HTTP | Real browser startup fixture and unconfigured HTTP smoke | Passed; migration head **0002_task007b_paqs_e_ledger** |
| Diff/secret/protected-file audit | `git diff --check`, changed-file secret scan and protected-path comparison | Passed; no private artifacts or protected changes |

The sole skip is the existing optional PostgreSQL smoke: `PHASE1_POSTGRESQL_TEST_URL` is not
configured. The sole warning is Starlette's deprecated `anyio.abc.BlockingPortal` alias. There
are no browser skips, xfails, deselections, failures or errors; all 51 browser business tests ran.
Local complete execution logs are outside the repository (`task007c1-full-final.log` and
`task007c1-focused-final-2.log`); no test output was rewritten or represented as live-provider evidence.

The browser suite launches actual Uvicorn on a fresh loopback port after SQLite migration through
`0002_task007b_paqs_e_ledger`; `/health`, `/openapi.json`, `/`, PAQS-E configuration and static assets
return successfully. Business scenarios use synthetic intercepted payloads and the real JavaScript.
Wide dark and narrow light viewport artifacts were inspected; the retained viewport assertions pass.
No key appears in screenshots. The first browser run found narrow controls below the viewport; the
layout was compacted and the unchanged assertions passed. The first full run found the older API
allowlist missing the newly authorized credential endpoint; only its bounded expectation was updated.

No paid live-provider smoke was run: no real key was supplied through the new UI. Contract section
22's opt-in domestic-provider smoke remains separate execution evidence for product acceptance.
Do not confuse deterministic transport fixtures with live entitlement/balance/provider validation.

## Exact changed files

- `README.md`
- `docs/API_CONTRACTS.md`
- `docs/ARCHITECTURE.md`
- `docs/PAQS_E_MODELS.md`
- `docs/PAQS_E_WORKBENCH.md`
- `docs/REQUIREMENTS_MATRIX.md`
- `docs/TASK_007C1_IMPLEMENTATION_REPORT.md`
- `pyproject.toml`
- `src/ai_infra_quant/application/paqs_e_analysis.py`
- `src/ai_infra_quant/application/paqs_e_models.py`
- `src/ai_infra_quant/application/paqs_e_research.py`
- `src/ai_infra_quant/application/paqs_e_runtime.py`
- `src/ai_infra_quant/backend/api/v1/paqs_e.py`
- `src/ai_infra_quant/backend/dependencies.py`
- `src/ai_infra_quant/backend/schemas/paqs_e.py`
- `src/ai_infra_quant/core/ports/credentials.py`
- `src/ai_infra_quant/frontend/static/app.css`
- `src/ai_infra_quant/frontend/static/paqs-e.js`
- `src/ai_infra_quant/frontend/templates/index.html`
- `src/ai_infra_quant/integrations/openai_reasoning/gateway.py`
- `src/ai_infra_quant/integrations/windows_credentials.py`
- `src/ai_infra_quant/resources/paqs_e/model_registry.json`
- `tests/browser/test_paqs_e_multi_model.py`
- `tests/browser/test_paqs_e_workbench.py`
- `tests/browser/workbench_support.py`
- `tests/conftest.py`
- `tests/integration/test_api_surface.py`
- `tests/integration/test_paqs_e_analysis_api.py`
- `tests/integration/test_paqs_e_configuration.py`
- `tests/integration/test_paqs_e_multi_model.py`
- `tests/paqs_e_support.py`
- `tests/unit/test_paqs_e_model_gateway.py`

## Preserved boundaries and handoff

No migration was added; both protected migrations remain byte-identical, as do accepted review
records/contracts, strategy Markdown, runtime prompt content and the Snapshot/domain validator.
No broker/account connectivity, live trading, execution, automatic analysis, PAQS-Q, TASK-006B1,
backtest, portfolio/PnL, model voting or unapproved model was added. No real API key was committed,
logged or persisted in browser storage/application DB. Only synthetic test sentinels occur in tests.
No database, log, `.env`, user export or screenshot is staged.

GLM, Kimi and Hy4 research are disabled pending an audited direct native source path; their reasoning
routes are implemented. All additional model families remain deferred. Provider-native cost limits
and separate live-provider smoke remain the explicit limitations above. Publication moves only
`task/007c1-paqs-e-multi-model-web-research`; `roadmap/no-live-trading` stays at the issued base.
No merge was performed. Stop here for independent review; no subsequent task is started.
