import React, { useState } from 'react';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { apiService } from './services/api';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!apiService.getToken());
  const [showRegister, setShowRegister] = useState(false);
  const [authMessage, setAuthMessage] = useState<string | null>(null);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    apiService.setToken(null);
    setIsAuthenticated(false);
  };

  const handleSwitchToRegister = () => {
    setAuthMessage(null);
    setShowRegister(true);
  };

  const handleSwitchToLogin = () => {
    setShowRegister(false);
  };

  const handleRegisterSuccess = (message: string) => {
    setAuthMessage(message);
    setShowRegister(false);
  };

  if (isAuthenticated) {
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
