"""Tests /api/auth/me avec session."""


def test_me_authentifie(client_joueur):
    r = client_joueur.get("/api/auth/me")
    assert r.status_code == 200
    body = r.get_json()
    assert body["authenticated"] is True
    assert body["user"]["id"] == "100"
