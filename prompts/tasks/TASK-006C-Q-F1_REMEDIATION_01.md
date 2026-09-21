# TASK-006C-Q-F1 Remediation 01

Authorized by the owner's “进行下一步” after the independent F1 review on 2026-09-21.
Starting commit: `d0e8dc22b38d85b0d1395cf76fc03f2de1e85122`.
Parent contract: [F1](TASK-006C-Q-F1_VERSIONED_QUANT_EVENT_FRAMEWORK_FOUNDATION.md),
blob `c2c5448c1eb72fd0ece1572c31ba30246a761b51`, remains unchanged.

## Findings and bounded correction

- F01: Record construction and result decoding must share closed field/type validation.
  Missing price, object-valued price and unknown record fields remain invalid even with
  recomputed record/result hashes. Validate named nested support schemas, record ordering,
  identity hashes and stage/upstream consistency. Plugin-owned evidence/lineage objects
  remain canonical payloads; this task does not define a production Event strategy.
- F02: Before invoking an Event plugin, check the Structure against the supplied input,
  including qualification mode, snapshot identity and exact registered descriptor binding.
  Verify record/evidence integrity; no latest-version fallback or strategy re-evaluation.
  An unavailable historical implementation cannot silently become the current binding.
- F03: Validate security/timeframe for every selected input bar, including bars older than
  the calculation window, before evaluation. Mixed identities return INVALID without payload.
- F1-12: Replace only the obsolete global `*paqs_q*` absence assertion with dedicated-module
  and existing-product isolation checks. Retain all Ledger/account/order prohibitions.

The owner authorizes this narrow exception to the original retained-test protection for
`tests/architecture/test_task007b_boundaries.py`; the original frozen contract and historical
test at the starting commit remain immutable history. No unrelated test relaxation is allowed.

## Planned files

Existing implementation paths:

- `src/ai_infra_quant/core/domain/paqs_q/inputs.py`
- `src/ai_infra_quant/core/domain/paqs_q/results.py`
- `src/ai_infra_quant/core/strategy/paqs_q/registry.py`
- `src/ai_infra_quant/resources/paqs_q/b0.json`
- `src/ai_infra_quant/resources/paqs_q/a1.json`
- `tests/architecture/test_task007b_boundaries.py`
- `tests/paqs_q/test_registry.py` only if existing malformed-result fixtures need valid rehashing
  to continue exercising their original binding rejection.

Add `tests/paqs_q/test_remediation_01.py`, this contract and
`docs/evidence/TASK_006C_Q_F1/remediation-01/` report/receipts/reproduction instructions.
Update `docs/engineering/PAQS_Q_FRAMEWORK.md` and the six existing current status documents:
ROADMAP, MASTER_SPEC, ARCHITECTURE, STRATEGY_SPEC, REQUIREMENTS_MATRIX,
engineering/PAQS_ENGINEERING_GUIDE. Additional helpers, if required, stay within the listed
implementation modules; no new dependency or architecture layer.

B0/A1 semantic IDs/versions and frozen golden inputs stay unchanged during this unaccepted F1
correction. New artifact/code/binding/result hashes identify the corrected implementation;
the previous manifests/results remain available at the exact parent SHA. Never register both
contents under the same ID/version in one registry, or reinterpret an old result as new.

## Validation and delivery

Reproduce findings, add focused adverse tests and positive roundtrips, preserve B0/A1 semantic
parity, run original 268 research/input tests, retained product/browser regressions, Ruff,
format, native/win32 strict mypy, temporary-resource startup, links/diff and object protection.
Run Linux vectors against the corrected artifact. Windows must actually run the same corrected
artifact to close F1-02; prior Windows hashes cannot be relabelled as the new implementation.
If Windows execution is unavailable, finish all other work, supply commands and mark PENDING.

Preserve original evidence, research, golden fixtures, dependencies, migrations and all existing
product source outside these dedicated Q modules. Never access the user database/providers/LLMs.
No R06, new symbols, formal Event strategy, UI/API connection, trading, merge or authority update.
Use isolated work; normal push to the original F1 task branch only if its remote head still
equals the starting SHA, otherwise preserve concurrent work and report the divergence.
Stop after implementation/evidence for independent focused review; do not self-approve closure.
