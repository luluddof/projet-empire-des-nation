"""
Règles métier des évènements : validation, synchronisation des impacts,
matérialisation joueurs / gains passifs.

Ne dépend pas de Flask (hors db session) — une seule raison de changer : la logique évènement.
"""

from __future__ import annotations

import json

from ..extensions import db
from ..models import (
    Categorie,
    CategorieModificateurJoueur,
    Evenement,
    EvenementImpactCategorie,
    EvenementImpactProduction,
    EvenementImpactRessource,
    EvenementJoueur,
    GainPassif,
    Ressource,
    RessourceModificateurJoueur,
    Utilisateur,
)
from ..utils.gain_passif import normaliser_mode


def parse_operation(op: str) -> str:
    op = (op or "add").strip().lower()
    if op not in ("add", "remove", "set"):
        raise ValueError("operation invalide (add, remove, set)")
    return op


def validate_pct(val: float, op: str) -> float:
    v = float(val)
    if op == "set" and v <= 0:
        raise ValueError("En mode set, valeur_pct doit être > 0")
    if op in ("add", "remove") and v <= 0:
        raise ValueError("Pour add/remove, valeur_pct (delta) doit être > 0")
    return v


def validate_cible(c: str) -> str:
    c = (c or "aucun").strip().lower()
    if c not in ("aucun", "tous", "joueurs"):
        raise ValueError("cible invalide (aucun, tous, joueurs)")
    return c


def parse_uid_list(raw) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return []
    if not isinstance(raw, list):
        return []
    out = []
    for x in raw:
        if x is None:
            continue
        s = str(x).strip()
        if s:
            out.append(s)
    return out


def effective_user_ids(e: Evenement) -> list[str]:
    if e.brouillon or not e.actif:
        return []
    c = validate_cible(e.cible)
    if c == "aucun":
        return []
    if c == "tous":
        return [u.id for u in Utilisateur.query.filter_by(is_mj=False).order_by(Utilisateur.id).all()]
    if c == "joueurs":
        uids = parse_uid_list(e.cible_utilisateur_ids)
        ok = []
        for uid in uids:
            if db.session.get(Utilisateur, uid):
                ok.append(uid)
        return ok
    return []


def validate_utilisateur_id(uid: str | None) -> str | None:
    if uid is None:
        return None
    uid = str(uid).strip()
    if uid == "":
        return None
    if not db.session.get(Utilisateur, uid):
        raise ValueError(f"Joueur inconnu : {uid}")
    return uid


def validate_ressource_id(rid: int) -> int:
    rid = int(rid)
    if not db.session.get(Ressource, rid):
        raise ValueError(f"Ressource introuvable : {rid}")
    return rid


def validate_categorie_id(cid: int) -> int:
    cid = int(cid)
    if not db.session.get(Categorie, cid):
        raise ValueError(f"Catégorie introuvable : {cid}")
    return cid


def sync_impacts(e: Evenement, data: dict) -> None:
    impacts = (data or {}).get("impacts") or {}
    cats = impacts.get("categories") or []
    res = impacts.get("ressources") or []
    prods = impacts.get("productions") or []

    if not isinstance(cats, list) or not isinstance(res, list) or not isinstance(prods, list):
        raise ValueError("impacts.categories / impacts.ressources / impacts.productions doivent être des listes")

    e.impacts_categories.clear()
    e.impacts_ressources.clear()
    e.impacts_productions.clear()

    for row in cats:
        op = parse_operation(row.get("operation"))
        cid = validate_categorie_id(row.get("categorie_id"))
        val = validate_pct(row.get("valeur_pct", 0), op)
        e.impacts_categories.append(
            EvenementImpactCategorie(categorie_id=cid, operation=op, valeur_pct=val)
        )

    for row in res:
        op = parse_operation(row.get("operation"))
        rid = validate_ressource_id(row.get("ressource_id"))
        val = validate_pct(row.get("valeur_pct", 0), op)
        e.impacts_ressources.append(
            EvenementImpactRessource(ressource_id=rid, operation=op, valeur_pct=val)
        )

    for row in prods:
        uid = validate_utilisateur_id(row.get("utilisateur_id"))
        rid = validate_ressource_id(row.get("ressource_id"))
        qpt = int(row.get("quantite_par_tour", 0))
        mode = normaliser_mode(row.get("mode_production"))
        delai = int(row.get("delai_tours", 0) or 0)
        actif = bool(row.get("actif", True))

        tours_restants = row.get("tours_restants", None)
        if tours_restants is None:
            tr = None
        else:
            tr = int(tours_restants)
            if tr <= 0:
                raise ValueError("tours_restants doit être > 0 (ou null pour illimité)")

        if delai < 0 or delai > 1000:
            raise ValueError("delai_tours doit être entre 0 et 1000")

        e.impacts_productions.append(
            EvenementImpactProduction(
                utilisateur_id=uid,
                ressource_id=rid,
                quantite_par_tour=qpt,
                mode_production=mode,
                delai_tours=delai,
                tours_restants=tr,
                actif=actif,
            )
        )


def supprimer_gains_passifs_evenement(evenement_id: int, utilisateur_id: str | None = None) -> None:
    q = GainPassif.query.filter_by(evenement_id=evenement_id)
    if utilisateur_id is not None:
        q = q.filter_by(utilisateur_id=utilisateur_id)
    q.delete()


def sync_evenement_joueurs(e: Evenement) -> None:
    EvenementJoueur.query.filter_by(evenement_id=e.id).delete()
    if e.brouillon or not e.actif:
        return
    uids = effective_user_ids(e)
    d = int(e.delai_tours or 0)
    tr = e.tours_restants
    for uid in uids:
        db.session.add(
            EvenementJoueur(
                evenement_id=e.id,
                utilisateur_id=uid,
                delai_tours=d,
                tours_restants=tr,
                actif=True,
            )
        )


def materialiser_productions(e: Evenement) -> None:
    targets = set(effective_user_ids(e))
    for imp in e.impacts_productions or []:
        if not imp.actif:
            continue
        if imp.utilisateur_id is None:
            users = sorted(targets)
        else:
            if imp.utilisateur_id not in targets:
                continue
            users = [imp.utilisateur_id]

        for uid in users:
            db.session.add(
                GainPassif(
                    utilisateur_id=uid,
                    ressource_id=imp.ressource_id,
                    quantite_par_tour=int(imp.quantite_par_tour),
                    actif=bool(imp.actif),
                    tours_restants=imp.tours_restants,
                    delai_tours=int(imp.delai_tours or 0),
                    balise="evenement",
                    mode_production=imp.mode_production,
                    evenement_id=e.id,
                )
            )


def appliquer_effets_materiels(e: Evenement) -> None:
    supprimer_gains_passifs_evenement(e.id)
    if e.brouillon or not e.actif:
        return
    sync_evenement_joueurs(e)
    db.session.flush()
    materialiser_productions(e)


def sync_evenement_champs(e: Evenement, data: dict) -> None:
    if "brouillon" in data:
        e.brouillon = bool(data.get("brouillon"))
    if "cible" in data:
        e.cible = validate_cible(data.get("cible"))
    if "cible_utilisateur_ids" in data:
        uids = data.get("cible_utilisateur_ids") or []
        if not isinstance(uids, list):
            raise ValueError("cible_utilisateur_ids doit être une liste")
        for uid in uids:
            if not db.session.get(Utilisateur, str(uid)):
                raise ValueError(f"Joueur inconnu : {uid}")
        e.cible_utilisateur_ids = json.dumps([str(x) for x in uids if x is not None])
    if "delai_tours" in data:
        dt = int(data.get("delai_tours") or 0)
        if dt < 0 or dt > 1000:
            raise ValueError("delai_tours doit être entre 0 et 1000")
        e.delai_tours = dt
    if "tours_restants" in data:
        tr = data.get("tours_restants")
        if tr is None:
            e.tours_restants = None
        else:
            tr = int(tr)
            if tr <= 0:
                raise ValueError("tours_restants doit être > 0 ou null (illimité)")
            e.tours_restants = tr


def _impacts_categorie_hors_evenement(
    categorie_id: int, utilisateur_id: str, exclude_evenement_id: int | None
) -> list[dict]:
    from ..utils.prix import _evenement_effet_prix_actif

    out: list[dict] = []
    for imp in EvenementImpactCategorie.query.filter_by(categorie_id=categorie_id).all():
        if exclude_evenement_id is not None and imp.evenement_id == exclude_evenement_id:
            continue
        if not _evenement_effet_prix_actif(imp.evenement_id, utilisateur_id):
            continue
        out.append({"operation": imp.operation, "valeur_pct": float(imp.valeur_pct)})
    return out


def _impacts_ressource_hors_evenement(
    ressource_id: int, utilisateur_id: str, exclude_evenement_id: int | None
) -> list[dict]:
    from ..utils.prix import _evenement_effet_prix_actif

    out: list[dict] = []
    for imp in EvenementImpactRessource.query.filter_by(ressource_id=ressource_id).all():
        if exclude_evenement_id is not None and imp.evenement_id == exclude_evenement_id:
            continue
        if not _evenement_effet_prix_actif(imp.evenement_id, utilisateur_id):
            continue
        out.append({"operation": imp.operation, "valeur_pct": float(imp.valeur_pct)})
    return out


def _pct_base_categorie_joueur(utilisateur_id: str, categorie: Categorie) -> float:
    row = CategorieModificateurJoueur.query.filter_by(
        utilisateur_id=utilisateur_id, categorie_id=categorie.id
    ).first()
    if row is not None:
        return float(row.modificateur_pct)
    return float(getattr(categorie, "modificateur_pct", 100.0))


def _pct_base_ressource_joueur(utilisateur_id: str, ressource: Ressource) -> float:
    row = RessourceModificateurJoueur.query.filter_by(
        utilisateur_id=utilisateur_id, ressource_id=ressource.id
    ).first()
    if row is not None:
        return float(row.modificateur_pct)
    return float(getattr(ressource, "modificateur_pct", 100.0))


def _somme_qpt_gains_sauf_evenement(
    utilisateur_id: str, ressource_id: int, mode_production: str, exclude_evenement_id: int | None
) -> int:
    q = GainPassif.query.filter_by(
        utilisateur_id=utilisateur_id,
        ressource_id=ressource_id,
        actif=True,
        mode_production=mode_production,
    )
    s = 0
    for g in q:
        if exclude_evenement_id is not None and g.evenement_id == exclude_evenement_id:
            continue
        s += int(g.quantite_par_tour or 0)
    return s


def preview_evenement_impacts(data: dict) -> dict:
    """
    Aperçu MJ : pour chaque ligne d'impact, % prix catégorie / ressource ou somme de production
    avant → après pour chaque joueur ciblé (hors impacts de l'évènement en cours d'édition).
    """
    from ..utils.prix import _pct_apres_impacts

    exclude_eid = data.get("evenement_id")
    if exclude_eid is not None:
        exclude_eid = int(exclude_eid)

    cible = validate_cible(data.get("cible", "aucun"))
    raw_uids = data.get("cible_utilisateur_ids") or []
    if cible == "tous":
        uids = [u.id for u in Utilisateur.query.filter_by(is_mj=False).order_by(Utilisateur.id).all()]
    elif cible == "joueurs":
        uids = [str(x) for x in raw_uids if x is not None and str(x).strip()]
    else:
        uids = []

    impacts = data.get("impacts") or {}
    cat_rows = impacts.get("categories") or []
    res_rows = impacts.get("ressources") or []
    prod_rows = impacts.get("productions") or []

    if not uids:
        return {
            "ok": True,
            "utilisateur_ids": [],
            "blocs": [],
            "message": "Aucun joueur dans la cible : sélectionnez des comptes pour voir l’aperçu.",
        }

    uid_set = set(uids)
    blocs: list[dict] = []

    for i, row in enumerate(cat_rows):
        cid = row.get("categorie_id")
        if cid is None:
            continue
        cat = db.session.get(Categorie, int(cid))
        if not cat:
            continue
        try:
            op = parse_operation(row.get("operation"))
            val = validate_pct(float(row.get("valeur_pct", 0)), op)
        except (ValueError, TypeError):
            continue
        stacked_prior: list[dict] = []
        for j in range(i):
            rj = cat_rows[j]
            if rj.get("categorie_id") is None:
                continue
            if int(rj["categorie_id"]) != int(cid):
                continue
            try:
                oj = parse_operation(rj.get("operation"))
                vj = validate_pct(float(rj.get("valeur_pct", 0)), oj)
                stacked_prior.append({"operation": oj, "valeur_pct": vj})
            except (ValueError, TypeError):
                continue
        joueurs: list[dict] = []
        for uid in uids:
            u = db.session.get(Utilisateur, uid)
            if not u:
                continue
            base = _pct_base_categorie_joueur(uid, cat)
            existing = _impacts_categorie_hors_evenement(int(cid), uid, exclude_eid)
            chain = list(existing) + stacked_prior
            avant = _pct_apres_impacts(base, chain)
            apres = _pct_apres_impacts(avant, [{"operation": op, "valeur_pct": val}])
            joueurs.append(
                {
                    "utilisateur_id": uid,
                    "username": u.username or uid,
                    "avant_pct": round(avant, 2),
                    "apres_pct": round(apres, 2),
                }
            )
        blocs.append(
            {
                "kind": "categorie",
                "index": i,
                "categorie_id": int(cid),
                "nom": cat.nom,
                "titre": f"{cat.nom} — % catégorie (prix marché)",
                "sous_titre": "Modificateur de catégorie pour le calcul du prix (add / remove = delta).",
                "joueurs": joueurs,
            }
        )

    for i, row in enumerate(res_rows):
        rid = row.get("ressource_id")
        if rid is None:
            continue
        r = db.session.get(Ressource, int(rid))
        if not r:
            continue
        try:
            op = parse_operation(row.get("operation"))
            val = validate_pct(float(row.get("valeur_pct", 0)), op)
        except (ValueError, TypeError):
            continue
        stacked_prior: list[dict] = []
        for j in range(i):
            rj = res_rows[j]
            if rj.get("ressource_id") is None:
                continue
            if int(rj["ressource_id"]) != int(rid):
                continue
            try:
                oj = parse_operation(rj.get("operation"))
                vj = validate_pct(float(rj.get("valeur_pct", 0)), oj)
                stacked_prior.append({"operation": oj, "valeur_pct": vj})
            except (ValueError, TypeError):
                continue
        joueurs: list[dict] = []
        for uid in uids:
            u = db.session.get(Utilisateur, uid)
            if not u:
                continue
            base = _pct_base_ressource_joueur(uid, r)
            existing = _impacts_ressource_hors_evenement(int(rid), uid, exclude_eid)
            chain = list(existing) + stacked_prior
            avant = _pct_apres_impacts(base, chain)
            apres = _pct_apres_impacts(avant, [{"operation": op, "valeur_pct": val}])
            joueurs.append(
                {
                    "utilisateur_id": uid,
                    "username": u.username or uid,
                    "avant_pct": round(avant, 2),
                    "apres_pct": round(apres, 2),
                }
            )
        blocs.append(
            {
                "kind": "ressource",
                "index": i,
                "ressource_id": int(rid),
                "nom": r.nom,
                "titre": f"{r.nom} — % ressource (prix marché)",
                "sous_titre": "Modificateur propre à la ressource pour le calcul du prix (hors catégories).",
                "joueurs": joueurs,
            }
        )

    for i, row in enumerate(prod_rows):
        rid = row.get("ressource_id")
        if rid is None:
            continue
        r = db.session.get(Ressource, int(rid))
        if not r:
            continue
        mode = normaliser_mode(row.get("mode_production"))
        qpt_new = int(row.get("quantite_par_tour") or 0)
        uid_line = row.get("utilisateur_id")
        if uid_line is not None and str(uid_line).strip() != "":
            u_one = str(uid_line).strip()
            prod_targets = [u_one] if u_one in uid_set else []
        else:
            prod_targets = list(uids)

        joueurs: list[dict] = []
        for uid in prod_targets:
            u = db.session.get(Utilisateur, uid)
            if not u:
                continue
            if mode == "fixe":
                avant = _somme_qpt_gains_sauf_evenement(uid, int(rid), mode, exclude_eid)
                apres = avant + qpt_new
                joueurs.append(
                    {
                        "utilisateur_id": uid,
                        "username": u.username or uid,
                        "avant_qpt": avant,
                        "apres_qpt": apres,
                        "mode": mode,
                    }
                )
            else:
                joueurs.append(
                    {
                        "utilisateur_id": uid,
                        "username": u.username or uid,
                        "avant_qpt": None,
                        "apres_qpt": None,
                        "mode": mode,
                        "note": "Mode pourcentage : l’effet dépend de l’ordre des gains ce tour — pas de total simple.",
                    }
                )
        if not joueurs:
            continue
        blocs.append(
            {
                "kind": "production",
                "index": i,
                "ressource_id": int(rid),
                "nom": r.nom,
                "titre": f"{r.nom} — production (quantité / tour, mode {mode})",
                "sous_titre": "Somme des gains passifs « fixe » pour cette ressource + la ligne ajoutée par l’évènement.",
                "joueurs": joueurs,
            }
        )

    return {"ok": True, "utilisateur_ids": uids, "blocs": blocs, "message": None}


def marquer_deja_publie_si_non_brouillon(e: Evenement) -> None:
    """Après une sauvegarde : si l’évènement n’est plus en brouillon, verrouiller l’UI brouillon côté client."""
    if not e.brouillon:
        e.deja_publie = True


def apercu_impacts_pour_joueur(evenement_id: int, utilisateur_id: str) -> dict:
    """
    Même logique que preview-impacts MJ, mais pour un joueur et les impacts persistés de l’évènement.
    Les autres évènements actifs pour ce joueur sont pris en compte (exclude_evenement_id).
    """
    e = db.session.get(Evenement, evenement_id)
    if not e:
        raise ValueError("Évènement introuvable")
    d = e.to_dict()
    uid = str(utilisateur_id).strip()
    prods = []
    for p in d.get("impacts", {}).get("productions") or []:
        prods.append(
            {
                "utilisateur_id": p.get("utilisateur_id"),
                "ressource_id": p.get("ressource_id"),
                "quantite_par_tour": int(p.get("quantite_par_tour") or 0),
                "mode_production": p.get("mode_production") or "fixe",
                "delai_tours": int(p.get("delai_tours") or 0),
                "tours_restants": p.get("tours_restants"),
                "actif": bool(p.get("actif", True)),
            }
        )
    cats = []
    for c in d.get("impacts", {}).get("categories") or []:
        cats.append(
            {
                "categorie_id": c.get("categorie_id"),
                "operation": c.get("operation") or "add",
                "valeur_pct": float(c.get("valeur_pct") or 0),
            }
        )
    ress = []
    for r in d.get("impacts", {}).get("ressources") or []:
        ress.append(
            {
                "ressource_id": r.get("ressource_id"),
                "operation": r.get("operation") or "add",
                "valeur_pct": float(r.get("valeur_pct") or 0),
            }
        )
    payload = {
        "evenement_id": e.id,
        "cible": "joueurs",
        "cible_utilisateur_ids": [uid],
        "impacts": {"categories": cats, "ressources": ress, "productions": prods},
    }
    return preview_evenement_impacts(payload)


def resume_lignes_depuis_apercu(apercu: dict) -> list[dict]:
    """Lignes plates pour un tableau « avant / après » (un joueur par bloc)."""
    rows: list[dict] = []
    for b in apercu.get("blocs") or []:
        kind = b.get("kind")
        j_list = b.get("joueurs") or []
        j = j_list[0] if j_list else {}
        row: dict = {
            "kind": kind,
            "titre": b.get("titre") or b.get("nom") or "",
            "avant": None,
            "apres": None,
            "note": None,
        }
        if kind in ("categorie", "ressource"):
            row["avant"] = f"{j.get('avant_pct')} %"
            row["apres"] = f"{j.get('apres_pct')} %"
        elif kind == "production":
            if j.get("note"):
                row["note"] = j["note"]
                row["avant"] = "—"
                row["apres"] = "—"
            else:
                row["avant"] = f"{j.get('avant_qpt')} / tour"
                row["apres"] = f"{j.get('apres_qpt')} / tour"
        rows.append(row)
    return rows
