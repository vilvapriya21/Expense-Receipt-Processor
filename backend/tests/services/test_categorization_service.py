"""Tests for CategorizationService: keyword matching and the LLM fallback."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx2
import pytest
from anthropic import APIConnectionError
from tests.fakes import FakeCategoryProvider

from app.core.config import Settings
from app.services.categorization_service import (
    CategorizationService,
    CategoryOption,
)


def _text_block(text: str) -> SimpleNamespace:
    """Build a fake Anthropic content block of type 'text'."""
    return SimpleNamespace(type="text", text=text)


def _mock_anthropic() -> MagicMock:
    """Build an injected mock Anthropic client for a test."""
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock()
    return mock_client


async def test_suggest_category_keyword_match_skips_llm() -> None:
    """A single keyword match is confident enough to skip the LLM entirely."""
    mock_client = _mock_anthropic()
    categories = [CategoryOption(id=1, name="Meals", keywords=["coffee"])]
    service = CategorizationService(
        FakeCategoryProvider(categories),
        Settings(anthropic_api_key="test-key"),
        mock_client,
    )

    suggestion = await service.suggest_category("Blue Bottle Coffee Shop", "text")

    assert suggestion.category_id == 1
    assert suggestion.category_name == "Meals"
    assert suggestion.confidence == pytest.approx(0.7)
    mock_client.messages.create.assert_not_called()


async def test_suggest_category_multiple_keyword_matches_confidence_capped() -> None:
    """Confidence rises with each matching keyword but never exceeds the cap."""
    categories = [
        CategoryOption(
            id=2, name="Office", keywords=["office", "depot", "paper", "toner"]
        )
    ]
    service = CategorizationService(
        FakeCategoryProvider(categories), Settings(anthropic_api_key=None)
    )

    suggestion = await service.suggest_category("Office Depot Paper Toner", "text")

    assert suggestion.category_id == 2
    assert suggestion.confidence == pytest.approx(0.95)


async def test_suggest_category_no_merchant_name_returns_null_without_llm() -> None:
    """A missing merchant_name never matches a keyword; no API key skips the LLM."""
    mock_client = _mock_anthropic()
    categories = [CategoryOption(id=3, name="Travel", keywords=["hotel"])]
    service = CategorizationService(
        FakeCategoryProvider(categories), Settings(anthropic_api_key=None)
    )

    suggestion = await service.suggest_category(None, "text")

    assert suggestion.category_id is None
    assert suggestion.confidence == 0.0
    mock_client.messages.create.assert_not_called()


async def test_suggest_category_no_match_and_no_api_key_returns_null() -> None:
    """A merchant that matches nothing, with no API key configured, skips the LLM."""
    mock_client = _mock_anthropic()
    categories = [CategoryOption(id=3, name="Travel", keywords=["hotel"])]
    service = CategorizationService(
        FakeCategoryProvider(categories), Settings(anthropic_api_key=None)
    )

    suggestion = await service.suggest_category("Random Shop", "text")

    assert suggestion.category_id is None
    assert suggestion.category_name is None
    assert suggestion.confidence == 0.0
    mock_client.messages.create.assert_not_called()


async def test_suggest_category_llm_fallback_matches_restricted_category_list() -> None:
    """The LLM is offered only the active category names; its pick is matched back."""
    mock_client = _mock_anthropic()
    mock_client.messages.create.return_value = SimpleNamespace(
        content=[
            _text_block(json.dumps({"category_name": "Lodging", "confidence": 0.8}))
        ]
    )
    categories = [
        CategoryOption(id=4, name="Lodging", keywords=[]),
        CategoryOption(id=5, name="Meals", keywords=[]),
    ]
    service = CategorizationService(
        FakeCategoryProvider(categories),
        Settings(anthropic_api_key="test-key"),
        mock_client,
    )

    suggestion = await service.suggest_category("Hotel Metropole", "raw text")

    assert suggestion.category_id == 4
    assert suggestion.category_name == "Lodging"
    assert suggestion.confidence == pytest.approx(0.8)
    prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "Lodging" in prompt
    assert "Meals" in prompt


async def test_suggest_category_llm_unknown_category_falls_back() -> None:
    """If the LLM picks a category outside the restricted list, the fallback is kept."""
    mock_client = _mock_anthropic()
    mock_client.messages.create.return_value = SimpleNamespace(
        content=[
            _text_block(json.dumps({"category_name": "NotInList", "confidence": 0.9}))
        ]
    )
    categories = [CategoryOption(id=6, name="Lodging", keywords=[])]
    service = CategorizationService(
        FakeCategoryProvider(categories),
        Settings(anthropic_api_key="test-key"),
        mock_client,
    )

    suggestion = await service.suggest_category("Unknown Merchant", "raw text")

    assert suggestion.category_id is None
    assert suggestion.confidence == 0.0


async def test_suggest_category_llm_non_json_response_falls_back() -> None:
    """A non-JSON LLM response is treated as no suggestion, falling back."""
    mock_client = _mock_anthropic()
    mock_client.messages.create.return_value = SimpleNamespace(
        content=[_text_block("not json at all")]
    )
    categories = [CategoryOption(id=7, name="Lodging", keywords=[])]
    service = CategorizationService(
        FakeCategoryProvider(categories),
        Settings(anthropic_api_key="test-key"),
        mock_client,
    )

    suggestion = await service.suggest_category("Unknown Merchant", "raw text")

    assert suggestion.category_id is None
    assert suggestion.confidence == 0.0


async def test_suggest_category_llm_schema_mismatch_falls_back() -> None:
    """An LLM response that doesn't match the expected schema falls back."""
    mock_client = _mock_anthropic()
    mock_client.messages.create.return_value = SimpleNamespace(
        content=[_text_block(json.dumps({"category_name": "Lodging"}))]
    )
    categories = [CategoryOption(id=8, name="Lodging", keywords=[])]
    service = CategorizationService(
        FakeCategoryProvider(categories),
        Settings(anthropic_api_key="test-key"),
        mock_client,
    )

    suggestion = await service.suggest_category("Unknown Merchant", "raw text")

    assert suggestion.category_id is None
    assert suggestion.confidence == 0.0


async def test_suggest_category_llm_api_error_falls_back() -> None:
    """A transient Anthropic API error during category suggestion falls back."""
    mock_client = _mock_anthropic()
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    mock_client.messages.create.side_effect = APIConnectionError(request=request)
    categories = [CategoryOption(id=9, name="Lodging", keywords=[])]
    service = CategorizationService(
        FakeCategoryProvider(categories),
        Settings(anthropic_api_key="test-key"),
        mock_client,
    )

    suggestion = await service.suggest_category("Unknown Merchant", "raw text")

    assert suggestion.category_id is None
    assert suggestion.confidence == 0.0


@pytest.mark.parametrize(
    ("llm_confidence", "expected"), [(1.5, 1.0), (-0.2, 0.0), (0.5, 0.5)]
)
async def test_suggest_category_llm_confidence_is_clamped(
    llm_confidence: float, expected: float
) -> None:
    """The LLM's self-reported confidence is clamped into the valid [0, 1] range."""
    mock_client = _mock_anthropic()
    mock_client.messages.create.return_value = SimpleNamespace(
        content=[
            _text_block(
                json.dumps({"category_name": "Lodging", "confidence": llm_confidence})
            )
        ]
    )
    categories = [CategoryOption(id=10, name="Lodging", keywords=[])]
    service = CategorizationService(
        FakeCategoryProvider(categories),
        Settings(anthropic_api_key="test-key"),
        mock_client,
    )

    suggestion = await service.suggest_category("Unknown Merchant", "raw text")

    assert suggestion.confidence == pytest.approx(expected)


async def test_suggest_category_llm_response_code_fenced_is_parsed() -> None:
    """A fenced ```json LLM response is parsed correctly after fence stripping."""
    mock_client = _mock_anthropic()
    fenced = (
        "```json\n"
        + json.dumps({"category_name": "Lodging", "confidence": 0.75})
        + "\n```"
    )
    mock_client.messages.create.return_value = SimpleNamespace(
        content=[_text_block(fenced)]
    )
    categories = [CategoryOption(id=11, name="Lodging", keywords=[])]
    service = CategorizationService(
        FakeCategoryProvider(categories),
        Settings(anthropic_api_key="test-key"),
        mock_client,
    )

    suggestion = await service.suggest_category("Unknown Merchant", "raw text")

    assert suggestion.category_id == 11
    assert suggestion.confidence == pytest.approx(0.75)
