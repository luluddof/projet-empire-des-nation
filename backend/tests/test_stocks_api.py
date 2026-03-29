"""Tests API stocks, commerce et gains passifs."""

from app.extensions import db
from app.models import GainPassif, Stock, Transaction, Utilisateur


def test_stocks_401_sans_session(client):
    assert client.get("/api/stocks").status_code == 401


def test_stocks_liste_joueur(client_joueur, ids_ressources):
    r = client_joueur.get("/api/stocks")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    ids = {row["ressource_id"] for row in data}
    assert ids_ressources["florins"] in ids
    assert ids_ressources["acier"] in ids


def test_stocks_ajustement_manuel(client_joueur, ids_ressources):
    rid = ids_ressources["acier"]
    r = client_joueur.put(
        f"/api/stocks/{rid}",
        json={"quantite": 42, "motif": "test"},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["quantite"] == 42

    tr = (
        Transaction.query.filter_by(utilisateur_id="100", ressource_id=rid)
        .order_by(Transaction.id.desc())
        .first()
    )
    assert tr is not None
    assert tr.motif == "test"


def test_commerce_achat(client_joueur, ids_ressources):
    fid, aid = ids_ressources["florins"], ids_ressources["acier"]
    r = client_joueur.put(f"/api/stocks/{fid}", json={"quantite": 50_000_000})
    assert r.status_code == 200

    r = client_joueur.post(
        "/api/stocks/commerce",
        json={"ressource_id": aid, "quantite": 1, "sens": "achat"},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["ok"] is True
    assert body["stock_ressource"]["quantite"] == 1


def test_commerce_vente_insuffisant(client_joueur, ids_ressources):
    aid = ids_ressources["acier"]
    r = client_joueur.post(
        "/api/stocks/commerce",
        json={"ressource_id": aid, "quantite": 1, "sens": "vente"},
    )
    assert r.status_code == 400
    assert "insuffisant" in r.get_json()["error"].lower()


def test_gains_passifs_crud_et_chronologie(client_joueur, ids_ressources, app):
    rid = ids_ressources["acier"]
    r = client_joueur.put(f"/api/stocks/{rid}", json={"quantite": 1000})
    assert r.status_code == 200

    r = client_joueur.post(
        "/api/gains-passifs",
        json={
            "ressource_id": rid,
            "quantite_par_tour": 5,
            "mode_production": "fixe",
            "balise": "science",
            "definitif": True,
            "actif": True,
        },
    )
    assert r.status_code == 201
    gain = r.get_json()
    assert gain["quantite_par_tour"] == 5
    assert gain["balise"] == "science"
    assert gain["mode_production"] == "fixe"
    gid = gain["id"]

    r = client_joueur.get("/api/gains-passifs")
    assert r.status_code == 200
    assert len(r.get_json()) >= 1

    r = client_joueur.get(f"/api/gains-passifs/chronologie?ressource_id={rid}")
    assert r.status_code == 200
    ch = r.get_json()
    assert ch["prochain_tour"] == 5
    assert "passe" in ch and "futur" in ch
    assert len(ch["futur"]) == 3

    r = client_joueur.put(
        f"/api/gains-passifs/{gid}",
        json={
            "quantite_par_tour": 7,
            "balise": "politique",
            "mode_production": "fixe",
            "definitif": True,
            "actif": True,
        },
    )
    assert r.status_code == 200
    assert r.get_json()["quantite_par_tour"] == 7

    r = client_joueur.delete(f"/api/gains-passifs/{gid}")
    assert r.status_code == 200


def test_gains_passifs_pourcentage_refuse_hors_plage(client_joueur, ids_ressources):
    rid = ids_ressources["acier"]
    r = client_joueur.post(
        "/api/gains-passifs",
        json={
            "ressource_id": rid,
            "quantite_par_tour": 2000,
            "mode_production": "pourcentage",
            "balise": "evenement",
            "definitif": True,
        },
    )
    assert r.status_code == 400


def test_gains_passifs_pourcentage_ok(client_joueur, ids_ressources):
    rid = ids_ressources["acier"]
    r = client_joueur.post(
        "/api/gains-passifs",
        json={
            "ressource_id": rid,
            "quantite_par_tour": -100,
            "mode_production": "pourcentage",
            "balise": "evenement",
            "definitif": True,
        },
    )
    assert r.status_code == 201
    assert r.get_json()["mode_production"] == "pourcentage"


def test_joueur_ne_peut_pas_voir_stocks_autre_user(client_joueur, client_joueur_b, ids_ressources):
    r = client_joueur.get("/api/stocks")
    assert r.status_code == 200
    r = client_joueur.get("/api/stocks?uid=101")
    assert r.status_code == 403


def test_mj_peut_stocks_et_gains_passifs_autre(client_mj, app, ids_ressources):
    with app.app_context():
        db.session.add(Utilisateur(id="101", username="Cible", is_mj=False))
        db.session.commit()

    r = client_mj.get("/api/stocks?uid=101")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)

    rid = ids_ressources["acier"]
    r = client_mj.post(
        f"/api/gains-passifs?uid=101",
        json={
            "ressource_id": rid,
            "quantite_par_tour": 5,
            "mode_production": "fixe",
            "balise": "autre",
            "definitif": True,
        },
    )
    assert r.status_code == 201
    gid = r.get_json()["id"]

    r = client_mj.get(f"/api/gains-passifs/chronologie?ressource_id={rid}&uid=101")
    assert r.status_code == 200

    r = client_mj.delete(f"/api/gains-passifs/{gid}?uid=101")
    assert r.status_code == 200


def test_scheduler_applique_gain_fixe(app, ids_ressources):
    from app.scheduler.tours import _appliquer_gains_passifs

    rid = ids_ressources["acier"]
    with app.app_context():
        u = Utilisateur(id="300", username="Sched", is_mj=False)
        db.session.add(u)
        db.session.commit()
        s = Stock(utilisateur_id="300", ressource_id=rid, quantite=100)
        db.session.add(s)
        g = GainPassif(
            utilisateur_id="300",
            ressource_id=rid,
            quantite_par_tour=3,
            actif=True,
            tours_restants=None,
            balise="autre",
            mode_production="fixe",
        )
        db.session.add(g)
        db.session.commit()

    _appliquer_gains_passifs(app)

    with app.app_context():
        s = Stock.query.filter_by(utilisateur_id="300", ressource_id=rid).first()
        assert s.quantite == 103
        tx = Transaction.query.filter_by(
            utilisateur_id="300", ressource_id=rid, motif="gain_passif"
        ).first()
        assert tx is not None
        assert tx.quantite == 3
