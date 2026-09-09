# TASK-006B-Q-R02 — Explain and test structural stability

Status: **AUTHORIZED RESEARCH IMPLEMENTATION — causal diagnostics, bounded candidate experiments and validation; no production adoption.**

Owner continuation instruction: “继续”, following independent F01/F02 PASS and the recommendation to address the remaining seed/window sensitivity and validation shortfall.

Repository: `ahhhhzzz/ai-infra-quant`.

Only task branch: `task/006b-q-r02-structure-stability`.

Exact development base: `d50d73eea28005bc96e5ed0721b6a8e385ecedf5` (reviewed research implementation, not merged into product authority).

Unchanged product authority: `roadmap/no-live-trading`, `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`.

Focused review: `fcdf69e5714ad32ddd8b526759e802d20c53f70a`, branch `review/006b-q-f01-f02-focused`.

R02 remains inside the 006B-Q workstream; it does not start 006C-Q or amend PAQS-E.

## 1. Read and establish the baseline

Read AGENTS.md, ROADMAP, MASTER_SPEC, ARCHITECTURE, STRATEGY_SPEC, REQUIREMENTS_MATRIX and applicable phase plan; the original 006B-Q contract and candidate; remediation-01 CONTRACT/REPORT; and these exact reviews:

- [Initial review](https://github.com/ahhhhzzz/ai-infra-quant/blob/e4bf4cb6092e48c98732bd7d355d31affbf8a332/docs/reviews/TASK_006B_Q_INDEPENDENT_REVIEW.md).
- [Focused PASS](https://github.com/ahhhhzzz/ai-infra-quant/blob/fcdf69e5714ad32ddd8b526759e802d20c53f70a/docs/reviews/TASK_006B_Q_F01_F02_FOCUSED_RE_REVIEW.md).
- [Current prototype](../../tools/research/paqs_q/engine.py), [availability-aware diagnostics](../../tools/research/paqs_q/diagnostics.py), [temporal checks](../../tools/research/paqs_q/temporal.py).
- [Original cases](../../docs/evidence/TASK_006B_Q/boundary-case-review.json), original diagnostics, corrected-study evidence and [fixed universe](../../docs/evidence/TASK_006B_Q/universe.json).

Fetch exact commits, verify ancestry and git status, inspect worktrees, and state planned paths before implementation. Work from the R02 branch; do not merge review branches or update the original task branch. Preserve unrelated worktrees, untracked files, user data and phase1_remediation_commit.txt.

Prior facts: F01/F02 are CLOSED; original product files are unchanged. Real coverage is AVGO only: W1/D1 100 valid endpoints each, M30 74. Reported 12 material LEFT_ONLY cases and D1 UNCERTAIN 96/100 are not resolved by the focused correctness fixes. They are hypotheses to investigate, not permission to force trend labels. Lack of data is separately disclosed, not a reason to treat synthetic data as real.

## 2. Objective and complete delivery

Answer with executable evidence:

1. Why do recent pivots disappear/reappear when the left window moves?
2. Which reasons account for the high D1 UNCERTAIN proportion? Distinguish actual conflicting/equal structure, insufficient active comparisons, current-close breach, seed ambiguity/path lock, stale pivots, missing data and range unavailability.
3. Can a small, explicitly defined rule revision improve structural robustness while preserving bounded memory, origin invariance, completed-only evidence and deterministic arithmetic?

Deliver a root-cause report, an executable diagnostic harness, at most two hypothesis-driven candidate implementations, new adversarial tests, same-input comparisons and a final research recommendation. A prose-only proposal, blanket “more data needed” conclusion, or increased trend-label count is not completion. A well-supported rejection of both candidates is a valid research outcome; do not adopt an unstable candidate to manufacture success.

## 3. Allowed files and preservation

Add files only under:

- `tools/research/paqs_q/r02/` — isolated candidate algorithms, traces, CLI and research integrations.
- `tests/research/paqs_q/r02/` — dedicated validation of the new work.
- `docs/evidence/TASK_006B_Q/research-02/` — plan, frozen hypotheses, manifests, trace samples, metrics, report and reproduction instructions.
- `docs/research/PAQS_Q_STRUCTURE_R02_CANDIDATES.md` — explicit mathematics and recommendation.

The issued R02 contract is immutable after handoff. All files present at the exact development base, including the accepted research implementation/tests, original candidate, remediation evidence, profile/universe and every product file, must retain Git mode/type/blob. Do not modify the existing verifier to waive protection. Add an R02-specific verifier for this contract's additive scope if useful.

Read-only imports of existing pure research/domain code are permitted. Candidate results must not be produced by relabelling the baseline's structure. Version any changed algorithm separately; do not present it under QSTR-CANDIDATE-1.1. No src changes, dependency/config changes, database migration, API/UI, archive-to-chart/Analyze wiring, LLM call, background scan, brokerage or accounting work. No Event/Setup/RR/advisory implementation.

## 4. Phase A — root causes before candidate selection

Use the exact retained AVGO normalized files from the original local worktree if available. Verify their hashes against the prior source manifest before calculation. Read the database only if required to reconstruct the same Capture with the accepted normalizer; never modify it or query accounts/credentials. All new outputs go under research-02 or a separate external data directory. Never point a rerun at original evidence directories.

For each of the 12 cases, reproduce the four arms and explain the first meaningful computational divergence. Record, at minimum:

- exact source/capture identity, timeframe, cutoff and bounded observation hashes;
- actual calendar/session and complete-bar indices for the exiting warm/active item;
- seed-state sequence, candidate High/Low references, positive ATR initialization, reversal predicates, confirmation and minimum-separation predicates;
- whether the disappearing pivot's extreme AND confirmation remain active in both normal evaluations;
- whether its loss arises from legitimate active expiry, a changed seed path, ATR recurrence differences, active-comparator insufficiency, quality/version changes or interacting/unresolved causes;
- consequences for the latest eligible labels, zones/range and Regime, with reasons and operands.

Four-arm equality alone is not a causal explanation. Use bounded instrumented traces and targeted ablations to locate the earliest divergence. Diagnostic counterfactual ATR/seed runs must be labelled diagnostic-only and never become normal outputs. Do not give a definitive causal label where the interventions cannot distinguish interacting mechanisms.

Create minimal synthetic counterexamples for distinct mechanisms; preserve hand-computed expected events/uncertainty. Particularly test a wide initial bar that leaves both reversal predicates true, a recent pivot far from expiry disappearing after a warm bar exits, and genuinely expired active evidence. Synthetic reductions explain the mechanism; they do not replace the original market record.

Break down every available D1 evaluation's UNCERTAIN reason and affected active evidence. Do not assume all 96 cases are wrong, and do not optimize their percentage downward. For each proposed fix state which independently demonstrated defect it addresses and which legitimate uncertainty it preserves.

## 5. Phase B — at most two explicit mathematical hypotheses

Freeze `research-02/EXPERIMENT_PLAN.md`, hypothesis definitions and evaluation cutoffs in a commit before candidate market comparisons. Phase-A observations may inform a hypothesis; disclose that the known AVGO cases are a development sample, not an unseen validation set.

Authorize at most two candidates total. Each must have a narrow mechanism and complete deterministic equations/state transitions, not a grid search. Suitable questions include deterministic initialization under persistent dual-reversal ambiguity and bounded seed handoff that reduces dependence on the oldest warm bar. Select the concrete mechanisms from Phase-A evidence; this contract does not prescribe an untested reversal shortcut.

For each candidate specify:

- state variables, reset/initialization, processing order, tie/equality/same-bar handling;
- earliest legitimate extreme and confirmation timestamps, warm-to-active handoff and minimum evidence;
- memory window and sufficiency; how origin invariance follows from the declared inputs;
- exact Decimal context, rounding, parameter/algorithm version and canonical result identity;
- expected behavior on flat, monotone, alternating, gap and ambiguous OHLC inputs;
- failure modes, semantic changes versus baseline, and evidence that would reject the hypothesis.

Keep existing numerical profile, ATR convention, W/A/N, lambda, zone/range rules and active directional-evidence gates fixed for this experiment. Candidate differences should concern the demonstrated seed/window mechanism. Do not reduce the two-high/two-low gate, add forced pivots, hysteresis or return-fitted thresholds merely to increase coverage. If Phase A shows that solving the problem necessarily requires changing one of those protected semantics, complete the diagnosis and admissible experiments and document the specific proposed amendment; do not silently enlarge scope.

Do not use unbounded persistent state to satisfy a bounded-current-structure claim. A stateful reference may be a labelled diagnostic comparator, but cannot become the adopted candidate if identical bounded input then depends on process history. Do not promise both arbitrary rolling-window repaint immunity and finite-memory origin invariance without proving the stated assumptions. Earlier output artifacts remain immutable; distinguish a genuinely newly confirmed pivot from an old pivot rediscovered by recalculation.

## 6. Phase C — validation and data acquisition

Keep the original fixed 40-member universe and show original vs additional coverage separately. Use all original available endpoints for baseline comparisons; do not select only attractive cases. Lock an additional validation cutoff ceiling before acquisition/comparison. Additional equities serve as a held-out structural check after hypothesis freeze; do not iterate candidates against them or claim current-survivor sampling establishes predictive performance.

This task authorizes an explicit, separate attempt to acquire missing public historical research observations without OpenD. Check current provider documentation/terms and actual availability. Use accessible public or already authorized sources; no new paid service, account registration, secret handling or access-control bypass. Acquisition lives under `r02/integrations/`; no networking on import, ordinary analysis or tests. Do not add production dependencies; optional research tools use an isolated environment.

**OpenD historical research quota budget remains zero.** External data are research inputs, not a new production provider. No fabricated calendars, copied vendor M30 with unverified bucket semantics, gap-filled OHLC or upgraded precision/availability labels. Maintain exact numeric text where available and disclose any upstream float loss. Current-adjusted data remain observational, not strict corporate-action-safe historical information sets.

Target the existing >=40-equity / >=24-US / >=16-HK sample and >=100 sequential eligible endpoints per timeframe where data permit. Request enough history for full windows plus endpoints: at least 229 completed W1, 411 D1, 299 M30. Verify calendar derivation and regular-session M30 alignment. Daily-only sources can add D1/W1 coverage without falsely satisfying M30. Report unavailable symbols/timeframes in the original denominators. One documented attempt per plausible accessible path is sufficient; do not waste repeated failing requests or consume the user's quotas.

Record acquisition commands, source/version, retrieval time, original bytes/content hashes, normalization, calendar/session origin, adjustment/availability quality, exact cutoff selection and exclusions. Retain permitted raw observations outside Git; commit only permitted compact traces/metrics and reproduction metadata. If original or additional observations remain inaccessible, complete synthetic and obtainable-data experiments, identify exact shortfalls, and keep the affected market gate INCOMPLETE. Do not describe a hash-only record as fully reproducible without accessible observations.

## 7. Acceptance and comparison matrix

All candidate comparisons use the same eligible observations, cutoffs and baseline. Compare structural facts/geometry/references rather than algorithm-version hashes, which necessarily differ.

| ID | Required result |
|---|---|
| R02-01 | Each original case reproduced or explicitly unavailable; earliest divergence trace and evidence-supported cause; no blanket expiry explanation. |
| R02-02 | D1 reason census covers all available declared endpoints; no UNCERTAIN-rate target or fabricated trend evidence. |
| R02-03 | At most two frozen hypotheses; complete formulas and independent synthetic oracles; baseline files unchanged. |
| R02-04 | Fixed-cutoff future/availability isolation and F01/F02 protections hold, including all warm inputs and revision-confounded transitions. |
| R02-05 | Same bounded observations/config yield identical results across processes, surrounding Decimal contexts and arbitrary extra older valid history. |
| R02-06 | Warm anchors, expired pivots/zones and incomplete bars cannot silently create active directional/range evidence; retain legitimate uncertainty. |
| R02-07 | Quantify baseline/candidate seed ambiguity, recent-pivot disappearance/reappearance, legitimate expiry, direct flips, geometry discontinuity, churn, structure sufficiency and available coverage. |
| R02-08 | Explain every remaining material left-only case in the evaluated sample; unresolved recent-structure jumps prevent candidate robustness acceptance. No arbitrary zero-expiry-change requirement. |
| R02-09 | Original universe retained; additional-data coverage and quality honest; missing timeframes do not become synthetic market PASS. |
| R02-10 | Frozen small OFAT sensitivity checks remain robustness diagnostics only. Do not choose lambda/window/zone thresholds by P&L, label frequency or PAQS-E agreement. |
| R02-11 | Performance measured on declared hardware/fixtures and bounded windows; report timing overhead and comparison counts, no invented SLA. |
| R02-12 | Separate engineering correctness, observed structural robustness, real-data completeness and production adoption verdicts; no prediction/return claim. |

For recent-pivot disappearance metrics, explicitly define the comparable event identity independently of config ID and require the original extreme and confirmation to remain eligible in both windows. Count denominator opportunities, not just selected failures. Separate normal confirmations and actual expiry from re-seeding changes. Compare geometry with declared ATR-normalized distances/IoU and show relevant hand-inspected cases.

No new arbitrary acceptance threshold may be chosen after observing results. At minimum hard correctness violations must be zero; repeatable loss/reappearance of still-eligible recent structure due only to seed reconstruction requires resolution or candidate rejection. Legitimate price evidence and eligibility changes may alter structure. Do not call a conservative constant-UNCERTAIN engine successful simply because it has low churn.

## 8. Tests, report and handoff

Run original 97 research tests, the same 59 related regressions, new R02 tests, Ruff/format and strict mypy (including Windows target) over all added Python. Use explicit test/type paths without changing configuration. Verify all development-base mode/type/blob identities, contract identity, new-path allowlist and links; run diff check. No unrelated full-browser/business/Uvicorn suite is required for this isolated research experiment.

Provide:

- `docs/evidence/TASK_006B_Q/research-02/REPORT.md`, readable Chinese summary plus technical evidence;
- reproducible commands, exact base/implementation SHA and complete changed-path list;
- per-case causal table, UNCERTAIN reason census, hypothesis freeze commit, parameter/version hashes;
- baseline/candidate metrics and representative traces on development and additional validation observations separately;
- preservation/data-coverage/quality results, unresolved limitations and a clear recommendation: retain baseline, recommend a specific candidate for independent review, or reject both with a concrete next decision.

Do not conclude merely “tests passed”. Explain whether the experiment actually addresses the demonstrated mechanism, what it leaves unresolved, and what may legitimately be adopted after independent review. No automatic production integration follows from a recommendation.

The owner authorizes commits and normal push only to the R02 task branch. Read back the exact GitHub SHA/report. Do not force-push, change authority, merge prior research/reviews, overwrite another worktree or start 006C-Q. Stop after delivering this bounded experiment for independent review.
