from fastapi import FastAPI
from database import init_db
from routes import (
    register_account_routes,
    register_transaction_routes,
    register_transfer_routes,
    register_deposit_routes,
    register_complete_routes,
    register_cancel_routes
)


# --- Application FastAPI ---
app = FastAPI()


# Initialisation de la BDD au démarrage
init_db()


# Enregistrement des routes
register_account_routes(app)
register_transaction_routes(app)
register_transfer_routes(app)
register_deposit_routes(app)
register_complete_routes(app)
register_cancel_routes(app)
