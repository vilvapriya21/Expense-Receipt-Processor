"""Auth dependencies: current user resolution and role checks."""

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    encoded_jwt: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the current authenticated User from a bearer JWT."""
    claims = decode_access_token(encoded_jwt)
    email = claims.get("sub")
    if not email:
        raise UnauthorizedError("Token is missing a subject claim")

    user = await UserRepository(session).get_by_email(email)
    if user is None:
        raise UnauthorizedError("User for this token no longer exists")
    return user


def require_role(required_role: UserRole) -> Callable[..., Coroutine[Any, Any, User]]:
    """Return a dependency that raises ForbiddenError unless the user has that role."""

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        """Verify the current user holds required_role, or raise ForbiddenError."""
        if current_user.role != required_role:
            raise ForbiddenError(f"This action requires the {required_role.value} role")
        return current_user

    return _check


def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    """Build an AuthService wired to a request-scoped user repository."""
    return AuthService(UserRepository(session))
