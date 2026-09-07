# Database migrations

Alembic is the only application schema-change path. Normal application startup checks for
the required application revision and never calls `Base.metadata.create_all()`.

TASK-007B adds `0002_task007b_paqs_e_ledger` after the unchanged
`0001_phase1_foundation`. Run `alembic upgrade head` before application startup.
Its migration adds only the three immutable PAQS-E evidence tables; downgrade to
`0001_phase1_foundation` removes only those TASK-007B objects.

The initial revision emits SQLite `TEXT` for every `ExactDecimal(38,18)` column and installs
append-only triggers for posted opening facts. PostgreSQL compilation emits `NUMERIC(38,18)`.

Revision 0001 uses only explicit Alembic table, constraint, index, and SQLite trigger operations.
It never imports ORM models or metadata, so a later ORM table cannot alter the historical schema.
Static and deterministic migration-isolation tests enforce that property.

The prior local Phase 1 draft used current ORM metadata while running revision 0001. Development
databases created by that draft are not upgrade-compatible and must be recreated manually. No
migration or startup path deletes an existing database automatically.
