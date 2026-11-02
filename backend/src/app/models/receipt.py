"""The Receipt ORM model."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ReceiptStatus
from app.models.receipt_line_item import ReceiptLineItem
from app.models.user import User


class Receipt(Base):
    """An uploaded expense receipt, moving through the review lifecycle."""

    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    file_path: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100))

    status: Mapped[ReceiptStatus] = mapped_column(
        Enum(ReceiptStatus, name="receipt_status"), default=ReceiptStatus.UPLOADED
    )
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)

    merchant_name: Mapped[str | None] = mapped_column(String(255), default=None)
    receipt_date: Mapped[date | None] = mapped_column(Date, default=None)
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=None)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=None)
    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=None)
    currency: Mapped[str | None] = mapped_column(String(3), default=None)

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"), default=None
    )
    suggested_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"), default=None
    )
    category_confidence: Mapped[float | None] = mapped_column(default=None)
    extraction_confidence: Mapped[dict[str, float] | None] = mapped_column(
        JSON, default=None
    )
    raw_text: Mapped[str | None] = mapped_column(Text, default=None)

    reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), default=None
    )
    review_comment: Mapped[str | None] = mapped_column(Text, default=None)

    line_items: Mapped[list[ReceiptLineItem]] = relationship(
        back_populates="receipt", cascade="all, delete-orphan", lazy="selectin"
    )
    owner: Mapped["User"] = relationship(foreign_keys=[owner_id], lazy="selectin")

    @property
    def owner_name(self) -> str:
        """Return the owning employee's full name, for admin-facing display."""
        return self.owner.full_name

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
