"""Tests for post-extraction validation rules (validate_extraction)."""

from datetime import datetime, timezone

import pytest
from tests.factories import load_extraction_fixture

from app.extraction.validation import validate_extraction
from app.schemas.extraction import ConfidenceScores, ExtractionResult

HIGH_CONFIDENCE = ConfidenceScores(
    merchant_name=0.9,
    receipt_date=0.9,
    subtotal=0.9,
    tax_amount=0.9,
    total_amount=0.9,
    currency=0.9,
)


class _FixedClock:
    """A stand-in for the datetime class, whose now() always returns a fixed instant."""

    def __init__(self, fixed: datetime) -> None:
        """Create a _FixedClock that always reports fixed from now()."""
        self._fixed = fixed

    def now(self, tz: timezone | None = None) -> datetime:
        """Return the fixed instant regardless of the requested timezone."""
        return self._fixed


def test_validate_extraction_clean_fixture_passes_with_no_reasons() -> None:
    """The clean restaurant receipt fixture needs no review and has no reasons."""
    result, expected = load_extraction_fixture("clean_restaurant_receipt.json")
    outcome = validate_extraction(result)
    assert outcome.needs_review is False
    assert outcome.reasons == []
    assert expected is None


def test_validate_extraction_total_mismatch_fixture_flags_consistency_reason() -> None:
    """The total-mismatch fixture is flagged for review with a consistency reason."""
    result, expected = load_extraction_fixture("total_mismatch_needs_review.json")
    outcome = validate_extraction(result)
    assert outcome.needs_review is True
    assert expected is not None and expected["needs_review"] is True
    assert any("does not equal" in reason for reason in outcome.reasons)


def test_validate_extraction_future_date_fixture_flags_date_reason() -> None:
    """The future-date fixture is flagged for review with a date reason."""
    result, expected = load_extraction_fixture("foreign_currency_future_date.json")
    outcome = validate_extraction(result)
    assert outcome.needs_review is True
    assert expected is not None and expected["needs_review"] is True
    assert any("is in the future" in reason for reason in outcome.reasons)


def test_validate_extraction_unknown_currency_is_flagged() -> None:
    """A currency that is not a recognized ISO-4217 code is flagged for review."""
    result = ExtractionResult(currency="XYZ", confidence=HIGH_CONFIDENCE)
    outcome = validate_extraction(result)
    assert outcome.needs_review is True
    assert any("not a recognized ISO-4217 code" in r for r in outcome.reasons)


def test_validate_extraction_known_currency_is_not_flagged() -> None:
    """A recognized ISO-4217 currency code raises no currency-related reason."""
    result = ExtractionResult(currency="JPY", confidence=HIGH_CONFIDENCE)
    outcome = validate_extraction(result)
    assert not any("ISO-4217" in r for r in outcome.reasons)


def test_validate_extraction_single_low_confidence_field_is_flagged_once() -> None:
    """A field below the confidence threshold produces one low-confidence reason."""
    confidence = HIGH_CONFIDENCE.model_copy(update={"merchant_name": 0.1})
    result = ExtractionResult(confidence=confidence)
    outcome = validate_extraction(result)
    assert outcome.needs_review is True
    assert sum("low confidence" in r for r in outcome.reasons) == 1
    assert any("merchant_name" in r for r in outcome.reasons)


def test_validate_extraction_total_within_tolerance_is_not_flagged() -> None:
    """A total within the rounding tolerance of subtotal + tax raises no reason."""
    result = ExtractionResult(
        subtotal=10.00, tax_amount=1.00, total_amount=11.005, confidence=HIGH_CONFIDENCE
    )
    outcome = validate_extraction(result)
    assert not any("does not equal" in r for r in outcome.reasons)


def test_validate_extraction_date_exactly_today_is_not_flagged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A receipt_date equal to today (UTC) is not considered in the future."""
    fixed_now = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("app.extraction.validation.datetime", _FixedClock(fixed_now))
    result = ExtractionResult(receipt_date=fixed_now.date(), confidence=HIGH_CONFIDENCE)
    outcome = validate_extraction(result)
    assert not any("future" in r for r in outcome.reasons)


def test_validate_extraction_date_one_day_ahead_is_flagged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A receipt_date one day after today (UTC) is flagged as being in the future."""
    fixed_now = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("app.extraction.validation.datetime", _FixedClock(fixed_now))
    tomorrow = fixed_now.date().replace(day=fixed_now.day + 1)
    result = ExtractionResult(receipt_date=tomorrow, confidence=HIGH_CONFIDENCE)
    outcome = validate_extraction(result)
    assert any("is in the future" in r for r in outcome.reasons)
