# R04 reproduction and evidence map

Status: research implementation delivered for independent review, not adopted or merged.
Read [REPORT.md](REPORT.md), the immutable [PLAN](PLAN.md), [freeze manifest](freeze.json),
[math/calendar specification](../../../research/PAQS_Q_LOCAL_CERTIFICATE_MARKET_APPLICABILITY_R04.md)
and [proof/clock boundaries](PROOFS_AND_BOUNDARIES.md).

Final results are [study-02 summary](study-02/summary.json), [coverage](study-02/coverage.json),
[source/calendar manifest](study-02/source-calendar-manifest.json), [audit](audit-02.json) and
[case review](CASE_REVIEW.md). Per-mode/frame JSON contains all100 cutoff records, full census
catalogs, event witnesses, actual recognition records and unchanged baseline/H1 hash checks.
Array position in census_ids is window index; use active_start to distinguish warm/active.
More-extreme omissions use the nearest earlier accepted same-kind active event, not ground truth.

[Correction01](CORRECTION_01.md) documents the input-enum defect discovered during evidence
review. study-01/audit-01/charts-01 are retained preliminary outputs. Use
[same-input delta](same-input-delta.json) to compare them; do not treat them as another candidate.

## Inputs and offline execution

Run from this worktree. Python3.12.14; existing project environment has pytest8.4.1, Ruff0.12.9,
mypy1.17.1. No repository dependency/configuration edits. Set PYTHONPATH and MYPYPATH to the
checkout root and src (Windows separator`;`). Original files are outside Git and required for
full reproduction; the committed compact chart cases are not a substitute for full source data.

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONPATH="$PWD/src;$PWD"
$env:MYPYPATH="$PWD/src;$PWD"
python -m tools.research.paqs_q.r04 --data-dir D:/AI_Infra_Quant_Codex_v1/task006b-q-data --calendar-file D:/AI_Infra_Quant_Codex_v1/task006b-q-r04-source/capture-calendar.json --output D:/AI_Infra_Quant_Codex_v1/r04-fresh-reproduction
python -m tools.research.paqs_q.r04.audit --data-dir D:/AI_Infra_Quant_Codex_v1/task006b-q-data --calendar D:/AI_Infra_Quant_Codex_v1/task006b-q-r04-source/capture-calendar.json --study D:/AI_Infra_Quant_Codex_v1/r04-fresh-reproduction --output D:/AI_Infra_Quant_Codex_v1/r04-fresh-audit.json
```

Choose never-existing output paths for each reproduction. Writers use exclusive creation;
never rerun against historical evidence directories. The evaluator, study and audit have no
network/provider/database actions. They verify the three source hashes and calendar export hash
against the immutable freeze. Original cutoffs are copied exactly from R02; no grid or universe
selection occurs at execution time. Price-request budget0, OpenD history0.

Optional explicit archive attestation uses the existing enforced read-only loader, not app startup:

```powershell
python -m tools.research.paqs_q.r04.integrations.attest --database D:/AI_Infra_Quant_Codex_v1/ai_infra_quant_codex_v1/data/ai_infra_quant.db --data-dir D:/AI_Infra_Quant_Codex_v1/task006b-q-data --calendar D:/AI_Infra_Quant_Codex_v1/task006b-q-r04-source/capture-calendar.json --output D:/AI_Infra_Quant_Codex_v1/r04-fresh-normalizer-attestation.json
```

This checks only the authorized Capture's memberships/data against the originals, without
accounts, credentials, migrations, bootstrap or writes. It does not claim a stable whole-database
hash while another process might change that database.

## Static plots

Matplotlib3.11.1 was installed in separate `task006b-q-r04-plot-env`, no dependency-file changes.
Run with its site-packages visible, `MPLBACKEND=Agg`, and a writable task-specific MPLCONFIGDIR.
Agg is the static renderer; Tk is unnecessary. The initial default backend failed because bundled
Tcl init.tcl was unavailable; the first cache path was also unwritable. Explicit Agg/writable cache
resolved both. There is no browser/product frontend requirement in this research contract.

```powershell
$env:MPLBACKEND='Agg'
$env:MPLCONFIGDIR='D:/AI_Infra_Quant_Codex_v1/task006b-q-r04-mpl-cache'
$env:PYTHONPATH="$PWD/src;$PWD;D:/AI_Infra_Quant_Codex_v1/task006b-q-r04-plot-env/Lib/site-packages"
python -m tools.research.paqs_q.r04.charts --cases D:/AI_Infra_Quant_Codex_v1/r04-fresh-reproduction/cases --output D:/AI_Infra_Quant_Codex_v1/r04-fresh-plots
```

All numeric calculations remain Decimal. Float conversion is confined to rendering. Each case
contains at most40 actual candles and the calculation cutoff; selection follows the frozen rubric.
Blue triangles mark accepted extreme bars; purple square is the selected next-bar reversal check;
orange x marks a vetoed row (its vertical offset is not the omitted price); gray tick marks rejected
support. Dotted lines mark session/week/segment changes on an observation-index x-axis, not filled
missing candles. A square on a rejected case does not mean the certificate was accepted.

## Validation

```powershell
python -m pytest tests/research/paqs_q tests/unit/test_paqs_input.py -ra
python -m ruff check tools/research/paqs_q/r04 tests/research/paqs_q/r04
python -m ruff format --check tools/research/paqs_q/r04 tests/research/paqs_q/r04
python -m mypy --strict --explicit-package-bases tools/research/paqs_q/r04 tests/research/paqs_q/r04
python -m mypy --strict --explicit-package-bases --platform win32 tools/research/paqs_q/r04 tests/research/paqs_q/r04
python -m tools.research.paqs_q.r04.verify --output D:/AI_Infra_Quant_Codex_v1/r04-fresh-protection.json
git diff --check
```

Native host is Windows; native and explicit win32 type-check commands are both retained, not
claimed as two OS execution platforms. No original tests/fixtures/parameters/verifiers changed.
