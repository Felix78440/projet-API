"""Un scénario par story : python -m pytest"""

import pytest
from fastapi.testclient import TestClient

from app import iban
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("BANK_DB", str(tmp_path / "test.db"))
    with TestClient(app) as test_client:  # le lifespan crée la base et les données de démo
        yield test_client


def login(client, email="alice@banque.fr", password="alice1234"):
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.json()
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


def accounts(client, headers):
    return client.get("/accounts", headers=headers).json()


def principal(client, headers):
    return next(a for a in accounts(client, headers) if a["type"] == "principal")


def test_s1_register(client):
    res = client.post("/auth/register", json={"email": "Chloe@Banque.fr", "password": "chloe1234"})
    assert res.status_code == 201
    body = res.json()
    assert body["user"]["email"] == "chloe@banque.fr"
    headers = {"Authorization": f"Bearer {body['accessToken']}"}
    [account] = accounts(client, headers)
    assert account["type"] == "principal" and account["balance"] == 0

    assert client.post("/auth/register", json={"email": "chloe@banque.fr", "password": "x" * 8}).status_code == 409
    res = client.post("/auth/register", json={"email": "pas-un-email", "password": "x" * 8})
    assert res.status_code == 400 and res.json() == {"message": "Format d'email invalide"}
    assert client.post("/auth/register", json={"email": "d@banque.fr", "password": "court"}).status_code == 400


def test_s2_login_and_protected_routes(client):
    res = client.post("/auth/login", json={"email": "alice@banque.fr", "password": "faux"})
    assert res.status_code == 401 and res.json()["message"] == "Email ou mot de passe incorrect"
    assert client.get("/accounts").status_code == 401
    assert client.get("/accounts", headers={"Authorization": "Bearer inconnu"}).status_code == 401

    headers = login(client)
    assert client.get("/auth/me", headers=headers).json()["email"] == "alice@banque.fr"
    assert client.post("/auth/logout", headers=headers).status_code == 204
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_s3_s9_accounts_sorted_newest_first(client):
    headers = login(client)
    data = accounts(client, headers)
    assert [a["type"] for a in data] == ["secondaire", "principal"]
    assert sum(a["balance"] for a in data) == 2552.5
    assert all(iban.is_valid(a["iban"]) for a in data)


def test_s4_deposit(client):
    headers = login(client)
    account = principal(client, headers)
    res = client.post(f"/accounts/{account['id']}/deposits", json={"amount": 49.99}, headers=headers)
    assert res.status_code == 201
    assert res.json()["direction"] == "credit" and res.json()["fromIban"] is None
    assert client.get(f"/accounts/{account['id']}", headers=headers).json()["balance"] == 2102.49

    for amount, message in [(0, "supérieur à 0"), (-5, "supérieur à 0"), (1.234, "2 décimales"), (20_000, "10 000")]:
        res = client.post(f"/accounts/{account['id']}/deposits", json={"amount": amount}, headers=headers)
        assert res.status_code == 400 and message in res.json()["message"]
    res = client.post(f"/accounts/{account['id']}/deposits", json={"amount": "abc"}, headers=headers)
    assert res.status_code == 400 and res.json()["message"] == "Le champ « amount » doit être un nombre"


def test_s5_transfer(client):
    alice = login(client)
    bob = login(client, "bob@banque.fr", "bob12345")
    source = principal(client, alice)
    target = principal(client, bob)

    spaced = " ".join(target["iban"][i : i + 4] for i in range(0, 27, 4)).lower()
    res = client.post(
        "/transfers",
        json={"fromAccountId": source["id"], "toIban": spaced, "amount": 100, "label": "Loyer"},
        headers=alice,
    )
    assert res.status_code == 201
    assert res.json()["direction"] == "debit" and res.json()["label"] == "Loyer"
    assert principal(client, alice)["balance"] == source["balance"] - 100
    assert principal(client, bob)["balance"] == target["balance"] + 100

    def attempt(**changes):
        body = {"fromAccountId": source["id"], "toIban": target["iban"], "amount": 10} | changes
        return client.post("/transfers", json=body, headers=alice)

    assert attempt(amount=1_000_000).json() == {"message": "Solde insuffisant"}
    assert attempt(toIban="FR00 1234").status_code == 400
    assert attempt(toIban=iban.generate()).status_code == 404
    assert attempt(toIban=source["iban"]).status_code == 400
    assert attempt(fromAccountId=target["id"]).status_code == 403
    assert attempt(fromAccountId=999).status_code == 404


def test_s6_s11_history_direction_depends_on_account(client):
    alice = login(client)
    bob = login(client, "bob@banque.fr", "bob12345")
    alice_main = principal(client, alice)
    history = client.get(f"/accounts/{alice_main['id']}/transactions", headers=alice).json()
    assert [t["label"] for t in history] == ["Dépôt", "Remboursement cinéma", "Restaurant", "Épargne", "Dépôt"]
    assert [t["direction"] for t in history] == ["credit", "credit", "debit", "debit", "credit"]

    restaurant = history[2]
    bob_main = principal(client, bob)
    seen_by_bob = client.get(f"/accounts/{bob_main['id']}/transactions/{restaurant['id']}", headers=bob)
    assert seen_by_bob.json()["direction"] == "credit"

    savings = next(a for a in accounts(client, alice) if a["type"] == "secondaire")
    assert client.get(f"/accounts/{savings['id']}/transactions/{restaurant['id']}", headers=alice).status_code == 404
    assert client.get(f"/accounts/{alice_main['id']}/transactions/999", headers=alice).status_code == 404
    assert client.get(f"/accounts/{alice_main['id']}/transactions/{restaurant['id']}", headers=bob).status_code == 403


def test_s7_account_detail_errors(client):
    alice = login(client)
    bob = login(client, "bob@banque.fr", "bob12345")
    account = principal(client, alice)
    assert client.get(f"/accounts/{account['id']}", headers=alice).json() == account
    assert client.get(f"/accounts/{account['id']}", headers=bob).json() == {"message": "Ce compte ne vous appartient pas"}
    assert client.get("/accounts/999", headers=alice).status_code == 404
    assert client.get("/accounts/abc", headers=alice).status_code == 400


def test_s8_s10_open_and_close(client):
    headers = login(client)
    res = client.post("/accounts", headers=headers)
    assert res.status_code == 201
    new = res.json()
    assert new["type"] == "secondaire" and new["balance"] == 0
    assert accounts(client, headers)[0]["id"] == new["id"]

    assert client.delete(f"/accounts/{new['id']}", headers=headers).status_code == 204
    assert new["id"] not in [a["id"] for a in accounts(client, headers)]
    assert client.get(f"/accounts/{new['id']}", headers=headers).status_code == 404

    main = principal(client, headers)
    assert "principal" in client.delete(f"/accounts/{main['id']}", headers=headers).json()["message"]
    savings = next(a for a in accounts(client, headers) if a["type"] == "secondaire")
    assert "0 €" in client.delete(f"/accounts/{savings['id']}", headers=headers).json()["message"]

    for _ in range(3):
        client.post("/accounts", headers=headers)
    res = client.post("/accounts", headers=headers)
    assert res.status_code == 400 and "maximum" in res.json()["message"]


def test_s12_s13_beneficiaries(client):
    alice = login(client)
    [bob_benef] = client.get("/beneficiaries", headers=alice).json()
    assert bob_benef["name"] == "Bob Martin"

    def add(name, value):
        return client.post("/beneficiaries", json={"name": name, "iban": value}, headers=alice)

    assert add("Bob", bob_benef["iban"]).status_code == 409
    assert add("  ", bob_benef["iban"]).status_code == 400
    assert add("X", "FR761234").json() == {"message": "IBAN invalide"}
    assert add("X", iban.generate()).status_code == 404
    assert add("Moi", principal(client, alice)["iban"]).status_code == 400

    chloe = client.post("/auth/register", json={"email": "chloe@banque.fr", "password": "chloe1234"}).json()
    chloe_headers = {"Authorization": f"Bearer {chloe['accessToken']}"}
    chloe_iban = principal(client, chloe_headers)["iban"]
    res = add("Chloé", chloe_iban.lower())
    assert res.status_code == 201 and res.json()["iban"] == chloe_iban
    assert client.get("/beneficiaries", headers=alice).json()[0]["name"] == "Chloé"
    assert client.get("/beneficiaries", headers=chloe_headers).json() == []

    assert client.delete(f"/beneficiaries/{res.json()['id']}", headers=alice).status_code == 204
    assert client.delete(f"/beneficiaries/{res.json()['id']}", headers=alice).status_code == 404


def test_s14_statement_pdf(client):
    headers = login(client)
    account = principal(client, headers)
    res = client.get(f"/accounts/{account['id']}/statement", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.headers["content-disposition"] == f'attachment; filename="releve-{account["iban"]}.pdf"'
    assert res.content.startswith(b"%PDF-1.4") and res.content.rstrip().endswith(b"%%EOF")
    assert "Restaurant".encode() in res.content
    assert client.get(f"/accounts/{account['id']}/statement").status_code == 401


def test_errors_always_have_a_message(client):
    assert client.get("/nimporte-quoi").json() == {"message": "Route introuvable"}
    res = client.post("/auth/login", content="pas du json", headers={"Content-Type": "application/json"})
    assert res.status_code == 400 and "JSON" in res.json()["message"]
    res = client.post("/auth/login", json={"email": "a@b.fr"})
    assert res.json() == {"message": "Le champ « password » est obligatoire"}
