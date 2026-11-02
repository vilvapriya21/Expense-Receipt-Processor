"""Integration tests for /api/v1/admin, against the real app over ASGI transport."""

from datetime import date

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.factories import make_category, make_receipt, make_user

from app.core.security import create_access_token
from app.models.enums import ReceiptStatus, UserRole


def _auth_headers(email: str, role: UserRole) -> dict[str, str]:
    """Build an Authorization header carrying a freshly minted JWT for email/role."""
    token = create_access_token(subject=email, role=role.value)
    return {"Authorization": f"Bearer {token}"}


async def _save_committed(db_session: AsyncSession, *rows: object) -> None:
    """Add and commit rows so they're visible to other sessions on the same engine."""
    db_session.add_all(rows)
    await db_session.commit()


async def test_list_all_receipts_employee_token_returns_403(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A non-admin employee token is forbidden from the admin receipts list."""
    employee = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, employee)

    response = await client.get(
        "/api/v1/admin/receipts",
        headers=_auth_headers(employee.email, employee.role),
    )

    assert response.status_code == 403


async def test_list_all_receipts_admin_sees_every_employees_receipts(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """An admin's list includes receipts owned by every employee."""
    admin = make_user(role=UserRole.ADMIN)
    employee_a = make_user(role=UserRole.EMPLOYEE)
    employee_b = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, admin, employee_a, employee_b)
    receipt_a = make_receipt(owner_id=employee_a.id, status=ReceiptStatus.SUBMITTED)
    receipt_b = make_receipt(owner_id=employee_b.id, status=ReceiptStatus.SUBMITTED)
    await _save_committed(db_session, receipt_a, receipt_b)

    response = await client.get(
        "/api/v1/admin/receipts", headers=_auth_headers(admin.email, admin.role)
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2


async def test_list_all_receipts_filters_by_status(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """The admin receipts list can be filtered by status."""
    admin = make_user(role=UserRole.ADMIN)
    employee = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, admin, employee)
    submitted = make_receipt(owner_id=employee.id, status=ReceiptStatus.SUBMITTED)
    approved = make_receipt(owner_id=employee.id, status=ReceiptStatus.APPROVED)
    await _save_committed(db_session, submitted, approved)

    response = await client.get(
        "/api/v1/admin/receipts",
        params={"status": "APPROVED"},
        headers=_auth_headers(admin.email, admin.role),
    )

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == approved.id


async def test_list_all_receipts_filters_by_employee_id(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """The admin receipts list can be filtered by employee_id."""
    admin = make_user(role=UserRole.ADMIN)
    employee_a = make_user(role=UserRole.EMPLOYEE)
    employee_b = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, admin, employee_a, employee_b)
    receipt_a = make_receipt(owner_id=employee_a.id, status=ReceiptStatus.SUBMITTED)
    receipt_b = make_receipt(owner_id=employee_b.id, status=ReceiptStatus.SUBMITTED)
    await _save_committed(db_session, receipt_a, receipt_b)

    response = await client.get(
        "/api/v1/admin/receipts",
        params={"employee_id": employee_a.id},
        headers=_auth_headers(admin.email, admin.role),
    )

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == receipt_a.id


async def test_list_all_receipts_filters_by_category_id(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """The admin receipts list can be filtered by category_id."""
    admin = make_user(role=UserRole.ADMIN)
    employee = make_user(role=UserRole.EMPLOYEE)
    category = make_category()
    await _save_committed(db_session, admin, employee, category)
    in_category = make_receipt(
        owner_id=employee.id, status=ReceiptStatus.SUBMITTED, category_id=category.id
    )
    uncategorized = make_receipt(owner_id=employee.id, status=ReceiptStatus.SUBMITTED)
    await _save_committed(db_session, in_category, uncategorized)

    response = await client.get(
        "/api/v1/admin/receipts",
        params={"category_id": category.id},
        headers=_auth_headers(admin.email, admin.role),
    )

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == in_category.id


async def test_list_all_receipts_filters_by_date_range(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """The admin receipts list can be filtered by receipt_date range."""
    admin = make_user(role=UserRole.ADMIN)
    employee = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, admin, employee)
    in_range = make_receipt(
        owner_id=employee.id,
        status=ReceiptStatus.SUBMITTED,
        receipt_date=date(2026, 6, 15),
    )
    out_of_range = make_receipt(
        owner_id=employee.id,
        status=ReceiptStatus.SUBMITTED,
        receipt_date=date(2025, 1, 1),
    )
    await _save_committed(db_session, in_range, out_of_range)

    response = await client.get(
        "/api/v1/admin/receipts",
        params={"date_from": "2026-01-01", "date_to": "2026-12-31"},
        headers=_auth_headers(admin.email, admin.role),
    )

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == in_range.id


async def test_approve_receipt_from_submitted_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Approving a SUBMITTED receipt returns 200 with status APPROVED."""
    admin = make_user(role=UserRole.ADMIN)
    employee = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, admin, employee)
    receipt = make_receipt(owner_id=employee.id, status=ReceiptStatus.SUBMITTED)
    await _save_committed(db_session, receipt)

    response = await client.post(
        f"/api/v1/admin/receipts/{receipt.id}/approve",
        headers=_auth_headers(admin.email, admin.role),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


async def test_approve_receipt_invalid_status_returns_409(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Approving a receipt that isn't SUBMITTED returns 409."""
    admin = make_user(role=UserRole.ADMIN)
    employee = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, admin, employee)
    receipt = make_receipt(owner_id=employee.id, status=ReceiptStatus.EXTRACTED)
    await _save_committed(db_session, receipt)

    response = await client.post(
        f"/api/v1/admin/receipts/{receipt.id}/approve",
        headers=_auth_headers(admin.email, admin.role),
    )

    assert response.status_code == 409


async def test_reject_receipt_with_comment_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Rejecting a SUBMITTED receipt with a comment returns 200 with status REJECTED."""
    admin = make_user(role=UserRole.ADMIN)
    employee = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, admin, employee)
    receipt = make_receipt(owner_id=employee.id, status=ReceiptStatus.SUBMITTED)
    await _save_committed(db_session, receipt)

    response = await client.post(
        f"/api/v1/admin/receipts/{receipt.id}/reject",
        headers=_auth_headers(admin.email, admin.role),
        json={"comment": "Missing itemized breakdown"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"
    assert response.json()["review_comment"] == "Missing itemized breakdown"


async def test_reject_receipt_without_comment_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Rejecting without a comment field at all fails schema validation with 422."""
    admin = make_user(role=UserRole.ADMIN)
    employee = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, admin, employee)
    receipt = make_receipt(owner_id=employee.id, status=ReceiptStatus.SUBMITTED)
    await _save_committed(db_session, receipt)

    response = await client.post(
        f"/api/v1/admin/receipts/{receipt.id}/reject",
        headers=_auth_headers(admin.email, admin.role),
        json={},
    )

    assert response.status_code == 422


async def test_reject_receipt_with_empty_comment_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Rejecting with an empty-string comment fails the min_length schema rule."""
    admin = make_user(role=UserRole.ADMIN)
    employee = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, admin, employee)
    receipt = make_receipt(owner_id=employee.id, status=ReceiptStatus.SUBMITTED)
    await _save_committed(db_session, receipt)

    response = await client.post(
        f"/api/v1/admin/receipts/{receipt.id}/reject",
        headers=_auth_headers(admin.email, admin.role),
        json={"comment": ""},
    )

    assert response.status_code == 422


async def test_create_category_returns_201(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """An admin can create a new category."""
    admin = make_user(role=UserRole.ADMIN)
    await _save_committed(db_session, admin)

    response = await client.post(
        "/api/v1/admin/categories",
        headers=_auth_headers(admin.email, admin.role),
        json={"name": "Meals", "description": "Food and drink", "keywords": ["cafe"]},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Meals"
    assert body["is_active"] is True


async def test_list_categories_returns_all_categories(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Listing categories returns every category, active or not."""
    admin = make_user(role=UserRole.ADMIN)
    active = make_category(is_active=True)
    inactive = make_category(is_active=False)
    await _save_committed(db_session, admin, active, inactive)

    response = await client.get(
        "/api/v1/admin/categories", headers=_auth_headers(admin.email, admin.role)
    )

    assert response.status_code == 200
    ids = {c["id"] for c in response.json()}
    assert {active.id, inactive.id} <= ids


async def test_get_category_missing_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Fetching a nonexistent category returns 404."""
    admin = make_user(role=UserRole.ADMIN)
    await _save_committed(db_session, admin)

    response = await client.get(
        "/api/v1/admin/categories/999999",
        headers=_auth_headers(admin.email, admin.role),
    )

    assert response.status_code == 404


async def test_update_category_soft_deactivate_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Setting is_active=false via PUT soft-deactivates a category."""
    admin = make_user(role=UserRole.ADMIN)
    category = make_category(is_active=True)
    await _save_committed(db_session, admin, category)

    response = await client.put(
        f"/api/v1/admin/categories/{category.id}",
        headers=_auth_headers(admin.email, admin.role),
        json={"is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


async def test_delete_unused_category_returns_204(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Deleting a category with no referencing receipts succeeds with 204."""
    admin = make_user(role=UserRole.ADMIN)
    category = make_category()
    await _save_committed(db_session, admin, category)

    response = await client.delete(
        f"/api/v1/admin/categories/{category.id}",
        headers=_auth_headers(admin.email, admin.role),
    )

    assert response.status_code == 204


async def test_delete_category_in_use_returns_409(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Deleting a category still referenced by a receipt is blocked with 409."""
    admin = make_user(role=UserRole.ADMIN)
    employee = make_user(role=UserRole.EMPLOYEE)
    category = make_category()
    await _save_committed(db_session, admin, employee, category)
    receipt = make_receipt(
        owner_id=employee.id,
        status=ReceiptStatus.APPROVED,
        category_id=category.id,
    )
    await _save_committed(db_session, receipt)

    response = await client.delete(
        f"/api/v1/admin/categories/{category.id}",
        headers=_auth_headers(admin.email, admin.role),
    )

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


async def test_get_admin_summaries_returns_200_with_expected_shape(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """The admin summaries endpoint reports tax, category, month, and employee data."""
    admin = make_user(role=UserRole.ADMIN)
    employee = make_user(role=UserRole.EMPLOYEE)
    category = make_category()
    await _save_committed(db_session, admin, employee, category)
    approved = make_receipt(
        owner_id=employee.id,
        status=ReceiptStatus.APPROVED,
        category_id=category.id,
        total_amount=100,
        tax_amount=10,
        receipt_date=date(2026, 6, 1),
    )
    await _save_committed(db_session, approved)

    response = await client.get(
        "/api/v1/admin/summaries", headers=_auth_headers(admin.email, admin.role)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["tax_total"] == "10.00"
    assert body["by_category"][0]["category_id"] == category.id
    assert body["by_employee"][0]["employee_id"] == employee.id
    assert body["by_month"][0]["month"] == "2026-06"


async def test_get_admin_summaries_employee_token_returns_403(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A non-admin employee token is forbidden from the admin summaries endpoint."""
    employee = make_user(role=UserRole.EMPLOYEE)
    await _save_committed(db_session, employee)

    response = await client.get(
        "/api/v1/admin/summaries",
        headers=_auth_headers(employee.email, employee.role),
    )

    assert response.status_code == 403
