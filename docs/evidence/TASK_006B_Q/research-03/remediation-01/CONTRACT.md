# TASK-006B-Q-R03-F01 — Frozen M2 state clarification

Status: **AUTHORIZED DOCS-ONLY FOCUSED REMEDIATION**, issued 2026-09-10 after owner instruction “下一步”.

Repository: `ahhhhzzz/ai-infra-quant`.
Only task branch: `task/006b-q-r03-confirmation-stability-contract`.
Exact remediation base: `7044bb1d3a4e9752bbad0417b753b706723d5b8b`.
Product authority remains `roadmap/no-live-trading` at
`8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`.
Independent review: `8338c2b61cd60dc5c1079a3648b66d9643b19031`,
[R03-F01](https://github.com/ahhhhzzz/ai-infra-quant/blob/8338c2b61cd60dc5c1079a3648b66d9643b19031/docs/reviews/TASK_006B_Q_R03_INDEPENDENT_REVIEW.md).

## 1. Read and preserve

Read AGENTS and the governing documents required there; the original R03 contract and the
pinned independent review, especially section 2. Reuse previously read governing documents
only after confirming unchanged Git blobs. Fetch and verify exact task ancestry and status.
Use an isolated worktree if necessary; preserve all other worktrees and untracked user files.
Read the review from its Git object or pinned GitHub URL without merging its branch.

Read the literal frozen [PLAN](../PLAN.md), final
[mathematical specification](../../../../research/PAQS_Q_CONFIRMATION_AND_ROLLING_STABILITY_R03.md),
`History`/`advance` in [models.py](../../../../../tools/research/paqs_q/r03/models.py),
and the original [report](../REPORT.md).

All **479** files present at the exact remediation base must retain mode/type/blob.
This includes the frozen PLAN, original/final mathematics and reports, all model/test code,
contracts, enumeration and witness evidence. This issued remediation contract is also immutable.

## 2. Required clarification

Frozen PLAN lines 49–50 say M2 state contains the entire supplied snapshot sequence.
The actual History retains records, latest cutoff, lineage hash and steps; complete earlier
snapshots are not retained. The final specification describes the implementation correctly.

Add a dated clarification that:

1. Links the exact frozen wording, reviewed code and final specification, with pinned commits.
2. Separates actual stored fields, conceptual historical dependencies and external replay inputs.
   Explain the initial History, ordered snapshot/cutoff schedule and exact rule/configuration
   needed to reproduce history, rather than claiming it can be recovered from the final hash.
3. States that full snapshot-sequence retention was not implemented. Explain whether the frozen
   wording overstated the intended state or the implementation departed from that requirement.
   Do not invent prior intent: if it cannot be established, state the literal discrepancy and
   the actual retained-state interpretation being documented now.
4. Gives the implementation's memory/work bound and clarifies lineage limitations: deterministic
   recomputation can compare a supplied sequence with a recorded hash; a hash is not the sequence,
   evidence availability certification, or proof that the historical inputs were true.
5. Explains why P2's explicit-history dependence, P6's append-only recognition records, actual
   recognition timestamps and all submitted witnesses/metrics are unaffected. Identify the
   changed documentation claim rather than asserting that the frozen text already matched.
6. Explicitly qualifies the original report's blanket statement that model definitions were
   not adjusted. The addendum is the later authoritative clarification for this state-retention
   discrepancy; original evidence and its chronology remain intact.

This contract authorizes documenting the actual reviewed model, not implementing full history
retention or changing algorithms. It does not adopt M1/M2 into PAQS-Q or alter the frozen plan.

## 3. Exact deliverables and validation

Add only these two files beside this contract:

- `M2_STATE_CLARIFICATION.md` — the complete clarification above.
- `REPORT.md` — a short Chinese remediation note linking the clarification, review and frozen
  evidence; exact base/final handoff information, changed files, checks and remaining limits.

The new report provides discovery without editing the old README/REPORT or frozen PLAN.
Do not edit code, tests, verifiers, dependencies, configuration, user data or database files.
Do not run acquisition, inspect credentials, implement a ledger, merge or start another task.

Verify all 479 base mode/type/blob identities and this contract, exact two-file addition scope,
relative links, pinned reference identities and `git diff --check`. Record actual results in
the new report. Use read-only Git checks; no verifier source changes or additional scripts are
needed. Runtime, research enumeration, full tests, Ruff and mypy reruns are not required for
these Markdown-only additions. Do not attribute old test results to this remediation run.

## 4. Delivery and focused review

Normal commits and push are authorized only to the existing R03 task branch. Never force-push,
update authority, merge the review branch or modify another checkout. Read back final GitHub
SHA, both new documents and the preserved PLAN identity. Leave R03-F01 as remediation completed
pending independent focused review; do not self-close the independent finding.

Stop after delivery. The follow-up review checks only R03-F01 and preservation unless new
evidence gives a concrete reason to broaden scope. Mathematical guarantees remain conditional,
real-market completeness INCOMPLETE, and product adoption/006C-Q NOT AUTHORIZED.
