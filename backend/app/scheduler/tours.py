import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from ..extensions import db
from ..models import GainPassif, Stock, Transaction
from ..utils.gain_passif import delta_ligne
from ..utils.prix import prix_achat_pour_utilisateur

logger = logging.getLogger(__name__)


def _appliquer_gains_passifs(app):
    """
    Parcourt tous les gains passifs actifs et incrémente/décrémente les stocks.
    Une transaction est enregistrée pour chaque mouvement.
    Les gains « temporaires » décrémentent tours_restants ; à 0 le gain est désactivé.
    Exécuté chaque mercredi et samedi à 00h00 (un tour).
    """
    with app.app_context():
        gains = GainPassif.query.filter_by(actif=True).order_by(GainPassif.id).all()
        if not gains:
            return

        for gain in gains:
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
                # Pendant le délai : la production ne s'applique pas, mais on compte le temps.
                gain.delai_tours = delay - 1
                continue

            q = delta_ligne(stock.quantite, gain)
            stock.quantite += q
            pa = prix_achat_pour_utilisateur(gain.ressource, gain.utilisateur_id)
            db.session.add(
                Transaction(
                    utilisateur_id=gain.utilisateur_id,
                    ressource_id=gain.ressource_id,
                    quantite=q,
                    valeur_florins=q * pa,
                    motif="gain_passif",
                )
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
