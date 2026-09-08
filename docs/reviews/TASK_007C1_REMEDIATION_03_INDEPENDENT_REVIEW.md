# TASK-007C1 Remediation 03 — Independent Review

Status: **CODE / CONTRACT REVIEW PASS — DEEPSEEK RESEARCH-ON LIVE ACCEPTANCE PENDING**

Reviewed implementation SHA: `a9c7eabd1862d491f61843dfc68cbc3a1d9c936f`

Remediation 03 Contract commit / direct implementation parent: `5285ed7d4553e7a9d3860b9263135d4d94b2f3e5`

Remediation 03 implementation base: `74a19387adc408e9453c30fdbb30e6636ac4e695`

Authoritative branch: `roadmap/no-live-trading`

Authoritative SHA during review: `80f089bc2d285cca492c41aaeaf047e177bc2812`

Task branch: `task/007c1-paqs-e-multi-model-web-research`

Review branch: `review/007c1-remediation-03-independent`

Review date: 2026-09-08

This review is independent of the Codex implementation report. GitHub repository contents at the exact reviewed SHA are the source of truth. Claimed local test counts in the implementation report are treated as handoff evidence only and are not represented here as independently executed tests.

---

## 1. Git provenance gate — PASS

GitHub comparison verified:

- `5285ed7d... -> a9c7eabd...`: ahead 1 / behind 0;
- task branch HEAD equals exact reviewed SHA `a9c7eabd...`;
- authoritative `roadmap/no-live-trading` remains exactly `80f089bc...`;
- task branch is ahead 8 / behind 0 relative to authoritative;
- merge base remains exactly `80f089bc...`;
- no authoritative merge was performed during review.

The Remediation 03 implementation diff contains only the authorized research/UI/test/document changes. It does not contain:

- a database migration;
- edits to migrations 0001/0002/0003;
- Narrative Ledger schema/repository changes;
- PAQS-E primary strategy changes;
- Narrative runtime prompt changes;
- legacy validator/runtime changes;
- model-registry/provider-endpoint changes;
- credential-store architecture changes;
- launcher/source-revision changes.

---

## 2. Review conclusion

No blocking code/contract defect was found in the Remediation 03 implementation at `a9c7eabd...`.

The code/contract review therefore passes this exact SHA to the final user-executed DeepSeek V4 Flash research-ON live acceptance gate.

This is **not final TASK-007C1 PASS** until that live gate succeeds on this exact SHA and a final branch/topology gate confirms the task branch has not mutated.

Do not merge before the live gate.

---

## 3. R03-A — DeepSeek provider-native research memo — PASS

A dedicated DeepSeek-only normalizer is introduced at:

`src/ai_infra_quant/integrations/openai_reasoning/deepseek_research.py`

The shared research gateway delegates to this path only for `provider_id == "deepseek"`; OpenAI/Alibaba keep the pre-existing source-normalized research path.

Verified DeepSeek research behavior:

- uses the registered DeepSeek model and fixed registered research endpoint;
- uses one Responses request;
- `store=false`;
- `stream=false`;
- only native `web_search` tool is requested;
- `tool_choice=required`;
- output budget remains bounded;
- research instructions request a factual memo rather than application JSON;
- research instructions retain the Snapshot As-Of cutoff and Snapshot-facts-take-precedence rule;
- no application-side retry or provider/model fallback is added.

The native response can succeed without `action.sources` and without an exposed query string, provided there is a completed response, at least one completed `web_search_call`, at least one `search` action, legal native actions only, and exactly one bounded non-empty final memo.

This directly addresses the real live failure that remained at `74a19387...` without weakening the successful final Narrative reasoning path.

---

## 4. DeepSeek native action and memo bounds — PASS

The normalizer accepts only:

- `search`;
- `open_page`;
- `find_in_page`.

Unknown actions fail closed.

Verified local bounds and checks include:

- maximum 10 accepted native action records;
- at least one `search` action;
- maximum four retained provider-exposed query strings;
- query strings are optional when the provider does not expose them;
- memo must be one non-empty string;
- memo maximum 24,000 characters before total-capsule accounting;
- response id is optional but, when retained, must match a bounded safe character set;
- completed response required;
- incomplete/failed/cancelled/refusal/malformed output fails;
- hidden `reasoning` output items are ignored and never persisted;
- arbitrary extra tool/output types fail closed;
- secret echo remains rejected by the gateway before normalization.

No raw provider response dump or chain-of-thought is retained.

---

## 5. Optional source/citation provenance — PASS

The DeepSeek memo is explicitly treated as provider-native auxiliary research, not as sentence-level independently verified source material.

When native source/citation records are present, the implementation validates and bounds them before retaining provenance.

Verified safeguards include:

- raw record count capped before deduplication;
- retained URLs limited to `http` / `https`;
- userinfo/embedded credentials rejected;
- malformed ports/hostnames rejected;
- control/whitespace/backslash URL tricks rejected;
- URL/title lengths bounded;
- arbitrary URL text occurring only in the memo is not promoted into trusted source provenance;
- timezone-aware publication timestamps are retained when usable;
- known future-dated sources are excluded from trusted provenance;
- the memo is retained with an explicit limitation rather than pretending every statement has URL/timestamp verification.

The required limitation text states that source URLs/publication times may be incomplete, cutoff compliance cannot be independently verified for every memo statement, and frozen Snapshot market facts take precedence.

This matches the approved Remediation 03 contract, including `as_of_compatible=true` subject to that explicit limitation.

---

## 6. Frozen research before final Narrative — PASS

The research stage remains separate from final PAQS-E reasoning.

The integration path freezes the native memo into `auxiliary_context` before building the Narrative request. Final Narrative reasoning then receives the frozen request with:

- the memo already present in `auxiliary_context`;
- `web_research=true`;
- final reasoning `tools=[]`;
- final reasoning `tool_choice=none`;
- no JSON-schema output requirement;
- no research continuation inside final reasoning.

If explicitly requested research fails, final Narrative reasoning is not invoked and no Narrative Run/Result is fabricated.

The already live-passed research-OFF Narrative path remains structurally unchanged by this remediation.

---

## 7. R03-B — safe formatted Narrative view — PASS

A local parser is added at:

`src/ai_infra_quant/frontend/static/narrative-markdown.js`

It is loaded locally before `paqs-e.js`. No CDN or remote Markdown dependency is introduced.

The parser builds the formatted view using DOM elements and text nodes. Model text is never inserted as trusted HTML.

Supported presentation includes:

- H1–H4 headings;
- paragraphs;
- unordered and ordered lists;
- bounded nested lists;
- bold and italic emphasis;
- inline code;
- fenced code blocks;
- horizontal rules;
- blockquotes;
- simple pipe tables with horizontal-scroll wrapper.

This is sufficient for the real AVGO Narrative format that motivated the remediation.

---

## 8. Markdown/XSS boundary — PASS

The formatted renderer does not create model-controlled anchors or images. Model-provided HTML and Markdown link/image syntax therefore remain inert text.

The implementation does not use model text as `innerHTML`.

Browser tests cover hostile/malformed inputs including:

- `<script>`;
- `<img onerror>`;
- `<a href="javascript:...">`;
- `<style>`;
- `<iframe>` / `srcdoc`;
- Markdown `javascript:`, `data:`, `file:` and protocol-relative link/image forms;
- malformed tables;
- unmatched formatting delimiters;
- unclosed fences;
- escaped Markdown punctuation;
- long tokens/code/table cells;
- nested lists;
- Chinese/Unicode text.

Tests also assert no model-created external request occurs and no executable model DOM elements are created.

---

## 9. Formatted/raw auditability — PASS

Narrative persistence remains unchanged. The exact stored `response_text` and its SHA remain authoritative.

For a Narrative result, the UI now exposes:

- `格式化` — default derived presentation;
- `原文` — exact persisted response text.

Switching views changes only presentation state. It does not:

- send Analyze;
- call a provider;
- mutate ledger state;
- change the selected Narrative;
- alter the response SHA;
- alter frozen Snapshot/research evidence.

The browser regression verifies exact raw-text equality and retained result identity/hash while toggling views.

Legacy structured Decision rendering remains separate.

---

## 10. R03-C — research default OFF / explicit opt-in — PASS

The old automatic behavior is removed.

`modelChanged()` now always sets:

`web-research.checked = false`

and disables the checkbox only when the selected model does not support research.

Verified intended behavior:

- initial DeepSeek selection starts research OFF;
- research-capable model selection does not auto-check research;
- model changes reset research to OFF;
- unsupported models remain disabled and unchecked;
- explicit user checkbox state is what enters the Analyze payload;
- reload does not persist research opt-in;
- no localStorage/sessionStorage/cookie persistence for research is added;
- UI includes a cost/latency disclosure.

This directly fixes the dogfood issue where an intended OFF smoke accidentally submitted `web_research=true`.

---

## 11. Protected components — PASS

The Remediation 03 diff does not modify the protected product components that were explicitly out of scope:

- PAQS-E primary strategy / Context-Free Master Spec;
- accepted Narrative runtime prompt;
- legacy deterministic validator/runtime;
- migrations 0001/0002/0003;
- Narrative Run/Result schema and lineage;
- Narrative response/request hashing semantics;
- secure credential store;
- model registry/model list/endpoints;
- stale-backend source-revision handshake;
- Snapshot construction;
- long-running non-aborting Analyze guard;
- no-live-trading boundary.

Migration head therefore remains `0003_task007c1_narrative_ledger`.

---

## 12. Test review

The Remediation 03 diff adds focused deterministic/browser coverage for the authorized changes.

Independently inspected tests include:

- native memo success without sources/query exposure;
- `search -> open_page -> find_in_page` acceptance;
- query/citation retention when present;
- future citation exclusion;
- malformed/unsafe URL handling;
- action/query/source/memo bounds;
- refusal/incomplete/failed/malformed/secret/model-id failure behavior;
- no internal retry;
- research memo freeze into the Narrative request;
- final Narrative `tools=[]` after research;
- ledger request/result hash readback with research ON/OFF;
- no fabricated Narrative Run/Result after research failure;
- formatted AVGO-like Markdown;
- formatted/raw toggle identity preservation;
- hostile Markdown XSS/network tests;
- mobile-width/table overflow behavior;
- research default OFF and explicit ON payload behavior;
- research failure preserves prior Narrative and does not retry.

Codex reports 1,130 passed, 1 optional PostgreSQL skip; 82 browser tests; 570 focused tests; Ruff/format/mypy/migration/startup/protected-file checks passed. Those counts are not independently re-executed in this review, but the relevant test code was inspected and no weakening/xfail bypass was found in the Remediation 03 diff.

---

## 13. External provider contract consistency

Current DeepSeek Responses documentation continues to describe server-side `web_search_call` output with actions `search`, `open_page`, and `find_in_page`, and supports the native `web_search` tool with server-side continuation bounded to 10 rounds.

The Remediation 03 adapter is therefore directionally consistent with the documented provider contract while deliberately not requiring undocumented source/query fields for success.

Live provider behavior remains an external acceptance gate.

---

## 14. Remaining acceptance gate

The previous exact SHA `74a19387...` already has user-executed live PASS evidence for DeepSeek V4 Flash Narrative reasoning with `web_research=false`, including verified request/response hashes and a >180-second successful completion.

Because Remediation 03 does not modify that final Narrative provider/Ledger path, another paid OFF smoke is not required for this review.

One paid user-executed gate remains on exact SHA `a9c7eabd...`:

- Security: `US.AVGO` or another supported Security;
- model: DeepSeek V4 Flash;
- strategy: `paqs-e-master`;
- user explicitly checks Web Research;
- exactly one Analyze submission;
- research stage must succeed;
- final Narrative must succeed;
- resulting Narrative Run must persist `web_research=true` and a non-empty frozen `auxiliary_context` containing the DeepSeek native research memo/provenance;
- request and response hashes must verify;
- formatted UI should render the final Narrative readably while raw mode remains exact.

If that gate fails, do not merge and do not automatically retry.

If it passes, update independent review evidence to final PASS only after confirming:

- task branch still equals the exact live-tested SHA;
- authoritative branch still equals the expected base;
- merge base remains the expected authoritative SHA;
- ahead/behind permits non-force fast-forward integration.

---

## 15. Current disposition

**CODE / CONTRACT REVIEW PASS — LIVE DEEPSEEK RESEARCH-ON ACCEPTANCE PENDING**

No merge performed.
