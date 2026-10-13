from types import SimpleNamespace

import pytest

from api.v1.ai import AZURE_URL, get_fetch
from main import app

ALLOWED = "https://henrikbecker.net"


class FakeUpstream:
    def __init__(self, body: bytes = b'{"answer": "hi"}', status: int = 200) -> None:
        self.status = status
        self.headers = {"content-type": "application/json"}
        self._body = body

    async def bytes(self) -> bytes:
        return self._body


@pytest.fixture
def upstream():
    calls: list[tuple[str, dict]] = []
    response = FakeUpstream()

    async def fake_fetch(url, **kwargs):
        calls.append((url, kwargs))
        return response

    app.dependency_overrides[get_fetch] = lambda: fake_fetch
    yield SimpleNamespace(calls=calls, response=response)
    app.dependency_overrides.pop(get_fetch, None)


@pytest.mark.parametrize(
    ("path", "azure_action"),
    [("ask", "ask"), ("ingest", "ingest"), ("ingress", "ingest")],
)
def test_forwards_to_azure(client, upstream, path, azure_action):
    action = azure_action
    response = client.post(f"/{path}/docs", json={"q": "hello"})

    assert response.status_code == 200
    assert response.json() == {"answer": "hi"}
    [(url, kwargs)] = upstream.calls
    assert url == f"{AZURE_URL}/ai/{action}/docs"
    assert kwargs["method"] == "POST"
    assert kwargs["body"] == b'{"q":"hello"}'
    assert kwargs["headers"]["content-type"] == "application/json"
    assert "host" not in {k.lower() for k in kwargs["headers"]}


def test_passes_through_upstream_status(client, upstream):
    upstream.response.status = 502
    response = client.post("/ask/docs", json={})
    assert response.status_code == 502


def test_cors_preflight_allows_post(client, upstream):
    response = client.options(
        "/ask/docs",
        headers={"Origin": ALLOWED, "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED
    assert not upstream.calls


def test_rate_limited(limited_client, upstream):
    assert limited_client.post("/ask/docs", json={}).status_code == 200
    assert limited_client.post("/ask/docs", json={}).status_code == 429
    assert len(upstream.calls) == 1
