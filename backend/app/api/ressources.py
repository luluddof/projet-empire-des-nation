from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Categorie, Ressource
from ..utils.prix import appliquer_produit_categories_sur_ressource, recalcule_prix_ressource
from ..utils.decorators import login_required, mj_required

ressources_bp = Blueprint("ressources", __name__)


def _assign_categories(r: Ressource, categorie_ids):
    if categorie_ids is None:
        return
    ids = [int(x) for x in categorie_ids]
    cats = Categorie.query.filter(Categorie.id.in_(ids)).all()
    if len(cats) != len(ids):
        return False, "Une ou plusieurs catégories sont introuvables"
    r.categories_rel.clear()
    for c in cats:
        r.categories_rel.append(c)
    return True, None


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
    for k in ("nom", "type", "prix_base"):
        if k not in data:
            return jsonify({"error": f"Champ '{k}' requis"}), 400
    # Nouvelle ressource : % ressource = 100 % par défaut ; le prix intègre les % des catégories liées.
    pct_res = float(data.get("modificateur_pct", 100.0))
    r = Ressource(
        nom=str(data["nom"]).strip(),
        type=data["type"],
        prix_base=int(data["prix_base"]),
        modificateur_pct=pct_res,
        prix_modifie=0,
        prix_achat=0,
        prix_lointain=0,
    )
    db.session.add(r)
    db.session.flush()
    ok, err = _assign_categories(r, data.get("categorie_ids", []))
    if not ok:
        db.session.rollback()
        return jsonify({"error": err}), 400
    recalcule_prix_ressource(r)
    db.session.commit()
    return jsonify(r.to_dict()), 201


@ressources_bp.put("/api/ressources/<int:ressource_id>")
@mj_required
def update_ressource(ressource_id):
    r = db.get_or_404(Ressource, ressource_id)
    data = request.get_json() or {}
    if "nom" in data:
        r.nom = str(data["nom"]).strip()
    if "type" in data:
        r.type = data["type"]
    if "prix_base" in data:
        r.prix_base = int(data["prix_base"])
    if "modificateur_pct" in data:
        r.modificateur_pct = float(data["modificateur_pct"])
    if "categorie_ids" in data:
        ok, err = _assign_categories(r, data["categorie_ids"])
        if not ok:
            return jsonify({"error": err}), 400
    recalcule_prix_ressource(r)
    db.session.commit()
    return jsonify(r.to_dict())


@ressources_bp.post("/api/ressources/<int:ressource_id>/appliquer-modificateurs-categories")
@mj_required
def appliquer_mods_categories(ressource_id):
    """Remet modificateur_pct de la ressource à 100 % (neutre)."""
    r = db.get_or_404(Ressource, ressource_id)
    appliquer_produit_categories_sur_ressource(r)
    db.session.commit()
    return jsonify(r.to_dict())


@ressources_bp.delete("/api/ressources/<int:ressource_id>")
@mj_required
def delete_ressource(ressource_id):
    r = db.get_or_404(Ressource, ressource_id)
    db.session.delete(r)
    db.session.commit()
    return jsonify({"ok": True})
