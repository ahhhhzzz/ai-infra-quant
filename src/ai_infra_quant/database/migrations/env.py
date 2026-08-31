from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from ai_infra_quant.config import Settings
from ai_infra_quant.database import models  # noqa: F401
from ai_infra_quant.database.base import Base
from ai_infra_quant.database.session import ensure_sqlite_database_parent

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def database_url() -> str:
    arguments = context.get_x_argument(as_dictionary=True)
    explicit_url = arguments.get("database_url")
    if explicit_url is not None:
        return explicit_url
    return Settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    selected_database_url = database_url()
    ensure_sqlite_database_parent(selected_database_url)
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = selected_database_url
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
