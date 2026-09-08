# TASK-007C1 Remediation 03 implementation report

Status: implemented; required deterministic validation passed; stop for independent review. No merge or independent
PASS is claimed. Only the three Remediation 03 changes are included.

## Exact source identity and preconditions

- Repository: `ahhhhzzz/ai-infra-quant`.
- Only publication branch: `task/007c1-paqs-e-multi-model-web-research`.
- Exact final implementation SHA: the immutable Git commit containing this report. Its literal
  40-character SHA is supplied in the final handoff and SHA-pinned report link. A commit cannot
  embed its own hash in its tree; this binding avoids an incorrect self-referential SHA.
- Exact parent / R03 Contract commit: `5285ed7d4553e7a9d3860b9263135d4d94b2f3e5`.
- Exact R03 base / Contract parent: `74a19387adc408e9453c30fdbb30e6636ac4e695`.
- Authoritative branch: `roadmap/no-live-trading`.
- Exact authoritative SHA and merge base: `80f089bc2d285cca492c41aaeaf047e177bc2812`.

Before editing, GitHub ref, Git commit and compare reads confirmed the expected task HEAD,
Contract parent, authoritative HEAD, merge base, ahead=7/behind=0, and exactly one added Contract
file since the R03 base. The isolated local checkout was clean and matched the exact GitHub tree
`07fb26f1eea9239dffd901d5b83ee41ef1d75b11`; the Contract blob was
`2ed0744a455c5b64c99b0f4bb0286a6cd2c30f1b`. Existing Narrative architecture was present and protected
files had no unexpected changes. Original TASK-007C1 and Remediations 01, 02 and 03 were read in full.
GitHub remains authoritative; the approved branch is published as one fast-forward implementation
commit using GitHub Git-data operations with a locally verified matching tree. No other ref is written.

## Exact changed files

1. `src/ai_infra_quant/integrations/openai_reasoning/deepseek_research.py` — new native memo normalizer.
2. `src/ai_infra_quant/integrations/openai_reasoning/gateway.py` — DeepSeek-only research instructions and dispatch.
3. `src/ai_infra_quant/frontend/static/narrative-markdown.js` — new local DOM-only Markdown subset.
4. `src/ai_infra_quant/frontend/static/paqs-e.js` — formatted/raw controls and research OFF/reset behavior.
5. `src/ai_infra_quant/frontend/static/app.css` — scoped formatting, overflow and compact mobile disclosure layout.
6. `src/ai_infra_quant/frontend/templates/index.html` — local script and disclosure/control order.
7. `tests/unit/test_paqs_e_native_research.py` — native memo, provenance, bounds, failures and final tool-free request.
8. `tests/integration/test_paqs_e_native_memo_ledger.py` — actual gateway/API/ledger ON/OFF freeze and atomic failure.
9. `tests/browser/test_paqs_e_safe_markdown.py` — formatting/raw/XSS/responsiveness/races/opt-in acceptance.
10. `tests/browser/test_paqs_e_multi_model.py` — all-model OFF/reset and explicit ON failure scenario.
11. `tests/browser/test_paqs_e_narrative.py` — existing ON scenario explicitly checks research.
12. `tests/browser/test_paqs_e_workbench.py` — ordinary Analyze payload expectations now false;
    pending-history fixture waits for its intercepted POST before releasing the route hold.
13. `docs/ARCHITECTURE.md` — bounded R03 architecture addition.
14. `docs/PAQS_E_MODELS.md` — native memo/provenance limits, OFF default and remaining live gate.
15. `docs/PAQS_E_WORKBENCH.md` — formatted/raw workflow, opt-in and disclosure.
16. `docs/REQUIREMENTS_MATRIX.md` — R03 requirements and evidence mapping.
17. `docs/TASK_007C1_REMEDIATION_03_IMPLEMENTATION_REPORT.md` — this report.

No dependency, configuration, model registry, strategy, prompt, core, API, ledger, launcher,
credential-store, migration, vendor or accepted review file changes are included.

## DeepSeek native research memo

The unchanged lifecycle freezes one Snapshot, optionally researches once, freezes auxiliary context,
forms the existing Narrative request, invokes tool-free final reasoning once, and atomically stores
the terminal Run and successful exact-text Result. Research failure remains an existing safe 422
precondition failure, with no final provider call and no new Run/Result. No retry, fallback or
application continuation is introduced.

Only `provider_id=deepseek` receives the new concise factual-memo instruction and normalizer.
The selected registered endpoint/model, `store=false`, `stream=false`, native `web_search` only,
`tool_choice=required`, 6,000 output tokens, 120-second transport timeout and 2 MB response cap remain.
The instruction binds Security/As-Of, excludes future publications, prohibits trading analysis and
chain-of-thought, and makes frozen Snapshot market facts authoritative over web prices. It does not
require JSON, a result schema or a source array. The final Narrative provider/prompt is unchanged.

Success requires a completed non-error response, matching model when exposed, a safe optional
response ID, 1–10 completed native web actions, at least one search, and exactly one non-empty final
memo. Accepted action types are only `search`, `open_page`, `find_in_page`. Missing native queries
or source arrays alone do not fail a completed search. Unknown actions, malformed/incomplete
envelopes/content, refusal, empty/multiple/oversize text, unsafe identity and credential echo fail
closed. Existing credential scanning examines the response before normalization. Reasoning records
are discarded; hidden traces, debug data and raw envelopes are never frozen.

### Exact bounds and provenance

- Actions: 1–10, including a search; every accepted action is completed.
- Exposed queries: at most 4, each non-blank and at most 500 characters; absence retains an empty list.
- Native sources/citations: at most 64 raw records before deduplication and at most 64 unique URLs.
- URLs: 1–1,000 characters; HTTP(S), syntactically valid hostname/port, no userinfo,
  whitespace/control characters or backslashes. Hostnames use bounded IDNA labels or IPv6 validation.
- Optional titles: at most 500 characters. Dates are retained only when parseable and timezone-aware.
- Memo: at most 24,000 Unicode characters. The preserved aggregate research budget is also 24,000
  characters for memo + canonical provenance + source label, so metadata reduces usable memo space.
  Oversize content fails without truncation. This is compatible with unchanged exact-TEXT Narrative
  request/ledger storage; no schema extension is used.
- Safe optional response ID: 1–200 ASCII letters/digits or `_.:-`.

One frozen item has category `web_research`, label `DeepSeek native web research memo`, exact memo
content, null memo source timestamp, `as_of_compatible=true` subject to the explicit limitation,
and a SHA-256-derived context identity. Provenance is canonical sorted compact JSON with:

`provider`, `model`, `provider_response_id`, `retrieved_at`, `intent`, `snapshot_as_of`,
`native_action_count`, ordered `action_types`, actual `queries`, optional deduplicated `sources`
(`url`, optional `title`, optional aware UTC `publication_time`), `excluded_future_source_count`,
and `limitation`.

The limitation is visible in frozen research/audit evidence:

> Provider-native web research memo. Source URLs and/or publication times were not fully exposed by
> the provider response; cutoff compliance was requested but cannot be independently verified for
> every memo statement. Frozen Snapshot market facts take precedence.

A known future-dated URL is excluded even when another record for that URL lacks the date. This
does not discard an otherwise valid memo. No query, title, timestamp or URL is fabricated. Prose
URLs and page/find targets do not become trusted citations. Native URLs are never fetched by the app.

OpenAI/Alibaba keep their exact existing source-normalized instructions and normalization. The
existing `normalize_research`, `_text`, `_publication_time` and secret helper source are unchanged.
Existing model-gateway and R01 regressions continue to enforce their source provenance guarantees.

## Safe Narrative Markdown and explicit opt-in

Formatted mode (**格式化**) is the initial default. Raw mode (**原文**) displays the exact persisted
`response_text` using `textContent` and `white-space: pre-wrap`. Toggling changes only local DOM
visibility and accessible `aria-pressed` state. It does not Analyze, fetch, change selection, alter
Snapshot/evidence or mutate any hash/revision. Late history reads retain existing selection guards.

The local subset supports H1–H4, paragraphs/ordinary line breaks, `-/*/+` unordered lists, ordered
lists, deterministic indentation up to 12 spaces, bold, italic, inline backtick code, fenced
backtick/tilde code, horizontal rules, simple pipe tables with header separators and safe inline
cells, blockquotes and escaped punctuation. Inline nesting is bounded to eight levels. Unsupported
or malformed syntax falls back to inert text; unmatched fences and malformed tables are not
rejected as analysis failures. This is a presentation subset, not full CommonMark compliance.

All tags come from local fixed code via `document.createElement`; model content enters only
`textContent` or text nodes. There is no HTML parser, model-created style/event attribute,
`innerHTML`, `insertAdjacentHTML`, `DOMParser`, dynamic code execution, CDN or new dependency.
All Markdown links and images are inert, including HTTP(S) links; raw HTML is visible text.
Tables and code scroll in local containers; long tokens wrap without horizontal page overflow.
Buttons are keyboard-operable, and text/formatting inherit dark/light theme colors.

The browser regression uses the Contract's AVGO-like heading, WATCH_LONG, reference-only code,
342–350 / 371–377 table and ordered-list fixture, plus nested lists and code blocks. Hostile
script/image/link/style/iframe, malformed syntax, escaped punctuation, Chinese text, long prose,
long code and long table cases execute business assertions. No script, image request or active
link is produced. Raw/formatted toggles preserve exact text, audit hash and selected history.

Research is unchecked on initial configuration, on every model change and after reload. Supported
models enable the control without selecting it; unsupported models disable and uncheck it. No
research preference is stored in localStorage/sessionStorage/cookies or restored from history.
The visible Chinese disclosure explains extra latency and API cost. The unchanged four-field
Analyze POST captures true only after explicit checking. Tests retain no-auto-Analyze and no-retry
assertions across model, credential, history, refresh and long-running scenarios.

## Deterministic validation

Environment: Windows; Python 3.12.14; pytest 8.4.1; Playwright 1.55.0; Chromium 140.0.7339.16;
Ruff 0.12.9; mypy 1.17.1. Declared dependencies were used without repository configuration changes.
Commands run from the isolated repository with `..\task007c1-env\Scripts\python.exe` (`python`
below). Browser runs set `TASK007C_BROWSER_CHANNEL=chromium` and point `PLAYWRIGHT_BROWSERS_PATH`
at the installed Chromium runtime. Temporary SQLite files, logs and screenshots stay outside Git.

| Command | Result |
|---|---|
| `python -m pytest -ra --basetemp=../task007c1-test-tmp/r03-acceptance` | **1130 passed, 1 skipped, 1 warning in 507.37s**; exit 0 |
| `python -m pytest tests/browser -ra --basetemp=../task007c1-test-tmp/r03-browser-acceptance` | **82 passed, 1 warning in 110.71s**; exit 0; no skips/xfails/deselections |
| Focused command below | **570 passed, 1 warning in 67.66s**; exit 0 |
| `python -m ruff check .` | All checks passed |
| `python -m ruff format --check .` | 188 files already formatted |
| `python -m mypy src tests` | Success: no issues in 184 source files |
| Fresh SQLite Alembic upgrade/current/heads and actual Uvicorn HTTP smoke | Head exactly `0003_task007c1_narrative_ledger`; health READY; root/OpenAPI/configuration all 200; eleven models, default DeepSeek V4 Flash |
| Actual PowerShell source-revision helper against the owned Uvicorn HTTP health endpoint | Matching source exit 0; stale source exit 2 |
| Protected-file, helper, secret/private-artifact and unsafe DOM sink audit | Passed; 147 protected files and all existing gateway helpers unchanged |

The sole skip is the existing optional PostgreSQL migration test because
`PHASE1_POSTGRESQL_TEST_URL` is not configured; PostgreSQL execution is not claimed.
The warning is Starlette's deprecated `anyio.abc.BlockingPortal` alias. Browser tests execute actual
Chromium business assertions; no real provider request is made. The local smoke helper runs
`python -m alembic -x database_url=<fresh temporary SQLite URL> upgrade head`, `current`, `heads`,
then `python -m uvicorn ai_infra_quant.backend.main:app --host 127.0.0.1 --port <ephemeral port>`
with market/fundamental/event providers `none`. It probes `/health`, `/openapi.json`, `/` and
`/api/v1/paqs-e/configuration`; invokes `scripts/dashboard_runtime.ps1` for matched/stale revisions;
and stops only its own server. Initial smoke was against the working implementation with the
Contract HEAD reported honestly; the final committed SHA is checked again after publication.

Focused command:

```text
python -m pytest tests/unit/test_paqs_e_native_research.py tests/unit/test_paqs_e_narrative_provider.py tests/unit/test_paqs_e_remediation_01.py tests/unit/test_paqs_e_model_gateway.py tests/integration/test_paqs_e_native_memo_ledger.py tests/integration/test_paqs_e_narrative_ledger_api.py tests/integration/test_runtime_source_revision.py tests/integration/test_windows_launcher.py -ra --basetemp=../task007c1-test-tmp/r03-focused-final
```

Initial development runs caught new fixture assertions/import typing and the old implicit-ON test
assumption, then a mobile above-fold layout regression from the disclosure. A full run under
concurrent test load exposed an existing fixture race (`app.pending.pop()` before route interception).
That scenario now waits at most five seconds and asserts exactly one intercepted pending POST before
releasing its hold; all original history/selection/business assertions remain. Fixtures now perform
explicit ON actions; the mobile form pairs controls and uses compact spacing. No test was skipped,
xfail-marked, removed or weakened to bypass a failure. Final suite results supersede development runs.

## Protected files and security audit

147 protected files are byte-identical to the R03 base (canonical Git LF bytes), including all
database/migration files, core/Snapshot, application/API, resources/registry/prompts, scripts,
credential storage and accepted reviews. All pre-existing gateway helper function sources match.

| Protected evidence | SHA-256 |
|---|---|
| Complete legacy validator function | `1f52c6c6094ce9b25fe0a7a22ddfdea0e52d8484eb5032ab4bac5e8b9ff1d271` |
| Migration 0001 | `aa46ffadabb227b86124e396b66a5fe6a0839a7439ad10ab4a726e4f6788daf8` |
| Migration 0002 | `36441501046bd5594401c989bbf7424e997bb6b687fdafd71c34c3e663eaefe3` |
| Migration 0003 | `5a5056490eed678e8533a20719c0c6becf7d8f40da3af26f54d689329b81caf6` |
| Final Narrative gateway file | `200e474605c080cf7c170527a3f0de373a41dd9695725f19ee83b6c1c5f9f1f6` |

The Narrative service, domain acceptance, final prompt, repository, schema, lineage, response-text
hash and request hash behavior remain unchanged. Thus the Contract-recorded successful OFF Run
`b45f2209-54ae-464a-80e4-651c2ffb40d6` / Result `7db32fc2-fb2a-4849-8b84-cded2239079d`
at `74a19387adc408e9453c30fdbb30e6636ac4e695` retains its read/hash path. The user's live database
was not opened or modified; that record's live execution is attributed to the Contract, not rerun.

Changed-file secret/private-artifact scan and DOM-sink audit pass. Test credentials are synthetic;
integration asserts no credential or hidden trace in persisted rows. No database/log/private export
or screenshot is committed. No provider/model endpoint, retry/fallback, broker/trading, PAQS-Q,
backtest or portfolio/PnL scope is added. No real provider call was made during implementation/testing.

## Remaining limits and independent review stop

Provider-native research is auxiliary material, not independently verified statement-level fact.
Unknown publication times remain unknown; a future citation can be excluded without rewriting
the exact memo. Native internal tool activity/billing is provider-controlled; one application HTTP
attempt and bounded accepted evidence do not guarantee one billed provider search. Provider
availability, permissions, latency and live ON success are not established by synthetic tests.

After independent review, the user must perform one explicit DeepSeek V4 Flash, normal supported
Security, `paqs-e-master`, research-ON Analyze on the exact reviewed final SHA. It must produce one
successful immutable Run/Result, non-empty native memo/provenance, true research flags, valid
request/response hashes, readable formatted text and exact raw text. No automatic retry is allowed.
The Contract does not require a second paid OFF run if independent review confirms the preserved
final Narrative path; this report supplies its exact unchanged-code evidence.

Only the task branch is published. The authoritative branch remains unchanged. No merge, independent
PASS, final live acceptance or next-task work is claimed. Stop for independent review.
