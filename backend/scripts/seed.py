"""Idempotent seed script: 1 admin, 2 employees, and the default categories."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.logging import configure_logging, get_logger  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.user import User  # noqa: E402

logger = get_logger("seed")

SEED_PASSWORD: str = "ChangeMe123!"

DEFAULT_CATEGORIES: dict[str, list[str]] = {
    "Travel": [
        "flight",
        "airline",
        "airfare",
        "hotel",
        "rental car",
        "taxi",
        "uber",
        "lyft",
        "mileage",
        "parking",
        "train ticket",
    ],
    "Meals": [
        "restaurant",
        "cafe",
        "coffee",
        "lunch",
        "dinner",
        "catering",
        "doordash",
        "grubhub",
        "diner",
        "bakery",
    ],
    "Lodging": [
        "hotel",
        "motel",
        "lodging",
        "airbnb",
        "resort",
        "inn",
        "accommodation",
        "hostel",
    ],
    "Office Supplies": [
        "staples",
        "office depot",
        "paper",
        "pens",
        "printer",
        "toner",
        "stationery",
        "supplies",
        "ink cartridge",
    ],
    "Software": [
        "subscription",
        "saas",
        "license",
        "software",
        "app store",
        "github",
        "aws",
        "azure",
        "slack",
        "microsoft 365",
    ],
    "Transport": [
        "gas",
        "fuel",
        "parking",
        "toll",
        "metro",
        "transit",
        "train",
        "bus",
        "taxi",
        "uber",
        "rideshare",
    ],
    "Other": ["miscellaneous", "other", "general", "sundry", "uncategorized"],
}


async def _ensure_user(
    session: AsyncSession, email: str, full_name: str, role: UserRole
) -> None:
    """Create the given user if it does not already exist, by email."""
    existing = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if existing is not None:
        return
    pw_hash = hash_password(SEED_PASSWORD)
    new_user = User(email=email, full_name=full_name, role=role)
    new_user.hashed_password = pw_hash
    session.add(new_user)


async def _ensure_category(
    session: AsyncSession, name: str, keywords: list[str]
) -> None:
    """Create the given category if it does not already exist, by name."""
    existing = (
        await session.execute(select(Category).where(Category.name == name))
    ).scalar_one_or_none()
    if existing is not None:
        return
    session.add(Category(name=name, description=f"{name} expenses", keywords=keywords))


async def seed() -> None:
    """Seed the database with default users and categories, idempotently."""
    async with AsyncSessionLocal() as session:
        await _ensure_user(session, "admin@example.com", "Admin User", UserRole.ADMIN)
        await _ensure_user(
            session, "employee1@example.com", "Employee One", UserRole.EMPLOYEE
        )
        await _ensure_user(
            session, "employee2@example.com", "Employee Two", UserRole.EMPLOYEE
        )

        for name, keywords in DEFAULT_CATEGORIES.items():
            await _ensure_category(session, name, keywords)

        await session.commit()
    logger.info("Seed complete")


if __name__ == "__main__":
    configure_logging()
    asyncio.run(seed())
