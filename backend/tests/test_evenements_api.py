"""Tests API évènements MJ (liste, création, aperçu des impacts)."""

from app.extensions import db as _db
from app.models import Evenement, EvenementJoueur


def _evenement_avec_ligne_joueur100(app):
    """Évènement actif publié + ligne evenement_joueur active pour l’utilisateur 100."""
    with app.app_context():
        e = Evenement(
            titre="Evt concernant 100",
            description="",
            actif=True,
            brouillon=False,
            cible="joueurs",
            cible_utilisateur_ids='["100"]',
            delai_tours=0,
            tours_restants=None,
        )
        _db.session.add(e)
        _db.session.flush()
        _db.session.add(
            EvenementJoueur(
                evenement_id=e.id,
                utilisateur_id="100",
                actif=True,
                delai_tours=0,
                tours_restants=None,
            )
        )
        _db.session.commit()
        return e.id


def _preview_payload(
    *,
    cible="joueurs",
    cible_utilisateur_ids=None,
    impacts=None,
    evenement_id=None,
    titre="Évènement test",
    brouillon=True,
):
    u = cible_utilisateur_ids if cible_utilisateur_ids is not None else ["100", "101"]
    body = {
        "titre": titre,
        "description": "",
        "actif": True,
        "brouillon": brouillon,
        "cible": cible,
        "cible_utilisateur_ids": u if cible == "joueurs" else [],
        "delai_tours": 0,
        "tours_restants": None,
        "impacts": impacts or {"categories": [], "ressources": [], "productions": []},
    }
    if evenement_id is not None:
        body["evenement_id"] = evenement_id
    return body


def test_preview_impacts_401_sans_session(client):
    r = client.post("/api/evenements/preview-impacts", json=_preview_payload())
    assert r.status_code == 401


def test_preview_impacts_403_joueur(client_joueur):
    r = client_joueur.post("/api/evenements/preview-impacts", json=_preview_payload())
    assert r.status_code == 403


def test_preview_impacts_sans_joueurs_cibles(client_mj):
    r = client_mj.post(
        "/api/evenements/preview-impacts",
        json=_preview_payload(cible="aucun", cible_utilisateur_ids=[]),
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["ok"] is True
    assert data["blocs"] == []
    assert data.get("message")


def test_preview_impacts_cible_invalide(client_mj):
    body = _preview_payload()
    body["cible"] = "invalide"
    r = client_mj.post("/api/evenements/preview-impacts", json=body)
    assert r.status_code == 400


def test_preview_impacts_categorie_add_delta(client_mj, client_joueur, client_joueur_b):
    cat = client_mj.post(
        "/api/categories",
        json={"nom": "CatPreviewEvt", "modificateur_pct": 100.0},
    )
    assert cat.status_code == 201
    cat_id = cat.get_json()["id"]

    # Joueur 100 : surcharge 108 %
    r = client_mj.put(
        f"/api/categories/{cat_id}/modificateur-joueur",
        json={"utilisateur_id": "100", "modificateur_pct": 108.0, "operation": "set"},
    )
    assert r.status_code == 200
    # Joueur 101 : pas de surcharge -> 100 % global
    r = client_mj.post(
        "/api/evenements/preview-impacts",
        json=_preview_payload(
            impacts={
                "categories": [{"categorie_id": cat_id, "operation": "add", "valeur_pct": 4.0}],
                "ressources": [],
                "productions": [],
            },
        ),
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["ok"] is True
    assert len(data["blocs"]) == 1
    b = data["blocs"][0]
    assert b["kind"] == "categorie"
    assert b["categorie_id"] == cat_id
    by_uid = {j["utilisateur_id"]: j for j in b["joueurs"]}
    assert by_uid["100"]["avant_pct"] == 108.0
    assert by_uid["100"]["apres_pct"] == 112.0
    assert by_uid["101"]["avant_pct"] == 100.0
    assert by_uid["101"]["apres_pct"] == 104.0


def test_preview_impacts_ressource_remove_delta(client_mj, ids_ressources):
    rid = ids_ressources["acier"]
    r = client_mj.put(
        f"/api/ressources/{rid}",
        json={
            "modificateur_pct": 110.0,
            "cible_modificateur": "joueurs",
            "utilisateur_ids": ["100"],
            "operation": "set",
        },
    )
    assert r.status_code == 200

    r = client_mj.post(
        "/api/evenements/preview-impacts",
        json=_preview_payload(
            cible_utilisateur_ids=["100"],
            impacts={
                "categories": [],
                "ressources": [{"ressource_id": rid, "operation": "remove", "valeur_pct": 2.0}],
                "productions": [],
            },
        ),
    )
    assert r.status_code == 200
    data = r.get_json()
    assert len(data["blocs"]) == 1
    b = data["blocs"][0]
    assert b["kind"] == "ressource"
    assert b["ressource_id"] == rid
    j = b["joueurs"][0]
    assert j["utilisateur_id"] == "100"
    assert j["avant_pct"] == 110.0
    assert j["apres_pct"] == 108.0


def test_preview_impacts_production_fixe(client_mj, ids_ressources):
    aid = ids_ressources["acier"]
    r = client_mj.post(
        "/api/gains-passifs?uid=100",
        json={
            "ressource_id": aid,
            "quantite_par_tour": 112,
            "delai_tours": 0,
            "mode_production": "fixe",
            "balise": "autre",
            "actif": True,
            "definitif": True,
        },
    )
    assert r.status_code == 201

    r = client_mj.post(
        "/api/gains-passifs?uid=101",
        json={
            "ressource_id": aid,
            "quantite_par_tour": 13,
            "delai_tours": 0,
            "mode_production": "fixe",
            "balise": "autre",
            "actif": True,
            "definitif": True,
        },
    )
    assert r.status_code == 201

    r = client_mj.post(
        "/api/evenements/preview-impacts",
        json=_preview_payload(
            impacts={
                "categories": [],
                "ressources": [],
                "productions": [
                    {
                        "utilisateur_id": None,
                        "ressource_id": aid,
                        "quantite_par_tour": 3,
                        "mode_production": "fixe",
                        "delai_tours": 0,
                        "tours_restants": None,
                        "actif": True,
                    }
                ],
            },
        ),
    )
    assert r.status_code == 200
    data = r.get_json()
    assert len(data["blocs"]) == 1
    b = data["blocs"][0]
    assert b["kind"] == "production"
    by_uid = {j["utilisateur_id"]: j for j in b["joueurs"]}
    assert by_uid["100"]["avant_qpt"] == 112
    assert by_uid["100"]["apres_qpt"] == 115
    assert by_uid["101"]["avant_qpt"] == 13
    assert by_uid["101"]["apres_qpt"] == 16


def test_preview_impacts_production_pourcentage_note(client_mj, ids_ressources):
    aid = ids_ressources["acier"]
    r = client_mj.post(
        "/api/evenements/preview-impacts",
        json=_preview_payload(
            cible_utilisateur_ids=["100"],
            impacts={
                "categories": [],
                "ressources": [],
                "productions": [
                    {
                        "utilisateur_id": None,
                        "ressource_id": aid,
                        "quantite_par_tour": 10,
                        "mode_production": "pourcentage",
                        "delai_tours": 0,
                        "tours_restants": None,
                        "actif": True,
                    }
                ],
            },
        ),
    )
    assert r.status_code == 200
    b = r.get_json()["blocs"][0]
    assert b["kind"] == "production"
    assert "note" in b["joueurs"][0]


def test_evenements_liste_joueur_200(client_joueur):
    r = client_joueur.get("/api/evenements")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("ok") is True
    assert isinstance(body.get("evenements"), list)


def test_evenements_create_403_joueur(client_joueur):
    r = client_joueur.post(
        "/api/evenements",
        json={
            "titre": "X",
            "description": "",
            "actif": True,
            "brouillon": True,
            "cible": "aucun",
            "cible_utilisateur_ids": [],
            "delai_tours": 0,
            "tours_restants": None,
            "impacts": {"categories": [], "ressources": [], "productions": []},
        },
    )
    assert r.status_code == 403


def test_evenements_actifs_1_seulement_si_ligne_active(app, client_joueur, client_joueur_b, client_mj):
    eid = _evenement_avec_ligne_joueur100(app)
    r100 = client_joueur.get("/api/evenements?actifs=1")
    assert r100.status_code == 200
    ids100 = [x["id"] for x in r100.get_json()["evenements"]]
    assert eid in ids100

    r101 = client_joueur_b.get("/api/evenements?actifs=1")
    assert r101.status_code == 200
    assert eid not in [x["id"] for x in r101.get_json()["evenements"]]

    r_mj = client_mj.get("/api/evenements?actifs=1")
    assert r_mj.status_code == 200
    assert eid not in [x["id"] for x in r_mj.get_json()["evenements"]]


def test_evenement_get_detail_joueur_concerne_403_autre(app, client_joueur, client_joueur_b, client_mj):
    eid = _evenement_avec_ligne_joueur100(app)
    assert client_joueur.get(f"/api/evenements/{eid}").status_code == 200
    assert client_joueur_b.get(f"/api/evenements/{eid}").status_code == 403
    assert client_mj.get(f"/api/evenements/{eid}").status_code == 200


def test_apercu_joueur_200_et_403(app, client_joueur, client_joueur_b, client_mj):
    eid = _evenement_avec_ligne_joueur100(app)
    r = client_joueur.get(f"/api/evenements/{eid}/apercu-joueur")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("ok") is True
    assert isinstance(body.get("blocs"), list)
    assert isinstance(body.get("resume"), list)
    assert client_joueur_b.get(f"/api/evenements/{eid}/apercu-joueur").status_code == 403
    assert client_mj.get(f"/api/evenements/{eid}/apercu-joueur").status_code == 403
