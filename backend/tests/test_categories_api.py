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


def test_categories_inflation_moyenne_multi_categories_et_multi_joueurs(
    client_mj, client_joueur, client_joueur_b
):
    # Catégories globales
    r1 = client_mj.post(
        "/api/categories",
        json={"nom": "CatTestMoyenne1", "modificateur_pct": 120.0},
    )
    assert r1.status_code == 201
    c1_id = r1.get_json()["id"]

    r2 = client_mj.post(
        "/api/categories",
        json={"nom": "CatTestMoyenne2", "modificateur_pct": 110.0},
    )
    assert r2.status_code == 201
    c2_id = r2.get_json()["id"]

    # Ressource liée à 2 catégories : facteur = moyenne(1.2, 1.1) = 1.15
    rr = client_mj.post(
        "/api/ressources",
        json={
            "nom": "RessTestMoyenne",
            "type": "Première",
            "prix_base": 10,
            "categorie_ids": [c1_id, c2_id],
        },
    )
    assert rr.status_code == 201
    rid = rr.get_json()["id"]

    ra = client_joueur.get(f"/api/ressources/{rid}")
    assert ra.status_code == 200
    assert abs(ra.get_json()["facteur_prix"] - 1.15) < 1e-6

    # Override joueur B :
    # - c1: 80% => 0.8
    # - c2: 90% => 0.9
    # facteur = moyenne(0.8, 0.9) = 0.85
    rr = client_mj.put(
        f"/api/categories/{c1_id}/modificateur-joueur",
        json={"utilisateur_id": "101", "modificateur_pct": 80.0},
    )
    assert rr.status_code == 200
    rr = client_mj.put(
        f"/api/categories/{c2_id}/modificateur-joueur",
        json={"utilisateur_id": "101", "modificateur_pct": 90.0},
    )
    assert rr.status_code == 200

    rb = client_joueur_b.get(f"/api/ressources/{rid}")
    assert rb.status_code == 200
    assert abs(rb.get_json()["facteur_prix"] - 0.85) < 1e-6

    # Multi-joueurs sur c1 : 75% pour A et B
    # A : moyenne(0.75, 1.1) = 0.925
    # B : moyenne(0.75, 0.9) = 0.825
    rr = client_mj.put(
        f"/api/categories/{c1_id}/modificateur-joueur",
        json={"utilisateur_ids": ["100", "101"], "modificateur_pct": 75.0},
    )
    assert rr.status_code == 200

    ra2 = client_joueur.get(f"/api/ressources/{rid}")
    assert ra2.status_code == 200
    assert abs(ra2.get_json()["facteur_prix"] - 0.925) < 1e-6

    rb2 = client_joueur_b.get(f"/api/ressources/{rid}")
    assert rb2.status_code == 200
    assert abs(rb2.get_json()["facteur_prix"] - 0.825) < 1e-6

    # Reset c1 pour A et B uniquement
    rr = client_mj.put(
        f"/api/categories/{c1_id}/modificateur-joueur",
        json={"utilisateur_ids": ["100", "101"], "supprimer": True},
    )
    assert rr.status_code == 200

    # A : moyenne(1.2, 1.1) = 1.15 ; B : moyenne(1.2, 0.9) = 1.05
    ra3 = client_joueur.get(f"/api/ressources/{rid}")
    assert ra3.status_code == 200
    assert abs(ra3.get_json()["facteur_prix"] - 1.15) < 1e-6

    rb3 = client_joueur_b.get(f"/api/ressources/{rid}")
    assert rb3.status_code == 200
    assert abs(rb3.get_json()["facteur_prix"] - 1.05) < 1e-6


def test_ressource_override_mj_puis_categorie_modifiee(
    client_mj, client_joueur
):
    # Catégories globales
    c1 = client_mj.post(
        "/api/categories",
        json={"nom": "CatTestRessOverride1", "modificateur_pct": 120.0},
    )
    assert c1.status_code == 201
    c1_id = c1.get_json()["id"]

    c2 = client_mj.post(
        "/api/categories",
        json={"nom": "CatTestRessOverride2", "modificateur_pct": 110.0},
    )
    assert c2.status_code == 201
    c2_id = c2.get_json()["id"]

    # Ressource liée aux 2 catégories (prix_base = 10)
    rr = client_mj.post(
        "/api/ressources",
        json={
            "nom": "RessTestRessOverride",
            "type": "Première",
            "prix_base": 10,
            "categorie_ids": [c1_id, c2_id],
        },
    )
    assert rr.status_code == 201
    rid = rr.get_json()["id"]

    # Joueur A (id=100) : surcharge ressource à 110% (indépendante des catégories)
    mod = client_mj.put(
        f"/api/ressources/{rid}",
        json={
            "modificateur_pct": 110.0,
            "cible_modificateur": "joueurs",
            "utilisateur_ids": ["100"],
        },
    )
    assert mod.status_code == 200

    # Facteur attendu initial :
    # ressource 110% => 1.1
    # catégories 120% & 110% => moyenne(1.2, 1.1) = 1.15
    # => 1.1 * 1.15 = 1.265
    ra = client_joueur.get(f"/api/ressources/{rid}")
    assert ra.status_code == 200
    assert abs(ra.get_json()["facteur_prix"] - 1.265) < 1e-6

    # On modifie une catégorie (c1 passe de 120% -> 130%)
    up = client_mj.put(
        f"/api/categories/{c1_id}",
        json={"modificateur_pct": 130.0},
    )
    assert up.status_code == 200

    # Nouveau facteur attendu :
    # catégories => moyenne(1.3, 1.1) = 1.2
    # => 1.1 * 1.2 = 1.32
    ra2 = client_joueur.get(f"/api/ressources/{rid}")
    assert ra2.status_code == 200
    assert abs(ra2.get_json()["facteur_prix"] - 1.32) < 1e-6
