# TASK-006B-Q — Independent review

Verdict: **NEEDS REVISION — 0 Critical / 2 Major / 0 Minor.**

Reviewed implementation: `a29d2d6e0195ed4509cfa8daa9223a41c3d6fcf0`.

Issued contract: `3e547189fa446bb04913e5fecc73720e424cc240`.

Authority/base: `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f` on `roadmap/no-live-trading`.

Review date: 2026-09-09. Review performed on an isolated checkout fetched from GitHub. The task
branch was read back at the implementation above; the user's push succeeded. The report's final
`BLOCKED_BY_NETWORK` paragraph is preserved as historical delivery evidence and is superseded by
this readback, not treated as a new finding.

## 1. Scope and independent verification

Reviewed the issued contract/candidate and executable 1.1 clarification, all prototype modules and
dedicated tests, allowlist/protection tooling, report, frozen universe/profile, coverage and the
four-arm boundary evidence. Current governance was already read at the unchanged base; baseline
Git identities were independently compared again.

- All 377 existing base files retain mode/type/blob. The reviewed tree has 412 files. Changes from
  the issued contract are 34 files and remain inside its allowlist. The issued contract is unchanged.
- Implementation history is contract -> profile/universe freeze `6285fe3` -> code/tests `e67575f`
  -> evidence `ea127e5` -> network disclosure `a29d2d6`. No return-optimized parameters were found.
- The Q engine implements its own Pivot sequence; the old engine is invoked for diagnostic
  comparisons only. No production import/wiring or product/DB/migration change was found.
- Independently executed **111 passed, 1 warning** on Linux/Python 3.12.14: 52 research tests plus
  59 existing structure/input/API/architecture regressions. Existing Starlette/AnyIO deprecation only.
- Ruff check and format: PASS, 17 files. Strict mypy with explicit package bases and Windows target:
  PASS, 17 files. Task verification tool: PASS, including 377 protected paths, 12 rule mappings and
  26 local links. Existing source code was not changed to obtain these results.
- Two independent synthetic counterexamples below reproduce despite those test passes.

Commands (from the reviewed checkout, using an existing environment and `PYTHONPATH=src:.`):

```text
python -m pytest tests/research/paqs_q tests/unit/test_paqs_structure.py tests/unit/test_paqs_input.py tests/integration/test_paqs_structure_api.py tests/integration/test_paqs_input_api.py tests/architecture/test_task006a_boundaries.py tests/architecture/test_task006b_boundaries.py -ra
python -m ruff check tools/research/paqs_q tests/research/paqs_q
python -m ruff format --check tools/research/paqs_q tests/research/paqs_q
MYPYPATH=src python -m mypy --explicit-package-bases --platform win32 tools/research/paqs_q tests/research/paqs_q
python -m tools.research.paqs_q.verify --output <scratch>/006b-q-independent-protection.json
python docs/reviews/evidence/task006b_q_reproducers.py
```

The last script is new reviewer evidence on this review branch. It pins observed failures at the
reviewed SHA; its assertions are not the required post-remediation expectations. Production files,
engineer tests, report and original evidence remain unchanged by this review.

## 2. Findings

### 006B-Q-F01 — Major — invalid D1 coverage can produce a clean directional result

Locations: [engine.prepare and validate_window](../../tools/research/paqs_q/engine.py),
`calculate_window` input-status assignment; [wire parser](../../tools/research/paqs_q/io.py).

`prepare` filters non-COMPLETE W1/M30 bars, but D1 coverage is not checked. `validate_window` validates
financial/time/identity fields but neither validates coverage values nor reconciles bar quality with
aggregate quality. `calculate_window` directly copies `data.quality` to `input_status`.

Reproduction: create the supplied 440-bar synthetic bullish dataset; replace every D1 bar's coverage
with `INVALID`, leaving the aggregate quality `COMPLETE`; call public `evaluate`. Actual result:

```json
{"input_status":"COMPLETE","structure_status":"DIRECTIONAL_EVIDENCE","regime":"BULL_TREND","warnings":[]}
```

This is an internally inconsistent input, which the boundary must reject conservatively; if INVALID
is outside the bar coverage vocabulary, that is itself a schema error, not permission to analyze it.
The wire format also accepts the string unchanged, so this is reachable from a local JSON input,
not merely a helper-only financial oracle.

Impact: invalid/malformed bar-quality evidence can be presented as clean completed evidence and
establish directional structure. Violates QSTR-004/QSTR-008 and candidate sections 3, 9 and 13.2.
It does not show that the actual AVGO capture was invalid or that current product behavior changed.

Required remediation: explicitly validate allowed per-bar quality/coverage states and define the
aggregate consistency policy. Reject invalid/unknown-enum/conflicting quality as typed
INVALID/UNCERTAIN, or preserve legitimate PARTIAL/UNKNOWN status under a documented policy without
upgrading it. Keep future/unavailable records excluded before validating their irrelevant price
payloads. Add public evaluator and wire-path regressions; no fixture-wide relabelling to COMPLETE.

### 006B-Q-F02 — Major — boundary OLD/LEFT calculations can consume later-available revisions

Locations: [diagnostics.audit and boundary](../../tools/research/paqs_q/diagnostics.py),
[calculate_window](../../tools/research/paqs_q/engine.py).

At each terminal `audit` selects latest versions with `prepare(data, cutoff)` and passes the selected
N+1 bars into `boundary`. `boundary` replaces its dataset with those selected versions and calls
`calculate_window` for OLD and LEFT at the prior cutoff. That low-level function does not reselect
versions or reject `available_at` after its cutoff; earlier versions have already been discarded.

Independent AS_OF reproduction: use a 313-bar synthetic bullish D1 dataset; add a version for index
290 with High=9999 and `available_at` equal to the final bar's completion, later than OLD's cutoff.

| Check | Observed |
|---|---|
| Public evaluate at OLD cutoff, with vs without the revision | Identical (correct) |
| Actual OLD active Pivot count | 21 |
| Boundary OLD active Pivot count | 19 |
| Boundary OLD equals actual OLD structure | False |
| Audit `future_references` | 0 |

The future revision changes ATR/Pivot reconstruction inside OLD even though the normal evaluator
correctly excludes it. `future_references` inspects only current active-Pivot confirmation completion
times; it does not detect the later availability used in old diagnostic arms. Therefore a zero value
cannot certify the four-arm experiment's temporal integrity.

Impact: diagnostics can attribute differences to rolling history using an OLD state that never
existed at the old information cutoff. Violates QSTR-002/QSTR-009 and the fixed-cutoff/availability
contracts. This finding concerns diagnostic revision handling, not a demonstrated failure of normal
`evaluate` cutoff isolation. The supplied single-capture observational AVGO sample has no such
version stream, so this counterexample does not by itself invalidate its 12 cases.

Required remediation: retain the original versioned dataset and make OLD match independently
evaluated old-cutoff evidence. Freeze each arm's availability/cutoff policy before ablation. Treat
new revisions as new information separately, or report the transition as revision-confounded/
unresolved rather than silently reusing them in OLD/LEFT. Cover additions, revisions, delayed
availability and missing prior versions. Audit evidence availability across all arms, not only
completed times of current pivots; preserve distinctions between legitimate observational studies
and AS_OF information-set claims.

## 3. Real-market and semantic assessment

The raw Windows SQLite database and normalized AVGO files were **not available to this reviewer**.
No independent claim is made that the database hash stayed unchanged, that archival normalization
was rerun on the real capture, or that real-market outputs were recomputed. Source access remains
the owner's reported read-only experiment. No OpenD or external market research requests were made.

The committed report and diagnostic JSON were cross-checked independently:

| Timeframe | Valid endpoints | BULL / BEAR / RANGE / UNCERTAIN | Material LEFT_ONLY cases |
|---|---:|---|---:|
| W1 | 100 | 13 / 0 / 0 / 87 | 4 |
| D1 | 100 | 4 / 0 / 0 / 96 | 1 |
| M30 | 74 | 20 / 3 / 0 / 51 | 7 |

All 12 case references match their committed four-arm records: OLD=RIGHT, LEFT=BOTH and OLD!=BOTH.
This verifies internal evidence consistency, not the correctness of original raw-data calculations.
Examples where recent M30 pivots disappear and reappear on adjacent cutoffs, and the April W1
pivot reappears/disappears in August, warrant further seed/window analysis; they are not explained
merely by an old active pivot reaching expiry. No direct BULL-to-BEAR flip is required for such
instability to matter.

D1 UNCERTAIN at 96/100 is not automatically an implementation defect: it is consistent with the
candidate's conservative rules and disclosed by the implementer. It makes low churn weak evidence
of useful structural classification. No observed RANGE means zero zone/range parameter disagreement
is uninformative about robustness. W1 lambda=1.9 disagrees on Regime at 35/100 endpoints, reinforcing
the need for broader structural review rather than declaring the parameters accepted.

The fixed 40-security denominator was retained. Only AVGO was supplied; M30 has 74 rather than 100
valid endpoints. Under contract section 4, truthful incomplete market coverage is a permitted
research delivery outcome, **not an additional engineering finding**, but the real-market gate
remains INCOMPLETE. Likewise, disclosed candidate boundary sensitivity is an adoption concern;
this review does not authorize changing thresholds, adding smoothing or optimizing returns.

## 4. Disposition

| Gate | Verdict |
|---|---|
| Delivery to GitHub | CONFIRMED at a29d2d6 |
| Scope / production preservation | PASS |
| Existing automated checks | PASS within the independently executed scope |
| Independent engineering correctness | NEEDS REVISION: F01/F02 OPEN |
| Real-market coverage | INCOMPLETE |
| Structural robustness / semantic adoption | NOT ACCEPTED; known sensitivity unresolved |
| Predictive/trading performance | NOT EVALUATED |
| Merge / product wiring / 006C-Q | DO NOT PROCEED |

Recommended next action is focused remediation of F01/F02 on the original task branch, with
reproducible regression evidence and a separate remediation report. Preserve this review, original
report/diagnostics, fixed profile/universe, contract and all production baselines. Regenerate any
affected evidence as a new explicitly labelled artifact rather than rewriting original evidence.
Do not expand the market sample or change the strategy rules merely to hide these defects. After
focused re-review, separately decide how to resolve the known semantic issues and incomplete sample.
