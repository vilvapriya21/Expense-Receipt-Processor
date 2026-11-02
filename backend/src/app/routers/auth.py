"""HTTP routes for /api/v1/auth — I/O only; logic lives in AuthService."""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies.auth import get_auth_service, get_current_user
from app.models.user import User
from app.schemas.auth import Token, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> Token:
    """Authenticate via the OAuth2 password flow and return a signed access token."""
    return await service.authenticate(form_data.username, form_data.password)


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    """Return the currently authenticated user."""
    return UserRead.model_validate(current_user)
