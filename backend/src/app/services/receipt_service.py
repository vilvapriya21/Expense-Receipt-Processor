"""Business logic for receipts: upload, review lifecycle, ownership, and summaries."""

import logging
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

import magic

from app.core.config import Settings, get_settings
from app.core.exceptions import (
    ForbiddenError,
    InvalidStatusTransitionError,
    NotFoundError,
)
from app.core.exceptions import ValidationError as AppValidationError
from app.extraction.base import ReceiptExtractor
from app.extraction.validation import validate_extraction
from app.models.enums import ReceiptStatus
from app.models.receipt import Receipt
from app.models.receipt_line_item import ReceiptLineItem
from app.models.user import User
from app.repositories.receipt_repository import ReceiptRepository
from app.schemas.extraction import ExtractionResult
from app.schemas.receipt import (
    CategoryTotal,
    PaginatedReceipts,
    ReceiptRead,
    ReceiptSummary,
    ReceiptUpdate,
)
from app.services.categorization_service import CategorizationService

logger = logging.getLogger("app.services.receipt")

EDITABLE_STATUSES = frozenset(
    {ReceiptStatus.UPLOADED, ReceiptStatus.EXTRACTED, ReceiptStatus.REJECTED}
)
SUBMITTABLE_STATUSES = frozenset({ReceiptStatus.EXTRACTED, ReceiptStatus.REJECTED})
DELETABLE_STATUSES = frozenset({ReceiptStatus.UPLOADED, ReceiptStatus.EXTRACTED})
REVIEWABLE_STATUSES = frozenset({ReceiptStatus.SUBMITTED})

_EXTENSION_BY_MIME_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
}


def _to_decimal(value: float | None) -> Decimal | None:
    """Convert an optional float to a Decimal, avoiding binary-float imprecision."""
    if value is None:
        return None
    return Decimal(str(value))


class ReceiptService:
    """Orchestrates receipt upload, extraction, review, and lifecycle transitions."""

    def __init__(
        self,
        repository: ReceiptRepository,
        extractor: ReceiptExtractor,
        categorization_service: CategorizationService,
        settings: Settings | None = None,
    ) -> None:
        """Create a ReceiptService wired to a repository, extractor, and categorizer."""
        self._repository = repository
        self._extractor = extractor
        self._categorization_service = categorization_service
        self._settings = settings or get_settings()

    async def upload(
        self,
        owner: User,
        file_bytes: bytes,
        original_filename: str,
        claimed_mime_type: str,
    ) -> ReceiptRead:
        """Validate, store, extract, and categorize a newly uploaded receipt."""
        mime_type = self._validate_upload(file_bytes, claimed_mime_type)
        stored_path = self._store_file(file_bytes, mime_type)

        receipt = Receipt(
            owner=owner,
            file_path=str(stored_path),
            original_filename=original_filename,
            mime_type=mime_type,
            status=ReceiptStatus.UPLOADED,
        )

        extraction = await self._extractor.extract(file_bytes, mime_type)
        self._apply_extraction(receipt, extraction)

        suggestion = await self._categorization_service.suggest_category(
            extraction.merchant_name, extraction.raw_text
        )
        receipt.suggested_category_id = suggestion.category_id
        receipt.category_confidence = suggestion.confidence
        receipt.status = ReceiptStatus.EXTRACTED

        # Mutate every field (including the line_items collection) on this
        # still-transient object before the first add()/flush: setting a
        # relationship collection on an already-flushed object triggers a
        # synchronous lazy-load of its prior value, which raises
        # MissingGreenlet under AsyncSession.
        receipt = await self._repository.add(receipt)
        await self._repository.commit_and_refresh(receipt)
        return ReceiptRead.model_validate(receipt)

    def _validate_upload(self, file_bytes: bytes, claimed_mime_type: str) -> str:
        """Validate size, declared MIME, and magic bytes; return the real MIME."""
        if len(file_bytes) > self._settings.max_upload_size_bytes:
            raise AppValidationError("Uploaded file exceeds the maximum allowed size")

        if claimed_mime_type not in self._settings.allowed_upload_mime_types:
            raise AppValidationError(f"Unsupported file type: {claimed_mime_type}")

        detected_mime_type = magic.from_buffer(file_bytes, mime=True)
        if detected_mime_type not in self._settings.allowed_upload_mime_types:
            raise AppValidationError(
                f"File content does not match an allowed type: {detected_mime_type}"
            )
        return str(detected_mime_type)

    def _store_file(self, file_bytes: bytes, mime_type: str) -> Path:
        """Save file_bytes under a random filename; never trust the client's name."""
        extension = _EXTENSION_BY_MIME_TYPE.get(mime_type, "")
        upload_dir = Path(self._settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_path = upload_dir / f"{uuid.uuid4().hex}{extension}"
        stored_path.write_bytes(file_bytes)
        return stored_path

    def _apply_extraction(self, receipt: Receipt, extraction: ExtractionResult) -> None:
        """Copy an ExtractionResult's fields onto a Receipt and compute needs_review."""
        receipt.merchant_name = extraction.merchant_name
        receipt.receipt_date = extraction.receipt_date
        receipt.subtotal = _to_decimal(extraction.subtotal)
        receipt.tax_amount = _to_decimal(extraction.tax_amount)
        receipt.total_amount = _to_decimal(extraction.total_amount)
        receipt.currency = extraction.currency
        receipt.raw_text = extraction.raw_text
        receipt.extraction_confidence = extraction.confidence.model_dump()
        receipt.line_items = [
            ReceiptLineItem(
                description=item.description,
                quantity=Decimal(str(item.quantity)),
                unit_price=Decimal(str(item.unit_price)),
                amount=Decimal(str(item.amount)),
            )
            for item in extraction.line_items
        ]
        receipt.needs_review = validate_extraction(extraction).needs_review

    async def _get_owned(self, receipt_id: int, owner: User) -> Receipt:
        """Return a receipt by id, enforcing that it belongs to owner."""
        receipt = await self._repository.get_by_id(receipt_id)
        if receipt is None:
            raise NotFoundError(f"Receipt {receipt_id} not found")
        if receipt.owner_id != owner.id:
            raise ForbiddenError("You do not have access to this receipt")
        return receipt

    async def get_read_model(self, receipt_id: int, owner: User) -> ReceiptRead:
        """Return a receipt (owned by owner) as a ReceiptRead."""
        receipt = await self._get_owned(receipt_id, owner)
        return ReceiptRead.model_validate(receipt)

    async def get_file(self, receipt_id: int, owner: User) -> tuple[str, str, str]:
        """Return (file_path, mime_type, filename) for a receipt owned by owner."""
        receipt = await self._get_owned(receipt_id, owner)
        return receipt.file_path, receipt.mime_type, receipt.original_filename

    async def list_own(
        self, owner: User, page: int, size: int, status: ReceiptStatus | None
    ) -> PaginatedReceipts:
        """Return a paginated page of the owner's receipts, filtered by status."""
        receipts, total = await self._repository.list_for_owner(
            owner.id, page, size, status
        )
        return PaginatedReceipts(
            items=[ReceiptRead.model_validate(r) for r in receipts],
            total=total,
            page=page,
            size=size,
        )

    async def update(
        self, receipt_id: int, owner: User, payload: ReceiptUpdate
    ) -> ReceiptRead:
        """Apply employee corrections to a receipt, only while it is still editable."""
        receipt = await self._get_owned(receipt_id, owner)
        if receipt.status not in EDITABLE_STATUSES:
            raise InvalidStatusTransitionError(
                f"Receipt in status {receipt.status.value} cannot be edited"
            )

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(receipt, field, value)

        await self._repository.commit_and_refresh(receipt)
        return ReceiptRead.model_validate(receipt)

    async def submit(self, receipt_id: int, owner: User) -> ReceiptRead:
        """Move a receipt to SUBMITTED, only from an allowed prior status."""
        receipt = await self._get_owned(receipt_id, owner)
        if receipt.status not in SUBMITTABLE_STATUSES:
            raise InvalidStatusTransitionError(
                f"Receipt in status {receipt.status.value} cannot be submitted"
            )
        receipt.status = ReceiptStatus.SUBMITTED
        await self._repository.commit_and_refresh(receipt)
        return ReceiptRead.model_validate(receipt)

    async def delete(self, receipt_id: int, owner: User) -> None:
        """Delete a receipt, only before it has ever been submitted."""
        receipt = await self._get_owned(receipt_id, owner)
        if receipt.status not in DELETABLE_STATUSES:
            raise InvalidStatusTransitionError(
                f"Receipt in status {receipt.status.value} cannot be deleted"
            )
        await self._repository.delete(receipt)
        await self._repository.commit()

    async def summary(self, owner: User) -> ReceiptSummary:
        """Return the owner's own receipt totals."""
        counts = await self._repository.counts_by_status(owner.id)
        approved_total = await self._repository.approved_total_amount(owner.id)
        by_category = await self._repository.approved_totals_by_category(owner.id)
        return ReceiptSummary(
            counts_by_status=counts,
            approved_total_amount=approved_total,
            approved_by_category=[
                CategoryTotal(
                    category_id=category_id,
                    category_name=category_name,
                    total_amount=total,
                    count=count,
                )
                for category_id, category_name, total, count in by_category
            ],
        )

    async def _get_any(self, receipt_id: int) -> Receipt:
        """Return a receipt by id, with no ownership check (admin-only callers)."""
        receipt = await self._repository.get_by_id(receipt_id)
        if receipt is None:
            raise NotFoundError(f"Receipt {receipt_id} not found")
        return receipt

    async def list_for_admin(
        self,
        page: int,
        size: int,
        status: ReceiptStatus | None,
        owner_id: int | None,
        category_id: int | None,
        date_from: date | None,
        date_to: date | None,
    ) -> PaginatedReceipts:
        """List all receipts, filtered by status/employee/category/date range."""
        receipts, total = await self._repository.list_for_admin(
            page, size, status, owner_id, category_id, date_from, date_to
        )
        return PaginatedReceipts(
            items=[ReceiptRead.model_validate(r) for r in receipts],
            total=total,
            page=page,
            size=size,
        )

    async def approve(self, receipt_id: int, reviewer: User) -> ReceiptRead:
        """Approve a submitted receipt."""
        receipt = await self._get_any(receipt_id)
        if receipt.status not in REVIEWABLE_STATUSES:
            raise InvalidStatusTransitionError(
                f"Receipt in status {receipt.status.value} cannot be approved"
            )
        receipt.status = ReceiptStatus.APPROVED
        receipt.reviewer_id = reviewer.id
        await self._repository.commit_and_refresh(receipt)
        return ReceiptRead.model_validate(receipt)

    async def reject(
        self, receipt_id: int, reviewer: User, comment: str
    ) -> ReceiptRead:
        """Reject a submitted receipt with a required comment."""
        receipt = await self._get_any(receipt_id)
        if receipt.status not in REVIEWABLE_STATUSES:
            raise InvalidStatusTransitionError(
                f"Receipt in status {receipt.status.value} cannot be rejected"
            )
        receipt.status = ReceiptStatus.REJECTED
        receipt.reviewer_id = reviewer.id
        receipt.review_comment = comment
        await self._repository.commit_and_refresh(receipt)
        return ReceiptRead.model_validate(receipt)
