import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { getAccount, getTransactions } from '../services/accounts';
import { getAuthEmail, logout } from '../services/demoAuth';

const euroFormat = new Intl.NumberFormat('fr-FR', {
  style: 'currency',
  currency: 'EUR',
});

const dateFormat = new Intl.DateTimeFormat('fr-FR', {
  dateStyle: 'long',
  timeStyle: 'short',
});

export default function TransactionsPage() {
  const navigate = useNavigate();
  const { accountId } = useParams();
  const email = getAuthEmail();
  const [account, setAccount] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    Promise.all([getAccount(email, accountId), getTransactions(email, accountId)])
      .then(([loadedAccount, loadedTransactions]) => {
        if (active) {
          setAccount(loadedAccount);
          setTransactions(loadedTransactions);
        }
      })
      .catch((loadError) => {
        if (active) {
          setError(loadError instanceof Error
            ? loadError.message
            : 'Les transactions sont indisponibles.');
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [email, accountId]);

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
        <Link
          className="back-link"
          to={account ? `/accounts/${encodeURIComponent(account.id)}` : '/accounts'}
        >
          ← Retour au détail du compte
        </Link>
        {error && <p className="form-error" role="alert">{error}</p>}
        {loading && <p role="status">Chargement des transactions...</p>}
        {account && (
          <>
            <div className="page-heading">
              <div>
                <span className="eyebrow">HISTORIQUE DU COMPTE</span>
                <h1>Transactions</h1>
                <p className="intro">{account.label} · {account.iban}</p>
              </div>
            </div>

            {transactions.length === 0 ? (
              <section className="dashboard-card empty-state transaction-empty-state">
                <h2>Aucune transaction pour ce compte.</h2>
                <p className="intro">
                  Les dépôts et virements apparaîtront ici.
                </p>
              </section>
            ) : (
              <div className="transaction-list" aria-label="Transactions du compte">
                {transactions.map((transaction) => (
                  <article className="transaction-card" key={transaction.id}>
                    <div className="transaction-heading">
                      <span className={`transaction-type transaction-type-${transaction.type}`}>
                        {transaction.type === 'debit' ? 'Débit' : 'Crédit'}
                      </span>
                      <strong className={`transaction-amount transaction-amount-${transaction.type}`}>
                        {transaction.type === 'debit' ? '−' : '+'}
                        {euroFormat.format(transaction.amountCents / 100)}
                      </strong>
                    </div>
                    <time className="transaction-date" dateTime={transaction.date}>
                      {dateFormat.format(new Date(transaction.date))}
                    </time>
                    <dl className="transaction-accounts">
                      <div>
                        <dt>Compte source</dt>
                        <dd>{transaction.sourceAccountId || transaction.sourceLabel}</dd>
                      </div>
                      <div>
                        <dt>Compte destinataire</dt>
                        <dd>{transaction.recipientAccountId}</dd>
                      </div>
                    </dl>
                  </article>
                ))}
              </div>
            )}
          </>
        )}
      </section>
    </main>
  );
}
