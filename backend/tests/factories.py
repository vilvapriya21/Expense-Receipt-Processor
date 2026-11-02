"""Factory helpers for test data: ORM rows and canonical extraction fixtures."""

import itertools
import json
from pathlib import Path
from typing import Any

from app.core.security import hash_password
from app.models.category import Category
from app.models.enums import ReceiptStatus, UserRole
from app.models.receipt import Receipt
from app.models.user import User
from app.schemas.extraction import ExtractionResult

FIXTURES_DIR = (
    Path(__file__).resolve().parents[2]
    / ".claude"
    / "skills"
    / "receipt-extraction"
    / "fixtures"
)

# Not a real credential — a fixed low-entropy placeholder used only to satisfy the
# User.hashed_password column for factory-built rows in tests.
_PLACEHOLDER_PASSWORD = "placeholder"

_sequence = itertools.count(1)


def make_user(
    *,
    email: str | None = None,
    role: UserRole = UserRole.EMPLOYEE,
    full_name: str = "Test User",
) -> User:
    """Build an unsaved User ORM instance with sensible defaults."""
    number = next(_sequence)
    return User(
        email=email or f"user{number}@example.com",
        full_name=full_name,
        hashed_password=hash_password(_PLACEHOLDER_PASSWORD),
        role=role,
    )


def make_category(
    *,
    name: str | None = None,
    keywords: list[str] | None = None,
    is_active: bool = True,
) -> Category:
    """Build an unsaved Category ORM instance with sensible defaults."""
    number = next(_sequence)
    return Category(
        name=name or f"Category {number}",
        description=None,
        keywords=keywords or [],
        is_active=is_active,
    )


def make_receipt(
    *, owner_id: int, status: ReceiptStatus = ReceiptStatus.UPLOADED, **overrides: Any
) -> Receipt:
    """Build an unsaved Receipt ORM instance owned by owner_id."""
    number = next(_sequence)
    defaults: dict[str, Any] = {
        "owner_id": owner_id,
        "file_path": f"/tmp/receipt-{number}.pdf",
        "original_filename": f"receipt-{number}.pdf",
        "mime_type": "application/pdf",
        "status": status,
        "needs_review": False,
    }
    defaults.update(overrides)
    return Receipt(**defaults)


def load_extraction_fixture(
    name: str,
) -> tuple[ExtractionResult, dict[str, Any] | None]:
    """Load a fixture JSON as an ExtractionResult, plus its expected_validation."""
    payload = json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))
    expected_validation = payload.pop("expected_validation", None)
    return ExtractionResult.model_validate(payload), expected_validation
