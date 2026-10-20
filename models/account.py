from peewee import *
from .base import BaseModelPeewee


# Modèle pour les comptes
class Account(BaseModelPeewee):
    id = AutoField(primary_key=True)  # Clé primaire auto-incrémentée
    name = CharField(max_length=100, null=False)
    solde = FloatField(default=0.0)
