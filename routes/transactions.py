from fastapi import FastAPI
from models import Transaction


# --- Endpoints GET pour les transactions ---

def register_transaction_routes(app: FastAPI):
    @app.get("/transactions/{transaction_id}")
    def get_account_transaction(transaction_id: str):
        try:
            t = Transaction.get(Transaction.id == transaction_id)
            return {
                "transaction": {
                    "sender_id": t.sender.id,
                    "receiver_id": t.receiver.id,
                    "amount": t.amount,
                    "timestamp": t.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    "status": t.status
                }
            }
        except Transaction.DoesNotExist:
            return {"message": "Transaction not found"}
