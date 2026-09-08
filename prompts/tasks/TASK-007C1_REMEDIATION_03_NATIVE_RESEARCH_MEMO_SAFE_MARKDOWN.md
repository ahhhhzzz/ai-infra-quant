# TASK-007C1 REMEDIATION 03 — Provider-Native Research Memo + Safe Narrative Markdown

Status: **APPROVED REMEDIATION CONTRACT — user-authorized remediation only**

Issued: 2026-09-08

Repository: `ahhhhzzz/ai-infra-quant`

Authoritative branch: `roadmap/no-live-trading`

Authoritative SHA at issuance: `80f089bc2d285cca492c41aaeaf047e177bc2812`

TASK-007C1 branch: `task/007c1-paqs-e-multi-model-web-research`

Exact remediation base / latest reviewed implementation SHA: `74a19387adc408e9453c30fdbb30e6636ac4e695`

Original TASK-007C1 Contract commit: `9f41016b2341e91ad2825b7f731bca4f378b0108`

Remediation 01 Contract commit: `b7316e83f7fd377f4c628db90dee8e3d7b4a5335`

Remediation 02 Contract commit: `ca1b71f94565dee02f0bd43d280a59f3ec15ac6d`

Original Contract:
`prompts/tasks/TASK-007C1_PAQS_E_MULTI_MODEL_SECURE_CREDENTIALS_WEB_RESEARCH.md`

Remediation 01 Contract:
`prompts/tasks/TASK-007C1_REMEDIATION_01_LIVE_DOGFOOD_RUNTIME_COMPATIBILITY.md`

Remediation 02 Contract:
`prompts/tasks/TASK-007C1_REMEDIATION_02_NARRATIVE_FIRST_REASONING.md`

This remediation is intentionally narrow. It preserves the successfully dogfooded Narrative-first reasoning path and fixes only:

1. DeepSeek web-research acceptance, which is still failing before final Narrative reasoning;
2. Narrative presentation, which currently shows raw Markdown punctuation as plain text;
3. the current UI behavior that automatically enables paid web research when a supported model is selected.

No other product behavior is authorized.

---

## 1. Accepted live evidence

### 1.1 Narrative-first reasoning without research — LIVE PASS

On exact implementation SHA:

`74a19387adc408e9453c30fdbb30e6636ac4e695`

with:

- Security: `US.AVGO`;
- provider: `deepseek`;
- model: `deepseek-v4-flash`;
- strategy: `paqs-e-master`;
- `web_research=false`;

real local dogfooding produced a successful Narrative result.

Verified safe evidence:

- Narrative Run: `b45f2209-54ae-464a-80e4-651c2ffb40d6`;
- status: `SUCCEEDED`;
- Narrative Result: `7db32fc2-fb2a-4849-8b84-cded2239079d`;
- revision: `1`;
- provider response id: `c3fda397-5a60-479c-b326-6d11515caa6f`;
- response characters: `4043`;
- persisted response SHA-256 verified true;
- persisted request SHA-256 verified true;
- `web_research=false`;
- frozen auxiliary context count = `0`.

The request ran for approximately 235 seconds and still returned successfully, providing real product evidence that the Remediation-01 non-aborting long-running guard works.

**This successful path is protected. Do not redesign or replace it in this remediation.**

### 1.2 DeepSeek research ON — LIVE FAIL

On the same exact SHA, the user explicitly enabled web research for:

- `US.AVGO`;
- DeepSeek V4 Flash;
- `paqs-e-master`.

The product returned:

`PAQS_E_RESEARCH_PRECONDITION_FAILED`

with:

`Requested web research could not produce a complete auditable capsule.`

No Narrative Run or Result was fabricated, which is correct.

This isolates the remaining live blocker to the research stage:

```text
Snapshot freeze                 PASS
DeepSeek Narrative final text   PASS
Narrative Ledger                PASS
DeepSeek Web Research capsule   FAIL
```

### 1.3 Narrative formatting UX defect

The successful Narrative response contains ordinary Markdown-style structure such as:

- `#` / `##` headings;
- `**bold**` emphasis;
- bullet lists;
- numbered lists;
- inline code using backticks;
- tables using pipes;
- horizontal separators.

The current UI deliberately renders the exact text in an inert `<pre>`/`textContent` representation. That is safe, but user-facing output visibly contains raw Markdown punctuation and tables do not render as tables.

The user explicitly approved a safe formatted view while preserving exact raw-text auditability.

### 1.4 Research default UX defect

The current browser automatically sets the research checkbox to checked whenever the selected model reports `web_research_supported=true`.

This caused an earlier attempted research-OFF smoke to actually submit `web_research=true`.

The user explicitly approved changing web research to **default OFF / explicit opt-in only**.

---

## 2. Remediation scope

Implement only these three changes:

### R03-A — DeepSeek provider-native research memo

Replace the current DeepSeek-only requirement that native web search must be converted into the strict source-normalized JSON summary capsule with a provider-native final research memo acceptance path.

### R03-B — Safe formatted Narrative presentation

Display persisted Narrative Markdown-like prose in a readable, safe formatted view while preserving the exact immutable raw text and SHA.

### R03-C — Explicit research opt-in

Web research must be unchecked by default and must never become enabled/checked merely because the user selects a research-capable model.

Everything else is out of scope.

---

## 3. Permanent boundaries remain unchanged

Preserve all existing permanent boundaries:

- local-first, single-user;
- loopback-only server;
- read-only quantitative research / decision support;
- no broker account connection or observation;
- no broker write;
- no live OMS/EMS;
- no autonomous/unattended trading;
- no order APIs;
- no automatic Analyze;
- no automatic retry after provider/research failure;
- no provider/model fallback;
- no model voting/ensemble;
- no PAQS-Q;
- no backtest;
- no portfolio/PnL/positions;
- no Phase 5/live trading;
- Snapshot remains immutable and authoritative for market facts;
- web research remains auxiliary and cannot mutate Snapshot facts;
- final PAQS-E Narrative reasoning remains tool-free;
- credential storage/security remains unchanged;
- stale-backend source-revision handshake remains unchanged;
- long-running Analyze guard remains non-aborting;
- Narrative-first Ledger remains immutable and append-only;
- legacy structured history remains read-only historical evidence.

---

# PART A — DEEPSEEK PROVIDER-NATIVE RESEARCH MEMO

## 4. Preserve research separation

The required lifecycle remains:

```text
User explicitly checks Web Research
↓
Freeze immutable Snapshot
↓
Selected provider/model performs bounded research
↓
Normalize/freeze one or more auxiliary_context items
↓
Build immutable NarrativeRequest
↓
Final Narrative reasoning with tools disabled
↓
Persist Narrative Run + Result
```

Do **not** allow the final Narrative reasoning call to invoke web search.

Do **not** merge research and final reasoning into one provider call.

Do **not** silently continue without research when the user explicitly requested research.

Do **not** automatically retry a paid research call.

---

## 5. DeepSeek research success criterion

For `provider_id == "deepseek"`, research must no longer require the model's final research text to be JSON of the form:

```json
{"items":[{"url":"...","summary":"..."}]}
```

and must no longer require every included memo statement to be linked to a provider-native `action.sources` record before the research stage can succeed.

Instead, DeepSeek research may succeed when all of the following are true:

1. the registered DeepSeek research endpoint/model route is used;
2. the request is one bounded native Responses web-search request;
3. no application retry or continuation request is sent;
4. the provider response is a completed successful envelope;
5. no credential secret appears in retained response material;
6. returned model identity matches the selected DeepSeek model when supplied;
7. at least one completed native `web_search_call` exists;
8. at least one completed `web_search_call.action.type == "search"` exists;
9. every accepted web-search action type is one of:
   - `search`;
   - `open_page`;
   - `find_in_page`;
10. unknown action types fail closed;
11. the existing maximum 10 DeepSeek native web-search action records remains;
12. when query strings are exposed, no more than four bounded search queries may be retained;
13. absence of a provider-exposed query string by itself must not invalidate an otherwise completed native search call;
14. exactly one bounded non-empty final research text/memo can be extracted from the provider response;
15. provider refusal, incomplete/cancelled/failed response, unexpected tool shape, unsafe response id, secret echo or malformed envelope still fails closed.

The goal is to trust the provider-native **research operation and final research memo as auxiliary material**, not to claim that every sentence has independently verified URL-level provenance.

---

## 6. DeepSeek research request

Keep the research request narrow and cost-aware.

Requirements:

- selected model route only;
- one HTTP request;
- `store=false` where supported;
- `stream=false`;
- native `web_search` tool only;
- no arbitrary tools;
- no provider/model fallback;
- no app-side retry;
- no app-side multi-turn continuation;
- explicit intent bounded to the selected Security and Snapshot As-Of cutoff;
- instruction to return a concise factual research memo rather than JSON required for application schema compliance;
- instruction not to provide chain-of-thought;
- instruction not to treat web prices as authoritative Snapshot facts;
- instruction not to use sources published after the Snapshot cutoff;
- a bounded output-token budget consistent with the existing cost controls.

Do not require the provider to emit a PAQS-E trading analysis during research. Research is factual auxiliary context only.

---

## 7. DeepSeek frozen research memo

Normalize the successful provider-native research response into a bounded `AuxiliaryContextItem` or equivalent existing auxiliary-context representation.

Preferred v1 representation: one primary memo item.

Conceptually:

```text
category = web_research
source_label = DeepSeek native web research memo
content = exact bounded final research memo text
source_timestamp = null unless one authoritative memo-level timestamp exists
as_of_compatible = true, subject to explicit limitation below
provenance = bounded canonical JSON
```

The memo `content` must be the final visible research memo only.

Never retain:

- chain-of-thought;
- reasoning tokens;
- encrypted reasoning traces;
- provider debug bodies;
- API keys;
- hidden prompts;
- raw provider response dumps.

---

## 8. Research provenance for DeepSeek memo

The memo provenance must remain auditable without pretending stronger provenance than the provider exposed.

Include bounded safe metadata such as:

- provider id;
- model id;
- provider response id when safe;
- retrieval timestamp;
- original research intent;
- Snapshot As-Of cutoff;
- number of native web-search action records;
- ordered accepted action types;
- search query strings when actually exposed by the provider;
- verified native citation/source URLs when actually exposed;
- publication timestamps when actually exposed and valid;
- explicit provenance-quality/limitation text.

Required limitation when URL-level or publication-time metadata is incomplete:

> Provider-native web research memo. Source URLs and/or publication times were not fully exposed by the provider response; cutoff compliance was requested but cannot be independently verified for every memo statement. Frozen Snapshot market facts take precedence.

Equivalent concise wording is allowed.

Do not fabricate URLs, source titles, publication timestamps or query strings.

Do not infer a URL from arbitrary prose.

---

## 9. Optional native citations/sources

When DeepSeek actually exposes URL citations or source records:

- validate URL syntax;
- accept only `http`/`https`;
- reject embedded credentials/userinfo;
- bound individual URL length;
- bound total retained URL/source records to the existing conservative maximum of 64;
- deduplicate only after raw-record count enforcement;
- do not accept an arbitrary URL merely because the final memo text contains it;
- retain publication timestamp only if it parses as timezone-aware;
- if a known publication timestamp is after the Snapshot cutoff, do not promote that citation/source as As-Of-compatible evidence.

A future-dated optional citation must not automatically make the entire provider-native memo disappear if the memo otherwise satisfies the native research contract; instead exclude that citation from trusted provenance and preserve an explicit limitation.

The final Narrative prompt already treats Snapshot market facts as authoritative.

---

## 10. DeepSeek research bounds

Preserve or tighten these bounds:

- maximum 10 native DeepSeek `web_search_call` action records;
- at least one `search` action;
- maximum four retained provider-exposed search queries;
- maximum 64 raw native source/citation records;
- maximum 64 retained/deduplicated safe URLs;
- final memo text maximum 24,000 Unicode characters;
- auxiliary item total serialized size must remain compatible with the existing Narrative request/ledger bounds;
- provider response transport remains capped at the existing 2 MB HTTP response bound;
- no automatic retry.

If the memo exceeds the accepted local bound, fail closed rather than truncating silently.

---

## 11. Other providers

Do **not** automatically relax all providers to the DeepSeek memo semantics.

For OpenAI / Alibaba research routes:

- preserve existing source-normalized behavior unless a tiny internal refactor is required to share safe helpers;
- do not reduce existing source provenance guarantees without separate evidence and approval;
- do not alter model registry entries;
- do not add providers/models.

This remediation is specifically motivated by the real DeepSeek research failure.

---

## 12. DeepSeek research tests

Add deterministic fixtures proving at minimum:

1. completed `search -> final memo` with no `action.sources` succeeds;
2. completed `search -> open_page -> final memo` succeeds;
3. completed `search -> open_page -> find_in_page -> final memo` succeeds;
4. no provider-exposed query string can still succeed if a real completed `search` action exists;
5. exposed bounded query strings are retained in provenance;
6. optional native URL citations are retained safely;
7. arbitrary URLs appearing only in memo prose are not promoted to trusted citations;
8. future-dated optional citation is excluded from trusted provenance and limitation remains visible;
9. more than 10 actions fails;
10. unknown action type fails;
11. no `search` action fails;
12. incomplete/cancelled/failed response fails;
13. refusal fails;
14. missing/empty memo fails;
15. oversize memo fails;
16. secret echo fails;
17. wrong model identity fails;
18. no retry occurs;
19. research ON freezes a non-empty auxiliary context before final reasoning;
20. final Narrative reasoning call still has `tools=[]` / equivalent no-tool behavior.

---

# PART B — SAFE NARRATIVE MARKDOWN PRESENTATION

## 13. Persistence remains exact raw text

Do not change Narrative persistence semantics.

The database remains authoritative for the exact provider final text:

- `response_text` remains byte/Unicode-for-Unicode the accepted provider final text;
- `response_text_sha256` remains computed from that exact text;
- no Markdown rendering output is persisted as the Narrative result;
- no HTML rendering output is hashed as the Narrative result;
- revision lineage remains unchanged;
- successful existing result `7db32fc2-fb2a-4849-8b84-cded2239079d` must remain readable and hash-valid.

Formatted Markdown is a **derived presentation only**.

---

## 14. Default formatted view + explicit raw view

For Narrative results, the UI must provide two presentation modes:

- **格式化** — default user-facing view;
- **原文** — exact persisted response text for audit/debug/copying.

Switching views:

- must not call Analyze;
- must not mutate ledger state;
- must not alter the selected Narrative;
- must not refetch a provider;
- must not alter response SHA;
- must not lose the user's selected historical result.

Legacy structured Decision rendering remains unchanged.

---

## 15. Safe Markdown subset

The formatted Narrative view should support the common syntax already observed in real PAQS-E output:

- H1/H2/H3/H4 headings (`#` through `####`);
- paragraphs;
- unordered lists using `-`, `*` or `+`;
- ordered lists;
- modest nested list indentation where deterministic and safe;
- bold (`**text**` / `__text__`);
- italic (`*text*` / `_text_`) if safely supported;
- inline code using backticks;
- fenced code blocks;
- horizontal rules (`---`, `***`, `___`);
- Markdown pipe tables with a header separator row;
- blockquotes if implemented safely;
- ordinary line breaks.

This is presentation syntax only. It does not create structured PAQS-E fields.

No machine validation may reject a Narrative because Markdown is malformed. Unsupported syntax falls back to inert text.

---

## 16. Markdown security model

The formatted renderer must be safe by construction.

Preferred implementation for this local vanilla-JS application:

- parse the supported Markdown subset into DOM nodes using `document.createElement`;
- put textual content into `textContent` / text nodes;
- do not parse provider prose as HTML;
- do not use raw `innerHTML` with model content;
- do not use `insertAdjacentHTML` with model content;
- do not use `DOMParser` to turn model content into executable HTML;
- do not inject model-provided style/script/event attributes;
- do not execute HTML embedded in Markdown.

Raw HTML such as:

```html
<script>alert(1)</script>
<img src=x onerror=alert(1)>
```

must render as visible inert text or be safely escaped/represented, never as live DOM elements.

Do not load a Markdown renderer or sanitizer from a CDN.

Do not add remote runtime dependencies.

A small local audited dependency is allowed only if clearly justified in the implementation report and fully covered by browser XSS tests; a strict local DOM-based subset parser is preferred.

---

## 17. Links and images

Model prose is not a trusted source registry.

For v1:

- Markdown image syntax must never create an `<img>` from model output;
- render image syntax as inert text or label text;
- `javascript:`, `data:`, `file:`, custom schemes and protocol-relative URLs must never become clickable;
- if clickable Markdown links are implemented, only explicit `http://` or `https://` URLs may be used;
- any clickable link must use safe attributes such as `rel="noopener noreferrer"`;
- opening in a new tab is allowed but not required;
- a simpler acceptable implementation is to render Markdown link text and URL as inert text rather than a clickable anchor.

Provider-native frozen research source links, when separately rendered from trusted provenance, remain distinct from arbitrary links inside model prose.

---

## 18. Table presentation

The real AVGO Narrative contains a pipe table.

Formatted view must render valid simple Markdown tables readably:

- table header;
- separator row;
- body rows;
- text-only cell content with safe inline emphasis/code;
- horizontal overflow container on small screens;
- no arbitrary HTML inside cells;
- malformed tables fall back to inert text rather than broken HTML.

Do not attempt spreadsheet-style formula evaluation.

---

## 19. Responsive/accessibility requirements

Narrative formatted output must remain usable at existing browser widths covered by TASK-007C tests, including narrow mobile-sized viewport tests.

Requirements:

- no horizontal page overflow caused by long prose/table/code blocks;
- tables/code may scroll within their own container;
- headings remain visible in dark/light themes;
- formatted/raw toggle is keyboard reachable;
- current mode is exposed with `aria-pressed`, tab state, or equivalent accessible state;
- raw text uses `white-space: pre-wrap` or equivalent;
- formatted view preserves readable spacing.

---

## 20. Markdown regression fixture

Use a regression fixture closely matching the real successful AVGO Narrative characteristics:

```markdown
# PAQS-E 研究报告

## 结论

- 当前为 **WATCH_LONG**。
- `CURRENT_PRICE_REFERENCE` 仅供参考。

---

## 关键位置

| 区域 | 角色 | 说明 |
|---|---|---|
| 342–350 | 支撑 | 失败下破候选 |
| 371–377 | 阻力 | 结构确认区 |

1. 等待完成 M30。
2. 不追价。
```

Browser tests must prove the formatted view contains actual headings/lists/table/code/emphasis rather than visibly exposing formatting punctuation as the primary view.

The raw view must still exactly equal the persisted source string.

---

## 21. Markdown hostile-content tests

At minimum prove that all of these are inert:

```text
<script>window.attack=1</script>
<img src=x onerror="window.attack=2">
[bad](javascript:alert(1))
![bad](javascript:alert(1))
<a href="javascript:alert(1)">x</a>
<style>body{display:none}</style>
<iframe srcdoc="<script>alert(1)</script>"></iframe>
```

Also test:

- malformed table;
- unmatched bold/code delimiters;
- very long unbroken token;
- nested lists;
- Unicode/Chinese text;
- backslash-escaped Markdown punctuation;
- raw/formatted switching after a delayed history read;
- selected Narrative does not change during rendering-mode switch.

No script execution, network fetch from model-created image, or DOM event handler may occur.

---

# PART C — EXPLICIT RESEARCH OPT-IN

## 22. Research default OFF

Web research is a paid/variable-latency auxiliary operation and must be explicit.

Required browser behavior:

- initial page configuration: research checkbox is unchecked;
- selecting DeepSeek V4 Flash: checkbox remains unchecked;
- selecting any other research-capable model: checkbox remains unchecked;
- changing models resets research to unchecked;
- selecting a model that does not support research disables the checkbox and leaves it unchecked;
- selecting a model that supports research enables the checkbox but does not check it;
- user must explicitly click/check research before an Analyze payload may contain `web_research=true`.

Do not persist research opt-in in localStorage/cookies/sessionStorage.

Do not remember it across reloads.

Do not auto-enable it from previous Narrative history.

---

## 23. Research UX text

Near the checkbox, show a concise disclosure such as:

> 联网研究默认关闭；开启会先进行额外的提供方联网研究请求，可能增加耗时和 API 成本。

Equivalent concise Chinese wording is allowed.

Do not expose provider implementation jargon in the normal control label.

---

## 24. Explicit-intent tests

Browser tests must prove:

- default model DeepSeek loads with research OFF;
- model change never auto-checks research;
- clicking Analyze without explicit research interaction sends exactly one Narrative POST with `web_research=false`;
- after explicitly checking research, clicking Analyze sends exactly one Narrative POST with `web_research=true`;
- after changing model, research returns to false;
- no model/config/history/credential/market-refresh event dispatches Analyze;
- no automatic retry after research failure.

---

# PART D — PROTECTED COMPONENTS

## 25. Do not modify these semantics

This remediation must not alter:

- PAQS-E Context-Free Master Spec strategy semantics;
- accepted PAQS-E Doctrine;
- legacy structured validator rules;
- legacy structured runtime schema;
- migration 0001;
- migration 0002;
- migration 0003;
- existing Narrative Run/Result schema;
- Narrative revision lineage;
- response-text hash semantics;
- request hash semantics;
- secure credential store architecture;
- model registry/model list;
- provider endpoints;
- stale-backend handshake;
- no-live-trading boundary;
- long-running non-aborting guard;
- Snapshot construction;
- market-data provider behavior;
- final Narrative provider text success semantics that already passed live research-OFF dogfooding.

A code movement/refactor that preserves exact behavior is allowed only when necessary for the three authorized fixes and must be called out explicitly.

---

## 26. No database migration

Remediation 03 authorizes **no migration**.

Expected migration head remains exactly:

`0003_task007c1_narrative_ledger`

Do not add 0004.

Do not edit 0001/0002/0003.

---

## 27. No strategy/prompt semantic rewrite

Do not rewrite the PAQS-E primary strategy.

Do not change the successful Narrative prompt merely to cosmetically eliminate Markdown. The model may continue to produce Markdown-like reports; the UI should render them safely.

The DeepSeek research-stage instruction may be changed from strict JSON summary output to a plain bounded factual research memo because that is explicitly authorized here.

---

# PART E — API / LEDGER BEHAVIOR

## 28. Narrative API remains unchanged

Normal Analyze remains:

`POST /api/v1/paqs-e/narrative-analyses`

Do not change the request shape:

```json
{
  "security_id": "...",
  "model_key": "deepseek-v4-flash",
  "strategy_id": "paqs-e-master",
  "web_research": false
}
```

Do not introduce a second final-analysis endpoint.

Do not add background-job/polling APIs.

---

## 29. Research failure semantics

If the user explicitly requests research and DeepSeek provider-native research still cannot produce a valid completed memo under this remediation:

- return the existing safe research precondition failure;
- do not call final Narrative reasoning;
- do not create a Narrative Run/Result;
- do not retry automatically;
- preserve the prior successful Narrative in the UI as historical/earlier content;
- do not pretend research was disabled.

Research success must produce non-empty frozen auxiliary context in the Narrative request.

---

## 30. Audit display

When a successful Narrative used web research:

- existing frozen evidence/audit views must show the research auxiliary context;
- the user must be able to distinguish provider-native research memo/provenance from the final PAQS-E Narrative prose;
- display the provenance limitation when provider URL/timestamp coverage is incomplete;
- do not label unverified prose URLs as independently verified sources.

---

# PART F — VALIDATION

## 31. Required deterministic validation

At minimum run:

- full pytest suite;
- full browser suite;
- focused DeepSeek research tests;
- focused Narrative provider tests;
- focused Narrative API/Ledger tests;
- focused source-revision launcher tests;
- Ruff check;
- Ruff format check;
- mypy;
- fresh SQLite migration/health smoke confirming head remains 0003;
- real local Uvicorn/OpenAPI/root/configuration smoke with synthetic/no-paid provider behavior only;
- secret/private-artifact audit;
- protected-file hash/diff audit.

No ordinary automated test may call a paid real provider.

---

## 32. Required browser acceptance scenarios

Browser suite must include:

1. DeepSeek loads with research unchecked;
2. explicit research OFF Analyze payload;
3. explicit research ON Analyze payload;
4. research failure retains prior successful Narrative and does not retry;
5. formatted Narrative default view;
6. raw exact-text view;
7. real-table-like Markdown formatting;
8. dark/light modes;
9. desktop/mobile widths;
10. hostile HTML/Markdown XSS fixture;
11. no image/network side effect from model prose;
12. raw/formatted switching does not Analyze;
13. frozen Snapshot/research evidence remains associated with selected Narrative;
14. legacy structured history remains separately readable.

---

## 33. Live product acceptance after implementation

Do not perform paid provider calls during Codex implementation/testing.

After implementation is independently reviewed, the user performs the final provider gate on the exact reviewed final SHA.

Because the research-OFF Narrative path already passed live dogfooding on `74a19387...`, the mandatory Remediation-03 live acceptance is:

### Mandatory

One explicit DeepSeek V4 Flash Analyze with:

- one normal supported Security;
- `paqs-e-master`;
- web research explicitly ON;
- no automatic retry.

PASS requires:

- research stage succeeds;
- Narrative final reasoning succeeds;
- one successful Narrative Run + Result is committed;
- `web_research=true` in persisted Run/Result/request;
- frozen auxiliary context is non-empty;
- provider-native memo/provenance is present;
- response/request hashes verify;
- final Narrative text displays in formatted mode;
- raw mode exactly matches persisted response text.

### Research-OFF re-smoke

A second paid research-OFF call is **not mandatory** if independent review proves the successful NarrativeGateway/Ledger/provider path from `74a19387...` was not materially changed by Remediation 03.

If implementation changes NarrativeGateway final-reasoning semantics, Narrative Ledger persistence, or final-text acceptance behavior, then one exact-final-SHA research-OFF live smoke becomes mandatory again.

---

# PART G — IMPLEMENTATION REPORT

## 34. Required Remediation 03 implementation report

Codex must create:

`docs/TASK_007C1_REMEDIATION_03_IMPLEMENTATION_REPORT.md`

The report must include:

- exact final implementation SHA;
- exact parent Contract SHA;
- authoritative SHA and merge base;
- exact changed files;
- explanation of DeepSeek provider-native research memo behavior;
- evidence that other provider research behavior was not silently weakened;
- exact research bounds;
- exact provenance fields/limitations;
- exact Markdown supported subset;
- exact Markdown security construction;
- confirmation that raw Narrative text/hash remains unchanged;
- confirmation that research defaults OFF;
- test commands/results;
- migration head verification = 0003;
- protected-file audit;
- secrets/XSS audit;
- known limitations;
- explicit statement that no real provider call was made;
- explicit stop for independent review;
- no merge.

---

## 35. Stop conditions

Stop without implementation if any precondition is not true:

- task branch HEAD is not the Remediation 03 Contract commit;
- Contract commit parent is not exact base `74a19387adc408e9453c30fdbb30e6636ac4e695`;
- authoritative branch is no longer exact `80f089bc2d285cca492c41aaeaf047e177bc2812` before implementation starts;
- merge base is not exact authoritative SHA;
- task branch is behind authoritative;
- protected files already differ unexpectedly;
- required existing Narrative-first architecture is not present.

Do not repair unrelated repository state under this task.

---

## 36. Completion / acceptance criteria

Remediation 03 implementation is ready for independent review only when all are true:

- DeepSeek research accepts a completed provider-native memo without requiring strict JSON summary/source-array output;
- DeepSeek research still fails closed on unknown actions/incomplete/refusal/unsafe envelopes;
- final reasoning remains tool-free;
- frozen auxiliary context records honest provenance/limitations;
- research checkbox defaults OFF and requires explicit user opt-in;
- Narrative formatted view renders the real report structure readably;
- raw view preserves exact persisted text;
- hostile model HTML/Markdown is inert;
- no migration was added or changed;
- Narrative Ledger semantics are unchanged;
- research-OFF live-success path is not regressed by design;
- full required deterministic validation passes;
- task branch alone is pushed;
- authoritative branch remains unchanged;
- no merge occurs;
- Codex stops for independent review.

Final TASK-007C1 acceptance remains bound to a later independent review and user-executed real DeepSeek research-ON smoke on the exact reviewed implementation SHA.
