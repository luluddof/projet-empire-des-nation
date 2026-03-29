from urllib.parse import urlencode

import requests
from flask import Blueprint, current_app, jsonify, redirect, request, session

from ..extensions import db
from ..models import Utilisateur

auth_bp = Blueprint("auth", __name__)


def _build_discord_authorize_url():
    params = {
        "client_id": current_app.config["DISCORD_CLIENT_ID"],
        "redirect_uri": current_app.config["DISCORD_REDIRECT_URI"],
        "response_type": "code",
        "scope": "identify",
    }
    return f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"


def _exchange_code_for_token(code):
    response = requests.post(
        "https://discord.com/api/oauth2/token",
        data={
            "client_id": current_app.config["DISCORD_CLIENT_ID"],
            "client_secret": current_app.config["DISCORD_CLIENT_SECRET"],
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": current_app.config["DISCORD_REDIRECT_URI"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def _fetch_discord_profile(access_token):
    response = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    return {
        "id": payload.get("id"),
        "username": payload.get("username"),
        "avatar": payload.get("avatar"),
    }


def _upsert_utilisateur(profile):
    """Crée ou met à jour l'utilisateur en base, renvoie l'objet Utilisateur."""
    mj_raw = current_app.config.get("MJ_DISCORD_IDS", "") or ""
    mj_ids = {x.strip() for x in mj_raw.split(",") if x.strip()}
    user = db.session.get(Utilisateur, profile["id"])
    if user is None:
        user = Utilisateur(
            id=profile["id"],
            username=profile["username"],
            avatar=profile.get("avatar"),
            is_mj=profile["id"] in mj_ids,
        )
        db.session.add(user)
    else:
        user.username = profile["username"]
        user.avatar = profile.get("avatar")
        if profile["id"] in mj_ids:
            user.is_mj = True
    db.session.commit()
    return user


@auth_bp.get("/api/auth/discord/redirect-uri")
def discord_redirect_uri_info():
    """
    Retourne l'URI exacte envoyée à Discord pour OAuth2.
    Copie cette valeur dans Discord Developer Portal > OAuth2 > Redirects (Save).
    """
    uri = current_app.config["DISCORD_REDIRECT_URI"]
    return jsonify(
        {
            "redirect_uri": uri,
            "hint": "Colle cette chaine telle quelle dans OAuth2 > Redirects, puis enregistre.",
        }
    )


@auth_bp.get("/api/auth/discord/login")
def discord_login():
    return redirect(_build_discord_authorize_url())


@auth_bp.get("/api/auth/discord/callback")
def discord_callback():
    code = request.args.get("code")
    frontend_url = current_app.config["FRONTEND_URL"]
    if not code:
        return redirect(f"{frontend_url}/?error=missing_code")

    try:
        access_token = _exchange_code_for_token(code)
        profile = _fetch_discord_profile(access_token)
    except requests.RequestException:
        return redirect(f"{frontend_url}/?error=discord_auth_failed")

    user = _upsert_utilisateur(profile)
    session["discord_user"] = {**profile, "is_mj": user.is_mj}
    return redirect(f"{frontend_url}/")


@auth_bp.get("/api/auth/me")
def me():
    discord_user = session.get("discord_user")
    if not discord_user:
        return jsonify({"authenticated": False})
    return jsonify({"authenticated": True, "user": discord_user})


@auth_bp.post("/api/auth/logout")
def logout():
    session.pop("discord_user", None)
    return jsonify({"ok": True})
