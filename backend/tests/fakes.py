"""Test doubles for external boundaries: the extractor and the category provider."""

from app.schemas.extraction import ExtractionResult
from app.services.categorization_service import CategoryOption


class FakeExtractor:
    """A ReceiptExtractor stub returning a canned result, or raising a canned error."""

    def __init__(
        self, result: ExtractionResult | None = None, error: Exception | None = None
    ) -> None:
        """Create a FakeExtractor returning result, or raising error, from extract()."""
        self._result = result
        self._error = error

    async def extract(self, file_bytes: bytes, mime_type: str) -> ExtractionResult:
        """Return the canned result, or raise the canned error."""
        if self._error is not None:
            raise self._error
        assert self._result is not None
        return self._result


class FakeCategoryProvider:
    """A CategoryProvider stub returning a fixed list of active categories."""

    def __init__(self, categories: list[CategoryOption] | None = None) -> None:
        """Create a FakeCategoryProvider serving the given categories."""
        self._categories = categories or []

    async def list_active(self) -> list[CategoryOption]:
        """Return the fixed list of active categories."""
        return self._categories
