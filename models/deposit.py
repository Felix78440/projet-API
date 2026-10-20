from peewee import *
from datetime import datetime
from .base import BaseModelPeewee
from .account import Account


# Modèle pour les dépôts
class Deposit(BaseModelPeewee):
    id = AutoField(primary_key=True)
    account = ForeignKeyField(Account, backref='deposits')
    amount = FloatField(null=False)
    timestamp = DateTimeField(default=datetime.now)
