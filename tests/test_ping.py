ALLOWED = "https://henrikbecker.net"


def test_ping(client):
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "Pong"


def test_cors_allows_listed_origins(client):
    for origin in (ALLOWED, "https://becker-consulting.se"):
        response = client.get("/ping", headers={"Origin": origin})
        assert response.headers["access-control-allow-origin"] == origin


def test_cors_rejects_other_origins(client):
    response = client.get("/ping", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_rate_limit_returns_429_with_cors_headers(limited_client):
    headers = {"Origin": ALLOWED}
    assert limited_client.get("/ping", headers=headers).status_code == 200
    response = limited_client.get("/ping", headers=headers)
    assert response.status_code == 429
    assert response.headers["access-control-allow-origin"] == ALLOWED
