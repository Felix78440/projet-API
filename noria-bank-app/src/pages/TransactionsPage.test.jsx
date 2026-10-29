import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { getAccount, getTransactions } from '../services/accounts';
import { getAuthEmail } from '../services/demoAuth';
import TransactionsPage from './TransactionsPage';

vi.mock('../services/accounts', () => ({
  getAccount: vi.fn(),
  getTransactions: vi.fn(),
}));

vi.mock('../services/demoAuth', () => ({
  getAuthEmail: vi.fn(),
  logout: vi.fn(),
}));

const account = {
  id: '1',
  iban: 'FR7611111111111111111111111',
  label: 'Compte principal',
};

function renderTransactions(accountId = account.id) {
  return render(
    <MemoryRouter initialEntries={[`/accounts/${accountId}/transactions`]}>
      <Routes>
        <Route
          path="/accounts/:accountId/transactions"
          element={<TransactionsPage />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe('TransactionsPage', () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.mocked(getAuthEmail).mockReturnValue('alice@banque.fr');
    vi.mocked(getAccount).mockResolvedValue(account);
    vi.mocked(getTransactions).mockReset();
  });

  it('shows an explicit empty state when the account has no transactions', async () => {
    vi.mocked(getTransactions).mockResolvedValue([]);
    renderTransactions();

    expect(await screen.findByText('Aucune transaction pour ce compte.')).toBeTruthy();
  });

  it('shows API transactions with their direction, amount, and IBANs', async () => {
    vi.mocked(getTransactions).mockResolvedValue([
      {
        id: '2',
        amountCents: 1250,
        date: '2026-01-03T10:00:00Z',
        sourceAccountId: account.iban,
        recipientAccountId: 'FR7622222222222222222222222',
        type: 'debit',
        label: 'Virement',
      },
      {
        id: '1',
        amountCents: 5000,
        date: '2026-01-02T10:00:00Z',
        sourceAccountId: null,
        sourceLabel: 'Dépôt externe',
        recipientAccountId: account.iban,
        type: 'credit',
        label: 'Dépôt',
      },
    ]);
    renderTransactions();

    expect(await screen.findByText('Débit')).toBeTruthy();
    expect(screen.getByText('Crédit')).toBeTruthy();
    expect(screen.getAllByText(account.iban).length).toBeGreaterThan(0);
    expect(screen.getByText('FR7622222222222222222222222')).toBeTruthy();
    expect(screen.getByText('Dépôt externe')).toBeTruthy();
    expect(screen.getByText(/−.*12,50/)).toBeTruthy();
    expect(screen.getByText(/\+.*50,00/)).toBeTruthy();
  });
});
