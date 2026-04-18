"""Règles de prix (florins). Modificateurs en % (100 = neutre).

Multiplicateur effectif = (pct_ressource / 100) × ∏(pct_catégorie / 100).

Prix modifié = arrondi(base × M_eff) ; achat = modifié × 1,2 ; lointain = modifié × 2,5.
"""


def _facteur_depuis_pct(pct) -> float:
    v = float(pct) if pct is not None else 100.0
    if v <= 0:
        return 1.0
    return v / 100.0


def _evenement_effet_prix_actif(evenement_id: int, utilisateur_id: str | None) -> bool:
    """Impacts prix d'un évènement : seulement si le joueur est ciblé et la fenêtre temporelle le permet."""
    if utilisateur_id is None:
        return False
    from ..extensions import db
    from ..models import Evenement, EvenementJoueur

    ej = EvenementJoueur.query.filter_by(
        evenement_id=evenement_id, utilisateur_id=utilisateur_id, actif=True
    ).first()
    if ej is None:
        return False
    e = db.session.get(Evenement, evenement_id)
    if e is None or e.brouillon or not e.actif:
        return False
    if int(ej.delai_tours or 0) > 0:
        return False
    if ej.tours_restants is not None and int(ej.tours_restants) <= 0:
        return False
    return True


def _pct_apres_impacts(pct_base: float, impacts: list[dict]) -> float:
    """
    Applique une liste d'impacts {operation, valeur_pct} sur un % base.
    - set : remplace la valeur
    - add : ajoute (delta)
    - remove : retire (delta), comme bulk ressources/catégories
    """
    cur = float(pct_base)
    for imp in impacts or []:
        op = (imp.get("operation") or "add").strip().lower()
        val = float(imp.get("valeur_pct") or 0.0)
        if op == "set":
            cur = val
        elif op == "remove":
            cur = cur - val
        else:
            cur = cur + val
    if cur <= 0:
        return 1.0
    return cur


def _impacts_categorie_pour_utilisateur(categorie_id: int, utilisateur_id: str | None) -> list[dict]:
    if utilisateur_id is None:
        return []
    from ..models import EvenementImpactCategorie

    out = []
    for imp in EvenementImpactCategorie.query.filter_by(categorie_id=categorie_id).all():
        if not _evenement_effet_prix_actif(imp.evenement_id, utilisateur_id):
            continue
        out.append({"operation": imp.operation, "valeur_pct": imp.valeur_pct})
    return out


def _impacts_ressource_pour_utilisateur(ressource_id: int, utilisateur_id: str | None) -> list[dict]:
    if utilisateur_id is None:
        return []
    from ..models import EvenementImpactRessource

    out = []
    for imp in EvenementImpactRessource.query.filter_by(ressource_id=ressource_id).all():
        if not _evenement_effet_prix_actif(imp.evenement_id, utilisateur_id):
            continue
        out.append({"operation": imp.operation, "valeur_pct": imp.valeur_pct})
    return out


def multiplicateur_effectif(r) -> float:
    """
    Facteur prix catalogue global.

    Règle métier (cf. demande utilisateur) :
    - inflation ressource indépendante : (pct_ressource / 100)
    - inflation due aux catégories : moyenne des (pct_categorie / 100)
    """
    f = _facteur_depuis_pct(getattr(r, "modificateur_pct", 100))
    cats = list(getattr(r, "categories_rel", []) or [])
    if not cats:
        return f
    avg = sum(_facteur_depuis_pct(getattr(c, "modificateur_pct", 100)) for c in cats) / len(cats)
    return f * avg


def modificateur_pct_categorie_effectif(categorie, utilisateur_id) -> float:
    """
    % catégorie effectif pour un joueur (surcharge éventuelle).

    - sinon retourne le % catalogue global de la catégorie.
    """
    from ..models.categorie_modificateur_joueur import CategorieModificateurJoueur

    if utilisateur_id is None:
        pct_base = float(getattr(categorie, "modificateur_pct", 100.0))
        return pct_base

    row = CategorieModificateurJoueur.query.filter_by(
        utilisateur_id=utilisateur_id, categorie_id=categorie.id
    ).first()
    if row is not None:
        pct_base = float(row.modificateur_pct)
    else:
        pct_base = float(getattr(categorie, "modificateur_pct", 100.0))
    return _pct_apres_impacts(pct_base, _impacts_categorie_pour_utilisateur(categorie.id, utilisateur_id))


def recalcule_prix_ressource(r):
    m = multiplicateur_effectif(r)
    pm = int(round(r.prix_base * m))
    r.prix_modifie = pm
    r.prix_achat = int(round(pm * 1.2))
    r.prix_lointain = int(round(pm * 2.5))


def appliquer_produit_categories_sur_ressource(r):
    """
    Remet le % propre à la ressource à 100 % (neutre).
    Seuls les % des catégories liées s'appliquent alors au calcul global.
    """
    r.modificateur_pct = 100.0
    recalcule_prix_ressource(r)


def modificateur_pct_effectif(ressource, utilisateur_id) -> float:
    """% ressource effectif : surcharge joueur ou % catalogue global."""
    from ..models.ressource_modificateur_joueur import RessourceModificateurJoueur

    row = None
    if utilisateur_id is not None:
        row = RessourceModificateurJoueur.query.filter_by(
            utilisateur_id=utilisateur_id, ressource_id=ressource.id
        ).first()
    if row is not None:
        pct_base = float(row.modificateur_pct)
    else:
        pct_base = float(getattr(ressource, "modificateur_pct", 100.0))
    return _pct_apres_impacts(pct_base, _impacts_ressource_pour_utilisateur(ressource.id, utilisateur_id))


def multiplicateur_effectif_pour_utilisateur(ressource, utilisateur_id) -> float:
    """
    Facteur prix effectif pour un joueur :
    - facteur ressource (surcharge joueur ou catalogue global)
    - facteur catégories = moyenne des facteurs catégories effectifs pour ce joueur
    """
    f = _facteur_depuis_pct(modificateur_pct_effectif(ressource, utilisateur_id))
    cats = list(getattr(ressource, "categories_rel", []) or [])
    if not cats:
        return f
    avg = sum(
        _facteur_depuis_pct(modificateur_pct_categorie_effectif(c, utilisateur_id))
        for c in cats
    ) / len(cats)
    return f * avg


def prix_derives_pour_utilisateur(ressource, utilisateur_id) -> dict:
    m = multiplicateur_effectif_pour_utilisateur(ressource, utilisateur_id)
    pm = int(round(ressource.prix_base * m))
    return {
        "modificateur_pct": modificateur_pct_effectif(ressource, utilisateur_id),
        "facteur_prix": round(m, 6),
        "prix_modifie": pm,
        "prix_achat": int(round(pm * 1.2)),
        "prix_lointain": int(round(pm * 2.5)),
    }


def prix_achat_pour_utilisateur(ressource, utilisateur_id) -> int:
    return prix_derives_pour_utilisateur(ressource, utilisateur_id)["prix_achat"]


def prix_modifie_pour_utilisateur(ressource, utilisateur_id) -> int:
    return prix_derives_pour_utilisateur(ressource, utilisateur_id)["prix_modifie"]


def prix_lointain_pour_utilisateur(ressource, utilisateur_id) -> int:
    return prix_derives_pour_utilisateur(ressource, utilisateur_id)["prix_lointain"]
