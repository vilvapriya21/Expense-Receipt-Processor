"""Receipt extractor backed by the Anthropic Messages API."""

import base64
import json
import logging
from typing import Any

import anthropic
from pydantic import ValidationError as SchemaValidationError

from app.core.config import Settings, get_settings
from app.extraction.base import ExtractionError
from app.schemas.extraction import ExtractionResult

logger = logging.getLogger("app.extraction.claude")

MAX_ATTEMPTS = 3  # initial call + 2 retries
REQUEST_TIMEOUT_SECONDS = 30.0
MAX_OUTPUT_TOKENS = 2048

_IMAGE_MIME_TYPES = frozenset({"image/jpeg", "image/png"})
_PDF_MIME_TYPE = "application/pdf"

_SYSTEM_PROMPT = """You are a receipt data extraction assistant. Given a receipt image \
or PDF, respond with ONLY a single JSON object (no markdown fences, no prose) matching \
this exact shape:

{
  "merchant_name": string or null,
  "receipt_date": "YYYY-MM-DD" or null,
  "subtotal": number or null,
  "tax_amount": number or null,
  "total_amount": number or null,
  "currency": "ISO-4217 code" or null,
  "line_items": [
    {"description": string, "quantity": number, "unit_price": number, "amount": number}
  ],
  "confidence": {
    "merchant_name": 0-1, "receipt_date": 0-1, "subtotal": 0-1,
    "tax_amount": 0-1, "total_amount": 0-1, "currency": 0-1
  },
  "raw_text": string
}

Use your own reading of the document for raw_text. If a field cannot be determined, \
set it to null and give it a low confidence score. Respond with the JSON object only."""


def _strip_code_fence(text: str) -> str:
    """Remove a surrounding triple-backtick fence from a model response, if present."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _parse_result(text: str) -> ExtractionResult:
    """Safely parse a model's JSON text response into an ExtractionResult."""
    cleaned = _strip_code_fence(text)
    try:
        payload: dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ExtractionError("Claude extractor returned non-JSON output") from exc
    try:
        return ExtractionResult.model_validate(payload)
    except SchemaValidationError as exc:
        raise ExtractionError(
            "Claude extractor output did not match the expected schema"
        ) from exc


def _build_content_block(file_bytes: bytes, mime_type: str) -> dict[str, Any]:
    """Build the Anthropic content block (image or document) for the given file."""
    encoded = base64.standard_b64encode(file_bytes).decode("ascii")
    source = {"type": "base64", "media_type": mime_type, "data": encoded}
    if mime_type in _IMAGE_MIME_TYPES:
        return {"type": "image", "source": source}
    if mime_type == _PDF_MIME_TYPE:
        return {"type": "document", "source": source}
    raise ExtractionError(f"Unsupported mime type for Claude extraction: {mime_type}")


class ClaudeExtractor:
    """ReceiptExtractor backed by the Anthropic Messages API."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Create a ClaudeExtractor using the given Settings, or the global default."""
        self._settings = settings or get_settings()
        client_kwargs: dict[str, Any] = {
            "api_key": self._settings.anthropic_api_key,
            "timeout": REQUEST_TIMEOUT_SECONDS,
        }
        self._client = anthropic.AsyncAnthropic(**client_kwargs)

    async def extract(self, file_bytes: bytes, mime_type: str) -> ExtractionResult:
        """Extract receipt fields via the Anthropic API, retrying transient failures."""
        content_block = _build_content_block(file_bytes, mime_type)
        last_error: Exception | None = None

        messages_payload: list[Any] = [
            {
                "role": "user",
                "content": [
                    content_block,
                    {"type": "text", "text": "Extract this receipt's fields."},
                ],
            }
        ]

        for _attempt in range(MAX_ATTEMPTS):
            try:
                message = await self._client.messages.create(
                    model=self._settings.anthropic_model,
                    max_tokens=MAX_OUTPUT_TOKENS,
                    system=_SYSTEM_PROMPT,
                    messages=messages_payload,
                )
            except anthropic.APIError as exc:
                last_error = exc
                continue

            text = "".join(
                block.text for block in message.content if block.type == "text"
            )
            return _parse_result(text)

        logger.warning("Claude extraction failed after %d attempts", MAX_ATTEMPTS)
        raise ExtractionError("Claude extraction failed after retries") from last_error
