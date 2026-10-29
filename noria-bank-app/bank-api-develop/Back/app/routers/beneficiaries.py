from fastapi import APIRouter, Depends, HTTPException, Response

from .. import db
from .. import iban as iban_utils
from ..deps import errors, get_current_user, get_db
from ..schemas import Beneficiary, BeneficiaryIn

router = APIRouter(prefix="/beneficiaries", tags=["Bénéficiaires"])


def beneficiary_out(row) -> Beneficiary:
    return Beneficiary(id=row["id"], name=row["name"], iban=row["iban"], createdAt=row["created_at"])


@router.get("", response_model=list[Beneficiary], responses=errors(401))
def list_beneficiaries(user=Depends(get_current_user), conn=Depends(get_db)):
    """S12 : Mes bénéficiaires, du plus récent au plus ancien."""
    rows = conn.execute(
        "SELECT * FROM beneficiaries WHERE user_id = ? ORDER BY created_at DESC, id DESC",
        (user["id"],),
    ).fetchall()
    return [beneficiary_out(row) for row in rows]


@router.post("", status_code=201, response_model=Beneficiary, responses=errors(400, 401, 404, 409))
def add_beneficiary(body: BeneficiaryIn, user=Depends(get_current_user), conn=Depends(get_db)):
    """S13, S15 : Ajoute un bénéficiaire : l'IBAN doit être celui d'un compte ouvert de la banque.

    Erreurs : nom vide (400), IBAN invalide (400), son propre compte (400),
    aucun compte avec cet IBAN (404), bénéficiaire déjà enregistré (409).
    """
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Le nom du bénéficiaire est obligatoire")
    if len(name) > 100:
        raise HTTPException(400, "Le nom ne doit pas dépasser 100 caractères")
    iban = iban_utils.normalize(body.iban)
    if not iban_utils.is_valid(iban):
        raise HTTPException(400, "IBAN invalide")

    with db.transaction(conn):
        account = conn.execute(
            "SELECT * FROM accounts WHERE iban = ? AND closed_at IS NULL", (iban,)
        ).fetchone()
        if account is None:
            raise HTTPException(404, "Aucun compte ouvert avec cet IBAN")
        if account["user_id"] == user["id"]:
            raise HTTPException(400, "Vous ne pouvez pas ajouter votre propre compte")
        if conn.execute(
            "SELECT 1 FROM beneficiaries WHERE user_id = ? AND iban = ?", (user["id"], iban)
        ).fetchone():
            raise HTTPException(409, "Ce bénéficiaire est déjà enregistré")
        cursor = conn.execute(
            "INSERT INTO beneficiaries (user_id, name, iban, created_at) VALUES (?, ?, ?, ?)",
            (user["id"], name, iban, db.now_iso()),
        )
    row = conn.execute("SELECT * FROM beneficiaries WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return beneficiary_out(row)


@router.delete("/{beneficiary_id}", status_code=204, responses=errors(401, 404))
def delete_beneficiary(beneficiary_id: int, user=Depends(get_current_user), conn=Depends(get_db)):
    """Supprime un de mes bénéficiaires (hors stories, utile pour les tests)."""
    with db.transaction(conn):
        cursor = conn.execute(
            "DELETE FROM beneficiaries WHERE id = ? AND user_id = ?", (beneficiary_id, user["id"])
        )
        if cursor.rowcount == 0:
            raise HTTPException(404, "Bénéficiaire introuvable")
    return Response(status_code=204)
