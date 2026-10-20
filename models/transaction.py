from peewee import *
from datetime import datetime
from .base import BaseModelPeewee
from .account import Account


# Modèle pour les transactions
class Transaction(BaseModelPeewee):
    id = TextField(primary_key=True)  # UUID en texte
    sender = ForeignKeyField(Account, backref='sent_transactions')  # Compte émetteur
    receiver = ForeignKeyField(Account, backref='received_transactions')  # Compte destinataire
    amount = FloatField(null=False)
    status = CharField(max_length=20, null=False)  # pending, completed, cancelled
    timestamp = DateTimeField(default=datetime.now)  # Date de création
