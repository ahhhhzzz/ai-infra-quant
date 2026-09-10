# TASK-006B-Q-R04 — Local certificate market applicability

Status: **AUTHORIZED BOUNDED RESEARCH EXPERIMENT**, issued 2026-09-10 following owner “批准”.

Repository: `ahhhhzzz/ai-infra-quant`.
Only task branch: `task/006b-q-r04-local-certificate-market-applicability`.
Exact development base: `cc909077a470f7a6e717787307e8a4a8062ff792`.
Product authority remains `roadmap/no-live-trading` at
`8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`.
R03 focused PASS / F01 CLOSED:
`1f8eba9b7112695e59e2dcd1bbef218dac51e74e`, branch `review/006b-q-r03-f01-focused`.

Approval permits studying calendar-aware local certificates, their structural meaning and
real-observation comparisons. It does not adopt M1/M2 as the formal PAQS Pivot definition,
merge prior research, change PAQS-E, or start 006C-Q.

## 1. Read, verify and preserve

Read AGENTS, ROADMAP, MASTER_SPEC, ARCHITECTURE, STRATEGY_SPEC, REQUIREMENTS_MATRIX and
the applicable phase plan. Previously read governing files may be reused after blob equality
is verified. Read the original Q contract/math, F01/F02 quality/time policy, R02 contract/report,
R03 contract/frozen plan/math and R03-F01 clarification. Read these exact independent reviews:

- [R03 review](https://github.com/ahhhhzzz/ai-infra-quant/blob/8338c2b61cd60dc5c1079a3648b66d9643b19031/docs/reviews/TASK_006B_Q_R03_INDEPENDENT_REVIEW.md).
- [R03-F01 closure](https://github.com/ahhhhzzz/ai-infra-quant/blob/1f8eba9b7112695e59e2dcd1bbef218dac51e74e/docs/reviews/TASK_006B_Q_R03_F01_FOCUSED_RE_REVIEW.md).
- [Current proposed mathematics](../../docs/research/PAQS_Q_CONFIRMATION_AND_ROLLING_STABILITY_R03.md),
  [state clarification](../../docs/evidence/TASK_006B_Q/research-03/remediation-01/M2_STATE_CLARIFICATION.md),
  [M1/M2 code](../../tools/research/paqs_q/r03/models.py).
- [Existing archive normalizer](../../tools/research/paqs_q/integrations/local_archive.py),
  [original universe](../../docs/evidence/TASK_006B_Q/universe.json),
  [R02 frozen cutoffs](../../docs/evidence/TASK_006B_Q/research-02/freeze.json).

Fetch exact commits, confirm ancestry, remote authority and worktree status; state planned paths.
Read pinned reviews without merging their branches. Preserve unrelated worktrees, untracked
files, phase1_remediation_commit.txt and all user data. Use an isolated worktree as necessary.
All **482** files at the development base and this issued contract are immutable mode/type/blob.
Historical product-status documents do not authorize product changes or reopening accepted work.

## 2. Required decision

Determine whether the fixed local-certificate mechanism deserves a further structural-engine
experiment once real session/calendar semantics and its structural costs are exposed.

Answer with executable evidence:

1. Which ordered bars legitimately form the four-observation witness across trading calendars,
   and which gaps/unknowns must prevent certification?
2. Do the conditional support/padding guarantees survive that calendar treatment without
   hiding dependency changes, revisions, losses or excluded opportunities?
3. What structures does the local rule actually identify or omit on available real observations:
   repeated HIGH/HIGH or LOW/LOW, vetoed turns, more extreme omitted prices, sparse/no output,
   timing/coverage costs and ambiguity?

Deliver one conclusion: recommend a separately bounded continuation, recommend a specific
rule amendment for later testing, or reject this direction. Explain the evidence and limits.
Zero rolling loss, more events or reduced UNCERTAIN alone is not success. If evidence is too
limited to decide, state exactly which gate remains unresolved and complete the obtainable work.

## 3. Additive scope

Add only:

- `tools/research/paqs_q/r04/` — calendar-aware research wrapper, diagnostics, CLI, visual
  evidence generator and any research-only source adapters under its `integrations/` directory.
- `tests/research/paqs_q/r04/` — independent calendar, quality/time, identity and semantic oracles.
- `docs/research/PAQS_Q_LOCAL_CERTIFICATE_MARKET_APPLICABILITY_R04.md` — exact research semantics.
- `docs/evidence/TASK_006B_Q/research-04/` — frozen plan, manifests, comparisons, bounded chart
  cases, report, reproduction guide and verification metadata.

Do not edit existing code/specifications/tests/verifiers/parameters/evidence. Read-only imports
of existing pure helpers are allowed. No src, migration, dependency/config change, API/UI,
archive-to-chart/Analyze, persisted history service, broker/account action, LLM call, Event,
Setup/RR, advisory or scanner. Do not build a complete Swing/Zone/Range/Regime replacement.
M2 remains an explicit historical comparator only; no hidden persistent state to improve M1.
Use existing dependencies; an isolated plotting environment is permissible without changing
project dependency files. Exact data calculations use Decimal, with conversion only for plotting.

## 4. One fixed research candidate

Use one separately versioned calendar-aware extension of the R03 M1 local rule. Preserve its
raw D_j/U_j, XOR, prior-raw veto, preceding high-low scale with coefficient 1, strict neighboring
extrema, no same-bar confirmation and four-bar price support. Do not add another threshold,
alternation filter, smoothing, ATR variant or candidate after seeing market results.

The authorized changes are explicit calendar adjacency, input qualification, complete support
metadata and research window mapping. For comparable real evaluations use the original Q
W/A/N profiles: W1 26/104/130, D1 60/252/312, M30 40/160/200. These are fixed observation
horizons, not a parameter search; M1's scale does not become the old lambda/ATR. Keep R03's
N8 W0/W2 experiment and original algorithms unchanged as historical controls.

If this single mechanism is structurally inadequate, show the failing cases and propose the
specific next change without implementing it here. A revised full engine is outside scope.

Before candidate comparisons, commit PLAN.md plus the candidate/calendar/quality specification,
case-selection rubric and scheduled cutoffs. Freeze all model choices and rejection criteria.
Later corrections require additive explanation; never rewrite the freeze or conceal counterexamples.
AVGO informed prior research and remains development data, never an unseen validation sample.

## 5. Calendar and full-support contract

Define expected ordered slots from evidenced market/session calendars, separately from the
observations that happened to arrive. Deleting missing/incomplete rows must not manufacture
consecutive evidence. Never fill OHLC, infer a calendar solely from bar presence, or silently
reuse stale/unknown calendar metadata. Record calendar source/version, retrieval/availability
and the schedule facts actually used, including negative evidence that no slot is missing.

Freeze one deterministic boundary policy before market comparison. Required distinctions:

- D1: successive actual trading sessions can be adjacent across known weekends/holidays;
  a missing expected trading session is a break, not a weekend. Account for exceptional closures.
- W1: use accepted completed-week construction with its underlying session completeness;
  nominal interval endpoints do not advance factual completion/as-of. Partial/holiday weeks
  require their evidenced trading schedule, not an assumed five-day count.
- M30: use accepted REGULAR-session buckets, market timezone and actual session segments;
  US extended-session bars cannot silently enter the structural series. Specify handling of
  overnight, HK lunch, early closes, DST, missing buckets and incomplete final buckets.
- A known closure and a missing expected bar are different. Crossing a known segment boundary
  may be permitted or rejected only by the frozen per-timeframe policy, with the price-gap and
  coverage consequences disclosed. Unknown adjacency cannot establish a confirmed witness.

If a quartet crosses a prohibited or unverified edge, the certificate is ineligible. Do not
replace an unavailable prior raw predicate with false: the negative veto requires its own
complete four-bar witness. Retain all excluded raw centers with reasons in the census.

Complete computational support includes ordered price/version refs AND the calendar/adjacency
facts and qualification rules needed to evaluate both raw predicates. Mere unordered set inclusion
does not prove identical support. Verify ordering, no insertion/deletion, unchanged calendar
versions, valid global preconditions and active endpoints before applying R03's conditional proof.
If these additions change a proof premise, state it and supply an argument/counterexample.

Distinguish event identity, current support, reversal completion, available evidence, first actual
recognition and calculation cutoff. Calendar amendments and late observations/revisions are
information changes, not pure left-boundary reseeding. No recognition-time backdating.

## 6. Strict and observational research must remain distinct

Retain F01 vocabulary/quality relationships, F02 cutoff-specific version selection and all-input
time checks. Never coerce PARTIAL/UNKNOWN to COMPLETE or fabricate available_at.

Provide explicit qualifications rather than globally upgrading an archive:

- Strict AS_OF confirmation requires legitimately available completed price AND calendar
  evidence under the frozen completeness policy at that cutoff.
- The existing AVGO archive has current-QFQ/PARTIAL and unknown historical availability.
  It may support a separately labelled OBSERVATIONAL local-pattern computation on actual valid
  completed observations and evidenced calendar adjacency. These outputs are observational
  certificates/patterns, not proof that the event was knowable historically or strict PIT-safe.
- Invalid/contradictory selected inputs fail conservatively in both modes. Missing expected
  evidence and unknown adjacency cannot be erased by changing mode. Preserve per-bar and
  aggregate quality and distinguish an observed local pattern from certified full coverage.

Specify these policies in the freeze before the AVGO run. Report results/denominators per mode
and reason. Do not inherit R03's strict eight-bar gate unmodified, reject all real observations
and then claim this task established market applicability. Equally, inability to qualify strict
history must not be solved by inventing timestamps. If only observational comparison is possible,
complete it honestly and leave the strict-market gate unpassed.

## 7. Data access and sample discipline

First use the already authorized original normalized AVGO files and frozen calendar/capture
evidence. Verify hashes against prior manifests; use all original scheduled cutoffs including
insufficient cases. If normalized files lack necessary calendar facts, inspect the original
captured calendar and reconstruct with the accepted normalizer plus additive R04 metadata.
Preserve original normalized bytes and identities; no in-place rewriting.

Known source: user-local `data/ai_infra_quant.db` under the Windows project and Capture
`2babba19-e0ce-4bfa-aab9-93061a95818c`. Read-only archive queries are authorized only if needed;
prefer existing normalized inputs. Open SQLite in enforced read-only mode, never migrate,
checkpoint, bootstrap, write or inspect accounts/credentials. Outputs go to separate new paths.
Do not claim independent preservation of an externally changing database from a stale hash.

For independent equities, inventory already accessible authorized research data. Preserve the
fixed 40-member universe (24 US/16 HK) and original per-timeframe 100-cutoff target, with
original versus additional coverage separate. Freeze an additional cutoff ceiling and selection
rule before any new comparisons. Do not substitute convenient symbols or remove missing members.
Daily-only evidence can support D1/W1 if calendar qualification permits; it cannot satisfy M30.

OpenD historical request budget remains **zero**. Explicit public research retrieval via a
permitted route is allowed, after checking current primary documentation/terms; no paid service,
account registration, access-control bypass or user-secret inspection. Reuse R02 access-failure
evidence; do not repeat identical failed requests absent a concrete changed availability reason.
Try a materially different accessible route once where useful; do not spend the task on repeated
acquisition failures. Networking belongs only in explicit research integrations, never imports,
ordinary evaluation or tests. Freeze a small request budget before retrieval and report usage.

Retain permitted raw data outside Git, with source, retrieval, bytes hashes, version/adjustment,
calendar provenance, normalization and precision limits. Commit only permitted compact evidence.
If additional data are unavailable, preserve the shortfall and finish original-data/synthetic
work; no synthetic samples count as real equities. If original data are also unavailable, report
the exact blocked market gate instead of claiming charts or hashes establish a completed comparison.

## 8. Comparisons and structural meaning

For every scheduled cutoff, retain valid/insufficient/unavailable status, qualification mode,
window/source/calendar hashes and rejection reasons. Where raw input is identical, reconcile
baseline/H1 with retained hashes; report differing calendar domains as a disclosed comparison
difference rather than algorithm improvement. Keep raw versions for every cutoff/diagnostic arm.

Required quantitative evidence, with opportunity denominators and identities independent of
algorithm IDs:

- Original endpoint-eligible losses/rediscoveries, new confirmations, actual recognition and
  genuine active expiry; additional full-support opportunities/losses and coverage exclusions.
- Calendar breaks, ambiguous/unknown adjacency, revisions, missing/late/incomplete inputs and
  changed witness identities even where endpoint metric keys stay equal. Attribute separately.
- Counts/density and age of local certificates; repeated same-kind sequences, raw accepted
  turns versus XOR/veto/support rejections, and more extreme observed prices omitted by the
  local admissibility/veto policy. Do not silently select an alternating subsequence.
- Separation and volatility-normalized/local-range amplitudes where defined, with exact
  reference periods and zero-scale handling. These describe structure, not predicted return.
- Output and support coverage by timeframe, symbol, calendar segment and qualification mode.

Use a frozen all-center candidate census to quantify veto/rejection costs. A baseline pivot,
local turn or manually noticed reversal is a comparator, not universal ground truth; do not
call disagreement a false negative/recall rate without declaring the reference rule and its limits.
Do not implement or infer candidate Regime from unchanged old alternation-dependent logic.

Create a bounded visual case pack from the frozen selection rule: cover every available
timeframe, an accepted local pattern, repeated-kind output, a veto/omitted extreme, a calendar
boundary/missing-data case and every distinct unexplained still-active-change mechanism found.
Use deterministic first/most-extreme cases under declared rules, not only favorable screenshots.
If a category has zero instances, record zero rather than fabricate a real example; synthetic
calendar edge cases remain separately labelled. Keep full failures machine-readable even when
only representative images are shown.

Charts must use actual source OHLC up to the case cutoff, mark extreme and confirmation separately,
show price support/calendar edges and rejected centers, and identify source/adjustment/quality,
timezone, model and cutoff. No future candles or hindsight labels in the acceptance assessment.
Provide a short explicit visual-review rationale for each case; this is qualitative research,
not a user acceptance claim or statistically validated trading signal. Static reproducible SVG/PNG
charts or a local read-only case document are sufficient; no product frontend work is authorized.

## 9. Tests, delivery and stop

Use independent hand oracles for US/HK trading sessions, weekends/holidays, lunch/overnight,
DST/early close, missing expected slots, ambiguous calendar, delayed/revised calendar evidence,
unfinished bars and preserved W1 completion semantics. Synthetic calendar assumptions must be
labelled and cannot authenticate a real session. Test negative-veto support loss and insertion,
both input modes, F01/F02, all-input availability, origin invariance, calendar-aware common-support
consistency, active expiry, ties/dual ambiguity, repeated kinds and exact recognition timing.
Retain the H1 13-rediscovery witness and R03 W0 losses/W2 costs as unchanged controls.

Run all retained **168** research tests and new R04 tests, Ruff/format and strict mypy native
and Windows target over added Python. Run the existing input/calendar unit regressions if their
helpers are consumed; add other suites only for a concrete integration risk. No unrelated browser,
Uvicorn/database business suite is required. Verify all482 base mode/type/blob identities, issued
contract/freeze identity, links, new-path scope and diff. Measure bounded runtime/output size on
declared inputs for reproducibility; no production SLA or optimization mandate.

Deliver the research specification; frozen `research-04/PLAN.md`; `REPORT.md` with Chinese
decision summary and exact SHAs; `README.md` with commands/evidence map; source/calendar/cutoff
manifests; complete metric/rejection census; visual case pack; tests and preservation/validation
results. Evidence writes use fresh paths/exclusive creation. No overwritten old reports or evidence.

| Gate | Requirement |
|---|---|
| R04-01 | One frozen rule; explicit calendar/window/quality amendments and complete evidence dependency. |
| R04-02 | Calendar adjacency is evidenced; missing rows cannot fabricate consecutive support; calendar versions/time are audited. |
| R04-03 | Strict and observational outputs stay distinct; no quality/availability upgrade or retrospective knowledge claim. |
| R04-04 | Original loss/rediscovery/expiry metrics remain; narrower support exclusions and all failed cutoffs are visible. |
| R04-05 | Structural meaning/costs are assessed with all-center census and cutoff-limited visual cases; no zero-loss-only success. |
| R04-06 | Fixed original/additional sample coverage honest; raw availability limits and AVGO development status explicit. |
| R04-07 | Required tests/static/preservation/reproduction checks pass; no product or unrelated data changes. |
| R04-08 | One supported recommendation, clearly separate from conditional mathematics, market completeness and adoption. |

Unexplained still-active changes under claimed unchanged support, hidden dependencies, fabricated
continuity, recognition backdating or suppressed failure denominators prevent recommending the
candidate. A correctly explained but structurally unhelpful rule may be rejected as the research
outcome. Missing independent market coverage prevents a broad applicability PASS. A documented
rejection or incomplete market gate is valid delivery if all obtainable contracted work is done;
do not invent a new acceptance threshold after seeing results.

The owner authorizes commits and normal push only to the R04 task branch. Read back the exact
final GitHub SHA, report and freeze lineage. Do not force-push, update authority or prior task/review
branches, merge research, or start a successor. Stop for independent review after delivery.
