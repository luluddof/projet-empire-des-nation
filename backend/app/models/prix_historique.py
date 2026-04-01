from datetime import UTC, datetime

from ..extensions import db


class PrixRessourceHistorique(db.Model):
    """Points pour suivre l’évolution des prix marché (achat / modifié) dans le temps."""

    __tablename__ = "prix_ressource_historique"

    id = db.Column(db.Integer, primary_key=True)
    ressource_id = db.Column(
        db.Integer, db.ForeignKey("ressource.id"), nullable=False, index=True
    )
    prix_modifie = db.Column(db.Integer, nullable=False)
    prix_achat = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)

    ressource = db.relationship("Ressource")

    def to_dict(self):
        return {
            "id": self.id,
            "ressource_id": self.ressource_id,
            "prix_modifie": self.prix_modifie,
            "prix_achat": self.prix_achat,
            "created_at": self.created_at.isoformat(),
        }
