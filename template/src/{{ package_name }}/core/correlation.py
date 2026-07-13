"""Correlation ID context and middleware for request tracing."""

from __future__ import annotations

import contextvars
import logging
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

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


class CorrelationIdMiddleware:
    """ASGI middleware that generates and propagates correlation IDs.

    Generates a correlation ID for each incoming HTTP request, stores it in a
    context variable for logging, and includes it in the response headers.
    Caller-supplied correlation/request ID headers are intentionally ignored.

    Implemented as a plain ASGI middleware rather than
    `starlette.middleware.base.BaseHTTPMiddleware`: `BaseHTTPMiddleware` runs
    the downstream app in a separate task and is documented to lose client
    disconnects (the handler keeps running instead of being cancelled) and to
    add response-buffering overhead. A raw ASGI middleware wraps the
    downstream `send` calls directly, so `await self.app(...)` doesn't return
    until the response — including any background task — has actually
    finished, and a single `try`/`finally` around it is enough to reset the
    context variable correctly on every path, including cancellation.

    Attributes:
        app (ASGIApp): Downstream ASGI application.
    """

    def __init__(self, app: ASGIApp) -> None:
        """Wraps the downstream ASGI application.

        Args:
            app (ASGIApp): Downstream ASGI application.

        Returns:
            None: The middleware is initialized in-place.
        """

        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Processes the request and injects a correlation ID.

        Args:
            scope (Scope): ASGI connection scope.
            receive (Receive): ASGI receive callable.
            send (Send): ASGI send callable.

        Returns:
            None: The response is sent through `send`, with the correlation
                ID header attached.
        """

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        correlation_id = str(uuid.uuid4())

        async def send_with_correlation_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.append(CORRELATION_ID_HEADER, correlation_id)
            await send(message)

        token = _correlation_id_var.set(correlation_id)
        try:
            LOGGER.debug("Correlation ID: %s", correlation_id)
            await self.app(scope, receive, send_with_correlation_id)
        finally:
            _correlation_id_var.reset(token)
