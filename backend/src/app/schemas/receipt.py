"""Request/response schemas for the receipts API."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReceiptStatus


class LineItemRead(BaseModel):
    """A receipt line item as returned to the client."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal


class ReceiptRead(BaseModel):
    """A receipt as returned to the client."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    owner_id: int
    owner_name: str
    original_filename: str
    mime_type: str
    status: ReceiptStatus
    needs_review: bool

    merchant_name: str | None
    receipt_date: date | None
    subtotal: Decimal | None
    tax_amount: Decimal | None
    total_amount: Decimal | None
    currency: str | None

    category_id: int | None
    suggested_category_id: int | None
    category_confidence: float | None
    extraction_confidence: dict[str, float] | None

    reviewer_id: int | None
    review_comment: str | None

    line_items: list[LineItemRead] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime


class ReceiptUpdate(BaseModel):
    """Employee-submitted corrections to an extracted receipt."""

    model_config = ConfigDict(extra="forbid")

    merchant_name: str | None = None
    receipt_date: date | None = None
    subtotal: Decimal | None = None
    tax_amount: Decimal | None = None
    total_amount: Decimal | None = None
    currency: str | None = None
    category_id: int | None = None


class PaginatedReceipts(BaseModel):
    """A page of receipts plus pagination metadata."""

    model_config = ConfigDict(extra="forbid")

    items: list[ReceiptRead]
    total: int
    page: int
    size: int


class CategoryTotal(BaseModel):
    """Total approved amount and count for a single category."""

    model_config = ConfigDict(extra="forbid")

    category_id: int | None
    category_name: str | None
    total_amount: Decimal
    count: int


class ReceiptSummary(BaseModel):
    """An employee's own receipt totals."""

    model_config = ConfigDict(extra="forbid")

    counts_by_status: dict[str, int]
    approved_total_amount: Decimal
    approved_by_category: list[CategoryTotal]
