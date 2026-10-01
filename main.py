from sqlite3.dbapi2 import Timestamp
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid
import time
import threading

app = FastAPI()

#Class

class Account(BaseModel):
    id: int
    name: str
    solde: float

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
    account = accounts.get(account_id)
    if account:
        return {"name": account.name, "solde": account.solde}
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
    acc1 = accounts.get(account_id1)
    acc2 = accounts.get(account_id2)
    if acc1 and acc2 and acc1 != acc2 and amount > 0:
        if acc1.solde >= amount:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            transaction_id = str(uuid.uuid4())
            new_transactions[transaction_id] = {"id1": acc1.id, "id2": acc2.id, "amount": amount, "timestamp": timestamp, "status": "pending"}
            acc1.solde -= amount
            threading.Timer(5.0, send_amount, args=(transaction_id, acc1, acc2, amount)).start()
            return {"message": f"Transfer of {amount} from {acc1.name} to {acc2.name} initiated", "transaction_id": transaction_id, "new_solde": acc1.solde}
        return {"message": "Insufficient funds"}
    return {"message": "Invalid account(s) or amount"}

def send_amount(transaction_id, acc1, acc2, amount):
    if transaction_id in new_transactions:
        acc2.solde += amount
        transactions[transaction_id] = new_transactions[transaction_id]
        del new_transactions[transaction_id]

    

@app.post("/deposit/")
def depot(account_id: int, amount: float):
    acc = accounts.get(account_id)
    if acc and amount > 0:
        acc.solde += amount
        dépot.append({"account_id": account_id, "amount": amount})
        return {"message": f"Deposited {amount} to {acc.name}'s account", "new_solde": acc.solde, "depot_history": dépot}
    return {"message": "Invalid account or amount"}

@app.post("/complete/")
def complete_transaction():
    tmp = []
    for k, v in new_transactions.items():
        if datetime.now() - datetime.fromisoformat(v["timestamp"]) >= timedelta(seconds=5):
            transactions[k] = new_transactions[k]
            transactions[k]["status"] = "completed"
            tmp.append(k)
    for k in tmp:
        del new_transactions[k]

@app.post("/transactions/{transaction_id}/cancel")
def cancel_transaction(transaction_id: str):
    if transaction_id in new_transactions:
        acc = new_transactions[transaction_id]["id1"]
        amount = new_transactions[transaction_id]["amount"]
        accounts[acc].solde += amount
        del new_transactions[transaction_id]
        return {"message": f"Transaction {transaction_id} canceled"}
    return {"message": "Transaction not found or already completed"}