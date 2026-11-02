"""HTTP routes for /api/v1/receipts — I/O only; logic lives in ReceiptService."""

from fastapi import APIRouter, Depends, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.dependencies.auth import get_current_user
from app.dependencies.receipts import get_receipt_service
from app.models.enums import ReceiptStatus
from app.models.user import User
from app.schemas.receipt import (
    PaginatedReceipts,
    ReceiptRead,
    ReceiptSummary,
    ReceiptUpdate,
)
from app.services.receipt_service import ReceiptService

router = APIRouter(prefix="/api/v1/receipts", tags=["receipts"])


@router.post("/upload", response_model=ReceiptRead, status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    service: ReceiptService = Depends(get_receipt_service),
) -> ReceiptRead:
    """Upload a receipt, run extraction + categorization, and return it as EXTRACTED."""
    file_bytes = await file.read()
    return await service.upload(
        current_user, file_bytes, file.filename or "upload", file.content_type or ""
    )


@router.get("", response_model=PaginatedReceipts)
async def list_receipts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: ReceiptStatus | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    service: ReceiptService = Depends(get_receipt_service),
) -> PaginatedReceipts:
    """List the current user's own receipts, paginated and status-filtered."""
    return await service.list_own(current_user, page, size, status_filter)


@router.get("/summary", response_model=ReceiptSummary)
async def get_receipt_summary(
    current_user: User = Depends(get_current_user),
    service: ReceiptService = Depends(get_receipt_service),
) -> ReceiptSummary:
    """Return the current user's own receipt totals."""
    return await service.summary(current_user)


@router.get("/{receipt_id}", response_model=ReceiptRead)
async def get_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_user),
    service: ReceiptService = Depends(get_receipt_service),
) -> ReceiptRead:
    """Return a single receipt owned by the current user."""
    return await service.get_read_model(receipt_id, current_user)


@router.get("/{receipt_id}/file")
async def get_receipt_file(
    receipt_id: int,
    current_user: User = Depends(get_current_user),
    service: ReceiptService = Depends(get_receipt_service),
) -> FileResponse:
    """Download the original uploaded file for a receipt owned by the current user."""
    file_path, mime_type, original_filename = await service.get_file(
        receipt_id, current_user
    )
    return FileResponse(file_path, media_type=mime_type, filename=original_filename)


@router.put("/{receipt_id}", response_model=ReceiptRead)
async def update_receipt(
    receipt_id: int,
    payload: ReceiptUpdate,
    current_user: User = Depends(get_current_user),
    service: ReceiptService = Depends(get_receipt_service),
) -> ReceiptRead:
    """Apply employee corrections to a receipt that is still in an editable status."""
    return await service.update(receipt_id, current_user, payload)


@router.post("/{receipt_id}/submit", response_model=ReceiptRead)
async def submit_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_user),
    service: ReceiptService = Depends(get_receipt_service),
) -> ReceiptRead:
    """Submit a receipt for admin review."""
    return await service.submit(receipt_id, current_user)


@router.delete("/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_user),
    service: ReceiptService = Depends(get_receipt_service),
) -> None:
    """Delete a receipt that has not yet been submitted."""
    await service.delete(receipt_id, current_user)
