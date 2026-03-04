import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import './Auth.css';

interface LoginProps {
  onLogin: () => void;
  onSwitchToRegister: () => void;
  message?: string | null;
  clearMessage?: () => void;
}

export const Login: React.FC<LoginProps> = ({
  onLogin,
  onSwitchToRegister,
  message,
  clearMessage
}) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!message || !clearMessage) {
      return;
    }
    const timer = window.setTimeout(() => {
      clearMessage();
    }, 5000);
    return () => window.clearTimeout(timer);
  }, [message, clearMessage]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await apiService.login(email, password);
      apiService.setToken(response.access_token);
      onLogin();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Login</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {message && <div className="success-message">{message}</div>}
          {error && <div className="error-message">{error}</div>}
          <button type="submit" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        <p className="switch-auth">
          Don't have an account?{' '}
          <button onClick={onSwitchToRegister}>Register</button>
        </p>
      </div>
    </div>
  );
};
