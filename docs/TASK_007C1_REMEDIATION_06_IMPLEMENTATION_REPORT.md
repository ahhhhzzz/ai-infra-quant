# TASK-007C1 Remediation 06 implementation report

Status: implemented for independent review. Final Research-ON live acceptance remains
user-executed after independent review of the exact published implementation SHA. No final
TASK-007C1 PASS or integration is claimed.

## GitHub authority and implementation identity

Repository: `ahhhhzzz/ai-infra-quant`.

- Authoritative branch: `roadmap/no-live-trading`.
- Authoritative SHA and merge base: `80f089bc2d285cca492c41aaeaf047e177bc2812`.
- Only implementation branch: `task/007c1-paqs-e-multi-model-web-research`.
- Exact R06 base: `a3cc97d96887d9e31af4c3d56ab7206ef6600032`.
- Exact starting Contract SHA: `84d5e708a613293bd6edf36e0922b475de2ca368`.
- The Contract's direct parent is exactly the R06 base. GitHub comparison showed only the new
  R06 contract in that one-commit delta, and authoritative comparison was ahead 13 / behind 0.
- Final implementation identity is the commit introducing this report, with the starting Contract
  as its sole parent. The publication handoff supplies its literal 40-character SHA and a report
  link pinned to that SHA. Resolve it in any checkout with
  `git log -1 --format=%H -- docs/TASK_007C1_REMEDIATION_06_IMPLEMENTATION_REPORT.md`.
  A report cannot embed the hash of its own containing commit without changing that hash.

GitHub refs, commit metadata, contract blob, and comparisons were checked before implementation.
The isolated clean checkout was brought to the exact Contract commit with blob/tree/commit hash
verification against GitHub. No unrelated work was reset or stashed. The local
`phase1_remediation_commit.txt` was absent in both the isolated checkout and its parent workspace;
it was not created, edited, tracked, or committed.

The original TASK-007C1 Contract and Remediations 01–06 were read. R06 alone governs this change;
the earlier supersessions remain historical authority for the protected current architecture.

## Complete changed-file list

Relative to the starting Contract commit:

1. `src/ai_infra_quant/application/paqs_e_research.py`
2. `src/ai_infra_quant/integrations/openai_reasoning/deepseek_research.py`
3. `src/ai_infra_quant/integrations/openai_reasoning/deepseek_research_diagnostics.py` (new)
4. `src/ai_infra_quant/integrations/openai_reasoning/deepseek_research_flow.py`
5. `src/ai_infra_quant/frontend/static/paqs-e.js`
6. `tests/paqs_e_partial_action_support.py` (new)
7. `tests/unit/test_paqs_e_partial_actions.py` (new)
8. `tests/integration/test_paqs_e_partial_actions_api.py` (new)
9. `tests/browser/test_paqs_e_partial_actions.py` (new)
10. `docs/ARCHITECTURE.md`
11. `docs/PAQS_E_MODELS.md`
12. `docs/PAQS_E_WORKBENCH.md`
13. `docs/REQUIREMENTS_MATRIX.md`
14. `docs/TASK_007C1_REMEDIATION_06_IMPLEMENTATION_REPORT.md` (new)

Relative to the exact R06 base, the only additional file is the already-committed R06 Contract.
No existing test was modified, weakened, skipped, replaced, or superseded by R06.

## Parser status and trust semantics

SEARCH still requires a completed top-level envelope, matching supplied model identity, a safe
optional response ID, no error/refusal/credential echo, and a bounded output list. Every native
action requires an object and one of `search`, `open_page`, or `find_in_page`. Its item-level
status must be exactly `completed`, `in_progress`, `incomplete`, `failed`, or `cancelled`.
Missing, null, non-string, and unknown statuses fail closed; no default completion is fabricated.

Only completed actions count as successful evidence. Recognized partial actions are counted as
observations and skipped before query/source parsing or copying. Their malformed query/source
payloads cannot become trusted provenance and do not themselves reject an otherwise valid SEARCH.
Their raw objects are neither passed back nor persisted. Unknown action types and malformed outer
action objects still fail regardless of status.

At least one completed native `search` is mandatory. Completed page/find actions and any number
of partial searches cannot satisfy this quorum. Zero completed searches fails
`NO_COMPLETED_SEARCH`, with no SYNTHESIS, final Narrative, or new ledger row.

One valid direct memo plus completed search evidence freezes immediately. Otherwise valid
tool-only SEARCH reaches exactly one SYNTHESIS. Continuation input contains the original bounded
intent, only accepted completed native objects deep-copied without semantic rewrite in their
original order, and the existing factual synthesis instruction. Partial actions, reasoning items,
unknown items, and arbitrary messages are absent. These transport objects remain transient.

The synthetic live-like fixture has 16 native calls, seven searches, zero messages, 24 completed-
search query slots, zero raw sources, and zero unknown action types. It has 13 completed actions,
one incomplete search, one failed open-page action, and one in-progress find action: six completed
searches and one non-completed search. It reaches one SYNTHESIS with precisely the 13 completed
objects. Direct-memo and all four partial-status combinations also pass.

## Preserved query, source, and request bounds

R05 behavior remains for completed evidence: each query is a non-empty, UTF-8 encodable,
control-safe string of at most 500 Unicode characters. All valid exposed queries, including
duplicates and values after capture stops, are counted. Structural bounds remain 256 queries and
64,000 query characters. Capture remains a whole-query ordered prefix of 16 items / 4,000
characters, with truthful `provider_exposed_query_count` and `query_capture_complete`.
There is no normal four-search/four-query rejection.

Bounds remain 64 total native calls, 128 output items, and 64 raw trusted source/citation records
before deduplication. Sources keep HTTP(S), URL length 1000, no userinfo/control/whitespace/backslash
smuggling, valid host/port, bounded title, aware publication times, future-source exclusion, and
no source inference from memo prose. UTF-8 URL/title failures are now identified at the source
rule before synthesis, rather than surfacing later as an encoding failure while freezing evidence.

Response-size accounting defers surrogate rejection to the exact trusted query/source/memo or
pass-back rule, allowing malformed untrusted partial fields to be ignored. The actual HTTP
transport's existing 2 MB response limit and strict request encoding remain unchanged.
Research requests remain bounded to 2 MB; final memo and memo + provenance + label remain bounded
to 24,000 characters. Oversize evidence fails without memo truncation.

SEARCH and SYNTHESIS request expressions are AST-identical to R05, and their instruction constants
are byte-identical. SEARCH still forces only native web search, with `store=false`, `stream=false`,
`reasoning.effort=none`, and 6000 output tokens. SYNTHESIS uses the same endpoint/model/credential,
`tools=[]`, `tool_choice=none`, effort `none`, and 4000 output tokens. Neither uses
`previous_response_id`, conversation, background state, retry, or fallback. Final tool-free
Narrative runs only after memo freezing. Maximum research requests stays two; maximum successful
tool-only total stays three. Research-OFF remains zero research requests and one unchanged Narrative.

## Exact safe diagnostic design

`NativeParseFailure` carries an application allowlisted code and a copied, read-only mapping of
bounded numeric observations. The SEARCH parser raises it at the actual failing rule. Encoding
and URL-library exceptions are classified by their surrounding rule, never their exception text.
The adapter projects this metadata through the existing research precondition error without a
schema or ledger change. Envelope/pass-back/provenance/synthesis checks likewise raise their own
codes; a request-size failure before SYNTHESIS is sent reports SEARCH / PASSBACK_BOUND with one
research request and `synthesis_attempted=false`.

Allowed codes:

```text
SEARCH_ENVELOPE SEARCH_OUTPUT_SHAPE ACTION_SHAPE ACTION_TYPE ACTION_STATUS ACTION_BOUND
NO_COMPLETED_SEARCH QUERY_STRUCTURE QUERY_INTEGRITY QUERY_STRUCTURAL_BOUND
SOURCE_STRUCTURE SOURCE_BOUND SOURCE_URL MESSAGE_SHAPE MESSAGE_INTEGRITY
PASSBACK_BOUND PROVENANCE_BOUND SYNTHESIS_ENVELOPE SYNTHESIS_OUTPUT_SHAPE
SYNTHESIS_MESSAGE SYNTHESIS_MEMO_INTEGRITY
```

Representative failures test exact codes, including envelope status/model/id, output/action shapes,
unknown action/status, missing quorum, queries, sources, message integrity, pass-back/provenance
bounds, and synthesis failures. Transport/refusal/secret-tainted failures retain their safe classes;
they do not invent a parser code. The existing generic exception guard remains a safe last resort.

New optional fields are `boundary_code`, `completed_action_count`, `in_progress_action_count`,
`incomplete_action_count`, `failed_action_count`, `cancelled_action_count`, `completed_search_count`,
`non_completed_search_count`, `missing_or_unknown_status_count`, `invalid_query_value_count`,
`malformed_action_count`, and `unexpected_output_item_count`. Existing action/search/message and
query/source/unknown-action counts remain. New numeric fields accept exact integers 0–1024 only,
excluding booleans. Large observations saturate at 1024; unknown totals are omitted.

Counts are bounded observations, not a certification of successful evidence. Query diagnostics
count exposed slots on completed searches, including invalid individual slots; successful
provenance counts only validated queries. Partial payloads contribute neither query nor source
counts. Recognized status counts may describe an item whose outer action shape later fails.
The parser collects bounded counts before rule validation so failures can report the entire
bounded input's known counts, while the code originates at the rejecting rule. Unknown containers
omit affected totals; excessive output windows omit the new counters. Synthesis failures use their
own envelope. Secret-tainted responses are never reparsed for detailed counters or boundary codes.

No diagnostic contains query/memo text, URLs/titles, raw native items, provider body/error/refusal
text, hidden instructions, reasoning, Authorization material, or credentials. Diagnostics are
ephemeral API/UI failure metadata and never enter the Narrative Ledger. Successful provenance
adds safe status/search counts; `native_action_count` and ordered `action_types` describe completed
evidence only, alongside the existing factual memo and provenance limitation.

The browser independently allowlists codes and validates each numeric field. It displays a concise
Chinese suffix, omits invalid fields, and never renders raw JSON/provider IDs/private strings.
Tests prove prior Narrative remains selected as earlier content, raw/formatted views preserve exact
text, default OFF remains, and one explicit Analyze click causes exactly one POST with no retry.

## Validation

Environment: Windows, Python 3.12.14, pytest 8.4.1, Playwright 1.55.0, Chromium 140.0.7339.16,
Ruff 0.12.9, mypy 1.17.1. Declared dependencies were reused; Chromium launched normally.
Tests use synthetic credentials/providers and fresh owned SQLite databases. No paid provider call
was made by Codex. Temporary databases, logs, screenshots and audit helpers remain outside Git.

Commands ran in the isolated checkout with its Python 3.12 environment, `PYTHONUTF8=1`, repository
root in `PYTHONPATH`, `TASK007C_BROWSER_CHANNEL=chromium`, and the installed Playwright browser path.

| Command/check | Result |
|---|---|
| Focused command below | 801 passed, 1 warning in 103.93s |
| `python -m pytest -ra --basetemp=../task007c1-test-tmp/r06-full` | 1340 collected; 1339 passed, 1 skipped, 1 warning in 372.39s; exit 0 |
| `python -m pytest tests/browser -ra --basetemp=../task007c1-test-tmp/r06-browser` | 99 passed, 1 warning in 75.63s; exit 0; all business assertions executed, no skips/xfails/deselections/failures |
| `python -m ruff check .` | All checks passed |
| `python -m ruff format --check .` | 200 files already formatted |
| `python -m mypy src tests` | Success, 196 source files |
| Fresh SQLite `alembic upgrade head`, `current`, `heads` | PASS, exactly 0003 |
| Actual Uvicorn health/root/OpenAPI/configuration | PASS, all HTTP 200, 11 models, DeepSeek default |
| Actual PowerShell launcher source handshake over HTTP | Same SHA exit 0, stale SHA exit 2 |
| Protected diff/hash, secret/private-artifact and unsafe DOM audit | PASS |

Focused command:

```text
python -m pytest tests/unit/test_paqs_e_partial_actions.py tests/unit/test_paqs_e_search_multiplicity.py tests/unit/test_paqs_e_research_continuation.py tests/unit/test_paqs_e_native_research.py tests/unit/test_paqs_e_model_gateway.py tests/unit/test_paqs_e_remediation_01.py tests/unit/test_paqs_e_narrative_provider.py tests/integration/test_runtime_source_revision.py tests/integration/test_windows_launcher.py tests/integration/test_paqs_e_narrative_ledger_api.py tests/integration/test_paqs_e_native_memo_ledger.py tests/integration/test_paqs_e_research_continuation_api.py tests/integration/test_paqs_e_search_multiplicity_api.py tests/integration/test_paqs_e_partial_actions_api.py tests/browser/test_paqs_e_research_diagnostic.py tests/browser/test_paqs_e_safe_markdown.py tests/browser/test_paqs_e_multi_model.py tests/browser/test_paqs_e_search_multiplicity.py tests/browser/test_paqs_e_partial_actions.py -ra --basetemp=../task007c1-test-tmp/r06-focused
```

The warning is Starlette's deprecated `anyio.abc.BlockingPortal` alias. The optional PostgreSQL
test requires `PHASE1_POSTGRESQL_TEST_URL`; an unset environment is not a performed PostgreSQL
validation. Browser business assertions run in real Chromium with synthetic intercepted provider
behavior, not paid provider acceptance.

## Protected-file and private-artifact audit

153 protected tracked files are byte-identical to the exact R06 base using canonical Git LF bytes.
This includes the full shared gateway and other-provider behavior, NarrativeGateway, API, ledger/
repositories/schema/revisions, core/domain/ports, migrations, strategy/Doctrine/Narrative prompt,
validator, registry/endpoints, credentials, Snapshot and source-handshake/launcher code, accepted
reviews, and Markdown renderer/CSS/template. Every one of the 70 pre-existing test files is
unchanged. The workbench outside `researchDiagnostic` is byte-identical, including default OFF,
safe Markdown/raw toggle, and the long-running single-in-flight guard.

| Artifact | SHA-256 |
|---|---|
| Migration 0001 | `aa46ffadabb227b86124e396b66a5fe6a0839a7439ad10ab4a726e4f6788daf8` |
| Migration 0002 | `36441501046bd5594401c989bbf7424e997bb6b687fdafd71c34c3e663eaefe3` |
| Migration 0003 | `5a5056490eed678e8533a20719c0c6becf7d8f40da3af26f54d689329b81caf6` |
| NarrativeGateway module | `200e474605c080cf7c170527a3f0de373a41dd9695725f19ee83b6c1c5f9f1f6` |
| Legacy validator function | `1f52c6c6094ce9b25fe0a7a22ddfdea0e52d8484eb5032ab4bac5e8b9ff1d271` |

No migration was edited or added; head remains `0003_task007c1_narrative_ledger`. API regressions
prove exact request/response SHA readback, unchanged SQLite schema and prior successful rows,
and no new Run/Result on research precondition failure. Pattern scans and changed-file inspection
found no real credentials, keys, databases, logs, screenshots, private exports, or unsafe DOM sinks
staged for publication. No provider/model, retry/fallback, broker/trading, PAQS-Q, backtest,
portfolio/PnL, or unrelated scope was added.

## Publication and remaining acceptance

Publish only the approved task branch, as a fast-forward child of the exact starting Contract.
Verify the GitHub final SHA/tree against the tested local tree and recheck the authoritative SHA
and merge base; expected final topology is ahead 14 / behind 0. No force push or merge is authorized.
The final handoff records these publication checks and the exact final SHA.

The R06 fixture is synthetic evidence based on the observed shape; it is not a captured provider
body and does not prove that partial status was the sole live failure cause. Provider-native source
or publication metadata can remain incomplete; the existing provenance limitation remains explicit.
No paid DeepSeek/OpenAI/Alibaba call was made. Research-OFF paid revalidation is unnecessary here
because its accepted final provider/prompt/ledger behavior is unchanged.

Stop for independent review. Final Research-ON live acceptance remains user-executed only after
that review passes the exact final SHA: one explicit `US.AVGO` / DeepSeek V4 Flash / `paqs-e-master`
Analyze with research manually enabled. Success must verify frozen memo, final Narrative, request/
response hashes and lineage. If it fails, do not retry; use the safe boundary code and counts for
the next evidence-based review. The authoritative branch is not modified and no merge is performed.
