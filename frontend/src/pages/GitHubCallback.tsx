import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';

export const GitHubCallback: React.FC = () => {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const params = new URLSearchParams(window.location.search);
        const code = params.get('code');
        const state = params.get('state');

        if (!code) {
          throw new Error('No authorization code received from GitHub');
        }

        const queryParams = new URLSearchParams({
          code,
          ...(state && { state })
        });

        // Need to get the token by calling backend directly
        const response = await fetch(
          `${apiService.getApiBaseUrl()}/auth/github/callback?${queryParams}`,
          { method: 'GET' }
        );
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Authentication failed');
        }

        const data = await response.json() as { access_token: string; token_type: string };
        apiService.setToken(data.access_token);
        window.location.href = '/';
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Authentication failed');
        setTimeout(() => { window.location.href = '/'; }, 3000);
      }
    };

    handleCallback();
  }, []);

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
      {error ? (
        <div style={{ color: 'red', textAlign: 'center' }}>
          <p>Authentication failed: {error}</p>
          <p>Redirecting to login...</p>
        </div>
      ) : (
        <div style={{ textAlign: 'center' }}>
          <p>Authenticating with GitHub...</p>
        </div>
      )}
    </div>
  );
};
