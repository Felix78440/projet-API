import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { depositIntoAccount, getAccount } from '../services/accounts';
import { getAuthEmail } from '../services/demoAuth';
import DepositPage from './DepositPage';
import AccountDetailPage from './AccountDetailPage';

vi.mock('../services/accounts', () => ({
  depositIntoAccount: vi.fn(),
  getAccount: vi.fn(),
}));

vi.mock('../services/demoAuth', () => ({
  getAuthEmail: vi.fn(),
  logout: vi.fn(),
}));

function CurrentPath() {
  const location = useLocation();
  return <span data-testid="current-path">{location.pathname}</span>;
}

function renderDeposit(accountId) {
  return render(
    <MemoryRouter initialEntries={[`/accounts/${accountId}/deposit`]}>
      <Routes>
        <Route path="/accounts/:accountId/deposit" element={<DepositPage />} />
        <Route path="/accounts/:accountId" element={<AccountDetailPage />} />
      </Routes>
      <CurrentPath />
    </MemoryRouter>,
  );
}

describe('DepositPage', () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.mocked(getAuthEmail).mockReturnValue('alice@banque.fr');
    vi.mocked(depositIntoAccount).mockReset();
    vi.mocked(depositIntoAccount).mockResolvedValue({});
    vi.mocked(getAccount).mockReset();
  });

  it('rejects zero and returns to the selected account with its updated balance', async () => {
    const user = userEvent.setup();
    const account = {
      id: '1',
      iban: 'FR7611111111111111111111111',
      label: 'Compte principal',
      balanceCents: 0,
    };
    vi.mocked(getAccount).mockResolvedValueOnce(account).mockResolvedValueOnce({
      ...account,
      balanceCents: 1234,
    });
    renderDeposit(account.id);

    const amountInput = await screen.findByLabelText('Montant du dépôt (€)');
    await user.type(amountInput, '0');
    fireEvent.submit(amountInput.closest('form'));

    expect((await screen.findByRole('alert')).textContent).toContain(
      'Saisissez un montant positif avec au maximum deux décimales.',
    );
    expect(screen.getByTestId('current-path').textContent).toBe(`/accounts/${account.id}/deposit`);

    await user.clear(amountInput);
    await user.type(amountInput, '12.34');
    await user.click(screen.getByRole('button', { name: 'Confirmer le dépôt' }));

    await waitFor(() => {
      expect(screen.getByTestId('current-path').textContent).toBe(`/accounts/${account.id}`);
    });
    expect(depositIntoAccount).toHaveBeenCalledWith('alice@banque.fr', account.id, 1234);
    expect(screen.getByText((text) => text.includes('12,34'))).toBeTruthy();
  });
});
