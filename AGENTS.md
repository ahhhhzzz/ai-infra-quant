# Project Instructions

Before any change:

1. Read `docs/ROADMAP.md` and `docs/MASTER_SPEC.md` in full.
2. Read `docs/ARCHITECTURE.md`, `docs/STRATEGY_SPEC.md`, and the current phase plan if they exist.
3. Run `git status` and preserve unrelated user changes.
4. State the files you plan to modify.

Always:

- Work on the current approved phase only.
- Use a modular monolith; do not introduce unnecessary distributed infrastructure.
- Keep broker-specific and provider-specific code inside `integrations/`.
- Keep Strategy, Portfolio, Accounting, Risk, Performance, and Backtest broker-agnostic.
- Use Python `Decimal` for all financial values. Persist exact decimals through the approved dialect-aware design: fixed-scale canonical `TEXT` with no numeric affinity on SQLite, and `NUMERIC(p,s)` on PostgreSQL. Never use binary float for financial data.
- Keep external cash flows separate from investment return.
- Never fabricate market, valuation, fundamental, or broker data.
- Mark missing or unsupported data truthfully.
- Keep the product read-only and decision-support only. Daily data and current-session completed
  1-minute data are allowed; real trades are executed manually in the broker's official client.
- Keep independent read-only Market Data Provider access separate from brokerage-account access.
  No brokerage-account connection, real-account observation/import/matching, broker-write
  call, real-order endpoint, streaming execution, or autonomous trading is permitted; see
  `docs/ROADMAP.md` decision `MTF-001`.
- Never hard-code or commit credentials, external/private broker account IDs, trade passwords, tokens, databases, logs, or private broker exports. Internal canonical UUIDs and deterministic test identifiers are permitted when they contain no private broker information.
- Update simulated paper positions only from a confirmed PaperFill. The product has no real-position
  state.
- Run the application, tests, lint, and type checks before claiming a phase is complete.
- Update documentation and the requirements matrix when behavior or architecture changes.
- Stop after the current phase and wait for explicit approval.

Git rules:

- Local commits/checkpoints only unless the user explicitly authorizes a push.
- Never force-push, change remotes, change global Git config, or revert unrelated changes.
- If Git identity is missing, report it; do not silently change global configuration.
