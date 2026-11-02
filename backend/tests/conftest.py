"""Shared pytest fixtures: an isolated async SQLite database and HTTP client per run."""

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest_asyncio.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a fresh in-memory SQLite async engine with all tables, for one test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession bound to the per-test in-memory database."""
    session_maker = async_sessionmaker(
        db_engine, expire_on_commit=False, autoflush=False
    )
    async with session_maker() as session:
        yield session


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Return application Settings pointed at an isolated temp upload directory."""
    return Settings(upload_dir=str(tmp_path / "uploads"))


@pytest_asyncio.fixture
async def client(
    db_engine: AsyncEngine, test_settings: Settings
) -> AsyncGenerator[AsyncClient, None]:
    """An httpx AsyncClient for the real app, with DB/settings overridden for tests."""
    session_maker = async_sessionmaker(
        db_engine, expire_on_commit=False, autoflush=False
    )

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        """Yield a session bound to the per-test in-memory database."""
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_settings] = lambda: test_settings
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as http_client:
        yield http_client
    app.dependency_overrides.clear()
