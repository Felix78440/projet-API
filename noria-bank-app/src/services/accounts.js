import { api } from './api';

function accountFromApi(account) {
  return {
    id: String(account.id),
    iban: account.iban,
    label: account.type === 'principal' ? 'Compte principal' : 'Compte secondaire',
    balanceCents: Math.round(account.balance * 100),
    openedAt: account.createdAt,
  };
}

function transactionFromApi(transaction) {
  return {
    id: String(transaction.id),
    amountCents: Math.round(transaction.amount * 100),
    date: transaction.createdAt,
    sourceAccountId: transaction.fromIban,
    sourceLabel: transaction.fromIban ? undefined : 'Dépôt externe',
    recipientAccountId: transaction.toIban,
    type: transaction.direction,
    label: transaction.label,
  };
}

function accountIdNumber(accountId) {
  const id = Number(accountId);
  if (!Number.isSafeInteger(id) || id < 1) {
    throw new Error('Ce compte est introuvable.');
  }
  return id;
}

export async function getAccounts() {
  const accounts = await api('/accounts');
  return accounts.map(accountFromApi);
}

export async function getAccount(_email, accountId) {
  const account = await api(`/accounts/${accountIdNumber(accountId)}`);
  return accountFromApi(account);
}

export async function getTransactions(_email, accountId) {
  const transactions = await api(`/accounts/${accountIdNumber(accountId)}/transactions`);
  return transactions.map(transactionFromApi);
}

export async function openAccount() {
  const account = await api('/accounts', { method: 'POST' });
  return accountFromApi(account);
}

export async function depositIntoAccount(_email, accountId, amountCents) {
  if (!Number.isSafeInteger(amountCents) || amountCents <= 0) {
    throw new Error('Le montant du dépôt doit être positif.');
  }
  const transaction = await api(`/accounts/${accountIdNumber(accountId)}/deposits`, {
    method: 'POST',
    body: JSON.stringify({ amount: amountCents / 100 }),
  });
  return transactionFromApi(transaction);
}

export async function getBeneficiaries() {
  const beneficiaries = await api('/beneficiaries');
  return beneficiaries.map((beneficiary) => ({
    id: beneficiary.id,
    name: beneficiary.name,
    accountId: beneficiary.iban,
  }));
}

export async function saveBeneficiary(_email, name, iban) {
  if (typeof name !== 'string' || typeof iban !== 'string' || !name.trim() || !iban.trim()) {
    throw new Error('Saisissez le nom et l’IBAN du bénéficiaire.');
  }
  const beneficiary = await api('/beneficiaries', {
    method: 'POST',
    body: JSON.stringify({ name: name.trim(), iban: iban.trim() }),
  });
  return {
    id: beneficiary.id,
    name: beneficiary.name,
    accountId: beneficiary.iban,
  };
}

export async function transferBetweenAccounts(_email, sourceAccountId, recipientIban, amountCents) {
  if (!Number.isSafeInteger(amountCents) || amountCents <= 0) {
    throw new Error('Le montant du virement doit être positif.');
  }
  const transaction = await api('/transfers', {
    method: 'POST',
    body: JSON.stringify({
      fromAccountId: accountIdNumber(sourceAccountId),
      toIban: recipientIban,
      amount: amountCents / 100,
    }),
  });
  return transactionFromApi(transaction);
}
