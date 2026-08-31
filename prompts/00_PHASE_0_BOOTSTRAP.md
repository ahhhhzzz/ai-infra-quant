Read the following repository files in full before doing anything else:

- AGENTS.md
- docs/MASTER_SPEC.md

This run is Phase 0 only: design review and specification freeze.

Do not implement business functionality.
Do not install broker SDKs.
Do not connect to OpenD or any broker.
Do not create paper or live orders.
Do not begin Phase 1.
Do not push to GitHub or modify Git remotes/global Git configuration.

First, inspect the repository and run `git status`. Preserve all unrelated existing user changes.

Create or update only the following deliverables:

- docs/ARCHITECTURE.md
- docs/DATABASE_SCHEMA.md
- docs/API_CONTRACTS.md
- docs/STRATEGY_SPEC.md
- docs/REQUIREMENTS_MATRIX.md
- docs/phases/PHASE_1_PLAN.md

Requirements for this Phase 0 review:

1. Verify that Strategy, Portfolio, Accounting, Execution, Risk, Performance, Backtest, BrokerAdapter, MarketDataProvider, FundamentalDataProvider, and EventDataProvider are correctly separated.
2. Resolve or explicitly list every contradiction, ambiguity, and missing decision in MASTER_SPEC.md. Do not silently change requirements.
3. In STRATEGY_SPEC.md, propose exact formulas, normalization, data-coverage rules, entry/add/hold/reduce/exit/cooldown behavior, and deterministic golden test cases. Do not implement the strategy yet.
4. In DATABASE_SCHEMA.md, define entities, keys, relationships, Decimal/NUMERIC fields, append-only ledger behavior, multi-currency cash, unitized NAV, orders/fills, and point-in-time fundamental-data provenance.
5. In API_CONTRACTS.md, define versioned request/response models and error semantics. A functional live-order route must not exist in Phase 1.
6. In REQUIREMENTS_MATRIX.md, map each requirement to its target phase, design document, implementation status, and test/acceptance evidence.
7. In PHASE_1_PLAN.md, list exact files to create/change, implementation order, acceptance criteria, test plan, lint/type-check commands, and explicit out-of-scope items.
8. Keep the proposed system a single-process modular monolith. Do not introduce microservices, Kafka, Redis, Celery, Kubernetes, or autonomous trading.
9. If a design choice remains unresolved, provide:
   - options,
   - recommendation,
   - trade-offs,
   - whether user approval is required.
10. Do not claim that external broker or valuation data is available unless you have verified a legitimate source.

At the end, report:

- repository status,
- documents created or changed,
- key architecture decisions,
- contradictions resolved,
- unresolved decisions requiring my approval,
- exact validation performed.

Then stop and wait for the exact instruction:

APPROVE PHASE 1
