"""Calcul des effets des gains passifs (quantité fixe ou % de la production du tour)."""

BALISES_VALIDES = frozenset({"science", "politique", "evenement", "batiment", "autre"})
MODES_VALIDES = frozenset({"fixe", "pourcentage"})

# Libellés UI (utilisés pour construire les options sur le front).
BALISE_LABELS = {
    "science": "Science",
    "politique": "Politique",
    "evenement": "Événement",
    "batiment": "Bâtiment",
    "autre": "Autre",
}


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


def delta_ligne(production_avant: int, gain) -> int:
    """Effet d’une règle sur la production du tour, selon la production *avant* cette ligne (ordre par id)."""
    mode = normaliser_mode(getattr(gain, "mode_production", None))
    if mode == "pourcentage":
        return int(production_avant * int(gain.quantite_par_tour) / 100)
    return int(gain.quantite_par_tour)


def net_un_tour(gains, stock_initial: int) -> int:
    """
    Variation nette de stock sur un tour pour une ressource donnée
    (toutes les règles actives de ce joueur pour cette ressource, tri id).
    """
    return net_un_tour_breakdown(gains, stock_initial)["total"]


def net_un_tour_breakdown(gains, stock_initial: int) -> dict:
    """
    Breakdown sur 1 tour : contributions dues à des règles
    - déjà actives "maintenant" (dl<=0 à t=0 dans l'horizon)
    - qui vont s'activer (dl>0 au t=0, puis dl décrémenté à 0 avant l'application)
    """

    cur = stock_initial
    prod = 0
    total_actif = 0
    total_pending = 0

    def _dl(g) -> int:
        v = getattr(g, "delai_tours", 0) or 0
        try:
            return int(v)
        except Exception:
            return 0

    # pending_init = (dl>0 au début de l'horizon)
    candidats = []
    for g in gains:
        if not getattr(g, "actif", False):
            continue
        dl = _dl(g)
        if dl <= 0:
            candidats.append((int(g.id), bool(dl > 0), g))

    for _, pending_init, g in sorted(candidats, key=lambda x: x[0]):
        d = delta_ligne(prod, g)
        cur += d
        prod += d
        if pending_init:
            total_pending += d
        else:
            total_actif += d

    return {"total": total_actif + total_pending, "actif": total_actif, "pending": total_pending}


def _state_from_gains(gains):
    return [
        {
            "id": g.id,
            "q": int(g.quantite_par_tour),
            "actif": bool(g.actif),
            "tr": g.tours_restants,
            "dl": int(getattr(g, "delai_tours", 0) or 0),
            "pending_init": int(getattr(g, "delai_tours", 0) or 0) > 0,
            "mode": normaliser_mode(getattr(g, "mode_production", None)),
        }
        for g in gains
    ]


def simuler_trois_tours(gains, stock_initial: int):
    """
    Liste de 3 entiers : variation de stock pour chacun des 3 prochains tours
    (règles temporaires avancées entre les tours, stock cumulé).
    """
    breakdown = simuler_trois_tours_breakdown(gains, stock_initial)
    return [x["total"] for x in breakdown]


def simuler_trois_tours_breakdown(gains, stock_initial: int):
    """
    Breakdown sur 3 tours :
    - actif : contributions des règles avec dl<=0 au début de l'horizon
    - pending : contributions des règles qui avaient dl>0 au début de l'horizon
      (et qui deviennent effectives pendant l'horizon)
    """
    state = _state_from_gains(gains)
    out = []
    cur_stock = stock_initial

    for _ in range(3):
        active = [x for x in state if x["actif"] and int(x.get("dl") or 0) <= 0]
        active.sort(key=lambda x: x["id"])
        tour_actif = 0
        tour_pending = 0
        prod = 0

        for x in active:
            if x["mode"] == "pourcentage":
                d = int(prod * x["q"] / 100)
            else:
                d = x["q"]
            cur_stock += d
            prod += d
            if x.get("pending_init"):
                tour_pending += d
            else:
                tour_actif += d

        out.append({"actif": tour_actif, "pending": tour_pending, "total": tour_actif + tour_pending})

        new_state = []
        for x in state:
            if not x["actif"]:
                new_state.append(x)
                continue
            nx = dict(x)
            if int(nx.get("dl") or 0) > 0:
                nx["dl"] = int(nx["dl"]) - 1
            elif nx["tr"] is not None:
                nx["tr"] = int(nx["tr"]) - 1
                if nx["tr"] <= 0:
                    nx["actif"] = False
            new_state.append(nx)

        state = new_state

    return out
