from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from database.models import Base
from alembic import context
import asyncio
import os


config = context.config

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # Convert postgres:// or postgresql:// to postgresql+asyncpg://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Remove sslmode parameter from URL using proper URL parsing
    if "?" in DATABASE_URL:
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed = urlparse(DATABASE_URL)
        query_params = parse_qs(parsed.query)
        # Remove sslmode parameter
        query_params.pop('sslmode', None)
        # Rebuild URL without sslmode
        new_query = urlencode({k: v[0] for k, v in query_params.items()})
        DATABASE_URL = urlunparse(parsed._replace(query=new_query))
else:
    DATABASE_URL = "sqlite+aiosqlite:///./database.db"

# Override sqlalchemy.url from config with environment variable
config.set_main_option("sqlalchemy.url", DATABASE_URL)


# Конфигурация логгирования
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для автогенерации миграций
target_metadata = Base.metadata


def run_migrations_offline():
    """Запуск миграций в оффлайн-режиме (без подключения к БД)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Фактический запуск миграций."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Асинхронный запуск миграций."""
    url = config.get_main_option("sqlalchemy.url")
    connect_args = {}
    
    # asyncpg uses SSL by default with require mode
    if "postgresql+asyncpg" in url:
        connect_args = {"ssl": "require"}
    
    connectable = create_async_engine(
        url,
        poolclass=NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online():
    """Запуск миграций в онлайн-режиме с обработкой асинхронности."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
