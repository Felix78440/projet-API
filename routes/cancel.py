from fastapi import FastAPI
from models import Transaction
from database import db


# --- Endpoints POST pour annuler les transactions ---

def register_cancel_routes(app: FastAPI):
    @app.post("/transactions/{transaction_id}/cancel")
    def cancel_transaction(transaction_id: str):
        """Annule une transaction en attente et rend les fonds au compte émetteur."""
        with db.atomic():
            try:
                t = Transaction.get((Transaction.id == transaction_id) & (Transaction.status == "pending"))
                sender = t.sender

                # Annule la transaction : crédite le compte émetteur
                sender.solde += t.amount
                sender.save()

                # Met à jour le statut
                t.status = "cancelled"
                t.save()

                return {"message": f"Transaction {transaction_id} canceled"}
            except Transaction.DoesNotExist:
                return {"message": "Transaction not found or already completed"}
