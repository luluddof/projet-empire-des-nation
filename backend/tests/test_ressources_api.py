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


def test_ressource_modificateur_joueur_add_remove(
    client_mj, client_joueur, client_joueur_b, ids_ressources
):
    rid = ids_ressources["acier"]

    # Base catalogue globale (ne doit pas bouger pour une cible "joueurs")
    global_before = client_mj.get(f"/api/ressources/{rid}?global=1").get_json()[
        "modificateur_pct"
    ]

    # Overrides différents par joueur
    r1 = client_mj.put(
        f"/api/ressources/{rid}",
        json={
            "modificateur_pct": 80.0,
            "cible_modificateur": "joueurs",
            "utilisateur_ids": ["100"],
        },
    )
    assert r1.status_code == 200

    r2 = client_mj.put(
        f"/api/ressources/{rid}",
        json={
            "modificateur_pct": 120.0,
            "cible_modificateur": "joueurs",
            "utilisateur_ids": ["101"],
        },
    )
    assert r2.status_code == 200

    # Vérifie la lecture du modificateur par joueur
    state = client_mj.get(
        f"/api/ressources/{rid}/modificateur-joueur?utilisateur_ids=100&utilisateur_ids=101"
    )
    assert state.status_code == 200
    state_data = state.get_json()
    assert state_data["ok"] is True
    assert abs(state_data["valeurs"]["100"]["modificateur_pct"] - 80.0) < 1e-6
    assert abs(state_data["valeurs"]["101"]["modificateur_pct"] - 120.0) < 1e-6

    ra = client_joueur.get(f"/api/ressources/{rid}").get_json()
    rb = client_joueur_b.get(f"/api/ressources/{rid}").get_json()
    assert abs(ra["modificateur_pct"] - 80.0) < 1e-6
    assert abs(rb["modificateur_pct"] - 120.0) < 1e-6

    # Vue MJ "comme un joueur"
    as_a = client_mj.get(f"/api/ressources/{rid}?as_user_id=100")
    assert as_a.status_code == 200
    assert abs(as_a.get_json()["modificateur_pct"] - 80.0) < 1e-6

    as_list = client_mj.get("/api/ressources?as_user_id=101")
    assert as_list.status_code == 200
    # Argent/Aciers seed => au moins la ressource rid doit être présente
    row = [x for x in as_list.get_json() if x["id"] == rid][0]
    assert abs(row["modificateur_pct"] - 120.0) < 1e-6

    # +10 (delta) => 90 et 130
    r3 = client_mj.put(
        f"/api/ressources/{rid}",
        json={
            "modificateur_pct": 10.0,
            "cible_modificateur": "joueurs",
            "utilisateur_ids": ["100", "101"],
            "operation": "add",
        },
    )
    assert r3.status_code == 200

    ra2 = client_joueur.get(f"/api/ressources/{rid}").get_json()
    rb2 = client_joueur_b.get(f"/api/ressources/{rid}").get_json()
    assert abs(ra2["modificateur_pct"] - 90.0) < 1e-6
    assert abs(rb2["modificateur_pct"] - 130.0) < 1e-6

    global_after_add = client_mj.get(f"/api/ressources/{rid}?global=1").get_json()[
        "modificateur_pct"
    ]
    assert abs(global_after_add - global_before) < 1e-9

    # -5 (delta) => 85 et 125
    r4 = client_mj.put(
        f"/api/ressources/{rid}",
        json={
            "modificateur_pct": 5.0,
            "cible_modificateur": "joueurs",
            "utilisateur_ids": ["100", "101"],
            "operation": "remove",
        },
    )
    assert r4.status_code == 200

    ra3 = client_joueur.get(f"/api/ressources/{rid}").get_json()
    rb3 = client_joueur_b.get(f"/api/ressources/{rid}").get_json()
    assert abs(ra3["modificateur_pct"] - 85.0) < 1e-6
    assert abs(rb3["modificateur_pct"] - 125.0) < 1e-6
