"""Custom exception hierarchy and FastAPI handlers mapping them to a JSON envelope."""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("app")


class AppError(Exception):
    """Base class for all domain/application errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Create an AppError with a message and optional structured details."""
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ValidationError(AppError):
    """Raised when input fails a domain validation rule."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "validation_error"


class UnauthorizedError(AppError):
    """Raised when authentication is missing or invalid."""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"


class ForbiddenError(AppError):
    """Raised when an authenticated user lacks permission for an action."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"


class ConflictError(AppError):
    """Raised when a request conflicts with the current state of a resource."""

    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class InvalidStatusTransitionError(AppError):
    """Raised when an action would move a stateful resource to a disallowed status."""

    status_code = status.HTTP_409_CONFLICT
    code = "invalid_status_transition"


def _envelope(
    code: str, message: str, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build the project's standard error response body."""
    return {"code": code, "message": message, "details": details or {}}


async def handle_app_error(request: Request, exc: Exception) -> JSONResponse:
    """Map an AppError to the standard JSON error envelope."""
    if not isinstance(exc, AppError):
        raise TypeError("handle_app_error registered for a non-AppError exception")
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(exc.code, exc.message, exc.details),
    )


async def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    """Map a FastAPI/Pydantic request validation error to the standard envelope."""
    if not isinstance(exc, RequestValidationError):
        raise TypeError(
            "handle_validation_error registered for the wrong exception type"
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_envelope(
            "validation_error", "Request validation failed", {"errors": exc.errors()}
        ),
    )


async def handle_unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    """Map any uncaught exception to a generic envelope, never leaking internals."""
    logger.exception(
        "Unhandled error while processing %s %s", request.method, request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_envelope("internal_error", "An unexpected error occurred."),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all AppError subclasses and fallback handlers on the given app."""
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(Exception, handle_unhandled_error)
