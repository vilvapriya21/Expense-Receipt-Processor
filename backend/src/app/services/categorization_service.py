"""Expense category suggestion: keyword/merchant match first, LLM fallback second."""

import json
import logging
from typing import Protocol

import anthropic
from pydantic import BaseModel, ConfigDict
from pydantic import ValidationError as SchemaValidationError

from app.core.config import Settings, get_settings

logger = logging.getLogger("app.services.categorization")

KEYWORD_CONFIDENCE_FLOOR = 0.6
KEYWORD_CONFIDENCE_STEP = 0.1
KEYWORD_CONFIDENCE_CAP = 0.95
LLM_FALLBACK_THRESHOLD = 0.6
MAX_OUTPUT_TOKENS = 512
REQUEST_TIMEOUT_SECONDS = 15.0


class CategoryOption(BaseModel):
    """The minimal category data the categorization service needs to match against."""

    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    keywords: list[str]


class CategorySuggestion(BaseModel):
    """Categorization output: a suggested category, or none, with a confidence score."""

    model_config = ConfigDict(extra="forbid")

    category_id: int | None
    category_name: str | None
    confidence: float


class CategoryProvider(Protocol):
    """Supplies the active categories to match against (implemented by a repository)."""

    async def list_active(self) -> list[CategoryOption]:
        """Return every active category available for suggestion."""
        ...


class _LlmCategoryChoice(BaseModel):
    """The shape expected back from the LLM category-suggestion prompt."""

    model_config = ConfigDict(extra="forbid")

    category_name: str | None
    confidence: float


def _normalize(text: str) -> str:
    """Lowercase and strip text for case-insensitive keyword matching."""
    return text.strip().lower()


def _match_by_keyword(
    merchant_name: str | None, categories: list[CategoryOption]
) -> CategorySuggestion:
    """Return the category with the most matching keywords in merchant_name, if any."""
    if not merchant_name:
        return CategorySuggestion(category_id=None, category_name=None, confidence=0.0)

    normalized_name = _normalize(merchant_name)
    best_category: CategoryOption | None = None
    best_match_count = 0

    for category in categories:
        match_count = sum(
            1 for kw in category.keywords if _normalize(kw) in normalized_name
        )
        if match_count > best_match_count:
            best_category = category
            best_match_count = match_count

    if best_category is None:
        return CategorySuggestion(category_id=None, category_name=None, confidence=0.0)

    confidence = min(
        KEYWORD_CONFIDENCE_CAP,
        KEYWORD_CONFIDENCE_FLOOR + KEYWORD_CONFIDENCE_STEP * best_match_count,
    )
    return CategorySuggestion(
        category_id=best_category.id,
        category_name=best_category.name,
        confidence=confidence,
    )


def _strip_code_fence(text: str) -> str:
    """Remove a surrounding triple-backtick fence from a model response, if present."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


class CategorizationService:
    """Suggests a category: keyword/merchant match first, LLM fallback second."""

    def __init__(
        self,
        category_provider: CategoryProvider,
        settings: Settings | None = None,
        llm_client: anthropic.AsyncAnthropic | None = None,
    ) -> None:
        """Create a CategorizationService backed by the given category provider."""
        self._category_provider = category_provider
        self._settings = settings or get_settings()
        self._llm_client = llm_client

    async def suggest_category(
        self, merchant_name: str | None, raw_text: str
    ) -> CategorySuggestion:
        """Suggest a category: try keyword matching first, then fall back to the LLM."""
        categories = await self._category_provider.list_active()

        suggestion = _match_by_keyword(merchant_name, categories)
        if suggestion.confidence >= LLM_FALLBACK_THRESHOLD:
            return suggestion

        client = self._llm_client
        if client is None:
            return suggestion

        return await self._suggest_via_llm(
            client, merchant_name, raw_text, categories, suggestion
        )

    async def _suggest_via_llm(
        self,
        client: anthropic.AsyncAnthropic,
        merchant_name: str | None,
        raw_text: str,
        categories: list[CategoryOption],
        fallback: CategorySuggestion,
    ) -> CategorySuggestion:
        """Ask the LLM for a category name, restricted to the active category list."""
        category_names = [category.name for category in categories]
        prompt = (
            "Pick the single best-fitting expense category for this receipt from the "
            f"following list ONLY: {category_names}. If none fit, use null for "
            "category_name. Receipt merchant: "
            f"{merchant_name or 'unknown'}. Receipt text excerpt: {raw_text[:500]!r}. "
            "Respond with ONLY a JSON object: "
            '{"category_name": <one of the list above, or null>, "confidence": <0-1>}'
        )
        try:
            message = await client.messages.create(
                model=self._settings.anthropic_model,
                max_tokens=MAX_OUTPUT_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APIError as exc:
            logger.warning("LLM category suggestion failed: %s", exc)
            return fallback

        text = "".join(block.text for block in message.content if block.type == "text")
        choice = self._parse_llm_choice(text)
        if choice is None or choice.category_name is None:
            return fallback

        matched = next(
            (
                c
                for c in categories
                if _normalize(c.name) == _normalize(choice.category_name)
            ),
            None,
        )
        if matched is None:
            return fallback

        clamped_confidence = max(0.0, min(1.0, choice.confidence))
        return CategorySuggestion(
            category_id=matched.id,
            category_name=matched.name,
            confidence=clamped_confidence,
        )

    def _parse_llm_choice(self, text: str) -> _LlmCategoryChoice | None:
        """Safely parse the LLM's JSON category-choice response."""
        cleaned = _strip_code_fence(text)
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("LLM category suggestion returned non-JSON output")
            return None
        try:
            return _LlmCategoryChoice.model_validate(payload)
        except SchemaValidationError:
            logger.warning(
                "LLM category suggestion output did not match the expected schema"
            )
            return None
