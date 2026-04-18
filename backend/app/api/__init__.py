from .auth import auth_bp
from .categories import categories_bp
from .evenements import evenements_bp
from .health import health_bp
from .ressources import ressources_bp
from .stocks import stocks_bp
from .transactions import transactions_bp
from .utilisateurs import utilisateurs_bp

all_blueprints = [
    health_bp,
    auth_bp,
    categories_bp,
    evenements_bp,
    ressources_bp,
    stocks_bp,
    transactions_bp,
    utilisateurs_bp,
]

__all__ = ["all_blueprints"]
