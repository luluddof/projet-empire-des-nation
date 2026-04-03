import logging
import random

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from ..extensions import db
from ..models import GainPassif, Stock, Transaction
from ..utils.gain_passif import delta_ligne, normaliser_mode, tirage_pourcentage_sur_production_tour
from ..utils.prix import prix_achat_pour_utilisateur

logger = logging.getLogger(__name__)


def _ajouter_transaction_gain_passif(utilisateur_id, ressource, ressource_id, quantite, pa, motif="gain_passif"):
    if quantite == 0:
        return
    db.session.add(
        Transaction(
            utilisateur_id=utilisateur_id,
            ressource_id=ressource_id,
            quantite=quantite,
            valeur_florins=quantite * pa,
            motif=motif,
        )
    )


def _creer_archive_recolte_fructueuse(utilisateur_id, ressource_id):
    """Trace en base d’un +1 obtenu par tirage (règle inactive, lecture seule / historique)."""
    g = GainPassif(
        utilisateur_id=utilisateur_id,
        ressource_id=ressource_id,
        quantite_par_tour=1,
        mode_production="fixe",
        balise="recolte_fructueuse",
        actif=False,
        delai_tours=0,
        tours_restants=None,
    )
    db.session.add(g)


def _appliquer_gains_passifs(app):
    """
    Parcourt les gains actifs par (joueur, ressource), ordre des id.
    Pour chaque ressource, la production cumulée « prod » du tour sert de base
    aux règles en % (après toutes les règles fixes et % précédentes).
    Mode pourcentage : troncature + tirage sur la fraction pour ±1 unité ;
    un +1 bonus génère une transaction « recolte_fructueuse » et une entrée d’archive.
    """
    rng = random.Random()
    with app.app_context():
        gains = GainPassif.query.filter_by(actif=True).order_by(
            GainPassif.utilisateur_id, GainPassif.ressource_id, GainPassif.id
        ).all()
        if not gains:
            return

        prod = 0
        cur_key = None

        for gain in gains:
            key = (gain.utilisateur_id, gain.ressource_id)
            if key != cur_key:
                prod = 0
                cur_key = key

            stock = Stock.query.filter_by(
                utilisateur_id=gain.utilisateur_id,
                ressource_id=gain.ressource_id,
            ).first()
            if not stock:
                stock = Stock(
                    utilisateur_id=gain.utilisateur_id,
                    ressource_id=gain.ressource_id,
                    quantite=0,
                )
                db.session.add(stock)

            delay = getattr(gain, "delai_tours", 0) or 0
            try:
                delay = int(delay)
            except Exception:
                delay = 0

            if delay > 0:
                gain.delai_tours = delay - 1
                continue

            mode = normaliser_mode(getattr(gain, "mode_production", None))
            pa = prix_achat_pour_utilisateur(gain.ressource, gain.utilisateur_id)

            if mode == "fixe":
                q = delta_ligne(prod, gain)
                prod += q
                stock.quantite += q
                _ajouter_transaction_gain_passif(
                    gain.utilisateur_id, gain.ressource, gain.ressource_id, q, pa, "gain_passif"
                )
            else:
                raw = prod * float(gain.quantite_par_tour) / 100.0
                q_total, base, extra, recolte_flag = tirage_pourcentage_sur_production_tour(raw, rng)
                prod += q_total
                stock.quantite += q_total

                if extra > 0:
                    if base != 0:
                        _ajouter_transaction_gain_passif(
                            gain.utilisateur_id, gain.ressource, gain.ressource_id, base, pa, "gain_passif"
                        )
                    _ajouter_transaction_gain_passif(
                        gain.utilisateur_id, gain.ressource, gain.ressource_id, extra, pa, "recolte_fructueuse"
                    )
                    _creer_archive_recolte_fructueuse(gain.utilisateur_id, gain.ressource_id)
                else:
                    _ajouter_transaction_gain_passif(
                        gain.utilisateur_id, gain.ressource, gain.ressource_id, q_total, pa, "gain_passif"
                    )

            if gain.tours_restants is not None:
                gain.tours_restants = int(gain.tours_restants) - 1
                if gain.tours_restants <= 0:
                    gain.actif = False

        db.session.commit()
        logger.info("Tour gains passifs : %d entrées traitées.", len(gains))


def start_scheduler(app):
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        func=_appliquer_gains_passifs,
        args=[app],
        trigger=CronTrigger(day_of_week="wed,sat", hour=0, minute=0),
        id="tour_gains_passifs",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler démarré — tours (mercredi & samedi 00h00).")
    return scheduler
