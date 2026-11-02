"""Business logic for admin-wide receipt summaries."""

from datetime import date

from app.repositories.receipt_repository import ReceiptRepository
from app.schemas.admin import AdminSummary, EmployeeTotal, MonthTotal
from app.schemas.receipt import CategoryTotal


class SummaryService:
    """Assembles finance-wide receipt totals for the admin summaries endpoint."""

    def __init__(self, repository: ReceiptRepository) -> None:
        """Create a SummaryService wired to its receipt repository."""
        self._repository = repository

    async def summary(
        self, date_from: date | None, date_to: date | None
    ) -> AdminSummary:
        """Return finance-wide totals by category, month, employee, tax, and status."""
        counts = await self._repository.admin_counts_by_status(date_from, date_to)
        tax_total = await self._repository.admin_tax_total(date_from, date_to)
        by_category = await self._repository.admin_totals_by_category(
            date_from, date_to
        )
        by_month = await self._repository.admin_totals_by_month(date_from, date_to)
        by_employee = await self._repository.admin_totals_by_employee(
            date_from, date_to
        )

        return AdminSummary(
            counts_by_status=counts,
            tax_total=tax_total,
            by_category=[
                CategoryTotal(
                    category_id=category_id,
                    category_name=category_name,
                    total_amount=total,
                    count=count,
                )
                for category_id, category_name, total, count in by_category
            ],
            by_month=[
                MonthTotal(month=month, total_amount=total, count=count)
                for month, total, count in by_month
            ],
            by_employee=[
                EmployeeTotal(
                    employee_id=employee_id,
                    employee_name=employee_name,
                    total_amount=total,
                    count=count,
                )
                for employee_id, employee_name, total, count in by_employee
            ],
        )
