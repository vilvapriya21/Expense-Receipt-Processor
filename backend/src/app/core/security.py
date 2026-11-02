"""Password hashing and JWT creation/verification."""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

UTC = timezone.utc


def hash_password(raw_password: str) -> str:
    """Return a bcrypt hash of the given plaintext password."""
    return str(_pwd_context.hash(raw_password))


def verify_password(raw_password: str, pw_hash: str) -> bool:
    """Return True if raw_password matches the given bcrypt hash."""
    return bool(_pwd_context.verify(raw_password, pw_hash))


def create_access_token(
    subject: str, role: str, expires_delta: timedelta | None = None
) -> str:
    """Create a signed JWT for the given subject (user email) and role claim."""
    settings = get_settings()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    claims: dict[str, Any] = {"sub": subject, "role": role, "exp": expire}
    jwt_value = jwt.encode(
        claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return jwt_value


def decode_access_token(encoded_jwt: str) -> dict[str, Any]:
    """Decode and verify a JWT, returning its claims, or raise UnauthorizedError."""
    settings = get_settings()
    try:
        claims: dict[str, Any] = jwt.decode(
            encoded_jwt, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired authentication token") from exc
    return claims
