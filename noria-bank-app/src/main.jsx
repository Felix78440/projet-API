import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import AccountsPage from './pages/AccountsPage';
import NewAccountPage from './pages/NewAccountPage';
import AccountDetailPage from './pages/AccountDetailPage';
import DepositPage from './pages/DepositPage';
import TransferPage from './pages/TransferPage';
import TransactionsPage from './pages/TransactionsPage';
import { getAuthToken } from './services/demoAuth';
import './styles.css';

function ProtectedRoute({ children }) {
  return getAuthToken() ? children : <Navigate to="/login" replace />;
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/register" replace />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/dashboard"
          element={(
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          )}
        />
        <Route
          path="/accounts"
          element={(
            <ProtectedRoute>
              <AccountsPage />
            </ProtectedRoute>
          )}
        />
        <Route
          path="/accounts/:accountId"
          element={(
            <ProtectedRoute>
              <AccountDetailPage />
            </ProtectedRoute>
          )}
        />
        <Route
          path="/accounts/:accountId/deposit"
          element={(
            <ProtectedRoute>
              <DepositPage />
            </ProtectedRoute>
          )}
        />
        <Route
          path="/accounts/:accountId/transactions"
          element={(
            <ProtectedRoute>
              <TransactionsPage />
            </ProtectedRoute>
          )}
        />
        <Route
          path="/transfers"
          element={(
            <ProtectedRoute>
              <TransferPage />
            </ProtectedRoute>
          )}
        />
        <Route
          path="/accounts/new"
          element={(
            <ProtectedRoute>
              <NewAccountPage />
            </ProtectedRoute>
          )}
        />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
