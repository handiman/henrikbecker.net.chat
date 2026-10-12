import sys
import types
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

# `workers` only imports inside the Pyodide runtime, so stub what main.py needs.
_workers = types.ModuleType("workers")
_asgi = types.ModuleType("workers.asgi")
_asgi.entrypoint = lambda app: app
_workers.asgi = _asgi
sys.modules.setdefault("workers", _workers)
sys.modules.setdefault("workers.asgi", _asgi)

from main import app  # noqa: E402


class FakeRateLimiter:
    def __init__(self, allowed: int) -> None:
        self.allowed = allowed
        self.calls = 0

    async def limit(self, key: str) -> SimpleNamespace:
        self.calls += 1
        return SimpleNamespace(success=self.calls <= self.allowed)


class InjectEnv:
    """ASGI middleware that adds the Workers `env` to the scope, as the runtime does."""

    limiter = FakeRateLimiter(allowed=1000)

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        scope["env"] = SimpleNamespace(RATE_LIMITER=self.limiter)
        await self.app(scope, receive, send)


app.add_middleware(InjectEnv)


@pytest.fixture
def client() -> TestClient:
    InjectEnv.limiter = FakeRateLimiter(allowed=1000)
    return TestClient(app)


@pytest.fixture
def limited_client() -> TestClient:
    InjectEnv.limiter = FakeRateLimiter(allowed=1)
    return TestClient(app)
