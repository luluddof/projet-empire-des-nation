from ..extensions import db


class EvenementJoueur(db.Model):
    """
    Un joueur concerné par un évènement (prix + productions).
    - delai_tours : tours à attendre avant que les effets s'appliquent pour ce joueur
    - tours_restants : NULL = jusqu'à désactivation MJ ; sinon nombre de tours d'effet après le délai
    - actif : le MJ peut retirer un joueur sans supprimer l'évènement
    """

    __tablename__ = "evenement_joueur"
    __table_args__ = (db.UniqueConstraint("evenement_id", "utilisateur_id", name="uq_evenement_joueur_uid"),)

    id = db.Column(db.Integer, primary_key=True)
    evenement_id = db.Column(db.Integer, db.ForeignKey("evenement.id"), nullable=False, index=True)
    utilisateur_id = db.Column(db.String(20), db.ForeignKey("utilisateur.id"), nullable=False, index=True)

    delai_tours = db.Column(db.Integer, nullable=False, default=0)
    tours_restants = db.Column(db.Integer, nullable=True)
    actif = db.Column(db.Boolean, nullable=False, default=True)

    evenement = db.relationship("Evenement", back_populates="joueurs")
    utilisateur = db.relationship("Utilisateur")

    def to_dict(self):
        return {
            "id": self.id,
            "evenement_id": self.evenement_id,
            "utilisateur_id": self.utilisateur_id,
            "username": getattr(self.utilisateur, "username", None),
            "delai_tours": int(self.delai_tours or 0),
            "tours_restants": int(self.tours_restants) if self.tours_restants is not None else None,
            "actif": bool(self.actif),
        }
