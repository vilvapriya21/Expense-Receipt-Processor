"""Dependency wiring for the receipts feature's service layer."""

import anthropic
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.extraction.base import ReceiptExtractor
from app.extraction.dependencies import get_extractor
from app.repositories.category_repository import CategoryRepository
from app.repositories.receipt_repository import ReceiptRepository
from app.services.categorization_service import CategorizationService
from app.services.receipt_service import ReceiptService


def get_categorization_llm_client(
    settings: Settings = Depends(get_settings),
) -> anthropic.AsyncAnthropic | None:
    """Build the optional request-scoped client used for category fallback."""
    if not settings.anthropic_api_key:
        return None
    return anthropic.AsyncAnthropic(
        api_key=settings.anthropic_api_key,
        timeout=15.0,
    )


def get_receipt_service(
    session: AsyncSession = Depends(get_db),
    extractor: ReceiptExtractor = Depends(get_extractor),
    settings: Settings = Depends(get_settings),
    categorization_llm_client: anthropic.AsyncAnthropic | None = Depends(
        get_categorization_llm_client
    ),
) -> ReceiptService:
    """Build a ReceiptService wired to request-scoped repositories and the extractor."""
    category_repository = CategoryRepository(session)
    categorization_service = CategorizationService(
        category_repository, settings, categorization_llm_client
    )
    receipt_repository = ReceiptRepository(session)
    return ReceiptService(
        receipt_repository, extractor, categorization_service, settings
    )
