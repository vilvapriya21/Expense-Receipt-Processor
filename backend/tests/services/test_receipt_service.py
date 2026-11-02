"""Tests for ReceiptService: upload validation, the happy path, ownership, lifecycle."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from tests.factories import load_extraction_fixture, make_receipt, make_user
from tests.fakes import FakeExtractor

from app.core.config import Settings
from app.core.exceptions import (
    ForbiddenError,
    InvalidStatusTransitionError,
    NotFoundError,
)
from app.core.exceptions import ValidationError as AppValidationError
from app.models.enums import ReceiptStatus
from app.models.receipt import Receipt
from app.models.user import User
from app.repositories.receipt_repository import ReceiptRepository
from app.schemas.receipt import ReceiptUpdate
from app.services.categorization_service import (
    CategorizationService,
    CategorySuggestion,
)
from app.services.receipt_service import (
    DELETABLE_STATUSES,
    EDITABLE_STATUSES,
    SUBMITTABLE_STATUSES,
    ReceiptService,
)

ALL_STATUSES = list(ReceiptStatus)


def _build_service(
    db_session: AsyncSession,
    settings: Settings,
    *,
    extractor: object | None = None,
    categorization_service: object | None = None,
) -> ReceiptService:
    """Build a ReceiptService wired to a real repository on the given session."""
    return ReceiptService(
        ReceiptRepository(db_session),
        extractor or FakeExtractor(),  # type: ignore[arg-type]
        categorization_service or AsyncMock(spec=CategorizationService),  # type: ignore[arg-type]
        settings,
    )


async def _save(db_session: AsyncSession, *rows: User | Receipt) -> None:
    """Add and flush one or more ORM rows on the given session."""
    db_session.add_all(rows)
    await db_session.flush()


async def test_upload_file_exceeding_max_size_raises_validation_error(
    db_session: AsyncSession, test_settings: Settings
) -> None:
    """A file larger than max_upload_size_bytes is rejected before extraction runs."""
    owner = make_user()
    await _save(db_session, owner)
    settings = test_settings.model_copy(update={"max_upload_size_bytes": 10})
    service = _build_service(db_session, settings)

    with pytest.raises(AppValidationError):
        await service.upload(owner, b"x" * 20, "big.png", "image/png")


async def test_upload_disallowed_claimed_mime_type_raises_validation_error(
    db_session: AsyncSession, test_settings: Settings
) -> None:
    """A claimed MIME type outside the allow-list is rejected."""
    owner = make_user()
    await _save(db_session, owner)
    service = _build_service(db_session, test_settings)

    with pytest.raises(AppValidationError):
        await service.upload(owner, b"data", "archive.zip", "application/zip")


async def test_upload_magic_byte_mismatch_raises_validation_error(
    db_session: AsyncSession, test_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A claimed MIME type that doesn't match the real file content is rejected."""
    owner = make_user()
    await _save(db_session, owner)
    monkeypatch.setattr(
        "app.services.receipt_service.magic.from_buffer",
        lambda *args, **kwargs: "application/zip",
    )
    service = _build_service(db_session, test_settings)

    with pytest.raises(AppValidationError):
        await service.upload(owner, b"data", "receipt.png", "image/png")


async def test_upload_happy_path_sets_extracted_status_and_fields(
    db_session: AsyncSession, test_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A valid upload is stored, extracted, categorized, and marked EXTRACTED."""
    owner = make_user()
    await _save(db_session, owner)
    monkeypatch.setattr(
        "app.services.receipt_service.magic.from_buffer",
        lambda *args, **kwargs: "application/pdf",
    )
    extraction_result, _ = load_extraction_fixture("clean_restaurant_receipt.json")
    categorization_service = AsyncMock(spec=CategorizationService)
    categorization_service.suggest_category.return_value = CategorySuggestion(
        category_id=1, category_name="Meals", confidence=0.9
    )
    service = _build_service(
        db_session,
        test_settings,
        extractor=FakeExtractor(result=extraction_result),
        categorization_service=categorization_service,
    )

    result = await service.upload(owner, b"%PDF-data", "receipt.pdf", "application/pdf")

    assert result.status == ReceiptStatus.EXTRACTED
    assert result.merchant_name == "Blue Bottle Coffee"
    assert result.needs_review is False
    assert result.suggested_category_id == 1
    assert result.category_id is None
    assert len(result.line_items) == 2
    stored_files = list(Path(test_settings.upload_dir).glob("*.pdf"))
    assert len(stored_files) == 1


async def test_upload_needs_review_when_extraction_fails_validation(
    db_session: AsyncSession, test_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A receipt whose extraction fails validation rules is flagged needs_review."""
    owner = make_user()
    await _save(db_session, owner)
    monkeypatch.setattr(
        "app.services.receipt_service.magic.from_buffer",
        lambda *args, **kwargs: "application/pdf",
    )
    extraction_result, _ = load_extraction_fixture("total_mismatch_needs_review.json")
    categorization_service = AsyncMock(spec=CategorizationService)
    categorization_service.suggest_category.return_value = CategorySuggestion(
        category_id=None, category_name=None, confidence=0.0
    )
    service = _build_service(
        db_session,
        test_settings,
        extractor=FakeExtractor(result=extraction_result),
        categorization_service=categorization_service,
    )

    result = await service.upload(owner, b"%PDF-data", "receipt.pdf", "application/pdf")

    assert result.needs_review is True


async def test_get_read_model_non_owner_raises_forbidden(
    db_session: AsyncSession, test_settings: Settings
) -> None:
    """A user who does not own a receipt is forbidden from reading it."""
    owner = make_user()
    other = make_user()
    await _save(db_session, owner, other)
    receipt = make_receipt(owner_id=owner.id)
    await _save(db_session, receipt)
    service = _build_service(db_session, test_settings)

    with pytest.raises(ForbiddenError):
        await service.get_read_model(receipt.id, other)


async def test_get_read_model_missing_receipt_raises_not_found(
    db_session: AsyncSession, test_settings: Settings
) -> None:
    """Requesting a nonexistent receipt id raises NotFoundError."""
    owner = make_user()
    await _save(db_session, owner)
    service = _build_service(db_session, test_settings)

    with pytest.raises(NotFoundError):
        await service.get_read_model(999_999, owner)


async def test_get_file_non_owner_raises_forbidden(
    db_session: AsyncSession, test_settings: Settings
) -> None:
    """A non-owner cannot download another employee's receipt file."""
    owner = make_user()
    other = make_user()
    await _save(db_session, owner, other)
    receipt = make_receipt(owner_id=owner.id)
    await _save(db_session, receipt)
    service = _build_service(db_session, test_settings)

    with pytest.raises(ForbiddenError):
        await service.get_file(receipt.id, other)


async def test_delete_non_owner_raises_forbidden(
    db_session: AsyncSession, test_settings: Settings
) -> None:
    """A non-owner cannot delete another employee's receipt."""
    owner = make_user()
    other = make_user()
    await _save(db_session, owner, other)
    receipt = make_receipt(owner_id=owner.id, status=ReceiptStatus.UPLOADED)
    await _save(db_session, receipt)
    service = _build_service(db_session, test_settings)

    with pytest.raises(ForbiddenError):
        await service.delete(receipt.id, other)


@pytest.mark.parametrize("status", sorted(EDITABLE_STATUSES, key=str))
async def test_update_from_editable_status_succeeds(
    db_session: AsyncSession, test_settings: Settings, status: ReceiptStatus
) -> None:
    """Updating a receipt succeeds from every editable status."""
    owner = make_user()
    await _save(db_session, owner)
    receipt = make_receipt(owner_id=owner.id, status=status)
    await _save(db_session, receipt)
    service = _build_service(db_session, test_settings)

    result = await service.update(
        receipt.id, owner, ReceiptUpdate(merchant_name="Corrected Name")
    )

    assert result.merchant_name == "Corrected Name"


@pytest.mark.parametrize(
    "status", sorted(set(ALL_STATUSES) - EDITABLE_STATUSES, key=str)
)
async def test_update_from_non_editable_status_raises_invalid_transition(
    db_session: AsyncSession, test_settings: Settings, status: ReceiptStatus
) -> None:
    """Updating a receipt from a non-editable status is rejected."""
    owner = make_user()
    await _save(db_session, owner)
    receipt = make_receipt(owner_id=owner.id, status=status)
    await _save(db_session, receipt)
    service = _build_service(db_session, test_settings)

    with pytest.raises(InvalidStatusTransitionError):
        await service.update(receipt.id, owner, ReceiptUpdate(merchant_name="X"))


@pytest.mark.parametrize("status", sorted(SUBMITTABLE_STATUSES, key=str))
async def test_submit_from_submittable_status_succeeds(
    db_session: AsyncSession, test_settings: Settings, status: ReceiptStatus
) -> None:
    """Submitting a receipt succeeds from every submittable status."""
    owner = make_user()
    await _save(db_session, owner)
    receipt = make_receipt(owner_id=owner.id, status=status)
    await _save(db_session, receipt)
    service = _build_service(db_session, test_settings)

    result = await service.submit(receipt.id, owner)

    assert result.status == ReceiptStatus.SUBMITTED


@pytest.mark.parametrize(
    "status", sorted(set(ALL_STATUSES) - SUBMITTABLE_STATUSES, key=str)
)
async def test_submit_from_non_submittable_status_raises_invalid_transition(
    db_session: AsyncSession, test_settings: Settings, status: ReceiptStatus
) -> None:
    """Submitting a receipt from a non-submittable status is rejected."""
    owner = make_user()
    await _save(db_session, owner)
    receipt = make_receipt(owner_id=owner.id, status=status)
    await _save(db_session, receipt)
    service = _build_service(db_session, test_settings)

    with pytest.raises(InvalidStatusTransitionError):
        await service.submit(receipt.id, owner)


@pytest.mark.parametrize("status", sorted(DELETABLE_STATUSES, key=str))
async def test_delete_from_deletable_status_succeeds(
    db_session: AsyncSession, test_settings: Settings, status: ReceiptStatus
) -> None:
    """Deleting a receipt succeeds from every deletable status and removes the row."""
    owner = make_user()
    await _save(db_session, owner)
    receipt = make_receipt(owner_id=owner.id, status=status)
    await _save(db_session, receipt)
    receipt_id = receipt.id
    service = _build_service(db_session, test_settings)

    await service.delete(receipt_id, owner)

    assert await ReceiptRepository(db_session).get_by_id(receipt_id) is None


@pytest.mark.parametrize(
    "status", sorted(set(ALL_STATUSES) - DELETABLE_STATUSES, key=str)
)
async def test_delete_from_non_deletable_status_raises_invalid_transition(
    db_session: AsyncSession, test_settings: Settings, status: ReceiptStatus
) -> None:
    """Deleting a receipt from a non-deletable status is rejected."""
    owner = make_user()
    await _save(db_session, owner)
    receipt = make_receipt(owner_id=owner.id, status=status)
    await _save(db_session, receipt)
    service = _build_service(db_session, test_settings)

    with pytest.raises(InvalidStatusTransitionError):
        await service.delete(receipt.id, owner)


async def test_approve_from_submitted_sets_approved_and_reviewer(
    db_session: AsyncSession, test_settings: Settings
) -> None:
    """Approving a SUBMITTED receipt moves it to APPROVED and records the reviewer."""
    owner = make_user()
    admin = make_user()
    await _save(db_session, owner, admin)
    receipt = make_receipt(owner_id=owner.id, status=ReceiptStatus.SUBMITTED)
    await _save(db_session, receipt)
    service = _build_service(db_session, test_settings)

    result = await service.approve(receipt.id, admin)

    assert result.status == ReceiptStatus.APPROVED
    assert result.reviewer_id == admin.id


@pytest.mark.parametrize(
    "status",
    [s for s in ALL_STATUSES if s != ReceiptStatus.SUBMITTED],
)
async def test_approve_from_non_submitted_status_raises_invalid_transition(
    db_session: AsyncSession, test_settings: Settings, status: ReceiptStatus
) -> None:
    """Approving a receipt not in SUBMITTED status is rejected."""
    owner = make_user()
    admin = make_user()
    await _save(db_session, owner, admin)
    receipt = make_receipt(owner_id=owner.id, status=status)
    await _save(db_session, receipt)
    service = _build_service(db_session, test_settings)

    with pytest.raises(InvalidStatusTransitionError):
        await service.approve(receipt.id, admin)


async def test_reject_from_submitted_sets_rejected_reviewer_and_comment(
    db_session: AsyncSession, test_settings: Settings
) -> None:
    """Rejecting a SUBMITTED receipt moves it to REJECTED with the given comment."""
    owner = make_user()
    admin = make_user()
    await _save(db_session, owner, admin)
    receipt = make_receipt(owner_id=owner.id, status=ReceiptStatus.SUBMITTED)
    await _save(db_session, receipt)
    service = _build_service(db_session, test_settings)

    result = await service.reject(receipt.id, admin, "Missing itemization")

    assert result.status == ReceiptStatus.REJECTED
    assert result.reviewer_id == admin.id
    assert result.review_comment == "Missing itemization"


@pytest.mark.parametrize(
    "status",
    [s for s in ALL_STATUSES if s != ReceiptStatus.SUBMITTED],
)
async def test_reject_from_non_submitted_status_raises_invalid_transition(
    db_session: AsyncSession, test_settings: Settings, status: ReceiptStatus
) -> None:
    """Rejecting a receipt not in SUBMITTED status is rejected."""
    owner = make_user()
    admin = make_user()
    await _save(db_session, owner, admin)
    receipt = make_receipt(owner_id=owner.id, status=status)
    await _save(db_session, receipt)
    service = _build_service(db_session, test_settings)

    with pytest.raises(InvalidStatusTransitionError):
        await service.reject(receipt.id, admin, "comment")


async def test_list_own_filters_by_status_and_paginates(
    db_session: AsyncSession, test_settings: Settings
) -> None:
    """Listing an owner's receipts filters by status and returns pagination metadata."""
    owner = make_user()
    await _save(db_session, owner)
    extracted = make_receipt(owner_id=owner.id, status=ReceiptStatus.EXTRACTED)
    submitted = make_receipt(owner_id=owner.id, status=ReceiptStatus.SUBMITTED)
    await _save(db_session, extracted, submitted)
    service = _build_service(db_session, test_settings)

    page = await service.list_own(owner, 1, 20, ReceiptStatus.SUBMITTED)

    assert page.total == 1
    assert page.items[0].id == submitted.id


async def test_summary_counts_by_status_and_approved_total(
    db_session: AsyncSession, test_settings: Settings
) -> None:
    """An owner's summary reports counts by status and the approved total amount."""
    owner = make_user()
    await _save(db_session, owner)
    approved = make_receipt(
        owner_id=owner.id, status=ReceiptStatus.APPROVED, total_amount=42
    )
    extracted = make_receipt(owner_id=owner.id, status=ReceiptStatus.EXTRACTED)
    await _save(db_session, approved, extracted)
    service = _build_service(db_session, test_settings)

    summary = await service.summary(owner)

    assert summary.counts_by_status["APPROVED"] == 1
    assert summary.counts_by_status["EXTRACTED"] == 1
    assert summary.approved_total_amount == 42
