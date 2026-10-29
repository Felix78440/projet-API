import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getAccounts } from '../services/accounts';
import { getAuthEmail, logout } from '../services/demoAuth';

const euroFormat = new Intl.NumberFormat('fr-FR', {
  style: 'currency',
  currency: 'EUR',
});

export default function DashboardPage() {
  const navigate = useNavigate();
  const email = getAuthEmail();
  const [accounts, setAccounts] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getAccounts()
      .then((loadedAccounts) => {
        if (active) setAccounts(loadedAccounts);
      })
      .catch((loadError) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : 'Les comptes sont indisponibles.');
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  const totalBalance = accounts.reduce((total, account) => total + account.balanceCents, 0);

  return (
    <main className="page-shell">
      <header className="site-header dashboard-header">
        <Link className="brand" to="/dashboard" aria-label="Noria, tableau de bord">
          <span className="brand-mark" aria-hidden="true">n</span>
          <span>noria</span>
        </Link>
        <button className="logout-button" onClick={handleLogout} type="button">
          Se déconnecter
        </button>
      </header>
      <section className="dashboard-content">
        <div className="dashboard-welcome">
          <span className="eyebrow">ESPACE CLIENT</span>
          <h1>Bonjour, bienvenue chez Noria.</h1>
          <p className="intro">Connecté en tant que <strong>{email || 'utilisateur inconnu'}</strong></p>
        </div>

        {error && <p className="form-error" role="alert">{error}</p>}
        {loading && <p role="status">Chargement de vos comptes...</p>}

        {!loading && !error && (
          <div className="account-summary" aria-label="Résumé de vos comptes">
            <article className="summary-card">
              <span className="summary-label">Nombre de comptes</span>
              <strong className="summary-value">{accounts.length}</strong>
            </article>
            <article className="summary-card summary-card-balance">
              <span className="summary-label">Solde total</span>
              <strong className="summary-value">{euroFormat.format(totalBalance / 100)}</strong>
              <span className="summary-caption">Calculé à partir de vos comptes</span>
            </article>
          </div>
        )}

        <section className="dashboard-card dashboard-actions">
          <h2>Gérez vos comptes</h2>
          <p className="intro">Consultez vos comptes, effectuez un virement ou ouvrez-en un nouveau.</p>
          <div className="dashboard-links">
            <Link className="action-link action-link-secondary" to="/accounts">
              Voir la liste de mes comptes
            </Link>
            <Link className="action-link action-link-secondary" to="/transfers">
              Effectuer un virement
            </Link>
            <Link className="action-link" to="/accounts/new">
              Ouvrir un nouveau compte
            </Link>
          </div>
          <p className="demo-notice">
            Les opérations sont enregistrées par l’API de démonstration.
          </p>
        </section>
      </section>
    </main>
  );
}
