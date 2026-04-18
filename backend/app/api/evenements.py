"""Routes HTTP pour les évènements MJ — logique métier dans services.evenement_service."""

from __future__ import annotations

import json

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Evenement, EvenementJoueur, GainPassif, Utilisateur
from ..services.evenement_service import (
    appliquer_effets_materiels,
    apercu_impacts_pour_joueur,
    marquer_deja_publie_si_non_brouillon,
    preview_evenement_impacts,
    resume_lignes_depuis_apercu,
    supprimer_gains_passifs_evenement,
    sync_evenement_champs,
    sync_impacts,
    validate_cible,
)
from ..utils.decorators import get_current_user, login_required, mj_required

evenements_bp = Blueprint("evenements", __name__)


@evenements_bp.get("/api/evenements")
@login_required
def list_evenements():
    me = get_current_user()
    q_actifs = request.args.get("actifs")
    query = Evenement.query
    if q_actifs == "1":
        query = query.filter(Evenement.actif.is_(True), Evenement.brouillon.is_(False))
        # Tout le monde (y compris MJ) : uniquement les évènements où le joueur a une ligne active.
        ej_ids = [
            row[0]
            for row in db.session.query(EvenementJoueur.evenement_id)
            .filter_by(utilisateur_id=me.id, actif=True)
            .distinct()
            .all()
        ]
        if not ej_ids:
            query = query.filter(Evenement.id == -1)
        else:
            query = query.filter(Evenement.id.in_(ej_ids))

    rows = query.order_by(Evenement.updated_at.desc(), Evenement.id.desc()).all()
    return jsonify({"ok": True, "is_mj": bool(me.is_mj), "evenements": [e.to_dict() for e in rows]})


@evenements_bp.get("/api/evenements/<int:evenement_id>")
@login_required
def get_evenement(evenement_id: int):
    """Détail d’un évènement : MJ (tout) ou joueur avec ligne evenement_joueur active."""
    me = get_current_user()
    e = db.get_or_404(Evenement, evenement_id)
    if me.is_mj:
        return jsonify(e.to_dict())
    ej = EvenementJoueur.query.filter_by(
        evenement_id=e.id, utilisateur_id=me.id, actif=True
    ).first()
    if not ej:
        return jsonify({"error": "Accès refusé"}), 403
    return jsonify(e.to_dict())


@evenements_bp.get("/api/evenements/<int:evenement_id>/apercu-joueur")
@login_required
def apercu_joueur_evenement(evenement_id: int):
    """Avant / après (prix %, productions / tour) pour le joueur connecté — même règles que l’aperçu MJ."""
    me = get_current_user()
    if me.is_mj:
        return jsonify({"error": "Utilisez l’aperçu depuis le formulaire MJ."}), 403
    e = db.get_or_404(Evenement, evenement_id)
    ej = EvenementJoueur.query.filter_by(
        evenement_id=e.id, utilisateur_id=me.id, actif=True
    ).first()
    if not ej:
        return jsonify({"error": "Accès refusé"}), 403
    try:
        raw = apercu_impacts_pour_joueur(e.id, me.id)
        return jsonify(
            {
                "ok": True,
                "blocs": raw.get("blocs") or [],
                "resume": resume_lignes_depuis_apercu(raw),
                "message": raw.get("message"),
            }
        )
    except ValueError as ex:
        return jsonify({"error": str(ex)}), 400


@evenements_bp.post("/api/evenements/preview-impacts")
@mj_required
def preview_impacts_route():
    """Aperçu MJ : avant → après par joueur pour chaque ligne d’impact (sans enregistrer)."""
    data = request.get_json() or {}
    try:
        out = preview_evenement_impacts(data)
        return jsonify(out)
    except ValueError as ex:
        return jsonify({"error": str(ex)}), 400


@evenements_bp.post("/api/evenements")
@mj_required
def create_evenement():
    data = request.get_json() or {}
    titre = str(data.get("titre") or "").strip()
    if not titre:
        return jsonify({"error": "Champ 'titre' requis"}), 400
    desc = str(data.get("description") or "")
    actif = bool(data.get("actif", True))
    brouillon = bool(data.get("brouillon", True))

    cible = validate_cible(data.get("cible", "aucun"))
    uids = data.get("cible_utilisateur_ids") or []
    if not isinstance(uids, list):
        return jsonify({"error": "cible_utilisateur_ids doit être une liste"}), 400
    for uid in uids:
        if not db.session.get(Utilisateur, str(uid)):
            return jsonify({"error": f"Joueur inconnu : {uid}"}), 400

    dt = int(data.get("delai_tours", 0) or 0)
    if dt < 0 or dt > 1000:
        return jsonify({"error": "delai_tours doit être entre 0 et 1000"}), 400
    tr_raw = data.get("tours_restants")
    if tr_raw is None:
        tr = None
    else:
        tr = int(tr_raw)
        if tr <= 0:
            return jsonify({"error": "tours_restants doit être > 0 ou null (illimité)"}), 400

    e = Evenement(
        titre=titre,
        description=desc,
        actif=actif,
        brouillon=brouillon,
        cible=cible,
        cible_utilisateur_ids=json.dumps([str(x) for x in uids if x is not None]),
        delai_tours=dt,
        tours_restants=tr,
    )

    db.session.add(e)
    db.session.flush()
    try:
        sync_evenement_champs(e, data)
        sync_impacts(e, data)
        appliquer_effets_materiels(e)
        marquer_deja_publie_si_non_brouillon(e)
    except ValueError as ex:
        db.session.rollback()
        return jsonify({"error": str(ex)}), 400

    db.session.commit()
    return jsonify(e.to_dict()), 201


@evenements_bp.put("/api/evenements/<int:evenement_id>")
@mj_required
def update_evenement(evenement_id: int):
    e = db.get_or_404(Evenement, evenement_id)
    data = request.get_json() or {}

    if "titre" in data:
        titre = str(data.get("titre") or "").strip()
        if not titre:
            return jsonify({"error": "titre ne peut pas être vide"}), 400
        e.titre = titre
    if "description" in data:
        e.description = str(data.get("description") or "")
    if "actif" in data:
        e.actif = bool(data.get("actif"))

    try:
        sync_evenement_champs(e, data)
        if "impacts" in data:
            sync_impacts(e, data)
        appliquer_effets_materiels(e)
        marquer_deja_publie_si_non_brouillon(e)
    except ValueError as ex:
        db.session.rollback()
        return jsonify({"error": str(ex)}), 400

    db.session.commit()
    return jsonify(e.to_dict())


@evenements_bp.put("/api/evenements/<int:evenement_id>/joueurs/<user_id>")
@mj_required
def set_evenement_joueur_actif(evenement_id: int, user_id: str):
    e = db.get_or_404(Evenement, evenement_id)
    ej = EvenementJoueur.query.filter_by(evenement_id=e.id, utilisateur_id=str(user_id)).first()
    if not ej:
        return jsonify({"error": "Ligne joueur introuvable pour cet évènement"}), 404
    data = request.get_json() or {}
    if "actif" in data:
        ej.actif = bool(data.get("actif"))
        if not ej.actif:
            supprimer_gains_passifs_evenement(e.id, utilisateur_id=str(user_id))
    db.session.commit()
    return jsonify({"ok": True, "joueur": ej.to_dict()})


@evenements_bp.delete("/api/evenements/<int:evenement_id>")
@mj_required
def delete_evenement(evenement_id: int):
    e = db.get_or_404(Evenement, evenement_id)
    EvenementJoueur.query.filter_by(evenement_id=e.id).delete()
    supprimer_gains_passifs_evenement(e.id)
    db.session.delete(e)
    db.session.commit()
    return jsonify({"ok": True})
