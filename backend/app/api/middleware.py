"""
API Middleware — Request ID and Timing.

Person 5 owns this file.
Provides per-request UUID tracking and wall-clock timing headers.
"""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.telemetry.logger import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique X-Request-ID to every request/response.

    - Reuses the client-supplied X-Request-ID header if present.
    - Stores the ID on ``request.state.request_id`` for downstream use.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Measure wall-clock processing time per request.

    Adds ``X-Process-Time`` header (milliseconds) to every response.
    Logs slow requests (>2 s) at WARNING level.
    """

    SLOW_THRESHOLD_MS = 2000

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        response.headers["X-Process-Time"] = str(elapsed_ms)

        if elapsed_ms > self.SLOW_THRESHOLD_MS:
            logger.warning(
                f"[Slow Request] {request.method} {request.url.path} "
                f"took {elapsed_ms}ms"
            )

        return response
