# TASK-006B-Q F01/F02 focused remediation contract

Authority: owner instruction, 2026-09-09. Status: AUTHORIZED; independent focused re-review required.
This additive contract records the owner instruction before implementation. It does not amend the
original strategy profile, universe or immutable original task contract.

- Repository: `ahhhhzzz/ai-infra-quant`.
- Only task branch: `task/006b-q-structure-formalization`.
- Exact remediation start: `a29d2d6e0195ed4509cfa8daa9223a41c3d6fcf0`.
- Authority: `roadmap/no-live-trading`, `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`.
- Independent review: `review/006b-q-independent`, `e4bf4cb6092e48c98732bd7d355d31affbf8a332`.
- Read review report `docs/reviews/TASK_006B_Q_INDEPENDENT_REVIEW.md` and
  `docs/reviews/evidence/task006b_q_reproducers.py` directly at that exact review commit.
- Original contract: `prompts/tasks/TASK-006B-Q_STRUCTURE_FORMALIZATION_AND_STABILITY.md`.

## Preconditions verified before this file

Fetch and GitHub ls-remote confirm exact task/start, authority and review SHAs above. Review parent
is the start SHA and contains only the two review evidence files. Task/authority merge base is the
authority SHA. Existing isolated task worktree is clean and stays on the original task branch.
No unknown task commits, resets, force pushes or review merges. Other worktrees remain untouched.
AGENTS, current governance and original contract reviewed; governance bytes match the already-read
unchanged authority baseline. Historical Phase 1 instructions do not restart that accepted phase.

## F01 — per-observation quality

Validate the coverage vocabulary and specify consistency between individual and aggregate quality.
Invalid/contradictory input must fail conservatively, never COMPLETE/BULL_TREND. Legitimate
PARTIAL/UNKNOWN must not upgrade automatically. Cover public evaluate and JSON wire paths.
Filter future/unavailable observations before interpreting irrelevant payloads. Do not relabel
fixtures in bulk to hide failures.

## F02 — versioned boundary experiments

Keep original versions. OLD must equal independent evaluate at the old cutoff. Declare OLD,
RIGHT, LEFT and BOTH version-availability rules. Later revisions cannot enter old-cutoff arms.
Recognize revision/delayed-information effects separately, or mark attribution unresolved; never
mislabel them pure left expiry. Cover later revisions, delayed availability, missing old versions
and ordinary no-revision input. Check completion and availability of every input/evidence record
of every arm, not only current Pivot completion. Unknown observational availability stays explicit.
The review reproducer asserts old defects and is not the corrected acceptance oracle; preserve it.

## Scope and preservation

Allowed existing paths: `tools/research/paqs_q/`, `tests/research/paqs_q/`,
`docs/research/PAQS_Q_STRUCTURE_MATH_CANDIDATE_V1.md`. New contract/report/validation evidence only
under `docs/evidence/TASK_006B_Q/remediation-01/`. Preserve original contract/report/diagnostics,
frozen profile/universe, review evidence, src, existing business tests, dependencies/configuration,
migrations and PAQS-E. Do not adjust ATR, Pivot, windows, Zones, Range or Regime strategy rules.
No enlarged universe, OpenD historical quota, network market acquisition, product wiring or 006C-Q.
User database is read-only; do not overwrite original evidence with rerun commands.

## Validation and delivery

Run all research tests and the same 59 structure/input/API/boundary regressions, Ruff, format,
strict mypy (including Windows target), diff and protected mode/type/blob checks. Retain original
diagnostic evidence; produce same-input before/after comparison and explain changes. Real-market
gate remains INCOMPLETE; fixing two defects is not structural robustness or semantic acceptance.

The owner authorizes local commits and normal push only to the task branch. Read back exact final
GitHub SHA and report. Report F01/F02 changes, results and remaining limits. No merge, force push,
authority change, product adoption or successor task. Stop for independent focused re-review.
