# TASK-006B-Q closeout and TASK-006C-Q-F1 handoff — 2026-09-21

Owner-approved product decision. This record changes the forward task sequence; it does not
rewrite research evidence or integrate this branch into the product authority.

## Exact basis and decision

Product authority remains `roadmap/no-live-trading` at
`8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`.
R05 exact reviewed head is `7487cf57161a834d9100f983bab9d8534a1c0488`, with pre-result freeze
`b10e87cbb324442d1fc744d5fa94522802f870c1`, contract
`0d8ca48b046325c4d03a1716c806d42a333153ec`, and corrected R04 baseline
`c4e21a0204cf6cdd7bb139584b02f01792a49f13`.

The [formal independent R05 review](../reviews/TASK_006B_Q_R05_INDEPENDENT_REVIEW.md) is **PASS**,
with Critical 0 / Major 0 / Minor 0. Its independently executed checks are separately attributed
from the implementer's historical execution. No result-changing defect requires remediation.

**006B-Q: REVIEWED / CLOSED AS REFERENCE RESEARCH.** The research workflow is formally closed.
Do not initiate R06. Expanding the equity sample or proving full market applicability is no
longer a prerequisite to starting the bounded 006C-Q framework work.

The R05 disposition **RECOMMEND_CROSS_SAMPLE_ONLY** remains exactly as recorded in the
[historical report](../evidence/TASK_006B_Q/research-05/REPORT.md). It is retained as an optional
future validation recommendation, not a blocker and not a market-validity PASS. The Owner has
chosen an engineering foundation despite the disclosed research limits; the research conclusion
itself has not changed.

## Approved reference and experimental roles

B0, corrected R04 `PROPOSED_SEMANTICS:R04-CALENDAR-LOCAL-1`, is the first stable **reference
structure plugin**. Stable here refers to a frozen, reproducible engineering reference, not a
final or uniquely correct definition of market structure. The old accepted 006B runtime is not
replaced by this documentation decision.

A1, `PROPOSED_SEMANTICS:R05-NO-PRIOR-RAW-VETO-4SUPPORT-1`, remains an **experimental plugin,
disabled by default**. Running it requires explicit plugin/version selection and explicit
experimental permission. Event-count growth cannot promote it to the default. Each plugin keeps
its own semantic version and research lineage; old results always retain the original binding.

Neither B0 nor A1 is adopted as a profitable strategy, final Swing/Pivot truth, a trading
recommendation or a complete market model. The first engineering milestone requires neither
profitability proof, parameter optimization, all-market validation nor final strategy selection.

## Framework authorization

**006C-Q-F1: AUTHORIZED / CONTRACT FROZEN / IMPLEMENTATION NOT STARTED.**
The [versioned framework foundation contract](../../prompts/tasks/TASK-006C-Q-F1_VERSIONED_QUANT_EVENT_FRAMEWORK_FOUNDATION.md)
is **OWNER-APPROVED / READY FOR IMPLEMENTATION**. It authorizes the future bounded engineering
foundation: replaceable versioned structure/event protocols, immutable results/evidence,
deterministic identities, explicit registry selection and tests. It does not assert that the
006C-Q Event Engine or any formal event strategy is complete.

Formal Breakout, Failed Break, Retest, Transition, Trigger and Follow-through semantics belong
to later independent versioned plugin contracts. A test-only event fixture may prove an interface;
it is never a production strategy. A composition layer may bind plugins but cannot make one
specific strategy the hardcoded system core. Future strategies can be added or replaced without
rewriting the framework or reinterpreting historical results.

This authorization does not authorize Setup, Risk, Advisory, Paper, backtesting, Dashboard/API
integration, database changes, PAQS-E or Narrative/Analyze changes, 007D, new equity research,
market rankings or parameter optimization. The product permanently remains read-only: no
brokerage account, live trading, order capability or automatic trading.

## Preserved limits and history

Strict historical confirmation and broad market applicability remain **INCOMPLETE**. AVGO is
development data only, current-QFQ/PARTIAL with unknown legitimate historical availability;
all 300 strict AS_OF evaluations are insufficient. M30 has 26 additional insufficient
observational cutoffs. No independent equities or real HK validation were added. The nonminimal
quartet dependency, missing calendar coverage, repeated-kind output and dense alternating
chains remain limitations. Synthetic tests do not fill market-evidence gaps.

Original reports, contracts, frozen plans, source/test files and evidence keep their original
Git mode/type/blob identities and bytes, including historical wording such as “等待独立审查”.
Current status is supplied by this decision and the new review, not by editing the past.
The six current status documents may be minimally synchronized to this decision.

## Handoff validation

The docs-only handoff checks passed: all 201 relative links in the nine delivery documents
resolve, including local Markdown anchors; all six current documents carry the same status
and limitations; `git diff --check` is clean. No Mermaid block was added or changed.
Of the 693 objects tracked at exact R05, only the six explicitly permitted current documents
change. The other 687 retain their Git mode/type/blob identities, including all historical
evidence and frozen objects. Product source, tests, migrations, dependencies and resources
remain unchanged. The independent review records the executed research checks; this handoff
does not claim a new full-product regression run or actual Linux execution.

## Delivery and stop

This handoff descends from exact R05 in an isolated worktree. Only normal push of
`integration/006b-q-closeout-006c-q-f1-handoff` is authorized. Do not force-push, merge or update
`roadmap/no-live-trading`, or modify another remote branch. The fixed delivery SHA is read back
after all docs-only commits; the final delivery message supplies that SHA and pinned document
links rather than inventing a self-referential commit value here.

The current run ends after independent review, this closeout, contract freeze, documentation
validation and delivery readback. It must not begin F1 implementation. A later implementation
run consumes the exact verified handoff SHA and this frozen contract in its own isolated branch.
