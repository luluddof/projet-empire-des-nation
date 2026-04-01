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

    def to_dict(self, utilisateur_id=None):
        """
        Serialisation.

        - sans utilisateur_id : % catalogue global
        - avec utilisateur_id : % effectif (surcharge éventuelle)
        """
        if utilisateur_id is None:
            pct = float(self.modificateur_pct)
        else:
            from .categorie_modificateur_joueur import CategorieModificateurJoueur

            row = CategorieModificateurJoueur.query.filter_by(
                utilisateur_id=utilisateur_id, categorie_id=self.id
            ).first()
            pct = float(row.modificateur_pct) if row is not None else float(self.modificateur_pct)

        return {
            "id": self.id,
            "nom": self.nom,
            "modificateur_pct": pct,
        }
