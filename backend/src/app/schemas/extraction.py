"""Canonical extracted-field schema shared by every ReceiptExtractor implementation."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class LineItem(BaseModel):
    """A single line item parsed from a receipt."""

    model_config = ConfigDict(extra="forbid")

    description: str
    quantity: float
    unit_price: float
    amount: float


class ConfidenceScores(BaseModel):
    """Per-field confidence (0.0-1.0) for an ExtractionResult."""

    model_config = ConfigDict(extra="forbid")

    merchant_name: float = 0.0
    receipt_date: float = 0.0
    subtotal: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    currency: float = 0.0


class ExtractionResult(BaseModel):
    """The canonical shape every ReceiptExtractor must return."""

    model_config = ConfigDict(extra="forbid")

    merchant_name: str | None = None
    receipt_date: date | None = None
    subtotal: float | None = None
    tax_amount: float | None = None
    total_amount: float | None = None
    currency: str | None = None
    line_items: list[LineItem] = Field(default_factory=list)
    confidence: ConfidenceScores = Field(default_factory=ConfidenceScores)
    raw_text: str = ""
