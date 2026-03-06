const REDIRECT_URI = window.location.origin;

let cachedGoogleClientId: string | null = null;
let cachedGithubClientId: string | null = null;
let cachedFrontendUrl: string | null = null;

async function fetchOAuthConfig(): Promise<{ google_client_id?: string; github_client_id?: string; frontend_url?: string }> {
  try {
    // Try multiple possible backend URLs
    const possibleUrls = [
      'http://localhost:8000/auth/oauth/config',
      'http://127.0.0.1:8000/auth/oauth/config',
      `${window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'http://' + window.location.hostname + ':8000' : window.location.protocol + '//' + window.location.hostname}/auth/oauth/config`
    ];
    
    for (const url of possibleUrls) {
      try {
        const response = await fetch(url);
        if (response.ok) {
          return await response.json();
        }
      } catch (e) {
        // Try next URL
        continue;
      }
    }
  } catch (error) {
    console.warn('Could not fetch OAuth config from backend:', error);
  }
  return {};
}

async function getFrontendUrl(): Promise<string> {
  if (cachedFrontendUrl) {
    return cachedFrontendUrl;
  }
  
  // Try to get from backend first
  const config = await fetchOAuthConfig();
  if (config.frontend_url) {
    cachedFrontendUrl = config.frontend_url;
    console.log('Frontend URL loaded from backend:', cachedFrontendUrl);
    return cachedFrontendUrl;
  }
  
  // Fall back to current origin
  cachedFrontendUrl = REDIRECT_URI;
  console.log('Using current origin as frontend URL:', cachedFrontendUrl);
  return cachedFrontendUrl;
}

async function getGoogleClientId(): Promise<string> {
  if (cachedGoogleClientId) {
    return cachedGoogleClientId;
  }
  
  // Try to get from backend first
  const config = await fetchOAuthConfig();
  if (config.google_client_id) {
    cachedGoogleClientId = config.google_client_id;
    console.log('Google Client ID loaded from backend');
    return cachedGoogleClientId;
  }
  
  // Fall back to environment variable
  const envClientId = process.env.REACT_APP_GOOGLE_CLIENT_ID || '';
  if (envClientId) {
    cachedGoogleClientId = envClientId;
    console.log('Google Client ID loaded from environment');
    return envClientId;
  }
  
  throw new Error('Google Client ID not configured');
}

async function getGithubClientId(): Promise<string> {
  if (cachedGithubClientId) {
    return cachedGithubClientId;
  }
  
  // Try to get from backend first
  const config = await fetchOAuthConfig();
  if (config.github_client_id) {
    cachedGithubClientId = config.github_client_id;
    console.log('GitHub Client ID loaded from backend');
    return cachedGithubClientId;
  }
  
  // Fall back to environment variable
  const envClientId = process.env.REACT_APP_GITHUB_CLIENT_ID || '';
  if (envClientId) {
    cachedGithubClientId = envClientId;
    console.log('GitHub Client ID loaded from environment');
    return envClientId;
  }
  
  throw new Error('GitHub Client ID not configured');
}

export class OAuthService {
  static async getGoogleAuthUrl(): Promise<string> {
    const clientId = await getGoogleClientId();
    const frontendUrl = await getFrontendUrl();
    const redirectUri = `${frontendUrl}/auth/google/callback`;
    
    console.log('Using Google Client ID:', clientId);
    console.log('Using Redirect URI:', redirectUri);
    
    const params = new URLSearchParams({
      client_id: clientId,
      redirect_uri: redirectUri,
      response_type: 'code',
      scope: 'openid email profile',
      access_type: 'offline',
    });
    const url = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
    console.log('Google Auth URL:', url);
    return url;
  }

  static async getGitHubAuthUrl(): Promise<string> {
    const clientId = await getGithubClientId();
    const frontendUrl = await getFrontendUrl();
    const redirectUri = `${frontendUrl}/auth/github/callback`;
    
    console.log('Using GitHub Client ID:', clientId);
    console.log('Using Redirect URI:', redirectUri);
    
    const params = new URLSearchParams({
      client_id: clientId,
      redirect_uri: redirectUri,
      response_type: 'code',
      scope: 'user:email',
    });
    const url = `https://github.com/login/oauth/authorize?${params.toString()}`;
    console.log('GitHub Auth URL:', url);
    return url;
  }

  static async initiateGoogleLogin(): Promise<void> {
    try {
      const url = await this.getGoogleAuthUrl();
      window.location.href = url;
    } catch (error) {
      console.error('Failed to initiate Google login:', error);
      alert('Google authentication is not configured. Please check backend configuration.');
    }
  }

  static async initiateGitHubLogin(): Promise<void> {
    try {
      const url = await this.getGitHubAuthUrl();
      window.location.href = url;
    } catch (error) {
      console.error('Failed to initiate GitHub login:', error);
      alert('GitHub authentication is not configured. Please check backend configuration.');
    }
  }
}


