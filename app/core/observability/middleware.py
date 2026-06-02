"""
FastAPI middleware for request/response logging.
Every API request gets a unique request ID and is logged
with timing, status, and metadata.
"""
import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request with:
    - Unique request ID for tracing
    - Method, path and status code
    - Processing time in milliseconds
    - Client IP address

    In production this integrates with distributed tracing systems like Jaeger or Datadog APM.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]  # Short unique ID for easier log reading
        start_time = time.time()

        # Bind request context to all log calls in this request
        structlog.contextvars.bind_contextvars(request_id=request_id)

        logger.info(
            "request_start",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown"
        )
        try:
            response = await call_next(request)
            elapsed_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                latency_ms=elapsed_ms
            )

            # Add request ID to response headers for client-side tracing
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                latency_ms=elapsed_ms
            )
            raise
        finally:
            structlog.contextvars.clear_contextvars()
