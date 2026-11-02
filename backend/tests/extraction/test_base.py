"""Tests for the ReceiptExtractor strategy Protocol and ExtractionError."""

from app.extraction.base import ExtractionError, ReceiptExtractor
from app.schemas.extraction import ExtractionResult


class _ConformingExtractor:
    """A minimal class whose shape satisfies the ReceiptExtractor protocol."""

    async def extract(self, file_bytes: bytes, mime_type: str) -> ExtractionResult:
        """Return an empty ExtractionResult."""
        return ExtractionResult()


class _NonConformingExtractor:
    """A class missing the required extract() method."""


def test_receipt_extractor_protocol_conforming_class_is_instance() -> None:
    """A class implementing extract(...) satisfies the runtime-checkable Protocol."""
    assert isinstance(_ConformingExtractor(), ReceiptExtractor)


def test_receipt_extractor_protocol_non_conforming_class_is_not_instance() -> None:
    """A class without extract(...) does not satisfy the Protocol."""
    assert not isinstance(_NonConformingExtractor(), ReceiptExtractor)


def test_extraction_error_is_exception_with_message() -> None:
    """ExtractionError behaves like a standard Exception, carrying its message."""
    error = ExtractionError("boom")
    assert isinstance(error, Exception)
    assert str(error) == "boom"
