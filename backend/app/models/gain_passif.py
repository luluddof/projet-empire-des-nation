from ..extensions import db


class GainPassif(db.Model):
    """
    Gain ou perte passive par tour planifié (mercredi et samedi à minuit).
    Plusieurs entrées par (joueur, ressource) possibles.
    tours_restants NULL = définitif ; sinon nombre de tours restant avant désactivation.
    """

    __tablename__ = "gain_passif"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.String(20), db.ForeignKey("utilisateur.id"), nullable=False, index=True
    )
    ressource_id = db.Column(
        db.Integer, db.ForeignKey("ressource.id"), nullable=False, index=True
    )
    quantite_par_tour = db.Column(db.Integer, nullable=False)
    actif = db.Column(db.Boolean, default=True, nullable=False)
    tours_restants = db.Column(db.Integer, nullable=True)
    # science | politique | evenement | autre
    balise = db.Column(db.String(20), nullable=False, default="autre")
    # fixe = unités ; pourcentage = quantite_par_tour interprété comme % du stock avant la ligne
    mode_production = db.Column(db.String(20), nullable=False, default="fixe")

    ressource = db.relationship("Ressource")

    def to_dict(self):
        return {
            "id": self.id,
            "utilisateur_id": self.utilisateur_id,
            "ressource_id": self.ressource_id,
            "ressource": self.ressource.to_dict(),
            "quantite_par_tour": self.quantite_par_tour,
            "actif": self.actif,
            "definitif": self.tours_restants is None,
            "tours_restants": self.tours_restants,
            "balise": getattr(self, "balise", None) or "autre",
            "mode_production": getattr(self, "mode_production", None) or "fixe",
        }
