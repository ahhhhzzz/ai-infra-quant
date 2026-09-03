# PAQS-DOCS-002 — TASK-006B2 Final Closure + PAQS-E Runtime Semantic Authority Migration

Status: **APPROVED DOCS-ONLY MIGRATION**

Repository: `ahhhhzzz/ai-infra-quant`

Authoritative base branch: `roadmap/no-live-trading`

Authoritative base SHA: `5f996aebb012cc0884d912f6f3eb71c32e9fd627`

Migration branch: `roadmap/paqs-e-runtime-authority-006b2-closure`

This migration is documentation-only. It does not authorize product code, OpenAI integration, TASK-007A implementation, TASK-006B1, PAQS-Q implementation, persistence, Dashboard Analyze, or broker behavior.

## 1. Objective

Bring the authoritative GitHub documentation in line with two already-completed governance facts:

1. TASK-006B2 has passed independent post-remediation review at exact SHA `5f996aebb012cc0884d912f6f3eb71c32e9fd627` and is integrated on `roadmap/no-live-trading`.
2. The remediated PAQS-E Context-Free Master Spec has passed focused strategy re-review and is accepted as the primary **runtime semantic authority candidate** for future PAQS-E Task Contracts.

The migration must remove stale authoritative wording that still calls TASK-006B2 "NEXT PLANNED IMPLEMENTATION" or treats the older Naked Price Action Doctrine as the complete primary runtime semantic strategy authority.

## 2. Exact TASK-006B2 final acceptance facts

Record these facts without embellishment:

- Original authoritative base: `b35bb9ff62a7a88b8cc08a8af5278ea4ab5aca0c`
- Parent Contract: `5aba70d3737ebfaa868aa90d062e602067c38024`
- Amendment 01: `99e06a572eb1fbc6358cda443a8d6c6e41be4fb0`
- Reviewed implementation before remediation: `10692de359b5818c28a2e724a893b5b884e4c79e`
- Remediation 01 contract: `4d4c6b384f50e90da66dc4997af1c0cf93afcbdb`
- Final reviewed/integrated SHA: `5f996aebb012cc0884d912f6f3eb71c32e9fd627`
- Independent final verdict: `PASS`
- Deterministic validation independently confirmed at final SHA: `280 passed, 1 skipped`; focused TASK-006B2 `32 passed`; Ruff/mypy/startup/health/OpenAPI/fresh SQLite checks passed.
- Live OpenD remained an environmental limitation only: `127.0.0.1:11111` unavailable. Do not infer live evidence.

The accepted behavior includes:

- immutable provider-neutral Snapshot-on-Demand factual snapshot;
- W1/D1/M30 caps 156/500/200;
- W1 completed+COMPLETE only;
- D1 completed only;
- M30 completed+COMPLETE+REGULAR only;
- W1 PARTIAL/UNKNOWN machine-readable exclusion provenance;
- D1/M30 source evidence provenance;
- quote and market-state `reference_only`;
- nullable `provider_delay_seconds` factual provenance;
- canonical Decimal/UTC serialization and SHA-256 `snapshot_hash`;
- `created_at` and `snapshot_hash` excluded from hash payload;
- W1 nominal future interval geometry preserved and hashed but excluded from advancing Snapshot As-Of;
- no PAQS strategy conclusions, OpenAI/LLM, persistence/migration, Dashboard Analyze or broker behavior.

## 3. Independent review evidence file

Create:

`docs/reviews/TASK_006B2_INDEPENDENT_REVIEW.md`

It must be a concise immutable review record with:

- verdict `PASS`;
- reviewed exact SHA `5f996aebb012cc0884d912f6f3eb71c32e9fd627`;
- original base SHA;
- Parent Contract, Amendment 01 and Remediation 01 references;
- verified remediation semantics;
- verified contract boundaries and test evidence;
- environmental OpenD limitation clearly separate;
- explicit statement that PASS applies only to TASK-006B2 and does not authorize TASK-007A or other tasks.

Do not claim GitHub Actions evidence for TASK-006B2; none existed for the final SHA.

## 4. PAQS-E accepted research source migration

Source research branch:

`research/paqs-e-context-free-master-spec-zh`

Exact accepted research HEAD:

`6495e0d7aa4daac69e530eaa5cdce46d5ef52c0f`

Copy the following files from that exact research HEAD into this migration branch **without semantic rewriting**:

1. `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md`
2. `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_STRATEGY_REVIEW.md`
3. `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_REMEDIATION_SUMMARY.md`
4. `docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_FOCUSED_RE_REVIEW.md`

Preserve their contents exactly unless a path/header reference must be mechanically adjusted solely because the file is now present on the authoritative branch. Prefer byte-identical copying.

The focused re-review verdict is PASS. The Master Spec remains a research strategy specification and does not itself authorize implementation.

## 5. Authoritative PAQS-E semantic hierarchy update

Update `docs/ROADMAP.md` and `docs/REQUIREMENTS_MATRIX.md` so future Task Contracts use this hierarchy:

```text
docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md
    -> primary PAQS-E runtime semantic strategy authority candidate

PAQS_E_NAKED_PRICE_ACTION_DOCTRINE.md
    -> conceptual/doctrine foundation

PAQS v0.3.x
    -> historical guardrail / formalization / audit / terminology reference

PAQS-Q research
    -> separate deterministic/reference branch authority only when separately adopted
```

Important interpretation:

- "candidate" means accepted for bounded adoption by future Task Contracts; research files still do not directly authorize code.
- TASK-007A must explicitly adopt the Master Spec version/hash in its own approved Task Contract.
- PAQS-Q thresholds must not silently bind PAQS-E.

Do not rewrite the Master Spec back into the older doctrine hierarchy.

## 6. ROADMAP status corrections

Update `docs/ROADMAP.md` minimally but completely:

- add TASK-006B2 to completed Phase 2 increments;
- record final accepted/integrated SHA `5f996a...` and independent PASS;
- change the TASK-006B2 subsection from `NEXT PLANNED IMPLEMENTATION` to `COMPLETED / INTEGRATED` (or equivalent unambiguous wording);
- preserve its factual scope and no-strategy/no-LLM/no-persistence boundaries;
- identify `TASK-007A — PAQS-E Doctrine Runtime, Structured Output & OpenAI Provider Port` as the **next planned implementation** after TASK-006B2 final closure;
- update the recommended implementation order to show TASK-006B2 done;
- update the PAQS-E semantic authority hierarchy per Section 5;
- do not mark TASK-007A/B/C or TASK-006B1 implemented.

## 7. REQUIREMENTS_MATRIX status corrections

Update `docs/REQUIREMENTS_MATRIX.md` minimally:

- keep TASK-006B2-related rows IMPLEMENTED but strengthen evidence to include `docs/reviews/TASK_006B2_INDEPENDENT_REVIEW.md` and final SHA where appropriate;
- remove the obsolete final statement that says no TASK-006B2 Snapshot implementation exists;
- replace it with the accepted final TASK-006B2 implementation/review/integration status;
- update PAQSE-001 so the Context-Free Master Spec is the primary runtime semantic authority candidate, with the older Doctrine as conceptual foundation;
- update supporting PAQSE rows/evidence only where necessary for consistency;
- keep TASK-007A as PLANNED_TASK, not IMPLEMENTED;
- do not change Phase 1 accepted historical status.

Do not invent new probability/performance claims.

## 8. Scope exclusions

This migration must not modify:

- any file under `src/`;
- tests;
- database migrations;
- dependencies/pyproject;
- Dashboard/frontend behavior;
- OpenAI integration;
- API keys/config;
- PAQS-Q implementation;
- broker/account/order behavior;
- Phase 1 immutable review evidence.

Do not modify:

- `docs/phases/PHASE_1_PLAN.md`
- `src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py`

If `phase1_remediation_commit.txt` exists locally, leave it untracked/untouched/unstaged/uncommitted.

## 9. Expected changed files

The expected bounded set is:

- `docs/ROADMAP.md`
- `docs/REQUIREMENTS_MATRIX.md`
- `docs/reviews/TASK_006B2_INDEPENDENT_REVIEW.md`
- the four PAQS-E research files listed in Section 4
- this migration contract file already present on the branch

No other file should change unless required solely to repair a direct documentation link/reference; any extra file must be justified.

## 10. Validation

Before commit, verify:

- no `src/`, test, migration, pyproject or frontend file changed;
- copied PAQS-E research files match source research HEAD `6495e0d...` semantically/byte-for-byte where possible;
- Roadmap contains no stale statement that TASK-006B2 is the next planned implementation;
- Requirements Matrix contains no stale statement that TASK-006B2 is unimplemented;
- TASK-007A remains planned only;
- final docs consistently identify `5f996a...` as TASK-006B2 accepted SHA;
- permanent no-live-trading boundary remains unchanged.

## 11. Stop condition

Commit and push only:

`roadmap/paqs-e-runtime-authority-006b2-closure`

Do not merge into `roadmap/no-live-trading`.

Stop for independent review.

Do not create or implement TASK-007A.

Final report must include:

- base SHA;
- source research HEAD;
- migration contract SHA;
- final migration HEAD;
- exact changed files;
- exact TASK-006B2 closure wording/evidence;
- exact PAQS-E semantic hierarchy wording;
- validation that no code files changed;
- unresolved issues, if any.

**End — PAQS-DOCS-002**
