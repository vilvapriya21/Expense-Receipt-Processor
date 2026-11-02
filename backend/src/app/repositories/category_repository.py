"""Repository for Category — persistence only, no business rules."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.services.categorization_service import CategoryOption


class CategoryRepository:
    """Persistence for Category; also implements the CategoryProvider port."""

    def __init__(self, session: AsyncSession) -> None:
        """Create a CategoryRepository bound to the given session."""
        self._session = session

    async def get_by_id(self, category_id: int) -> Category | None:
        """Return the category with the given id, or None if it does not exist."""
        return await self._session.get(Category, category_id)

    async def list_active(self) -> list[CategoryOption]:
        """Return every active category as a CategoryOption, for category suggestion."""
        stmt = (
            select(Category).where(Category.is_active.is_(True)).order_by(Category.name)
        )
        result = await self._session.execute(stmt)
        return [
            CategoryOption(
                id=category.id, name=category.name, keywords=category.keywords
            )
            for category in result.scalars().all()
        ]

    async def list_all(self) -> list[Category]:
        """Return every category, active or not, for admin management."""
        stmt = select(Category).order_by(Category.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_active_full(self) -> list[Category]:
        """Return every active category as full ORM rows, for employee listing."""
        stmt = (
            select(Category).where(Category.is_active.is_(True)).order_by(Category.name)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Category | None:
        """Return the category with the given name, or None if it does not exist."""
        stmt = select(Category).where(Category.name == name)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def add(self, category: Category) -> Category:
        """Persist a new category and return it with generated fields populated."""
        self._session.add(category)
        await self._session.flush()
        return category

    async def delete(self, category: Category) -> None:
        """Delete the given category."""
        await self._session.delete(category)

    async def commit(self) -> None:
        """Commit the current unit of work."""
        await self._session.commit()
