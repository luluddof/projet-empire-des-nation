"""Tests API stocks, commerce et gains passifs."""

from app.extensions import db
from app.models import GainPassif, Stock, Transaction, Utilisateur
from datetime import UTC, datetime, timedelta


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


def test_commerce_achat_lointain(client_joueur, ids_ressources):
    fid, aid = ids_ressources["florins"], ids_ressources["acier"]
    r = client_joueur.put(f"/api/stocks/{fid}", json={"quantite": 100_000_000})
    assert r.status_code == 200

    r = client_joueur.post(
        "/api/stocks/commerce",
        json={
            "ressource_id": aid,
            "quantite": 1,
            "sens": "achat",
            "achat_mode": "lointain",
        },
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["ok"] is True
    assert body["stock_ressource"]["quantite"] == 1


def test_commerce_achat_mode_invalide(client_joueur, ids_ressources):
    fid, aid = ids_ressources["florins"], ids_ressources["acier"]
    r = client_joueur.put(f"/api/stocks/{fid}", json={"quantite": 100_000_000})
    assert r.status_code == 200

    r = client_joueur.post(
        "/api/stocks/commerce",
        json={
            "ressource_id": aid,
            "quantite": 1,
            "sens": "achat",
            "achat_mode": "bizarre",
        },
    )
    assert r.status_code == 400
    assert "achat_mode" in (r.get_json() or {}).get("error", "")


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


def test_gains_passifs_temporaire_creation_2_tours(client_joueur, ids_ressources):
    rid = ids_ressources["acier"]
    r = client_joueur.post(
        "/api/gains-passifs",
        json={
            "ressource_id": rid,
            "quantite_par_tour": 5,
            "mode_production": "fixe",
            "balise": "autre",
            "definitif": False,
            "tours_restants": 2,
            "actif": True,
        },
    )
    assert r.status_code == 201
    body = r.get_json()
    assert body["definitif"] is False
    assert int(body["tours_restants"]) == 2
    assert body["mode_production"] == "fixe"


def test_gains_passifs_balises(client_joueur):
    r = client_joueur.get("/api/gains-passifs/balises")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    ids = {x["id"] for x in data}
    assert "science" in ids
    assert "batiment" in ids
    assert "autre" in ids


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

    # MJ : peut consulter, mais ne peut pas acheter/vendre pour un autre joueur
    rid = ids_ressources["acier"]
    r = client_mj.post(
        "/api/stocks/commerce?uid=101",
        json={"ressource_id": rid, "quantite": 1, "sens": "achat", "achat_mode": "local"},
    )
    assert r.status_code == 403

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


def test_scheduler_applique_gain_temporaire_deux_tours(app, ids_ressources):
    from app.scheduler.tours import _appliquer_gains_passifs

    rid = ids_ressources["acier"]
    with app.app_context():
        u = Utilisateur(id="301", username="SchedTemp", is_mj=False)
        db.session.add(u)
        db.session.commit()

        s = Stock(utilisateur_id="301", ressource_id=rid, quantite=100)
        db.session.add(s)

        g = GainPassif(
            utilisateur_id="301",
            ressource_id=rid,
            quantite_par_tour=3,
            actif=True,
            tours_restants=2,
            balise="autre",
            mode_production="fixe",
        )
        db.session.add(g)
        db.session.commit()

    _appliquer_gains_passifs(app)

    with app.app_context():
        s1 = Stock.query.filter_by(utilisateur_id="301", ressource_id=rid).first()
        assert s1.quantite == 103
        g1 = GainPassif.query.filter_by(utilisateur_id="301", ressource_id=rid).first()
        assert g1 is not None
        assert g1.actif is True
        assert int(g1.tours_restants) == 1
        txs = Transaction.query.filter_by(utilisateur_id="301", ressource_id=rid, motif="gain_passif").all()
        assert len(txs) == 1
        assert txs[0].quantite == 3

    _appliquer_gains_passifs(app)

    with app.app_context():
        s2 = Stock.query.filter_by(utilisateur_id="301", ressource_id=rid).first()
        assert s2.quantite == 106
        g2 = GainPassif.query.filter_by(utilisateur_id="301", ressource_id=rid).first()
        assert g2 is not None
        assert g2.actif is False
        assert int(g2.tours_restants) == 0
        txs = Transaction.query.filter_by(utilisateur_id="301", ressource_id=rid, motif="gain_passif").all()
        assert len(txs) == 2
        assert sum(t.quantite for t in txs) == 6

    # 3e tour : plus de transaction (gain inactif)
    _appliquer_gains_passifs(app)

    with app.app_context():
        s3 = Stock.query.filter_by(utilisateur_id="301", ressource_id=rid).first()
        assert s3.quantite == 106
        txs = Transaction.query.filter_by(utilisateur_id="301", ressource_id=rid, motif="gain_passif").all()
        assert len(txs) == 2


def test_scheduler_applique_gain_delai_definitif_deux_tours(app, ids_ressources):
    from app.scheduler.tours import _appliquer_gains_passifs

    rid = ids_ressources["acier"]
    with app.app_context():
        u = Utilisateur(id="302", username="SchedDelayDef", is_mj=False)
        db.session.add(u)
        db.session.commit()

        s = Stock(utilisateur_id="302", ressource_id=rid, quantite=100)
        db.session.add(s)
        g = GainPassif(
            utilisateur_id="302",
            ressource_id=rid,
            quantite_par_tour=3,
            actif=True,
            tours_restants=None,
            delai_tours=2,
            balise="autre",
            mode_production="fixe",
        )
        db.session.add(g)
        db.session.commit()

    _appliquer_gains_passifs(app)
    with app.app_context():
        s1 = Stock.query.filter_by(utilisateur_id="302", ressource_id=rid).first()
        assert s1.quantite == 100
        assert Transaction.query.filter_by(utilisateur_id="302", ressource_id=rid, motif="gain_passif").count() == 0

    _appliquer_gains_passifs(app)
    with app.app_context():
        s2 = Stock.query.filter_by(utilisateur_id="302", ressource_id=rid).first()
        assert s2.quantite == 100
        assert GainPassif.query.filter_by(utilisateur_id="302", ressource_id=rid).first().delai_tours == 0
        assert Transaction.query.filter_by(utilisateur_id="302", ressource_id=rid, motif="gain_passif").count() == 0

    _appliquer_gains_passifs(app)
    with app.app_context():
        s3 = Stock.query.filter_by(utilisateur_id="302", ressource_id=rid).first()
        assert s3.quantite == 103
        assert Transaction.query.filter_by(utilisateur_id="302", ressource_id=rid, motif="gain_passif").count() == 1


def test_scheduler_applique_gain_delai_temporaire_deux_tours(app, ids_ressources):
    from app.scheduler.tours import _appliquer_gains_passifs

    rid = ids_ressources["acier"]
    with app.app_context():
        u = Utilisateur(id="303", username="SchedDelayTemp", is_mj=False)
        db.session.add(u)
        db.session.commit()

        s = Stock(utilisateur_id="303", ressource_id=rid, quantite=100)
        db.session.add(s)
        g = GainPassif(
            utilisateur_id="303",
            ressource_id=rid,
            quantite_par_tour=3,
            actif=True,
            tours_restants=1,
            delai_tours=2,
            balise="autre",
            mode_production="fixe",
        )
        db.session.add(g)
        db.session.commit()

    _appliquer_gains_passifs(app)  # delai -> 1
    _appliquer_gains_passifs(app)  # delai -> 0
    _appliquer_gains_passifs(app)  # application et désactivation

    with app.app_context():
        s3 = Stock.query.filter_by(utilisateur_id="303", ressource_id=rid).first()
        assert s3.quantite == 103

        g3 = GainPassif.query.filter_by(utilisateur_id="303", ressource_id=rid).first()
        assert g3 is not None
        assert g3.actif is False

        txs = Transaction.query.filter_by(
            utilisateur_id="303", ressource_id=rid, motif="gain_passif"
        ).all()
        assert len(txs) == 1
        assert txs[0].quantite == 3

    _appliquer_gains_passifs(app)  # pas de nouvelle transaction
    with app.app_context():
        txs2 = Transaction.query.filter_by(
            utilisateur_id="303", ressource_id=rid, motif="gain_passif"
        ).all()
        assert len(txs2) == 1


def test_chronologie_clustering_gain_passif_gap_seconds(client_joueur, ids_ressources, app):
    """
    Teste le clustering des transactions dans /api/gains-passifs/chronologie.

    Le clustering fusionne les lignes si (t2 - t1) <= gap_seconds (8s).
    C'est exactement le cas qui peut donner l'impression d'un "T-1 doublé"
    si deux tours sont simulés trop vite.
    """
    rid = ids_ressources["acier"]
    uid = "100"

    with app.app_context():
        # Nettoyage (au cas où)
        Transaction.query.filter_by(
            utilisateur_id=uid, ressource_id=rid, motif="gain_passif"
        ).delete()
        db.session.commit()

        base = datetime.now(UTC)

        # Cas 1 : proche (< 8s) => fusion => une seule ligne avec somme
        t1 = base
        t2 = base + timedelta(seconds=4)
        db.session.add(
            Transaction(
                utilisateur_id=uid,
                ressource_id=rid,
                quantite=3,
                valeur_florins=0,
                motif="gain_passif",
                created_at=t1,
            )
        )
        db.session.add(
            Transaction(
                utilisateur_id=uid,
                ressource_id=rid,
                quantite=5,
                valeur_florins=0,
                motif="gain_passif",
                created_at=t2,
            )
        )
        db.session.commit()

    r1 = client_joueur.get(f"/api/gains-passifs/chronologie?ressource_id={rid}")
    assert r1.status_code == 200
    passe1 = r1.get_json()["passe"]
    assert len(passe1) == 1
    assert passe1[0]["quantite"] == 8

    with app.app_context():
        Transaction.query.filter_by(
            utilisateur_id=uid, ressource_id=rid, motif="gain_passif"
        ).delete()
        db.session.commit()

        # Cas 2 : éloigné (> 8s) => deux clusters séparés
        t1 = base
        t2 = base + timedelta(seconds=9)
        db.session.add(
            Transaction(
                utilisateur_id=uid,
                ressource_id=rid,
                quantite=3,
                valeur_florins=0,
                motif="gain_passif",
                created_at=t1,
            )
        )
        db.session.add(
            Transaction(
                utilisateur_id=uid,
                ressource_id=rid,
                quantite=5,
                valeur_florins=0,
                motif="gain_passif",
                created_at=t2,
            )
        )
        db.session.commit()

    r2 = client_joueur.get(f"/api/gains-passifs/chronologie?ressource_id={rid}")
    assert r2.status_code == 200
    passe2 = r2.get_json()["passe"]
    assert len(passe2) == 2
    assert passe2[0]["quantite"] == 3
    assert passe2[1]["quantite"] == 5
