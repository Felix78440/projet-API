const API_PREFIX = '/api';
const TOKEN_KEY = 'noria_access_token';

export async function api(path, options = {}) {
  const headers = new Headers(options.headers);
  const token = window.sessionStorage.getItem(TOKEN_KEY);

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  let response;
  try {
    response = await fetch(`${API_PREFIX}${path}`, { ...options, headers });
  } catch {
    throw new Error("Impossible de joindre l'API bancaire. Vérifiez que le serveur est démarré.");
  }

  if (response.status === 204) {
    if (!response.ok) {
      throw new Error(`Erreur HTTP ${response.status}.`);
    }
    return null;
  }

  const contentType = response.headers.get('content-type') || '';
  const data = contentType.includes('application/json')
    ? await response.json()
    : null;

  if (!response.ok) {
    throw new Error(data?.message || `Erreur HTTP ${response.status}.`);
  }

  return data;
}

export { TOKEN_KEY };
