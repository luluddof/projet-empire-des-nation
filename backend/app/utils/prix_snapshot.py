"""Enregistrement des points d’historique des prix marché."""

from ..extensions import db
from ..models import PrixRessourceHistorique


def enregistrer_snapshot_prix(ressource) -> None:
    """Ajoute un point (prix modifié / achat) pour une ressource."""
    if ressource is None:
        return
    db.session.add(
        PrixRessourceHistorique(
            ressource_id=ressource.id,
            prix_modifie=int(ressource.prix_modifie),
            prix_achat=int(ressource.prix_achat),
        )
    )
