"""
Activité fictive pour le développement local.

Activation : ENABLE_DEV_MOCK=1 (ou true) dans l'environnement du backend.
Désactivation prod : ne pas définir cette variable (ou 0 / false).

Comportement (une seule fois par base) :
- Comptes factices (IDs Discord fixes) : 4 joueurs + 1 MJ factice.
- Stocks de départ et 2 règles de production (gain passif) par compte.
- Variations de prix sur quelques ressources du catalogue + snapshots d'historique.
- 2 « tours » simulés en réutilisant le même traitement que le scheduler.

Pour retirer complètement : supprimer ENABLE_DEV_MOCK, puis optionnellement le dossier
app/dev/ et l'import dans app/__init__.py. Les comptes factices restent en base tant
qu'on ne les supprime pas (username préfixé [dev]).
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime

from ..extensions import db
from ..models import GainPassif, Ressource, Stock, Transaction, Utilisateur
from ..scheduler.tours import _appliquer_gains_passifs
from ..utils.prix import recalcule_prix_ressource
from ..utils.prix_snapshot import enregistrer_snapshot_prix

logger = logging.getLogger(__name__)


def _env_enabled() -> bool:
    v = os.getenv("ENABLE_DEV_MOCK", "").strip().lower()
    return v in ("1", "true", "yes")


# IDs « neige » (format Discord) — éviter collision avec de vrais comptes
MOCK_IDS = {
    "alice": "900000000000000001",
    "bob": "900000000000000002",
    "charlie": "900000000000000003",
    "diana": "900000000000000004",
    "mj_dev": "900000000000000005",
}

# (username, discord_id, is_mj)
MOCK_USERS: list[tuple[str, str, bool]] = [
    ("[dev] Alice", MOCK_IDS["alice"], False),
    ("[dev] Bob", MOCK_IDS["bob"], False),
    ("[dev] Charlie", MOCK_IDS["charlie"], False),
    ("[dev] Diana", MOCK_IDS["diana"], False),
    ("[dev] MJ secondaire", MOCK_IDS["mj_dev"], True),
]

# par utilisateur_id : liste (nom_ressource, quantite, balise)
MOCK_GAINS: dict[str, list[tuple[str, int, str]]] = {
    MOCK_IDS["alice"]: [
        ("Bois", 35, "science"),
        ("Bétail", 12, "autre"),
    ],
    MOCK_IDS["bob"]: [
        ("Charbon", 28, "politique"),
        ("Acier", 8, "science"),
    ],
    MOCK_IDS["charlie"]: [
        ("Coton", 20, "evenement"),
        ("Argent", 3, "autre"),
    ],
    MOCK_IDS["diana"]: [
        ("Alcools", 15, "politique"),
        ("Bois", 10, "autre"),
    ],
    MOCK_IDS["mj_dev"]: [
        ("Acier", 25, "science"),
        ("Bronze", 6, "politique"),
    ],
}

# par utilisateur_id : liste (nom_ressource, quantite)
MOCK_STOCKS: dict[str, list[tuple[str, int]]] = {
    MOCK_IDS["alice"]: [("Florins", 8_000_000), ("Bois", 1400), ("Bétail", 200)],
    MOCK_IDS["bob"]: [("Florins", 5_500_000), ("Charbon", 900), ("Acier", 120)],
    MOCK_IDS["charlie"]: [("Florins", 6_200_000), ("Coton", 350), ("Argent", 45)],
    MOCK_IDS["diana"]: [("Florins", 4_000_000), ("Alcools", 180), ("Bois", 600)],
    MOCK_IDS["mj_dev"]: [("Florins", 12_000_000), ("Acier", 400), ("Bronze", 90)],
}


def _ressource_par_nom(nom: str) -> Ressource | None:
    return Ressource.query.filter_by(nom=nom).first()


def _appliquer_choc_prix(noms: list[str], facteurs_pct: list[float]) -> None:
    """facteurs_pct : modificateur_pct absolu sur la ressource (ex. 105.0 = +5 %)."""
    for nom, pct in zip(noms, facteurs_pct):
        r = _ressource_par_nom(nom)
        if r is None:
            logger.warning("Dev mock : ressource « %s » introuvable, ignorée.", nom)
            continue
        r.modificateur_pct = float(pct)
        recalcule_prix_ressource(r)
        enregistrer_snapshot_prix(r)
    db.session.commit()


def _deja_initialise() -> bool:
    """
    Le mock doit être idempotent, mais on évite de "bloquer" sur une initialisation partielle.
    Si les utilisateurs existent mais qu'il manque les gains passifs ou les transactions,
    on ré-exécute le mock pour compléter la base.
    """
    alice = db.session.get(Utilisateur, MOCK_IDS["alice"])
    if alice is None:
        return False
    gains = GainPassif.query.filter_by(utilisateur_id=MOCK_IDS["alice"]).count()
    if gains <= 0:
        return False
    tx_gain = Transaction.query.filter_by(
        utilisateur_id=MOCK_IDS["alice"],
        motif="gain_passif",
    ).count()
    if tx_gain <= 0:
        return False
    return True


def run_dev_mock_once(app) -> None:
    """
    Exécuté au démarrage si ENABLE_DEV_MOCK est actif (hors TESTING).
    Idempotent : ne fait rien si le compte Alice factice existe déjà.
    """
    if not _env_enabled():
        return
    try:
        _run_impl(app)
    except Exception:
        logger.exception("Dev mock activity : échec (voir la trace ci-dessus).")


def _run_impl(app) -> None:
    if _deja_initialise():
        logger.info("Dev mock activity : déjà appliqué (compte %s présent), ignoré.", MOCK_IDS["alice"])
        return

    logger.info("Dev mock activity : création des comptes, stocks, productions et 2 tours simulés…")

    now = datetime.now(UTC)
    for username, uid, is_mj in MOCK_USERS:
        db.session.add(
            Utilisateur(
                id=uid,
                username=username,
                avatar=None,
                is_mj=is_mj,
                created_at=now,
            )
        )

    rid_cache: dict[str, int] = {}

    def rid(nom: str) -> int:
        if nom not in rid_cache:
            r = _ressource_par_nom(nom)
            if r is None:
                raise RuntimeError(f"Ressource « {nom} » absente du seed")
            rid_cache[nom] = r.id
        return rid_cache[nom]

    for uid, lignes in MOCK_STOCKS.items():
        for nom_res, qte in lignes:
            db.session.add(
                Stock(
                    utilisateur_id=uid,
                    ressource_id=rid(nom_res),
                    quantite=qte,
                )
            )

    for uid, lignes in MOCK_GAINS.items():
        for nom_res, qte, balise in lignes:
            db.session.add(
                GainPassif(
                    utilisateur_id=uid,
                    ressource_id=rid(nom_res),
                    quantite_par_tour=qte,
                    actif=True,
                    tours_restants=None,
                    balise=balise,
                    mode_production="fixe",
                )
            )

    db.session.commit()

    # Choc prix avant tour 1
    _appliquer_choc_prix(
        ["Bois", "Charbon", "Argent"],
        [105.0, 97.0, 108.0],
    )

    _appliquer_gains_passifs(app)
    logger.info("Dev mock : tour simulé 1/2 terminé.")

    # On force un écart temporel suffisant pour que le regroupement des transactions
    # (dans /api/gains-passifs/chronologie) ne fusionne pas 2 tours consécutifs.
    # Le regroupement utilise un gap de ~8s ; on met 9s.
    time.sleep(9)

    # Choc prix entre les deux tours
    _appliquer_choc_prix(
        ["Bois", "Acier", "Coton"],
        [102.0, 95.0, 110.0],
    )

    _appliquer_gains_passifs(app)
    logger.info("Dev mock : tour simulé 2/2 terminé. Mock terminé.")
