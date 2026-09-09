# TASK-006B-Q R02 — Independent Review

Review date: 2026-09-09. Exact implementation reviewed:
`ddb61c15f1aea026b26c116f35fa1e2b0b0d055a` on
`task/006b-q-r02-structure-stability`.

Contract: `47e7020609e5655927c6aac11a3b1f35b03c96aa`.
Development base: `d50d73eea28005bc96e5ed0721b6a8e385ecedf5`.
Frozen hypothesis/Phase A: `251f2a2ea9609ddd875c5aff03f5758c81914c84`.
Candidate implementation: `36357c99809f44756c27035060edc3801d94ef67`.
Product authority read back during review:
`roadmap/no-live-trading` at `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`.

## 1. Verdict

**R02 research delivery: PASS. No new blocking findings identified in this review.**

**H1 as a stable replacement: REJECT. Real-market completeness: INCOMPLETE.
Product adoption: NOT AUTHORIZED.**

本轮完成了合同要求的诊断、冻结假设、独立候选实现、同输入对照及反证。
H1 确实处理了不合格极值长期占据候选位置的机制；但滚动窗口仍能使已在旧 cutoff
之前确认的 13 个 Pivot 重新出现，因此不能宣告结构稳定性通过。拒绝候选是本合同
允许的有效研究结论。保留基线用于研究对照，不代表接受基线的已知结构语义问题。
006B-Q 整体尚未达到产品采用门槛，也不因此启动 006C-Q。

## 2. Scope and preservation

Reviewed the issued contract, frozen mathematics/plan, all added Python, dedicated tests,
submitted causal traces, comparison records, refined causes, acquisition manifest and report.
The reviewed checkout was clean before adding this separate review and its read-only checks.

Independent Git tree comparison confirms all **429** development-base file mode/type/blob
identities are unchanged. The issued contract and six frozen documents are unchanged. There are
35 implementation additions after the contract (36 additions relative to the development base,
including that contract), all inside its allowed paths. The task verifier also passes and resolves
40 local documentation links. Existing runtime, dependencies, migrations, strategy parameters,
original research/tests/evidence and historical documentation retain their original blobs.
The user database and other Windows files were not accessible or touched by this reviewer;
their preservation hashes remain implementer evidence, not an independent filesystem check.

This review adds only this document and
[read-only review checks](evidence/task006b_q_r02_checks.py) on a separate review branch.
It does not modify the implementation branch or product authority.

## 3. Candidate and diagnostic assessment

H1 explicitly defines admissibility as `i - previous_extreme >= 2`. After a confirmation it
initializes the opposite candidate from the confirmation bar only when admissible; otherwise
it waits for the first admissible observation. Ties retain the earliest admissible extreme.
Same-bar confirmation remains forbidden. The mirrored four-bar oracle confirms HIGH at
extreme 0 / confirmation 1 and LOW at extreme 2 / confirmation 3, while the baseline remains
trapped on the ineligible LOW at index 1. The changed meaning of an extremum is disclosed:
the more extreme intervening price at `s+1` may be excluded from the candidate domain.

The candidate recomputes its own pivots and downstream geometry, reusing unchanged pure
ATR/labels/zones/range/regime helpers. It does not relabel a baseline result. Its rule/config
identity is separate; numerical profiles and active-evidence gates are unchanged. Reviewed
F01 coverage validation and F02 cutoff-specific version selection survive in the candidate.
Tests exercise malformed quality, future malformed revisions, missing historical versions,
all-arm evidence times, active expiry, insufficient history and surrounding Decimal contexts.

The 12 submitted baseline cases distinguish 8 seed-path, 2 legitimate active-expiry and
2 interacting/unresolved outcomes. The diagnostic trace asserts agreement with actual pivot
events and applies labelled seed/ATR interventions. The D1 census includes all 100 endpoints:
96 lack sufficient active two-sided history; 4 have directional evidence. Its separation
diagnosis provides a concrete mechanism for H1 without treating every UNCERTAIN as an error.

Six remaining H1 D1 material LEFT_ONLY records have refined ATR-geometry diagnostics.
Their submitted controls restore OLD geometry when holding OLD ATR, with reported maximum
bound movement of approximately `2.13e-16 ATR`. The inherited exact range comparison still
flags them; no tolerance was changed to hide them. Original event-only causal labels are
explicitly superseded by `refined-causes`, whose submitted geometry equalities were checked.
That distinction is necessary: unchanged common pivots alone do not prove geometry changed
only because of active expiry. Fresh market recomputation was not possible here.

## 4. Evidence reconciliation and rejection

Independently reconciled all 300 frozen scheduled cutoffs (including 26 insufficient M30
endpoints), all **274** valid baseline decision hashes against remediation-01, and per-row
event counts/partitions against the submitted structural projections and summaries.

| Frame | Baseline losses / opportunities | H1 losses / opportunities |
|---|---:|---:|
| W1 | 9 / 556 | 0 / 987 |
| D1 | 0 / 147 | 0 / 2454 |
| M30 | 58 / 870 | 0 / 2066 |

An opportunity is an OLD pivot whose extreme and confirmation remain in the next active
window. Identity includes kind, price, extreme ref and confirmation ref, excluding algorithm
IDs. Expired pivots and new confirmations are counted separately. Denominators differ because
the algorithms produce different event sets; these are development-sample descriptive rates,
not matched independent trials or statistical proof of robustness. AVGO informed the hypothesis.

**Independently reproduced the complete saved synthetic rejection diagnostic exactly.**
For the 201-bar M30 `path_lock` fixture, H1 produces no active pivots at the old cutoff;
the next bounded evaluation contains **13** active pivots, all confirmed before the new
rightmost bar and already before the old cutoff. The first wide positive-ATR seed bar leaves
both UNSEEDED reversal predicates true. Shifting the seed domain removes that ambiguity and
reconstructs old structure. The saved seed/ATR interventions classify this as `SEED_PATH`.
The executable review check verifies the exact diagnostic plus the public evaluator outputs.

This is the predeclared rejection condition, not an unreported failing test. H1 still retains
the original dual-ambiguity rule. Lower UNCERTAIN, no observed AVGO loss, or fewer material
LEFT_ONLY cases cannot override this counterexample. Parameter sensitivities and D1 geometry
changes remain disclosed rather than optimized away.

## 5. Independent validation and limits

Review environment: Linux, Python 3.12.14, pytest 8.4.1; explicit `PYTHONPATH=src:.` resolves
the reviewed checkout. Results:

- **191 passed, 1 warning in 10.52s**: 132 research tests (97 retained + 35 R02), plus the
  same 59 structure/input/API/architecture regressions. No skips or xfails.
- Ruff check and format check pass for all 12 added Python files.
- Strict mypy with Windows target passes for all 12 added Python files.
- Exact protected-tree/freeze/allowlist checks, 40 local links and task diff check pass.
- Separate review script reproduces the 13-pivot synthetic counterexample and reconciles
  the submitted metrics, baseline hashes and six geometry controls.

The single warning is the existing Starlette/AnyIO BlockingPortal deprecation. No browser,
full unrelated business suite, Uvicorn restart or database test is claimed for this isolated
research review; the R02 contract does not require them.

Reproduction from a checkout containing this review, using an environment with project test
dependencies and the referenced commits available:

```bash
PYTHONPATH=src:. python -m pytest tests/research/paqs_q tests/unit/test_paqs_structure.py tests/unit/test_paqs_input.py tests/integration/test_paqs_structure_api.py tests/integration/test_paqs_input_api.py tests/architecture/test_task006a_boundaries.py tests/architecture/test_task006b_boundaries.py -ra
python -m ruff check tools/research/paqs_q/r02 tests/research/paqs_q/r02
python -m ruff format --check tools/research/paqs_q/r02 tests/research/paqs_q/r02
PYTHONPATH=src:. MYPYPATH=src python -m mypy --strict --explicit-package-bases --platform win32 tools/research/paqs_q/r02 tests/research/paqs_q/r02
PYTHONPATH=src:. python docs/reviews/evidence/task006b_q_r02_checks.py
git diff 47e7020609e5655927c6aac11a3b1f35b03c96aa ddb61c15f1aea026b26c116f35fa1e2b0b0d055a --check
```

Original normalized AVGO observations and public-response bytes reside outside Git on the
implementer's Windows machine. This reviewer did **not** regenerate the real-market traces,
re-fetch the acquisition attempts, certify provider terms, or repeat the Windows performance
measurements. Market reconciliation above checks committed evidence and calculation code,
not independent acquisition-to-result reproducibility. The acquisition adapter is explicit,
bounded and isolated under research integrations; ordinary imports/evaluations/tests do not
invoke it. The submitted acquisition record adds **0** equities. The fixed 40-equity universe
is retained; available real observations remain AVGO only, with W1/D1 100 valid endpoints each
and M30 74. Unknown historical availability and current-QFQ remain observational, not strict PIT.
The benchmark uses declared synthetic windows, seven repeats and separate traced-memory runs;
it is not a production latency guarantee.

## 6. Disposition and next decision

Accept R02 as a completed, independently reviewed research experiment with a rejected stable
replacement candidate. Preserve baseline, H1 and the rejection evidence as separately identified
research artifacts. This report does not authorize merging research into product authority.

Before another candidate task, decide the mathematical contract for admissible extrema,
persistent two-way seed ambiguity and the stability promised for previously confirmed events
under a moving finite window. State assumptions, permitted changes and rejection oracles before
implementation. This counterexample does not itself prove all bounded algorithms impossible.
Additional independent equities remain a separate validation shortfall. Do not start Event,
Setup/Risk or scanner work on an asserted stable structure foundation until its acceptance
conditions are met under a separately authorized contract.

References: [R02 contract](../../prompts/tasks/TASK-006B-Q_R02_STRUCTURE_STABILITY_RESEARCH.md),
[implementation report](../evidence/TASK_006B_Q/research-02/REPORT.md),
[frozen mathematics](../research/PAQS_Q_STRUCTURE_R02_CANDIDATES.md),
[rejection evidence](../evidence/TASK_006B_Q/research-02/refined-causes/h1-rejection-counterexample.json).
