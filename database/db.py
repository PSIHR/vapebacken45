from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
import os

# Use PostgreSQL from Replit environment or fallback to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL")

connect_args = {}
pool_settings = {}

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
    
    # PostgreSQL pool settings for reliability
    pool_settings = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }
    # SSL is handled by asyncpg automatically with Neon/Replit PostgreSQL
    connect_args = {"server_settings": {"application_name": "telegram_miniapp"}}
else:
    # Fallback to SQLite for local development
    DATABASE_URL = "sqlite+aiosqlite:///./database.db"

engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    connect_args=connect_args,
    **pool_settings
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    from .models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        return session


@asynccontextmanager
async def lifespan():
    await init_db()
    yield
    await engine.dispose()
