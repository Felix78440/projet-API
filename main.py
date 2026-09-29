from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

#Class

class Account(BaseModel):
    name: str
    solde: float

accounts = {
    1: Account(name="Alice", solde=1000.0),
    2: Account(name="Bob", solde=500.0),
}

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
            acc1.solde -= amount
            acc2.solde += amount
            return {"message": f"Transferred {amount} from {acc1.name} to {acc2.name}", "account1_solde": acc1.solde, "account2_solde": acc2.solde}
        return {"message": "Insufficient funds"}
    return {"message": "Invalid account(s) or amount"}