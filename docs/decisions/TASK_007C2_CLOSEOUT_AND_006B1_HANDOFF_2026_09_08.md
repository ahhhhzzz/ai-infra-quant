# TASK-007C2 closeout and TASK-006B1 handoff — 2026-09-08

## Decision

TASK-007C2 is closed for the approved UI-cleanup scope. Integrate the independently reviewed implementation into `roadmap/no-live-trading` by fast-forward, retaining its review and this decision. The user reported successful acceptance and subsequently instructed “进行下一步”, authorizing this handoff and preparation of TASK-006B1.

This is a decision-support product only. The next task is local market-data storage and replay foundations; no real trading, brokerage-account connection, real-position import, order route, or autonomous execution is approved.

## Exact evidence and limits

- Previous authority: `2cc4eeea3cc31d4fd1f1a4e9c1fbec237f82a2c4`.
- TASK-007C2 implementation: `d2d25efc79d2560a7ed09895c7dd7a2c1724aee9`.
- Independent review commit: `2fc8105a77cf0adf5946aeaac0a148ae20e47fc5`; see [independent review](../reviews/TASK_007C2_INDEPENDENT_REVIEW.md).
- Review disposition: CODE / CONTRACT REVIEW PASS; zero Critical, Major, or Minor findings.
- Independently reproduced: 1234 passed, 7 skipped, 1 warning in non-browser coverage; Ruff, formatting, Windows-target mypy, Uvicorn and read-only HTTP smoke checks passed.
- Implementer reported 1350 passed, 1 skipped, 1 warning and 110 real Chromium browser cases passing. These are implementer results, not a second independently reproduced browser run.
- Independent browser execution was blocked by the environment's Playwright driver permission error. Eight submitted synthetic screenshots were inspected; that is visual evidence, not a replacement browser execution result.
- The user reported successful UI acceptance. Their accompanying PowerShell status showed `task/007c1-paqs-e-multi-model-web-research`, with no runtime commit SHA. Therefore the user's exact local runtime version is not independently confirmed as the C2 implementation. Do not rewrite this as user verification of the exact C2 SHA.
- The untracked `phase1_remediation_commit.txt` is unrelated local material. This handoff neither commits nor deletes it.

## Delivered behavior

The API credential modal has a scoped, usable layout and actions. The historical local-administration section and its dedicated frontend requests have been removed. The primary watchlist, chart, explicit Analyze workflow, Narrative history, and Research toggle remain in scope as before.

Removal of the old section is a frontend cleanup; it does not mean deleting historical database records, removing portfolio/accounting core code, or enabling any brokerage function. Existing databases and migrations were not changed by C2.

The earlier implementation report and contract remain historical records of the pre-integration state. This decision supersedes their “not merged / waiting for review” status only.

## TASK-006B1 handoff

Prepare a new task branch from this integrated baseline and a formal contract at:

`prompts/tasks/TASK-006B1_LOCAL_MARKET_DATA_STORE_REPLAY_FOUNDATION.md`

The historical planning node at `roadmap/task-006b1-local-market-data-store-staging` / `fe1e9497e62f1f9b48ba42c2e59e53a0c31989d1`, file `docs/roadmap/TASK-006B1_LOCAL_MARKET_DATA_STORE_REPLAY_FOUNDATION.md`, is background only. Do not merge that old branch or restore its old PAQS-Q task ordering.

Approved direction:

1. Explicitly archive legitimately obtained, completed D1/M1 canonical market facts and the calendar/provenance necessary to interpret them.
2. Retain immutable observations and corrected data versions. Never silently overwrite an older capture when the provider revises adjusted history.
3. Read and reconstruct saved captures entirely offline. Never mix a saved capture with newly fetched data.
4. Keep the accepted live workbench and Analyze behavior unchanged in this first foundation task. Replay is by saved observation; this is not strict historical point-in-time adjustment, a backtest engine, historical LLM evaluation, or a profitability claim.
5. Add only the bounded, additive persistence and minimal explicit archive UI/API specified by the new contract. No automatic polling/archive jobs, paid model calls, or trading scope.

TASK-006B1 implementation must be reviewed separately and is not authorized for automatic merge merely by completing this handoff.
