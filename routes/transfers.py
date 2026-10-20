from fastapi import FastAPI
import uuid
import threading
from datetime import datetime
from models import Account, Transaction
from services import send_amount


# --- Endpoints POST pour les transferts ---

def register_transfer_routes(app: FastAPI):
    @app.post("/transfer/")
    def envoie(account_id1: int, account_id2: int, amount: float):
        if amount <= 0:
            return {"message": "Amount must be positive"}

        try:
            acc1 = Account.get(Account.id == account_id1)
            acc2 = Account.get(Account.id == account_id2)
        except Account.DoesNotExist:
            return {"message": "Invalid account(s)"}

        if acc1.id == acc2.id:
            return {"message": "Cannot transfer to the same account"}

        if acc1.solde < amount:
            return {"message": "Insufficient funds"}

        # Crée la transaction en "pending"
        transaction_id = str(uuid.uuid4())
        Transaction.create(
            id=transaction_id,
            sender=acc1,
            receiver=acc2,
            amount=amount,
            status="pending",
            timestamp=datetime.now()
        )

        # Débit le compte émetteur
        acc1.solde -= amount
        acc1.save()

        # Planifie la complétion après 5 secondes
        threading.Timer(5.0, send_amount, args=(transaction_id, acc1.id, acc2.id, amount)).start()

        return {
            "message": f"Transfer of {amount} from {acc1.name} to {acc2.name} initiated",
            "transaction_id": transaction_id,
            "new_solde": acc1.solde
        }
