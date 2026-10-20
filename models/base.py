from peewee import *
from database import db


# --- Modèles Peewee (NE PAS CONFONDRE AVEC pydantic.BaseModel) ---
class BaseModelPeewee(Model):
    class Meta:
        database = db
