"""Formats JSON échangés avec le front (affichés dans la documentation /docs).

Les noms de champs sont en camelCase, comme en JavaScript.
Les montants sont des nombres en euros (12.5 = 12,50 €) ; les dates des strings ISO 8601 en UTC.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ErrorMessage(BaseModel):
    message: str = Field(examples=["Solde insuffisant"])


class Credentials(BaseModel):
    email: str = Field(examples=["alice@banque.fr"])
    password: str = Field(examples=["alice1234"])


class User(BaseModel):
    id: int
    email: str
    createdAt: str = Field(examples=["2026-09-01T08:00:00Z"])


class LoginResponse(BaseModel):
    accessToken: str
    user: User


class Account(BaseModel):
    id: int
    iban: str = Field(examples=["FR7699999000010123456789012"])
    type: Literal["principal", "secondaire"]
    balance: float = Field(examples=[2052.5])
    createdAt: str


class DepositIn(BaseModel):
    amount: float = Field(examples=[50])


class TransferIn(BaseModel):
    fromAccountId: int = Field(examples=[1])
    toIban: str = Field(examples=["FR76 9999 9000 0101 2345 6789 012"])
    amount: float = Field(examples=[42.5])
    label: str | None = Field(default=None, examples=["Loyer"])


class Transaction(BaseModel):
    """Une opération, vue depuis le compte `accountId`."""

    id: int
    accountId: int
    kind: Literal["deposit", "transfer"]
    direction: Literal["credit", "debit"] = Field(
        description="credit : l'argent entre sur `accountId` ; debit : il en sort"
    )
    amount: float = Field(description="Toujours positif ; le sens est donné par `direction`")
    label: str
    fromIban: str | None = Field(description="null pour un dépôt")
    toIban: str
    createdAt: str


class BeneficiaryIn(BaseModel):
    name: str = Field(examples=["Bob Martin"])
    iban: str = Field(examples=["FR76 9999 9000 0101 2345 6789 012"])


class Beneficiary(BaseModel):
    id: int
    name: str
    iban: str
    createdAt: str
