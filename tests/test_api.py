import pytest

from api.security_headers import SECURITY_HEADERS

ALLOWED = "https://henrikbecker.net"
TOOLS_LIST = {"jsonrpc": "2.0", "id": "1", "method": "tools/list"}


def mcp(client, **kwargs):
    """A cheap, rate-limited request that touches neither KV nor the model."""
    return client.post("/mcp", json=TOOLS_LIST, **kwargs)


def test_cors_allows_listed_origins(client):
    for origin in (ALLOWED, "https://becker-consulting.se"):
        response = mcp(client, headers={"Origin": origin})
        assert response.headers["access-control-allow-origin"] == origin


def test_cors_rejects_other_origins(client):
    response = mcp(client, headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_rate_limit_returns_429_with_cors_headers(limited_client):
    headers = {"Origin": ALLOWED}
    assert mcp(limited_client, headers=headers).status_code == 200
    response = mcp(limited_client, headers=headers)
    assert response.status_code == 429
    assert response.headers["access-control-allow-origin"] == ALLOWED


def test_ping_is_gone(client):
    assert client.get("/ping").status_code == 404


def _assert_security_headers(response):
    for name, value in SECURITY_HEADERS.items():
        assert response.headers[name] == value


@pytest.mark.parametrize(
    "request_",
    [
        lambda c: mcp(c),
        lambda c: c.get("/openapi.json"),
        lambda c: c.get("/does-not-exist"),
        lambda c: c.post("/ingest/henrik", content="cv"),  # 401, no token
        lambda c: c.options(
            "/ask/henrik",
            headers={"Origin": ALLOWED, "Access-Control-Request-Method": "POST"},
        ),
    ],
    ids=["mcp", "openapi", "404", "401", "preflight"],
)
def test_security_headers_on_every_response(client, request_):
    _assert_security_headers(request_(client))


def test_security_headers_on_429(limited_client):
    mcp(limited_client)
    response = mcp(limited_client)
    assert response.status_code == 429
    _assert_security_headers(response)
