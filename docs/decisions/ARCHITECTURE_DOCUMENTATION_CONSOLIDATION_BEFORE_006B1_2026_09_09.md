# Architecture / Documentation Consolidation before TASK-006B1

Date: 2026-09-09
Decision: user-directed sequencing correction; docs-only scope
Previous authoritative HEAD: `f78894bceb2900eff6e134bdf61f673309426355`

## User direction

Before TASK-006B1, complete **Architecture / Documentation Consolidation**.
The identified debt is documentation that lags the accepted implementation, not an authorization to restructure the modular monolith. The user explicitly requires docs-only work and no runtime changes.

## Current evidence

TASK-007C2 is reviewed, closed and integrated at the previous authority above. Its implementation is `d2d25efc79d2560a7ed09895c7dd7a2c1724aee9`; review and user-evidence limits remain in [the closeout](TASK_007C2_CLOSEOUT_AND_006B1_HANDOFF_2026_09_08.md).

Current ARCHITECTURE.md mixes historical 007A/B/C descriptions with appended C1 remediation sections. It already contains Narrative-first material, but the reader must resolve successive overrides. Current status paragraphs also still describe C2 as pending review. This calls for a coherent account of the accepted system, not a new runtime design.

## Approved order

1. **TASK-ADC-001 — Architecture / Documentation Consolidation**: document the actual accepted architecture, align current authority documents and clearly separate current behavior, retained legacy compatibility and deferred work.
2. Independently review the documentation and verify that all non-documentation files are byte-identical to the approved baseline; integrate only after the normal review/authorization handoff.
3. Reissue TASK-006B1's starting-baseline/handoff instructions against the resulting authority, then resume its implementation.

The original 006B1 contract at `d2bc397612a32adb2b5f78fec3ec894b3eacdb38` remains an immutable record of its approved functional scope. Its immediate-start instruction is **superseded / on hold**, including the previous chat startup prompt. This decision does not cancel its archival/versioning/offline-read requirements and does not authorize starting it during ADC-001.

At this decision's preparation, GitHub's 006B1 task branch still pointed to the contract-only commit above. Do not infer anything about unpushed local work. If work has already started locally, preserve it separately; do not merge it into ADC-001.

## Bounds

ADC-001 covers Narrative-first Analyze, current model selection and provider gateways, Windows Credential Manager, bounded optional research (including DeepSeek SEARCH → optional SYNTHESIS → final Narrative), immutable Narrative evidence, Research default OFF, current workbench and retained legacy boundaries.

No source, frontend, runtime prompt/strategy resource, model registry, credential implementation, database/migration, dependency, launcher, test or CI change is authorized. Source code is evidence to read, not a surface to edit. Finding a possible implementation defect permits recording it separately, not fixing it in this task or presenting desired behavior as already implemented.

Use `prompts/tasks/TASK-ADC-001_ARCHITECTURE_DOCUMENTATION_CONSOLIDATION.md` on `task/adc-001-architecture-documentation-consolidation` for the bounded implementation contract. The task title must not be “refactor” or “重构”.
