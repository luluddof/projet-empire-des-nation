from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import GainPassif, Ressource, Stock, Transaction
from ..utils.decorators import get_current_user, login_required

stocks_bp = Blueprint("stocks", __name__)


def _resolve_cible(uid_param):
    """Renvoie (uid_cible, utilisateur_courant). Un joueur ne peut accéder qu'à ses propres données."""
    me = get_current_user()
    if uid_param and me.is_mj:
        return uid_param, me
    return me.id, me


def _get_or_create_stock(utilisateur_id, ressource_id):
    stock = Stock.query.filter_by(
        utilisateur_id=utilisateur_id, ressource_id=ressource_id
    ).first()
    if not stock:
        stock = Stock(utilisateur_id=utilisateur_id, ressource_id=ressource_id, quantite=0)
        db.session.add(stock)
    return stock


# ---------------------------------------------------------------------------
# Stocks
# ---------------------------------------------------------------------------


@stocks_bp.get("/api/stocks")
@login_required
def get_stocks():
    uid = request.args.get("uid")
    cible_uid, me = _resolve_cible(uid)
    if uid and uid != me.id and not me.is_mj:
        return jsonify({"error": "Accès refusé"}), 403

    stocks_existants = (
        Stock.query.filter_by(utilisateur_id=cible_uid)
        .join(Stock.ressource)
        .order_by(Ressource.nom)
        .all()
    )
    stock_par_rid = {s.ressource_id: s for s in stocks_existants}

    toutes = Ressource.query.order_by(Ressource.nom).all()
    result = []
    for r in toutes:
        if r.id in stock_par_rid:
            result.append(stock_par_rid[r.id].to_dict())
        else:
            result.append({
                "id": None,
                "utilisateur_id": cible_uid,
                "ressource_id": r.id,
                "ressource": r.to_dict(),
                "quantite": 0,
            })
    return jsonify(result)


@stocks_bp.put("/api/stocks/<int:ressource_id>")
@login_required
def update_stock(ressource_id):
    uid = request.args.get("uid")
    cible_uid, me = _resolve_cible(uid)
    if uid and uid != me.id and not me.is_mj:
        return jsonify({"error": "Accès refusé"}), 403

    data = request.get_json() or {}
    if "quantite" not in data:
        return jsonify({"error": "Champ 'quantite' requis"}), 400

    ressource = db.get_or_404(Ressource, ressource_id)
    stock = _get_or_create_stock(cible_uid, ressource_id)

    nouvelle_qte = int(data["quantite"])
    delta = nouvelle_qte - stock.quantite
    stock.quantite = nouvelle_qte

    if delta != 0:
        db.session.add(Transaction(
            utilisateur_id=cible_uid,
            ressource_id=ressource_id,
            quantite=delta,
            valeur_florins=delta * ressource.prix_achat,
            motif=data.get("motif", "ajustement_manuel"),
        ))

    db.session.commit()
    return jsonify(stock.to_dict())


# ---------------------------------------------------------------------------
# Gains passifs
# ---------------------------------------------------------------------------


@stocks_bp.get("/api/gains-passifs")
@login_required
def get_gains_passifs():
    uid = request.args.get("uid")
    cible_uid, me = _resolve_cible(uid)
    if uid and uid != me.id and not me.is_mj:
        return jsonify({"error": "Accès refusé"}), 403

    gains = (
        GainPassif.query.filter_by(utilisateur_id=cible_uid)
        .join(GainPassif.ressource)
        .order_by(Ressource.nom)
        .all()
    )
    return jsonify([g.to_dict() for g in gains])


@stocks_bp.put("/api/gains-passifs/<int:ressource_id>")
@login_required
def set_gain_passif(ressource_id):
    uid = request.args.get("uid")
    cible_uid, me = _resolve_cible(uid)
    if uid and uid != me.id and not me.is_mj:
        return jsonify({"error": "Accès refusé"}), 403

    data = request.get_json() or {}
    if "quantite_par_tick" not in data:
        return jsonify({"error": "Champ 'quantite_par_tick' requis"}), 400

    db.get_or_404(Ressource, ressource_id)
    gain = GainPassif.query.filter_by(
        utilisateur_id=cible_uid, ressource_id=ressource_id
    ).first()

    if gain:
        gain.quantite_par_tick = int(data["quantite_par_tick"])
        gain.actif = bool(data.get("actif", True))
    else:
        gain = GainPassif(
            utilisateur_id=cible_uid,
            ressource_id=ressource_id,
            quantite_par_tick=int(data["quantite_par_tick"]),
            actif=bool(data.get("actif", True)),
        )
        db.session.add(gain)

    db.session.commit()
    return jsonify(gain.to_dict())


@stocks_bp.delete("/api/gains-passifs/<int:ressource_id>")
@login_required
def delete_gain_passif(ressource_id):
    uid = request.args.get("uid")
    cible_uid, me = _resolve_cible(uid)
    if uid and uid != me.id and not me.is_mj:
        return jsonify({"error": "Accès refusé"}), 403

    gain = GainPassif.query.filter_by(
        utilisateur_id=cible_uid, ressource_id=ressource_id
    ).first()
    if not gain:
        return jsonify({"error": "Gain passif introuvable"}), 404
    db.session.delete(gain)
    db.session.commit()
    return jsonify({"ok": True})
