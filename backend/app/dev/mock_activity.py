"""
Orchestration du mock dev : comptes, stocks, gains, évènements factices, tours simulés.

Activation : ENABLE_DEV_MOCK=1. Données dans mock_constants.py ; évènements dans mock_evenements.py.
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
from .mock_constants import MOCK_GAINS, MOCK_IDS, MOCK_STOCKS, MOCK_USERS
from .mock_evenements import creer_evenements_mock_dev

logger = logging.getLogger(__name__)


def _env_enabled() -> bool:
    v = os.getenv("ENABLE_DEV_MOCK", "").strip().lower()
    return v in ("1", "true", "yes")


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

    creer_evenements_mock_dev(rid)

    _appliquer_choc_prix(
        ["Bois", "Charbon", "Argent"],
        [105.0, 97.0, 108.0],
    )

    _appliquer_gains_passifs(app)
    logger.info("Dev mock : tour simulé 1/2 terminé.")

    time.sleep(9)

    _appliquer_choc_prix(
        ["Bois", "Acier", "Coton"],
        [102.0, 95.0, 110.0],
    )

    _appliquer_gains_passifs(app)
    logger.info("Dev mock : tour simulé 2/2 terminé. Mock terminé.")
