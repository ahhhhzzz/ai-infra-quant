# TASK-006B-Q F01/F02 — Independent focused re-review

Verdict: **PASS for focused remediation. F01 CLOSED; F02 CLOSED.**

New findings: **0 Critical / 0 Major / 0 Minor** within this focused scope.

Reviewed exact implementation: `d50d73eea28005bc96e5ed0721b6a8e385ecedf5`.

Remediation start: `a29d2d6e0195ed4509cfa8daa9223a41c3d6fcf0`.

Authority remains `roadmap/no-live-trading` at `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`.

Original [independent review](https://github.com/ahhhhzzz/ai-infra-quant/blob/e4bf4cb6092e48c98732bd7d355d31affbf8a332/docs/reviews/TASK_006B_Q_INDEPENDENT_REVIEW.md)
and [synthetic reproducers](https://github.com/ahhhhzzz/ai-infra-quant/blob/e4bf4cb6092e48c98732bd7d355d31affbf8a332/docs/reviews/evidence/task006b_q_reproducers.py)
remain immutable historical evidence. This report supersedes only their F01/F02 OPEN dispositions.

Reviewed against the owner's focused remediation instruction and the additive
[contract](../evidence/TASK_006B_Q/remediation-01/CONTRACT.md),
[implementation report](../evidence/TASK_006B_Q/remediation-01/REPORT.md) and candidate section 14.
Task branch SHA was independently read back from GitHub before a fresh detached checkout was created.
Review date: 2026-09-09.

## 1. Focus and method

This is a focused re-review of the two reported defects and their regression surface, not a fresh
full-market semantic review or approval of the entire PAQS-Q strategy. Read the changes to engine,
diagnostics, study, new temporal helpers, two new test modules, candidate clarification and contract.
Previously read current governance and original contracts are retained at unchanged base identities.

No engineer file, original evidence, production path, parameter or database was modified. The only
new tracked file on this review branch is this report. Tests used an existing isolated Python
environment with the reviewed checkout explicitly placed on PYTHONPATH.

## 2. Finding dispositions

### 006B-Q-F01 — CLOSED

`quality_error` now validates per-bar COMPLETE/PARTIAL/UNKNOWN vocabulary and the declared aggregate
consistency policy. Invalid values/types are rejected; aggregate quality cannot be more certain than
the used bar. Valid D1 partial/unknown evidence retains its conservative status. Normalization selects
the latest available version before derived-coverage exclusion, so a newer partial W1/M30 revision
does not silently resurrect an earlier complete version. Future, unavailable and unfinished records
remain excluded before irrelevant quality payloads are interpreted.

Independently reran the original all-bar counterexample, without modifying fixtures or the original
review script: 440 synthetic bullish D1 observations, each with coverage INVALID. Result changed from
COMPLETE/BULL_TREND to **INVALID/UNCERTAIN**, reason `BAR_COVERAGE_INVALID`.

The 35 new quality cases also pass independently: invalid enum/type values across D1/W1/M30, aggregate
contradictions, valid conservative statuses, public evaluate, JSON round trip, actual CLI, future-data
isolation and derived-version selection. These are research input checks, not evidence that actual
AVGO bars were invalid or that market completeness was certified.

### 006B-Q-F02 — CLOSED

`boundary` retains the raw versioned dataset, checks its transition sequence against selection at the
new cutoff, independently evaluates OLD and BOTH, and builds LEFT from the old information set.
RIGHT selects versions at the new cutoff. Low-level `calculate_window` rejects records completed or
explicitly available after its own cutoff and rejects unknown availability in AS_OF mode.

Historical revision, newly available historical key and missing-key changes are recorded separately
and force `REVISION_CONFOUNDED`. Missing OLD history and nonconforming RIGHT horizons remain explicit
instead of fabricating earlier records or changing the strategy horizon. `boundary_case_lists`
separates revision-confounded records from material LEFT_ONLY cases.

Independently reconstructed the original 313-bar synthetic bullish D1 counterexample: index 290 has
a High=9999 revision first available at the new cutoff. Corrected behavior:

| Check | Independent result |
|---|---|
| Normal OLD with/without the future revision | Identical decision bytes |
| Boundary OLD vs independent OLD | Identical structural projection and semantic hash |
| OLD active Pivot count | 21, rather than the defective 19 |
| Diagnostic attribution | REVISION_CONFOUNDED |
| All four actual arm-input time violation counts | 0 |

Ten new temporal tests pass independently, covering revision arrival, unchanged-price later versions,
delayed historical data, missing earlier versions, unmodified input, future invalid payloads, unknown
observational availability and warm-up input auditing. The zero count now checks all used inputs,
including warm-up, rather than just the current Pivot confirmation references. Unknown observation
availability remains explicitly unverified and is not converted to point-in-time certification.

## 3. Independent execution

Environment: Linux, Python 3.12.14, pytest 8.4.1; existing repository development dependencies.

| Check | Result |
|---|---|
| All research tests | 97 passed |
| Same six existing structure/input/API/architecture regression files | 59 passed |
| Combined pytest run | **156 passed, 1 warning in 7.55s** |
| Original F01/F02 inputs with corrected expectations | Both pass |
| Ruff check | PASS |
| Ruff format check | PASS, 20 files |
| Strict mypy, explicit package bases, Windows target | PASS, 20 source files |
| Diff check from remediation start | PASS |
| Existing task verification utility | PASS |
| Independent exact-tree/strategy-function preservation | PASS |

The only pytest warning is the existing Starlette/AnyIO BlockingPortal alias deprecation. No skip,
xfail or weakening of the original 52 research tests was introduced. Unrelated browser/full-business/
Uvicorn checks were not run, as allowed by the research-only contract; no product startup claim is made.

Commands, run from the reviewed checkout with PYTHONPATH=src:. and MYPYPATH=src:

```text
python -m pytest tests/research/paqs_q tests/unit/test_paqs_structure.py tests/unit/test_paqs_input.py tests/integration/test_paqs_structure_api.py tests/integration/test_paqs_input_api.py tests/architecture/test_task006a_boundaries.py tests/architecture/test_task006b_boundaries.py -ra
python -m ruff check tools/research/paqs_q tests/research/paqs_q
python -m ruff format --check tools/research/paqs_q tests/research/paqs_q
python -m mypy --strict --explicit-package-bases --platform win32 tools/research/paqs_q tests/research/paqs_q
python -m tools.research.paqs_q.verify --output <scratch>/006b-q-r1-independent-protection.json
git diff --check a29d2d6e0195ed4509cfa8daa9223a41c3d6fcf0 HEAD
```

## 4. Preservation and real-evidence limits

Compared Git mode/type/blob independently, not just the implementer's manifest:

- All 377 authority-base files are unchanged.
- 408 of the 412 files at the remediation start are unchanged. The four modified existing files are
  engine.py, diagnostics.py, study.py and the candidate document; 17 additions fall within the
  authorized research/test/remediation evidence paths.
- ATR, Pivot, labels and Regime function ASTs are unchanged. zones.py, types.py, fixtures, original
  tests, profile/universe, original reports/diagnostics, production code, dependencies and migrations
  are unchanged. The original issued contract remains unchanged.

Independently compared original and corrected committed diagnostic JSON at every scheduled row:
cutoff/status/decision hash/Regime/structure status/input status/boundary classification agree, and
all original material four-arm structural projections agree. Valid endpoints total **274**:
W1=100, D1=100, M30=74. This is a comparison of submitted artifacts, **not a real-market rerun**.

The user's Windows database and normalized AVGO files are not present in this review environment.
Their unchanged hashes and the real-data regeneration are implementer-reported evidence; this review
does not independently certify the database or recompute AVGO source aggregation. The synthetic
regressions and source inspection independently validate the two fixes without needing that database.

## 5. Remaining status and next boundary

| Item | Status |
|---|---|
| F01/F02 focused correctness | PASS / both CLOSED |
| New findings in this focused review | 0 Critical / 0 Major / 0 Minor |
| Real-market coverage | INCOMPLETE: only AVGO; other 39 members absent; M30 short of 100 endpoints |
| Existing 12 material LEFT_ONLY cases | Retained; semantic interpretation/stability unresolved |
| D1 UNCERTAIN 96/100, W1 parameter sensitivity, no real RANGE | Existing research limitations retained |
| Overall structural robustness / parameter adoption | NOT ACCEPTED |
| Predictive/trading performance | NOT EVALUATED |
| Merge, product integration, 006C-Q | Not authorized by this review |

These two engineering defects no longer block their focused remediation acceptance. They are distinct
from the known candidate design issues. The next separately scoped decision should address structural
seed/window sensitivity and the validation-data shortfall. Do not silently tune parameters, introduce
smoothing, claim whole-task semantic PASS or start the event engine from this focused result.
