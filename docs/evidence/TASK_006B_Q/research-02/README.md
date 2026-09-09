# R02 experiment evidence

[Complete report](REPORT.md) · [Frozen plan](EXPERIMENT_PLAN.md) · [Freeze manifest](freeze.json)
· [Mathematics](../../../research/PAQS_Q_STRUCTURE_R02_CANDIDATES.md)

- Phase A: [12 causal records](phase-a-cases.json), [100-row D1 census](phase-a-d1-census.json),
  [separation-gate traces](phase-a-separation.json).
- Comparison: [summary](comparison/summary.json), [W1](comparison/US.AVGO.W1.comparison.json),
  [D1](comparison/US.AVGO.D1.comparison.json), [M30](comparison/US.AVGO.M30.comparison.json),
  [timing/memory](comparison/performance.json).
- Final interpretation: [six H1 geometry cases](refined-causes/h1-geometry-causes.json),
  [synthetic rejection](refined-causes/h1-rejection-counterexample.json).
- [Public-access attempt](acquisition-attempt.json), [coverage and access disposition](coverage.json),
  [validation](validation.json), [protected identities](protection.json).

The first comparison's `material-causes.json` event-only `cause` label was overbroad when common
pivot events were unchanged. Do not read it as proof of geometry expiry. The additive refined
geometry evidence is the final explanation. Earlier outputs and original evidence are retained.

## Reproduction

Use the existing declared Python 3.12 environment; no production dependency/config change.
From the R02 checkout in PowerShell:

```powershell
$env:PYTHONUTF8="1"
$env:PYTHONPATH="$PWD\src;$PWD"
$env:MYPYPATH="$PWD\src"
python -m tools.research.paqs_q.r02.phase_a --data-dir ../task006b-q-data --output-dir ../r02-phase-a-new
python -m tools.research.paqs_q.r02.compare --data-dir ../task006b-q-data --output-dir ../r02-comparison-new
python -m tools.research.paqs_q.r02.explain --data-dir ../task006b-q-data --comparison-dir ../r02-comparison-new --output-dir ../r02-explanations-new
python -m tools.research.paqs_q.r02 evaluate --input ../task006b-q-data/US.AVGO.D1.json --cutoff 2026-09-08T20:00:00Z
python -m pytest tests/research/paqs_q -ra
python -m pytest tests/unit/test_paqs_structure.py tests/unit/test_paqs_input.py tests/integration/test_paqs_structure_api.py tests/integration/test_paqs_input_api.py tests/architecture/test_task006a_boundaries.py tests/architecture/test_task006b_boundaries.py -ra
python -m ruff check tools/research/paqs_q/r02 tests/research/paqs_q/r02
python -m ruff format --check tools/research/paqs_q/r02 tests/research/paqs_q/r02
python -m mypy --strict --explicit-package-bases tools/research/paqs_q/r02 tests/research/paqs_q/r02
python -m mypy --strict --explicit-package-bases --platform win32 tools/research/paqs_q/r02 tests/research/paqs_q/r02
python -m tools.research.paqs_q.r02.verify --output ../r02-protection-new.json
git diff 47e7020609e5655927c6aac11a3b1f35b03c96aa --check
```

Choose fresh output paths: writers refuse to overwrite evidence. All financial input values use
the existing `qstr-observations-v1` string-decimal format. The three exact AVGO files are retained
locally outside Git at `D:/AI_Infra_Quant_Codex_v1/task006b-q-data/`. Their required hashes are in
freeze.json. The original read-only normalization command and Capture binding remain in the
[original report](../../../reports/TASK_006B_Q_IMPLEMENTATION_REPORT.md) and
[source manifest](../source-manifest.json). Reviewers without those observations cannot reproduce
the real-market calculation from hashes alone; synthetic tests need no user data.

Explicit public-path recheck only (not part of normal evaluation/tests):

```powershell
python -m tools.research.paqs_q.r02.integrations.public_attempt --output ../r02-public-new.json --raw-dir ../r02-public-raw-new
```

It uses fixed public documentation/download-discovery URLs and the provider-published literal
demo key, never a user credential. Availability and terms may change; a fresh attempt is new evidence,
not a guarantee of byte-identical history. No normalized extra equity was accepted in this run.
Do not bypass challenges or subscriptions, fabricate calendars, or replace missing M30 with daily data.
