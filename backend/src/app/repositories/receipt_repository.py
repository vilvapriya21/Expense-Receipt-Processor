"""Repository for Receipt — persistence only, no business rules."""

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.enums import ReceiptStatus
from app.models.receipt import Receipt
from app.models.user import User


def _date_range_filters(date_from: date | None, date_to: date | None) -> list[Any]:
    """Build optional receipt_date >= / <= filter clauses for a date range query."""
    filters: list[Any] = []
    if date_from is not None:
        filters.append(Receipt.receipt_date >= date_from)
    if date_to is not None:
        filters.append(Receipt.receipt_date <= date_to)
    return filters


class ReceiptRepository:
    """Persistence for Receipt: CRUD, pagination, and summary aggregates."""

    def __init__(self, session: AsyncSession) -> None:
        """Create a ReceiptRepository bound to the given session."""
        self._session = session

    async def get_by_id(self, receipt_id: int) -> Receipt | None:
        """Return the receipt with the given id, or None if it does not exist."""
        return await self._session.get(Receipt, receipt_id)

    async def add(self, receipt: Receipt) -> Receipt:
        """Persist a new receipt and return it with generated fields populated."""
        self._session.add(receipt)
        await self._session.flush()
        return receipt

    async def delete(self, receipt: Receipt) -> None:
        """Delete the given receipt."""
        await self._session.delete(receipt)

    async def commit(self) -> None:
        """Commit the current unit of work."""
        await self._session.commit()

    async def commit_and_refresh(self, receipt: Receipt) -> None:
        """Commit, then refresh receipt so server-computed columns/relations load.

        Columns with onupdate=func.now() are expired after a flush/commit, and
        relationships (line_items, owner) can likewise need re-materializing.
        Accessing either synchronously (plain attribute access or session.refresh
        alone) raises MissingGreenlet under AsyncSession, so relationships are
        reloaded explicitly via the async-safe `awaitable_attrs`.
        """
        await self._session.commit()
        await self._session.refresh(receipt)
        await receipt.awaitable_attrs.line_items
        await receipt.awaitable_attrs.owner

    async def list_for_owner(
        self,
        owner_id: int,
        page: int,
        size: int,
        status: ReceiptStatus | None = None,
    ) -> tuple[list[Receipt], int]:
        """Page of the owner's receipts (optional status filter), plus the total."""
        filters = [Receipt.owner_id == owner_id]
        if status is not None:
            filters.append(Receipt.status == status)

        count_stmt = select(func.count()).select_from(Receipt).where(*filters)
        total = (await self._session.execute(count_stmt)).scalar_one()

        list_stmt = (
            select(Receipt)
            .where(*filters)
            .order_by(Receipt.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        receipts = (await self._session.execute(list_stmt)).scalars().all()
        return list(receipts), total

    async def counts_by_status(self, owner_id: int) -> dict[str, int]:
        """Return the owner's receipt count grouped by status."""
        stmt = (
            select(Receipt.status, func.count())
            .where(Receipt.owner_id == owner_id)
            .group_by(Receipt.status)
        )
        rows = (await self._session.execute(stmt)).all()
        return {status.value: count for status, count in rows}

    async def approved_total_amount(self, owner_id: int) -> Decimal:
        """Return the sum of total_amount for the owner's APPROVED receipts."""
        stmt = select(func.coalesce(func.sum(Receipt.total_amount), 0)).where(
            Receipt.owner_id == owner_id, Receipt.status == ReceiptStatus.APPROVED
        )
        result = (await self._session.execute(stmt)).scalar_one()
        return Decimal(str(result))

    async def approved_totals_by_category(
        self, owner_id: int
    ) -> list[tuple[int | None, str | None, Decimal, int]]:
        """Return (category_id, name, total, count) per owner's APPROVED receipts."""
        stmt = (
            select(
                Receipt.category_id,
                Category.name,
                func.coalesce(func.sum(Receipt.total_amount), 0),
                func.count(),
            )
            .outerjoin(Category, Category.id == Receipt.category_id)
            .where(
                Receipt.owner_id == owner_id, Receipt.status == ReceiptStatus.APPROVED
            )
            .group_by(Receipt.category_id, Category.name)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            (category_id, category_name, Decimal(str(total)), count)
            for category_id, category_name, total, count in rows
        ]

    async def count_with_category(self, category_id: int) -> int:
        """Return how many receipts currently use category_id."""
        stmt = (
            select(func.count())
            .select_from(Receipt)
            .where(Receipt.category_id == category_id)
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def list_for_admin(
        self,
        page: int,
        size: int,
        status: ReceiptStatus | None = None,
        owner_id: int | None = None,
        category_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[Receipt], int]:
        """Page of all receipts (status/employee/category/date filters), plus total."""
        filters = _date_range_filters(date_from, date_to)
        if status is not None:
            filters.append(Receipt.status == status)
        if owner_id is not None:
            filters.append(Receipt.owner_id == owner_id)
        if category_id is not None:
            filters.append(Receipt.category_id == category_id)

        count_stmt = select(func.count()).select_from(Receipt).where(*filters)
        total = (await self._session.execute(count_stmt)).scalar_one()

        list_stmt = (
            select(Receipt)
            .where(*filters)
            .order_by(Receipt.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        receipts = (await self._session.execute(list_stmt)).scalars().all()
        return list(receipts), total

    async def admin_counts_by_status(
        self, date_from: date | None = None, date_to: date | None = None
    ) -> dict[str, int]:
        """Count of all receipts grouped by status, within an optional date range."""
        filters = _date_range_filters(date_from, date_to)
        stmt = select(Receipt.status, func.count()).group_by(Receipt.status)
        if filters:
            stmt = stmt.where(*filters)
        rows = (await self._session.execute(stmt)).all()
        return {status.value: count for status, count in rows}

    async def admin_tax_total(
        self, date_from: date | None = None, date_to: date | None = None
    ) -> Decimal:
        """Sum of tax_amount for APPROVED receipts, within an optional date range."""
        filters = [
            Receipt.status == ReceiptStatus.APPROVED,
            *_date_range_filters(date_from, date_to),
        ]
        stmt = select(func.coalesce(func.sum(Receipt.tax_amount), 0)).where(*filters)
        result = (await self._session.execute(stmt)).scalar_one()
        return Decimal(str(result))

    async def admin_totals_by_category(
        self, date_from: date | None = None, date_to: date | None = None
    ) -> list[tuple[int | None, str | None, Decimal, int]]:
        """Return (category_id, name, total, count) for APPROVED receipts."""
        filters = [
            Receipt.status == ReceiptStatus.APPROVED,
            *_date_range_filters(date_from, date_to),
        ]
        stmt = (
            select(
                Receipt.category_id,
                Category.name,
                func.coalesce(func.sum(Receipt.total_amount), 0),
                func.count(),
            )
            .outerjoin(Category, Category.id == Receipt.category_id)
            .where(*filters)
            .group_by(Receipt.category_id, Category.name)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            (category_id, category_name, Decimal(str(total)), count)
            for category_id, category_name, total, count in rows
        ]

    async def admin_totals_by_month(
        self, date_from: date | None = None, date_to: date | None = None
    ) -> list[tuple[str, Decimal, int]]:
        """Return (YYYY-MM, total, count) for APPROVED receipts, admin-wide."""
        month = func.strftime("%Y-%m", Receipt.receipt_date)
        filters = [
            Receipt.status == ReceiptStatus.APPROVED,
            *_date_range_filters(date_from, date_to),
        ]
        stmt = (
            select(
                month, func.coalesce(func.sum(Receipt.total_amount), 0), func.count()
            )
            .where(*filters)
            .group_by(month)
            .order_by(month)
        )
        rows = (await self._session.execute(stmt)).all()
        return [(bucket, Decimal(str(total)), count) for bucket, total, count in rows]

    async def admin_totals_by_employee(
        self, date_from: date | None = None, date_to: date | None = None
    ) -> list[tuple[int, str, Decimal, int]]:
        """Return (employee_id, name, total, count) for APPROVED receipts."""
        filters = [
            Receipt.status == ReceiptStatus.APPROVED,
            *_date_range_filters(date_from, date_to),
        ]
        stmt = (
            select(
                Receipt.owner_id,
                User.full_name,
                func.coalesce(func.sum(Receipt.total_amount), 0),
                func.count(),
            )
            .join(User, User.id == Receipt.owner_id)
            .where(*filters)
            .group_by(Receipt.owner_id, User.full_name)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            (employee_id, employee_name, Decimal(str(total)), count)
            for employee_id, employee_name, total, count in rows
        ]
