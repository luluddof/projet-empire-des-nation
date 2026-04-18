import json
from datetime import UTC, datetime

from ..extensions import db


class Evenement(db.Model):
    __tablename__ = "evenement"

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    # Interrupteur global (désactive tout le monde d'un coup)
    actif = db.Column(db.Boolean, nullable=False, default=True)
    # Brouillon : définition seule, aucun joueur / aucun effet tant que publié
    brouillon = db.Column(db.Boolean, nullable=False, default=True)
    # Une fois publié (brouillon levé au moins une fois), l’UI ne propose plus le brouillon.
    deja_publie = db.Column(db.Boolean, nullable=False, default=False)
    # aucun | tous | joueurs — qui est ciblé quand l'évènement n'est pas brouillon
    cible = db.Column(db.String(20), nullable=False, default="aucun")
    # JSON ["id_discord", ...] si cible == joueurs
    cible_utilisateur_ids = db.Column(db.Text, nullable=False, default="[]")
    # Délais par défaut pour les lignes evenement_joueur (copiés à la publication)
    delai_tours = db.Column(db.Integer, nullable=False, default=0)
    tours_restants = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    joueurs = db.relationship(
        "EvenementJoueur",
        back_populates="evenement",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    impacts_categories = db.relationship(
        "EvenementImpactCategorie",
        back_populates="evenement",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    impacts_ressources = db.relationship(
        "EvenementImpactRessource",
        back_populates="evenement",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    impacts_productions = db.relationship(
        "EvenementImpactProduction",
        back_populates="evenement",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_dict(self):
        try:
            uids = json.loads(self.cible_utilisateur_ids or "[]")
        except Exception:
            uids = []
        return {
            "id": self.id,
            "titre": self.titre,
            "description": self.description or "",
            "actif": bool(self.actif),
            "brouillon": bool(self.brouillon),
            "deja_publie": bool(self.deja_publie),
            "cible": (self.cible or "aucun").strip().lower(),
            "cible_utilisateur_ids": uids if isinstance(uids, list) else [],
            "delai_tours": int(self.delai_tours or 0),
            "tours_restants": int(self.tours_restants) if self.tours_restants is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "joueurs": [x.to_dict() for x in (self.joueurs or [])],
            "impacts": {
                "categories": [x.to_dict() for x in (self.impacts_categories or [])],
                "ressources": [x.to_dict() for x in (self.impacts_ressources or [])],
                "productions": [x.to_dict() for x in (self.impacts_productions or [])],
            },
        }

