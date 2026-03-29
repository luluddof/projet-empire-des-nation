from ..extensions import db


class Stock(db.Model):
    __tablename__ = "stock"
    __table_args__ = (
        db.UniqueConstraint("utilisateur_id", "ressource_id", name="uq_stock"),
    )

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.String(20), db.ForeignKey("utilisateur.id"), nullable=False
    )
    ressource_id = db.Column(
        db.Integer, db.ForeignKey("ressource.id"), nullable=False
    )
    quantite = db.Column(db.Integer, default=0, nullable=False)

    ressource = db.relationship("Ressource")

    def to_dict(self):
        return {
            "id": self.id,
            "utilisateur_id": self.utilisateur_id,
            "ressource_id": self.ressource_id,
            "ressource": self.ressource.to_dict(),
            "quantite": self.quantite,
        }
