"""API de la banque en ligne, projet BackFrontDevops (Sprint Front, ESIEE-IT L2).

Lancement : uvicorn app.main:app --reload --port 8000
Documentation : http://localhost:8000/docs
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import db
from .routers import accounts, auth, beneficiaries, transfers

DESCRIPTION = """
API REST de la banque en ligne. Toutes les réponses sont en JSON (sauf le relevé PDF).

**Comptes de test** : `alice@banque.fr` / `alice1234` · `bob@banque.fr` / `bob12345`

**Authentification** : `POST /auth/login` renvoie un `accessToken`. Les autres routes
(sauf `/auth/register`) l'attendent dans le header `Authorization: Bearer <token>`.
Dans cette page : bouton **Authorize**, puis collez le token.

**Erreurs** : toujours `{ "message": "…" }`, avec le statut 400, 401, 403, 404 ou 409.

**Montants** : nombres en euros (`12.5` = 12,50 €), 2 décimales au maximum.
**Dates** : strings ISO 8601 en UTC (`"2026-10-25T14:30:00Z"`).
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(
    title="API Banque en ligne",
    description=DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
)

# Le proxy Vite évite CORS ; ces origines permettent aussi d'appeler l'API directement
origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

STARLETTE_MESSAGES = {"Not Found": "Route introuvable", "Method Not Allowed": "Méthode non autorisée"}


@app.exception_handler(StarletteHTTPException)
async def http_error(request, exc: StarletteHTTPException):
    """Toutes les erreurs au même format : { "message": … } (lu par le helper api() du front)."""
    message = STARLETTE_MESSAGES.get(exc.detail, exc.detail)
    return JSONResponse({"message": message}, status_code=exc.status_code, headers=exc.headers)


def validation_message(error: dict) -> str:
    location, kind = error["loc"], error["type"]
    if kind == "json_invalid":
        return "Corps de la requête invalide : JSON attendu"
    if location == ("body",):
        return "Corps de la requête manquant : JSON attendu (header Content-Type: application/json)"
    field = location[-1]
    if kind == "missing":
        return f"Le champ « {field} » est obligatoire"
    if kind.startswith(("float", "int")):
        return f"Le champ « {field} » doit être un nombre"
    if kind.startswith("string"):
        return f"Le champ « {field} » doit être une chaîne de caractères"
    return f"Le champ « {field} » est invalide"


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc: RequestValidationError):
    """FastAPI répond 422 avec une liste d'erreurs en anglais ; on renvoie 400 et un message lisible."""
    return JSONResponse({"message": validation_message(exc.errors()[0])}, status_code=400)


@app.get("/", include_in_schema=False)
def root():
    return {"message": "API Banque en ligne, documentation sur /docs"}


app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(transfers.router)
app.include_router(beneficiaries.router)
