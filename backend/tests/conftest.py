import pytest

from app import create_app


@pytest.fixture()
def app():
    flask_app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DISCORD_CLIENT_ID": "123456",
            "DISCORD_CLIENT_SECRET": "discord-secret",
            "DISCORD_REDIRECT_URI": "http://127.0.0.1:5000/api/auth/discord/callback",
            "FRONTEND_URL": "http://localhost:5173",
        }
    )
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()
