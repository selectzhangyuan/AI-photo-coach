"""请求日志 ASGI 中间件 —— 记录每个 HTTP 请求的摘要信息。

不记录 request body 和敏感 header（Authorization、Cookie 等）。
自动注入 request_id 到 contextvars，实现全链路追踪。
"""

import logging
import time

from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.request_id import generate_request_id, set_request_id

logger = logging.getLogger("app.middleware.request")


class RequestLoggingMiddleware:
    """纯 ASGI 中间件，记录 method、path、status_code、duration_ms。"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = generate_request_id()
        set_request_id(request_id)

        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")

        t0 = time.monotonic()
        status_code = 0

        async def wrapped_send(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        except Exception:
            status_code = 500
            raise
        finally:
            duration_ms = round((time.monotonic() - t0) * 1000)
            logger.info(
                "%s %s → %s (%sms)",
                method,
                path,
                status_code,
                duration_ms,
                extra={
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
