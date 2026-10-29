import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { getAuthToken, login } from '../services/demoAuth';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  if (getAuthToken()) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email.trim(), password);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'La connexion a échoué.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <header className="site-header">
        <Link className="brand" to="/register" aria-label="Noria, accueil">
          <span className="brand-mark" aria-hidden="true">n</span>
          <span>noria</span>
        </Link>
      </header>
      <section className="auth-layout">
        <div className="auth-card">
          <span className="eyebrow">ESPACE CLIENT</span>
          <h1>Connexion</h1>
          <p className="intro">Connectez-vous pour accéder à votre espace personnel.</p>
          <form className="register-form" onSubmit={handleSubmit}>
            {error && <p className="form-error" role="alert">{error}</p>}

            <div className="field">
              <label htmlFor="login-email">Adresse e-mail</label>
              <input
                autoComplete="email"
                id="login-email"
                type="email"
                placeholder="vous@exemple.fr"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="login-password">Mot de passe</label>
              <input
                autoComplete="current-password"
                id="login-password"
                type="password"
                placeholder="Votre mot de passe"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </div>

            <button className="submit-button" type="submit" disabled={loading}>
              {loading ? 'Connexion en cours...' : 'Se connecter'}
            </button>
          </form>

          <p className="demo-hint">
            Démo : <strong>alice@banque.fr</strong> / <strong>alice1234</strong>
          </p>
          <p className="form-footer">
            Pas encore de compte ? <Link className="text-link" to="/register">Créer un compte</Link>
          </p>
        </div>
        <aside className="benefit-panel">
          <span className="benefit-symbol" aria-hidden="true">n</span>
          <div className="benefit-copy">
            <h2>Votre argent, en mouvement.</h2>
            <p>Un compte pensé pour vous accompagner au quotidien, simplement et en toute sérénité.</p>
          </div>
        </aside>
      </section>
    </main>
  );
}
