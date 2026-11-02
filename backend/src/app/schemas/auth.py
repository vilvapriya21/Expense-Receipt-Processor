"""Request/response schemas for authentication."""

from pydantic import BaseModel, ConfigDict

from app.models.enums import UserRole


class Token(BaseModel):
    """An issued JWT access token."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    """The currently authenticated user."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    email: str
    full_name: str
    role: UserRole
