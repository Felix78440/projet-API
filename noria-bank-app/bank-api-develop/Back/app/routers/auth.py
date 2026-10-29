import re

from fastapi import APIRouter, Depends, HTTPException, Response

from .. import db
from ..deps import bearer, errors, get_current_user, get_db
from ..schemas import Credentials, LoginResponse, User
from ..security import verify_password

router = APIRouter(prefix="/auth", tags=["Authentification"])

EMAIL_FORMAT = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def user_out(row) -> User:
    return User(id=row["id"], email=row["email"], createdAt=row["created_at"])


def login_response(conn, user_id: int, token: str) -> LoginResponse:
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return LoginResponse(accessToken=token, user=user_out(user))


@router.post("/register", status_code=201, response_model=LoginResponse, responses=errors(400, 409))
def register(body: Credentials, conn=Depends(get_db)):
    """S1 : Crée l'utilisateur et son **compte principal** (solde 0 €), puis le connecte.

    Erreurs : email au mauvais format (400), mot de passe de moins de 8 caractères (400),
    email déjà utilisé (409).
    """
    email = body.email.strip().lower()
    if not EMAIL_FORMAT.match(email):
        raise HTTPException(400, "Format d'email invalide")
    if len(body.password) < 8:
        raise HTTPException(400, "Le mot de passe doit contenir au moins 8 caractères")
    with db.transaction(conn):
        if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            raise HTTPException(409, "Cet email est déjà utilisé")
        user_id = db.create_user(conn, email, body.password)
        db.open_account(conn, user_id, "principal")
        token = db.create_token(conn, user_id)
    return login_response(conn, user_id, token)


@router.post("/login", response_model=LoginResponse, responses=errors(400, 401))
def login(body: Credentials, conn=Depends(get_db)):
    """S2 : Renvoie un `accessToken`, à envoyer ensuite dans le header `Authorization: Bearer <token>`.

    Le token expire au bout de 24 h (401 ensuite). Erreur : identifiants incorrects (401).
    """
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (body.email.strip().lower(),)
    ).fetchone()
    if user is None or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "Email ou mot de passe incorrect")
    with db.transaction(conn):
        token = db.create_token(conn, user["id"])
    return login_response(conn, user["id"], token)


@router.get("/me", response_model=User, responses=errors(401))
def me(user=Depends(get_current_user)):
    """S3 : L'utilisateur connecté."""
    return user_out(user)


@router.post("/logout", status_code=204, responses=errors(401))
def logout(user=Depends(get_current_user), credentials=Depends(bearer), conn=Depends(get_db)):
    """Invalide le token côté serveur (facultatif : supprimer le token côté front suffit)."""
    with db.transaction(conn):
        conn.execute("DELETE FROM tokens WHERE token = ?", (credentials.credentials,))
    return Response(status_code=204)
