from peewee import *
from datetime import datetime

# --- Configuration de la base de données ---
db = SqliteDatabase('bdd.db')  # Fichier SQLite


# --- Initialisation de la BDD ---
def init_db():
    from models import Account, Transaction, Deposit
    
    db.connect()
    db.create_tables([Account, Transaction, Deposit], safe=True)  # safe=True évite les erreurs si les tables existent déjà

    # Ajoute les comptes initiaux s'ils n'existent pas
    if not Account.select().where(Account.id == 1).exists():
        Account.create(id=1, name="Enzo", solde=1000.0)
    if not Account.select().where(Account.id == 2).exists():
        Account.create(id=2, name="Bertrand", solde=500.0)
    if not Account.select().where(Account.id == 3).exists():
        Account.create(id=3, name="Charles", solde=200.0)
    print("Base de données 'bdd.db' initialisée avec succès !")
