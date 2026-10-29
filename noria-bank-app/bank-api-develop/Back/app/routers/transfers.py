from fastapi import APIRouter, Depends, HTTPException

from .. import db
from .. import iban as iban_utils
from ..deps import errors, get_current_user, get_db, get_transaction, owned_account, to_cents
from ..schemas import Transaction, TransferIn

router = APIRouter(prefix="/transfers", tags=["Virements"])


@router.post("", status_code=201, response_model=Transaction, responses=errors(400, 401, 403, 404))
def transfer(body: TransferIn, user=Depends(get_current_user), conn=Depends(get_db)):
    """S5 : Virement d'un de mes comptes vers n'importe quel compte ouvert de la banque (le mien ou celui
    d'un autre client). `toIban` accepte les espaces. Renvoie la transaction vue depuis le compte source.

    Erreurs : montant invalide (400), IBAN invalide (400), même compte (400), solde insuffisant (400),
    compte source d'un autre (403), compte source ou destinataire introuvable (404).
    """
    cents = to_cents(body.amount)
    label = (body.label or "").strip() or "Virement"
    if len(label) > 100:
        raise HTTPException(400, "Le libellé ne doit pas dépasser 100 caractères")
    to_iban = iban_utils.normalize(body.toIban)
    if not iban_utils.is_valid(to_iban):
        raise HTTPException(400, "IBAN du destinataire invalide")

    with db.transaction(conn):
        source = owned_account(conn, user, body.fromAccountId)
        target = conn.execute(
            "SELECT * FROM accounts WHERE iban = ? AND closed_at IS NULL", (to_iban,)
        ).fetchone()
        if target is None:
            raise HTTPException(404, "Aucun compte ouvert avec cet IBAN")
        if target["id"] == source["id"]:
            raise HTTPException(400, "Le compte destinataire doit être différent du compte source")
        if source["balance_cents"] < cents:
            raise HTTPException(400, "Solde insuffisant")
        transaction_id = db.record_transaction(conn, "transfer", cents, source["id"], target["id"], label)
    return get_transaction(conn, source["id"], transaction_id)
