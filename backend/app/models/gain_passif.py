from ..extensions import db


class GainPassif(db.Model):
    """
    Quantité ajoutée (>0) ou retirée (<0) au stock lors de chaque tick
    planifié (chaque mercredi et samedi à minuit).
    """

    __tablename__ = "gain_passif"
    __table_args__ = (
        db.UniqueConstraint(
            "utilisateur_id", "ressource_id", name="uq_gain_passif"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.String(20), db.ForeignKey("utilisateur.id"), nullable=False
    )
    ressource_id = db.Column(
        db.Integer, db.ForeignKey("ressource.id"), nullable=False
    )
    quantite_par_tick = db.Column(db.Integer, nullable=False)
    actif = db.Column(db.Boolean, default=True, nullable=False)

    ressource = db.relationship("Ressource")

    def to_dict(self):
        return {
            "id": self.id,
            "utilisateur_id": self.utilisateur_id,
            "ressource_id": self.ressource_id,
            "ressource": self.ressource.to_dict(),
            "quantite_par_tick": self.quantite_par_tick,
            "actif": self.actif,
        }
