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


def test_categories_modificateur_pct_par_joueur(
    client_mj, client_joueur, client_joueur_b
):
    # 1) Catégorie globale : 120% (facteur attendu 1.2)
    r = client_mj.post(
        "/api/categories",
        json={"nom": "CatTestParJoueur", "modificateur_pct": 120.0},
    )
    assert r.status_code == 201
    cat_id = r.get_json()["id"]

    # 2) Ressource liée à cette catégorie (prix_base = 10, ressource = 100%)
    r = client_mj.post(
        "/api/ressources",
        json={
            "nom": "RessTestParJoueur",
            "type": "Première",
            "prix_base": 10,
            "categorie_ids": [cat_id],
        },
    )
    assert r.status_code == 201
    rid = r.get_json()["id"]

    # 3) Joueur B (id 101) : surcharge catégorie à 80% (facteur attendu 0.8)
    r = client_mj.put(
        f"/api/categories/{cat_id}/modificateur-joueur",
        json={"utilisateur_id": "101", "modificateur_pct": 80.0},
    )
    assert r.status_code == 200

    # Joueur A (id 100) : pas de surcharge -> 1.2
    rA = client_joueur.get(f"/api/ressources/{rid}")
    assert rA.status_code == 200
    assert abs(rA.get_json()["facteur_prix"] - 1.2) < 1e-6

    # Joueur B : surcharge -> 0.8
    rB = client_joueur_b.get(f"/api/ressources/{rid}")
    assert rB.status_code == 200
    assert abs(rB.get_json()["facteur_prix"] - 0.8) < 1e-6
    assert rB.get_json()["categories"][0]["modificateur_pct"] == 80.0

    # 4) Suppression surcharge : retour à la valeur globale (1.2)
    r = client_mj.put(
        f"/api/categories/{cat_id}/modificateur-joueur",
        json={"utilisateur_id": "101", "supprimer": True},
    )
    assert r.status_code == 200

    rB2 = client_joueur_b.get(f"/api/ressources/{rid}")
    assert rB2.status_code == 200
    assert abs(rB2.get_json()["facteur_prix"] - 1.2) < 1e-6
