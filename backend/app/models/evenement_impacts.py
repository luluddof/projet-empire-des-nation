from ..extensions import db


class EvenementImpactCategorie(db.Model):
    __tablename__ = "evenement_impact_categorie"

    id = db.Column(db.Integer, primary_key=True)
    evenement_id = db.Column(db.Integer, db.ForeignKey("evenement.id"), nullable=False, index=True)
    categorie_id = db.Column(db.Integer, db.ForeignKey("categorie.id"), nullable=False, index=True)
    # add | remove | set (comme bulk prix ressources)
    operation = db.Column(db.String(10), nullable=False, default="add")
    valeur_pct = db.Column(db.Float, nullable=False, default=0.0)

    evenement = db.relationship("Evenement", back_populates="impacts_categories")
    categorie = db.relationship("Categorie")

    def to_dict(self):
        return {
            "id": self.id,
            "evenement_id": self.evenement_id,
            "categorie_id": self.categorie_id,
            "categorie_nom": getattr(self.categorie, "nom", None),
            "operation": self.operation,
            "valeur_pct": float(self.valeur_pct),
        }


class EvenementImpactRessource(db.Model):
    __tablename__ = "evenement_impact_ressource"

    id = db.Column(db.Integer, primary_key=True)
    evenement_id = db.Column(db.Integer, db.ForeignKey("evenement.id"), nullable=False, index=True)
    ressource_id = db.Column(db.Integer, db.ForeignKey("ressource.id"), nullable=False, index=True)
    # add | remove | set (comme bulk prix ressources)
    operation = db.Column(db.String(10), nullable=False, default="add")
    valeur_pct = db.Column(db.Float, nullable=False, default=0.0)

    evenement = db.relationship("Evenement", back_populates="impacts_ressources")
    ressource = db.relationship("Ressource")

    def to_dict(self):
        return {
            "id": self.id,
            "evenement_id": self.evenement_id,
            "ressource_id": self.ressource_id,
            "ressource_nom": getattr(self.ressource, "nom", None),
            "operation": self.operation,
            "valeur_pct": float(self.valeur_pct),
        }


class EvenementImpactProduction(db.Model):
    """
    Impact "production" = création d'une ligne GainPassif balisée "evenement".
    La suppression / désactivation de l'évènement supprime ces lignes.
    """

    __tablename__ = "evenement_impact_production"

    id = db.Column(db.Integer, primary_key=True)
    evenement_id = db.Column(db.Integer, db.ForeignKey("evenement.id"), nullable=False, index=True)

    utilisateur_id = db.Column(db.String(20), db.ForeignKey("utilisateur.id"), nullable=True, index=True)
    ressource_id = db.Column(db.Integer, db.ForeignKey("ressource.id"), nullable=False, index=True)
    quantite_par_tour = db.Column(db.Integer, nullable=False)
    mode_production = db.Column(db.String(20), nullable=False, default="fixe")
    delai_tours = db.Column(db.Integer, nullable=False, default=0)
    tours_restants = db.Column(db.Integer, nullable=True)
    actif = db.Column(db.Boolean, nullable=False, default=True)

    evenement = db.relationship("Evenement", back_populates="impacts_productions")
    ressource = db.relationship("Ressource")
    utilisateur = db.relationship("Utilisateur")

    def to_dict(self):
        return {
            "id": self.id,
            "evenement_id": self.evenement_id,
            "utilisateur_id": self.utilisateur_id,
            "ressource_id": self.ressource_id,
            "ressource_nom": getattr(self.ressource, "nom", None),
            "quantite_par_tour": int(self.quantite_par_tour),
            "mode_production": self.mode_production,
            "delai_tours": int(self.delai_tours or 0),
            "tours_restants": int(self.tours_restants) if self.tours_restants is not None else None,
            "actif": bool(self.actif),
        }

