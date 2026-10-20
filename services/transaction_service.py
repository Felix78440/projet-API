from datetime import datetime
from models import Transaction, Account
from database import db


def send_amount(transaction_id: str, sender_id: int, receiver_id: int, amount: float):
    """Fonction appelée par le Timer pour finaliser un transfert après 5 secondes."""
    with db.atomic():  # Transaction SQL pour éviter les incohérences
        try:
            # Vérifie que la transaction existe et est toujours en "pending"
            t = Transaction.get((Transaction.id == transaction_id) & (Transaction.status == "pending"))
            acc1 = Account.get(Account.id == sender_id)
            acc2 = Account.get(Account.id == receiver_id)

            # Crédite le compte receveur
            acc2.solde += amount
            acc2.save()

            # Met à jour le statut de la transaction
            t.status = "completed"
            t.save()
        except (Transaction.DoesNotExist, Account.DoesNotExist):
            pass  # La transaction a déjà été annulée ou complétée
