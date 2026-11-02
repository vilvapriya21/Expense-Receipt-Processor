"""Repository for User — persistence only, no business rules."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from app.models.user import User


class UserRepository:
    """Persistence for User."""

    def __init__(self, session: AsyncSession) -> None:
        """Create a UserRepository bound to the given session."""
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        """Return the user with the given email, or None if not found."""
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def list_by_role(self, role: UserRole) -> list[User]:
        """Return every user with the given role, ordered by name."""
        stmt = select(User).where(User.role == role).order_by(User.full_name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
