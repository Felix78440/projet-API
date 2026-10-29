import { api, TOKEN_KEY } from './api';

const EMAIL_KEY = 'noria_user_email';

export async function login(email, password) {
  const response = await api('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  saveAuthSession(response);
  return response;
}

export function saveAuthSession(response) {
  if (
    !response
    || typeof response.accessToken !== 'string'
    || typeof response.user?.email !== 'string'
  ) {
    throw new Error("La réponse d'authentification de l'API est invalide.");
  }
  window.sessionStorage.setItem(TOKEN_KEY, response.accessToken);
  window.sessionStorage.setItem(EMAIL_KEY, response.user.email);
}

export function getAuthToken() {
  return window.sessionStorage.getItem(TOKEN_KEY);
}

export function getAuthEmail() {
  return window.sessionStorage.getItem(EMAIL_KEY);
}

export function logout() {
  window.sessionStorage.removeItem(TOKEN_KEY);
  window.sessionStorage.removeItem(EMAIL_KEY);
}
