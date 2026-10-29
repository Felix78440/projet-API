import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../services/api';
import RegisterPage from './RegisterPage';

vi.mock('../services/api', () => ({
  api: vi.fn(),
  TOKEN_KEY: 'noria_access_token',
}));

function renderRegisterPage() {
  return render(
    <MemoryRouter>
      <RegisterPage />
    </MemoryRouter>,
  );
}

describe('RegisterPage', () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.mocked(api).mockReset();
    window.sessionStorage.clear();
  });

  it('displays the required email and password fields', () => {
    renderRegisterPage();

    expect(screen.getByRole('heading', { name: 'Votre compte commence ici.' })).toBeTruthy();
    expect(screen.getByLabelText('Adresse e-mail').required).toBe(true);
    expect(screen.getByLabelText('Mot de passe').required).toBe(true);
  });

  it('submits the registration data and displays success', async () => {
    const user = userEvent.setup();
    vi.mocked(api).mockResolvedValueOnce({
      accessToken: 'registered-token',
      user: { email: 'alice@example.com' },
    });
    renderRegisterPage();

    await user.type(screen.getByLabelText('Adresse e-mail'), 'alice@example.com');
    await user.type(screen.getByLabelText('Mot de passe'), 'SecurePass123!');
    await user.click(screen.getByRole('button', { name: 'Créer mon compte' }));

    await waitFor(() => {
      expect(api).toHaveBeenCalledWith('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'alice@example.com',
          password: 'SecurePass123!',
        }),
      });
    });
    expect(
      await screen.findByRole('heading', { name: 'Inscription réussie !' }),
    ).toBeTruthy();
    expect(
      screen.getByRole('link', { name: 'Accéder à mon espace' }).getAttribute('href'),
    ).toBe('/dashboard');
    expect(window.sessionStorage.getItem('noria_access_token')).toBe('registered-token');
  });

  it('displays an API error and re-enables the submit button', async () => {
    const user = userEvent.setup();
    vi.mocked(api).mockRejectedValueOnce(new Error('Adresse déjà utilisée'));
    renderRegisterPage();

    await user.type(screen.getByLabelText('Adresse e-mail'), 'alice@example.com');
    await user.type(screen.getByLabelText('Mot de passe'), 'SecurePass123!');
    await user.click(screen.getByRole('button', { name: 'Créer mon compte' }));

    expect(await screen.findByText('Adresse déjà utilisée')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Créer mon compte' }).disabled).toBe(false);
  });

  it('shows a disabled loading button while the request is pending', async () => {
    const user = userEvent.setup();
    let resolveRequest;
    vi.mocked(api).mockReturnValueOnce(
      new Promise((resolve) => {
        resolveRequest = resolve;
      }),
    );
    renderRegisterPage();

    await user.type(screen.getByLabelText('Adresse e-mail'), 'alice@example.com');
    await user.type(screen.getByLabelText('Mot de passe'), 'SecurePass123!');
    await user.click(screen.getByRole('button', { name: 'Créer mon compte' }));

    const loadingButton = screen.getByRole('button', { name: 'Création en cours...' });
    expect(loadingButton.disabled).toBe(true);

    resolveRequest({
      accessToken: 'registered-token',
      user: { email: 'alice@example.com' },
    });
    expect(
      await screen.findByRole('heading', { name: 'Inscription réussie !' }),
    ).toBeTruthy();
  });
});
