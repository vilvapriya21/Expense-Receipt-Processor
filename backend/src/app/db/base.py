"""Declarative base for all SQLAlchemy models."""

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """Base class every ORM model inherits from.

    Mixes in AsyncAttrs so relationships can be safely re-materialized after a
    commit via `await instance.awaitable_attrs.<relationship>`, instead of a
    synchronous lazy-load that raises MissingGreenlet under AsyncSession.
    """


# Imported here (not at module top) so every model registers on Base.metadata before
# Alembic autogenerate or create_all inspects it, without creating circular imports.
from app.models import category, receipt, receipt_line_item, user  # noqa: E402, F401
