"""Migrations légères SQLite (sans Alembic)."""

from sqlalchemy import inspect, text

from .extensions import db
from .models import Categorie, Ressource
from .utils.prix import recalcule_prix_ressource


def run_schema_updates():
    """Crée les nouvelles tables si besoin."""
    db.create_all()


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
