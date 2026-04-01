"""Tests API utilisateurs (MJ)."""


def test_liste_utilisateurs_interdit_joueur(client_joueur):
    r = client_joueur.get("/api/utilisateurs")
    assert r.status_code == 403


def test_liste_utilisateurs_mj(client_mj):
    """MJ voit au moins son propre compte."""
    r = client_mj.get("/api/utilisateurs")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    ids = {u["id"] for u in data}
    assert "200" in ids


def test_detail_utilisateur_interdit_joueur(client_joueur):
    r = client_joueur.get("/api/utilisateurs/100")
    assert r.status_code == 403


def test_detail_utilisateur_mj(client_mj):
    r = client_mj.get("/api/utilisateurs/200")
    assert r.status_code == 200
    data = r.get_json()
    assert data["id"] == "200"
    assert data["username"] == "MJTest"
