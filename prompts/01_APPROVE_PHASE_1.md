APPROVE PHASE 1

Read in full:

- AGENTS.md
- docs/MASTER_SPEC.md
- docs/ARCHITECTURE.md
- docs/DATABASE_SCHEMA.md
- docs/API_CONTRACTS.md
- docs/STRATEGY_SPEC.md
- docs/REQUIREMENTS_MATRIX.md
- docs/phases/PHASE_1_PLAN.md

Implement Phase 1 only.

Before editing:

1. Run `git status`.
2. Identify and preserve unrelated user changes.
3. Show the planned file changes.
4. Create a local Git checkpoint only if safe and already configured.

Phase 1 must implement only the foundation and contracts defined in the approved plan, including project skeleton, configuration, logging, migrations, canonical domain models, provider/broker interfaces and registries, security master, initial portfolio/watchlist, and minimal read-only API/dashboard.

Do not implement full PaperBroker execution, quantitative scoring, backtesting, Futu SDK connectivity, or live trading in this phase.

After implementation:

1. Run the application.
2. Run database migrations from a clean database.
3. Run pytest.
4. Run lint.
5. Run type checking.
6. Fix all Phase 1 failures.
7. Update README, requirements matrix, and Phase 1 documentation.
8. Report exact commands and complete results.
9. Report changed files, completed requirements, limitations, and blockers.
10. Create a local checkpoint only if safe.
11. Stop. Do not begin Phase 2.
