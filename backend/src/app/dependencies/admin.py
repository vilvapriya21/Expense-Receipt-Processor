"""Dependency wiring for the admin feature's service layer."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.category_repository import CategoryRepository
from app.repositories.receipt_repository import ReceiptRepository
from app.repositories.user_repository import UserRepository
from app.services.category_service import CategoryService
from app.services.employee_service import EmployeeService
from app.services.summary_service import SummaryService


def get_category_service(session: AsyncSession = Depends(get_db)) -> CategoryService:
    """Build a CategoryService wired to request-scoped repositories."""
    return CategoryService(CategoryRepository(session), ReceiptRepository(session))


def get_summary_service(session: AsyncSession = Depends(get_db)) -> SummaryService:
    """Build a SummaryService wired to a request-scoped receipt repository."""
    return SummaryService(ReceiptRepository(session))


def get_employee_service(session: AsyncSession = Depends(get_db)) -> EmployeeService:
    """Build an EmployeeService wired to a request-scoped user repository."""
    return EmployeeService(UserRepository(session))
