import pytest

LOCALHOST = "http://localhost:8787"


def allow_origin(client, origin):
    return client.get("/ping", headers={"Origin": origin}).headers.get(
        "access-control-allow-origin"
    )


def test_localhost_is_denied_by_default(client):
    assert allow_origin(client, LOCALHOST) is None


@pytest.mark.parametrize("value", ["false", "", "1", "yes"])
def test_localhost_is_denied_unless_var_is_true(make_client, value):
    assert allow_origin(make_client(value), LOCALHOST) is None


@pytest.mark.parametrize("value", ["true", "True"])
def test_localhost_is_allowed_when_var_is_true(make_client, value):
    client = make_client(value)
    assert allow_origin(client, LOCALHOST) == LOCALHOST
    assert allow_origin(client, "http://localhost:8080") == "http://localhost:8080"


def test_dev_mode_still_allows_listed_and_rejects_other_origins(make_client):
    client = make_client("true")
    assert allow_origin(client, "https://henrikbecker.net") == "https://henrikbecker.net"
    assert allow_origin(client, "https://evil.example") is None


def test_preflight_for_localhost_is_denied_by_default(client):
    response = client.options(
        "/ask/henrik",
        headers={"Origin": LOCALHOST, "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 400
