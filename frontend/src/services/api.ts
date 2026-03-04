const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface Recording {
  id: number;
  user_id: number;
  filename: string;
  file_path: string;
  file_size: number;
  duration: number | null;
  created_at: string;
}

export interface RecordingListItem {
  id: number;
  filename: string;
  file_size: number;
  duration: number | null;
  created_at: string;
}

class ApiService {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('token');
    }
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      ...options.headers,
    };

    const token = this.getToken();
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData)) {
      (headers as Record<string, string>)['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  async register(email: string, password: string): Promise<User> {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async login(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
    return this.request<{ access_token: string; token_type: string }>(
      `/auth/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
      { method: 'POST' }
    );
  }

  async uploadRecording(file: File, duration?: number): Promise<Recording> {
    const formData = new FormData();
    formData.append('file', file);
    if (duration !== undefined) {
      formData.append('duration', duration.toString());
    }

    return this.request<Recording>('/recordings/upload', {
      method: 'POST',
      body: formData,
    });
  }

  async getRecordings(): Promise<RecordingListItem[]> {
    return this.request<RecordingListItem[]>('/recordings', {
      method: 'GET',
    });
  }

  async getRecording(id: number): Promise<Recording> {
    return this.request<Recording>(`/recordings/${id}`, {
      method: 'GET',
    });
  }

  async deleteRecording(id: number): Promise<void> {
    return this.request<void>(`/recordings/${id}`, {
      method: 'DELETE',
    });
  }

  getStreamUrl(id: number): string {
    const token = this.getToken();
    return `${API_BASE_URL}/recordings/${id}/stream?token=${token}`;
  }
}

export const apiService = new ApiService();
