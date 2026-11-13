from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Set on every response, including 401/404/429 and CORS preflights.
SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "strict-transport-security": "max-age=31536000; includeSubDomains",
    # Blocks no-cors embedding (<script>, <img>) from other sites. CORS fetches are not affected.
    "cross-origin-resource-policy": "same-origin",
}


class SecurityHeadersMiddleware:
    """Adds `SECURITY_HEADERS` to every HTTP response, unless a route already set one."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                present = {name.lower() for name, _ in headers}
                for name, value in SECURITY_HEADERS.items():
                    if name.encode() not in present:
                        headers.append((name.encode(), value.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)
