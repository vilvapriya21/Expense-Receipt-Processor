"""Tests for the regex-based TextFallbackExtractor."""

from unittest.mock import MagicMock

import pytest

from app.extraction.text_fallback_extractor import TextFallbackExtractor


def _mock_pdfplumber(
    monkeypatch: pytest.MonkeyPatch, pages_text: list[str | None]
) -> None:
    """Patch pdfplumber.open so its pages yield extract_text() results in order."""
    pages = [MagicMock(extract_text=MagicMock(return_value=t)) for t in pages_text]
    pdf_mock = MagicMock()
    pdf_mock.pages = pages
    pdf_mock.__enter__ = MagicMock(return_value=pdf_mock)
    pdf_mock.__exit__ = MagicMock(return_value=False)
    monkeypatch.setattr(
        "app.extraction.text_fallback_extractor.pdfplumber.open",
        MagicMock(return_value=pdf_mock),
    )


async def test_extract_pdf_with_full_fields_parses_all_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A PDF whose text has every known field extracts them all at low confidence.

    Note: Total is listed before Subtotal here to sidestep a known production bug
    (see test_extract_standard_receipt_layout_misparses_total_due_to_regex_bug
    below) where _TOTAL_PATTERN also matches the "total" substring inside
    "Subtotal", so on the realistic Subtotal-then-Total layout it misparses.
    """
    text = (
        "BLUE BOTTLE COFFEE\n"
        "10/12/2026\n"
        "Total 26.70\n"
        "Subtotal 24.50\n"
        "Tax 2.20\n"
        "$ paid"
    )
    _mock_pdfplumber(monkeypatch, [text])

    result = await TextFallbackExtractor().extract(
        b"%PDF-fake-bytes", "application/pdf"
    )

    assert result.merchant_name == "BLUE BOTTLE COFFEE"
    assert result.subtotal == 24.50
    assert result.tax_amount == 2.20
    assert result.total_amount == 26.70
    assert result.currency == "USD"
    assert result.receipt_date is not None
    assert result.receipt_date.isoformat() == "2026-10-12"
    assert result.confidence.total_amount == pytest.approx(0.3)
    assert result.confidence.currency == pytest.approx(0.4)
    assert result.line_items == []
    assert result.raw_text == text


@pytest.mark.xfail(
    reason=(
        "BUG: _TOTAL_PATTERN in app/extraction/text_fallback_extractor.py matches "
        "the 'total' substring inside 'Subtotal', so on the standard receipt layout "
        "(Subtotal line before Total line) total_amount is misparsed as the "
        "subtotal value instead of the real total"
    ),
    strict=True,
)
async def test_extract_standard_receipt_layout_misparses_total_due_to_regex_bug(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """On the standard Subtotal-then-Total layout, total_amount should be 26.70."""
    text = "Subtotal 24.50\nTax 2.20\nTotal 26.70"
    _mock_pdfplumber(monkeypatch, [text])

    result = await TextFallbackExtractor().extract(b"bytes", "application/pdf")

    assert result.total_amount == 26.70


async def test_extract_pdf_with_no_matches_returns_all_null_low_confidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A PDF with no recognizable fields returns all-null fields and zero confidence."""
    _mock_pdfplumber(monkeypatch, ["Thanks for visiting, no useful data here."])

    result = await TextFallbackExtractor().extract(
        b"%PDF-fake-bytes", "application/pdf"
    )

    assert result.subtotal is None
    assert result.tax_amount is None
    assert result.total_amount is None
    assert result.receipt_date is None
    assert result.currency is None
    assert result.confidence.subtotal == 0.0
    assert result.confidence.total_amount == 0.0
    assert result.confidence.currency == 0.0


async def test_extract_non_pdf_mime_type_skips_pdf_parsing_entirely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-PDF mime types never invoke pdfplumber and return an all-empty result."""
    open_mock = MagicMock()
    monkeypatch.setattr(
        "app.extraction.text_fallback_extractor.pdfplumber.open", open_mock
    )

    result = await TextFallbackExtractor().extract(b"\xff\xd8\xff", "image/jpeg")

    open_mock.assert_not_called()
    assert result.raw_text == ""
    assert result.merchant_name is None
    assert result.confidence.merchant_name == 0.0


async def test_extract_iso_date_format_is_parsed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A YYYY-MM-DD date in the PDF text is parsed via the ISO date pattern."""
    _mock_pdfplumber(monkeypatch, ["Receipt\n2026-10-12\nTotal 10.00"])

    result = await TextFallbackExtractor().extract(b"bytes", "application/pdf")

    assert result.receipt_date is not None
    assert result.receipt_date.isoformat() == "2026-10-12"


async def test_extract_multi_page_pdf_concatenates_non_empty_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Text from multiple pages is concatenated; pages with no text are skipped."""
    _mock_pdfplumber(monkeypatch, ["Page one Total 5.00", None, "Page two Tax 1.00"])

    result = await TextFallbackExtractor().extract(b"bytes", "application/pdf")

    assert "Page one" in result.raw_text
    assert "Page two" in result.raw_text
    assert result.total_amount == 5.00
    assert result.tax_amount == 1.00


async def test_extract_amount_with_thousands_separator_parses_as_float(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Amounts containing a thousands separator (e.g. 1,234.56) parse correctly."""
    _mock_pdfplumber(monkeypatch, ["Total 1,234.56"])

    result = await TextFallbackExtractor().extract(b"bytes", "application/pdf")

    assert result.total_amount == 1234.56
