"""Async SQLAlchemy engine and per-request session dependency."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_settings = get_settings()

engine = create_async_engine(_settings.database_url, echo=_settings.sql_echo)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped AsyncSession; the session closes automatically afterward.

    Callers (repositories) are responsible for committing their own writes.
    """
    async with AsyncSessionLocal() as session:
        yield session
