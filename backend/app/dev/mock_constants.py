"""
Données statiques du mock dev (comptes, stocks, gains).
Ne change que si on modifie le scénario de démo.
"""

# IDs « neige » (format Discord) — éviter collision avec de vrais comptes
MOCK_IDS = {
    "alice": "900000000000000001",
    "bob": "900000000000000002",
    "charlie": "900000000000000003",
    "diana": "900000000000000004",
    "mj_dev": "900000000000000005",
}

# (username, discord_id, is_mj)
MOCK_USERS: list[tuple[str, str, bool]] = [
    ("[dev] Alice", MOCK_IDS["alice"], False),
    ("[dev] Bob", MOCK_IDS["bob"], False),
    ("[dev] Charlie", MOCK_IDS["charlie"], False),
    ("[dev] Diana", MOCK_IDS["diana"], False),
    ("[dev] MJ secondaire", MOCK_IDS["mj_dev"], True),
]

# par utilisateur_id : liste (nom_ressource, quantite, balise)
MOCK_GAINS: dict[str, list[tuple[str, int, str]]] = {
    MOCK_IDS["alice"]: [
        ("Bois", 35, "science"),
        ("Bétail", 12, "autre"),
    ],
    MOCK_IDS["bob"]: [
        ("Charbon", 28, "politique"),
        ("Acier", 8, "science"),
    ],
    MOCK_IDS["charlie"]: [
        ("Coton", 20, "evenement"),
        ("Argent", 3, "autre"),
    ],
    MOCK_IDS["diana"]: [
        ("Alcools", 15, "politique"),
        ("Bois", 10, "autre"),
    ],
    MOCK_IDS["mj_dev"]: [
        ("Acier", 25, "science"),
        ("Bronze", 6, "politique"),
    ],
}

# par utilisateur_id : liste (nom_ressource, quantite)
MOCK_STOCKS: dict[str, list[tuple[str, int]]] = {
    MOCK_IDS["alice"]: [("Florins", 8_000_000), ("Bois", 1400), ("Bétail", 200)],
    MOCK_IDS["bob"]: [("Florins", 5_500_000), ("Charbon", 900), ("Acier", 120)],
    MOCK_IDS["charlie"]: [("Florins", 6_200_000), ("Coton", 350), ("Argent", 45)],
    MOCK_IDS["diana"]: [("Florins", 4_000_000), ("Alcools", 180), ("Bois", 600)],
    MOCK_IDS["mj_dev"]: [("Florins", 12_000_000), ("Acier", 400), ("Bronze", 90)],
}
