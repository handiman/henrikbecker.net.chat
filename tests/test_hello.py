ALLOWED = "https://henrikbecker.net"


def test_hello(client):
    response = client.get("/api/v1/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World"}


def test_cors_allows_listed_origins(client):
    for origin in (ALLOWED, "https://becker-consulting.se"):
        response = client.get("/api/v1/hello", headers={"Origin": origin})
        assert response.headers["access-control-allow-origin"] == origin


def test_cors_rejects_other_origins(client):
    response = client.get("/api/v1/hello", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_rate_limit_returns_429_with_cors_headers(limited_client):
    headers = {"Origin": ALLOWED}
    assert limited_client.get("/api/v1/hello", headers=headers).status_code == 200
    response = limited_client.get("/api/v1/hello", headers=headers)
    assert response.status_code == 429
    assert response.headers["access-control-allow-origin"] == ALLOWED
