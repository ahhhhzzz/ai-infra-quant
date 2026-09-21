# TASK-006B-Q R05 Independent Review

Review date: 2026-09-21. Final verdict: **PASS** (bounded research implementation and evidence).

## Exact reviewed identity

| Object | SHA |
|---|---|
| Reviewed R05 head | `7487cf57161a834d9100f983bab9d8534a1c0488` |
| Pre-result implementation / PLAN / manifest freeze | `b10e87cbb324442d1fc744d5fa94522802f870c1` |
| R05 contract | `0d8ca48b046325c4d03a1716c806d42a333153ec` |
| Corrected R04 study-03 baseline | `c4e21a0204cf6cdd7bb139584b02f01792a49f13` |
| Product authority, roadmap/no-live-trading | `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f` |

Git fetch and GitHub commit/ref readback verified these references before review. The authority
and R05 remote branch heads matched exactly; the new handoff branch did not exist remotely.
Review ran in a new worktree from the exact reviewed head, on
`integration/006b-q-closeout-006c-q-f1-handoff`. Existing worktrees and untracked files were preserved.

## Findings

| Severity | Count | Disposition |
|---|---:|---|
| Critical | 0 | None |
| Major | 0 | None |
| Minor | 0 | None |

No result-changing defect was identified. R04-F01 remains closed by its
[exact focused review](https://github.com/ahhhhzzz/ai-infra-quant/blob/2094118f270e209b5b037162813815886678fdbd/docs/reviews/TASK_006B_Q_R04_F01_FOCUSED_RE_REVIEW.md).
The [original R04 finding](https://github.com/ahhhhzzz/ai-infra-quant/blob/4906985744512092fc098340f43e8eec1f41c494/docs/reviews/TASK_006B_Q_R04_INDEPENDENT_REVIEW.md)
was read independently and its corrected denominator was rechecked here.

## Review method and attribution

Read AGENTS, ROADMAP, MASTER_SPEC, ARCHITECTURE, STRATEGY_SPEC, engineering guide, phase plan,
R05 contract/PLAN/README/report/specification, all R05 source/tests, frozen manifests and
machine evidence, R04 and F01 contracts/plans/specifications/reports and the pinned reviews.
The implementer's [report](../evidence/TASK_006B_Q/research-05/REPORT.md),
[validation](../evidence/TASK_006B_Q/research-05/validation.json) and
[freeze receipt](../evidence/TASK_006B_Q/research-05/freeze-readback.json) remain historical evidence.
Their 2026-09-12 execution times and pre-result push observation are attributed to that record,
not claimed as events witnessed live by this reviewer. Commit ancestry, freeze contents and
receipt consistency were checked now. Git history cannot establish every unrecorded local action;
the observable chain contains no merge, rewritten specified commit or post-result calculation edit.

This review independently reran the frozen study and formal gates on 2026-09-21. It also used a
separate read-only decoder/oracle outside the repository: literal Decimal raw inequalities,
census-derived acceptance and segment counts, shared fields, set differences, rolling opportunity/
loss/expiry counts and an independent implementation of the frozen case ranking. It did not call
the submitted model, metrics or case selector as its counting/ranking oracle; the existing dataset
value decoder was reused solely to recover frozen bar values and references.

Local reproduction output: `D:/AI_Infra_Quant_Codex_v1/r05-independent-20260921/`.
Local oracle: `D:/AI_Infra_Quant_Codex_v1/r05-independent-audit-20260921.py`, SHA-256
`c8de9824ec9e373d0de3bced38235eba9e225613de192131e797de7ca8d028a4`.
These scratch artifacts are not product files or replacements for committed historical evidence.

## Independently established results

1. `merge-base(authority, reviewed head) == authority`; no merge exists in that range.
   The corrected R04 → contract → freeze → results → report → audit chain is linear:
   `c4e21a0 → 0d8ca48 → b10e87c → 3dda84b → 79824a6 → 7487cf5`.
   All 612 original mode/type/blob identities and all 14 frozen identities match. R05 adds
   exactly 81 files after its contract, exclusively inside the original allowlist.
2. Frozen source SHA-256 checks pass for W1/D1/M30 and the capture calendar. Full B0 reproduction
   matches all 21 study-03 files; the reconciliation explicitly lists 123 permitted metadata
   paths (recognition time and four summary run fields). No semantic field is excluded.
3. The complete rerun's 46 JSON artifacts match the submitted counterparts after only actual
   recognition/run metadata differences: 378 changed leaf paths, including the new study's
   `finished_at`. Case JSON, endpoint-delta, dependency audit and finite enumeration match exactly
   as data. Recognition is actual run time, never backdated to historical cutoff.

| OBSERVATIONAL timeframe | B0 → A1 occurrences | Added occurrences | Added distinct endpoints | Removed |
|---|---:|---:|---:|---:|
| W1 | 805 → 977 | 172 | 3 | 0 |
| D1 | 4867 → 5806 | 939 | 11 | 0 |
| M30 | 1553 → 1661 | 108 | 3 | 0 |

Counts describe overlapping windows, not independent samples. All additions biject exactly to
active B0 `PRIOR_RAW_VETO` centers; previous raw is opposite in every case, with no same/dual or
unqualified promotion. All 274 common valid cutoffs (100/100/74) satisfy inclusion, shared
kind/Decimal price/extreme and confirmation refs/times/support/availability/mode, unchanged
non-veto classification and all three segment conservation equations. The remaining 326 results
are explicitly insufficient: 300 AS_OF and 26 M30 observational. They are not hidden empty successes.

W1 retains **10400 = 8479 + 1921**, with unresolved support/events zero. Independent raw/census
decoding agrees with both arms' acceptance and segment maps, not just with their aggregate totals.
Rolling endpoint/full-support opportunities B0→A1 are 785→954, 4798→5726, 1523→1628;
loss/full-support loss/rediscovery are all zero. Valid pairs are 99/99/73; failed pairs remain
explicit (26 M30 observational plus 99 per AS_OF frame). Expiry and new confirmations reconcile.

Finite enumeration reran all **40,000** inputs with zero set/bijection failures and zero adjacent
same-kind raw counterexamples. Ordered input/output SHA-256:
`2a765fe99b5138a3bf92f992cb32836956eac4e6c6b48250f4bbdff7dfce3efd`.
The strict-high/low contradiction establishes the adjacent raw proposition; it does not imply
alternation of the complete accepted event sequence. Rolling stability is conditional on identical
ordered quartet, price/calendar versions, mode/quality and active endpoints, not arbitrary revisions.

## All 14 frozen cases

Independent ranking selects the same five categories per timeframe, deduplicating one W1 focus
to yield 4 W1 + 5 D1 + 5 M30 cases. All case data, cutoff bounds, stable ordering, completed source
bars, marker refs and chart manifest hashes agree. All 14 rerendered PNGs are byte-identical to
the originals and were individually opened and inspected. Exact case IDs/data/images are in the
unchanged [case index](../evidence/TASK_006B_Q/research-05/case-review.md).

| Frame / case-ID prefix | Independent visual assessment |
|---|---|
| D1 / 219c2df8 | Added HIGH followed by shared HIGH; intervening unsupported centers remain visible. No alternation guarantee. |
| D1 / 270c5807 | Triple-only diagnostic has no event at focus; unknown quartet support is not upgraded. |
| D1 / 3704289a | LOW/HIGH/LOW three-center chain exposes increased local density; confirmations are separate next bars. |
| D1 / 4e58c20e | First restored LOW follows HIGH; an addition alone does not establish improved structure. |
| D1 / 7cc746b7 | Restored LOW and further added LOW remain visible; original omission reference is traceable outside the crop. |
| M30 / 05d3bb5e | Two-event unit-gap chain coexists with later repeated HIGH; no larger chain inferred. |
| M30 / 755b3089 | Session edge and gray rejection marks distinguish the non-event diagnostic from an orange context event. |
| M30 / 8870f83f | Local LOW and next-bar confirmation are distinct; cross-session baseline reference is not a global truth. |
| M30 / a3a166ff | Nearby orange/shared HIGH pair exposes redundant local peaks. |
| M30 / f48912e4 | Same first HIGH as other categories, but distinct frozen focus; not an independent market sample. |
| W1 / 126a6d07 | Two-center LOW/HIGH chain confirmed by a completed week at cutoff; earlier LOW remains. |
| W1 / 2f10656e | Broad calendar-support gaps remain visible despite apparently continuous prices. |
| W1 / 8c439c0b | First/max-restoration categories share one focus; sparse old reference explains the large comparator gap. |
| W1 / fda26c6d | HIGH/HIGH separated by 40 observations and many support gaps is not a complete market Swing. |

Some non-focus context confirmations lie outside the crop, as the historical case index discloses;
their exact refs remain in JSON. Focus confirmations are visible. No outcome label or candle
completed after cutoff enters selection or interpretation. W1 nominal interval end is not its
factual completion time.

## Actual validation

Windows; Python 3.12.14, pytest 8.4.1, Ruff 0.12.9, mypy 1.17.1. Interpreter:
`D:/AI_Infra_Quant_Codex_v1/task007c1-env/Scripts/python.exe`. Working directory is the new review
worktree; `PYTHONUTF8=1`, `PYTHONPATH` and `MYPYPATH` contain its root and `src`.

| Executed command / check | Independent result |
|---|---|
| `python -m pytest tests/research/paqs_q tests/unit/test_paqs_input.py -ra` | 268 passed, 1 unchanged Starlette warning, 41.25s; exit 0; no skip/xfail/deselection |
| `python -m ruff check tools/research/paqs_q/r05 tests/research/paqs_q/r05` | PASS; exit 0 |
| `python -m ruff format --check tools/research/paqs_q/r05 tests/research/paqs_q/r05` | 11 files already formatted; exit 0 |
| `python -m mypy --strict --explicit-package-bases tools/research/paqs_q/r05 tests/research/paqs_q/r05` | 11 source files, no issues; exit 0 |
| Same mypy command plus `--platform win32` | 11 source files, no issues; exit 0 |
| R05 README study command, only output redirected to the new external directory | PASS; exit 0; all B0, A/B, temporal and enumeration assertions |
| R05 README charts command using the fresh cases/output and existing plotting environment | PASS; exit 0; 14 exact PNG matches |
| Independent decoder/oracle described above | PASS; exit 0; 46 JSON comparisons and 14 ranked cases |
| `python -m tools.research.paqs_q.r05.protect --freeze-sha b10e87cbb324442d1fc744d5fa94522802f870c1` | PASS at exact R05 head; 612 + 14 objects, scope, links and diff |
| `git diff --check 0d8ca48b046325c4d03a1716c806d42a333153ec 7487cf57161a834d9100f983bab9d8534a1c0488` | PASS; exit 0 |

The unchanged protector intentionally requires the R05 branch name, so it ran read-only in the
existing clean exact-head R05 worktree; it was not patched or bypassed. Native and win32 mypy
both ran on Windows; this is not a claimed Linux execution. Plotting used existing matplotlib
3.11.1, Agg and a new writable cache, with no dependency changes.

One review-harness check initially compared a CRLF checkout file to an original LF manifest hash.
`core.autocrlf=true` explains that transport difference. Rechecking the exact committed Git blob
matches all original manifest SHA-256 values; no historical file or manifest was edited.
Browser, Uvicorn, PostgreSQL, migrations and the full product suite were not run: the R05 contract
explicitly excludes those unrelated gates. No user database, OpenD, new prices, LLM or provider
was accessed. GitHub operations were repository provenance/delivery only.

## Verdict and limits

**PASS**: the sole veto ablation was implemented within its frozen domain and its evidence is
reproducible. The independent review agrees that `RECOMMEND_CROSS_SAMPLE_ONLY` is consistent with
the frozen research decision table. Same-kind rates do not rise in any timeframe; restored distinct
more-extreme endpoints are 3/8/1. The W1 same-kind absolute count increases 461→519 and M30 HIGH
maximum run grows 3→4; those costs remain disclosed, not reclassified as success.

Implementation correctness is established only in the reviewed scope. Structural interpretation
remains a local-certificate interpretation, not final Swing/Pivot truth. Market applicability and
strict historical confirmation remain **INCOMPLETE**: one AVGO development sample, current-QFQ,
PARTIAL coverage, unknown historical availability, no independent equity/HK real validation and
retained nonminimal j-2 dependency. No profitability, optimized parameter, predictive or trading
claim follows. Product adoption and permission for a versioned framework are separate Owner
decisions; this review itself neither promotes A1 nor starts F1 implementation.
