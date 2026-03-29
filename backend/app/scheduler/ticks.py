import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


def _appliquer_gains_passifs(app):
    """
    Parcourt tous les gains passifs actifs et incrémente/décrémente les stocks.
    Une transaction est enregistrée pour chaque mouvement.
    Exécuté chaque mercredi et samedi à 00h00.
    """
    with app.app_context():
        from ..extensions import db
        from ..models import GainPassif, Stock, Transaction

        gains = GainPassif.query.filter_by(actif=True).all()
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

            stock.quantite += gain.quantite_par_tick
            db.session.add(Transaction(
                utilisateur_id=gain.utilisateur_id,
                ressource_id=gain.ressource_id,
                quantite=gain.quantite_par_tick,
                valeur_florins=gain.quantite_par_tick * gain.ressource.prix_achat,
                motif="gain_passif",
            ))

        db.session.commit()
        logger.info("Tick gains passifs : %d entrées traitées.", len(gains))


def start_scheduler(app):
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        func=_appliquer_gains_passifs,
        args=[app],
        trigger=CronTrigger(day_of_week="wed,sat", hour=0, minute=0),
        id="tick_gains_passifs",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler démarré — ticks chaque mercredi et samedi à 00h00.")
    return scheduler
