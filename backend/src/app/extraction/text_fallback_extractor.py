"""Fallback receipt extractor: pdfplumber text + regex, used with no LLM configured."""

import io
import re
from datetime import date, datetime

import pdfplumber

from app.schemas.extraction import ConfidenceScores, ExtractionResult

_PDF_MIME_TYPE = "application/pdf"

_TOTAL_PATTERN = re.compile(r"total[^\d]{0,10}([\d,]+\.\d{2})", re.IGNORECASE)
_TAX_PATTERN = re.compile(r"tax[^\d]{0,10}([\d,]+\.\d{2})", re.IGNORECASE)
_SUBTOTAL_PATTERN = re.compile(
    r"sub[\s-]?total[^\d]{0,10}([\d,]+\.\d{2})", re.IGNORECASE
)
_DATE_PATTERNS = [
    (re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"), "%Y-%m-%d"),
    (re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b"), "%m/%d/%Y"),
]
_CURRENCY_SYMBOLS = {"$": "USD", "€": "EUR", "£": "GBP"}

LOW_CONFIDENCE = 0.3
SYMBOL_CONFIDENCE = 0.4
NO_CONFIDENCE = 0.0


def _extract_pdf_text(file_bytes: bytes) -> str:
    """Return the concatenated text of every page of a PDF, via pdfplumber."""
    pages_text: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
    return "\n".join(pages_text)


def _parse_amount(match: re.Match[str] | None) -> float | None:
    """Parse a regex amount match's first group into a float, or None if no match."""
    if match is None:
        return None
    return float(match.group(1).replace(",", ""))


def _parse_date(text: str) -> date | None:
    """Try each known date pattern against text and return the first match found."""
    for pattern, fmt in _DATE_PATTERNS:
        match = pattern.search(text)
        if match is None:
            continue
        try:
            return datetime.strptime(match.group(1), fmt).date()
        except ValueError:
            continue
    return None


def _guess_currency(text: str) -> str | None:
    """Guess a currency code from a currency symbol found in text."""
    for symbol, code in _CURRENCY_SYMBOLS.items():
        if symbol in text:
            return code
    return None


def _guess_merchant_name(text: str) -> str | None:
    """Return the first non-blank line of text as a naive merchant name guess."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


class TextFallbackExtractor:
    """Regex-based ReceiptExtractor used when no LLM API key is configured.

    Only PDFs are supported for text extraction (via pdfplumber) — image receipts
    cannot be read without an OCR engine, which this fallback does not include.
    """

    async def extract(self, file_bytes: bytes, mime_type: str) -> ExtractionResult:
        """Extract what this crude fallback can; confidence stays low throughout."""
        raw_text = _extract_pdf_text(file_bytes) if mime_type == _PDF_MIME_TYPE else ""

        total = _parse_amount(_TOTAL_PATTERN.search(raw_text))
        tax = _parse_amount(_TAX_PATTERN.search(raw_text))
        subtotal = _parse_amount(_SUBTOTAL_PATTERN.search(raw_text))
        receipt_date = _parse_date(raw_text)
        currency = _guess_currency(raw_text)
        merchant_name = _guess_merchant_name(raw_text)

        confidence = ConfidenceScores(
            merchant_name=LOW_CONFIDENCE if merchant_name else NO_CONFIDENCE,
            receipt_date=LOW_CONFIDENCE if receipt_date else NO_CONFIDENCE,
            subtotal=LOW_CONFIDENCE if subtotal is not None else NO_CONFIDENCE,
            tax_amount=LOW_CONFIDENCE if tax is not None else NO_CONFIDENCE,
            total_amount=LOW_CONFIDENCE if total is not None else NO_CONFIDENCE,
            currency=SYMBOL_CONFIDENCE if currency else NO_CONFIDENCE,
        )

        return ExtractionResult(
            merchant_name=merchant_name,
            receipt_date=receipt_date,
            subtotal=subtotal,
            tax_amount=tax,
            total_amount=total,
            currency=currency,
            line_items=[],
            confidence=confidence,
            raw_text=raw_text,
        )
