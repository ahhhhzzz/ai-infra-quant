# PAQS-Q F1 framework

Implementation plan at the exact handoff `857823a0dc39b4c10a1986c575bcbcd9dda11c85`.
The [frozen contract](../../prompts/tasks/TASK-006C-Q-F1_VERSIONED_QUANT_EVENT_FRAMEWORK_FOUNDATION.md)
remains byte-identical. No existing product implementation is edited.

Planned additive files (repository-relative):

```text
src/ai_infra_quant/core/domain/paqs_q/__init__.py
src/ai_infra_quant/core/domain/paqs_q/canonical.py
src/ai_infra_quant/core/domain/paqs_q/inputs.py
src/ai_infra_quant/core/domain/paqs_q/results.py
src/ai_infra_quant/core/ports/paqs_q.py
src/ai_infra_quant/core/strategy/paqs_q/__init__.py
src/ai_infra_quant/core/strategy/paqs_q/calendar.py
src/ai_infra_quant/core/strategy/paqs_q/qualification.py
src/ai_infra_quant/core/strategy/paqs_q/local.py
src/ai_infra_quant/core/strategy/paqs_q/plugins.py
src/ai_infra_quant/core/strategy/paqs_q/registry.py
src/ai_infra_quant/application/paqs_q_artifacts.py
src/ai_infra_quant/resources/paqs_q/b0.json
src/ai_infra_quant/resources/paqs_q/a1.json
tests/paqs_q/__init__.py
tests/paqs_q/support.py
tests/paqs_q/freeze_golden.py
tests/paqs_q/golden/README.md
tests/paqs_q/golden/r05.json
tests/paqs_q/golden/synthetic.json
tests/paqs_q/golden/canonical.json
tests/paqs_q/test_canonical.py
tests/paqs_q/test_parity.py
tests/paqs_q/test_registry.py
tests/paqs_q/test_boundaries.py
tools/validation/paqs_q_f1.py
docs/engineering/PAQS_Q_FRAMEWORK.md
docs/reports/TASK_006C_Q_F1_IMPLEMENTATION_REPORT.md
```

Current documentation updates: `docs/ROADMAP.md`, `docs/MASTER_SPEC.md`,
`docs/ARCHITECTURE.md`, `docs/STRATEGY_SPEC.md`, `docs/REQUIREMENTS_MATRIX.md`,
and `docs/engineering/PAQS_ENGINEERING_GUIDE.md`. Historical research, contracts,
tests and evidence remain unchanged. Validation receipts are added only under
`docs/evidence/TASK_006C_Q_F1/`.
