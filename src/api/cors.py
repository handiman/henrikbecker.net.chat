from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send


class EnvCORSMiddleware:
    """CORS with an extra set of dev-only origins, enabled by the `ALLOW_LOCALHOST` env var.

    Workers bindings and vars only exist per request (`scope["env"]`), so the choice can't be made
    when the app is built. Both middlewares are built up front and one is picked per request.
    """

    def __init__(
        self, app: ASGIApp, *, allow_origins: list[str], dev_origins: list[str], **options
    ) -> None:
        self.prod = CORSMiddleware(app, allow_origins=allow_origins, **options)
        self.dev = CORSMiddleware(app, allow_origins=[*allow_origins, *dev_origins], **options)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        env = scope.get("env")  # absent for lifespan events
        dev = str(getattr(env, "ALLOW_LOCALHOST", "")).lower() == "true"
        await (self.dev if dev else self.prod)(scope, receive, send)
