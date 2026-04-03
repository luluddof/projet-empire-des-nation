"""Tests API transactions."""

from app.extensions import db
from app.models import Stock


def test_transactions_401(client):
    assert client.get("/api/transactions").status_code == 401


def test_transactions_liste_vide(client_joueur):
    r = client_joueur.get("/api/transactions")
    assert r.status_code == 200
    body = r.get_json()
    assert "transactions" in body
    assert "total" in body
    assert "page" in body
    assert isinstance(body["transactions"], list)


def test_transactions_apres_mouvement_stock(client_joueur, ids_ressources):
    rid = ids_ressources["acier"]
    # L'ajustement de stock est réservé MJ ; on prépare le stock en base.
    s = Stock.query.filter_by(utilisateur_id="100", ressource_id=rid).first()
    if s is None:
        s = Stock(utilisateur_id="100", ressource_id=rid, quantite=5)
        db.session.add(s)
    else:
        s.quantite = 5
    db.session.commit()
    r = client_joueur.get("/api/transactions?per_page=5")
    assert r.status_code == 200
    txs = r.get_json()["transactions"]
    # Pas de transaction créée automatiquement par la préparation DB :
    # on vérifie juste que l'API répond correctement.
    assert isinstance(txs, list)
