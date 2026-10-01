from sqlite3.dbapi2 import Timestamp
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid
import time
import threading
from peewee import *

# --- Configuration de la base de données ---
db = SqliteDatabase('bdd.db')  # Fichier SQLite

# --- Modèles Peewee (NE PAS CONFONDRE AVEC pydantic.BaseModel) ---
class BaseModelPeewee(Model):
    class Meta:
        database = db

# Modèle pour les comptes
class Account(BaseModelPeewee):
    id = AutoField(primary_key=True)  # Clé primaire auto-incrémentée
    name = CharField(max_length=100, null=False)
    balance = FloatField(default=0.0)

# Modèle pour les transactions
class Transaction(BaseModelPeewee):
    id = TextField(primary_key=True)  # UUID en texte
    sender = ForeignKeyField(Account, backref='sent_transactions')  # Compte émetteur
    receiver = ForeignKeyField(Account, backref='received_transactions')  # Compte destinataire
    amount = FloatField(null=False)
    status = CharField(max_length=20, null=False)  # pending, completed, cancelled
    timestamp = DateTimeField(default=datetime.now)  # Date de création

# Modèle pour les dépôts
class Deposit(BaseModelPeewee):
    id = AutoField(primary_key=True)
    account = ForeignKeyField(Account, backref='deposits')
    amount = FloatField(null=False)
    timestamp = DateTimeField(default=datetime.now)

# --- Initialisation de la BDD ---
def init_db():
    db.connect()
    db.create_tables([Account, Transaction, Deposit], safe=True)  # safe=True évite les erreurs si les tables existent déjà

    # Ajoute les comptes initiaux s'ils n'existent pas
    if not Account.select().where(Account.id == 1).exists():
        Account.create(id=1, name="Enzo", balance=1000.0)
    if not Account.select().where(Account.id == 2).exists():
        Account.create(id=2, name="Bertrand", balance=500.0)
    if not Account.select().where(Account.id == 3).exists():
        Account.create(id=3, name="Charles", balance=200.0)
    print("Database 'bdd.db' successfully initialized !")

accounts = {
    1: Account(id=1, name="Alice", solde=1000.0),
    2: Account(id=2, name="Bob", solde=500.0),
    3: Account(id=3, name="Charlie", solde=200.0)
}

transactions = {}
new_transactions = {}

dépot = []


#Get

@app.get("/account/{account_id}")
def get_account(account_id: int):
    try:
        account = Account.get(Account.id == account_id)
        return {"name": account.name, "balance": account.balance}
    except Account.DoesNotExist:
        return {"message": "Account not found"}

@app.get("/account/{account_id}/transactions")
def get_all_account_transactions(account_id: int):
    if account_id in accounts:
        account_transactions = [(k, t) for k, t in transactions.items() if t["id1"] == account_id or t["id2"] == account_id]
        if account_transactions:
            t_list = []
            for k, t in account_transactions:
                if t["id1"] == account_id:
                    t_list.insert(0, {"transaction_id": k, "type": "debit", "receiver_id": t["id2"], "receiver_name": accounts[t["id2"]].name if t["id2"] in accounts else None, "amount": t["amount"], "timestamp": t["timestamp"], "status": t["status"]})
                else:
                    t_list.insert(0, {"transaction_id": k, "type": "credit", "sender_id": t["id1"], "sender_name": accounts[t["id1"]].name if t["id1"] in accounts else None, "amount": t["amount"], "timestamp": t["timestamp"], "status": t["status"]})
            return {"transactions": t_list}
        return {"message": "No transactions found for this account"}
    return {"message": "Account not found"}

@app.get("/transactions/{transaction_id}")
def get_account_transaction(transaction_id: str):
    if transaction_id in transactions.keys():
        return {"transaction": {"sender_id": transactions[transaction_id]["id1"], "receiver_id": transactions[transaction_id]["id2"], "amount": transactions[transaction_id]["amount"], "timestamp": transactions[transaction_id]["timestamp"], "status": transactions[transaction_id]["status"]}}
    return {"message": "Transaction not found"}

#Post

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

    if acc1.balance < amount:
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
    acc1.balance -= amount
    acc1.save()

    # Planifie la complétion après 5 secondes
    threading.Timer(5.0, send_amount, args=(transaction_id, acc1.id, acc2.id, amount)).start()

    return {
        "message": f"Transfer of {amount} from {acc1.name} to {acc2.name} initiated",
        "transaction_id": transaction_id,
        "new_balance": acc1.balance
    }

def send_amount(transaction_id: str, sender_id: int, receiver_id: int, amount: float):
    """Fonction appelée par le Timer pour finaliser un transfert après 5 secondes."""
    with db.atomic():  # Transaction SQL pour éviter les incohérences
        try:
            # Vérifie que la transaction existe et est toujours en "pending"
            t = Transaction.get((Transaction.id == transaction_id) & (Transaction.status == "pending"))
            acc1 = Account.get(Account.id == sender_id)
            acc2 = Account.get(Account.id == receiver_id)

            # Crédite le compte receveur
            acc2.balance += amount
            acc2.save()

            # Met à jour le statut de la transaction
            t.status = "completed"
            t.save()
        except (Transaction.DoesNotExist, Account.DoesNotExist):
            pass  # La transaction a déjà été annulée ou complétée

@app.post("/deposit/")
def depot(account_id: int, amount: float):
    if amount <= 0:
        return {"message": "Invalid amount"}

    try:
        acc = Account.get(Account.id == account_id)
    except Account.DoesNotExist:
        return {"message": "Invalid account"}

    # Ajoute le montant au balance
    acc.balance += amount
    acc.save()

    # Enregistre le dépôt dans l'historique
    Deposit.create(account=acc, amount=amount, timestamp=datetime.now())

    return {
        "message": f"Deposited {amount} to {acc.name}'s account",
        "new_balance": acc.balance
    }

@app.post("/transactions/{transaction_id}/cancel")
def cancel_transaction(transaction_id: str):
    """Annule une transaction en attente et rend les fonds au compte émetteur."""
    with db.atomic():
        try:
            t = Transaction.get((Transaction.id == transaction_id) & (Transaction.status == "pending"))
            sender = t.sender

            # Annule la transaction : crédite le compte émetteur
            sender.balance += t.amount
            sender.save()

            # Met à jour le statut
            t.status = "cancelled"
            t.save()

            return {"message": f"Transaction {transaction_id} canceled"}
        except Transaction.DoesNotExist:
            return {"message": "Transaction not found or already completed"}