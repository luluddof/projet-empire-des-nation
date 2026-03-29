from ..extensions import db


class RessourceModificateurJoueur(db.Model):
    """Surcharge du % modificateur ressource pour un joueur (catalogue personnalisé)."""

    __tablename__ = "ressource_modificateur_joueur"
    __table_args__ = (
        db.UniqueConstraint("utilisateur_id", "ressource_id", name="uq_res_mod_user"),
    )

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.String(20), db.ForeignKey("utilisateur.id"), nullable=False, index=True
    )
    ressource_id = db.Column(
        db.Integer, db.ForeignKey("ressource.id"), nullable=False, index=True
    )
    modificateur_pct = db.Column(db.Float, nullable=False)

    ressource = db.relationship("Ressource")
