from fastapi import FastAPI
from datetime import datetime, timedelta
from models import Transaction
from database import db


# --- Endpoints POST pour compléter les transactions ---

def register_complete_routes(app: FastAPI):
    @app.post("/complete/")
    def complete_transaction():
        """Finalise les transactions 'pending' dont le délai de 5 secondes est écoulé."""
        now = datetime.now()
        old_transactions = Transaction.select().where(
            (Transaction.status == "pending") &
            (Transaction.timestamp <= now - timedelta(seconds=5))
        )

        for t in old_transactions:
            with db.atomic():
                # Vérifie que la transaction est toujours en "pending" (au cas où)
                t_reloaded = Transaction.get(Transaction.id == t.id)
                if t_reloaded.status == "pending":
                    t_reloaded.status = "completed"
                    t_reloaded.save()
                    # Crédite le compte receveur
                    receiver = t_reloaded.receiver
                    receiver.solde += t_reloaded.amount
                    receiver.save()

        return {"message": f"Completed {len(old_transactions)} pending transactions"}
