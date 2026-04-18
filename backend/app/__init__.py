import os

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from .api import all_blueprints
from .data.seed import ensure_florins_ressource, seed_ressources
from .extensions import db
from .migrate_db import (
    migrate_gain_passif_balise_mode,
    migrate_gain_passif_multi,
    migrate_gain_passif_delai_tours,
    migrate_gain_passif_evenement_id,
    migrate_evenements_schema,
    migrate_legacy_categories_string,
    migrate_modificateur_to_percent,
    run_schema_updates,
    seed_prix_historique_si_vide,
)
from .models import Categorie, Ressource
from .scheduler import start_scheduler


def _env_str(key, default=""):
    """Lit une variable d'environnement en supprimant espaces / guillemets parasites."""
    raw = os.getenv(key, default)
    if raw is None:
        return default
    v = str(raw).strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
        v = v[1:-1].strip()
    return v


def create_app(test_config=None):
    load_dotenv(override=True)
    app = Flask(__name__, instance_relative_config=True)

    default_redirect = "http://localhost:5173/api/auth/discord/callback"

    app.config.from_mapping(
        SECRET_KEY=_env_str("FLASK_SECRET_KEY", "change-me"),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL", f"sqlite:///{os.path.join(app.instance_path, 'empire.db')}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        DISCORD_CLIENT_ID=_env_str("DISCORD_CLIENT_ID", ""),
        DISCORD_CLIENT_SECRET=_env_str("DISCORD_CLIENT_SECRET", ""),
        DISCORD_REDIRECT_URI=_env_str("DISCORD_REDIRECT_URI", default_redirect),
        FRONTEND_URL=_env_str("FRONTEND_URL", "http://localhost:5173"),
        MJ_DISCORD_IDS=_env_str("MJ_DISCORD_IDS", ""),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    if test_config is not None:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    CORS(
        app,
        resources={r"/api/*": {"origins": [app.config["FRONTEND_URL"]]}},
        supports_credentials=True,
    )

    db.init_app(app)

    for bp in all_blueprints:
        app.register_blueprint(bp)

    with app.app_context():
        run_schema_updates()
        migrate_gain_passif_multi()
        migrate_gain_passif_balise_mode()
        migrate_gain_passif_delai_tours()
        migrate_gain_passif_evenement_id()
        migrate_evenements_schema()
        migrate_modificateur_to_percent()
        migrate_legacy_categories_string()
        seed_ressources(db, Ressource, Categorie)
        ensure_florins_ressource(db, Ressource)
        seed_prix_historique_si_vide()
        if not app.config.get("TESTING"):
            from .dev.mock_activity import run_dev_mock_once

            run_dev_mock_once(app)

    if not app.config.get("TESTING"):
        start_scheduler(app)

    return app
