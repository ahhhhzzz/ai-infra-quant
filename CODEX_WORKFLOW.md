# Codex execution workflow

## Recommended mode

- Phase 0 architecture/specification: GPT-5.6 Sol, Extra High, Standard speed.
- Phase 1/2 implementation: GPT-5.6 Sol, High, Standard speed.
- Strategy contracts, Decimal accounting, evidence integrity and no-lookahead validation: Extra High when needed.
- Basic CRUD/CSS/docs: Medium or High.

## Current execution entrypoint

Read `docs/ROADMAP.md`, `docs/MASTER_SPEC.md`, the architecture/strategy specs and the current
committed Task Contract. The setup/Phase 0 examples below are historical onboarding instructions;
do not restart completed phases or treat old prompts as current implementation authority.

TASK-007B independent review PASS applies only to `7785cdeeacb14f0762f6104ed99f01b5e76d1dd3`; evidence: `docs/reviews/TASK_007B_INDEPENDENT_REVIEW.md`.
Verify authoritative integration separately. The user-authorized next task is `prompts/tasks/TASK-007C_PAQS_E_USER_DASHBOARD.md`,
which remains unimplemented and starts only after its own contract commit and prerequisites.
R20 product adoption is governed by `docs/decisions/R20_PRODUCT_ADOPTION_2026_09_07.md`; `docs/research/R20_ADOPTION_PLAN_AND_CODEX_PROMPT_ZH.md` is historical planning context.

## Local repository setup on Windows PowerShell

```powershell
mkdir D:\PythonProjects\ai_infra_quant
cd D:\PythonProjects\ai_infra_quant
git init
```

Extract this package into the repository root so that `AGENTS.md`, `docs/`, and `prompts/` are visible.

Optional first local commit:

```powershell
git add AGENTS.md docs prompts CODEX_WORKFLOW.md
git commit -m "Add quant platform master specification"
```

Do not commit real `.env`, broker credentials, databases, logs, or account exports.

## Desktop/IDE flow

1. Open the repository folder in Codex/ChatGPT desktop or the Codex IDE extension.
2. Start a new coding/work chat attached to that folder.
3. Select GPT-5.6 Sol, Extra High reasoning, Standard speed for Phase 0.
4. Keep command/file permissions conservative. Phase 0 does not need network access or dependency installation.
5. Paste the entire contents of `prompts/00_PHASE_0_BOOTSTRAP.md`.
6. Let Codex inspect the repository and produce only design documents.
7. Review `git diff`, the generated architecture, schema, API contracts, strategy formulas, and unresolved decisions.
8. Do not send `APPROVE PHASE 1` until the design is acceptable.
9. After approval, paste `prompts/01_APPROVE_PHASE_1.md` in the same chat.
10. At phase completion, inspect the exact commands/tests and run an independent review using `prompts/REVIEW_CURRENT_PHASE.md` or Codex review mode.
11. Proceed one phase at a time. Never say “continue everything”.

## CLI flow

From the repository root:

```powershell
codex
```

Select the model/reasoning level in the interactive UI, then paste `prompts/00_PHASE_0_BOOTSTRAP.md`.

Useful workflow commands depend on the current Codex interface, but common actions include choosing model/reasoning, plan mode, review mode, starting a new chat, and resuming a prior session.

## When to use the same chat

Use the same chat from Phase 0 through the immediately following approved phase when context is healthy.

Start a new chat when:

- the conversation becomes very long,
- Codex repeats old assumptions,
- it starts violating the current phase boundary,
- you want an independent review.

In a new chat, paste `prompts/RESUME_IN_NEW_CHAT.md` first.

## Approval sequence

- Continue only the current authorized bounded task and preserve its accepted exact base/contract.
- Complete implementation and required tests, then independent review at the exact final SHA.
- Integrate only an accepted reviewed implementation; verify the actual authoritative branch SHA.
- Start the next task only with its own authorization and committed contract. TASK-007C already
  has user authorization; a passing predecessor alone does not authorize unrelated future modules.
- Futu remains independent quote-only market-data access. No trading adapter, brokerage-account
  observation or later live mode is part of this product; all real trading is manual outside it.
- An explicit task's push/branch instructions govern that task. Do not push unrelated branches,
  rewrite historical evidence, merge unreviewed work or implement umbrella TASK-006/TASK-007.
- Scope changes require concrete contract/governance updates before coding; a historical R20
  adoption prompt must not interrupt or replace an already running approved task.

## What to inspect after every phase

- `git status`
- `git diff --stat`
- changed-file list
- application startup result
- migration result
- pytest result
- lint result
- type-check result
- requirements-matrix changes
- unresolved blockers
- accidental secrets or local data in Git

## Avoid these instructions

Do not send vague prompts such as:

- “把全部做完”
- “继续下一步直到完成”
- “直接接实盘”
- “把所有报错都修完并上线”

Always name the phase, scope, acceptance tests, and stop condition.
