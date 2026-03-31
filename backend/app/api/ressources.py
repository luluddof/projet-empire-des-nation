from typing import Optional, Tuple

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Categorie, PrixRessourceHistorique, Ressource, RessourceModificateurJoueur, Utilisateur
from ..utils.prix import (
    appliquer_produit_categories_sur_ressource,
    prix_derives_pour_utilisateur,
    recalcule_prix_ressource,
)
from ..utils.prix_snapshot import enregistrer_snapshot_prix
from ..utils.decorators import get_current_user, login_required, mj_required

ressources_bp = Blueprint("ressources", __name__)


def _upsert_override(utilisateur_id: str, ressource_id: int, pct: float) -> None:
    row = RessourceModificateurJoueur.query.filter_by(
        utilisateur_id=utilisateur_id, ressource_id=ressource_id
    ).first()
    if row:
        row.modificateur_pct = float(pct)
    else:
        db.session.add(
            RessourceModificateurJoueur(
                utilisateur_id=utilisateur_id,
                ressource_id=ressource_id,
                modificateur_pct=float(pct),
            )
        )


def _apply_modificateur_cible(
    me,
    pct: float,
    ressource_ids: list,
    cible: str,
    utilisateur_ids: list,
    operation: str = "set",
) -> Tuple[bool, Optional[str]]:
    """
    cible: tous | moi | joueurs
    - tous : met à jour le catalogue global et supprime les surcharges pour ces ressources.
    - moi / joueurs : surcharges par joueur sans changer le % catalogue global.
    """
    cible = (cible or "tous").strip().lower()
    operation = (operation or "set").strip().lower()
    if operation not in ("set", "add", "remove"):
        return False, "operation invalide (set, add, remove)"
    if operation in ("add", "remove") and pct <= 0:
        return False, "Pour add/remove, modificateur_pct (delta) doit être > 0"
    ids = [int(x) for x in ressource_ids if x is not None]

    if cible == "tous":
        for rid in ids:
            r = db.session.get(Ressource, rid)
            if not r:
                continue
            if operation == "set":
                new_val = float(pct)
            elif operation == "add":
                new_val = float(r.modificateur_pct) + float(pct)
            else:  # remove
                new_val = float(r.modificateur_pct) - float(pct)
            if new_val <= 0:
                return False, "Résultat invalide : modificateur_pct doit rester > 0"
            r.modificateur_pct = new_val
            recalcule_prix_ressource(r)
            enregistrer_snapshot_prix(r)
            RessourceModificateurJoueur.query.filter_by(ressource_id=rid).delete()
        return True, None

    if cible == "moi":
        for rid in ids:
            if not db.session.get(Ressource, rid):
                continue
            r = db.session.get(Ressource, rid)
            row = RessourceModificateurJoueur.query.filter_by(
                utilisateur_id=me.id, ressource_id=rid
            ).first()
            base = float(row.modificateur_pct) if row is not None else float(r.modificateur_pct)

            if operation == "set":
                new_val = float(pct)
            elif operation == "add":
                new_val = base + float(pct)
            else:  # remove
                new_val = base - float(pct)

            if new_val <= 0:
                return False, "Résultat invalide : modificateur_pct doit rester > 0"

            # Si le nouvel état retombe exactement sur la valeur catalogue, on retire la surcharge.
            if abs(new_val - float(r.modificateur_pct)) < 1e-9 and row is not None:
                db.session.delete(row)
            else:
                _upsert_override(me.id, rid, new_val)
        return True, None

    if cible == "joueurs":
        uids = [str(u) for u in (utilisateur_ids or []) if u is not None]
        if not uids:
            return False, "utilisateur_ids requis pour cible « joueurs »"
        for uid in uids:
            if not db.session.get(Utilisateur, uid):
                return False, f"Joueur inconnu ou sans compte lié : {uid}"
        for rid in ids:
            if not db.session.get(Ressource, rid):
                continue
            r = db.session.get(Ressource, rid)
            for uid in uids:
                row = RessourceModificateurJoueur.query.filter_by(
                    utilisateur_id=uid, ressource_id=rid
                ).first()
                base = float(row.modificateur_pct) if row is not None else float(r.modificateur_pct)

                if operation == "set":
                    new_val = float(pct)
                elif operation == "add":
                    new_val = base + float(pct)
                else:  # remove
                    new_val = base - float(pct)

                if new_val <= 0:
                    return False, "Résultat invalide : modificateur_pct doit rester > 0"

                # Si le nouvel état retombe exactement sur la valeur catalogue, on retire la surcharge.
                if abs(new_val - float(r.modificateur_pct)) < 1e-9 and row is not None:
                    db.session.delete(row)
                else:
                    _upsert_override(uid, rid, new_val)
        return True, None

    return False, "cible_modificateur invalide (tous, moi, joueurs)"


def _assign_categories(r: Ressource, categorie_ids):
    if categorie_ids is None:
        return
    ids = [int(x) for x in categorie_ids]
    cats = Categorie.query.filter(Categorie.id.in_(ids)).all()
    if len(cats) != len(ids):
        return False, "Une ou plusieurs catégories sont introuvables"
    r.categories_rel.clear()
    for c in cats:
        r.categories_rel.append(c)
    return True, None


@ressources_bp.get("/api/ressources")
@login_required
def list_ressources():
    me = get_current_user()
    ressources = Ressource.query.order_by(Ressource.nom).all()
    if me.is_mj:
        as_uid = request.args.get("as_user_id")
        if as_uid is not None and str(as_uid).strip() != "":
            as_uid = str(as_uid).strip()
            if not db.session.get(Utilisateur, as_uid):
                return jsonify({"error": f"Joueur inconnu : {as_uid}"}), 400
            return jsonify([r.to_dict(utilisateur_id=as_uid) for r in ressources])
        if request.args.get("global") == "1":
            return jsonify([r.to_dict() for r in ressources])
    return jsonify([r.to_dict(utilisateur_id=me.id) for r in ressources])


@ressources_bp.get("/api/ressources/<int:ressource_id>")
@login_required
def get_ressource(ressource_id):
    me = get_current_user()
    r = db.get_or_404(Ressource, ressource_id)
    if me.is_mj:
        as_uid = request.args.get("as_user_id")
        if as_uid is not None and str(as_uid).strip() != "":
            as_uid = str(as_uid).strip()
            if not db.session.get(Utilisateur, as_uid):
                return jsonify({"error": f"Joueur inconnu : {as_uid}"}), 400
            return jsonify(r.to_dict(utilisateur_id=as_uid))
        if request.args.get("global") == "1":
            return jsonify(r.to_dict())
    return jsonify(r.to_dict(utilisateur_id=me.id))


@ressources_bp.get("/api/ressources/<int:ressource_id>/modificateur-joueur")
@mj_required
def get_modificateur_ressource_joueur(ressource_id: int):
    r = db.get_or_404(Ressource, ressource_id)

    utilisateur_ids = request.args.getlist("utilisateur_ids")
    if not utilisateur_ids:
        uid = request.args.get("utilisateur_id")
        if uid:
            utilisateur_ids = [uid]

    utilisateur_ids = [
        str(x) for x in utilisateur_ids if x is not None and str(x).strip() != ""
    ]
    if not utilisateur_ids:
        return jsonify({"error": "utilisateur_id ou utilisateur_ids requis"}), 400

    for uid in utilisateur_ids:
        if not db.session.get(Utilisateur, uid):
            return jsonify({"error": f"Joueur inconnu : {uid}"}), 400

    valeurs = {}
    for uid in utilisateur_ids:
        derived = prix_derives_pour_utilisateur(r, uid)
        valeurs[uid] = {
            "modificateur_pct": float(derived["modificateur_pct"]),
            "facteur_prix": float(derived["facteur_prix"]),
            "prix_modifie": int(derived["prix_modifie"]),
            "prix_achat": int(derived["prix_achat"]),
            "prix_lointain": int(derived["prix_lointain"]),
        }

    return jsonify({"ok": True, "ressource_id": r.id, "valeurs": valeurs})


@ressources_bp.post("/api/ressources")
@mj_required
def create_ressource():
    data = request.get_json() or {}
    for k in ("nom", "type", "prix_base"):
        if k not in data:
            return jsonify({"error": f"Champ '{k}' requis"}), 400
    # Nouvelle ressource : % ressource = 100 % par défaut ; le prix intègre les % des catégories liées.
    pct_res = float(data.get("modificateur_pct", 100.0))
    r = Ressource(
        nom=str(data["nom"]).strip(),
        type=data["type"],
        prix_base=int(data["prix_base"]),
        modificateur_pct=pct_res,
        prix_modifie=0,
        prix_achat=0,
        prix_lointain=0,
    )
    db.session.add(r)
    db.session.flush()
    ok, err = _assign_categories(r, data.get("categorie_ids", []))
    if not ok:
        db.session.rollback()
        return jsonify({"error": err}), 400
    recalcule_prix_ressource(r)
    enregistrer_snapshot_prix(r)
    db.session.commit()
    return jsonify(r.to_dict()), 201


@ressources_bp.put("/api/ressources/<int:ressource_id>")
@mj_required
def update_ressource(ressource_id):
    r = db.get_or_404(Ressource, ressource_id)
    data = request.get_json() or {}
    me = get_current_user()

    if "nom" in data:
        r.nom = str(data["nom"]).strip()
    if "type" in data:
        r.type = data["type"]
    if "prix_base" in data:
        r.prix_base = int(data["prix_base"])
    if "categorie_ids" in data:
        ok, err = _assign_categories(r, data["categorie_ids"])
        if not ok:
            return jsonify({"error": err}), 400

    base_changed = "prix_base" in data or "categorie_ids" in data

    if "modificateur_pct" in data:
        pct = float(data["modificateur_pct"])
        cible = (data.get("cible_modificateur") or "tous").strip().lower()
        uids = data.get("utilisateur_ids") or []
        operation = data.get("operation") or "set"
        ok, err = _apply_modificateur_cible(me, pct, [r.id], cible, uids, operation=operation)
        if not ok:
            return jsonify({"error": err}), 400
        if cible != "tous" and base_changed:
            recalcule_prix_ressource(r)
            enregistrer_snapshot_prix(r)
    elif base_changed:
        recalcule_prix_ressource(r)
        enregistrer_snapshot_prix(r)

    db.session.commit()
    return jsonify(r.to_dict())


@ressources_bp.post("/api/ressources/bulk-prix-marche")
@mj_required
def bulk_prix_marche():
    """Applique le même % modificateur selon la cible (tous / moi / joueurs sélectionnés)."""
    data = request.get_json() or {}
    ids = data.get("ids")
    if not ids or not isinstance(ids, list):
        return jsonify({"error": "Champ 'ids' (liste d’entiers) requis"}), 400
    if "modificateur_pct" not in data:
        return jsonify({"error": "Champ 'modificateur_pct' requis"}), 400
    pct = float(data["modificateur_pct"])
    cible = (data.get("cible_modificateur") or "tous").strip().lower()
    operation = data.get("operation") or "set"
    uids = data.get("utilisateur_ids") or []
    me = get_current_user()

    rid_list = []
    for raw in ids:
        try:
            rid = int(raw)
        except (TypeError, ValueError):
            continue
        if db.session.get(Ressource, rid):
            rid_list.append(rid)

    if not rid_list:
        return jsonify({"error": "Aucune ressource valide"}), 400

    ok, err = _apply_modificateur_cible(
        me, pct, rid_list, cible, uids, operation=operation
    )
    if not ok:
        return jsonify({"error": err}), 400

    db.session.commit()
    return jsonify({"ok": True, "updated": rid_list, "count": len(rid_list), "cible_modificateur": cible})


@ressources_bp.get("/api/ressources/<int:ressource_id>/historique-prix")
@login_required
def historique_prix_ressource(ressource_id):
    db.get_or_404(Ressource, ressource_id)
    limit = min(200, max(1, int(request.args.get("limit", 80))))
    rows = (
        PrixRessourceHistorique.query.filter_by(ressource_id=ressource_id)
        .order_by(PrixRessourceHistorique.created_at.desc())
        .limit(limit)
        .all()
    )
    rows = list(reversed(rows))
    return jsonify([x.to_dict() for x in rows])


@ressources_bp.post("/api/ressources/<int:ressource_id>/appliquer-modificateurs-categories")
@mj_required
def appliquer_mods_categories(ressource_id):
    """Remet modificateur_pct de la ressource à 100 % (neutre)."""
    r = db.get_or_404(Ressource, ressource_id)
    appliquer_produit_categories_sur_ressource(r)
    enregistrer_snapshot_prix(r)
    db.session.commit()
    return jsonify(r.to_dict())


@ressources_bp.delete("/api/ressources/<int:ressource_id>")
@mj_required
def delete_ressource(ressource_id):
    r = db.get_or_404(Ressource, ressource_id)
    PrixRessourceHistorique.query.filter_by(ressource_id=ressource_id).delete()
    RessourceModificateurJoueur.query.filter_by(ressource_id=ressource_id).delete()
    db.session.delete(r)
    db.session.commit()
    return jsonify({"ok": True})
