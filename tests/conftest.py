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

INGEST_TOKEN = "test-ingest-token"


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
    ask_limiter = FakeRateLimiter(allowed=1000)
    ingest_token = INGEST_TOKEN
    allow_localhost: str | None = None  # the ALLOW_LOCALHOST var; unset in production

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        env = SimpleNamespace(
            RATE_LIMITER=self.limiter,
            ASK_RATE_LIMITER=self.ask_limiter,
            INGEST_TOKEN=self.ingest_token,
            CV_KV=None,  # tests override get_store; a real KV only exists in the runtime
        )
        if self.allow_localhost is not None:
            env.ALLOW_LOCALHOST = self.allow_localhost
        scope["env"] = env
        await self.app(scope, receive, send)


app.add_middleware(InjectEnv)


def _client(
    *, allowed: int = 1000, ask_allowed: int = 1000, allow_localhost: str | None = None
) -> TestClient:
    InjectEnv.limiter = FakeRateLimiter(allowed=allowed)
    InjectEnv.ask_limiter = FakeRateLimiter(allowed=ask_allowed)
    InjectEnv.ingest_token = INGEST_TOKEN
    InjectEnv.allow_localhost = allow_localhost
    return TestClient(app)


@pytest.fixture
def client() -> TestClient:
    return _client()


@pytest.fixture
def limited_client() -> TestClient:
    return _client(allowed=1)


@pytest.fixture
def ask_limited_client() -> TestClient:
    return _client(ask_allowed=1)


@pytest.fixture
def make_client():
    """Builds a client with the given ALLOW_LOCALHOST var; resets the shared env afterwards."""
    yield lambda allow_localhost=None: _client(allow_localhost=allow_localhost)
    InjectEnv.allow_localhost = None
