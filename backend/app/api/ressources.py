from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Ressource
from ..utils import login_required, mj_required

ressources_bp = Blueprint("ressources", __name__)

_CHAMPS = [
    "nom", "type", "prix_base", "modificateur",
    "prix_modifie", "prix_achat", "prix_lointain", "categories",
]
_CHAMPS_OBLIGATOIRES = {"nom", "type", "prix_base", "prix_modifie", "prix_achat", "prix_lointain"}


@ressources_bp.get("/api/ressources")
@login_required
def list_ressources():
    ressources = Ressource.query.order_by(Ressource.nom).all()
    return jsonify([r.to_dict() for r in ressources])


@ressources_bp.get("/api/ressources/<int:ressource_id>")
@login_required
def get_ressource(ressource_id):
    r = db.get_or_404(Ressource, ressource_id)
    return jsonify(r.to_dict())


@ressources_bp.post("/api/ressources")
@mj_required
def create_ressource():
    data = request.get_json() or {}
    manquants = _CHAMPS_OBLIGATOIRES - data.keys()
    if manquants:
        return jsonify({"error": f"Champs obligatoires manquants : {manquants}"}), 400
    r = Ressource(**{k: data[k] for k in _CHAMPS if k in data})
    db.session.add(r)
    db.session.commit()
    return jsonify(r.to_dict()), 201


@ressources_bp.put("/api/ressources/<int:ressource_id>")
@mj_required
def update_ressource(ressource_id):
    r = db.get_or_404(Ressource, ressource_id)
    data = request.get_json() or {}
    for champ in _CHAMPS:
        if champ in data:
            setattr(r, champ, data[champ])
    db.session.commit()
    return jsonify(r.to_dict())


@ressources_bp.delete("/api/ressources/<int:ressource_id>")
@mj_required
def delete_ressource(ressource_id):
    r = db.get_or_404(Ressource, ressource_id)
    db.session.delete(r)
    db.session.commit()
    return jsonify({"ok": True})
