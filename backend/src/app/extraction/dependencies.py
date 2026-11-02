"""Dependency wiring that selects a ReceiptExtractor based on Settings."""

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.extraction.base import ReceiptExtractor
from app.extraction.claude_extractor import ClaudeExtractor
from app.extraction.text_fallback_extractor import TextFallbackExtractor


def get_extractor(settings: Settings = Depends(get_settings)) -> ReceiptExtractor:
    """Return the ReceiptExtractor selected by settings.extractor_provider.

    Falls back to the regex-based TextFallbackExtractor whenever no Anthropic API
    key is configured, regardless of extractor_provider, so the app still works.
    """
    if settings.extractor_provider == "anthropic" and settings.anthropic_api_key:
        return ClaudeExtractor(settings)
    return TextFallbackExtractor()
