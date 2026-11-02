"""Shared enums used across models (kept separate to avoid circular imports)."""

import enum


class UserRole(str, enum.Enum):
    """A user's permission level."""

    EMPLOYEE = "EMPLOYEE"
    ADMIN = "ADMIN"


class ReceiptStatus(str, enum.Enum):
    """A receipt's position in its review lifecycle."""

    UPLOADED = "UPLOADED"
    EXTRACTED = "EXTRACTED"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
