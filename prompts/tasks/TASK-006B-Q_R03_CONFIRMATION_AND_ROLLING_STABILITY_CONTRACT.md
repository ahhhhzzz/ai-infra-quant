# TASK-006B-Q-R03 — Confirmation and rolling stability mathematical contract

Status: **AUTHORIZED BOUNDED RESEARCH — mathematical specification, proofs/counterexamples and executable synthetic witnesses; no replacement-engine adoption.**

Owner instruction: “下一步”, after independent R02 review. Issued 2026-09-10.

Repository: `ahhhhzzz/ai-infra-quant`.
Only task branch: `task/006b-q-r03-confirmation-stability-contract`.
Exact development base: `ddb61c15f1aea026b26c116f35fa1e2b0b0d055a`.
Product authority remains `roadmap/no-live-trading` at
`8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`.
Independent R02 review: `c01c69d7f3a8b6cc21d0dd4f6773cf14308841e4`,
branch `review/006b-q-r02-independent`.

[Review](https://github.com/ahhhhzzz/ai-infra-quant/blob/c01c69d7f3a8b6cc21d0dd4f6773cf14308841e4/docs/reviews/TASK_006B_Q_R02_INDEPENDENT_REVIEW.md)
records research delivery PASS, H1 stable-replacement REJECT, real-market INCOMPLETE and
product adoption NOT AUTHORIZED. This authorizes the next research step; it does not merge
R02, adopt H1, close all of 006B-Q or start 006C-Q. A rejected candidate is not an outstanding
implementation defect that must be silently repaired before this task can begin.

## 1. Establish the exact baseline

Read AGENTS.md, ROADMAP, MASTER_SPEC, ARCHITECTURE, STRATEGY_SPEC, REQUIREMENTS_MATRIX and
the applicable phase plan. Read the original 006B-Q contract/math candidate, remediation-01
quality/time contract and report, R02 contract, frozen experiment plan/math, R02 report and
the exact independent R02 review above. In particular read:

- [Original mathematical candidate](../../docs/research/PAQS_Q_STRUCTURE_MATH_CANDIDATE_V1.md).
- [R02 candidate mathematics](../../docs/research/PAQS_Q_STRUCTURE_R02_CANDIDATES.md).
- [R02 report](../../docs/evidence/TASK_006B_Q/research-02/REPORT.md).
- [13-pivot rejection witness](../../docs/evidence/TASK_006B_Q/research-02/refined-causes/h1-rejection-counterexample.json).
- [Refined geometry causes](../../docs/evidence/TASK_006B_Q/research-02/refined-causes/h1-geometry-causes.json).
- [Reviewed quality/version selection](../../tools/research/paqs_q/engine.py),
  [temporal guards](../../tools/research/paqs_q/temporal.py) and
  [H1 implementation](../../tools/research/paqs_q/r02/engine.py).

Fetch exact commits; verify task ancestry, worktree status and remote authority before changes.
Preserve every unrelated checkout and untracked file, especially phase1_remediation_commit.txt.
Use a separate worktree if required. Do not merge review branches to obtain their reports;
read the pinned review through GitHub or the corresponding Git object.

The development base has 465 tracked files. Protect their mode/type/blob identities, including
all R02 code, tests, contracts, frozen documents and evidence. Also protect this issued contract.
Inherited product documents intentionally retain the integrated-product status; they are not
permission to modify runtime or a reason to restart prior accepted work.

## 2. Outcome required

Produce a concrete, mathematically specified recommendation for what PAQS-Q may call a
confirmed Pivot and what it may promise when a finite analysis window moves. Support the
recommendation with explicit assumptions, proof arguments and executable counterexamples.

Answer these questions before another full algorithm experiment:

1. Is confirmation a fact established using information available at a particular cutoff,
   a label recomputed inside the current window, or two explicitly distinct objects?
2. Which exact evidence makes an extreme admissible and confirms it? What happens under
   persistent two-way reversal ambiguity, equal extrema, gaps and insufficient information?
3. Which rolling stability properties can a proposed model establish, under what assumptions,
   and which requirements would need an explicit semantic amendment?
4. What single next experimental direction is recommended, with concrete acceptance and
   rejection oracles? If none is defensible, identify the smallest unresolved decision.

A prose-only discussion, renamed instability metrics, or another AVGO-tuned H2 is insufficient.
Conversely, do not claim a universal impossibility theorem merely because baseline and H1 fail.
This task may deliver a supported incompatibility result and a precise amendment proposal.
It must complete the analysis and witnesses before returning a decision request.

## 3. Allowed changes and execution boundary

Add files only under:

- `docs/research/PAQS_Q_CONFIRMATION_AND_ROLLING_STABILITY_R03.md` — proposed mathematical contract.
- `docs/evidence/TASK_006B_Q/research-03/` — plan, proof register, compact synthetic evidence,
  preservation/validation metadata, report and reproduction guide.
- `tools/research/paqs_q/r03/` — small pure witness generators/checkers and at most two
  miniature semantic models needed to test propositions.
- `tests/research/paqs_q/r03/` — independent hand oracles and property/counterexample checks.

Do not edit any existing tracked file or expand an old verifier's exceptions. No src, API/UI,
database/migration, dependency/configuration, E-strategy, archive/Analyze, Event, Setup/RR,
advisory or scanner implementation. No persisted Pivot ledger or runtime state service.
Existing pure research helpers may be imported read-only. No monkeypatching baseline/H1.

Research code may execute enough of a proposed rule to prove or falsify a proposition; it
must not grow into a complete replacement Structure Engine or market-parameter study.
If a stateful process is used as a mathematical comparator, keep it in-memory, explicitly
declare its initial state and lineage, and do not present it as a stateless bounded candidate.

This task needs no new market acquisition or user database access. OpenD history budget is
zero. Do not repeat the failed R02 data-acquisition attempts, inspect credentials, register
accounts or add services. Existing committed AVGO summaries may illustrate known results;
do not claim a raw-data rerun from their hashes. Additional market validation is a later
separate gate, not a prerequisite to completing these mathematical deliverables.

## 4. Definitions and proposed invariants

Use stable source observation references and exact Decimal/aware-UTC semantics. Start with
the reviewed per-cutoff information set `I_t`, which selects legitimately available versions
and excludes unfinished observations. Distinguish this from OBSERVATIONAL data with unknown
historical availability; F01/F02 remain hard boundaries, not amendable conveniences.

Define, with all indices and domains explicit:

- `B_t`: last N eligible observations selected from `I_t`; active subset `A_t` and warm subset.
- A current calculation `F_theta(B_t)` and any separately proposed history-dependent object.
- Extreme time, reversal-confirmation time, first actual emission/recognition time, source
  availability time and calculation time. Never backdate a newly recognized event to imply
  it was known when its historical extreme occurred.
- Pivot identity, price, kind and complete evidence dependencies, including ATR seed and
  earlier state if they causally affect confirmation. Two visible endpoint refs alone must
  not conceal dependence on older warm observations.
- Candidate/admissible extreme, ambiguous candidate, confirmed evidence and active eligibility.
  Explain which distinctions are conceptual only and which a future wire contract would need.

Provide quantified definitions and a property table for at least:

| Property | Required distinction |
|---|---|
| Fixed-cutoff causality | Adding a not-yet-available revision cannot alter an earlier result. |
| Origin invariance | Identical bounded observations/configuration imply identical current results despite extra older history. |
| Stored-result immutability | A previously saved output is unchanged; this alone says nothing about agreement between new evaluations. |
| Confirmation consistency | Under declared unchanged-evidence conditions, an already confirmed event is not removed, rewritten or newly rediscovered as if just confirmed. |
| Active expiry | Evidence can leave the current active domain without deleting its historical existence. |
| Revision sensitivity | A legitimately available revised observation is distinguished from left-boundary reseeding. |
| Nontriviality and uncertainty | Hand-defined valid reversals can be recognized, while flat/ambiguous/insufficient input need not force a pivot or direction. |

The original R02 criterion remains visible: track events whose extreme AND confirmation stay
active in both windows, independent of algorithm IDs. If the recommendation instead conditions
stability on a wider evidence dependency set, state exactly how that set is computed, its maximum
extent and the resulting loss of coverage. Report both old and proposed eligibility measures.
It is a proposed semantic amendment, not retroactive passage of R02 or permission to hide all
unstable events as expired/ambiguous. Constant UNCERTAIN is not a satisfactory solution.

Separate stable Pivot identity from recomputed Swing labels, current Regime and zone/range
geometry. New legitimate price evidence and active expiry may alter the latter. Define the
scope of every exact-equality or tolerance statement; a tiny Decimal geometry difference and
a lost confirmed event are different claims. Preserve the existing 0.5 ATR/material diagnostics
when referring to R02; any alternative tolerance belongs in the explicit proposal only.

## 5. Analyze feasibility and specify at most two semantic models

Focus on the demonstrated mechanisms: an inadmissible opposite extreme can occupy the
candidate forever; persistent UNSEEDED dual reversal can prevent seeding; moving the finite
window changes ATR initialization and the initial candidate/state domain.

For the existing baseline and H1, trace their actual evidence dependency and give scoped
counterexamples to claimed stability. The retained 13-pivot witness is mandatory. Explain
why prefix independence at one fixed cutoff does not by itself establish rolling consistency.
Do not infer the unknowable order of high/low inside an OHLC bar.

Compare at most two precisely specified semantic models. Choose them for distinct evidence
and confirmation semantics, not a parameter grid. Useful questions include whether an event
can carry a finite, reconstructible witness independent of the moving window's oldest seed,
and what additional declared initial state a persistent-confirmation reference would require.
These are research questions, not preapproved algorithms or guarantees.

For each model, supply:

- equations/state transitions, initialization and update order, exact admissible-extreme domain;
- equality/tie behavior, minimum separation, same-bar prohibition and both-predicates-true behavior;
- confirmation versus recognition timing, finite evidence support or explicit state dependency;
- sufficiency, expiry and ambiguity rules, with their semantic cost and at least one useful
  hand-calculated reversal that is accepted and one legitimately uncertain case;
- dependency and complexity bounds, deterministic numeric/version identity, and minimal
  counterexamples to any property it does not satisfy;
- an exact amendment table against original/H1 semantics, including ATR, W/A/N, separation,
  active gates and possible downstream impacts. Proposed parameters must have a declared
  reasoning basis; they cannot be selected by AVGO labels, P&L or Q/E agreement.

The original profile and algorithms remain frozen. For isolated mathematical models only,
you may *propose* changes to seed/admissibility/evidence-support/confirmation rules and analyze
whether a different volatility dependency is necessary. Clearly version any such model as
`PROPOSED_SEMANTICS`, and declare every changed assumption. No proposal changes runtime or
the accepted research baseline, and no full zone/range/regime engine is authorized here.

For every theorem or incompatibility claim, list premises, quantifiers, proof argument and
scope. A finite enumeration establishes only that finite domain unless accompanied by a
general proof. Distinguish PROVED_UNDER_ASSUMPTIONS, COUNTEREXAMPLE_FOUND, FINITE_DOMAIN_CHECKED
and UNRESOLVED. Do not claim finite memory and immutable confirmation universally incompatible
without the precise extra assumptions needed. If no model resolves all desired properties,
finish the comparison and recommend a specific tradeoff for review rather than inventing success.

## 6. Executable evidence and bounded validation

Commit a research-03 plan before running new comparisons/enumerations. Freeze model definitions,
propositions, small-domain bounds, expected hand examples and rejection criteria. If a later
correction is necessary, record it additively with a reason; do not silently replace the plan
or remove counterexamples. All evidence output uses fresh paths and exclusive creation.

Include executable, labelled SYNTHETIC witnesses for:

1. The exact retained H1 201-bar/13-rediscovered-Pivot counterexample, independently reproduced.
2. The R02 four-bar admissibility trap and its price mirror, retaining the semantic cost of
   omitting the more extreme but too-close bar.
3. Persistent two-way seed ambiguity, exact equality/ties, flat and monotone sequences;
   no forced intrabar ordering or manufactured two-sided trend.
4. A genuine active expiry and a still-active event change; separate newly confirmed and
   newly recognized old events using timestamps and refs rather than local array indices.
5. The ATR boundary mechanism, including how an older seed influences otherwise common data;
   distinguish exact recurrence effects from rounded-geometry tolerances.
6. Future unavailable revisions, an available revision at a later cutoff, malformed quality,
   missing evidence and incomplete bars; proposed semantics cannot waive F01/F02.
7. Same bounded inputs under different prefixes, fresh processes and surrounding Decimal
   contexts; if a proposed stateful reference differs, report its additional input honestly.
8. Each new model's useful accepted hand example and rejection case, plus the exact assumptions
   of any finite-support/stability claim. Keep every counterexample that falsifies a proposal.

Use deterministic small exhaustive domains or generated families where useful. Declare the
actual domain size, seed, count and execution budget, and mark incomplete searches honestly.
Avoid combinatorial explosions, full-market scans and blanket statistical claims. Mathematical
proof prose plus a small independently checked witness is sufficient; no proof-assistant or
property-testing dependency needs to be added.

Run the existing **132** research tests plus all new R03 tests, Ruff/format and strict mypy
(native and Windows target) over added Python. This is isolated research; additional business,
browser, Uvicorn or database suites are only justified by a concrete changed dependency or
remaining risk. Do not claim unexecuted suites. Check links, `git diff --check`, all 465 base
mode/type/blob identities, issued-contract identity and the new-path allowlist.

## 7. Deliverables and acceptance

Required deliverables:

- `docs/research/PAQS_Q_CONFIRMATION_AND_ROLLING_STABILITY_R03.md`: complete proposed
  mathematics, property/assumption matrix and exact amendment comparison.
- `docs/evidence/TASK_006B_Q/research-03/PLAN.md`: frozen study definition.
- `docs/evidence/TASK_006B_Q/research-03/REPORT.md`: readable Chinese decision summary,
  proof/counterexample register, validation, limits, SHAs, changed paths and one recommendation.
- `docs/evidence/TASK_006B_Q/research-03/README.md`: reproducible commands and evidence map;
  compact machine-readable witness results and protection/validation metadata alongside it.
- Dedicated pure research checker/model code and independent tests in the allowed R03 paths.

| Gate | Passing this research task requires |
|---|---|
| R03-01 | Confirmation, recognition, current-window output and saved historical output are formally distinguished. |
| R03-02 | Evidence dependencies and unchanged-evidence conditions are explicit; old endpoint-based loss/reappearance measures remain visible. |
| R03-03 | Baseline/H1 failure mechanisms and the exact 13-pivot witness are reproduced; no universal inference from one example. |
| R03-04 | At most two complete semantic models, independently checked hand examples and an exact amendment/cost comparison. |
| R03-05 | Stability/feasibility claims carry scoped proofs or counterexamples; finite testing is not misrepresented as a theorem. |
| R03-06 | Quality, availability, time, Decimal, active-evidence and legitimate-uncertainty boundaries remain explicit and tested. |
| R03-07 | All prior files/contracts/evidence preserved; reproducible commands and proportional validation pass. |
| R03-08 | One concrete recommended next experiment or smallest unresolved semantic decision; no market/adoption PASS claim. |

Separate four conclusions: research-delivery correctness, mathematical feasibility under stated
assumptions, real-market completeness and product adoption. Real-market completeness remains
INCOMPLETE on the existing AVGO-only evidence; this task does not repair that gate. Proposed
semantics remain pending independent review and explicit adoption. A well-supported finding
that a desired combination is incompatible under named assumptions is a valid research result.

## 8. Handoff and stop

The owner authorizes local commits and a normal push **only** to
`task/006b-q-r03-confirmation-stability-contract`. Read back the exact final GitHub SHA,
report and frozen-plan lineage. Preserve unrelated worktrees and user data.

Do not force-push, alter remotes/global Git configuration, update the original Q/R02 branches,
change product authority or merge any research/review branch. No 006C-Q, complete replacement
engine, real-data acquisition campaign or product implementation follows automatically.
Stop after this mathematical contract and executable evidence are delivered for independent review.
