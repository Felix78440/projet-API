import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import {
  getAccounts,
  getBeneficiaries,
  saveBeneficiary,
  transferBetweenAccounts,
} from '../services/accounts';
import { getAuthEmail } from '../services/demoAuth';
import TransferPage from './TransferPage';

vi.mock('../services/accounts', () => ({
  getAccounts: vi.fn(),
  getBeneficiaries: vi.fn(),
  saveBeneficiary: vi.fn(),
  transferBetweenAccounts: vi.fn(),
}));

vi.mock('../services/demoAuth', () => ({
  getAuthEmail: vi.fn(),
  logout: vi.fn(),
}));

const source = {
  id: '1',
  iban: 'FR7611111111111111111111111',
  label: 'Compte principal',
  balanceCents: 5000,
};
const recipientIban = 'FR7622222222222222222222222';

function renderTransfer() {
  return render(
    <MemoryRouter initialEntries={['/transfers']}>
      <Routes>
        <Route path="/transfers" element={<TransferPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('TransferPage', () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.mocked(getAuthEmail).mockReturnValue('alice@banque.fr');
    vi.mocked(getAccounts).mockReset();
    vi.mocked(getAccounts).mockResolvedValue([source]);
    vi.mocked(getBeneficiaries).mockReset();
    vi.mocked(getBeneficiaries).mockResolvedValue([]);
    vi.mocked(saveBeneficiary).mockReset();
    vi.mocked(transferBetweenAccounts).mockReset();
  });

  it('saves an IBAN beneficiary, transfers money, and refreshes the source balance', async () => {
    const user = userEvent.setup();
    const savedBeneficiary = { name: 'Alex', accountId: recipientIban };
    vi.mocked(saveBeneficiary).mockResolvedValue(savedBeneficiary);
    vi.mocked(getBeneficiaries).mockResolvedValueOnce([]).mockResolvedValueOnce([savedBeneficiary]);
    vi.mocked(transferBetweenAccounts).mockResolvedValue({});
    vi.mocked(getAccounts)
      .mockResolvedValueOnce([source])
      .mockResolvedValueOnce([{ ...source, balanceCents: 3750 }]);
    renderTransfer();

    await user.selectOptions(await screen.findByLabelText('Compte source'), source.id);
    await user.type(screen.getByLabelText('IBAN du compte destinataire'), recipientIban);
    await user.type(screen.getByLabelText('Nom du bénéficiaire'), 'Alex');
    await user.click(screen.getByRole('button', { name: 'Enregistrer ce bénéficiaire' }));

    expect(await screen.findByRole('status')).toBeTruthy();
    expect(saveBeneficiary).toHaveBeenCalledWith(
      'alice@banque.fr',
      'Alex',
      recipientIban,
    );

    await user.selectOptions(screen.getByLabelText('Bénéficiaire enregistré'), recipientIban);
    await user.type(screen.getByLabelText('Montant (€)'), '12.50');
    await user.click(screen.getByRole('button', { name: 'Confirmer le virement' }));

    expect(await screen.findByText('Le virement a été effectué.')).toBeTruthy();
    expect(transferBetweenAccounts).toHaveBeenCalledWith(
      'alice@banque.fr',
      source.id,
      recipientIban,
      1250,
    );
    expect(screen.getByLabelText('Compte source').selectedOptions[0].textContent)
      .toContain('37,50');
  });

  it('shows an API error when the transfer is rejected', async () => {
    const user = userEvent.setup();
    vi.mocked(transferBetweenAccounts).mockRejectedValue(new Error('Solde insuffisant'));
    renderTransfer();

    await user.selectOptions(await screen.findByLabelText('Compte source'), source.id);
    await user.type(screen.getByLabelText('IBAN du compte destinataire'), recipientIban);
    await user.type(screen.getByLabelText('Montant (€)'), '1');
    await user.click(screen.getByRole('button', { name: 'Confirmer le virement' }));

    expect((await screen.findByRole('alert')).textContent).toContain('Solde insuffisant');
  });
});
