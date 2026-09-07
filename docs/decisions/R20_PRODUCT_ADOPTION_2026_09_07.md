# R20 Product Adoption and TASK-007C Handoff

Decision: `R20-ADOPT-001`  
Date: 2026-09-07  
Status: **APPROVED DIRECTION; TASK-007C IS THE ONLY NEW IMPLEMENTATION AUTHORIZATION**

## User request and current state

The user requested a complete personal quantitative decision workstation inspired by `555cute/r20-quantum-trader`, allowed reuse of its code, asked to preserve the ongoing Codex task, and subsequently requested that the plan and TASK-007C execution prompt be saved to this GitHub repository after TASK-007B delivery.

TASK-007B implementation `7785cdeeacb14f0762f6104ed99f01b5e76d1dd3` has independently passed source review and rerun verification. See [TASK-007B independent review](../reviews/TASK_007B_INDEPENDENT_REVIEW.md). The supplied Codex completion report explicitly stopped for review without merging; it was not itself independent acceptance.

The earlier complete [R20 adoption plan and planning prompt](../research/R20_ADOPTION_PLAN_AND_CODEX_PROMPT_ZH.md) is archived as a historical snapshot. Its old branch status, draft status, and planning-only prompt describe that earlier moment. They do not override this decision or the newly approved [TASK-007C implementation contract](https://github.com/ahhhhzzz/ai-infra-quant/blob/task/007c-paqs-e-user-dashboard/prompts/tasks/TASK-007C_PAQS_E_USER_DASHBOARD.md). The contract lives on `task/007c-paqs-e-user-dashboard`.

## Adopted product direction

AI Infra Quant remains a local, single-user US/HK decision-support product with PAQS-E as its primary analysis branch. R20 supplies product layout, interaction patterns, and individually reviewed reusable code; existing provider-neutral market data, immutable snapshots, validated PAQS-E runtime, and Decision Ledger remain the foundation.

For TASK-007C, retain HTML/JavaScript/CSS and the locally vendored Lightweight Charts library. Deliver a coherent workstation: watchlist → market charts → explicit model/registered-strategy selection → Analyze → structured reasoning → immutable Decision history and frozen evidence. Use a compact three-column desktop layout, responsive narrow layout, deep/light themes, truthful empty/error/loading states, and useful chart annotations.

Current Daily/1m market views remain distinct from the W1/D1/M30 evidence frozen for a selected Decision. Refreshing the market does not rewrite a Decision or initiate a model call. Conditional Holder Advisory is not a real-position fact. Missing data must never be replaced with synthetic production prices, fake performance, or simulated account values presented as real assets.

## Fixed upstream source and reuse controls

Reference repository: [555cute/r20-quantum-trader](https://github.com/555cute/r20-quantum-trader/tree/3840ef1af57c929c081fbe45087225cca1b508f1). Reviewed upstream commit: `3840ef1af57c929c081fbe45087225cca1b508f1`.

The reviewed upstream license is MIT with notice `Copyright (c) 2026 R20 Quantum Trader Team`. Any copied or adapted source must retain the applicable license/copyright and record source path, exact commit, local destination, and adaptation rationale. Third-party assets/dependencies require their own notices. No framework migration or new chart dependency is authorized in TASK-007C merely because upstream uses Vue/TypeScript and klinecharts.

The archived plan documents source-level security findings, including model-controlled shell dispatch, sensitive aggregate API exposure, credential/configuration handling, and synthetic fallback candles. These findings are bounded to the reviewed upstream commit and are not a claim that every future release is unsafe. Do not import the affected execution, account, admin, or fallback-data paths. This record adopts product ideas; it does not certify the upstream application for use with funds.

## Authorized now versus later

| Work package | Current authorization |
|---|---|
| TASK-007C workstation, manual Analyze, frozen evidence, history | Implement only under its dedicated approved contract after verifying the exact accepted base |
| Model configuration center and additional providers | Future bounded contract; 007C supports explicit existing OpenAI model ID and safe configuration readiness only |
| Prompt/strategy studio | Future contract; preserve immutable PAQS-E baseline and hard constraints |
| TASK-006B1 local market store and replay | Deferred; required before strict arbitrary historical As-Of evaluation claims |
| Paper portfolio, PaperFill, NAV and analytics | Dormant Phase 3 extension; no authorization from this record |
| Multi-model review and research improvement candidates | Separate later contract, same-snapshot evidence and explicit adoption of revisions |
| News, reports, notifications and maintenance | Separate later contracts; no hidden auxiliary context or autonomous analysis |
| TASK-007D | Retains its existing E/Q comparison meaning; do not reuse the identifier for a model council |

Future sequencing may be revised when its next bounded contract is approved. The archived feature list is not a request to implement the entire product in one task.

## Preserved boundary and handoff procedure

The authoritative phase model remains Phase 0–4. No broker-account access, real-account observation/import, real orders, broker writes, autonomous trading, execution workers, or live-position tracking is authorized. Real trades remain manual in the broker's official client. Server secrets stay out of the browser, repository, application ledger, error payloads, and logs.

Review and documentation preparation use an isolated source snapshot. Accepted 007B can then be fast-forward integrated, with the documentation record on its own branch, and TASK-007C created from the exact accepted documentation baseline. Never force-update a ref or rewrite the 007B task branch. Recheck remote refs immediately before updates to detect concurrent work.

Codex executing TASK-007C must use a separate worktree/checkout if another task's directory is active, verify the exact contract and base SHAs in its launch prompt, implement only that contract, test and push only the task branch, then stop for independent review. It must not merge itself or automatically continue to later work packages.
