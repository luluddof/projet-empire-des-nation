from datetime import UTC, datetime

from ..extensions import db


class Transaction(db.Model):
    """
    Historique de tous les mouvements de stock.
    quantite > 0 = gain, quantite < 0 = perte.
    valeur_florins reflète la valeur au prix d'achat au moment du mouvement.
    """

    __tablename__ = "transaction"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.String(20), db.ForeignKey("utilisateur.id"), nullable=False
    )
    ressource_id = db.Column(
        db.Integer, db.ForeignKey("ressource.id"), nullable=False
    )
    quantite = db.Column(db.Integer, nullable=False)
    valeur_florins = db.Column(db.Integer, nullable=False)
    motif = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)

    ressource = db.relationship("Ressource")

    def to_dict(self):
        return {
            "id": self.id,
            "utilisateur_id": self.utilisateur_id,
            "ressource_id": self.ressource_id,
            "ressource": self.ressource.to_dict(),
            "quantite": self.quantite,
            "valeur_florins": self.valeur_florins,
            "motif": self.motif,
            "created_at": self.created_at.isoformat(),
        }
