from fastapi import APIRouter, Depends, HTTPException, Response

from .. import db
from ..deps import (
    TRANSACTIONS_QUERY,
    account_out,
    errors,
    get_current_user,
    get_db,
    get_transaction,
    owned_account,
    to_cents,
    transaction_out,
)
from ..pdf import statement_pdf
from ..schemas import Account, DepositIn, Transaction

router = APIRouter(prefix="/accounts", tags=["Comptes"])

MAX_OPEN_ACCOUNTS = 5
MAX_DEPOSIT_CENTS = 10_000_00


@router.get("", response_model=list[Account], responses=errors(401))
def list_accounts(user=Depends(get_current_user), conn=Depends(get_db)):
    """S3, S9 : Les comptes ouverts de l'utilisateur, du plus récent au plus ancien."""
    rows = conn.execute(
        "SELECT * FROM accounts WHERE user_id = ? AND closed_at IS NULL"
        " ORDER BY created_at DESC, id DESC",
        (user["id"],),
    ).fetchall()
    return [account_out(row) for row in rows]


@router.post("", status_code=201, response_model=Account, responses=errors(400, 401))
def open_account(user=Depends(get_current_user), conn=Depends(get_db)):
    """S8 : Ouvre un compte **secondaire** (solde 0 €). Pas de corps de requête.

    Erreur : 5 comptes ouverts au maximum (400).
    """
    with db.transaction(conn):
        count = conn.execute(
            "SELECT COUNT(*) FROM accounts WHERE user_id = ? AND closed_at IS NULL", (user["id"],)
        ).fetchone()[0]
        if count >= MAX_OPEN_ACCOUNTS:
            raise HTTPException(400, f"Vous avez déjà {MAX_OPEN_ACCOUNTS} comptes ouverts (maximum)")
        account_id = db.open_account(conn, user["id"], "secondaire")
    return account_out(conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone())


@router.get("/{account_id}", response_model=Account, responses=errors(401, 403, 404))
def get_account(account_id: int, user=Depends(get_current_user), conn=Depends(get_db)):
    """S7 : Détail d'un compte. Erreurs : compte inexistant ou clôturé (404), compte d'un autre (403)."""
    return account_out(owned_account(conn, user, account_id))


@router.delete("/{account_id}", status_code=204, responses=errors(400, 401, 403, 404))
def close_account(account_id: int, user=Depends(get_current_user), conn=Depends(get_db)):
    """S10 : Clôture un compte : il disparaît de GET /accounts.

    Erreurs : compte principal (400), solde différent de 0 € (400).
    """
    with db.transaction(conn):
        account = owned_account(conn, user, account_id)
        if account["type"] == "principal":
            raise HTTPException(400, "Le compte principal ne peut pas être clôturé")
        if account["balance_cents"] != 0:
            raise HTTPException(
                400, "Le solde doit être de 0 € : faites d'abord un virement vers un autre compte"
            )
        conn.execute("UPDATE accounts SET closed_at = ? WHERE id = ?", (db.now_iso(), account_id))
    return Response(status_code=204)


@router.post(
    "/{account_id}/deposits",
    status_code=201,
    response_model=Transaction,
    responses=errors(400, 401, 403, 404),
)
def deposit(account_id: int, body: DepositIn, user=Depends(get_current_user), conn=Depends(get_db)):
    """S4 : Dépose de l'argent sur le compte. Renvoie la transaction créée (relire le compte pour le solde).

    Erreurs : montant ≤ 0 ou à plus de 2 décimales (400), dépôt supérieur à 10 000 € (400).
    """
    cents = to_cents(body.amount)
    if cents > MAX_DEPOSIT_CENTS:
        raise HTTPException(400, "Dépôt limité à 10 000 € par opération")
    with db.transaction(conn):
        owned_account(conn, user, account_id)
        transaction_id = db.record_transaction(conn, "deposit", cents, None, account_id, "Dépôt")
    return get_transaction(conn, account_id, transaction_id)


@router.get(
    "/{account_id}/transactions", response_model=list[Transaction], responses=errors(401, 403, 404)
)
def list_transactions(account_id: int, user=Depends(get_current_user), conn=Depends(get_db)):
    """S6 : Historique du compte, de la plus récente à la plus ancienne.

    `direction` est calculé pour ce compte : un même virement est un debit pour l'envoyeur
    et un credit pour le destinataire.
    """
    owned_account(conn, user, account_id)
    rows = conn.execute(
        TRANSACTIONS_QUERY + " ORDER BY t.created_at DESC, t.id DESC", {"account": account_id}
    ).fetchall()
    return [transaction_out(row, account_id) for row in rows]


@router.get(
    "/{account_id}/transactions/{transaction_id}",
    response_model=Transaction,
    responses=errors(401, 403, 404),
)
def get_account_transaction(
    account_id: int, transaction_id: int, user=Depends(get_current_user), conn=Depends(get_db)
):
    """S11 : Détail d'une transaction de ce compte.

    Erreurs : compte d'un autre utilisateur (403), transaction inexistante ou qui ne concerne
    pas ce compte (404).
    """
    owned_account(conn, user, account_id)
    return get_transaction(conn, account_id, transaction_id)


@router.get(
    "/{account_id}/statement",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}, "description": "Le relevé au format PDF"},
        **errors(401, 403, 404),
    },
)
def statement(account_id: int, user=Depends(get_current_user), conn=Depends(get_db)):
    """S14 : Relevé du compte en PDF (header `Content-Disposition: attachment`).

    Le token est obligatoire : un simple lien `<a href>` ne suffit pas, il faut un `fetch`
    puis `res.blob()`.
    """
    account = owned_account(conn, user, account_id)
    rows = conn.execute(
        TRANSACTIONS_QUERY + " ORDER BY t.created_at DESC, t.id DESC", {"account": account_id}
    ).fetchall()
    pdf = statement_pdf(
        user["email"], account_out(account), [transaction_out(row, account_id) for row in rows]
    )
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="releve-{account["iban"]}.pdf"'},
    )
