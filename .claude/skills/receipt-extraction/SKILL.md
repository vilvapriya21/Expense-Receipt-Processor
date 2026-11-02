---
name: receipt-extraction
description: Domain knowledge and procedure for this project's receipt extraction and categorization pipeline — the canonical extracted-field schema, the ReceiptExtractor strategy interface, field validation rules, and categorization logic. Trigger when working on anything under backend/src/app/extraction/, adding or modifying a receipt extractor, writing validation for extracted receipt fields, implementing expense category suggestion, or writing tests against receipt data. Do NOT trigger for generic CRUD features unrelated to extraction — use fastapi-react-feature-scaffold for those.
---

# Receipt Extraction

Project-specific knowledge for the extraction domain of the Expense Receipt Processor.

## Canonical extracted-field schema

Every extractor must return this shape (backed by a Pydantic v2 schema in
`schemas/extraction.py`):

```json
{
  "merchant_name": "string",
  "receipt_date": "YYYY-MM-DD",
  "subtotal": 0.00,
  "tax_amount": 0.00,
  "total_amount": 0.00,
  "currency": "ISO-4217 code, e.g. USD",
  "line_items": [
    { "description": "string", "quantity": 1, "unit_price": 0.00, "amount": 0.00 }
  ],
  "confidence": {
    "merchant_name": 0.0,
    "receipt_date": 0.0,
    "subtotal": 0.0,
    "tax_amount": 0.0,
    "total_amount": 0.0,
    "currency": 0.0
  },
  "raw_text": "full OCR/LLM text dump, for audit and reprocessing"
}
```

- `confidence` holds one float (0.0–1.0) per top-level field — used to decide what the
  employee must double-check before submitting.
- `line_items` may be empty (some receipts don't itemize) but the key must always be
  present.
- `raw_text` is stored for audit/reprocessing but must never be logged (see
  [[security]] — no full receipt text in logs) and must never be shown to anyone but the
  owning employee and admins.

## The `ReceiptExtractor` strategy interface

Defined in `backend/src/app/extraction/base.py`:

```python
class ReceiptExtractor(ABC):
    @abstractmethod
    async def extract(self, file_bytes: bytes, mime_type: str) -> ExtractedReceipt:
        """Return a populated ExtractedReceipt or raise ExtractionError."""
```

**To add a new extractor** (e.g. a new OCR provider or LLM backend):
1. Implement `ReceiptExtractor` in `extraction/<provider>_extractor.py`. Do not change the
   interface to fit the provider — adapt the provider's output to `ExtractedReceipt`.
2. Register it behind a `core/settings.py` flag (e.g. `EXTRACTOR_PROVIDER`) resolved via a
   `Depends`-injected factory — never hardcode a concrete extractor in a service.
3. Never put extraction logic (parsing, regex, provider SDK calls) in `services/`; the
   service only calls `extractor.extract(...)` and then runs validation + categorization.
4. Add a test using the fixtures in `fixtures/` plus at least one fixture specific to the
   new provider's quirks.

## Validation rules

Run after extraction, before saving as `EXTRACTED`:

- **Total consistency**: `total_amount` must equal `subtotal + tax_amount` within a small
  tolerance (e.g. ±0.01 for rounding) — see `fixtures/total_mismatch_needs_review.json`.
- **Date sanity**: `receipt_date` must not be in the future relative to upload time — see
  `fixtures/foreign_currency_future_date.json`.
- **Currency**: `currency` must be a valid ISO-4217 code; reject/flag anything else.
- Any failed rule, or any field with `confidence` below the configured threshold, marks the
  receipt as **needs review** — surfaced to the employee before they can submit, never
  silently auto-corrected.

## Categorization rules

Applied in this order, first match wins, each result carries a `confidence` score:

1. **Keyword/merchant map** — look up `merchant_name` (normalized) against a
   merchant → category table; exact or fuzzy match gives high confidence.
2. **LLM suggestion** — if no map match, ask the configured LLM for a category suggestion
   from the **existing category list**; confidence comes from the LLM's own signal
   (e.g. a self-reported score or a fallback heuristic), never hardcoded to 1.0.
3. Categories always come from the database (`categories` table managed by admins) — never
   hardcode category names/IDs in extraction or categorization code. If no category fits,
   return `null` and let the employee pick one.

## Test fixtures

Three sample extracted-receipt JSON fixtures live in `fixtures/`:
- `clean_restaurant_receipt.json` — fully valid, high confidence, no review needed.
- `total_mismatch_needs_review.json` — total ≠ subtotal + tax, must flag needs-review.
- `foreign_currency_future_date.json` — EUR receipt with a future date, must flag
  needs-review on the date rule.

Use these as the baseline inputs for extractor, validation, and categorization tests —
extend with provider-specific fixtures rather than replacing these.
