import React, { useState } from 'react';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { apiService } from './services/api';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!apiService.getToken());
  const [showRegister, setShowRegister] = useState(false);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    apiService.setToken(null);
    setIsAuthenticated(false);
  };

  const handleSwitchToRegister = () => {
    setShowRegister(true);
  };

  const handleSwitchToLogin = () => {
    setShowRegister(false);
  };

  if (isAuthenticated) {
    return <Dashboard onLogout={handleLogout} />;
  }

  return showRegister ? (
    <Register onRegister={handleLogin} onSwitchToLogin={handleSwitchToLogin} />
  ) : (
    <Login onLogin={handleLogin} onSwitchToRegister={handleSwitchToRegister} />
  );
}

export default App;
