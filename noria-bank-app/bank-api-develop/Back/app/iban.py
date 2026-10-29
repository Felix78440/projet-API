"""IBAN : génération de numéros français valides et vérification (clé modulo 97)."""

import random
import re

# Banque et guichet fictifs : tous les comptes de l'API partagent ces codes
BANK_CODE = "99999"
BRANCH_CODE = "00001"

IBAN_FORMAT = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$")


def _to_digits(text: str) -> int:
    # Chaque lettre devient un nombre : A = 10, B = 11, … Z = 35
    return int("".join(str(int(char, 36)) for char in text))


def _rib_key(bank: str, branch: str, account: str) -> str:
    return f"{97 - (89 * int(bank) + 15 * int(branch) + 3 * int(account)) % 97:02d}"


def generate(rng: random.Random | None = None) -> str:
    rng = rng or random.Random()
    account = f"{rng.randrange(10**11):011d}"
    bban = BANK_CODE + BRANCH_CODE + account + _rib_key(BANK_CODE, BRANCH_CODE, account)
    check = 98 - _to_digits(bban + "FR00") % 97
    return f"FR{check:02d}{bban}"


def normalize(value: str) -> str:
    """« fr76 9999 … » → « FR769999… » : sans espaces, en majuscules."""
    return re.sub(r"\s+", "", value).upper()


def is_valid(iban: str) -> bool:
    """Format (2 lettres, 2 chiffres, 11 à 30 caractères) et clé de contrôle."""
    if not IBAN_FORMAT.match(iban):
        return False
    return _to_digits(iban[4:] + iban[:4]) % 97 == 1
