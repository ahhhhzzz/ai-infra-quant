# TASK-006B-Q R03 — Independent review

Review date: 2026-09-10.
Exact reviewed implementation: `7044bb1d3a4e9752bbad0417b753b706723d5b8b`.
Task branch: `task/006b-q-r03-confirmation-stability-contract`.
Development base: `ddb61c15f1aea026b26c116f35fa1e2b0b0d055a`.
Issued contract: `8338144f0185f1b5b416daf08d5bcbff074bb345`.
Frozen plan: `2e048607414021e12984871db3a888cba7f20557`.
Model/test implementation: `ea46324471c6c558afa66896a1b95eaadda2f44e`.

## 1. Decision

**PASS WITH MINOR — 0 Critical, 0 Major, 1 Minor.**

核心研究交付和合成验证通过；一项冻结计划与最终模型的文档口径差异待附加澄清。
本轮没有发现推翻局部支持证明、枚举结果或已披露覆盖代价的阻塞问题。
这不是 M1 的市场适用性通过，也不是 PAQS-Q 产品采用许可。

| Dimension | Verdict |
|---|---|
| Research delivery | PASS WITH MINOR; R03-F01 remains open |
| Mathematical feasibility | Supported only under the explicitly declared conditions |
| Original/H1 stability | Previous rejection and counterexamples remain valid |
| Real-market completeness | INCOMPLETE; no new real observations or raw-market rerun |
| Product adoption / 006C-Q | NOT AUTHORIZED / NOT STARTED |

## 2. Finding R03-F01 — frozen M2 state definition needs an additive clarification

Severity: **Minor**. Status: **OPEN**. Scope: documentation and frozen-plan reconciliation.

Evidence locations:

- `docs/evidence/TASK_006B_Q/research-03/PLAN.md`, lines 49–50, says the state includes the
  entire supplied snapshot sequence and grows with recognized events plus steps.
- `tools/research/paqs_q/r03/models.py`, `History` and `advance`, lines 156–182, retains
  recognition records, latest cutoff, lineage hash and step count. It does not retain the
  supplied snapshot sequence.
- `docs/research/PAQS_Q_CONFIRMATION_AND_ROLLING_STABILITY_R03.md`, section 4, correctly
  describes O(K+N) memory and treats older snapshots as conceptual dependencies; it explicitly
  says the hash cannot substitute for the supplied schedule when auditing history.

The final specification and executable model agree, but the literal frozen state definition
does not. The distinction affects what a caller must supply for replay and what information
can actually be recovered from History. A hash and count do not contain an auditable sequence
of earlier snapshots. The report's statement that model definitions were not adjusted does
not reconcile this discrepancy.

This is Minor because M2's append-only-record proof and history-dependent-output counterexample
do not require storing every snapshot, and the final specification already discloses the
audit limitation. No hidden statelessness claim or incorrect enumeration follows from it.

Required bounded correction:

1. Preserve the frozen PLAN blob. Add a clearly dated clarification/addendum under
   `docs/evidence/TASK_006B_Q/research-03/` linking the exact frozen wording, final specification
   and implementation.
2. State which fields are actually retained, which schedule/snapshot inputs must be supplied
   externally for replay, the memory bound and what lineage proves or cannot reconstruct.
3. Explicitly identify whether this is an overstatement in the plan or a departure from its
   intended storage requirement. Do not silently reinterpret the old text as already matching
   the implementation. Record the effect on the frozen definition and affected claims.
4. Explain why P2/P6 and the reported witnesses/metrics remain unchanged, and make the addendum
   discoverable through a new remediation note/README inside the same evidence directory.

There is no request to store a full history, change model/runtime code, rewrite original
evidence, or rerun all tests. For this docs-only clarification, check links, diff and protected
blobs and perform a focused readback/re-review of R03-F01. If the implementer instead proposes
a code change, it requires a separately justified scope rather than being hidden in this fix.

## 3. Mathematical assessment

M1 is a local certificate model, not the original alternating swing detector. E_j depends on
raw predicates at j and j-1, whose combined support is the ordered quartet j-2 through j+1.
With identical support versions, configuration and valid wrapper preconditions, shifting local
indices does not change either predicate or the negative veto. This supports the conditional
P3 equality claim. An event at j implies R_j, while an event at j+1 requires not R_j; therefore
accepted centers cannot be adjacent. This proves separation, not high/low alternation.

For one left shift and W>=2, an OLD center remaining active in NEW has old index j>=W+1>=3,
so j-2>=1 remains inside NEW. Together with unchanged versions/adjacency and valid global
preconditions, this supplies the stated P5 padding result. It does not cover arbitrary
missing bars, revisions, changed quality or a different calendar interpretation.

The public wrapper only admits eight COMPLETE AS_OF, contiguous equal-duration observations.
The proposed scale is one preceding high-low range, not EMA ATR. Neighbor ties, dual predicates
and the nonrecursive prior-raw veto differ from running extrema; repeated event kinds are
allowed. These changes and the exclusion of real session gaps are materially disclosed.
No Swing/Regime/Zone/Range validity follows from this local existence proof.

M2 appends unseen witness identities with the actual supplied cutoff as recognition time.
Record preservation follows by induction over immutable tuple concatenation; it does not
make an unsupported event currently valid. Same current window with different prior histories
can produce different records. The scoped incompatibility argument applies to the stated
requirement to retain recognized history while hiding that history from the function's inputs;
it is not a theorem that all finite-memory confirmation methods are impossible.

Quality/version preparation and complete-input time checks remain inherited and exercised.
P1/P2 require legitimate input envelopes, declared metadata and input bounds; prefix invariance
does not permit malformed/conflicting arbitrary envelopes. Recognition, reversal completion
and availability are distinguished; no first-recognition backdating was found in these models.
The ATR seed example is a separate counterexample to recurrence equality, not evidence of
continuity of discrete structural decisions. Proofs here are ordinary scoped mathematical
arguments, not formal-machine verification or empirical market certification.

## 4. Independent execution and evidence comparison

Review environment: Linux, Python 3.12.14, pytest 8.4.1. Explicit `PYTHONPATH=src:.` and
`MYPYPATH=src` resolve the reviewed checkout rather than another worktree's editable package.

- **168 passed, 1 warning in 13.05s**: all retained 132 and new 36 research tests, no skips.
- Ruff and format checks pass for all five added Python files.
- Strict mypy passes on both native Linux and Windows target for all five files.
- Independently regenerated the full submitted `run-01/witnesses.json` object in memory and
  matched its canonical contents exactly: H1 rejection, mirrored trap, ATR and local/history cases.
- Reran all **19,683** frozen inputs. Enumeration metadata and every metric match the submitted
  JSON after excluding environment-dependent elapsed time (review run: 0.601 seconds).
- Independent Git tree comparison preserves all **465** development-base mode/type/blob entries.
  The task verifier additionally confirms issued contract and frozen PLAN: **467** protected
  entries total, 14 local links and additive scope/diff checks.

The one warning is the existing Starlette/AnyIO BlockingPortal deprecation. No unrelated product,
browser, Uvicorn, database, network acquisition or market-data replay test was required or claimed.

| View | Original opportunities | Lost | Rediscovered | Active expiry | Full-support opportunities | Full-support lost | Excluded by narrower support |
|---|---:|---:|---:|---:|---:|---:|---:|
| M1 W0 | 17010 | 3402 | 0 | 0 | 13608 | 0 | 3402 |
| M1 W2 | 13608 | 0 | 0 | 3402 | 13608 | 0 | 0 |

The W0 loss rate on this finite domain is 20%; changing to W2 makes those centers actually
leave the newly declared active domain. The report correctly keeps W0 losses, W2 expiry and
the two-bar/25%-of-eight active-capacity cost distinct. The two views are not independent
market trials. Zero full-support loss is not retroactive acceptance under the original Q/H1
criterion. The exact H1 witness still produces 13 rediscovered historical pivots.

Reproduction commands from the reviewed checkout with existing project dependencies:

```bash
PYTHONPATH=src:. python -m pytest tests/research/paqs_q -ra
python -m ruff check tools/research/paqs_q/r03 tests/research/paqs_q/r03
python -m ruff format --check tools/research/paqs_q/r03 tests/research/paqs_q/r03
PYTHONPATH=src:. MYPYPATH=src python -m mypy --strict --explicit-package-bases tools/research/paqs_q/r03 tests/research/paqs_q/r03
PYTHONPATH=src:. MYPYPATH=src python -m mypy --strict --explicit-package-bases --platform win32 tools/research/paqs_q/r03 tests/research/paqs_q/r03
```

To regenerate evidence, use the existing witnesses command from the implementation README
with a fresh output directory. Compare witnesses exactly and enumeration excluding elapsed time;
do not overwrite run-01. The task scope verifier is for the implementation checkout, before
adding this separate review document outside its implementation allowlist.

## 5. Scope, disposition and next decision

Only this independent review is added on `review/006b-q-r03-independent`. The implementation
branch and all engineer artifacts are preserved. Product authority read back during review
remains `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f` on `roadmap/no-live-trading`.
The base's governing documents were previously read and retain identical blobs. No Windows
user filesystem or database preservation certification is claimed by this reviewer.

R03-F01 can be resolved with an additive documentation clarification and focused review.
No new algorithm experiment is authorized by this report. The next substantive decision is
whether to investigate finite local certificates under real session/calendar semantics,
with their changed extreme/volatility/veto definitions and explicit coverage cost. That
would require a separate contract and eventual downstream/market validation; a local
certificate's mathematical consistency does not yet make it a useful PAQS swing structure.

References: [R03 contract](../../prompts/tasks/TASK-006B-Q_R03_CONFIRMATION_AND_ROLLING_STABILITY_CONTRACT.md),
[frozen plan](../evidence/TASK_006B_Q/research-03/PLAN.md),
[mathematics](../research/PAQS_Q_CONFIRMATION_AND_ROLLING_STABILITY_R03.md),
[implementation report](../evidence/TASK_006B_Q/research-03/REPORT.md),
[reproduction guide](../evidence/TASK_006B_Q/research-03/README.md).
