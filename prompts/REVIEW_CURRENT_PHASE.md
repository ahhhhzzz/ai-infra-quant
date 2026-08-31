Review the current working tree against:

- AGENTS.md
- docs/MASTER_SPEC.md
- docs/ARCHITECTURE.md
- docs/DATABASE_SCHEMA.md
- docs/API_CONTRACTS.md
- docs/STRATEGY_SPEC.md
- docs/REQUIREMENTS_MATRIX.md
- the current phase plan

Do not add new features.

Focus on:

1. Requirement omissions or scope creep.
2. Violations of broker/data-provider separation.
3. Incorrect financial accounting or use of float.
4. Data leakage, look-ahead bias, or impossible execution assumptions.
5. Security weaknesses, live-route exposure, idempotency, and reconciliation.
6. Missing tests, weak assertions, or tests that only mirror the implementation.
7. Unhandled missing-data and capability cases.
8. Database integrity and migration issues.
9. Unrelated files modified accidentally.

Run the relevant tests, lint, and type checks. Report findings ordered by severity with file and line references. Do not modify code unless I explicitly approve fixes.
