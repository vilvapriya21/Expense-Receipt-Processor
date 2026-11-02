"""Business logic for admin category management."""

from app.core.exceptions import ConflictError, NotFoundError
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.repositories.receipt_repository import ReceiptRepository
from app.schemas.admin import CategoryCreate, CategoryRead, CategoryUpdate


class CategoryService:
    """Orchestrates category CRUD, including the delete-blocked-if-in-use rule."""

    def __init__(
        self,
        category_repository: CategoryRepository,
        receipt_repository: ReceiptRepository,
    ) -> None:
        """Create a CategoryService wired to its category and receipt repositories."""
        self._category_repository = category_repository
        self._receipt_repository = receipt_repository

    async def list_all(self) -> list[CategoryRead]:
        """Return every category, active or not."""
        categories = await self._category_repository.list_all()
        return [CategoryRead.model_validate(c) for c in categories]

    async def list_active(self) -> list[CategoryRead]:
        """Return every active category, for any authenticated user to pick from."""
        categories = await self._category_repository.list_active_full()
        return [CategoryRead.model_validate(c) for c in categories]

    async def get(self, category_id: int) -> CategoryRead:
        """Return a single category by id."""
        category = await self._get_or_404(category_id)
        return CategoryRead.model_validate(category)

    async def create(self, payload: CategoryCreate) -> CategoryRead:
        """Create a new category."""
        category = Category(
            name=payload.name,
            description=payload.description,
            keywords=payload.keywords,
        )
        category = await self._category_repository.add(category)
        await self._category_repository.commit()
        return CategoryRead.model_validate(category)

    async def update(self, category_id: int, payload: CategoryUpdate) -> CategoryRead:
        """Apply changes to a category; also used to soft-deactivate via is_active."""
        category = await self._get_or_404(category_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        await self._category_repository.commit()
        return CategoryRead.model_validate(category)

    async def delete(self, category_id: int) -> None:
        """Delete a category, unless any receipt still references it."""
        category = await self._get_or_404(category_id)
        in_use = await self._receipt_repository.count_with_category(category_id)
        if in_use > 0:
            raise ConflictError(
                f"Category {category_id} is used by {in_use} receipt(s)"
            )
        await self._category_repository.delete(category)
        await self._category_repository.commit()

    async def _get_or_404(self, category_id: int) -> Category:
        """Return a category by id, or raise NotFoundError."""
        category = await self._category_repository.get_by_id(category_id)
        if category is None:
            raise NotFoundError(f"Category {category_id} not found")
        return category
