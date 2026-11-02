"""Integration tests for /api/v1/receipts, against the real app over ASGI transport."""

from pathlib import Path

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.factories import load_extraction_fixture, make_receipt, make_user
from tests.fakes import FakeExtractor

from app.core.security import create_access_token
from app.extraction.dependencies import get_extractor
from app.main import app
from app.models.enums import ReceiptStatus, UserRole


def _auth_headers(email: str, role: UserRole) -> dict[str, str]:
    """Build an Authorization header carrying a freshly minted JWT for email/role."""
    token = create_access_token(subject=email, role=role.value)
    return {"Authorization": f"Bearer {token}"}


async def _save_committed(db_session: AsyncSession, *rows: object) -> None:
    """Add and commit rows so they're visible to other sessions on the same engine."""
    db_session.add_all(rows)
    await db_session.commit()


async def test_upload_receipt_success_returns_201_extracted(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A valid upload returns 201 with the receipt in EXTRACTED status."""
    owner = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner)
    extraction_result, _ = load_extraction_fixture("clean_restaurant_receipt.json")
    app.dependency_overrides[get_extractor] = lambda: FakeExtractor(
        result=extraction_result
    )

    response = await client.post(
        "/api/v1/receipts/upload",
        headers=_auth_headers(owner.email, owner.role),
        files={"file": ("receipt.pdf", b"%PDF-data", "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "EXTRACTED"


async def test_upload_receipt_exceeding_size_limit_returns_400(
    client: AsyncClient, db_session: AsyncSession, test_settings: object
) -> None:
    """A file larger than the configured max size is rejected with 400."""
    owner = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner)

    response = await client.post(
        "/api/v1/receipts/upload",
        headers=_auth_headers(owner.email, owner.role),
        files={"file": ("big.png", b"x" * (11 * 1024 * 1024), "image/png")},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"


async def test_upload_receipt_disallowed_mime_type_returns_400(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A disallowed claimed MIME type is rejected with 400."""
    owner = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner)

    response = await client.post(
        "/api/v1/receipts/upload",
        headers=_auth_headers(owner.email, owner.role),
        files={"file": ("archive.zip", b"data", "application/zip")},
    )

    assert response.status_code == 400


async def test_list_receipts_returns_only_current_users_receipts(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Listing receipts returns only the authenticated user's own receipts."""
    owner = make_user(role=UserRole.EMPLOYEE)
    other = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner, other)
    mine = make_receipt(owner_id=owner.id, status=ReceiptStatus.EXTRACTED)
    theirs = make_receipt(owner_id=other.id, status=ReceiptStatus.EXTRACTED)
    await _save_committed(db_session, mine, theirs)

    response = await client.get(
        "/api/v1/receipts", headers=_auth_headers(owner.email, owner.role)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == mine.id


async def test_get_receipt_owner_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """The owner of a receipt can fetch it successfully."""
    owner = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner)
    receipt = make_receipt(owner_id=owner.id, status=ReceiptStatus.EXTRACTED)
    await _save_committed(db_session, receipt)

    response = await client.get(
        f"/api/v1/receipts/{receipt.id}",
        headers=_auth_headers(owner.email, owner.role),
    )

    assert response.status_code == 200
    assert response.json()["id"] == receipt.id


async def test_get_receipt_non_owner_returns_403(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A different employee's token gets 403 on someone else's receipt."""
    owner = make_user(role=UserRole.EMPLOYEE)
    other = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner, other)
    receipt = make_receipt(owner_id=owner.id, status=ReceiptStatus.EXTRACTED)
    await _save_committed(db_session, receipt)

    response = await client.get(
        f"/api/v1/receipts/{receipt.id}",
        headers=_auth_headers(other.email, other.role),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


async def test_get_receipt_missing_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Requesting a nonexistent receipt id returns 404."""
    owner = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner)

    response = await client.get(
        "/api/v1/receipts/999999", headers=_auth_headers(owner.email, owner.role)
    )

    assert response.status_code == 404


async def test_get_receipt_file_downloads_stored_bytes(
    client: AsyncClient, db_session: AsyncSession, test_settings: object
) -> None:
    """Downloading a receipt's file streams back the bytes stored on disk."""
    owner = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner)
    upload_dir = Path(test_settings.upload_dir)  # type: ignore[attr-defined]
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / "stored.png"
    stored_path.write_bytes(b"fake-png-bytes")
    receipt = make_receipt(
        owner_id=owner.id,
        status=ReceiptStatus.EXTRACTED,
        file_path=str(stored_path),
        mime_type="image/png",
        original_filename="receipt.png",
    )
    await _save_committed(db_session, receipt)

    response = await client.get(
        f"/api/v1/receipts/{receipt.id}/file",
        headers=_auth_headers(owner.email, owner.role),
    )

    assert response.status_code == 200
    assert response.content == b"fake-png-bytes"


async def test_get_receipt_file_non_owner_returns_403(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A non-owner cannot download another employee's receipt file."""
    owner = make_user(role=UserRole.EMPLOYEE)
    other = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner, other)
    receipt = make_receipt(owner_id=owner.id, status=ReceiptStatus.EXTRACTED)
    await _save_committed(db_session, receipt)

    response = await client.get(
        f"/api/v1/receipts/{receipt.id}/file",
        headers=_auth_headers(other.email, other.role),
    )

    assert response.status_code == 403


async def test_update_receipt_editable_status_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Updating a receipt in an editable status returns 200 with corrected fields."""
    owner = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner)
    receipt = make_receipt(owner_id=owner.id, status=ReceiptStatus.EXTRACTED)
    await _save_committed(db_session, receipt)

    response = await client.put(
        f"/api/v1/receipts/{receipt.id}",
        headers=_auth_headers(owner.email, owner.role),
        json={"merchant_name": "Corrected Name"},
    )

    assert response.status_code == 200
    assert response.json()["merchant_name"] == "Corrected Name"


async def test_update_receipt_non_editable_status_returns_409(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Updating a receipt that is no longer editable returns 409."""
    owner = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner)
    receipt = make_receipt(owner_id=owner.id, status=ReceiptStatus.SUBMITTED)
    await _save_committed(db_session, receipt)

    response = await client.put(
        f"/api/v1/receipts/{receipt.id}",
        headers=_auth_headers(owner.email, owner.role),
        json={"merchant_name": "Corrected Name"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "invalid_status_transition"


async def test_update_receipt_non_owner_returns_403(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A non-owner cannot update another employee's receipt."""
    owner = make_user(role=UserRole.EMPLOYEE)
    other = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner, other)
    receipt = make_receipt(owner_id=owner.id, status=ReceiptStatus.EXTRACTED)
    await _save_committed(db_session, receipt)

    response = await client.put(
        f"/api/v1/receipts/{receipt.id}",
        headers=_auth_headers(other.email, other.role),
        json={"merchant_name": "Hijacked"},
    )

    assert response.status_code == 403


async def test_submit_receipt_from_extracted_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Submitting an EXTRACTED receipt returns 200 with status SUBMITTED."""
    owner = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner)
    receipt = make_receipt(owner_id=owner.id, status=ReceiptStatus.EXTRACTED)
    await _save_committed(db_session, receipt)

    response = await client.post(
        f"/api/v1/receipts/{receipt.id}/submit",
        headers=_auth_headers(owner.email, owner.role),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "SUBMITTED"


async def test_submit_receipt_invalid_status_returns_409(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Submitting a receipt that is not in a submittable status returns 409."""
    owner = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner)
    receipt = make_receipt(owner_id=owner.id, status=ReceiptStatus.APPROVED)
    await _save_committed(db_session, receipt)

    response = await client.post(
        f"/api/v1/receipts/{receipt.id}/submit",
        headers=_auth_headers(owner.email, owner.role),
    )

    assert response.status_code == 409


async def test_delete_receipt_deletable_status_returns_204(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Deleting a receipt in a deletable status returns 204 and removes it."""
    owner = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner)
    receipt = make_receipt(owner_id=owner.id, status=ReceiptStatus.UPLOADED)
    await _save_committed(db_session, receipt)

    response = await client.delete(
        f"/api/v1/receipts/{receipt.id}",
        headers=_auth_headers(owner.email, owner.role),
    )

    assert response.status_code == 204


async def test_delete_receipt_non_deletable_status_returns_409(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Deleting a receipt that has already been submitted returns 409."""
    owner = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, owner)
    receipt = make_receipt(owner_id=owner.id, status=ReceiptStatus.SUBMITTED)
    await _save_committed(db_session, receipt)

    response = await client.delete(
        f"/api/v1/receipts/{receipt.id}",
        headers=_auth_headers(owner.email, owner.role),
    )

    assert response.status_code == 409


async def test_get_receipt_without_token_returns_401(client: AsyncClient) -> None:
    """A request with no bearer token is rejected with 401."""
    response = await client.get("/api/v1/receipts/1")

    assert response.status_code == 401
