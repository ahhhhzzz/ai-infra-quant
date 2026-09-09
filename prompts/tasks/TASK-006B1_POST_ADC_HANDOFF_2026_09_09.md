# TASK-006B1 — Post-ADC exact-baseline handoff

Issued: 2026-09-09
Status: **APPROVED TO IMPLEMENT — prior startup hold lifted for this handoff**
Task branch: `task/006b1-local-market-data-store-replay`
Repository: `ahhhhzzz/ai-infra-quant`

## 1. Read this addendum with the original contract

Original scope contract:
[TASK-006B1_LOCAL_MARKET_DATA_STORE_REPLAY_FOUNDATION.md](TASK-006B1_LOCAL_MARKET_DATA_STORE_REPLAY_FOUNDATION.md)
at original publication `d2bc397612a32adb2b5f78fec3ec894b3eacdb38`.

That file remains byte-identical. All of its functional scope, persistence/versioning/time rules,
file restrictions, validation obligations and stop conditions remain in force unless a sequencing
or baseline statement is expressly replaced below.

The user instructed “下一步” after ADC-001's focused PASS, authorizing its integration and this
new 006B1 handoff. ADC-001 is closed/integrated; no further ADC implementation or review is required
as a prerequisite to starting this task. This is not authorization to merge 006B1 automatically.

[ADC closeout and resumption decision](../../docs/decisions/TASK_ADC_001_CLOSEOUT_AND_006B1_RESUMPTION_2026_09_09.md)
and [focused PASS](../../docs/reviews/TASK_ADC_001_F01_FOCUSED_RE_REVIEW.md) contain the evidence.

## 2. Exact replacement baseline and topology

| Reference | Fixed value |
|---|---|
| Current authoritative branch | `roadmap/no-live-trading` |
| Integrated ADC authority / implementation baseline | `02326a3bb19c2a89352d765f5331670b5f3f466d` |
| Accepted ADC implementation | `66a3ca7bbff258665b25e5ab17231138bf3cc49f` |
| Focused independent review | `50540f3eafa1ebcf58cc1938f666934157d79c43` |
| Prior 006B1 task HEAD with original contract and hold record | `9767554a4bca8c4ea29a8af93ec7f4f3e0f08748` |
| Prepared normal merge of prior task HEAD + current authority | `3b1685ac3f5e491114bba5945786d56b291fb422` |
| Current runtime code lineage | `d2d25efc79d2560a7ed09895c7dd7a2c1724aee9`; docs-only ADC adds no runtime changes |
| Existing schema head | `0003_task007c1_narrative_ledger` |

This handoff publication is the sole direct child of the prepared merge and adds only this file.
Its full resulting SHA is supplied by the startup prompt, not self-embedded in the file.

The prepared merge's ordered parents are prior task HEAD 9767554... and current authority 02326a3bb19c2a89352d765f5331670b5f3f466d.
Its tree is the normal Git merge tree: current authority plus the unchanged original 006B1 contract
and historical hold file. The task branch therefore retains its history without reset/rebase/force.
The merge base with current authority is exactly 02326a3bb19c2a89352d765f5331670b5f3f466d.

This section replaces the original contract's old f78894b... starting baseline and its old
single-contract-child topology prerequisite. Do not switch back to the old branch tip or try to
recreate those old conditions.

## 3. Supersession of the startup hold

The earlier `TASK-006B1_HOLD_FOR_ADC_001_2026_09_09.md` and ADC sequencing decision are immutable
historical records. Their hold is fulfilled/superseded by the integrated ADC closeout and this
handoff. Their “do not start” wording is no longer the current instruction for this exact baseline.
The old chat startup prompt remains obsolete; use the newly published handoff SHA.

Current documentation reports ADC-001 as reviewed/closed/integrated and 006B1 as authorized next
but not implemented. Do not invent a missing approval gate, re-open accepted ADC work, or repeat
full ADC/007C1/007C2 reviews before ordinary implementation.

## 4. Start procedure and boundaries

1. Fetch and read back authority, task branch, handoff commit and parents. Verify the prepared merge
   and original-contract/hold blobs, exact merge base and source identity.
2. Read AGENTS.md, current governing documents, the entire original scope contract and this addendum.
   Use the consolidated ARCHITECTURE.md; historical instructions remain historical.
3. Work from the existing task branch's published handoff HEAD in a clean isolated worktree/checkout.
   Preserve other worktrees, untracked files (including phase1_remediation_commit.txt) and user
   databases. No reset, automatic stash/clean, unrelated cherry-pick or branch-history rewrite.
4. If there are newer upstream commits or pre-existing task implementation changes, inspect and
   report the actual delta; do not overwrite them or silently pretend this exact starting SHA still
   matches. Resolve routine compatible implementation choices without unnecessary confirmation.
5. State planned concrete files/schema, then complete the original bounded implementation and
   validation. No extra ADC integration step is required: authority is already integrated.

The implementation remains explicit capture of completed D1/M1 and calendar/provenance; immutable
capture membership and content versions; honest partial/error coverage; persistence across restart;
provider-free saved-capture reads; additive 0004; bounded API and minimal archive UI.

Keep current live refresh, charts and Analyze snapshot behavior unchanged. Do not turn this into
automatic capture, silent cache fallback, cross-capture adjusted-history stitching, historical
Analyze, strict arbitrary AsOf/GoldSet evaluation, PAQS-Q work or a trading/account feature.

The original provider-neutral/Decimal/UTC rules and tested migration/data-preservation requirements
apply. No paid model calls are required for this task. Normal implementation validation must not be
confused with the docs-only checks used for ADC.

The contract and this addendum remain unchanged during implementation. Current status documentation
should retain ADC's closed/integrated state and describe 006B1 as implemented/pending review only
when that is true. Preserve original reports/reviews/closeouts; write the new 006B1 implementation
report in its original approved path.

## 5. Authorized delivery and stop

Complete the implementation, required tests/static checks/browser/Uvicorn evidence and original
report. Push only `task/006b1-local-market-data-store-replay`, with no force. Return final exact
SHA, validation results and material environment limits; read back GitHub to verify the pushed
test object.

Do not update authority, merge 006B1, begin later tasks or claim independent acceptance. Stop for
independent review. This handoff publishes no 006B1 runtime implementation itself.
