import pytest

from app import create_app
from app.extensions import db as _db
from app.data.seed import NOM_RESSOURCE_FLORINS
from app.models import Ressource, Utilisateur


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
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "MJ_DISCORD_IDS": "",
        }
    )
    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _session_discord(uid: str, username: str, is_mj: bool = False):
    return {"id": uid, "username": username, "avatar": None, "is_mj": is_mj}


@pytest.fixture()
def client_joueur(app):
    """Client Flask connecté en tant que joueur (non MJ)."""
    with app.app_context():
        u = Utilisateur(id="100", username="JoueurTest", is_mj=False)
        _db.session.add(u)
        _db.session.commit()
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["discord_user"] = _session_discord("100", "JoueurTest", False)
    return c


@pytest.fixture()
def client_joueur_b(app):
    """Deuxième joueur pour tests cross-utilisateur."""
    with app.app_context():
        u = Utilisateur(id="101", username="JoueurB", is_mj=False)
        _db.session.add(u)
        _db.session.commit()
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["discord_user"] = _session_discord("101", "JoueurB", False)
    return c


@pytest.fixture()
def client_mj(app):
    """Client Flask connecté en tant que MJ."""
    with app.app_context():
        u = Utilisateur(id="200", username="MJTest", is_mj=True)
        _db.session.add(u)
        _db.session.commit()
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["discord_user"] = _session_discord("200", "MJTest", True)
    return c


@pytest.fixture()
def ids_ressources(app):
    """Identifiants Florins + une ressource marchande (seed)."""
    with app.app_context():
        flor = Ressource.query.filter_by(nom=NOM_RESSOURCE_FLORINS).first()
        acier = Ressource.query.filter_by(nom="Acier").first()
        assert flor is not None, "Seed Florins requis"
        assert acier is not None, "Seed Acier requis"
        return {"florins": flor.id, "acier": acier.id}
