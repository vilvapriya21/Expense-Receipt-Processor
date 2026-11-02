"""Request/response schemas for the admin API: category CRUD and summaries."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.receipt import CategoryTotal


class RejectRequest(BaseModel):
    """An admin's rejection of a submitted receipt; a comment is required."""

    model_config = ConfigDict(extra="forbid")

    comment: str = Field(min_length=1)


class CategoryCreate(BaseModel):
    """Fields required to create a new expense category."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)


class CategoryUpdate(BaseModel):
    """Admin-submitted changes to an existing category; also used to soft-deactivate."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    keywords: list[str] | None = None
    is_active: bool | None = None


class EmployeeRead(BaseModel):
    """An employee, for the admin receipts filter picker."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    email: str
    full_name: str


class CategoryRead(BaseModel):
    """A category as returned to the admin client."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    name: str
    description: str | None
    keywords: list[str]
    is_active: bool


class MonthTotal(BaseModel):
    """Total approved amount and count for a single calendar month."""

    model_config = ConfigDict(extra="forbid")

    month: str
    total_amount: Decimal
    count: int


class EmployeeTotal(BaseModel):
    """Total approved amount and count for a single employee."""

    model_config = ConfigDict(extra="forbid")

    employee_id: int
    employee_name: str
    total_amount: Decimal
    count: int


class AdminSummary(BaseModel):
    """Finance-wide receipt totals, across all employees, for an optional date range."""

    model_config = ConfigDict(extra="forbid")

    counts_by_status: dict[str, int]
    tax_total: Decimal
    by_category: list[CategoryTotal]
    by_month: list[MonthTotal]
    by_employee: list[EmployeeTotal]
