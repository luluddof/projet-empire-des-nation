from urllib.parse import parse_qs, urlparse


def test_discord_login_redirects_to_discord(client):
    response = client.get("/api/auth/discord/login")

    assert response.status_code == 302
    location = response.headers["Location"]
    parsed = urlparse(location)
    query = parse_qs(parsed.query)
    assert parsed.netloc == "discord.com"
    assert parsed.path == "/api/oauth2/authorize"
    assert query["client_id"] == ["123456"]
    assert query["response_type"] == ["code"]
    assert query["scope"] == ["identify"]


def test_me_returns_unauthenticated_without_session(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.get_json() == {"authenticated": False}


def test_logout_clears_session(client):
    with client.session_transaction() as session:
        session["discord_user"] = {"id": "99", "username": "demo"}

    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.get_json() == {"ok": True}
    with client.session_transaction() as session:
        assert "discord_user" not in session


def test_callback_missing_code_redirects_with_error(client):
    response = client.get("/api/auth/discord/callback")

    assert response.status_code == 302
    assert response.headers["Location"] == "http://localhost:5173/?error=missing_code"


def test_callback_success_sets_session_and_redirects(client, monkeypatch):
    def fake_exchange(_code):
        return "fake-token"

    def fake_profile(_token):
        return {"id": "42", "username": "empire", "avatar": "abc"}

    monkeypatch.setattr("app.auth.exchange_code_for_token", fake_exchange)
    monkeypatch.setattr("app.auth.fetch_discord_user_profile", fake_profile)

    response = client.get("/api/auth/discord/callback?code=discord-code")

    assert response.status_code == 302
    assert response.headers["Location"] == "http://localhost:5173/dashboard"
    with client.session_transaction() as session:
        assert session["discord_user"]["id"] == "42"
        assert session["discord_user"]["username"] == "empire"
