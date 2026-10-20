from fastapi import FastAPI
from models import Account, Transaction


# --- Endpoints GET pour les comptes ---

def register_account_routes(app: FastAPI):
    @app.get("/account/{account_id}")
    def get_account(account_id: int):
        try:
            account = Account.get(Account.id == account_id)
            return {"name": account.name, "solde": account.solde}
        except Account.DoesNotExist:
            return {"message": "Account not found"}

    @app.get("/account/{account_id}/transactions")
    def get_all_account_transactions(account_id: int):
        try:
            # Vérifie que le compte existe
            Account.get(Account.id == account_id)
        except Account.DoesNotExist:
            return {"message": "Account not found"}

        # Récupère toutes les transactions où le compte est sender ou receiver
        transactions = Transaction.select().where(
            (Transaction.sender == account_id) | (Transaction.receiver == account_id)
        ).order_by(Transaction.timestamp.desc())  # Tri par date décroissante

        if not transactions:
            return {"message": "No transactions found for this account"}

        t_list = []
        for t in transactions:
            if t.sender.id == account_id:
                # Transaction sortante (débit)
                t_list.append({
                    "transaction_id": t.id,
                    "type": "debit",
                    "receiver_id": t.receiver.id,
                    "receiver_name": t.receiver.name,
                    "amount": t.amount,
                    "timestamp": t.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    "status": t.status
                })
            else:
                # Transaction entrante (crédit)
                t_list.append({
                    "transaction_id": t.id,
                    "type": "credit",
                    "sender_id": t.sender.id,
                    "sender_name": t.sender.name,
                    "amount": t.amount,
                    "timestamp": t.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    "status": t.status
                })

        return {"transactions": t_list}
