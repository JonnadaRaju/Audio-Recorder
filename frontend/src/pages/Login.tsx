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
      <div className="auth-left">
        <div className="auth-left-content">
          <h1 className="auth-headline">Record, Store & Replay — Anywhere</h1>
          <p className="auth-subtext">Capture crystal-clear audio and video recordings, 
search your library instantly, and let AI answer 
questions about your recordings.</p>
          
          <div className="feature-list">
            <div className="feature-item">High-quality audio recording</div>
            <div className="feature-item">Video capture with live preview</div>
            <div className="feature-item">AI assistant for your recordings</div>
          </div>

          <div className="mock-visual">
            <div className="mock-visual-label">
              <span className="rec-dot"></span>
              Recording_001.webm  •  02:34
            </div>
            <div className="waveform">
              <div className="wf-bar" style={{"--h": "30%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "60%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "45%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "80%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "55%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "95%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "40%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "70%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "85%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "50%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "100%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "60%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "75%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "35%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "90%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "55%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "65%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "40%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "80%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "25%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "70%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "50%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "88%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "42%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "60%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "33%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "78%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "55%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "45%"} as React.CSSProperties}></div>
              <div className="wf-bar" style={{"--h": "20%"} as React.CSSProperties}></div>
            </div>
            <div className="mock-visual-footer">
              <span>00:00</span>
              <div className="playback-controls">
                <span className="ctrl-btn">⏮</span>
                <span className="ctrl-btn play">▶</span>
                <span className="ctrl-btn">⏭</span>
              </div>
              <span>02:34</span>
            </div>
          </div>
        </div>

        
        <p className="auth-copyright">© 2025. Audio Recorder. All Rights Reserved.</p>
      </div>
      
      <div className="auth-right">
        <div className="auth-card">
          <div className="auth-logo">
            <span>AR</span>
          </div>
          <h2>Welcome to <span className="accent">AudioReach</span></h2>
          <p className="auth-subtitle">Enter your details to access your account</p>
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
          
          <div className="social-row">
            <button className="social-btn" type="button">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              
              
            </button>
            <button className="social-btn" type="button">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              GitHub
            </button>
          </div>
          
          <p className="switch-auth">
            Don't have an account?{' '}
            <button onClick={onSwitchToRegister}>Register</button>
          </p>
        </div>
      </div>
    </div>
  );
};
