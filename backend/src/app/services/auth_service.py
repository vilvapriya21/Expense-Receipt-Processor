"""Business logic for authentication."""

from typing import Any

from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token


class AuthService:
    """Authenticates users and issues access tokens."""

    def __init__(self, user_repository: UserRepository) -> None:
        """Create an AuthService wired to its user repository."""
        self._user_repository = user_repository

    async def authenticate(self, email: str, raw_password: str) -> Token:
        """Verify the given credentials and return a signed access Token."""
        user = await self._user_repository.get_by_email(email)
        if user is None or not verify_password(raw_password, user.hashed_password):
            raise UnauthorizedError("Incorrect email or password")
        jwt_value = create_access_token(subject=user.email, role=user.role.value)
        token_fields: dict[str, Any] = {
            "access_token": jwt_value,
            "token_type": "bearer",  # nosec B105
        }
        return Token(**token_fields)
