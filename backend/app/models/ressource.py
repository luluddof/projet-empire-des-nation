from ..extensions import db


class Ressource(db.Model):
    __tablename__ = "ressource"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    type = db.Column(db.String(50), nullable=False)
    prix_base = db.Column(db.Integer, nullable=False)
    modificateur = db.Column(db.Float, nullable=False, default=0.0)
    prix_modifie = db.Column(db.Integer, nullable=False)
    prix_achat = db.Column(db.Integer, nullable=False)
    prix_lointain = db.Column(db.Integer, nullable=False)
    categories = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "type": self.type,
            "prix_base": self.prix_base,
            "modificateur": self.modificateur,
            "prix_modifie": self.prix_modifie,
            "prix_achat": self.prix_achat,
            "prix_lointain": self.prix_lointain,
            "categories": self.categories,
        }
