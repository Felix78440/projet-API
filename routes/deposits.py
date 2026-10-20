from fastapi import FastAPI
from datetime import datetime
from models import Account, Deposit


# --- Endpoints POST pour les dépôts ---

def register_deposit_routes(app: FastAPI):
    @app.post("/deposit/")
    def depot(account_id: int, amount: float):
        if amount <= 0:
            return {"message": "Invalid amount"}

        try:
            acc = Account.get(Account.id == account_id)
        except Account.DoesNotExist:
            return {"message": "Invalid account"}

        # Ajoute le montant au solde
        acc.solde += amount
        acc.save()

        # Enregistre le dépôt dans l'historique
        Deposit.create(account=acc, amount=amount, timestamp=datetime.now())

        return {
            "message": f"Deposited {amount} to {acc.name}'s account",
            "new_solde": acc.solde
        }
