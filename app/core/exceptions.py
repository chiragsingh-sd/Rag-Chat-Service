from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger: logging.Logger = logging.getLogger(__name__)


class ServiceUnavailableError(Exception):
    """Raised when a required external service cannot complete a request."""

    def __init__(self, service: str) -> None:
        self.service = service
        super().__init__(service)


def register_exception_handlers(app: FastAPI) -> None:
    """Register safe, consistent JSON responses for application failures."""

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        _: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": jsonable_encoder(exc.detail)},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(ServiceUnavailableError)
    async def handle_service_unavailable(
        request: Request,
        exc: ServiceUnavailableError,
    ) -> JSONResponse:
        logger.error(
            "Service unavailable service=%s path=%s",
            exc.service,
            request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": f"{exc.service} unavailable"},
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_database_error(
        request: Request,
        _: SQLAlchemyError,
    ) -> JSONResponse:
        logger.exception("Database operation failed path=%s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Database unavailable"},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request,
        _: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled application error path=%s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
