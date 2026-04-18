"""Migrations légères SQLite (sans Alembic)."""

from sqlalchemy import inspect, text

from .extensions import db
from .models import Categorie, Ressource
from .utils.prix import recalcule_prix_ressource
from .utils.prix_snapshot import enregistrer_snapshot_prix


def run_schema_updates():
    """Crée les nouvelles tables si besoin."""
    from . import models as _models  # noqa: F401 — enregistre tous les modèles pour create_all

    db.create_all()


def migrate_gain_passif_multi():
    """
    Ancienne table : unique (utilisateur, ressource) + une colonne de quantité par tour (schéma d’origine).
    Nouvelle : plusieurs lignes par couple, quantite_par_tour, tours_restants (NULL = définitif).
    """
    insp = inspect(db.engine)
    if "gain_passif" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("gain_passif")}
    if "quantite_par_tour" in cols:
        return

    db.session.execute(
        text(
            """
            CREATE TABLE gain_passif_new (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                utilisateur_id VARCHAR(20) NOT NULL,
                ressource_id INTEGER NOT NULL,
                quantite_par_tour INTEGER NOT NULL,
                actif BOOLEAN NOT NULL,
                tours_restants INTEGER,
                FOREIGN KEY(utilisateur_id) REFERENCES utilisateur (id),
                FOREIGN KEY(ressource_id) REFERENCES ressource (id)
            )
            """
        )
    )
    db.session.execute(
        text(
            """
            INSERT INTO gain_passif_new
                (id, utilisateur_id, ressource_id, quantite_par_tour, actif, tours_restants)
            SELECT id, utilisateur_id, ressource_id, quantite_par_tick, actif, NULL
            FROM gain_passif
            """
        )
    )
    db.session.execute(text("DROP TABLE gain_passif"))
    db.session.execute(text("ALTER TABLE gain_passif_new RENAME TO gain_passif"))
    db.session.commit()


def migrate_gain_passif_balise_mode():
    """Ajoute balise (justification) et mode_production (fixe | pourcentage)."""
    insp = inspect(db.engine)
    if "gain_passif" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("gain_passif")}
    if "balise" not in cols:
        db.session.execute(
            text("ALTER TABLE gain_passif ADD COLUMN balise VARCHAR(20) NOT NULL DEFAULT 'autre'")
        )
    if "mode_production" not in cols:
        db.session.execute(
            text(
                "ALTER TABLE gain_passif ADD COLUMN mode_production VARCHAR(20) NOT NULL DEFAULT 'fixe'"
            )
        )
    db.session.commit()


def migrate_gain_passif_delai_tours():
    """Ajoute delai_tours (nombre de tours avant démarrage effectif)."""
    insp = inspect(db.engine)
    if "gain_passif" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("gain_passif")}
    if "delai_tours" not in cols:
        db.session.execute(
            text(
                "ALTER TABLE gain_passif ADD COLUMN delai_tours INTEGER NOT NULL DEFAULT 0"
            )
        )
        db.session.commit()


def migrate_gain_passif_evenement_id():
    """Ajoute evenement_id sur gain_passif (lignes créées par les évènements)."""
    insp = inspect(db.engine)
    if "gain_passif" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("gain_passif")}
    if "evenement_id" not in cols:
        db.session.execute(
            text("ALTER TABLE gain_passif ADD COLUMN evenement_id INTEGER")
        )
        db.session.commit()


def seed_prix_historique_si_vide():
    """Un point initial par ressource si l’historique est vide (graphiques utilisables)."""
    from .models import PrixRessourceHistorique

    insp = inspect(db.engine)
    if "prix_ressource_historique" not in insp.get_table_names():
        return
    if PrixRessourceHistorique.query.count() > 0:
        return
    for r in Ressource.query.all():
        enregistrer_snapshot_prix(r)
    db.session.commit()


def migrate_modificateur_to_percent():
    """
    Ancienne colonne modificateur (multiplicateur) -> modificateur_pct (%).
    1.0 -> 100 %, 1.2 -> 120 %, etc.
    """
    insp = inspect(db.engine)
    for table in ("categorie", "ressource"):
        if table not in insp.get_table_names():
            continue
        cols = {c["name"] for c in insp.get_columns(table)}
        if "modificateur_pct" not in cols:
            db.session.execute(
                text(f"ALTER TABLE {table} ADD COLUMN modificateur_pct REAL DEFAULT 100")
            )
            db.session.commit()
            cols = {c["name"] for c in inspect(db.engine).get_columns(table)}
        if "modificateur" in cols:
            db.session.execute(
                text(
                    f"UPDATE {table} SET modificateur_pct = CASE "
                    f"WHEN modificateur IS NULL OR modificateur <= 0 THEN 100 "
                    f"ELSE modificateur * 100 END"
                )
            )
            db.session.commit()
            try:
                db.session.execute(text(f"ALTER TABLE {table} DROP COLUMN modificateur"))
                db.session.commit()
            except Exception:
                db.session.rollback()


def migrate_legacy_categories_string():
    """
    Ancienne colonne ressource.categories (texte) -> table categorie + liaison.
    Idempotent : ignore les lignes déjà liées.
    """
    insp = inspect(db.engine)
    if "ressource" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("ressource")}
    if "categories" not in cols:
        for r in Ressource.query.all():
            recalcule_prix_ressource(r)
        db.session.commit()
        return

    rows = db.session.execute(
        text(
            "SELECT id, categories FROM ressource "
            "WHERE categories IS NOT NULL AND TRIM(categories) != ''"
        )
    ).fetchall()

    for rid, cat_str in rows:
        r = db.session.get(Ressource, rid)
        if not r or r.categories_rel:
            continue
        if not cat_str:
            continue
        for part in str(cat_str).split(";"):
            nom = part.strip()
            if not nom:
                continue
            c = Categorie.query.filter_by(nom=nom).first()
            if c is None:
                c = Categorie(nom=nom, modificateur_pct=100.0)
                db.session.add(c)
                db.session.flush()
            if c not in r.categories_rel:
                r.categories_rel.append(c)

    db.session.commit()

    for r in Ressource.query.all():
        recalcule_prix_ressource(r)
    db.session.commit()

    try:
        db.session.execute(text("ALTER TABLE ressource DROP COLUMN categories"))
        db.session.commit()
    except Exception:
        db.session.rollback()


def migrate_evenements_schema():
    """
    Colonnes évènements v2 (brouillon, cible, délais) + seed evenement_joueur.
    `run_schema_updates()` crée les tables ; ici ALTER pour bases existantes.
    """
    from .models import Evenement, EvenementJoueur, Utilisateur

    insp = inspect(db.engine)
    if "evenement" not in insp.get_table_names():
        return

    cols = {c["name"] for c in insp.get_columns("evenement")}
    added_brouillon = False
    if "brouillon" not in cols:
        db.session.execute(text("ALTER TABLE evenement ADD COLUMN brouillon BOOLEAN NOT NULL DEFAULT 1"))
        db.session.commit()
        added_brouillon = True
        cols = {c["name"] for c in inspect(db.engine).get_columns("evenement")}
    if "cible" not in cols:
        db.session.execute(text("ALTER TABLE evenement ADD COLUMN cible VARCHAR(20) NOT NULL DEFAULT 'aucun'"))
        db.session.commit()
        cols = {c["name"] for c in inspect(db.engine).get_columns("evenement")}
    if "cible_utilisateur_ids" not in cols:
        db.session.execute(text("ALTER TABLE evenement ADD COLUMN cible_utilisateur_ids TEXT NOT NULL DEFAULT '[]'"))
        db.session.commit()
        cols = {c["name"] for c in inspect(db.engine).get_columns("evenement")}
    if "delai_tours" not in cols:
        db.session.execute(text("ALTER TABLE evenement ADD COLUMN delai_tours INTEGER NOT NULL DEFAULT 0"))
        db.session.commit()
        cols = {c["name"] for c in inspect(db.engine).get_columns("evenement")}
    if "tours_restants" not in cols:
        db.session.execute(text("ALTER TABLE evenement ADD COLUMN tours_restants INTEGER"))
        db.session.commit()

    cols = {c["name"] for c in inspect(db.engine).get_columns("evenement")}
    if "deja_publie" not in cols:
        db.session.execute(text("ALTER TABLE evenement ADD COLUMN deja_publie BOOLEAN NOT NULL DEFAULT 0"))
        db.session.commit()
        try:
            db.session.execute(
                text(
                    "UPDATE evenement SET deja_publie = 1 "
                    "WHERE brouillon = 0 OR id IN (SELECT DISTINCT evenement_id FROM evenement_joueur)"
                )
            )
            db.session.commit()
        except Exception:
            db.session.rollback()

    if added_brouillon:
        try:
            db.session.execute(text("UPDATE evenement SET brouillon = 0, cible = 'tous' WHERE actif = 1"))
            db.session.execute(text("UPDATE evenement SET cible = 'aucun' WHERE actif = 0"))
            db.session.commit()
        except Exception:
            db.session.rollback()

    insp2 = inspect(db.engine)
    if "evenement_joueur" not in insp2.get_table_names():
        return

    for e in Evenement.query.filter(Evenement.actif.is_(True), Evenement.brouillon.is_(False)).all():
        if EvenementJoueur.query.filter_by(evenement_id=e.id).count() > 0:
            continue
        d = int(getattr(e, "delai_tours", 0) or 0)
        tr = getattr(e, "tours_restants", None)
        for u in Utilisateur.query.filter_by(is_mj=False).all():
            db.session.add(
                EvenementJoueur(
                    evenement_id=e.id,
                    utilisateur_id=u.id,
                    delai_tours=d,
                    tours_restants=tr,
                    actif=True,
                )
            )
        db.session.commit()
