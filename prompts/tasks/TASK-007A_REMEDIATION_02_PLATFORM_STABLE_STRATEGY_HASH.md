# TASK-007A REMEDIATION 02 — Platform-Stable Strategy/Prompt Byte Identity

Status: **APPROVED FOCUSED REMEDIATION CONTRACT**

Repository: `ahhhhzzz/ai-infra-quant`

Task branch: `task/007a-paqs-e-runtime-openai-strategy-port`

Original authoritative base: `6218c69bfc8202d6649e7ab01a2bd20fd585cdd5`

Parent TASK-007A Contract: `prompts/tasks/TASK-007A_PAQS_E_RUNTIME_STRUCTURED_OUTPUT_OPENAI_STRATEGY_PORT.md`

Parent Contract commit: `b74712b8828518d9b507e4bdbf9c43084c8129d3`

Remediation 01 Contract: `prompts/tasks/TASK-007A_REMEDIATION_01_RUNTIME_CONTRACT_GUARDRAILS.md`

Remediation 01 Contract commit: `d17e60f8ba014d6324965be88bc5606cdbe021a4`

Final SHA independently re-reviewed before Work review: `5acd725148bb006a639bf7aceb187b8089418adf`

Work independent final review verdict on that exact SHA: **NEEDS REVISION**

This remediation is deliberately narrow. It fixes one independently verified cross-platform exact-byte identity defect. It does not alter PAQS-E strategy semantics, runtime reasoning behavior, OpenAI adapter behavior, I/O schema/enums, validation semantics, TASK-007B/007C scope, persistence, historical replay, PAQS-Q, or broker boundaries.

---

## 1. Verified finding — authoritative strategy SHA assertion is checkout-line-ending dependent

### Evidence

The TASK-007A strategy loader correctly loads repository-relative Markdown with `read_bytes()` and computes SHA-256 over the exact bytes loaded.

The committed focused test then asserts one fixed SHA-256 for the accepted default strategy file:

`docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md`

Authoritative Git blob identity remains:

`5e27d45c38fbd9ad4ab49e05df4a5158b3469b73`

At reviewed SHA `5acd725148bb006a639bf7aceb187b8089418adf`, the test hard-codes:

`0a29f83256cdb21c64e9dfe90e037dddca399ff407d2cd23167f5f504f612ae8`

The repository has no tracked `.gitattributes` file at that reviewed SHA, so checkout line-ending behavior is not fixed by the repository.

Work independently reproduced that the exact LF bytes stored by GitHub hash to:

`73bed86ffef402d3d1e5eff855aaa2cc4bebf1ca1aafa33500c8839f63c16f82`

and that the currently asserted `0a29f...` value corresponds to a CRLF-converted checkout.

Independent Product review confirmed the structural defect: the exact-byte loader/test contract is real, the fixed test value is checkout-sensitive, and no repository line-ending policy currently stabilizes the hashed resource bytes.

Therefore the same accepted Git commit can pass on one checkout convention and fail on another, violating TASK-007A's exact-byte strategy identity and focused/full validation gates.

---

## 2. Required remediation

Establish a repository-controlled, platform-stable byte policy for the exact resources whose content SHA-256 is used as PAQS-E runtime identity.

### 2.1 Add narrow tracked `.gitattributes`

Add a repository-root `.gitattributes` file with explicit LF checkout/normalization for at least these hashed runtime resources:

```text
docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md text eol=lf
src/ai_infra_quant/resources/paqs_e/runtime_prompt_v1.md text eol=lf
```

A similarly narrow LF rule for `src/ai_infra_quant/resources/paqs_e/strategy_registry.json` is allowed if useful, but do not introduce broad repository-wide renormalization in this remediation.

Do not change the semantic content of the accepted PAQS-E Master Spec or runtime prompt merely to satisfy line endings.

### 2.2 Correct the authoritative default-strategy SHA assertion

Update the focused test so the accepted default strategy exact-byte SHA-256 is the canonical LF/GitHub-byte value:

`73bed86ffef402d3d1e5eff855aaa2cc4bebf1ca1aafa33500c8839f63c16f82`

Before committing, independently recompute the SHA-256 from the Git object / index-normalized LF bytes rather than trusting only the existing Windows working-tree file. If the recomputed Git-object hash does not equal the value above, stop and report the discrepancy instead of guessing.

Preserve the existing separate test that proves the loader hashes the actual bytes and changes identity when content changes.

### 2.3 Preserve exact-byte runtime behavior

Do not replace byte hashing with newline-insensitive or text-normalized hashing inside the loader.

The runtime identity must continue to mean:

```text
SHA-256(exact UTF-8 bytes actually loaded and supplied as the strategy/prompt package)
```

The remediation makes those tracked authoritative resource bytes stable across normal Git checkouts; it must not weaken the exact-byte audit model.

### 2.4 Clean-checkout verification

Validation must include evidence that the result is not dependent on the developer's pre-existing Windows CRLF working tree.

At minimum verify from Git/index/object content and, where feasible, a clean checkout/worktree that:

- the strategy file is checked out as LF under repository attributes;
- its exact UTF-8 SHA-256 is `73bed86ffef402d3d1e5eff855aaa2cc4bebf1ca1aafa33500c8839f63c16f82`;
- the focused test passes with the clean LF checkout;
- normal Windows `core.autocrlf` behavior cannot silently convert the two explicitly governed hashed resources to CRLF.

Do not require a paid/live OpenAI call.

---

## 3. Scope and protected boundaries

Preserve all accepted TASK-007A and Remediation 01 behavior, including:

- immutable Snapshot-bound reasoning request;
- As-Of-safe auxiliary context;
- exact v1 runtime policy identifiers;
- strict output schema and exact enums;
- 1–4 Key Level contract;
- Trigger/Follow-through separation;
- short advisory vs short execution authorization;
- deterministic Decimal RR validation;
- configured minimum RR behavior for READY vs non-action states;
- Strategy Markdown registry/loader separation from runtime prompt;
- provider-neutral reasoning port;
- OpenAI Responses API adapter;
- exact caller model ID;
- `store=false`;
- no tools/conversation/background/previous-response state;
- server-side-only API-key secrecy;
- no Analyze endpoint;
- no Decision Ledger or other persistence/migrations;
- no Dashboard Analyze UI;
- no historical replay implementation;
- no PAQS-Q changes;
- no broker/account/order/write capability.

Do not change accepted PAQS-E research semantics.

Do not modify:

- `docs/phases/PHASE_1_PLAN.md`
- `src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py`
- immutable Phase 1 review evidence.

If `phase1_remediation_commit.txt` exists locally, leave it untracked, untouched, unstaged, and uncommitted.

---

## 4. Expected bounded changed files

Prefer only:

```text
.gitattributes
tests/unit/test_paqs_e_runtime.py
```

A minimal update to `docs/engineering/PAQS_ENGINEERING_GUIDE.md` is allowed only if needed to document the LF/exact-byte identity policy.

Production runtime/adapter/domain code should not need changes. If Codex believes production code must change, stop and explain why before broadening scope.

Do not renormalize unrelated files.

---

## 5. Required tests and validation

Run at minimum:

- focused TASK-007A/config/architecture suite;
- full pytest suite;
- Ruff check;
- Ruff format verification;
- mypy;
- startup/health/OpenAPI/fresh SQLite migration regression where feasible.

Additionally prove:

1. Git/index/object SHA-256 for the accepted Master Spec exact LF bytes equals `73bed86ffef402d3d1e5eff855aaa2cc4bebf1ca1aafa33500c8839f63c16f82`.
2. The default-strategy focused test asserts that value and passes.
3. `.gitattributes` explicitly fixes LF for the strategy and runtime-prompt hashed resources.
4. No semantic diff exists in `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md` or `src/ai_infra_quant/resources/paqs_e/runtime_prompt_v1.md` relative to reviewed SHA `5acd725148bb006a639bf7aceb187b8089418adf`.
5. No TASK-007B/007C/persistence/broker scope appears.

The expected PostgreSQL environment-dependent skip remains acceptable if `PHASE1_POSTGRESQL_TEST_URL` is not configured.

---

## 6. Git and stop condition

Continue on the same task branch:

`task/007a-paqs-e-runtime-openai-strategy-port`

This Remediation 02 Contract is based directly on Work-reviewed SHA:

`5acd725148bb006a639bf7aceb187b8089418adf`

Use targeted staging only.

Commit and push only the same task branch.

Do not merge `roadmap/no-live-trading`.

Do not start TASK-007B or TASK-007C.

Stop after remediation for independent re-review.

Final report must include:

- Remediation 02 Contract SHA;
- pre-remediation SHA `5acd725148bb006a639bf7aceb187b8089418adf`;
- final remediation HEAD;
- exact changed files;
- exact `.gitattributes` rules added;
- Git-object/index-normalized strategy SHA-256 evidence;
- focused/full validation results;
- clean-checkout or equivalent platform-stability evidence;
- confirmation strategy/runtime-prompt semantic bytes remain otherwise unchanged;
- confirmation protected files remained unchanged;
- confirmation no scope leakage occurred;
- push verification;
- unresolved issues, if any.

**End — TASK-007A REMEDIATION 02**