from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Utilisateur
from ..utils.decorators import login_required, mj_required

utilisateurs_bp = Blueprint("utilisateurs", __name__)


@utilisateurs_bp.get("/api/utilisateurs")
@mj_required
def list_utilisateurs():
    users = Utilisateur.query.order_by(Utilisateur.username).all()
    return jsonify([u.to_dict() for u in users])


@utilisateurs_bp.get("/api/utilisateurs/<string:uid>")
@mj_required
def get_utilisateur(uid):
    user = db.get_or_404(Utilisateur, uid)
    return jsonify(user.to_dict())


@utilisateurs_bp.patch("/api/utilisateurs/<string:uid>")
@mj_required
def update_utilisateur(uid):
    user = db.get_or_404(Utilisateur, uid)
    data = request.get_json() or {}
    if "is_mj" in data:
        user.is_mj = bool(data["is_mj"])
    db.session.commit()
    return jsonify(user.to_dict())
