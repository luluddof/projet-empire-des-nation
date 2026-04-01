"""Tests API transactions."""


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
    client_joueur.put(f"/api/stocks/{rid}", json={"quantite": 5})
    r = client_joueur.get("/api/transactions?per_page=5")
    assert r.status_code == 200
    txs = r.get_json()["transactions"]
    assert len(txs) >= 1
