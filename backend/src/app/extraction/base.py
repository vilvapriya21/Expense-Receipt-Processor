"""The ReceiptExtractor strategy interface."""

from typing import Protocol, runtime_checkable

from app.schemas.extraction import ExtractionResult


class ExtractionError(Exception):
    """Raised when an extractor cannot produce a result for a given file."""


@runtime_checkable
class ReceiptExtractor(Protocol):
    """Strategy interface every concrete receipt extractor must implement."""

    async def extract(self, file_bytes: bytes, mime_type: str) -> ExtractionResult:
        """Return a populated ExtractionResult, or raise ExtractionError."""
        ...
