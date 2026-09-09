# TASK-ADC-001 Independent Review

Date: 2026-09-09
Disposition: **PASS WITH MINOR FINDING — focused documentation correction requested before integration**
Findings: **Critical 0 / Major 0 / Minor 1**

## 1. Exact review object and scope

| Reference | SHA |
|---|---|
| Reviewed implementation | `e2f19917d7dcad213b79702eedf733a1f7cc5108` |
| Sole parent / published contract | `ce3f3125b0cbfab10bf4f983736fffc2f6ff660f` |
| Authoritative baseline / merge base | `722936984deac652b443eba132c69650653345e1` |
| Unchanged accepted runtime implementation | `d2d25efc79d2560a7ed09895c7dd7a2c1724aee9` |

Contract: [TASK-ADC-001](../prompts/tasks/TASK-ADC-001_ARCHITECTURE_DOCUMENTATION_CONSOLIDATION.md).
Implementation report: [report](../reports/TASK_ADC_001_IMPLEMENTATION_REPORT.md).

GitHub commit and branch reads matched these references. The implementation is a single direct
child of the contract; authority remained at 7229369... and the task branch at e2f1991... during
review. An isolated detached local worktree at the exact implementation was used. No implementer
document, source file, test, database or original working tree was edited.

This is an independent docs-only review, not new runtime certification or user-local SHA acceptance.

## 2. Findings

### ADC-001-F01 — Minor — requirement evidence retained obsolete section/checkpoint references

Location: [REQUIREMENTS_MATRIX at reviewed SHA](https://github.com/ahhhhzzz/ai-infra-quant/blob/e2f19917d7dcad213b79702eedf733a1f7cc5108/docs/REQUIREMENTS_MATRIX.md), section 5.2, rows **PAQSE-003, PAQSE-013, PAQSE-015, PAQSE-019**.

Evidence:

- PAQSE-015 and PAQSE-019 still cite plain-text `API Contracts 5.10`. The consolidated
  [API_CONTRACTS](https://github.com/ahhhhzzz/ai-infra-quant/blob/e2f19917d7dcad213b79702eedf733a1f7cc5108/docs/API_CONTRACTS.md)
  has no section 5.10; the retained Legacy structured compatibility is now section 8.
  A reader cannot follow the stated current-document reference.
- PAQSE-003 now describes current Narrative/Legacy ports and registered model selection, but its
  evidence cell still names only the original 007A implementation. PAQSE-013 now describes local
  password submission, Windows service slots and current safe reads, but its evidence cell still
  names only the old 007A/007B implementation/review and Roadmap. Those historical checkpoints do
  not independently establish the C1-added Narrative gateway or Windows Credential Manager flow.
- The correct current source/test references already exist in section 10 and the implementation
  report. This is incomplete local traceability, not a missing runtime capability.

Impact: the consolidation substantially succeeds, but these four rows still require a reader to
repair the evidence mapping mentally. The 199/2 Markdown-link audit passes because plain-text
section citations and the semantic relevance of a historical SHA are outside that audit.

Requested correction, docs-only:

1. Replace the two obsolete 5.10 references with a valid link to current API section 8, or explicitly
   pin an original historical document/section if the intent is solely the original 007B contract.
2. In PAQSE-003 and PAQSE-013 retain historical attribution where useful, but add current C1/Narrative
   source/test evidence or a direct link to the matching section-10 rows. Do not attribute later
   behavior to the earlier implementation.
3. Preserve requirement IDs and all runtime/historical evidence bytes. Limit the correction to the
   matrix and a short new remediation note; do not rewrite the submitted implementation report.

Severity is Minor: correct descriptions and current evidence are available elsewhere in the same
document set, no runtime change exists, and no scope/security failure was found. Nevertheless,
repair these references before recommending integration of the final documentation baseline.

## 3. Independent verification

| Check | Result |
|---|---|
| Exact parent and authority/task references | PASS |
| Implementation delta from contract | Exactly 12 allowed documents; no other implementation path |
| Delta from authority | Same 12 documents plus the previously published ADC contract only |
| Protected baseline entries | **323 unchanged**, comparing recursive Git mode/type/blob identities |
| Published contract | Byte-identical to its published commit |
| Runtime/resources/tests/migrations/dependencies/CI/history | No changes; no 0004/archive implementation |
| Requirement identifiers | No previous requirement ID removed |
| Outgoing relative Markdown links in changed documents | **199 checked; zero missing paths/anchors** |
| Incoming Markdown links to changed documents | **2 checked; zero missing paths/anchors** |
| Fixed-baseline source/test links in implementation report | **18 checked** for existing files and referenced line bounds |
| Registered model guide | **11 entries** matched registry keys, provider identities and credential slots |
| Mermaid graph | **15 nodes / 19 edges**; used simple syntax subset, references and branch checks passed |
| `git diff --check 7229369... e2f1991...` | PASS |
| Review worktree | Clean before review publication |

The reviewer separately read the current component descriptions and relevant source:
NarrativeAnalysisService/build_narrative_request; composition; ModelRegistry/ModelCredentials;
credential routes/storage boundary; NarrativeGateway and final-text domain checks; ModelGateway
research normalization; DeepSeek parser/flow/diagnostics; Narrative repository, schema and migration
declarations; frontend request/credential/opt-in/diagnostic handling and cited test sources.

Verified current descriptions include:

- Narrative-first four-field explicit Analyze; one selected registered model; tool-free final
  text and integrity checks distinct from Legacy semantic validation.
- DeepSeek direct memo or conditional tool-free synthesis, completed-search quorum, partial-action
  exclusions, structural versus capture/query budgets and separate research/final request counts.
- Honest cutoff/provenance limitations, no hidden conversation and no failed research Run invention.
- Password input submission versus status-only reads, stored-slot preference, OpenAI read-only
  fallback and safe unavailable-storage behavior.
- Post-provider short ledger transaction, terminal outcomes, exact-text/hash/lineage, independent
  Narrative revision series and retained Legacy compatibility.
- C2 current integration status, preserved user/reviewer evidence distinctions, ADC awaiting review
  and 006B1 startup hold. Architecture is now organized by current components/lifecycle instead of
  requiring the reader to resolve R01–R06 overrides.

## 4. Limits and evidence attribution

No pytest, browser, Uvicorn, migration, paid provider, Ruff or mypy execution was performed in this
review. The contract makes those repeat runtime gates unnecessary for unchanged runtime code.
No new provider availability, Windows execution, financial/strategy validity or user-local runtime
identity is claimed.

The Mermaid check is static inspection of the actual simple flowchart grammar/branch semantics,
not execution of a Mermaid rendering engine or visual-layout certification. The implementer
disclosed the same limit; it is not an additional finding under this contract.

The source-link count verifies file/line existence; semantic support was assessed separately for
key architecture claims. The F01 issue illustrates why link validity alone is not full traceability.

## 5. Disposition and next handoff

Architecture/content and docs-only preservation pass. There is **one small traceability correction**,
with no Critical/Major finding and no runtime remediation request.

Do not merge this exact implementation yet. Request a focused correction of ADC-001-F01 on the
existing ADC task branch, preserve this independent review and historical reports, and return the
new exact SHA. Focused re-review needs only the corrected references, documentation links and
protected-file diff; it does not require another full architecture/runtime review.

This review does not integrate ADC, update authority or start 006B1. After focused closure and
separately authorized integration, issue a new 006B1 exact-baseline handoff preserving the original
contract's bounded archival/versioning/offline-read scope.
