"""Application factory: creates and configures the FastAPI app."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.categories import router as categories_router
from app.routers.receipts import router as receipts_router


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    settings = get_settings()
    configure_logging()

    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=settings.cors_allowed_methods,
        allow_headers=settings.cors_allowed_headers,
    )

    register_exception_handlers(app)

    app.include_router(auth_router)
    app.include_router(categories_router)
    app.include_router(receipts_router)
    app.include_router(admin_router)

    return app


app = create_app()
