"""Tests API ressources et historique de prix."""


def test_ressources_401_sans_session(client):
    assert client.get("/api/ressources").status_code == 401


def test_ressources_liste_joueur(client_joueur):
    r = client_joueur.get("/api/ressources")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    assert len(data) >= 2
    noms = {x["nom"] for x in data}
    assert "Florins" in noms


def test_ressource_introuvable(client_joueur):
    r = client_joueur.get("/api/ressources/999999")
    assert r.status_code == 404


def test_ressource_detail(client_joueur, ids_ressources):
    aid = ids_ressources["acier"]
    r = client_joueur.get(f"/api/ressources/{aid}")
    assert r.status_code == 200
    assert r.get_json()["nom"] == "Acier"


def test_historique_prix(client_joueur, ids_ressources):
    aid = ids_ressources["acier"]
    r = client_joueur.get(f"/api/ressources/{aid}/historique-prix?limit=10")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)


def test_ressources_global_mj(client_mj):
    r = client_mj.get("/api/ressources?global=1")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_create_ressource_reserve_mj(client_joueur):
    r = client_joueur.post(
        "/api/ressources",
        json={
            "nom": "TestRes",
            "type": "Première",
            "prix_base": 1000,
        },
    )
    assert r.status_code == 403


def test_create_ressource_mj(client_mj):
    r = client_mj.post(
        "/api/ressources",
        json={
            "nom": "RessourceTestXYZ",
            "type": "Première",
            "prix_base": 1000,
        },
    )
    assert r.status_code == 201
    assert r.get_json()["nom"] == "RessourceTestXYZ"
