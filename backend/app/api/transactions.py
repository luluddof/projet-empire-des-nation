from flask import Blueprint, jsonify, request

from ..models import Transaction
from ..utils.decorators import get_current_user, login_required

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.get("/api/transactions")
@login_required
def get_transactions():
    me = get_current_user()
    uid = request.args.get("uid")

    if uid and uid != me.id and not me.is_mj:
        return jsonify({"error": "Accès refusé"}), 403

    cible_uid = uid if (uid and me.is_mj) else me.id
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 50))))

    pagination = (
        Transaction.query.filter_by(utilisateur_id=cible_uid)
        .order_by(Transaction.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return jsonify({
        "transactions": [t.to_dict() for t in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "page": page,
    })
