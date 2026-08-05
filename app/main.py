import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.database.connection import engine
from app.routers.auth import router as auth_router
from app.routers.documents import router as documents_router
from app.routers.health import router as health_router

settings: Settings = get_settings()
configure_logging(settings)
logger: logging.Logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize and shut down application-level resources."""
    logger.info("Application started with %s database engine", engine.dialect.name)
    yield
    logger.info("Application stopped")


app: FastAPI = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(health_router)
