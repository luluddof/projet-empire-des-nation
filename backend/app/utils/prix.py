"""Règles de prix (florins). Modificateurs en % (100 = neutre).

Multiplicateur effectif = (pct_ressource / 100) × ∏(pct_catégorie / 100).

Prix modifié = arrondi(base × M_eff) ; achat = modifié × 1,2 ; lointain = modifié × 2,5.
"""


def _facteur_depuis_pct(pct) -> float:
    v = float(pct) if pct is not None else 100.0
    if v <= 0:
        return 1.0
    return v / 100.0


def multiplicateur_effectif(r) -> float:
    f = _facteur_depuis_pct(getattr(r, "modificateur_pct", 100))
    for c in r.categories_rel:
        f *= _facteur_depuis_pct(getattr(c, "modificateur_pct", 100))
    return f


def modificateur_pct_categorie_effectif(categorie, utilisateur_id) -> float:
    """
    % catégorie effectif pour un joueur (surcharge éventuelle).

    - sinon retourne le % catalogue global de la catégorie.
    """
    from ..models.categorie_modificateur_joueur import CategorieModificateurJoueur

    if utilisateur_id is None:
        return float(getattr(categorie, "modificateur_pct", 100.0))

    row = CategorieModificateurJoueur.query.filter_by(
        utilisateur_id=utilisateur_id, categorie_id=categorie.id
    ).first()
    if row is not None:
        return float(row.modificateur_pct)
    return float(getattr(categorie, "modificateur_pct", 100.0))


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

    row = RessourceModificateurJoueur.query.filter_by(
        utilisateur_id=utilisateur_id, ressource_id=ressource.id
    ).first()
    if row is not None:
        return float(row.modificateur_pct)
    return float(getattr(ressource, "modificateur_pct", 100.0))


def multiplicateur_effectif_pour_utilisateur(ressource, utilisateur_id) -> float:
    f = _facteur_depuis_pct(modificateur_pct_effectif(ressource, utilisateur_id))
    for c in ressource.categories_rel:
        f *= _facteur_depuis_pct(modificateur_pct_categorie_effectif(c, utilisateur_id))
    return f


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
