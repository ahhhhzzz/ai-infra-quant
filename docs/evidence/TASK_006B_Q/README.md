# TASK-006B-Q reproducible evidence

Engineering candidate only. Real-market gate **INCOMPLETE**; no production adoption or trading validation.
The [implementation report](../../reports/TASK_006B_Q_IMPLEMENTATION_REPORT.md) explains results and limitations.

## Authority and freeze

- Base: `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`.
- Issued contract: `3e547189fa446bb04913e5fecc73720e424cc240`.
- Pre-diagnostic freeze: `6285fe319e6a1af07715455d404d3ec81bbd640c`.
- Executable implementation: `e67575f3de064f9badb2fd06791e7fc803251bb9`.
- [Profile](profile.json), [fixed universe](universe.json), [protected base tree](protected-base-tree.txt).

## Local reproduction

Use Python 3.12 and repository-declared development dependencies. No new dependency or networking is
needed. Commands run from the repository root. The original run used the existing external environment
`D:\AI_Infra_Quant_Codex_v1\task007c1-env\Scripts\python.exe`; activating an equivalent environment is sufficient.

```powershell
$env:PYTHONPATH="$PWD\src;$PWD"
$env:MYPYPATH="$PWD\src"
python -m pytest tests/research/paqs_q -ra
python -m tools.research.paqs_q example --pattern tight_range --output ../q-example.json
python -m tools.research.paqs_q analyze ../q-example.json --cutoff 2011-03-20T00:00:00Z --output ../q-result.json
```

`qstr-observations-v1` is JSON containing `schema` and `dataset`. The dataset fields and immutable Bar
fields are specified in [types.py](../../../tools/research/paqs_q/types.py); a generated example is the
complete wire template. Prices/volume are decimal strings, UTC times are ISO8601, `available_at` may
be null only with explicit observational treatment. `AS_OF` excludes unknown availability.
`analyze` returns a local JSON file with decision, semantic hash, diagnostics, source-envelope hash
and provenance. Invalid numerical/identity observations return conservative INVALID/UNCERTAIN; malformed
wire input exits 2. No automatic provider initialization occurs.

The user-authorized original database remains at
`D:\AI_Infra_Quant_Codex_v1\ai_infra_quant_codex_v1\data\ai_infra_quant.db`.
The exact retained Capture ID is `2babba19-e0ce-4bfa-aab9-93061a95818c`.

```powershell
python -m tools.research.paqs_q archive --database ../ai_infra_quant_codex_v1/data/ai_infra_quant.db --capture 2babba19-e0ce-4bfa-aab9-93061a95818c --output-dir ../task006b-q-data
python -m tools.research.paqs_q.study --data-dir ../task006b-q-data --output-dir docs/evidence/TASK_006B_Q
python -m tools.research.paqs_q analyze ../task006b-q-data/US.AVGO.M30.json --cutoff 2026-09-01T16:00:00Z --output ../q-avgo-case.json
python -m tools.research.paqs_q benchmark --repeats 10 --output ../q-performance.json
python -m tools.research.paqs_q.verify --output ../q-protection.json
```

`archive` opens SQLite with `mode=ro`, `query_only=ON`, a read snapshot and parameterized queries.
It checks stored Capture/version hashes and membership ownership, and preserves accepted 006A
weekly/M30 aggregation. It does not start the application or contact OpenD. Exports are deliberately
outside Git. Reading another capture requires supplying its explicit ID. Missing files in a study
stay UNAVAILABLE; no synthetic fallback, automatic acquisition or survivor substitution exists.

Only the database owner or a reviewer supplied the exact exported observations can reproduce AVGO
byte for byte. These files are not publicly redistributable bulk data in Git. A later vendor refetch
can revise QFQ history and cannot promise identical observations. See [source manifest](source-manifest.json)
for hashes, exact coverage, retrieval, provider/precision/calendar limitations and retention.

## Reading results

- [Coverage and summary](coverage.json): fixed 40-member denominators; 39 missing members retained.
- [W1 diagnostics](US.AVGO.W1.diagnostics.json), [D1 diagnostics](US.AVGO.D1.diagnostics.json),
  [M30 diagnostics](US.AVGO.M30.diagnostics.json): every scheduled cutoff, all parameter differences
  and all material boundary cases, with four structural projections and reproducible cutoff keys.
- [Boundary case review](boundary-case-review.json): all 12 material LEFT_ONLY cases, including
  UTC dates and replaced/expired references. Operational attribution does not establish economic causality.
- [Synthetic cases](synthetic-cases.json): deterministic examples, explicitly not real-market proof.
  `path_lock` plants an early two-sided ambiguity outside the final bounded window; `relocation`
  illustrates historical levels remaining in the old engine. No price-return optimization.
- [Performance](performance.json): bounded-window timing/memory and actual candidate/comparison counts.
- [Rule matrix](rule-matrix.json): QSTR-001 through QSTR-012 mapped to concrete functions and tests.
- [Validation](validation.json), [protection and local links](protection.json): execution evidence.

For a single boundary case, load the normalized dataset with `read_dataset`, call `prepare(data, cutoff)`,
then call `boundary(data, bars[-params.total-1:], params)` with `Parameters.default(timeframe)`.
OLD/RIGHT/LEFT/BOTH use N/N+1/N-1/N horizons defined in the mathematical specification. The two
modified horizons are diagnostics, not decision outputs. OFAT comparisons ignore config-derived IDs
and compare roles, geometry and bar references. Exact-ID range runs and continuous RANGE runs are separate.

The database and normalized bulk observations, raw logs, existing review evidence, screenshots,
credentials and unrelated workspaces are not included in this evidence directory.
