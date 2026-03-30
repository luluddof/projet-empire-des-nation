from flask import Blueprint, jsonify, request

from ..data.seed import NOM_RESSOURCE_FLORINS
from ..extensions import db
from ..models import GainPassif, Ressource, Stock, Transaction
from ..utils.decorators import get_current_user, login_required
from ..utils.gain_passif import (
    BALISE_LABELS,
    normaliser_balise,
    normaliser_mode,
    net_un_tour,
    net_un_tour_breakdown,
    simuler_trois_tours,
    simuler_trois_tours_breakdown,
)
from ..utils.prix import prix_achat_pour_utilisateur, prix_modifie_pour_utilisateur

stocks_bp = Blueprint("stocks", __name__)


def _resolve_cible(uid_param):
    """Renvoie (uid_cible, utilisateur_courant). Un joueur ne peut accéder qu'à ses propres données."""
    me = get_current_user()
    if uid_param and me.is_mj:
        return uid_param, me
    return me.id, me


def _get_or_create_stock(utilisateur_id, ressource_id):
    stock = Stock.query.filter_by(
        utilisateur_id=utilisateur_id, ressource_id=ressource_id
    ).first()
    if not stock:
        stock = Stock(utilisateur_id=utilisateur_id, ressource_id=ressource_id, quantite=0)
        db.session.add(stock)
    return stock


# ---------------------------------------------------------------------------
# Stocks
# ---------------------------------------------------------------------------


@stocks_bp.get("/api/gains-passifs/balises")
@login_required
def list_balises_gains_passifs():
    # Retour pour pilotage UI : {id,label}
    order = ["science", "politique", "evenement", "batiment", "autre"]
    out = []
    for k in order:
        if k in BALISE_LABELS:
            out.append({"id": k, "label": BALISE_LABELS[k]})
    return jsonify(out)


@stocks_bp.get("/api/stocks")
@login_required
def get_stocks():
    uid = request.args.get("uid")
    cible_uid, me = _resolve_cible(uid)
    if uid and uid != me.id and not me.is_mj:
        return jsonify({"error": "Accès refusé"}), 403

    stocks_existants = (
        Stock.query.filter_by(utilisateur_id=cible_uid)
        .join(Stock.ressource)
        .order_by(Ressource.nom)
        .all()
    )
    stock_par_rid = {s.ressource_id: s for s in stocks_existants}

    toutes = Ressource.query.order_by(Ressource.nom).all()
    result = []
    for r in toutes:
        if r.id in stock_par_rid:
            result.append(stock_par_rid[r.id].to_dict(cible_uid))
        else:
            result.append({
                "id": None,
                "utilisateur_id": cible_uid,
                "ressource_id": r.id,
                "ressource": r.to_dict(cible_uid),
                "quantite": 0,
            })
    return jsonify(result)


@stocks_bp.post("/api/stocks/commerce")
@login_required
def commerce_ressource_contre_florins():
    """
    Achat : +quantité de ressource, débit florins au prix d'achat (× prix_achat).
    Vente : −quantité de ressource, crédit florins au prix modifié (× prix_modifie).
    """
    uid = request.args.get("uid")
    cible_uid, me = _resolve_cible(uid)
    if uid and uid != me.id and not me.is_mj:
        return jsonify({"error": "Accès refusé"}), 403

    data = request.get_json() or {}
    sens = (data.get("sens") or "").strip().lower()
    if sens not in ("achat", "vente"):
        return jsonify({"error": "sens doit être 'achat' ou 'vente'"}), 400
    if "ressource_id" not in data or "quantite" not in data:
        return jsonify({"error": "Champs 'ressource_id' et 'quantite' requis"}), 400

    try:
        ressource_id = int(data["ressource_id"])
        quantite = int(data["quantite"])
    except (TypeError, ValueError):
        return jsonify({"error": "ressource_id et quantite doivent être des entiers"}), 400

    if quantite <= 0:
        return jsonify({"error": "quantite doit être > 0"}), 400

    florins_r = Ressource.query.filter_by(nom=NOM_RESSOURCE_FLORINS).first()
    if not florins_r:
        return jsonify({"error": "Ressource Florins introuvable (redémarrer le serveur)"}), 500
    if ressource_id == florins_r.id:
        return jsonify({"error": "Impossible d'échanger des florins contre des florins"}), 400

    ressource = db.get_or_404(Ressource, ressource_id)
    stock_res = _get_or_create_stock(cible_uid, ressource_id)
    stock_florins = _get_or_create_stock(cible_uid, florins_r.id)
    pf = prix_achat_pour_utilisateur(florins_r, cible_uid) or 1
    pa = prix_achat_pour_utilisateur(ressource, cible_uid)
    pm = prix_modifie_pour_utilisateur(ressource, cible_uid)

    if sens == "achat":
        cout = quantite * pa
        if stock_florins.quantite < cout:
            return jsonify({"error": "Florins insuffisants pour cet achat"}), 400
        stock_res.quantite += quantite
        stock_florins.quantite -= cout
        db.session.add(
            Transaction(
                utilisateur_id=cible_uid,
                ressource_id=ressource_id,
                quantite=quantite,
                valeur_florins=quantite * pa,
                motif="achat_marche",
            )
        )
        db.session.add(
            Transaction(
                utilisateur_id=cible_uid,
                ressource_id=florins_r.id,
                quantite=-cout,
                valeur_florins=-cout * pf,
                motif="achat_marche",
            )
        )
    else:
        if stock_res.quantite < quantite:
            return jsonify({"error": "Stock insuffisant pour cette vente"}), 400
        recette = quantite * pm
        stock_res.quantite -= quantite
        stock_florins.quantite += recette
        db.session.add(
            Transaction(
                utilisateur_id=cible_uid,
                ressource_id=ressource_id,
                quantite=-quantite,
                valeur_florins=-quantite * pa,
                motif="vente_marche",
            )
        )
        db.session.add(
            Transaction(
                utilisateur_id=cible_uid,
                ressource_id=florins_r.id,
                quantite=recette,
                valeur_florins=recette * pf,
                motif="vente_marche",
            )
        )

    db.session.commit()
    return jsonify(
        {
            "ok": True,
            "stock_ressource": stock_res.to_dict(cible_uid),
            "stock_florins": stock_florins.to_dict(cible_uid),
        }
    )


@stocks_bp.put("/api/stocks/<int:ressource_id>")
@login_required
def update_stock(ressource_id):
    uid = request.args.get("uid")
    cible_uid, me = _resolve_cible(uid)
    if uid and uid != me.id and not me.is_mj:
        return jsonify({"error": "Accès refusé"}), 403

    data = request.get_json() or {}
    if "quantite" not in data:
        return jsonify({"error": "Champ 'quantite' requis"}), 400

    ressource = db.get_or_404(Ressource, ressource_id)
    stock = _get_or_create_stock(cible_uid, ressource_id)
    pa = prix_achat_pour_utilisateur(ressource, cible_uid)

    nouvelle_qte = int(data["quantite"])
    delta = nouvelle_qte - stock.quantite
    stock.quantite = nouvelle_qte

    if delta != 0:
        db.session.add(Transaction(
            utilisateur_id=cible_uid,
            ressource_id=ressource_id,
            quantite=delta,
            valeur_florins=delta * pa,
            motif=data.get("motif", "ajustement_manuel"),
        ))

    db.session.commit()
    return jsonify(stock.to_dict(cible_uid))


# ---------------------------------------------------------------------------
# Gains passifs
# ---------------------------------------------------------------------------


def _erreur_pourcentage(mode, quantite_par_tour):
    if normaliser_mode(mode) != "pourcentage":
        return None
    q = int(quantite_par_tour)
    if q < -1000 or q > 1000:
        return "En mode pourcentage, la valeur doit être entre -1000 et 1000 (% du stock avant la ligne)."
    return None


def _cluster_transactions_gain_passif(transactions, gap_seconds=8):
    """
    Regroupe les transactions « gain_passif » exécutées dans le même passage du scheduler
    (plusieurs lignes par ressource = plusieurs lignes dans la même fenêtre temporelle).
    """
    if not transactions:
        return []
    ordered = sorted(transactions, key=lambda t: t.created_at)
    clusters = []
    current = []
    for t in ordered:
        if not current:
            current.append(t)
        elif (t.created_at - current[0].created_at).total_seconds() <= gap_seconds:
            current.append(t)
        else:
            clusters.append(current)
            current = [t]
    if current:
        clusters.append(current)
    return clusters


@stocks_bp.get("/api/gains-passifs/chronologie")
@login_required
def get_gains_chronologie():
    """
    Pour une ressource : production au prochain tour, 5 derniers tours (transactions),
    3 prochains tours (simulation à partir des règles actuelles).
    """
    uid = request.args.get("uid")
    cible_uid, me = _resolve_cible(uid)
    if uid and uid != me.id and not me.is_mj:
        return jsonify({"error": "Accès refusé"}), 403

    rid = request.args.get("ressource_id")
    if not rid:
        return jsonify({"error": "ressource_id requis"}), 400
    try:
        ressource_id = int(rid)
    except (TypeError, ValueError):
        return jsonify({"error": "ressource_id invalide"}), 400

    ressource = db.session.get(Ressource, ressource_id)
    if not ressource:
        return jsonify({"error": "Ressource introuvable"}), 404

    gains = (
        GainPassif.query.filter_by(
            utilisateur_id=cible_uid,
            ressource_id=ressource_id,
        )
        .order_by(GainPassif.id)
        .all()
    )

    stock = Stock.query.filter_by(
        utilisateur_id=cible_uid,
        ressource_id=ressource_id,
    ).first()
    sq = int(stock.quantite) if stock else 0

    prochain_breakdown = net_un_tour_breakdown(gains, sq)
    prochain_tour = prochain_breakdown["total"]

    txs = (
        Transaction.query.filter_by(
            utilisateur_id=cible_uid,
            ressource_id=ressource_id,
            motif="gain_passif",
        )
        .order_by(Transaction.created_at.asc())
        .all()
    )
    clusters = _cluster_transactions_gain_passif(txs)
    derniers = clusters[-5:]
    passe = [
        {
            "at": cl[0].created_at.isoformat(),
            "quantite": sum(t.quantite for t in cl),
        }
        for cl in derniers
    ]

    futur_breakdown_vals = simuler_trois_tours_breakdown(gains, sq)
    futur = [
        {
            "tour": i + 1,
            "quantite": int(row["total"]),
        }
        for i, row in enumerate(futur_breakdown_vals)
    ]
    futur_breakdown = [
        {
            "tour": i + 1,
            "actif": int(row["actif"]),
            "pending": int(row["pending"]),
        }
        for i, row in enumerate(futur_breakdown_vals)
    ]

    return jsonify({
        "ressource": ressource.to_dict(cible_uid),
        "prochain_tour": prochain_tour,
        "prochain_tour_breakdown": {
            "actif": int(prochain_breakdown["actif"]),
            "pending": int(prochain_breakdown["pending"]),
        },
        "passe": passe,
        "futur": futur,
        "futur_breakdown": futur_breakdown,
    })


@stocks_bp.get("/api/gains-passifs")
@login_required
def get_gains_passifs():
    uid = request.args.get("uid")
    cible_uid, me = _resolve_cible(uid)
    if uid and uid != me.id and not me.is_mj:
        return jsonify({"error": "Accès refusé"}), 403

    gains = (
        GainPassif.query.filter_by(utilisateur_id=cible_uid)
        .join(GainPassif.ressource)
        .order_by(Ressource.nom, GainPassif.id)
        .all()
    )
    return jsonify([g.to_dict() for g in gains])


@stocks_bp.post("/api/gains-passifs")
@login_required
def create_gain_passif():
    uid = request.args.get("uid")
    cible_uid, me = _resolve_cible(uid)
    if uid and uid != me.id and not me.is_mj:
        return jsonify({"error": "Accès refusé"}), 403

    data = request.get_json() or {}
    if "ressource_id" not in data:
        return jsonify({"error": "Champ 'ressource_id' requis"}), 400

    ressource_id = int(data["ressource_id"])
    db.get_or_404(Ressource, ressource_id)

    qpt = data.get("quantite_par_tour")
    if qpt is None:
        return jsonify({"error": "Champ 'quantite_par_tour' requis"}), 400
    quantite_par_tour = int(qpt)

    delai_tours = data.get("delai_tours", 0)
    if delai_tours is None:
        delai_tours = 0
    try:
        delai_tours = int(delai_tours)
    except (TypeError, ValueError):
        return jsonify({"error": "delai_tours doit être un entier"}), 400
    if delai_tours < 0 or delai_tours > 1000:
        return jsonify({"error": "delai_tours doit être entre 0 et 1000"}), 400

    mode = normaliser_mode(data.get("mode_production"))
    balise = normaliser_balise(data.get("balise"))
    err_pct = _erreur_pourcentage(mode, quantite_par_tour)
    if err_pct:
        return jsonify({"error": err_pct}), 400

    definitif = bool(data.get("definitif", True))
    tours_restants = data.get("tours_restants")
    if not definitif:
        if tours_restants is None or int(tours_restants) <= 0:
            return jsonify({"error": "Pour un gain temporaire, 'tours_restants' (>0) est requis"}), 400
        tr = int(tours_restants)
    else:
        tr = None

    gain = GainPassif(
        utilisateur_id=cible_uid,
        ressource_id=ressource_id,
        quantite_par_tour=quantite_par_tour,
        actif=bool(data.get("actif", True)),
        tours_restants=tr,
        delai_tours=delai_tours,
        balise=balise,
        mode_production=mode,
    )
    db.session.add(gain)
    db.session.commit()
    return jsonify(gain.to_dict()), 201


@stocks_bp.put("/api/gains-passifs/<int:gain_id>")
@login_required
def update_gain_passif(gain_id):
    uid = request.args.get("uid")
    cible_uid, me = _resolve_cible(uid)
    if uid and uid != me.id and not me.is_mj:
        return jsonify({"error": "Accès refusé"}), 403

    gain = GainPassif.query.filter_by(id=gain_id, utilisateur_id=cible_uid).first()
    if not gain:
        return jsonify({"error": "Gain passif introuvable"}), 404

    data = request.get_json() or {}
    if "quantite_par_tour" in data:
        gain.quantite_par_tour = int(data["quantite_par_tour"])
    if "actif" in data:
        gain.actif = bool(data["actif"])
    if "delai_tours" in data:
        dt = data.get("delai_tours", 0)
        if dt is None:
            dt = 0
        try:
            dt = int(dt)
        except (TypeError, ValueError):
            return jsonify({"error": "delai_tours doit être un entier"}), 400
        if dt < 0 or dt > 1000:
            return jsonify({"error": "delai_tours doit être entre 0 et 1000"}), 400
        gain.delai_tours = dt
    if "definitif" in data or "tours_restants" in data:
        definitif = bool(data.get("definitif", gain.tours_restants is None))
        if definitif:
            gain.tours_restants = None
        else:
            tr = data.get("tours_restants", gain.tours_restants)
            if tr is None or int(tr) <= 0:
                return jsonify({"error": "tours_restants requis (>0) pour un gain temporaire"}), 400
            gain.tours_restants = int(tr)
    if "balise" in data:
        gain.balise = normaliser_balise(data["balise"])
    if "mode_production" in data:
        gain.mode_production = normaliser_mode(data["mode_production"])

    err_pct = _erreur_pourcentage(gain.mode_production, gain.quantite_par_tour)
    if err_pct:
        return jsonify({"error": err_pct}), 400

    db.session.commit()
    return jsonify(gain.to_dict())


@stocks_bp.delete("/api/gains-passifs/<int:gain_id>")
@login_required
def delete_gain_passif(gain_id):
    uid = request.args.get("uid")
    cible_uid, me = _resolve_cible(uid)
    if uid and uid != me.id and not me.is_mj:
        return jsonify({"error": "Accès refusé"}), 403

    gain = GainPassif.query.filter_by(id=gain_id, utilisateur_id=cible_uid).first()
    if not gain:
        return jsonify({"error": "Gain passif introuvable"}), 404
    db.session.delete(gain)
    db.session.commit()
    return jsonify({"ok": True})
