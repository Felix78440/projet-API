from pydantic import BaseModel


# --- Schéma Pydantic pour les réponses (optionnel mais utile) ---
class AccountResponse(BaseModel):
    name: str
    solde: float
