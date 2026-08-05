from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Consistent error envelope returned by the API."""

    detail: Any


ERROR_RESPONSES: dict[int, dict[str, object]] = {
    400: {"model": ErrorResponse, "description": "Bad request"},
    401: {"model": ErrorResponse, "description": "Authentication failed"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    409: {"model": ErrorResponse, "description": "Resource conflict"},
    413: {"model": ErrorResponse, "description": "Payload too large"},
    415: {"model": ErrorResponse, "description": "Unsupported media type"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    500: {"model": ErrorResponse, "description": "Internal server error"},
    503: {"model": ErrorResponse, "description": "Dependency unavailable"},
}


def responses_for(*status_codes: int) -> dict[int, dict[str, object]]:
    """Select documented error responses for one endpoint."""
    return {status_code: ERROR_RESPONSES[status_code] for status_code in status_codes}
