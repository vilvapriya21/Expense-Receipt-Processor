"""Post-extraction validation rules that decide whether a receipt needs review."""

from datetime import date, datetime, timezone

from pydantic import BaseModel, ConfigDict

from app.schemas.extraction import ExtractionResult

AMOUNT_TOLERANCE = 0.01
CONFIDENCE_THRESHOLD = 0.6

# Common ISO-4217 currency codes accepted for a POC; extend as needed.
KNOWN_CURRENCY_CODES = frozenset(
    {
        "USD",
        "EUR",
        "GBP",
        "JPY",
        "CAD",
        "AUD",
        "CHF",
        "CNY",
        "INR",
        "MXN",
        "BRL",
        "SGD",
        "HKD",
        "NZD",
        "SEK",
        "NOK",
        "DKK",
        "ZAR",
        "AED",
        "KRW",
    }
)


class ValidationOutcome(BaseModel):
    """Whether an ExtractionResult needs human review, and why."""

    model_config = ConfigDict(extra="forbid")

    needs_review: bool
    reasons: list[str]


def _check_total_consistency(result: ExtractionResult, reasons: list[str]) -> None:
    """Append a reason if total_amount != subtotal + tax_amount within tolerance."""
    if (
        result.subtotal is None
        or result.tax_amount is None
        or result.total_amount is None
    ):
        return
    expected_total = result.subtotal + result.tax_amount
    if abs(result.total_amount - expected_total) > AMOUNT_TOLERANCE:
        reasons.append(
            f"total_amount ({result.total_amount}) does not equal "
            f"subtotal + tax_amount ({expected_total})"
        )


def _check_date_not_future(result: ExtractionResult, reasons: list[str]) -> None:
    """Append a reason if receipt_date is in the future relative to today (UTC)."""
    if result.receipt_date is None:
        return
    today: date = datetime.now(timezone.utc).date()
    if result.receipt_date > today:
        reasons.append(f"receipt_date ({result.receipt_date}) is in the future")


def _check_currency_known(result: ExtractionResult, reasons: list[str]) -> None:
    """Append a reason if currency is present but not a recognized ISO-4217 code."""
    if result.currency is None:
        return
    if result.currency.upper() not in KNOWN_CURRENCY_CODES:
        reasons.append(
            f"currency '{result.currency}' is not a recognized ISO-4217 code"
        )


def _check_confidence_thresholds(result: ExtractionResult, reasons: list[str]) -> None:
    """Append a reason for every confidence field below CONFIDENCE_THRESHOLD."""
    scores = result.confidence.model_dump()
    for field_name, score in scores.items():
        if score < CONFIDENCE_THRESHOLD:
            reasons.append(f"low confidence on field '{field_name}' ({score:.2f})")


def validate_extraction(result: ExtractionResult) -> ValidationOutcome:
    """Run all validation rules, flagging the result for review if any rule fails."""
    reasons: list[str] = []
    _check_total_consistency(result, reasons)
    _check_date_not_future(result, reasons)
    _check_currency_known(result, reasons)
    _check_confidence_thresholds(result, reasons)
    return ValidationOutcome(needs_review=bool(reasons), reasons=reasons)
