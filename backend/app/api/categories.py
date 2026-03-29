from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Categorie
from ..utils.prix import recalcule_prix_ressource
from ..utils.prix_snapshot import enregistrer_snapshot_prix
from ..utils.decorators import login_required, mj_required

categories_bp = Blueprint("categories", __name__)


def _propager_prix_vers_ressources_liees(cat: Categorie):
    for r in list(cat.ressources):
        recalcule_prix_ressource(r)
        enregistrer_snapshot_prix(r)


@categories_bp.get("/api/categories")
@login_required
def list_categories():
    rows = Categorie.query.order_by(Categorie.nom).all()
    return jsonify([c.to_dict() for c in rows])


@categories_bp.post("/api/categories")
@mj_required
def create_categorie():
    data = request.get_json() or {}
    if "nom" not in data or not str(data["nom"]).strip():
        return jsonify({"error": "Champ 'nom' requis"}), 400
    nom = str(data["nom"]).strip()
    if Categorie.query.filter_by(nom=nom).first():
        return jsonify({"error": "Cette catégorie existe déjà"}), 400
    pct = float(data.get("modificateur_pct", 100.0))
    c = Categorie(nom=nom, modificateur_pct=pct)
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201


@categories_bp.put("/api/categories/<int:categorie_id>")
@mj_required
def update_categorie(categorie_id):
    c = db.get_or_404(Categorie, categorie_id)
    data = request.get_json() or {}
    if "nom" in data and str(data["nom"]).strip():
        nouveau = str(data["nom"]).strip()
        existant = Categorie.query.filter(Categorie.nom == nouveau, Categorie.id != c.id).first()
        if existant:
            return jsonify({"error": "Ce nom est déjà utilisé"}), 400
        c.nom = nouveau
    if "modificateur_pct" in data:
        c.modificateur_pct = float(data["modificateur_pct"])
    db.session.commit()
    if data.get("propager"):
        _propager_prix_vers_ressources_liees(c)
        db.session.commit()
    return jsonify(c.to_dict())


@categories_bp.delete("/api/categories/<int:categorie_id>")
@mj_required
def delete_categorie(categorie_id):
    c = db.get_or_404(Categorie, categorie_id)
    for r in list(c.ressources):
        r.categories_rel.remove(c)
        recalcule_prix_ressource(r)
        enregistrer_snapshot_prix(r)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"ok": True})
