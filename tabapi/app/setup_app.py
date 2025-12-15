from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from tabapi.app.core.config import settings
from tabapi.app.core.logger import get_logger
from tabapi.app.modules.auth.router import protected_router as auth_protected_router
from tabapi.app.modules.auth.router import public_router as auth_public_router
from tabapi.app.routes import api_router

logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.APP_VERSION,
        docs_url=None if settings.is_prod() else "/docs",
        redoc_url=None if settings.is_prod() else "/redoc",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )
    setup_routers(app)
    setup_middlewares(app)
    return app


def setup_routers(app: FastAPI) -> None:
    # System routes
    app.include_router(api_router, prefix=settings.API_V1_STR)
    # Auth public routes (no authentication required)
    app.include_router(auth_public_router)
    # Auth protected routes (authentication required)
    app.include_router(auth_protected_router)


def setup_middlewares(app) -> None:
    # CORS
    origins = []

    # Set all CORS enabled origins : adding security between Backend and Frontend
    if settings.BACKEND_CORS_ORIGINS:
        origins_raw = settings.BACKEND_CORS_ORIGINS.split(",")

        for origin in origins_raw:
            use_origin = origin.strip()
            origins.append(use_origin)

        logger.info(f"Allowed CORS origins: {origins}")

        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
