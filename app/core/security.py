import base64
import secrets

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import get_settings


class AdminBasicAuthMiddleware:
    """Protect the operator UI/API while leaving health and provider webhooks reachable."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        settings = get_settings()
        path = scope.get("path", "")
        if (
            scope["type"] != "http"
            or not settings.auth_enabled
            or path == "/health"
            or path.startswith("/api/webhooks/")
        ):
            await self.app(scope, receive, send)
            return

        header = Headers(scope=scope).get("authorization", "")
        authenticated = False
        if header.lower().startswith("basic "):
            try:
                decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
                username, password = decoded.split(":", 1)
                authenticated = secrets.compare_digest(username, settings.admin_username) and secrets.compare_digest(
                    password, settings.admin_password.get_secret_value()
                )
            except (ValueError, UnicodeDecodeError):
                authenticated = False

        if not authenticated:
            response = JSONResponse(
                {"detail": "Authentication required"},
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="LeadPulse Nexus"'},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
