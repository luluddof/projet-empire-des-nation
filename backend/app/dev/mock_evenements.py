"""
Évènements de démo pour ENABLE_DEV_MOCK — isolé du flux principal mock_activity.
"""

from __future__ import annotations

import json

from ..extensions import db
from ..models import Categorie, Evenement, EvenementImpactCategorie, EvenementImpactProduction, EvenementImpactRessource
from ..services.evenement_service import appliquer_effets_materiels, marquer_deja_publie_si_non_brouillon
from .mock_constants import MOCK_IDS


def _cat_id(nom: str) -> int:
    c = Categorie.query.filter_by(nom=nom).first()
    if c is None:
        raise RuntimeError(f"Catégorie « {nom} » absente du seed")
    return c.id


def creer_evenements_mock_dev(rid: callable) -> None:
    """Couverture : cible tous, paires de joueurs, joueur seul, brouillon."""
    e1 = Evenement(
        titre="Sécheresse [dev]",
        description="Impact prix sur la catégorie Agro-alimentaire (+12 %). Cible : tous les joueurs.",
        actif=True,
        brouillon=False,
        cible="tous",
        cible_utilisateur_ids="[]",
        delai_tours=0,
        tours_restants=None,
    )
    db.session.add(e1)
    db.session.flush()
    e1.impacts_categories.append(
        EvenementImpactCategorie(
            categorie_id=_cat_id("Agro-alimentaire"),
            operation="add",
            valeur_pct=12.0,
        )
    )
    appliquer_effets_materiels(e1)
    marquer_deja_publie_si_non_brouillon(e1)
    db.session.commit()

    e2 = Evenement(
        titre="Prime acier Nord [dev]",
        description="Surcharge marché sur l’Acier pour Alice et Bob uniquement.",
        actif=True,
        brouillon=False,
        cible="joueurs",
        cible_utilisateur_ids=json.dumps([MOCK_IDS["alice"], MOCK_IDS["bob"]]),
        delai_tours=0,
        tours_restants=None,
    )
    db.session.add(e2)
    db.session.flush()
    e2.impacts_ressources.append(
        EvenementImpactRessource(
            ressource_id=rid("Acier"),
            operation="add",
            valeur_pct=5.0,
        )
    )
    appliquer_effets_materiels(e2)
    marquer_deja_publie_si_non_brouillon(e2)
    db.session.commit()

    e3 = Evenement(
        titre="Offre coton [dev]",
        description="Modificateur ressource Coton : remove 3 (points de %) pour Charlie et Diana.",
        actif=True,
        brouillon=False,
        cible="joueurs",
        cible_utilisateur_ids=json.dumps([MOCK_IDS["charlie"], MOCK_IDS["diana"]]),
        delai_tours=0,
        tours_restants=None,
    )
    db.session.add(e3)
    db.session.flush()
    e3.impacts_ressources.append(
        EvenementImpactRessource(
            ressource_id=rid("Coton"),
            operation="remove",
            valeur_pct=3.0,
        )
    )
    appliquer_effets_materiels(e3)
    marquer_deja_publie_si_non_brouillon(e3)
    db.session.commit()

    e4 = Evenement(
        titre="Aide sylvicole [dev]",
        description="Une ligne de production +1 Bois / tour pour Alice.",
        actif=True,
        brouillon=False,
        cible="joueurs",
        cible_utilisateur_ids=json.dumps([MOCK_IDS["alice"]]),
        delai_tours=0,
        tours_restants=None,
    )
    db.session.add(e4)
    db.session.flush()
    e4.impacts_productions.append(
        EvenementImpactProduction(
            utilisateur_id=None,
            ressource_id=rid("Bois"),
            quantite_par_tour=1,
            mode_production="fixe",
            delai_tours=0,
            tours_restants=None,
            actif=True,
        )
    )
    appliquer_effets_materiels(e4)
    marquer_deja_publie_si_non_brouillon(e4)
    db.session.commit()

    e5 = Evenement(
        titre="Raid naval (brouillon) [dev]",
        description="Évènement préparé — aucun joueur affecté tant que le brouillon est coché.",
        actif=True,
        brouillon=True,
        cible="aucun",
        cible_utilisateur_ids="[]",
        delai_tours=0,
        tours_restants=None,
    )
    db.session.add(e5)
    db.session.flush()
    e5.impacts_categories.append(
        EvenementImpactCategorie(
            categorie_id=_cat_id("Métallurgie"),
            operation="add",
            valeur_pct=20.0,
        )
    )
    appliquer_effets_materiels(e5)
    marquer_deja_publie_si_non_brouillon(e5)
    db.session.commit()
