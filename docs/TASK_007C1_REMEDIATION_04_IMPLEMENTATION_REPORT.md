# TASK-007C1 Remediation 04 implementation report

Status: deterministic validation complete; implementation ready for independent review.
No final TASK-007C1 acceptance, live Research-ON success, or integration is claimed.

## Authority and exact Git identity

GitHub is the authoritative source. Before editing, GitHub refs, Git commit/tree data and compare
results verified the following, followed by an isolated clean, hash-matched local checkout:

| Evidence | Exact value |
|---|---|
| Repository | `ahhhhzzz/ai-infra-quant` |
| Only publication branch | `task/007c1-paqs-e-multi-model-web-research` |
| Starting HEAD / R04 Contract commit | `e6fe791a5c99033da77a8bc877e772e0c84f55df` |
| Contract parent / exact R04 base | `a9c7eabd1862d491f61843dfc68cbc3a1d9c936f` |
| Authoritative HEAD and merge base | `80f089bc2d285cca492c41aaeaf047e177bc2812` |
| Starting ahead / behind authoritative | 9 / 0 |
| Final implementation parent | `e6fe791a5c99033da77a8bc877e772e0c84f55df` |
| Final ahead / behind authoritative | 10 / 0 after the single implementation commit |
| Final implementation SHA | The Git commit containing this report; the handoff supplies its literal 40-character SHA and a SHA-pinned report URL. A commit cannot embed its own content-derived SHA. |

The Contract commit adds only the issued R04 Contract relative to the exact R04 base. The original
TASK-007C1 Contract and all four remediation Contracts were read in full, along with repository
governance. Only R04 supersessions are implemented. The local worktree was clean before editing;
unrelated workspace files/processes were preserved. Publication uses GitHub Git-data APIs and a
non-forced update of only the approved branch, with the GitHub tree matched to the tested local tree.

## Complete implementation changed-file list

Relative to the starting Contract commit (15 files):

```text
docs/ARCHITECTURE.md
docs/PAQS_E_MODELS.md
docs/PAQS_E_WORKBENCH.md
docs/REQUIREMENTS_MATRIX.md
docs/TASK_007C1_REMEDIATION_04_IMPLEMENTATION_REPORT.md
src/ai_infra_quant/application/paqs_e_research.py
src/ai_infra_quant/backend/api/v1/paqs_e.py
src/ai_infra_quant/frontend/static/paqs-e.js
src/ai_infra_quant/integrations/openai_reasoning/deepseek_research.py
src/ai_infra_quant/integrations/openai_reasoning/deepseek_research_flow.py
src/ai_infra_quant/integrations/openai_reasoning/gateway.py
tests/browser/test_paqs_e_research_diagnostic.py
tests/integration/test_paqs_e_research_continuation_api.py
tests/unit/test_paqs_e_native_research.py
tests/unit/test_paqs_e_research_continuation.py
```

Relative to the R04 base, the previously committed R04 Contract is the only additional file.
No historical Contract, accepted review, or earlier implementation report is rewritten.

## DeepSeek SEARCH and optional SYNTHESIS

`ModelGateway.research` dispatches only the registered DeepSeek route to the isolated new flow.
The same existing registry, exact model, endpoint and secure credential are used throughout.
The existing OpenAI/Alibaba research body and normalizer remain unchanged.

SEARCH sends exactly one request to the registered DeepSeek Responses research endpoint:

```json
{
  "model": "<selected registered DeepSeek model_id>",
  "store": false,
  "stream": false,
  "reasoning": {"effort": "none"},
  "tools": [{"type": "web_search"}],
  "tool_choice": {"type": "web_search"},
  "max_output_tokens": 6000,
  "instructions": "<bounded factual research instruction>",
  "input": "<original Security, market and Snapshot As-Of intent>"
}
```

The exact instruction strings are committed as `MEMO_INSTRUCTION` and the SEARCH prefix in
`deepseek_research_flow.py`. They request at most four queries and a concise factual company/news/
earnings/public-event memo, respect the cutoff and Snapshot market-fact precedence, and prohibit
chain-of-thought, trading/Setup/Trigger/entry analysis and application-schema output requirements.
Neither research request contains PAQS-E strategy Markdown or the final Narrative runtime prompt.

The SEARCH envelope must be completed, error-free, secret-free, model-matched when exposed and
have a safe/null response ID. Every output must be an allowed completed native search/page/find
call, a valid final assistant message, or an ignored reasoning item. At least one real search is
required. Unknown/malformed/refused/incomplete content fails before further provider work.

One acceptable final memo takes the direct path: exact text is frozen, `synthesis_used=false`,
`research_http_request_count=1`, and SYNTHESIS is not sent. This accepts 11 or up to 64 valid calls.
An empty, malformed, multiple or refused message fails; it is never rescued by another call.

Only otherwise valid completed tool-only SEARCH output triggers one SYNTHESIS request:

```json
{
  "model": "<same selected registered DeepSeek model_id>",
  "store": false,
  "stream": false,
  "reasoning": {"effort": "none"},
  "tools": [],
  "tool_choice": "none",
  "max_output_tokens": 4000,
  "instructions": "<SYNTHESIS_INSTRUCTION>",
  "input": [
    {"role": "user", "content": "<exact original SEARCH intent>"},
    "<each accepted web_search_call object, passed back as-is>",
    {"role": "user", "content": "<SYNTHESIS_INSTRUCTION>"}
  ]
}
```

The middle entries above represent native objects, not strings in the actual request. The parser
deep-copies each accepted item without rewriting any fields, including native restoration data.
There is no `previous_response_id`, `conversation`, background mode, fabricated call, arbitrary
SEARCH message, or reasoning item in continuation input. The instruction requests a factual memo
using only restored native results and the original intent. There is no second SEARCH or loop.

SYNTHESIS requires the same envelope integrity and exactly one final assistant message with one
non-empty visible text. Message status/role, when exposed, must be completed/assistant; absent
status/role retain the existing compatible Responses-message defaults. Any unexpected tool call,
refusal, multiple/missing/empty text, invalid UTF-8/control characters or oversized memo fails closed.
No semantic PAQS-E validation or JSON parsing is applied to the memo. Failure at either stage
prevents final Narrative reasoning and creates no Narrative Run/Result. No stage retries.

## Bounds, provenance and diagnostics

Local safety bounds are 64 native calls and 128 output items per response; these are not provider
continuation-round or billing guarantees. Eleven calls are explicitly tested on both successful
paths. Requests and responses are capped at 2,000,000 serialized UTF-8 bytes. Each HTTP transport
retains its existing 120-second timeout. SEARCH/SYNTHESIS output caps are 6,000/4,000 tokens.
At most four actually exposed queries are retained, each at most 500 characters; absent queries
remain absent. Raw source records are counted before deduplication, maximum 64.

The existing source rules remain: HTTP(S) URLs up to 1,000 characters, valid hostname/port, no
userinfo/whitespace/control/backslash smuggling, titles up to 500 characters, aware parseable
publication timestamps only. Known future URLs are excluded even when duplicated; the memo may
remain with its limitation. Prose URLs and page/find targets never acquire source authority.

One `web_research` auxiliary item freezes the exact final memo, label, null memo-level publication
time, explicit As-Of limitation and canonical JSON provenance. Memo text is at most 24,000 Unicode
characters; memo + label + canonical provenance must also fit 24,000 characters without truncation.
This retains R03's aggregate character policy, compatible with the unchanged Narrative capsule.
Oversized SEARCH provenance fails before synthesis. No provisional/fabricated memo is persisted.

Provenance contains provider/model, original intent, retrieval time, Snapshot As-Of, SEARCH ID/status,
native-call/search counts, ordered action types, actual queries, safe sources/times, excluded-future
count, `synthesis_used`, optional SYNTHESIS ID, and research HTTP count 1 or 2. The existing
`provider_response_id` and `native_action_count` remain as compatible SEARCH metadata. The explicit
limitation states that cutoff compliance cannot be independently verified for every memo statement
and frozen Snapshot market facts take precedence.

`ResearchDiagnostic` is a frozen, validated provider-neutral dataclass. Its optional API projection
under the existing `PAQS_E_RESEARCH_PRECONDITION_FAILED` error has only:

- fixed `detail_version=paqs-e-research-diagnostic-v1`;
- stage `SEARCH` or `SYNTHESIS`;
- failure class `TRANSPORT_ERROR`, `INVALID_RESPONSE`, `UNSAFE_RESPONSE`, or `REFUSAL`;
- registered provider/model IDs;
- allowlisted completed/incomplete/failed/cancelled status and safe/null response ID;
- stage-local web-call/search/message counts, bounded by examining at most 129 output items;
- synthesis-attempt flag and actual research HTTP request count;
- optional incomplete reason limited to `max_output_tokens` or `content_filter`.

Unknown status/reason strings and unsafe IDs are omitted. Secret-tainted envelopes contribute no
provider-derived diagnostic fields. API/log messages do not interpolate provider exceptions.
The UI displays only fixed stage/class/count fields; raw diagnostic JSON, provider IDs/messages,
memo, reasoning, hidden prompt and arbitrary extra keys are not rendered. Research errors use a
fixed safe user-facing detail and leave the selected prior Narrative visible. Diagnostics are not
stored in the database. Native call objects and full envelopes stay transient and are never frozen.

Research-OFF still has zero research calls. ON has at most two research calls, followed by one
unchanged tool-free Narrative call: maximum three provider HTTP requests per explicit Analyze.
The Chinese disclosure says research defaults OFF and may add up to two requests before final
analysis, increasing latency/API cost. It contains no continuation/tool-item jargon. Research is
still unchecked on load/model change, never remembered, and requires explicit user opt-in.

## Protected behavior and hash audit

The R04-base audit verifies 149 protected tracked files byte-identical under canonical Git LF bytes,
including all migrations, database/ledger code, core/domain/ports, resources, strategy/Doctrine,
Narrative application/runtime/provider path, credential architecture, source handshake/launcher,
accepted reviews/Contracts, and the R03 Markdown renderer, CSS and template. Only the specifically
authorized application research-error type and API failure projection are excluded from those
application/backend comparisons. All existing gateway top-level helpers remain byte-identical,
including final-text extraction, secret scanning and other-provider source normalization.

| Protected artifact | SHA-256 |
|---|---|
| 0001 | `aa46ffadabb227b86124e396b66a5fe6a0839a7439ad10ab4a726e4f6788daf8` |
| 0002 | `36441501046bd5594401c989bbf7424e997bb6b687fdafd71c34c3e663eaefe3` |
| 0003 | `5a5056490eed678e8533a20719c0c6becf7d8f40da3af26f54d689329b81caf6` |
| NarrativeGateway module | `200e474605c080cf7c170527a3f0de373a41dd9695725f19ee83b6c1c5f9f1f6` |
| Legacy validator function source | `1f52c6c6094ce9b25fe0a7a22ddfdea0e52d8484eb5032ab4bac5e8b9ff1d271` |

No 0004 or other migration exists. Head remains `0003_task007c1_narrative_ledger`. Narrative schema,
lineage, request/output versions, prompt semantics, request hashes and exact response text/hashes
are unchanged. API integration tests compare SQLite schema and all prior Narrative rows before/after
failed SEARCH/SYNTHESIS. No raw response/restoration token, synthetic secret or hidden reasoning
enters persisted evidence. No protected OFF-path semantic change requires another paid OFF smoke.

## Deterministic validation

Environment: Windows, Python 3.12.14, pytest 8.4.1, Playwright 1.55.0, Chromium 140.0.7339.16,
Ruff 0.12.9, mypy 1.17.1; repository-declared dependencies. Browser tests launch real Chromium and
the real local Uvicorn/static UI against synthetic intercepted API responses, with fresh SQLite.
No test is rewritten, skipped or weakened to avoid Chromium or business assertions.

Commands ran from the isolated checkout with its Python environment. Browser settings were
`PYTHONUTF8=1`, `PYTHONPATH=<checkout>`, `TASK007C_BROWSER_CHANNEL=chromium`, and
`PLAYWRIGHT_BROWSERS_PATH=<existing local Playwright runtime>/browsers`. Temporary databases,
logs and screenshots stayed outside Git.

| Validation | Result |
|---|---|
| Focused command below | 665 passed, 1 warning in 87.03s |
| `python -m pytest -ra --basetemp=../task007c1-test-tmp/r04-full` | 1203 passed, 1 skipped, 1 warning in 1096.26s; 1204 collected |
| `python -m pytest tests/browser -ra --basetemp=../task007c1-test-tmp/r04-browser` | 85 passed, 1 warning in 89.18s; all 85 executed business assertions, no skips/failures |
| `python -m ruff check .` | All checks passed |
| `python -m ruff format --check .` | 192 files already formatted |
| `python -m mypy src tests` | Success, 188 source files |
| Fresh SQLite Alembic upgrade/current/heads | PASS, exactly 0003 |
| Real Uvicorn health/root/OpenAPI/configuration HTTP smoke | PASS; all 200, 11 models, DeepSeek default |
| Production PowerShell handshake over real HTTP | Same SHA exit 0; stale SHA exit 2 |
| Protected/secret/private-artifact/unsafe DOM audit | PASS; protected hashes unchanged, no secret/private runtime artifacts staged |

Focused command:

```text
python -m pytest tests/unit/test_paqs_e_research_continuation.py tests/unit/test_paqs_e_native_research.py tests/unit/test_paqs_e_model_gateway.py tests/unit/test_paqs_e_remediation_01.py tests/unit/test_paqs_e_narrative_provider.py tests/integration/test_runtime_source_revision.py tests/integration/test_windows_launcher.py tests/integration/test_paqs_e_narrative_ledger_api.py tests/integration/test_paqs_e_native_memo_ledger.py tests/integration/test_paqs_e_research_continuation_api.py tests/browser/test_paqs_e_research_diagnostic.py tests/browser/test_paqs_e_safe_markdown.py tests/browser/test_paqs_e_multi_model.py -ra --basetemp=../task007c1-test-tmp/r04-focused-final
```

The sole skip is the existing optional PostgreSQL migration smoke: `PHASE1_POSTGRESQL_TEST_URL`
is not configured (`tests/integration/test_postgresql_migrations.py:67`); PostgreSQL execution is
not claimed. No browser tests were skipped. The warning is the existing Starlette deprecated
`anyio.abc.BlockingPortal` alias. Initial local
development runs exposed and corrected gateway dispatch wiring, formatting and a focused-command
path typo before final validation; no failure expectation was weakened.

The standalone startup smoke used source identity equal to the checked-out Contract SHA while
testing the uncommitted implementation tree; a post-publication repeat verifies the final commit
identity. Only its own temporary Uvicorn process was terminated. No user runtime/database was used.

## Older-test supersession

Only `tests/unit/test_paqs_e_native_research.py` has existing test changes:

1. `test_native_memo_without_sources_or_queries` now rejects the old `Return only JSON` instruction
   rather than every occurrence of the word JSON; R04 explicitly says not to emit application JSON
   merely to satisfy a schema. It still proves ordinary text/no structured format and one direct call.
2. The `actions` case in `test_native_memo_fails_closed_without_retry` now tests 65, replacing the
   superseded 11-call failure. New tests prove 11 and 64 direct calls succeed and 11 tool-only calls
   enter exactly one synthesis with unchanged items.
3. The old `missing` first-response-message failure case is removed from that one-request failure
   table. New tool-only lifecycle tests replace it; missing/empty/multiple SYNTHESIS messages still
   fail after exactly two calls with no retry or final analysis. Malformed SEARCH messages still fail.

All R03 Markdown/opt-in browser tests remain intact. Legacy structured normalizer/validator tests,
including the unused legacy DeepSeek JSON helper's historical bounds, remain unchanged; normal
DeepSeek research now uses only the R04 native lifecycle. OpenAI/Alibaba guarantees are preserved.

## Stop and remaining acceptance

No paid live provider call was made by Codex. No real credential was requested, exposed or committed.
No migration, model/provider, endpoint, fallback/retry, arbitrary URL, background analysis, broker/
trading, PAQS-Q, backtest or portfolio scope was added. No merge or authoritative branch move occurred.

Stop for independent review of the exact final implementation SHA. After review passes, the user
must perform one explicitly authorized DeepSeek V4 Flash Research-ON Analyze (preferably US.AVGO,
paqs-e-master) on that reviewed SHA, confirming health identity/head 0003 and manually opting in.
Required live evidence remains a durable successful Narrative/revision with non-empty frozen memo,
one-/two-stage provenance, matching request/response hashes, and tool-free final reasoning. If it
fails, collect only safe diagnostics and stop without retry. Final PASS and integration remain gated
on that evidence, final Git topology verification and separately explicit integration authorization.
