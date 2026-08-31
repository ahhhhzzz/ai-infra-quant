# Codex execution workflow

## Recommended mode

- Phase 0 architecture/specification: GPT-5.6 Sol, Extra High, Standard speed.
- Phase 1/2 implementation: GPT-5.6 Sol, High, Standard speed.
- Strategy formulas, accounting, backtest timing, broker state machine, live safety: Extra High when needed.
- Basic CRUD/CSS/docs: Medium or High.

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

- Phase 0 completes -> review -> `APPROVE PHASE 1`.
- Phase 1 completes -> independent review/fixes -> `APPROVE PHASE 2`.
- Continue the same pattern for each phase.
- Futu read-only comes before any trading adapter.
- Live mode requires a separate explicit authorization after the safety phase; completing code is not authorization to enable live trading.

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
