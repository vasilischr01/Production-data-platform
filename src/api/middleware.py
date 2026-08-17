import logging
from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.request_context import (
    generate_request_id,
    reset_request_id,
    set_request_id,
)

logger = logging.getLogger(
    __name__
)

class RequestIDMiddleware(
    BaseHTTPMiddleware
):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[
            [Request],
            Awaitable[Response],
        ],
    ) -> Response:
        request_id = request.headers.get(
            "X-Request-ID"
        )

        if not request_id:
            request_id = generate_request_id()

        context_token = set_request_id(
            request_id
        )

        request.state.request_id = request_id

        start_time = perf_counter()

        logger.info(
            "Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
            },
        )
        try:
            response = await call_next(
                request
            )
            duration_ms = (
                perf_counter()
                - start_time
            ) * 1000

            logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": (
                        response.status_code
                    ),
                    "duration_ms": round(
                        duration_ms,
                        2,
                    ),
                },
            )
        finally:
            reset_request_id(
                context_token
            )

        response.headers[
            "X-Request-ID"
        ] = request_id

        return response