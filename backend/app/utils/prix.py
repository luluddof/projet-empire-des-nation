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
