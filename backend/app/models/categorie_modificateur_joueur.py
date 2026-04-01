from ..extensions import db


class CategorieModificateurJoueur(db.Model):
    """
    Surcharge du % modificateur de catégorie pour un joueur.

    Permet par ex. : catégorie globale = 100% (neutre) mais effective = 80% pour un joueur.
    """

    __tablename__ = "categorie_modificateur_joueur"
    __table_args__ = (
        db.UniqueConstraint(
            "utilisateur_id", "categorie_id", name="uq_cat_mod_user"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.String(20), db.ForeignKey("utilisateur.id"), nullable=False, index=True
    )
    categorie_id = db.Column(
        db.Integer, db.ForeignKey("categorie.id"), nullable=False, index=True
    )
    modificateur_pct = db.Column(db.Float, nullable=False)

    categorie = db.relationship("Categorie")

