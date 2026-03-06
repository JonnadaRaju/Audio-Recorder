import React, { useState, useEffect } from 'react';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { GoogleCallback } from './pages/GoogleCallback';
import { GitHubCallback } from './pages/GitHubCallback';
import { apiService } from './services/api';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!apiService.getToken());
  const [showRegister, setShowRegister] = useState(false);
  const [authMessage, setAuthMessage] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<string>('login');

  useEffect(() => {
    const pathname = window.location.pathname;
    if (pathname.includes('/auth/google/callback')) {
      setCurrentPage('google-callback');
    } else if (pathname.includes('/auth/github/callback')) {
      setCurrentPage('github-callback');
    }
  }, []);

  const handleLogin = () => {
    setIsAuthenticated(true);
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    apiService.setToken(null);
    setIsAuthenticated(false);
    setCurrentPage('login');
  };

  const handleSwitchToRegister = () => {
    setAuthMessage(null);
    setShowRegister(true);
    setCurrentPage('register');
  };

  const handleSwitchToLogin = () => {
    setShowRegister(false);
    setCurrentPage('login');
  };

  const handleRegisterSuccess = (message: string) => {
    setAuthMessage(message);
    setShowRegister(false);
    setCurrentPage('login');
  };

  if (currentPage === 'google-callback') {
    return <GoogleCallback />;
  }

  if (currentPage === 'github-callback') {
    return <GitHubCallback />;
  }

  if (isAuthenticated || currentPage === 'dashboard') {
    return <Dashboard onLogout={handleLogout} />;
  }

  return showRegister ? (
    <Register onSwitchToLogin={handleSwitchToLogin} onRegisterSuccess={handleRegisterSuccess} />
  ) : (
    <Login
      onLogin={handleLogin}
      onSwitchToRegister={handleSwitchToRegister}
      message={authMessage}
      clearMessage={() => setAuthMessage(null)}
    />
  );
}

export default App;
