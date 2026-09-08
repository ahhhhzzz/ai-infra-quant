# TASK-007C1 Remediation 05 implementation report

Status: deterministic validation complete; ready for independent review.
No final TASK-007C1 PASS, paid Research-ON success or integration is claimed.

## Exact authority and topology

GitHub refs, commit/tree metadata and comparisons were verified before implementation. The isolated
checkout was clean and advanced to the exact, hash-matched Contract commit. The original Contract
and R01-R04 full texts, read during the preceding implementation work, are unchanged; R05 was read
in full before editing. Repository governance and protected behavior remain in force.

| Evidence | Value |
|---|---|
| Repository | `ahhhhzzz/ai-infra-quant` |
| Only task/publication branch | `task/007c1-paqs-e-multi-model-web-research` |
| Starting HEAD / R05 Contract commit | `a86efee5801ab4355b27fa6ffa4bbabaab7828c5` |
| Exact Contract parent / R05 base | `a82340db89be0e2a47583b03f97fb28218dd7a09` |
| Authoritative HEAD / merge base | `80f089bc2d285cca492c41aaeaf047e177bc2812` |
| Starting ahead / behind | 11 / 0 |
| Final implementation parent | `a86efee5801ab4355b27fa6ffa4bbabaab7828c5` |
| Final ahead / behind after one implementation commit | 12 / 0 |
| Final implementation / task HEAD SHA | The commit containing this report; the handoff supplies its literal 40-character SHA and SHA-pinned report URL. A commit cannot embed its own content-derived SHA. |

The Contract commit adds only the issued R05 Contract relative to the exact base. GitHub Git-data
publication matches the tested local tree and updates only the approved task ref without force.
The authoritative branch is not modified. No merge, reset, stash or unrelated-process termination
occurs. Accepted reviews, Contracts and previous implementation reports remain unchanged.

## Complete changed-file list

Relative to the starting Contract commit, 14 files:

```text
docs/ARCHITECTURE.md
docs/PAQS_E_MODELS.md
docs/PAQS_E_WORKBENCH.md
docs/REQUIREMENTS_MATRIX.md
docs/TASK_007C1_REMEDIATION_05_IMPLEMENTATION_REPORT.md
src/ai_infra_quant/application/paqs_e_research.py
src/ai_infra_quant/frontend/static/paqs-e.js
src/ai_infra_quant/integrations/openai_reasoning/deepseek_research.py
src/ai_infra_quant/integrations/openai_reasoning/deepseek_research_flow.py
tests/browser/test_paqs_e_search_multiplicity.py
tests/integration/test_paqs_e_search_multiplicity_api.py
tests/unit/test_paqs_e_native_research.py
tests/unit/test_paqs_e_research_continuation.py
tests/unit/test_paqs_e_search_multiplicity.py
```

Relative to the R05 base, the previously committed R05 Contract is the only additional file.

## Query acceptance and bounded provenance

`parse_native_search` replaces the DeepSeek `queries.extend(values); len(queries) > 4` rejection
with individual validation, high structural limits, and separate provenance capture. More than
four search actions or valid exposed queries is no longer an acceptance failure. The unchanged
SEARCH instruction asks for at most four queries as advisory guidance; it does not guarantee
provider billing or define post-hoc acceptance. R05 does not claim the old cap was proven to be
the only cause of the live R04 rejection.

Every exposed query must be a string, non-empty after whitespace checking, at most 500 Unicode
characters, strictly UTF-8 encodable, and free of the research boundary's forbidden controls
(`U+0000..0008`, `000B..000C`, `000E..001F`, `007F..009F`). Existing permitted tab/CR/LF semantics
remain. Missing query strings are allowed. When both native `query` and `queries` fields exist,
both are validated/count in received field order; duplicates count separately.

Structural limits are **256 exposed queries** and **64,000 total Unicode query characters** per
SEARCH. Exceeding either fails before SYNTHESIS without retry. These are anti-abuse parsing limits,
not business rules, strategy semantics, provider continuation-round limits or billing guarantees.

Capture retains an ordered prefix of **16 complete queries** and **4,000 query characters** at
most. The first complete query that cannot fit stops capture; later shorter queries cannot fill
the gap. No query is partially truncated. All subsequent exposed values are still validated and
counted. Capture truncation alone does not fail research. New successful provenance fields are:

- `provider_exposed_query_count`: total valid queries, before capture, including duplicates;
- `query_capture_complete`: exact boolean, false whenever the full list was not captured;
- existing `queries`: now the bounded ordered whole-query prefix.

Fixtures cover six queries with complete capture, 37 with an ordered 16-query prefix, character
boundary/exclusion without fragments, 256-query and 64,000-character boundary successes, and
malformed/oversized values after capture has already stopped.

All existing provenance remains: provider/model, intent/retrieval/As-Of, safe SEARCH ID/status,
web/search counts and ordered actions, validated native sources/publication times, future-source
exclusions, optional SYNTHESIS ID, synthesis flag, HTTP request count and explicit limitation.
The memo + label + canonical provenance still must fit 24,000 characters. The 64-native-call,
128-output-item, 64-raw-source-record and 2 MB transport/request bounds remain unchanged.
Source URL syntax, credentials/control/hostname/port safeguards, timestamp/As-Of exclusions and
no-authority-from-prose rules are unchanged. No raw native call is persisted.

## Safe failure diagnostics and browser projection

The frozen `ResearchDiagnostic` adds optional exact nonnegative integers, bounded to 1024:
`provider_exposed_query_count`, `raw_source_record_count`, `unknown_action_count`.
Absent/unknowable totals are omitted; booleans, strings, negative and oversized values are rejected
by the diagnostic type. Numeric counting is bounded and values above 1024 saturate at 1024.

On failed envelopes, the query diagnostic counts exposed slots, including malformed individual
entries, rather than certifying their validity. Successful provenance counts only validated queries.
Malformed query/source containers omit the affected totals. Raw source records count before
deduplication, matching the parser's search-source and native URL-citation inputs. Unknown native
action types are counted without copying their names. New totals are omitted when the output
shape is unavailable or exceeds the bounded inspection window. SYNTHESIS failures report counts
from their own envelope; transport/secret-tainted failures omit unavailable new counts.

The existing API error code and projection remain unchanged; the dataclass's safe dictionary adds
the optional numbers automatically. There is no schema/API-request change or database diagnostic
storage. Query strings, source URLs/titles, memo, raw body, reasoning, hidden prompt, exception text
and credentials never enter these fields. Unit tests exercise malformed queries, structural/source
overflow, unknown actions, synthesis failure, saturation/omission and secret-tainted envelopes.

The existing Chinese diagnostic gains a suffix such as `查询 6，来源记录 24，未知动作 0` only for
strictly validated numeric fields. Invalid optional fields are ignored independently. Mandatory
diagnostic shape checks remain. The browser never renders raw diagnostic JSON, provider response
IDs, URLs, query text or raw API detail. Failure preserves the prior Narrative and creates one
explicit Analyze POST only, with no automatic retry. Raw/formatted switching remains unchanged.

## R04 lifecycle and protected behavior

The exact R04 `research_native` function and SEARCH/SYNTHESIS instruction constants are byte-
identical to the base. Only its safe diagnostic projector changes. Thus SEARCH is still exactly
one request; a direct memo skips synthesis; valid tool-only output triggers at most one SYNTHESIS.
Accepted native items are passed back as-is, with original intent, no previous-response/conversation
state or reasoning items, and `tools=[]`, `tool_choice=none`, `reasoning.effort=none` for SYNTHESIS.
No extra request, second SEARCH, retry, fallback or model change is added.

The live-like fixture has 20 calls, six native searches with six valid query strings, and no message.
It reaches exactly one SYNTHESIS; successful memo freezing precedes the unchanged tool-free final
Narrative. Maximum research calls remains two; maximum successful tool-only total is three.
Research-OFF remains zero research calls plus the unchanged final Narrative call.

The audit compares **152 protected tracked files** to the exact R05 base using canonical Git LF
bytes. All are identical, including the entire gateway (therefore OpenAI/Alibaba behavior), API,
NarrativeGateway, database/ledger/schema/revisions, core/domain/ports, resources/strategy/Doctrine/
Narrative prompt, validator, model registry/endpoints, credentials, Snapshot/market-data boundaries,
source handshake/launcher, accepted evidence and R03 renderer/CSS/template. The workbench outside
its diagnostic formatter is byte-identical, including default-OFF opt-in, Markdown/raw view and
the non-aborting single-in-flight guard.

| Protected artifact | SHA-256 |
|---|---|
| 0001 | `aa46ffadabb227b86124e396b66a5fe6a0839a7439ad10ab4a726e4f6788daf8` |
| 0002 | `36441501046bd5594401c989bbf7424e997bb6b687fdafd71c34c3e663eaefe3` |
| 0003 | `5a5056490eed678e8533a20719c0c6becf7d8f40da3af26f54d689329b81caf6` |
| NarrativeGateway module | `200e474605c080cf7c170527a3f0de373a41dd9695725f19ee83b6c1c5f9f1f6` |
| Legacy validator function | `1f52c6c6094ce9b25fe0a7a22ddfdea0e52d8484eb5032ab4bac5e8b9ff1d271` |

No migration is added or edited; head remains `0003_task007c1_narrative_ledger`. New API tests
verify exact request and response SHA readback, unchanged SQLite schema, no precondition-failure
Run/Result, and byte/value-identical prior successful rows. No provider/model, broker/trading,
PAQS-Q, backtest, portfolio/PnL or unrelated scope is added.

## Validation and older-test supersession

Environment: Windows, Python 3.12.14, pytest 8.4.1, Playwright 1.55.0, Chromium 140.0.7339.16,
Ruff 0.12.9 and mypy 1.17.1. Repository-declared dependencies are reused. Tests use synthetic
credentials/providers; browser scenarios launch real Chromium and local Uvicorn. Temporary logs,
screenshots and databases remain outside Git. No paid provider call was made by Codex.

| Command/check | Result |
|---|---|
| Focused command below | 725 passed, 1 warning in 71.64s |
| `python -m pytest -ra --basetemp=../task007c1-test-tmp/r05-full` | 1263 passed, 1 skipped, 1 warning in 348.67s; 1264 collected |
| `python -m pytest tests/browser -ra --basetemp=../task007c1-test-tmp/r05-browser` | 92 passed, 1 warning in 65.26s; all business assertions executed, no skips/failures |
| `python -m ruff check .` | All checks passed |
| `python -m ruff format --check .` | 195 files already formatted |
| `python -m mypy src tests` | Success, 191 source files |
| Fresh SQLite upgrade/current/heads | PASS, exactly 0003 |
| Real Uvicorn health/root/OpenAPI/configuration | PASS, all HTTP 200; 11 models, DeepSeek default |
| Actual PowerShell source handshake over HTTP | Same SHA exit 0; stale SHA exit 2 |
| Protected-file, secret/private-artifact and unsafe DOM audit | PASS |

Focused command:

```text
python -m pytest tests/unit/test_paqs_e_search_multiplicity.py tests/unit/test_paqs_e_research_continuation.py tests/unit/test_paqs_e_native_research.py tests/unit/test_paqs_e_model_gateway.py tests/unit/test_paqs_e_remediation_01.py tests/unit/test_paqs_e_narrative_provider.py tests/integration/test_runtime_source_revision.py tests/integration/test_windows_launcher.py tests/integration/test_paqs_e_narrative_ledger_api.py tests/integration/test_paqs_e_native_memo_ledger.py tests/integration/test_paqs_e_research_continuation_api.py tests/integration/test_paqs_e_search_multiplicity_api.py tests/browser/test_paqs_e_research_diagnostic.py tests/browser/test_paqs_e_safe_markdown.py tests/browser/test_paqs_e_multi_model.py tests/browser/test_paqs_e_search_multiplicity.py -ra --basetemp=../task007c1-test-tmp/r05-focused
```

Browser environment uses `PYTHONUTF8=1`, `PYTHONPATH=<checkout>`,
`TASK007C_BROWSER_CHANNEL=chromium` and the existing local `PLAYWRIGHT_BROWSERS_PATH`. The existing
Starlette deprecated `anyio.abc.BlockingPortal` warning is unrelated to R05. Development lint/type
findings were corrected before final validation; no failure expectations were weakened.
The full suite's only skip is the existing optional PostgreSQL migration test because
`PHASE1_POSTGRESQL_TEST_URL` is unset (`tests/integration/test_postgresql_migrations.py:67`).
No PostgreSQL execution is claimed; no browser test was skipped, xfailed or deselected.

Only two older test inputs change: the native research `queries` failure case and R04 continuation
`query-limit` failure case now use 257 queries instead of five. They exercise the new structural
overflow boundary; new six-query direct and tool-only successes replace the superseded normal
five-query rejection. All other assertions and other-provider fixtures remain unchanged. New tests
add 47 unit, six integration and seven browser cases.

The initial standalone smoke used the Contract HEAD as source identity while testing the modified
tree. A post-publication repeat checks the literal final commit identity with the same head 0003
and endpoints. Only owned smoke processes are stopped; user databases/runtimes remain untouched.

## Stop for independent review

Only the approved task branch is published. The authoritative branch remains exactly
`80f089bc2d285cca492c41aaeaf047e177bc2812`. No merge or paid provider call occurred.

After independent code/contract PASS, the user must run one explicit DeepSeek V4 Flash Research-ON
smoke on the reviewed SHA, preferably US.AVGO / paqs-e-master. Verify source SHA, head 0003, manual
opt-in, durable successful Narrative/revision, frozen memo, query count/capture completeness,
synthesis/request-count provenance and request/response hashes. On failure, report only safe
diagnostics and stop without retry. Final TASK-007C1 PASS and integration remain pending that live
evidence and the final SHA/topology gate; this report does not start another task.
