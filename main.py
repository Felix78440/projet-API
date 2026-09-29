from sqlite3.dbapi2 import Timestamp

from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime


app = FastAPI()

#Class

class Account(BaseModel):
    name: str
    solde: float
    transactions: list = []

accounts = {
    1: Account(name="Alice", solde=1000.0),
    2: Account(name="Bob", solde=500.0),
}


dépot = []
#Get

@app.get("/account/{account_id}")
def get_account(account_id: int):
    return accounts.get(account_id)

#Post

@app.post("/account/transfer/")
def envoie(account_id1: int, account_id2: int, amount: float):
    acc1 = accounts.get(account_id1)
    acc2 = accounts.get(account_id2)
    if acc1 and acc2 and acc1 != acc2 and amount > 0:
        if acc1.solde >= amount:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            acc1.solde -= amount
            acc2.solde += amount
            acc1.transactions.insert(0, {"to": acc2.name, "amount": amount, "timestamp": timestamp})
            acc2.transactions.insert(0, {"from": acc1.name, "amount": amount, "timestamp": timestamp})
            return {"message": f"Transferred {amount} from {acc1.name} to {acc2.name}", "account1_solde": acc1.solde, "account2_solde": acc2.solde, "account1_transactions": acc1.transactions, "account2_transactions": acc2.transactions}
        return {"message": "Insufficient funds"}
    return {"message": "Invalid account(s) or amount"}

@app.post("/account/deposit/")
def depot(account_id: int, amount: float):
    acc = accounts.get(account_id)
    if acc and amount > 0:
        acc.solde += amount
        dépot.append({"account_id": account_id, "amount": amount})
        return {"message": f"Deposited {amount} to {acc.name}'s account", "new_solde": acc.solde, "depot_history": dépot}
    return {"message": "Invalid account or amount"}