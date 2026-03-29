from ..extensions import db
from .associations import ressource_categorie
from ..utils.prix import multiplicateur_effectif


class Ressource(db.Model):
    __tablename__ = "ressource"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    type = db.Column(db.String(50), nullable=False)
    prix_base = db.Column(db.Integer, nullable=False)
    modificateur_pct = db.Column(db.Float, nullable=False, default=100.0)
    prix_modifie = db.Column(db.Integer, nullable=False)
    prix_achat = db.Column(db.Integer, nullable=False)
    prix_lointain = db.Column(db.Integer, nullable=False)

    categories_rel = db.relationship(
        "Categorie",
        secondary=ressource_categorie,
        back_populates="ressources",
    )

    def to_dict(self):
        cats = sorted(self.categories_rel, key=lambda c: c.nom.lower())
        return {
            "id": self.id,
            "nom": self.nom,
            "type": self.type,
            "prix_base": self.prix_base,
            "modificateur_pct": self.modificateur_pct,
            "facteur_prix": round(multiplicateur_effectif(self), 6),
            "prix_modifie": self.prix_modifie,
            "prix_achat": self.prix_achat,
            "prix_lointain": self.prix_lointain,
            "categories": [c.to_dict() for c in cats],
            "categorie_ids": [c.id for c in cats],
        }
