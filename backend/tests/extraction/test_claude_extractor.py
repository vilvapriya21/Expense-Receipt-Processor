"""Tests for the Claude (Anthropic) receipt extractor."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx2
import pytest
from anthropic import APIConnectionError

from app.core.config import Settings
from app.extraction.base import ExtractionError
from app.extraction.claude_extractor import (
    MAX_ATTEMPTS,
    ClaudeExtractor,
    _parse_result,
    _strip_code_fence,
)

CLEAN_PAYLOAD = {
    "merchant_name": "Blue Bottle Coffee",
    "receipt_date": "2026-10-12",
    "subtotal": 24.50,
    "tax_amount": 2.20,
    "total_amount": 26.70,
    "currency": "USD",
    "line_items": [],
    "confidence": {
        "merchant_name": 0.97,
        "receipt_date": 0.95,
        "subtotal": 0.93,
        "tax_amount": 0.90,
        "total_amount": 0.96,
        "currency": 0.99,
    },
    "raw_text": "BLUE BOTTLE COFFEE",
}


def _text_block(text: str) -> SimpleNamespace:
    """Build a fake Anthropic content block of type 'text'."""
    return SimpleNamespace(type="text", text=text)


def _settings() -> Settings:
    """Build Settings with a dummy Anthropic API key configured."""
    return Settings(anthropic_api_key="test-key", anthropic_model="claude-sonnet-5")


def _request() -> httpx2.Request:
    """Build a throwaway request for constructing Anthropic API errors."""
    return httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def test_strip_code_fence_fenced_text_removes_fence() -> None:
    """A ```json fenced block has its fences stripped, leaving only the JSON body."""
    fenced = '```json\n{"a": 1}\n```'
    assert _strip_code_fence(fenced) == '{"a": 1}'


def test_strip_code_fence_plain_text_returns_unchanged() -> None:
    """Text with no code fence is returned stripped but otherwise unchanged."""
    assert _strip_code_fence('  {"a": 1}  ') == '{"a": 1}'


def test_parse_result_valid_json_returns_extraction_result() -> None:
    """A well-formed JSON payload parses into a matching ExtractionResult."""
    result = _parse_result(json.dumps(CLEAN_PAYLOAD))
    assert result.merchant_name == "Blue Bottle Coffee"
    assert result.total_amount == 26.70


def test_parse_result_non_json_raises_extraction_error() -> None:
    """Non-JSON model output raises ExtractionError."""
    with pytest.raises(ExtractionError):
        _parse_result("not json at all")


def test_parse_result_schema_mismatch_raises_extraction_error() -> None:
    """JSON that doesn't match ExtractionResult's schema raises ExtractionError."""
    with pytest.raises(ExtractionError):
        _parse_result(json.dumps({"unknown_field": "oops"}))


@pytest.mark.parametrize(
    ("mime_type", "expected_block_type"),
    [
        ("image/jpeg", "image"),
        ("image/png", "image"),
        ("application/pdf", "document"),
    ],
)
async def test_extract_success_returns_result_for_each_supported_mime_type(
    monkeypatch: pytest.MonkeyPatch, mime_type: str, expected_block_type: str
) -> None:
    """A successful API call returns the parsed result, with the right content block."""
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(
        return_value=SimpleNamespace(content=[_text_block(json.dumps(CLEAN_PAYLOAD))])
    )
    monkeypatch.setattr(
        "app.extraction.claude_extractor.anthropic.AsyncAnthropic",
        MagicMock(return_value=mock_client),
    )

    extractor = ClaudeExtractor(_settings())
    result = await extractor.extract(b"fake-bytes", mime_type)

    assert result.merchant_name == "Blue Bottle Coffee"
    sent_messages = mock_client.messages.create.call_args.kwargs["messages"]
    assert sent_messages[0]["content"][0]["type"] == expected_block_type


async def test_extract_strips_code_fence_from_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fenced ```json response is parsed correctly after fence stripping."""
    fenced_text = "```json\n" + json.dumps(CLEAN_PAYLOAD) + "\n```"
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(
        return_value=SimpleNamespace(content=[_text_block(fenced_text)])
    )
    monkeypatch.setattr(
        "app.extraction.claude_extractor.anthropic.AsyncAnthropic",
        MagicMock(return_value=mock_client),
    )

    extractor = ClaudeExtractor(_settings())
    result = await extractor.extract(b"fake-bytes", "image/png")

    assert result.currency == "USD"


async def test_extract_unsupported_mime_type_raises_without_calling_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unsupported mime type raises ExtractionError without calling the API."""
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock()
    monkeypatch.setattr(
        "app.extraction.claude_extractor.anthropic.AsyncAnthropic",
        MagicMock(return_value=mock_client),
    )

    extractor = ClaudeExtractor(_settings())
    with pytest.raises(ExtractionError):
        await extractor.extract(b"fake-bytes", "text/plain")
    mock_client.messages.create.assert_not_called()


async def test_extract_persistent_api_error_retries_then_raises_extraction_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Persistent Anthropic API errors are retried MAX_ATTEMPTS times then raise."""
    api_error = APIConnectionError(request=_request())
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(side_effect=api_error)
    monkeypatch.setattr(
        "app.extraction.claude_extractor.anthropic.AsyncAnthropic",
        MagicMock(return_value=mock_client),
    )

    extractor = ClaudeExtractor(_settings())
    with pytest.raises(ExtractionError) as exc_info:
        await extractor.extract(b"fake-bytes", "image/png")

    assert mock_client.messages.create.call_count == MAX_ATTEMPTS
    assert exc_info.value.__cause__ is api_error


async def test_extract_transient_api_error_is_retried_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A transient API error on the first attempt is retried and can still succeed."""
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(
        side_effect=[
            APIConnectionError(request=_request()),
            SimpleNamespace(content=[_text_block(json.dumps(CLEAN_PAYLOAD))]),
        ]
    )
    monkeypatch.setattr(
        "app.extraction.claude_extractor.anthropic.AsyncAnthropic",
        MagicMock(return_value=mock_client),
    )

    extractor = ClaudeExtractor(_settings())
    result = await extractor.extract(b"fake-bytes", "image/png")

    assert result.merchant_name == "Blue Bottle Coffee"
    assert mock_client.messages.create.call_count == 2
