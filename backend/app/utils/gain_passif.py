"""Calcul des effets des gains passifs (quantité fixe ou % du stock courant)."""

BALISES_VALIDES = frozenset({"science", "politique", "evenement", "autre"})
MODES_VALIDES = frozenset({"fixe", "pourcentage"})


def normaliser_balise(v):
    if v is None:
        return "autre"
    s = str(v).strip().lower()
    return s if s in BALISES_VALIDES else "autre"


def normaliser_mode(v):
    if v is None:
        return "fixe"
    s = str(v).strip().lower()
    return s if s in MODES_VALIDES else "fixe"


def delta_ligne(stock_avant: int, gain) -> int:
    """Effet d’une règle sur le stock, selon le stock *avant* cette ligne (ordre par id)."""
    mode = normaliser_mode(getattr(gain, "mode_production", None))
    if mode == "pourcentage":
        return int(stock_avant * int(gain.quantite_par_tour) / 100)
    return int(gain.quantite_par_tour)


def net_un_tour(gains, stock_initial: int) -> int:
    """
    Variation nette de stock sur un tour pour une ressource donnée
    (toutes les règles actives de ce joueur pour cette ressource, tri id).
    """
    cur = stock_initial
    total = 0
    for g in sorted((x for x in gains if x.actif), key=lambda x: x.id):
        d = delta_ligne(cur, g)
        cur += d
        total += d
    return total


def _state_from_gains(gains):
    return [
        {
            "id": g.id,
            "q": int(g.quantite_par_tour),
            "actif": bool(g.actif),
            "tr": g.tours_restants,
            "mode": normaliser_mode(getattr(g, "mode_production", None)),
        }
        for g in gains
    ]


def simuler_trois_tours(gains, stock_initial: int):
    """
    Liste de 3 entiers : variation de stock pour chacun des 3 prochains tours
    (règles temporaires avancées entre les tours, stock cumulé).
    """
    state = _state_from_gains(gains)
    out = []
    cur_stock = stock_initial
    for _ in range(3):
        active = [x for x in state if x["actif"]]
        active.sort(key=lambda x: x["id"])
        tour_delta = 0
        for x in active:
            if x["mode"] == "pourcentage":
                d = int(cur_stock * x["q"] / 100)
            else:
                d = x["q"]
            cur_stock += d
            tour_delta += d
        out.append(tour_delta)
        new_state = []
        for x in state:
            if not x["actif"]:
                new_state.append(x)
                continue
            nx = dict(x)
            if nx["tr"] is not None:
                nx["tr"] = int(nx["tr"]) - 1
                if nx["tr"] <= 0:
                    nx["actif"] = False
            new_state.append(nx)
        state = new_state
    return out
