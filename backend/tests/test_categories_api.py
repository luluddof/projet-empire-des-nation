"""Tests API catégories."""


def test_categories_liste(client_joueur):
    r = client_joueur.get("/api/categories")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_categories_create_interdit_joueur(client_joueur):
    r = client_joueur.post(
        "/api/categories",
        json={"nom": "CatTestInterdite"},
    )
    assert r.status_code == 403


def test_categories_create_mj(client_mj):
    r = client_mj.post(
        "/api/categories",
        json={"nom": "CatTestMJUnique", "modificateur_pct": 100.0},
    )
    assert r.status_code == 201
    assert r.get_json()["nom"] == "CatTestMJUnique"
