# R03 reproduction and evidence map

[Report](REPORT.md), [frozen plan](PLAN.md),
[mathematics/proof register](../../../research/PAQS_Q_CONFIRMATION_AND_ROLLING_STABILITY_R03.md).
Every generated observation is SYNTHETIC. No user DB, market API, OpenD or credentials are needed.
Do not rerun prior acquisition/market commands. AVGO references are committed-summary references only.

## Environment and commands

Use the repository's already-declared development dependencies. Recorded environment:
Windows / Python3.12.14, pytest8.4.1, Ruff0.12.9, mypy1.17.1. Work from the R03 checkout;
the exact development base, contract and freeze commits must exist for the preservation check.
In PowerShell, set `PYTHONPATH` to `<checkout>/src;<checkout>` and `MYPYPATH` to `<checkout>/src`.
In POSIX, use `PYTHONPATH=src:.` and `MYPYPATH=src`. No installation/configuration changes required
when the existing project environment is available.

```text
python -m tools.research.paqs_q.r03.witnesses --output docs/evidence/TASK_006B_Q/research-03/recheck-new
python -m pytest tests/research/paqs_q -ra
python -m ruff check tools/research/paqs_q/r03 tests/research/paqs_q/r03
python -m ruff format --check tools/research/paqs_q/r03 tests/research/paqs_q/r03
python -m mypy --strict --explicit-package-bases tools/research/paqs_q/r03 tests/research/paqs_q/r03
python -m mypy --strict --explicit-package-bases --platform win32 tools/research/paqs_q/r03 tests/research/paqs_q/r03
python -m tools.research.paqs_q.r03.verify --output docs/evidence/TASK_006B_Q/research-03/recheck-new/protection.json
git diff ddb61c15f1aea026b26c116f35fa1e2b0b0d055a --check
```

Choose an unused `recheck-new` name. The witness command requires a fresh directory and JSON writers
open files exclusively; the verifier also requires a new output filename. Do not overwrite run-01,
validation, report, freeze, or any older evidence. Enumeration checks its 120-second budget and
reports actual count/INCOMPLETE if not finished; its regression requires the complete declared domain.
Elapsed time is environment-dependent and excluded from mathematical equivalence claims.

The complete suite includes retained132 + new36 tests. No product runtime dependency changed;
business/browser/Uvicorn/database suites are outside this contract's required validation and unexecuted.
One inherited Starlette/AnyIO deprecation warning is recorded; no skip/xfail is used.

## Evidence files and claims

| File | Scope |
|---|---|
| [PLAN.md](PLAN.md) | Commit2e048607414021e12984871db3a888cba7f20557, before new comparisons; models/domain/reject criteria |
| [run-01/witnesses.json](run-01/witnesses.json) | Exact retained H1 diagnostic equality/hash and13 timed events; trap/mirror; ATR; both local views and history-origin counterexample |
| [run-01/enumeration.json](run-01/enumeration.json) | 19683 synthetic words, actual0.411s, original/support metrics, no market claim |
| [validation.json](validation.json) | Actual argv/stdout/stderr/exit codes for168 research tests and required static commands |
| `protection-final.json` | All465 base mode/type/blob identities plus issued contract and frozen PLAN; additions/links/diff |

The verifier protects every old file, not selected folders only; it compares committed mode/type/blob
and filtered worktree blob, rejects non-additive diffs and paths outside the R03 allowlist, and resolves
local file links. Its own fresh output is created after the scan, so that output's filename is not in
its just-computed additions list; a final read-only rerun after staging checks the complete tree.
No external user database hash is claimed. Link checks resolve files, not remote page contents.

The retained H1 JSON is independently regenerated in memory and compared in full; run-01 stores a
compact equality/hash plus timed events rather than a second copy of the large prior diagnostic.
R02 four-bar constant ATR and fixed-distance EMA tests are labelled diagnostic interventions; they
do not change the original ATR convention. M1 is a four-observation finite certificate, M2 an explicit
in-memory history comparator. Neither is a Structure Engine or authorized production contract.
