from ..extensions import db
from .associations import ressource_categorie


class Categorie(db.Model):
    __tablename__ = "categorie"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), nullable=False, unique=True)
    modificateur_pct = db.Column(db.Float, nullable=False, default=100.0)

    ressources = db.relationship(
        "Ressource",
        secondary=ressource_categorie,
        back_populates="categories_rel",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "modificateur_pct": self.modificateur_pct,
        }
