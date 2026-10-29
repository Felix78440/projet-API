import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getAccounts } from '../services/accounts';
import { getAuthEmail, logout } from '../services/demoAuth';

const euroFormat = new Intl.NumberFormat('fr-FR', {
  style: 'currency',
  currency: 'EUR',
});

const dateFormat = new Intl.DateTimeFormat('fr-FR', {
  dateStyle: 'long',
});

export default function AccountsPage() {
  const email = getAuthEmail();
  const navigate = useNavigate();
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
        <Link className="back-link" to="/dashboard">← Retour au tableau de bord</Link>
        <div className="page-heading">
          <div>
            <span className="eyebrow">MES COMPTES</span>
            <h1>La liste de mes comptes</h1>
            <p className="intro">{email}</p>
          </div>
          <Link className="action-link" to="/accounts/new">Ouvrir un nouveau compte</Link>
        </div>

        {error && <p className="form-error" role="alert">{error}</p>}
        {loading && <p role="status">Chargement de vos comptes...</p>}

        {!loading && !error && accounts.length === 0 && (
          <section className="dashboard-card empty-state">
            <h2>Vous n’avez pas encore de compte.</h2>
            <p className="intro">Ouvrez votre premier compte pour le retrouver ici.</p>
            <Link className="action-link" to="/accounts/new">Ouvrir un compte</Link>
          </section>
        )}

        {!loading && !error && accounts.length > 0 && (
          <div className="account-list">
            {accounts.map((account) => (
              <article className="account-card" key={account.id}>
                <div>
                  <Link className="account-type account-detail-link" to={`/accounts/${encodeURIComponent(account.id)}`}>
                    {account.label}
                  </Link>
                  <p className="account-reference">IBAN : {account.iban}</p>
                  <p className="account-date">
                    Ouvert le {dateFormat.format(new Date(account.openedAt))}
                  </p>
                </div>
                <strong className="account-balance">
                  {euroFormat.format(account.balanceCents / 100)}
                </strong>
                <Link className="action-link action-link-secondary" to={`/accounts/${encodeURIComponent(account.id)}`}>
                  Voir le compte
                </Link>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
