import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  depositIntoAccount,
  getAccount,
  getAccounts,
  getBeneficiaries,
  getTransactions,
  openAccount,
  saveBeneficiary,
  transferBetweenAccounts,
} from './accounts';
import { api } from './api';

vi.mock('./api', () => ({ api: vi.fn() }));

const apiAccount = {
  id: 2,
  iban: 'FR7699999000010123456789012',
  type: 'secondaire',
  balance: 12.34,
  createdAt: '2026-01-02T10:00:00Z',
};

describe('bank account API adapter', () => {
  beforeEach(() => {
    vi.mocked(api).mockReset();
  });

  it('converts API account values to the format used by the interface', async () => {
    vi.mocked(api).mockResolvedValueOnce([apiAccount]);

    await expect(getAccounts()).resolves.toEqual([{
      id: '2',
      iban: apiAccount.iban,
      label: 'Compte secondaire',
      balanceCents: 1234,
      openedAt: apiAccount.createdAt,
    }]);
  });

  it('loads a single account and its transaction history by API id', async () => {
    vi.mocked(api)
      .mockResolvedValueOnce(apiAccount)
      .mockResolvedValueOnce([{
        id: 9,
        amount: 12.34,
        createdAt: '2026-01-03T10:00:00Z',
        fromIban: null,
        toIban: apiAccount.iban,
        direction: 'credit',
        label: 'Dépôt',
      }]);

    await expect(getAccount('alice@example.com', '2')).resolves.toMatchObject({
      id: '2',
      iban: apiAccount.iban,
      balanceCents: 1234,
    });
    await expect(getTransactions('alice@example.com', '2')).resolves.toMatchObject([{
      id: '9',
      amountCents: 1234,
      sourceLabel: 'Dépôt externe',
      recipientAccountId: apiAccount.iban,
      type: 'credit',
    }]);
    expect(api).toHaveBeenNthCalledWith(1, '/accounts/2');
    expect(api).toHaveBeenNthCalledWith(2, '/accounts/2/transactions');
  });

  it('creates accounts and deposits exact euro amounts through the API', async () => {
    vi.mocked(api).mockResolvedValueOnce(apiAccount).mockResolvedValueOnce({
      id: 10,
      amount: 12.34,
      createdAt: '2026-01-03T10:00:00Z',
      fromIban: null,
      toIban: apiAccount.iban,
      direction: 'credit',
      label: 'Dépôt',
    });

    await openAccount();
    await depositIntoAccount('alice@example.com', '2', 1234);

    expect(api).toHaveBeenNthCalledWith(1, '/accounts', { method: 'POST' });
    expect(api).toHaveBeenNthCalledWith(2, '/accounts/2/deposits', {
      method: 'POST',
      body: JSON.stringify({ amount: 12.34 }),
    });
  });

  it('sends transfers and beneficiary requests using IBANs', async () => {
    vi.mocked(api)
      .mockResolvedValueOnce({ id: 1, name: 'Bob', iban: apiAccount.iban })
      .mockResolvedValueOnce([{ id: 1, name: 'Bob', iban: apiAccount.iban }])
      .mockResolvedValueOnce({ id: 7 });

    await saveBeneficiary('alice@example.com', ' Bob ', apiAccount.iban);
    await getBeneficiaries('alice@example.com');
    await transferBetweenAccounts('alice@example.com', '3', apiAccount.iban, 250);

    expect(api).toHaveBeenNthCalledWith(1, '/beneficiaries', {
      method: 'POST',
      body: JSON.stringify({ name: 'Bob', iban: apiAccount.iban }),
    });
    expect(api).toHaveBeenNthCalledWith(2, '/beneficiaries');
    expect(api).toHaveBeenNthCalledWith(3, '/transfers', {
      method: 'POST',
      body: JSON.stringify({
        fromAccountId: 3,
        toIban: apiAccount.iban,
        amount: 2.5,
      }),
    });
  });

  it('rejects invalid amounts and account identifiers before making a request', async () => {
    await expect(depositIntoAccount('', '2', 0)).rejects.toThrow('positif');
    await expect(transferBetweenAccounts('', 'unknown', apiAccount.iban, 100))
      .rejects.toThrow('introuvable');
    expect(api).not.toHaveBeenCalled();
  });
});
