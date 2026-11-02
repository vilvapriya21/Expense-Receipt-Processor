"""HTTP routes for /api/v1/admin — I/O only; logic lives in the admin services."""

from datetime import date

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.admin import (
    get_category_service,
    get_employee_service,
    get_summary_service,
)
from app.dependencies.auth import require_role
from app.dependencies.receipts import get_receipt_service
from app.models.enums import ReceiptStatus, UserRole
from app.models.user import User
from app.schemas.admin import (
    AdminSummary,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    EmployeeRead,
    RejectRequest,
)
from app.schemas.receipt import PaginatedReceipts, ReceiptRead
from app.services.category_service import CategoryService
from app.services.employee_service import EmployeeService
from app.services.receipt_service import ReceiptService
from app.services.summary_service import SummaryService

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

require_admin = require_role(UserRole.ADMIN)


@router.get("/receipts", response_model=PaginatedReceipts)
async def list_all_receipts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: ReceiptStatus | None = Query(None, alias="status"),
    employee_id: int | None = Query(None),
    category_id: int | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    _admin: User = Depends(require_admin),
    service: ReceiptService = Depends(get_receipt_service),
) -> PaginatedReceipts:
    """List all receipts, filtered by status, employee, category, and date range."""
    return await service.list_for_admin(
        page, size, status_filter, employee_id, category_id, date_from, date_to
    )


@router.post("/receipts/{receipt_id}/approve", response_model=ReceiptRead)
async def approve_receipt(
    receipt_id: int,
    admin: User = Depends(require_admin),
    service: ReceiptService = Depends(get_receipt_service),
) -> ReceiptRead:
    """Approve a submitted receipt."""
    return await service.approve(receipt_id, admin)


@router.post("/receipts/{receipt_id}/reject", response_model=ReceiptRead)
async def reject_receipt(
    receipt_id: int,
    payload: RejectRequest,
    admin: User = Depends(require_admin),
    service: ReceiptService = Depends(get_receipt_service),
) -> ReceiptRead:
    """Reject a submitted receipt, with a required comment."""
    return await service.reject(receipt_id, admin, payload.comment)


@router.get("/employees", response_model=list[EmployeeRead])
async def list_employees(
    _admin: User = Depends(require_admin),
    service: EmployeeService = Depends(get_employee_service),
) -> list[EmployeeRead]:
    """List every employee, for the admin receipts filter picker."""
    return await service.list_employees()


@router.get("/categories", response_model=list[CategoryRead])
async def list_categories(
    _admin: User = Depends(require_admin),
    service: CategoryService = Depends(get_category_service),
) -> list[CategoryRead]:
    """List every category, active or not."""
    return await service.list_all()


@router.post(
    "/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED
)
async def create_category(
    payload: CategoryCreate,
    _admin: User = Depends(require_admin),
    service: CategoryService = Depends(get_category_service),
) -> CategoryRead:
    """Create a new expense category."""
    return await service.create(payload)


@router.get("/categories/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: int,
    _admin: User = Depends(require_admin),
    service: CategoryService = Depends(get_category_service),
) -> CategoryRead:
    """Return a single category by id."""
    return await service.get(category_id)


@router.put("/categories/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    _admin: User = Depends(require_admin),
    service: CategoryService = Depends(get_category_service),
) -> CategoryRead:
    """Update a category; set is_active=false to soft-deactivate it."""
    return await service.update(category_id, payload)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    _admin: User = Depends(require_admin),
    service: CategoryService = Depends(get_category_service),
) -> None:
    """Delete a category, unless any receipt still references it."""
    await service.delete(category_id)


@router.get("/summaries", response_model=AdminSummary)
async def get_admin_summaries(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    _admin: User = Depends(require_admin),
    service: SummaryService = Depends(get_summary_service),
) -> AdminSummary:
    """Return finance-wide totals by category, month, employee, tax, and status."""
    return await service.summary(date_from, date_to)
