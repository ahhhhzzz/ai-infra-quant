# TASK-006B-Q-R05 — Prior-raw veto controlled ablation

Status: **AUTHORIZED BOUNDED RESEARCH EXPERIMENT ONLY**

Owner authorization: `批准 R04-F01 收尾并准备 R05`, received 2026-09-11.

Repository: `ahhhhzzz/ai-infra-quant`

Only task branch: `task/006b-q-r05-prior-raw-veto-ablation`

## 1. Exact authority and lineage

Required starting lineage:

- product authority `roadmap/no-live-trading`:
  `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`;
- corrected R04 research head and R05 development base:
  `c4e21a0204cf6cdd7bb139584b02f01792a49f13`;
- original R04 independent review:
  `4906985744512092fc098340f43e8eec1f41c494`;
- R04-F01 focused independent PASS / closure:
  `2094118f270e209b5b037162813815886678fdbd`;
- corrected R04 evidence candidate: `docs/evidence/TASK_006B_Q/research-04/study-03/`;
- R04 frozen semantics: `PROPOSED_SEMANTICS:R04-CALENDAR-LOCAL-1`.

This issued contract commit must be a direct child of the corrected R04 task head. Begin work only
after the new R05 task branch is at the exact contract SHA supplied in the handoff. Read the two
review commits by exact SHA; never merge, cherry-pick or copy their history into the task branch.

Before editing, read `AGENTS.md`, `docs/ROADMAP.md`, `docs/MASTER_SPEC.md`,
`docs/ARCHITECTURE.md`, `docs/STRATEGY_SPEC.md`, `docs/phases/PHASE_1_PLAN.md`, the R04 contract,
frozen specification/plan, final R04 report, R04-F01 contract/report and both exact reviews. Record
all worktrees and `git status`; preserve unrelated changes and untracked user files. Use an isolated
clean worktree.

This authorization prepares and executes R05 only. It does not merge R04, adopt either candidate
into product code, modify PAQS-E, start 006C-Q, or authorize any broker/account/trading capability.

## 2. Research question and non-claim

R04 showed that the fixed local certificate excludes otherwise unambiguous current raw reversals
whenever the immediately preceding center has any raw predicate. Across overlapping valid AVGO
cutoffs, R04 recorded active `PRIOR_RAW_VETO` occurrences of W1/D1/M30 = 172/939/108 and many
omitted-more-extreme comparisons. R04 did not establish whether the veto improves structural
meaning or merely suppresses useful adjacent opposite turns.

R05 must answer one narrow causal question:

> Holding prices, calendar qualification, four-observation support, cutoff selection, strict
> extrema, reversal scale and XOR fixed, what structural evidence changes when the prior-raw veto
> alone is removed?

This is a controlled structural ablation, not a profitability test, backtest, trading signal,
parameter search, market-applicability PASS or formal Swing/Pivot adoption. More events, fewer
omissions or zero rolling losses alone are not success.

## 3. Frozen baseline and single candidate

### 3.1 Baseline B0

`B0` is the exact corrected R04 rule and evidence:

```text
PROPOSED_SEMANTICS:R04-CALENDAR-LOCAL-1
study-03
```

R05 must independently reproduce B0 from the exact frozen R04 inputs and compare the reproduction
with study-03. It may consume R04 pure helpers read-only, but it must not modify R04 code or
evidence.

### 3.2 Candidate A1

The only event-producing R05 candidate is:

```text
PROPOSED_SEMANTICS:R05-NO-PRIOR-RAW-VETO-4SUPPORT-1
```

For center `j`, retain the R04 definitions exactly:

```text
v_j = H_(j-1) - L_(j-1), with v_j > 0

D_j =
  H_j > H_(j-1)
  AND H_j > H_(j+1)
  AND H_j - C_(j+1) >= v_j

U_j =
  L_j < L_(j-1)
  AND L_j < L_(j+1)
  AND C_(j+1) - L_j >= v_j

current_raw_j = D_j XOR U_j
```

Keep the exact R04 four-observation price/calendar support `j-2..j+1`, active/warm horizons,
quality gates, AS_OF/OBSERVATIONAL distinction, session/slot rules, Decimal context, event price,
extreme/confirmation endpoints and completed-bar requirements. The only acceptance change is:

```text
B0: accept current_raw_j only when neither D_(j-1) nor U_(j-1) is true
A1: accept current_raw_j regardless of D_(j-1) or U_(j-1)
```

The previous raw predicate may be calculated for diagnostics, but it must not gate A1. A1 must not
add an alternation filter, minimum spacing, ATR, smoothing, threshold, voting, trend/Regime logic,
tie-breaking rule or after-the-fact exception. Current dual raw remains rejected. Zero scale,
missing/invalid support, unknown calendar adjacency and incomplete evidence remain rejected.

Four-observation support is deliberately retained although `j-2` is no longer logically required
to decide A1. This preserves a matched eligibility domain and isolates the Boolean veto effect.
Do not silently shrink support or claim the retained dependency is minimal.

### 3.3 Diagnostic dependency audit, not a second candidate

R05 must separately count `TRIPLE_ONLY_ELIGIBLE` centers where the ordered current-raw triple
`j-1..j+1` is calendar/quality eligible but the retained R04 quartet is not eligible solely because
of `j-2`. Classify the unavailable dependency and timeframe/segment. This is a coverage-tax audit
only: it emits no event and cannot be used to improve A1 results. A three-support candidate requires
a future separately approved contract.

## 4. Pre-registration and freeze before AVGO results

The first R05 implementation commit after this contract must freeze, at minimum:

```text
docs/research/PAQS_Q_PRIOR_RAW_VETO_ABLATION_R05.md
docs/evidence/TASK_006B_Q/research-05/PLAN.md
docs/evidence/TASK_006B_Q/research-05/freeze.json
tools/research/paqs_q/r05/
tests/research/paqs_q/r05/
```

`PLAN.md` and `freeze.json` must record the exact B0/A1 definitions, implementation hashes, input
and calendar hashes, all 600 scheduled mode/cutoff evaluations, metric formulae, endpoint identity
policy, case-selection rubric, finite-enumeration domain, decision table and zero external-data
request budget. Commit and normally push this freeze, then read back its GitHub SHA **before**
running or inspecting AVGO A1 results.

Synthetic unit results needed to validate implementation may be run before the freeze. Do not run
the real AVGO A1 study, select real cases or compute its aggregate metrics before the freeze commit.
After real results are observed, no candidate, metric, cutoff, case-selection or calculation code
may change. If a result-affecting defect is found, preserve the failed output and stop for a new
correction authorization. A purely presentational correction must be additive and explicitly
identified.

## 5. Exact data and clock discipline

Use only the exact external normalized AVGO W1/D1/M30 inputs and captured/calendar material already
frozen by R04. Verify every hash against the R04 freeze and study-03 manifest. Use the same:

- W1/D1/M30 W/A/N profiles: 26/104/130, 60/252/312, 40/160/200;
- 100 scheduled cutoffs per timeframe per mode;
- OBSERVATIONAL and AS_OF qualification policies;
- calendar facts, source versions, current-QFQ/PARTIAL labels and unknown availability;
- actual recognition-time policy and no-lookahead audit.

R05 has zero OpenD, market-price, public-web, provider, model and LLM request budget. Do not access
the user database: R04's external normalized files are sufficient. Do not migrate, bootstrap,
checkpoint or inspect account/credential data. The other 39 fixed-universe members remain missing;
synthetic inputs do not count as additional real equities.

All calculations select the input version legitimately available under the declared mode/cutoff.
No recognition timestamp may be backdated. AS_OF insufficiency must not be repaired by invented
availability. OBSERVATIONAL output remains retrospective and cannot be called strict historical
confirmation.

## 6. Mathematical and implementation invariants

Use endpoint keys independent of algorithm/rule IDs for B0/A1 comparison. Event identities and
support hashes may carry the candidate version, but identity differences alone are not event
differences.

For every cutoff with a common valid eligibility domain, prove and test:

1. `endpoints(B0) subset_of endpoints(A1)`;
2. `removed_endpoints(B0 -> A1) == empty`;
3. every A1-only endpoint maps bijectively to one B0 active census row whose reason is
   `PRIOR_RAW_VETO` and whose current raw is XOR-unambiguous with complete quartet support;
4. every such B0 `PRIOR_RAW_VETO` row becomes exactly one A1 endpoint;
5. all shared endpoints retain kind, exact Decimal price, extreme/confirmation refs and times,
   calendar/price support components, availability and mode;
6. all non-veto census classifications, cutoff status/reason, selected window, calendar hash,
   quality and support coverage remain unchanged;
7. no dual, zero-scale, missing-support, unknown-calendar or prohibited-segment row is promoted;
8. B0 independently reproduces corrected R04 study-03 apart from explicitly listed actual run and
   recognition timestamps; B0 event keys, identities and support hashes do not receive an R05
   relabel;
9. the corrected segment aggregation invariants from R04-F01 hold for every valid B0 and A1 result.

Supply a conditional proof that A1 remains rolling-origin stable while the exact ordered quartet,
calendar facts, qualification mode, active endpoints and price versions are unchanged. Separately
show why insertion, revision, calendar change, unavailable support or active expiry is outside that
premise.

Prove or refute from the strict inequalities that two adjacent same-kind raw centers cannot both
hold; classify A1 additions by previous raw kind (`opposite`, `same`, `dual`) rather than assuming
that removal creates valid alternation. Preserve counterexamples for ties, dual current raw,
revision/insertion, missing `j-2`, and adjacent alternating chains.

Perform one frozen finite enumeration over a small exact Decimal OHLC alphabet and declared
calendar states. Record the input count and hashes. The enumeration must test the set/bijection
invariants, strict-neighbor proposition and at least one baseline-veto/A1-accept witness. It is a
mathematical implementation check, not market evidence.

## 7. Required A/B measurements

Report both overlapping-cutoff occurrence counts and deduplicated endpoint counts; never present
the former as independent samples. At minimum, retain per timeframe/mode/cutoff/segment:

- B0 and A1 event counts and densities;
- added/removed/shared endpoint keys and exact mapping to B0 reasons;
- prior-raw kind and separation for every added endpoint;
- consecutive event-pair same-kind/opposite-kind counts and rates;
- separation distribution, mass at separation one, maximum unit-gap alternating-chain length and
  run-length distribution by kind;
- event age and exact local-range-normalized amplitude distributions where defined;
- baseline and recomputed omitted-more-extreme/reference-opportunity counts, with identities;
- rolling endpoint/full-support losses, rediscoveries, new confirmations, expiry and all failed
  cutoff pairs;
- support/segment/quality/calendar coverage and `TRIPLE_ONLY_ELIGIBLE` diagnostic counts;
- strict AS_OF and observational statuses kept separate.

The B0 reproduction must reconcile the corrected R04 reference values, including valid cutoff
counts, W1 `10,400 = 8,479 + 1,921`, and active `PRIOR_RAW_VETO` occurrences W1/D1/M30 =
172/939/108. If it does not, stop; do not compare A1 against a drifting baseline.

No return, future-direction, PnL, win-rate, Sharpe, target/RR, optimized score, statistical
significance or trading language is authorized. Prices after each evaluation cutoff may not enter
selection, labelling or judgment.

## 8. Frozen case pack and qualitative inspection

Before AVGO A1 execution, freeze a deterministic case rubric that selects, where available and for
each timeframe:

1. first A1-only endpoint;
2. most-extreme baseline omission restored by A1 under the existing declared comparator;
3. longest unit-gap alternating chain containing an A1-only endpoint;
4. any A1-created consecutive same-kind pair or invariant anomaly; record zero if absent;
5. one `TRIPLE_ONLY_ELIGIBLE` diagnostic boundary, if present, clearly marked non-event.

Deduplicate identical cases deterministically and set a bounded maximum before execution. Charts
must use only completed source candles available at the case cutoff, identify B0 versus A1,
distinguish extreme and confirmation bars, mark predecessor raw/support/calendar edges and contain
no future candle or outcome label. Inspect every selected chart and record an explicit rationale,
including unfavorable or noisy cases. Do not replace zero categories with synthetic real cases;
synthetic counterexamples remain separately labelled.

## 9. Predeclared research decision

Deliver exactly one R05 disposition:

- `RECOMMEND_CROSS_SAMPLE_ONLY`: all integrity/proof invariants pass; every timeframe with valid
  observations has at least one deduplicated restored more-extreme endpoint; the consecutive
  same-kind pair rate does not increase in any timeframe; added unit-gap chains are fully exposed
  and no unexplained/non-veto additions occur. This recommends only a later independent-symbol
  validation contract, not product adoption.
- `REJECT_NO_VETO`: a valid experiment shows that A1 increases the consecutive same-kind pair rate
  in any timeframe, or the complete case review establishes a clear structural failure under the
  frozen rubric.
- `INCONCLUSIVE`: execution is valid but the limited AVGO evidence or mixed predeclared structural
  trade-offs do not satisfy either disposition honestly.

Event-count growth is never a decision criterion by itself. If a hard implementation/evidence
invariant fails, mark the experiment `INVALID` and stop rather than selecting one of the three
research dispositions.

Regardless of disposition, strict historical confirmation and broad market applicability remain
`INCOMPLETE` because this task adds no legitimate historical availability or independent equity.

## 10. Exact permitted file scope

After this immutable contract, implementation may only add files under:

```text
tools/research/paqs_q/r05/
tests/research/paqs_q/r05/
docs/research/PAQS_Q_PRIOR_RAW_VETO_ABLATION_R05.md
docs/evidence/TASK_006B_Q/research-05/
```

No file present at the R05 development base may be modified, renamed or deleted. In particular,
all R04 code/tests/study-01/02/03/audits/charts/reports/freeze material, this contract, prior
research/reviews, `src/`, product tests, dependencies, migrations, configuration, databases and
user data are immutable. Read-only imports of existing pure research helpers are allowed.

If the experiment cannot be implemented additively within this scope, stop and report the blocker.

## 11. Required tests, evidence and protection

Add independent tests for the formulae and every invariant in sections 3, 6 and 7. Tests must cover
W1/D1/M30, US/HK synthetic calendar/session boundaries, both modes, invalid/insufficient inputs,
ties/dual/zero scale, missing and revised support, adjacent opposite raw centers, event-key versus
rule-identity comparison, finite enumeration and deterministic evidence writing. Do not weaken or
rename retained tests.

Run and record exact commands, versions, exit codes and counts:

```text
python -m pytest tests/research/paqs_q tests/unit/test_paqs_input.py -ra
python -m ruff check tools/research/paqs_q/r05 tests/research/paqs_q/r05
python -m ruff format --check tools/research/paqs_q/r05 tests/research/paqs_q/r05
python -m mypy --strict --explicit-package-bases tools/research/paqs_q/r05 tests/research/paqs_q/r05
python -m mypy --strict --explicit-package-bases --platform win32 tools/research/paqs_q/r05 tests/research/paqs_q/r05
git diff --check
```

The retained baseline is 234 passing tests. Add at least 12 focused tests; the final collection must
be at least **246 passed**, with no skip/xfail/deselection introduced. The unchanged Starlette
deprecation warning may remain.

Evidence under `research-05/` must include at minimum:

```text
PLAN.md
freeze.json
REPORT.md
README.md
baseline-reproduction.json
ablation-results.json
endpoint-delta.json
proof-and-enumeration.json
dependency-audit.json
case-review.md
validation.json
protection.json
```

Store full failures and per-cutoff data machine-readably; summaries may not replace them. Evidence
writes use exclusive new paths. Deterministic manifests must sort stored POSIX path strings
explicitly so Windows/Linux path ordering cannot change inventory arrays.

Protection must verify Git mode/type/blob identity for all **611** files at
`c4e21a0204cf6cdd7bb139584b02f01792a49f13` plus this immutable contract: **612 protected
objects**. It must also prove additive path scope, no deletion/rename/symlink/mode change, resolved
relative links, clean index/worktree, linear no-merge ancestry, unchanged product authority and
unchanged review/prior-task branches. At final delivery it must additionally verify mode/type/blob
identity for the frozen PLAN, freeze manifest, R05 research specification, candidate code and tests
from the pre-result freeze commit. Do not claim the external user database was unchanged from a
stale hash; state truthfully that R05 did not access it.

No browser, Uvicorn, PostgreSQL, migration or full product suite is required because R05 is isolated
offline research. Do not claim unrun checks.

## 12. Delivery and stop

`REPORT.md` must be in Chinese and include exact authority/base/review/contract/freeze/final SHAs,
all changed/added paths, mathematical propositions and counterexamples, B0 reproduction, complete
A/B metrics, dependency tax, case findings, disposition, validation, preservation and unchanged
limitations. Separate implementation validity, structural interpretation, market applicability
and product adoption explicitly.

Commit and normally push only `task/006b-q-r05-prior-raw-veto-ablation`. Read back the freeze SHA
before the real run, and read back the final branch SHA/report after delivery. Never force-push,
merge, update `roadmap/no-live-trading` or any R04/review branch, modify prior evidence, access the
user database, start a three-support candidate, implement 006C-Q, or connect the result to product
runtime. Stop for independent review.
