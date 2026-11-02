"""Business logic for listing employees (admin filter pickers)."""

from app.models.enums import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.admin import EmployeeRead


class EmployeeService:
    """Lists employees for admin filter pickers."""

    def __init__(self, user_repository: UserRepository) -> None:
        """Create an EmployeeService wired to its user repository."""
        self._user_repository = user_repository

    async def list_employees(self) -> list[EmployeeRead]:
        """Return every user with the EMPLOYEE role."""
        users = await self._user_repository.list_by_role(UserRole.EMPLOYEE)
        return [EmployeeRead.model_validate(u) for u in users]
