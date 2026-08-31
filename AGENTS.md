# Project Instructions

Before any change:

1. Read `docs/MASTER_SPEC.md` in full.
2. Read `docs/ARCHITECTURE.md`, `docs/STRATEGY_SPEC.md`, and the current phase plan if they exist.
3. Run `git status` and preserve unrelated user changes.
4. State the files you plan to modify.

Always:

- Work on the current approved phase only.
- Use a modular monolith; do not introduce unnecessary distributed infrastructure.
- Keep broker-specific and provider-specific code inside `integrations/`.
- Keep Strategy, Portfolio, Accounting, Risk, Performance, and Backtest broker-agnostic.
- Use `Decimal`/database `NUMERIC` for money, price, quantity, fees, and FX.
- Keep external cash flows separate from investment return.
- Never fabricate market, valuation, fundamental, or broker data.
- Mark missing or unsupported data truthfully.
- Keep live trading disabled by default and blocked server-side.
- Never hard-code or commit credentials, account IDs, trade passwords, tokens, databases, logs, or private broker exports.
- Never update a position before a confirmed fill.
- Run the application, tests, lint, and type checks before claiming a phase is complete.
- Update documentation and the requirements matrix when behavior or architecture changes.
- Stop after the current phase and wait for explicit approval.

Git rules:

- Local commits/checkpoints only unless the user explicitly authorizes a push.
- Never force-push, change remotes, change global Git config, or revert unrelated changes.
- If Git identity is missing, report it; do not silently change global configuration.
