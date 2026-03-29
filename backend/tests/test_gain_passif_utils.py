"""Tests unitaires des calculs de gains passifs (fixe / pourcentage)."""

from types import SimpleNamespace

from app.utils.gain_passif import (
    delta_ligne,
    net_un_tour,
    normaliser_balise,
    normaliser_mode,
    simuler_trois_tours,
)


def test_normaliser_balise_et_mode():
    assert normaliser_balise("science") == "science"
    assert normaliser_balise("INCONNU") == "autre"
    assert normaliser_mode("pourcentage") == "pourcentage"
    assert normaliser_mode(None) == "fixe"


def test_delta_ligne_fixe():
    g = SimpleNamespace(quantite_par_tour=7, mode_production="fixe")
    assert delta_ligne(1000, g) == 7


def test_delta_ligne_pourcentage():
    g = SimpleNamespace(quantite_par_tour=-25, mode_production="pourcentage")
    assert delta_ligne(100, g) == -25


def test_net_un_tour_tri_par_id():
    """L’ordre d’application est l’id, pas l’ordre dans la liste."""
    g2 = SimpleNamespace(
        id=2, actif=True, quantite_par_tour=-50, mode_production="pourcentage", tours_restants=None
    )
    g1 = SimpleNamespace(
        id=1, actif=True, quantite_par_tour=10, mode_production="fixe", tours_restants=None
    )
    # stock 100 : +10 -> 110 ; puis -50 % de 110 = -55 ; total = -45
    assert net_un_tour([g2, g1], 100) == -45


def test_simuler_trois_tours_regle_temporaire():
    g = SimpleNamespace(
        id=1,
        quantite_par_tour=5,
        actif=True,
        tours_restants=1,
        mode_production="fixe",
    )
    out = simuler_trois_tours([g], 0)
    assert out == [5, 0, 0]


def test_simuler_trois_tours_pourcentage_sur_stock_cumule():
    g = SimpleNamespace(
        id=1,
        quantite_par_tour=10,
        actif=True,
        tours_restants=None,
        mode_production="pourcentage",
    )
    out = simuler_trois_tours([g], 100)
    # tour1: +10% de 100 = +10, stock 110
    # tour2: +10% de 110 = +11, stock 121
    # tour3: +10% de 121 = +12
    assert out[0] == 10
    assert out[1] == 11
    assert out[2] == 12
