"""Ce que partagent les routes : connexion à la base, utilisateur connecté, montants, conversions."""

import math
from decimal import Decimal

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import db
from .schemas import Account, ErrorMessage, Transaction

bearer = HTTPBearer(auto_error=False, description="Le accessToken renvoyé par POST /auth/login")

ERROR_DESCRIPTIONS = {
    400: "Données invalides ou opération refusée",
    401: "Token absent, invalide ou expiré",
    403: "La ressource appartient à un autre utilisateur",
    404: "Ressource introuvable",
    409: "Doublon",
}


def errors(*codes: int) -> dict:
    """Documente dans /docs les erreurs possibles d'une route, toutes au format { "message": … }."""
    return {code: {"model": ErrorMessage, "description": ERROR_DESCRIPTIONS[code]} for code in codes}


def get_db():
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    conn=Depends(get_db),
):
    headers = {"WWW-Authenticate": "Bearer"}
    if credentials is None:
        raise HTTPException(401, "Non authentifié : header « Authorization: Bearer <token> » manquant", headers)
    user = conn.execute(
        "SELECT users.* FROM tokens JOIN users ON users.id = tokens.user_id"
        " WHERE tokens.token = ? AND tokens.expires_at > ?",
        (credentials.credentials, db.now_iso()),
    ).fetchone()
    if user is None:
        raise HTTPException(401, "Token invalide ou expiré : reconnectez-vous", headers)
    return user


def owned_account(conn, user, account_id: int):
    """Le compte ouvert `account_id`, s'il appartient à l'utilisateur ; sinon 404 ou 403."""
    account = conn.execute(
        "SELECT * FROM accounts WHERE id = ? AND closed_at IS NULL", (account_id,)
    ).fetchone()
    if account is None:
        raise HTTPException(404, "Compte introuvable")
    if account["user_id"] != user["id"]:
        raise HTTPException(403, "Ce compte ne vous appartient pas")
    return account


def to_cents(amount: float) -> int:
    """12.5 → 1250. En base, les montants sont des entiers (centimes) : pas d'erreur d'arrondi."""
    if not math.isfinite(amount) or amount <= 0:
        raise HTTPException(400, "Le montant doit être supérieur à 0")
    value = Decimal(str(amount))
    if value.as_tuple().exponent < -2:
        raise HTTPException(400, "Le montant ne peut pas avoir plus de 2 décimales")
    return int(value * 100)


def account_out(row) -> Account:
    return Account(
        id=row["id"],
        iban=row["iban"],
        type=row["type"],
        balance=row["balance_cents"] / 100,
        createdAt=row["created_at"],
    )


TRANSACTIONS_QUERY = """
SELECT t.*, source.iban AS from_iban, target.iban AS to_iban
FROM transactions t
LEFT JOIN accounts source ON source.id = t.from_account_id
JOIN accounts target ON target.id = t.to_account_id
WHERE (t.from_account_id = :account OR t.to_account_id = :account)
"""


def transaction_out(row, account_id: int) -> Transaction:
    return Transaction(
        id=row["id"],
        accountId=account_id,
        kind=row["kind"],
        direction="debit" if row["from_account_id"] == account_id else "credit",
        amount=row["amount_cents"] / 100,
        label=row["label"],
        fromIban=row["from_iban"],
        toIban=row["to_iban"],
        createdAt=row["created_at"],
    )


def get_transaction(conn, account_id: int, transaction_id: int) -> Transaction:
    row = conn.execute(
        TRANSACTIONS_QUERY + " AND t.id = :id", {"account": account_id, "id": transaction_id}
    ).fetchone()
    if row is None:
        raise HTTPException(404, "Transaction introuvable sur ce compte")
    return transaction_out(row, account_id)
