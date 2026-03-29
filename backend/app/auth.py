from urllib.parse import urlencode

import requests
from flask import Blueprint, current_app, jsonify, redirect, request, session

auth_bp = Blueprint("auth", __name__)


def build_discord_authorize_url():
    params = {
        "client_id": current_app.config["DISCORD_CLIENT_ID"],
        "redirect_uri": current_app.config["DISCORD_REDIRECT_URI"],
        "response_type": "code",
        "scope": "identify",
    }
    return f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"


def exchange_code_for_token(code):
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
    payload = response.json()
    return payload["access_token"]


def fetch_discord_user_profile(access_token):
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


@auth_bp.get("/api/auth/discord/login")
def discord_login():
    return redirect(build_discord_authorize_url())


@auth_bp.get("/api/auth/discord/callback")
def discord_callback():
    code = request.args.get("code")
    frontend_url = current_app.config["FRONTEND_URL"]
    if not code:
        return redirect(f"{frontend_url}/?error=missing_code")

    try:
        access_token = exchange_code_for_token(code)
        discord_user = fetch_discord_user_profile(access_token)
    except requests.RequestException:
        return redirect(f"{frontend_url}/?error=discord_auth_failed")

    session["discord_user"] = discord_user
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
