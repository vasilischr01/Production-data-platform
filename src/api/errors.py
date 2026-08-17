import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.request_context import get_request_id

logger = logging.getLogger(__name__)


def build_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details=None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    payload = {
        "error": {
            "code": code,
            "message": message,
        },
        "request_id": get_request_id(),
    }

    if details is not None:
        payload["error"]["details"] = details

    return JSONResponse(
        status_code=status_code,
        content=payload,
        headers=headers,
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    return build_error_response(
        status_code=exc.status_code,
        code="http_error",
        message=str(exc.detail),
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return build_error_response(
        status_code=422,
        code="validation_error",
        message="Request validation failed",
        details=exc.errors(),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception(
        "Unhandled application exception",
        extra={
            "method": request.method,
            "path": request.url.path,
        },
    )

    return build_error_response(
        status_code=500,
        code="internal_server_error",
        message="Internal server error",
    )