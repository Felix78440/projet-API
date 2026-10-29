"""Base SQLite : schéma, connexion, écritures communes et données de démonstration.

Remise à zéro : python -m app.db reset
"""

import os
import random
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import iban as iban_utils
from .security import hash_password, new_token

DEFAULT_DB = Path(__file__).resolve().parent.parent / "bank.db"
TOKEN_TTL_MINUTES = int(os.environ.get("TOKEN_TTL_MINUTES", 24 * 60))

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tokens (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    iban TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL CHECK (type IN ('principal', 'secondaire')),
    balance_cents INTEGER NOT NULL DEFAULT 0 CHECK (balance_cents >= 0),
    created_at TEXT NOT NULL,
    closed_at TEXT
);
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL CHECK (kind IN ('deposit', 'transfer')),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    from_account_id INTEGER REFERENCES accounts(id),
    to_account_id INTEGER NOT NULL REFERENCES accounts(id),
    label TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS beneficiaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    iban TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (user_id, iban)
);
"""


def db_path() -> Path:
    return Path(os.environ.get("BANK_DB", DEFAULT_DB))


def now_iso(moment: datetime | None = None) -> str:
    """Date ISO 8601 en UTC, à la seconde : « 2026-10-25T14:30:00Z »."""
    return (moment or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect() -> sqlite3.Connection:
    # isolation_level=None : les transactions sont ouvertes explicitement (voir transaction())
    conn = sqlite3.connect(db_path(), timeout=5, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection):
    """Tout ou rien : une erreur (HTTPException comprise) annule les écritures du bloc.

    BEGIN IMMEDIATE verrouille la base dès le début : deux virements simultanés
    ne peuvent pas lire le même solde.
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    conn.execute("COMMIT")


def create_user(conn, email: str, password: str, at: str | None = None) -> int:
    cursor = conn.execute(
        "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
        (email, hash_password(password), at or now_iso()),
    )
    return cursor.lastrowid


def create_token(conn, user_id: int) -> str:
    token = new_token()
    expires = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES)
    conn.execute(
        "INSERT INTO tokens (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, now_iso(expires)),
    )
    return token


def open_account(conn, user_id: int, account_type: str, at: str | None = None, rng=None) -> int:
    while True:
        iban = iban_utils.generate(rng)
        if not conn.execute("SELECT 1 FROM accounts WHERE iban = ?", (iban,)).fetchone():
            break
    cursor = conn.execute(
        "INSERT INTO accounts (user_id, iban, type, created_at) VALUES (?, ?, ?, ?)",
        (user_id, iban, account_type, at or now_iso()),
    )
    return cursor.lastrowid


def record_transaction(conn, kind, amount_cents, from_id, to_id, label, at=None) -> int:
    """Écrit l'opération et met à jour les soldes. Les vérifications sont faites avant l'appel."""
    if from_id is not None:
        conn.execute(
            "UPDATE accounts SET balance_cents = balance_cents - ? WHERE id = ?",
            (amount_cents, from_id),
        )
    conn.execute(
        "UPDATE accounts SET balance_cents = balance_cents + ? WHERE id = ?",
        (amount_cents, to_id),
    )
    cursor = conn.execute(
        "INSERT INTO transactions (kind, amount_cents, from_account_id, to_account_id, label, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (kind, amount_cents, from_id, to_id, label, at or now_iso()),
    )
    return cursor.lastrowid


def seed(conn) -> None:
    """Deux clients de démonstration, avec un historique daté des dernières semaines."""
    rng = random.Random(2026)  # mêmes IBAN à chaque remise à zéro
    now = datetime.now(timezone.utc).replace(microsecond=0)

    def ago(days: int) -> str:
        return now_iso(now - timedelta(days=days))

    with transaction(conn):
        alice = create_user(conn, "alice@banque.fr", "alice1234", ago(60))
        bob = create_user(conn, "bob@banque.fr", "bob12345", ago(45))
        alice_main = open_account(conn, alice, "principal", ago(60), rng)
        bob_main = open_account(conn, bob, "principal", ago(45), rng)
        alice_savings = open_account(conn, alice, "secondaire", ago(30), rng)

        record_transaction(conn, "deposit", 250_000, None, alice_main, "Dépôt", ago(59))
        record_transaction(conn, "deposit", 120_000, None, bob_main, "Dépôt", ago(44))
        record_transaction(conn, "transfer", 50_000, alice_main, alice_savings, "Épargne", ago(29))
        record_transaction(conn, "transfer", 4_250, alice_main, bob_main, "Restaurant", ago(12))
        record_transaction(conn, "transfer", 1_500, bob_main, alice_main, "Remboursement cinéma", ago(5))
        record_transaction(conn, "deposit", 8_000, None, alice_main, "Dépôt", ago(2))

        bob_iban = conn.execute("SELECT iban FROM accounts WHERE id = ?", (bob_main,)).fetchone()[0]
        conn.execute(
            "INSERT INTO beneficiaries (user_id, name, iban, created_at) VALUES (?, ?, ?, ?)",
            (alice, "Bob Martin", bob_iban, ago(12)),
        )


def init_db() -> None:
    """Crée les tables si besoin ; ajoute les données de démonstration si la base est vide."""
    conn = connect()
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA)
        if not conn.execute("SELECT 1 FROM users").fetchone():
            seed(conn)
    finally:
        conn.close()


def reset_db() -> None:
    path = db_path()
    for suffix in ("", "-wal", "-shm"):
        Path(f"{path}{suffix}").unlink(missing_ok=True)
    init_db()


if __name__ == "__main__":
    if sys.argv[1:] == ["reset"]:
        reset_db()
        print(f"Base remise à zéro : {db_path()}")
    else:
        print("Usage : python -m app.db reset")
