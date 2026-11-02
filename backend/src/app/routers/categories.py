"""HTTP routes for /api/v1/categories — read-only listing for authenticated users."""

from fastapi import APIRouter, Depends

from app.dependencies.admin import get_category_service
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.admin import CategoryRead
from app.services.category_service import CategoryService

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
async def list_active_categories(
    _current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
) -> list[CategoryRead]:
    """List every active category, for any authenticated user to pick from."""
    return await service.list_active()
