import os

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from .auth import auth_bp
from .health import health_bp


def create_app(test_config=None):
    load_dotenv(override=True)
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "change-me"),
        DISCORD_CLIENT_ID=os.getenv("DISCORD_CLIENT_ID", "").strip().strip('"'),
        DISCORD_CLIENT_SECRET=os.getenv("DISCORD_CLIENT_SECRET", "")
        .strip()
        .strip('"'),
        DISCORD_REDIRECT_URI=os.getenv(
            "DISCORD_REDIRECT_URI",
            "http://127.0.0.1:5000/api/auth/discord/callback",
        ),
        FRONTEND_URL=os.getenv("FRONTEND_URL", "http://localhost:5173"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    if test_config is not None:
        app.config.update(test_config)

    CORS(
        app,
        resources={r"/api/*": {"origins": [app.config["FRONTEND_URL"]]}},
        supports_credentials=True,
    )

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)

    return app
