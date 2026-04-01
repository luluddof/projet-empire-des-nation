from functools import wraps

from flask import jsonify, session

from ..models import Utilisateur


def get_current_user():
    discord_user = session.get("discord_user")
    if not discord_user:
        return None
    return Utilisateur.query.get(discord_user["id"])


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user():
            return jsonify({"error": "Non authentifié"}), 401
        return f(*args, **kwargs)

    return decorated


def mj_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_mj:
            return jsonify({"error": "Accès réservé aux Maîtres du Jeu"}), 403
        return f(*args, **kwargs)

    return decorated
