"""Correlation ID context and middleware for request tracing."""

from __future__ import annotations

import contextvars
import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import override

from fastapi import Request
from starlette.background import BackgroundTask
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

LOGGER = logging.getLogger(__name__)

# Context variable to store correlation ID per request
_correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default="-"
)

# Standard response header name for correlation ID
CORRELATION_ID_HEADER = "x-correlation-id"


def get_correlation_id() -> str:
    """Retrieves the current request's correlation ID.

    Returns:
        str: The correlation ID for the current request context.
    """

    return _correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Sets the correlation ID for the current request context.

    Args:
        correlation_id (str): The correlation ID to set.

    Returns:
        None: The correlation ID is set in the context variable.
    """

    _correlation_id_var.set(correlation_id)


async def _reset_correlation_id_after_response(
    background_task: BackgroundTask | None,
    token: contextvars.Token[str],
) -> None:
    """Resets the correlation ID after the response has fully completed.

    Args:
        background_task (BackgroundTask | None): Existing response background task.
        token (contextvars.Token[str]): Token used to restore the previous value.

    Returns:
        None: Cleanup is performed after the response completes.
    """

    try:
        if background_task is not None:
            await background_task()
    finally:
        _correlation_id_var.reset(token)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and propagate correlation IDs for requests.

    This middleware generates a correlation ID for each incoming request, stores it
    in context variables for logging, and includes it in response headers.
    Caller-supplied correlation/request ID headers are intentionally ignored.
    """

    @override
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Processes the request and injects correlation ID.

        Args:
            request (Request): Incoming HTTP request.
            call_next (Callable[[Request], Awaitable[Response]]): Next
                middleware/route handler.

        Returns:
            Response: HTTP response with correlation ID header.
        """

        correlation_id = str(uuid.uuid4())

        token = _correlation_id_var.set(correlation_id)
        try:
            LOGGER.debug("Correlation ID: %s", correlation_id)
            response = await call_next(request)
        except Exception:
            _correlation_id_var.reset(token)
            raise
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        response.background = BackgroundTask(
            _reset_correlation_id_after_response, response.background, token
        )
        return response
