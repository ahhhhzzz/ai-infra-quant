# Focused F01/F02 remediation evidence

[Report](REPORT.md) · [Contract](CONTRACT.md) · [Rule matrix](rule-matrix.json)

- [Synthetic same-input before/after](reproducer-before-after.json): old review assertions were
  executed before changes; corrected expectations come from new dedicated tests.
- [AVGO before/after](real-before-after.json): identical normalized input hashes, zero changes in
  274 valid decisions and original material projections; expanded time checks remain observational.
- [Corrected coverage](corrected-study/coverage.json), [W1](corrected-study/US.AVGO.W1.diagnostics.json),
  [D1](corrected-study/US.AVGO.D1.diagnostics.json), [M30](corrected-study/US.AVGO.M30.diagnostics.json).
- [Validation](validation.json) · [Protected identities](protection.json).

Use the repository-declared Python 3.12 development environment. From repository root:

```powershell
$env:PYTHONUTF8="1"
$env:PYTHONPATH="$PWD\src;$PWD"
$env:MYPYPATH="$PWD\src"
python -m pytest tests/research/paqs_q -ra
python -m pytest tests/unit/test_paqs_structure.py tests/unit/test_paqs_input.py tests/integration/test_paqs_structure_api.py tests/integration/test_paqs_input_api.py tests/architecture/test_task006a_boundaries.py tests/architecture/test_task006b_boundaries.py -ra
python -m ruff check tools/research/paqs_q tests/research/paqs_q
python -m ruff format --check tools/research/paqs_q tests/research/paqs_q
python -m mypy --strict --explicit-package-bases --platform win32 tools/research/paqs_q tests/research/paqs_q
python -m tools.research.paqs_q.verify --output ../remediation-base-check.json
python -m tools.research.paqs_q.study --data-dir ../task006b-q-data --output-dir ../remediation-study-recheck
```

Use a fresh output directory: do not target the original evidence directory or overwrite committed
remediation evidence. The same raw observations are required for identical AVGO decisions; normalized
files remain outside Git and match hashes in the original frozen evidence. No OpenD history calls
or database changes are required. Missing inputs remain missing, never synthetic substitutes.

For the review counterexample, use `test_later_revision_keeps_old_identical_and_marks_confounded`:
the original dataset plus the later version must be passed to both `evaluate` and `boundary`.
The selected N+1 argument identifies the transition only. Inspect `arm_decision_hashes`,
`information_change` and all `availability_checks`; zero violations with OBSERVATIONAL_UNKNOWN
does not establish historical information-set safety.

The source review remains on exact commit `e4bf4cb6092e48c98732bd7d355d31affbf8a332`, never merged
or edited. The [original report](../../../reports/TASK_006B_Q_IMPLEMENTATION_REPORT.md),
[profile](../profile.json) and [universe](../universe.json) remain historical immutable evidence.
